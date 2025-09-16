"""
Background Task Processor
Processes Redis queues for email notifications and other background tasks
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any
import json

from app.services.redis_service import redis_service
from app.config import settings

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Background task processor using Redis queues"""

    def __init__(self):
        self.running = False
        self.tasks = {
            "email_queue": self._process_email_task,
            "paddle_queue": self._process_paddle_task,
        }

    def start(self):
        """Start the task processor"""
        self.running = True
        logger.info("🚀 Starting background task processor...")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            asyncio.run(self._run_processor())
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self._shutdown()

    def stop(self):
        """Stop the task processor"""
        logger.info("🛑 Stopping background task processor...")
        self.running = False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.stop()

    def _shutdown(self):
        """Cleanup on shutdown"""
        logger.info("✅ Background task processor stopped")

    async def _run_processor(self):
        """Main processor loop"""
        while self.running:
            try:
                # Process all queues
                for queue_name, processor_func in self.tasks.items():
                    await self._process_queue(queue_name, processor_func)

                # Sleep for a short time before checking again
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in processor loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def _process_queue(self, queue_name: str, processor_func):
        """Process tasks from a specific queue"""
        try:
            # Get queue length
            queue_length = redis_service.get_queue_length(queue_name)
            if queue_length > 0:
                logger.debug(f"Processing {queue_length} tasks in {queue_name}")

            # Process up to 10 tasks at a time to avoid blocking
            for _ in range(min(10, queue_length)):
                if not self.running:
                    break

                task_data = redis_service.dequeue_task(queue_name)
                if task_data:
                    try:
                        await processor_func(task_data)
                    except Exception as e:
                        logger.error(f"Error processing task from {queue_name}: {e}")
                        # Re-queue failed task (with retry limit)
                        if task_data.get('retry_count', 0) < 3:
                            task_data['retry_count'] = task_data.get('retry_count', 0) + 1
                            redis_service.queue_task(queue_name, task_data)
                            logger.info(f"Re-queued failed task (retry {task_data['retry_count']})")

        except Exception as e:
            logger.error(f"Error processing queue {queue_name}: {e}")

    async def _process_email_task(self, task_data: Dict[str, Any]):
        """Process email sending task"""
        task_type = task_data.get('type')

        if task_type == 'send_email':
            await self._send_email(
                to_email=task_data['to_email'],
                subject=task_data['subject'],
                body=task_data['body'],
                template_data=task_data.get('template_data', {})
            )
        elif task_type == 'send_notification_email':
            await self._send_notification_email(
                user_id=task_data['user_id'],
                template_key=task_data['template_key'],
                template_data=task_data.get('template_data', {})
            )
        else:
            logger.warning(f"Unknown email task type: {task_type}")

    async def _process_paddle_task(self, task_data: Dict[str, Any]):
        """Process Paddle webhook task"""
        task_type = task_data.get('type')

        if task_type == 'process_paddle_webhook':
            await self._process_paddle_webhook(task_data['webhook_data'])
        else:
            logger.warning(f"Unknown Paddle task type: {task_type}")

    async def _send_email(self, to_email: str, subject: str, body: str, template_data: Dict[str, Any]):
        """Send email using Mailgun"""
        try:
            # Import here to avoid circular imports
            from app.services.email_service import EmailService

            email_service = EmailService()
            success = await email_service.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                template_data=template_data
            )

            if success:
                logger.info(f"✅ Email sent to {to_email}: {subject}")
            else:
                logger.error(f"❌ Failed to send email to {to_email}: {subject}")

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            raise

    async def _send_notification_email(self, user_id: str, template_key: str, template_data: Dict[str, Any]):
        """Send notification email using template"""
        try:
            # Import here to avoid circular imports
            from app.services.notification_service import NotificationService
            from app.models.database import SessionLocal

            db = SessionLocal()
            try:
                notification_service = NotificationService(db)
                success = await notification_service.send_template_email(
                    user_id=user_id,
                    template_key=template_key,
                    template_data=template_data
                )

                if success:
                    logger.info(f"✅ Notification email sent to user {user_id} with template {template_key}")
                else:
                    logger.error(f"❌ Failed to send notification email to user {user_id}")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error sending notification email to user {user_id}: {e}")
            raise

    async def _process_paddle_webhook(self, webhook_data: Dict[str, Any]):
        """Process Paddle webhook"""
        try:
            # Import here to avoid circular imports
            from app.services.paddle_service import PaddleService

            paddle_service = PaddleService()
            await paddle_service.process_queued_webhook(webhook_data)

            logger.info("✅ Paddle webhook processed successfully")

        except Exception as e:
            logger.error(f"Error processing Paddle webhook: {e}")
            raise


# Global task processor instance
task_processor = TaskProcessor()


if __name__ == "__main__":
    # Run as standalone process
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    task_processor.start()