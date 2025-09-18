"""
Paddle Payment Integration Routes
Handles subscription management, webhooks, and payment processing
"""

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import hmac
import hashlib
from datetime import datetime
import logging

from .dependencies import get_current_user
from ..models.database import get_db
from ..models.user import User
from ..config import settings

router = APIRouter(tags=["payments"])

# Configure logging
logger = logging.getLogger(__name__)

# Try to import Paddle SDK, fall back to requests if not available
try:
    import paddle_billing
    PADDLE_SDK_AVAILABLE = True
    logger.info("Paddle SDK available")
except ImportError:
    PADDLE_SDK_AVAILABLE = False
    import requests
    logger.info("Paddle SDK not available, using requests")

# Pydantic models for request/response
class CreateSubscriptionRequest(BaseModel):
    """Request model for creating a subscription"""
    price_id: str
    custom_data: Optional[Dict[str, Any]] = None

class SubscriptionResponse(BaseModel):
    """Response model for subscription operations"""
    subscription_id: str
    status: str
    checkout_url: Optional[str] = None
    customer_id: str
    product_id: str
    price_id: str
    currency: str
    unit_price: int
    quantity: int
    next_billing_date: Optional[str] = None

class WebhookEvent(BaseModel):
    """Paddle webhook event model"""
    event_type: str
    data: Dict[str, Any]
    occurred_at: str

@router.post("/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new subscription for the current user
    """
    try:
        from ..services.paddle_service import PaddleService

        paddle_service = PaddleService()

        # Ensure user has Paddle customer ID
        if not current_user.paddle_customer_id:
            current_user.paddle_customer_id = await _create_paddle_customer(current_user)
            db.commit()

        # Create subscription using Paddle service
        subscription = await paddle_service.create_subscription(
            user_id=current_user.id,
            price_id=request.price_id,
            custom_data={
                "user_id": str(current_user.id),
                **(request.custom_data or {})
            }
        )

        return SubscriptionResponse(
            subscription_id=subscription["subscription_id"],
            status=subscription["status"],
            checkout_url=subscription.get("checkout_url"),
            customer_id=subscription["customer_id"],
            product_id=subscription["product_id"],
            price_id=subscription["price_id"],
            currency=subscription["currency"]
        )

    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/subscription/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get subscription details
    """
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {settings.PADDLE_API_KEY}"
        }

        response = requests.get(
            f"{settings.paddle_api_base_url}/subscriptions/{subscription_id}",
            headers=headers
        )

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription = response.json()

        # Verify ownership
        if subscription["customer_id"] != current_user.paddle_customer_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return subscription

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/webhook")
async def paddle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Paddle webhooks for payment events
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        signature = request.headers.get("Paddle-Signature")

        # Process webhook using Paddle service
        from ..services.paddle_service import PaddleService
        paddle_service = PaddleService()

        # Verify signature using service method
        if not paddle_service.verify_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse webhook data
        webhook_data = json.loads(body.decode())
        event_type = webhook_data.get("event_type")

        logger.info(f"Received Paddle webhook: {event_type}")

        # Process webhook using Paddle service (queues to Redis)
        await paddle_service.process_webhook(webhook_data)

        return {"status": "ok"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _create_paddle_customer(user: User) -> str:
    """
    Create a customer in Paddle
    """
    try:
        import requests

        customer_data = {
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "custom_data": {
                "user_id": str(user.id)
            }
        }

        headers = {
            "Authorization": f"Bearer {settings.PADDLE_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{settings.paddle_api_base_url}/customers",
            json=customer_data,
            headers=headers
        )

        if response.status_code != 201:
            logger.error(f"Failed to create Paddle customer: {response.text}")
            raise HTTPException(status_code=400, detail="Failed to create customer")

        customer = response.json()
        return customer["id"]

    except Exception as e:
        logger.error(f"Error creating Paddle customer: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def _verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify Paddle webhook signature
    """
    if not signature or not settings.PADDLE_WEBHOOK_SECRET:
        return False

    try:
        # Parse signature header
        signature_parts = {}
        for part in signature.split(","):
            key, value = part.split("=", 1)
            signature_parts[key] = value

        timestamp = signature_parts.get("t")
        received_hmac = signature_parts.get("h1")

        if not timestamp or not received_hmac:
            return False

        # Create expected signature
        signed_payload = f"{timestamp}:{body.decode()}"
        expected_hmac = hmac.new(
            settings.PADDLE_WEBHOOK_SECRET.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # Use constant time comparison
        return hmac.compare_digest(expected_hmac, received_hmac)

    except Exception as e:
        logger.error(f"Signature verification error: {str(e)}")
        return False

async def _process_webhook(webhook_data: Dict[str, Any]):
    """
    Process Paddle webhook events
    """
    try:
        event_type = webhook_data.get("event_type")
        data = webhook_data.get("data", {})

        logger.info(f"Processing webhook event: {event_type}")

        # Handle different event types
        if event_type == "subscription.created":
            await _handle_subscription_created(data)
        elif event_type == "subscription.updated":
            await _handle_subscription_updated(data)
        elif event_type == "subscription.canceled":
            await _handle_subscription_canceled(data)
        elif event_type == "transaction.completed":
            await _handle_transaction_completed(data)
        elif event_type == "transaction.failed":
            await _handle_transaction_failed(data)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")

async def _handle_subscription_created(data: Dict[str, Any]):
    """Handle subscription created event"""
    # Update user's subscription status in database
    customer_id = data.get("customer_id")
    subscription_id = data.get("id")

    # TODO: Update user subscription status
    logger.info(f"Subscription created: {subscription_id} for customer: {customer_id}")

async def _handle_subscription_updated(data: Dict[str, Any]):
    """Handle subscription updated event"""
    # Update subscription details
    logger.info(f"Subscription updated: {data.get('id')}")

async def _handle_subscription_canceled(data: Dict[str, Any]):
    """Handle subscription canceled event"""
    # Update user's subscription status
    logger.info(f"Subscription canceled: {data.get('id')}")

async def _handle_transaction_completed(data: Dict[str, Any]):
    """Handle successful transaction"""
    # Process successful payment
    logger.info(f"Transaction completed: {data.get('id')}")

async def _handle_transaction_failed(data: Dict[str, Any]):
    """Handle failed transaction"""
    # Handle payment failure
    logger.info(f"Transaction failed: {data.get('id')}")