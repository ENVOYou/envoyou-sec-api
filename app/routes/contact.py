from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from app.services.email_service import EmailService

router = APIRouter()
logger = logging.getLogger(__name__)

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    inquiry_type: Optional[str] = "general"

@router.post("/contact")
async def submit_contact_form(
    form_data: ContactForm,
    background_tasks: BackgroundTasks
):
    """
    Submit contact form - sends email to support team
    """
    try:
        # Log the contact form submission
        logger.info(f"Contact form submitted by {form_data.name} ({form_data.email}) - Subject: {form_data.subject}")

        # Send email to support team
        email_service = EmailService()

        # Email to support team
        support_subject = f"Envoyou Contact Form: {form_data.subject}"
        support_body = f"""
New contact form submission from Envoyou website:

Name: {form_data.name}
Email: {form_data.email}
Subject: {form_data.subject}
Inquiry Type: {form_data.inquiry_type}

Message:
{form_data.message}

---
This message was sent from the Envoyou contact form.
"""

        # Send to support team
        background_tasks.add_task(
            email_service.send_email,
            to_email="support@envoyou.com",
            subject=support_subject,
            body=support_body
        )

        # Auto-reply to user
        auto_reply_subject = "Thank you for contacting Envoyou"
        auto_reply_body = f"""
Dear {form_data.name},

Thank you for contacting Envoyou! We've received your message regarding "{form_data.subject}".

Our team will review your inquiry and get back to you within 24-48 hours.

For urgent matters, you can also reach us at:
- Email: support@envoyou.com
- Enterprise inquiries: info@envoyou.com

Best regards,
The Envoyou Team
support@envoyou.com
"""

        # Send auto-reply to user
        background_tasks.add_task(
            email_service.send_email,
            to_email=form_data.email,
            subject=auto_reply_subject,
            body=auto_reply_body
        )

        return {
            "status": "success",
            "message": "Your message has been sent successfully. We'll get back to you soon!"
        }

    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send message. Please try again or contact us directly at support@envoyou.com"
        )