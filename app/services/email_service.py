"""
Email Service
Handles email sending using Mailgun API
"""

import logging
from typing import Dict, Any, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Mailgun API"""

    def __init__(self):
        self.api_key = getattr(settings, 'MAILGUN_API_KEY', None)
        self.domain = getattr(settings, 'MAILGUN_DOMAIN', None)
        self.api_base_url = getattr(settings, 'MAILGUN_API_BASE_URL', 'https://api.mailgun.net')
        self.from_email = getattr(settings, 'EMAIL_FROM', 'noreply@envoyou.com')
        self.from_name = getattr(settings, 'EMAIL_FROM_NAME', 'Envoyou')

        # Check if Mailgun is configured
        if not self.api_key or not self.domain:
            logger.warning("⚠️  Mailgun not configured, email service disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("✅ Mailgun email service initialized")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        template_data: Optional[Dict[str, Any]] = None,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email using Mailgun"""
        if not self.enabled:
            logger.warning("Email service disabled, skipping email send")
            return False

        try:
            # Prepare email data
            email_data = {
                'from': f"{self.from_name} <{self.from_email}>",
                'to': to_email,
                'subject': subject,
            }

            # Add template variables if provided
            if template_data:
                for key, value in template_data.items():
                    email_data[f"v:{key}"] = str(value)

            # Add body content
            if html_body:
                email_data['html'] = html_body
            else:
                email_data['text'] = body

            # Send email via Mailgun API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v3/{self.domain}/messages",
                    auth=('api', self.api_key),
                    data=email_data,
                    timeout=30.0
                )

                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"Email sent successfully: {response_data.get('id', 'unknown')}")
                    return True
                else:
                    logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False

    async def send_template_email(
        self,
        to_email: str,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> bool:
        """Send email using Mailgun template"""
        if not self.enabled:
            logger.warning("Email service disabled, skipping template email send")
            return False

        try:
            # Prepare template data
            email_data = {
                'from': f"{self.from_name} <{self.from_email}>",
                'to': to_email,
                'template': template_name,
            }

            # Add template variables
            for key, value in template_data.items():
                email_data[f"v:{key}"] = str(value)

            # Send email via Mailgun API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v3/{self.domain}/messages",
                    auth=('api', self.api_key),
                    data=email_data,
                    timeout=30.0
                )

                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"Template email sent successfully: {response_data.get('id', 'unknown')}")
                    return True
                else:
                    logger.error(f"Mailgun template API error: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending template email to {to_email}: {e}")
            return False

    async def send_bulk_email(
        self,
        to_emails: list[str],
        subject: str,
        body: str,
        template_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send bulk email to multiple recipients"""
        if not self.enabled:
            logger.warning("Email service disabled, skipping bulk email send")
            return False

        success_count = 0
        total_count = len(to_emails)

        for email in to_emails:
            if await self.send_email(email, subject, body, template_data):
                success_count += 1

        logger.info(f"Bulk email sent: {success_count}/{total_count} successful")
        return success_count == total_count

    def get_email_stats(self) -> Dict[str, Any]:
        """Get email sending statistics (placeholder for future implementation)"""
        return {
            "enabled": self.enabled,
            "provider": "mailgun",
            "domain": self.domain,
            "from_email": self.from_email
        }