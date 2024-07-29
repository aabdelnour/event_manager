#app/services/email_service.py
from app.utils.smtp_connection import SMTPClient
from app.utils.template_manager import TemplateManager
from app.models.user_model import User
from settings.config import get_settings  # Ensure this matches the actual function location
import logging


logger = logging.getLogger(__name__)

settings = get_settings()

class EmailService:
    def __init__(self, template_manager: TemplateManager):
        self.smtp_client = SMTPClient(
            server=settings.smtp_server,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password
        )
        self.template_manager = template_manager

    async def send_user_email(self, user_data: dict, email_type: str):
        subject_map = {
            'email_verification': "Verify Your Account",
            'password_reset': "Password Reset Instructions",
            'account_locked': "Account Locked Notification"
        }
        if email_type not in subject_map:
            raise ValueError("Invalid email type")

        html_content = self.template_manager.render_template(email_type, **user_data)
        try:
            self.smtp_client.send_email(subject_map[email_type], html_content, user_data['email'])
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    async def send_verification_email(self, user: User):
        verification_url = f"{settings.server_base_url}verify-email/{user.id}/{user.verification_token}"
        await self.send_user_email({
            "name": user.first_name or "User",
            "verification_url": verification_url,
            "email": user.email
        }, 'email_verification')
