"""
Paddle Payment Service
Handles subscription management, webhook processing, and payment operations
"""

import json
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import requests  # Import requests at module level
import httpx  # For async HTTP requests

try:
    import paddle_billing
    PADDLE_SDK_AVAILABLE = True
except ImportError:
    PADDLE_SDK_AVAILABLE = False

from ..config import settings
from ..models.user import User
from ..services.redis_service import RedisService
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)

class PaddleService:
    """Paddle payment service for subscription management"""

    def __init__(self):
        self.redis_service = RedisService()
        self.email_service = EmailService()
        self.api_key = settings.PADDLE_API_KEY
        self.environment = settings.PADDLE_ENVIRONMENT
        self.webhook_secret = settings.PADDLE_WEBHOOK_SECRET

        if PADDLE_SDK_AVAILABLE:
            # Initialize Paddle SDK client
            self.client = paddle_billing.Client(
                api_key=self.api_key,
                environment=self.environment
            )
        else:
            self.client = None
            logger.warning("Paddle SDK not available, using requests fallback")

    async def create_subscription(
        self,
        user_id: int,
        price_id: str,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new subscription for a user
        """
        try:
            # Get user from database
            from ..models.database import get_db
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                raise ValueError(f"User {user_id} not found")

            if PADDLE_SDK_AVAILABLE and self.client:
                # Use Paddle SDK
                subscription_data = {
                    "customer_id": user.paddle_customer_id,
                    "price_id": price_id,
                    "custom_data": custom_data or {},
                    "collection_mode": "automatic"
                }

                subscription = self.client.subscriptions.create(subscription_data)
                return {
                    "subscription_id": subscription.id,
                    "status": subscription.status,
                    "checkout_url": getattr(subscription, 'checkout_url', None),
                    "customer_id": subscription.customer_id,
                    "product_id": subscription.product_id,
                    "price_id": subscription.price_id,
                    "currency": subscription.currency_code
                }
            else:
                # Fallback to requests
                url = f"https://api.paddle.com/subscriptions"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "customer_id": user.paddle_customer_id,
                    "price_id": price_id,
                    "custom_data": custom_data or {},
                    "collection_mode": "automatic"
                }

                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()

                result = response.json()
                return {
                    "subscription_id": result["data"]["id"],
                    "status": result["data"]["status"],
                    "checkout_url": result["data"].get("checkout_url"),
                    "customer_id": result["data"]["customer_id"],
                    "product_id": result["data"]["product_id"],
                    "price_id": result["data"]["price_id"],
                    "currency": result["data"]["currency_code"]
                }

        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details
        """
        try:
            if PADDLE_SDK_AVAILABLE and self.client:
                subscription = self.client.subscriptions.get(subscription_id)
                return {
                    "subscription_id": subscription.id,
                    "status": subscription.status,
                    "customer_id": subscription.customer_id,
                    "product_id": subscription.product_id,
                    "price_id": subscription.price_id,
                    "currency": subscription.currency_code,
                    "next_billing_date": getattr(subscription, 'next_billing_date', None)
                }
            else:
                url = f"https://api.paddle.com/subscriptions/{subscription_id}"
                headers = {"Authorization": f"Bearer {self.api_key}"}

                response = requests.get(url, headers=headers)
                response.raise_for_status()

                result = response.json()
                return {
                    "subscription_id": result["data"]["id"],
                    "status": result["data"]["status"],
                    "customer_id": result["data"]["customer_id"],
                    "product_id": result["data"]["product_id"],
                    "price_id": result["data"]["price_id"],
                    "currency": result["data"]["currency_code"],
                    "next_billing_date": result["data"].get("next_billing_date")
                }

        except Exception as e:
            logger.error(f"Error getting subscription: {str(e)}")
            raise

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancel a subscription
        """
        try:
            if PADDLE_SDK_AVAILABLE and self.client:
                self.client.subscriptions.cancel(subscription_id)
            else:
                url = f"https://api.paddle.com/subscriptions/{subscription_id}/cancel"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                response = requests.post(url, headers=headers)
                response.raise_for_status()

            logger.info(f"Subscription {subscription_id} cancelled successfully")
            return True

        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify Paddle webhook signature
        """
        if not signature or not self.webhook_secret:
            logger.warning("Missing webhook signature or secret")
            return False

        try:
            # Create HMAC signature
            secret_bytes = self.webhook_secret.encode()
            computed_signature = hmac.new(
                secret_bytes,
                body,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(computed_signature, signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False

    async def process_webhook(self, webhook_data: Dict[str, Any]):
        """
        Process Paddle webhook events using Redis task queue
        """
        try:
            event_type = webhook_data.get("event_type")
            logger.info(f"Processing Paddle webhook: {event_type}")

            # Queue webhook processing task
            await self.redis_service.queue_paddle_webhook_task(webhook_data)

        except Exception as e:
            logger.error(f"Error queuing webhook processing: {str(e)}")

    async def process_queued_webhook(self, webhook_data: Dict[str, Any]):
        """
        Process a queued webhook event
        """
        try:
            event_type = webhook_data.get("event_type")
            data = webhook_data.get("data", {})

            logger.info(f"Processing queued webhook event: {event_type}")

            # Handle different event types
            if event_type == "subscription.created":
                await self._handle_subscription_created(data)
            elif event_type == "subscription.updated":
                await self._handle_subscription_updated(data)
            elif event_type == "subscription.canceled":
                await self._handle_subscription_canceled(data)
            elif event_type == "transaction.completed":
                await self._handle_transaction_completed(data)
            elif event_type == "transaction.failed":
                await self._handle_transaction_failed(data)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")

        except Exception as e:
            logger.error(f"Error processing queued webhook: {str(e)}")

    async def _handle_subscription_created(self, data: Dict[str, Any]):
        """Handle subscription created event"""
        try:
            customer_id = data.get("customer_id")
            subscription_id = data.get("id")
            price_id = data.get("price_id")

            # Update user subscription in database
            from ..models.database import get_db
            db = next(get_db())

            user = db.query(User).filter(User.paddle_customer_id == customer_id).first()
            if user:
                # Update user plan based on price_id
                plan = self._get_plan_from_price_id(price_id)
                user.plan = plan
                user.subscription_id = subscription_id
                user.subscription_status = "active"
                db.commit()

                logger.info(f"Updated user {user.id} plan to {plan}")

                # Send welcome email
                await self._send_subscription_email(user, "welcome", plan)
            else:
                logger.warning(f"User with paddle_customer_id {customer_id} not found")

        except Exception as e:
            logger.error(f"Error handling subscription created: {str(e)}")

    async def _handle_subscription_updated(self, data: Dict[str, Any]):
        """Handle subscription updated event"""
        try:
            subscription_id = data.get("id")
            status = data.get("status")
            price_id = data.get("price_id")

            from ..models.database import get_db
            db = next(get_db())

            user = db.query(User).filter(User.subscription_id == subscription_id).first()
            if user:
                if price_id:
                    plan = self._get_plan_from_price_id(price_id)
                    user.plan = plan

                user.subscription_status = status
                db.commit()

                logger.info(f"Updated subscription {subscription_id} status to {status}")

        except Exception as e:
            logger.error(f"Error handling subscription updated: {str(e)}")

    async def _handle_subscription_canceled(self, data: Dict[str, Any]):
        """Handle subscription canceled event"""
        try:
            subscription_id = data.get("id")

            from ..models.database import get_db
            db = next(get_db())

            user = db.query(User).filter(User.subscription_id == subscription_id).first()
            if user:
                user.subscription_status = "canceled"
                user.plan = "FREE"  # Downgrade to free plan
                db.commit()

                logger.info(f"Cancelled subscription {subscription_id} for user {user.id}")

                # Send cancellation email
                await self._send_subscription_email(user, "cancellation")

        except Exception as e:
            logger.error(f"Error handling subscription canceled: {str(e)}")

    async def _handle_transaction_completed(self, data: Dict[str, Any]):
        """Handle successful transaction"""
        try:
            transaction_id = data.get("id")
            subscription_id = data.get("subscription_id")
            amount = data.get("details", {}).get("totals", {}).get("total")

            logger.info(f"Transaction {transaction_id} completed for subscription {subscription_id}")

            # Could send receipt email here
            # await self._send_payment_receipt_email(user, amount, transaction_id)

        except Exception as e:
            logger.error(f"Error handling transaction completed: {str(e)}")

    async def _handle_transaction_failed(self, data: Dict[str, Any]):
        """Handle failed transaction"""
        try:
            transaction_id = data.get("id")
            subscription_id = data.get("subscription_id")

            logger.warning(f"Transaction {transaction_id} failed for subscription {subscription_id}")

            # Could send payment failure notification here

        except Exception as e:
            logger.error(f"Error handling transaction failed: {str(e)}")

    def _get_plan_from_price_id(self, price_id: str) -> str:
        """Map Paddle price ID to plan name"""
        price_plan_map = {
            settings.PADDLE_PRICE_ID_BASIC: "BASIC",
            settings.PADDLE_PRICE_ID_PREMIUM_MONTHLY: "PREMIUM",
            settings.PADDLE_PRICE_ID_PREMIUM_ANNUAL: "PREMIUM",
            settings.PADDLE_PRICE_ID_ENTERPRISE_SMALL: "ENTERPRISE",
            settings.PADDLE_PRICE_ID_ENTERPRISE_MEDIUM: "ENTERPRISE",
            settings.PADDLE_PRICE_ID_ENTERPRISE_LARGE: "ENTERPRISE"
        }
        return price_plan_map.get(price_id, "FREE")

    async def _send_subscription_email(self, user: User, email_type: str, plan: str = None):
        """Send subscription-related emails"""
        try:
            if email_type == "welcome":
                subject = f"Welcome to Envoyou {plan} Plan!"
                template_data = {
                    "user_name": user.name or user.email,
                    "plan": plan,
                    "login_url": f"{settings.APP_DOMAIN}/auth/login"
                }
                await self.email_service.send_template_email(
                    user.email,
                    subject,
                    "subscription_welcome",
                    template_data
                )
            elif email_type == "cancellation":
                subject = "Your Envoyou Subscription Has Been Cancelled"
                template_data = {
                    "user_name": user.name or user.email,
                    "support_email": settings.SUPPORT_EMAIL
                }
                await self.email_service.send_template_email(
                    user.email,
                    subject,
                    "subscription_cancelled",
                    template_data
                )

        except Exception as e:
            logger.error(f"Error sending {email_type} email: {str(e)}")

    async def get_customer_subscriptions(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all subscriptions for a customer"""
        try:
            if PADDLE_SDK_AVAILABLE and self.client:
                subscriptions = self.client.subscriptions.list(customer_id=customer_id)
                return [{
                    "id": sub.id,
                    "status": sub.status,
                    "product_id": sub.product_id,
                    "price_id": sub.price_id,
                    "currency": sub.currency_code,
                    "next_billing_date": getattr(sub, 'next_billing_date', None)
                } for sub in subscriptions]
            else:
                url = f"https://api.paddle.com/subscriptions"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                params = {"customer_id": customer_id}

                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()

                result = response.json()
                return [{
                    "id": sub["id"],
                    "status": sub["status"],
                    "product_id": sub["product_id"],
                    "price_id": sub["price_id"],
                    "currency": sub["currency_code"],
                    "next_billing_date": sub.get("next_billing_date")
                } for sub in result["data"]]

        except Exception as e:
            logger.error(f"Error getting customer subscriptions: {str(e)}")
            return []
