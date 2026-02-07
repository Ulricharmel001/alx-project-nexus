"""
Celery background tasks for email operations
Handles all email sending asynchronously to avoid blocking requests
"""
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email_task(self, email, code):
    """
    Celery task to send verification email asynchronously
    
    Args:
        email (str): User's email address
        code (str): 6-digit verification code
        
    Returns:
        dict: Task result with status and message
        
    Retry Logic:
        - Automatically retries up to 3 times
        - Waits 60 seconds between retries
        - Logs failures for debugging
    """
    try:
        subject = "Email Verification Code"
        message = f"""
Hello,

Your email verification code is: {code}

This code will expire in 5 minutes.

If you didn't request this, please ignore this email.

Best regards,
Ulrich E-Commerce Team
        """
        
        # Send email via SMTP (runs in background worker)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {email}")
        return {
            "status": "success",
            "message": f"Verification email sent to {email}",
            "email": email
        }
        
    except Exception as exc:
        logger.error(f"Failed to send verification email to {email}: {str(exc)}")
    
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_task(self, user_email, user_first_name, reset_token, uid):
    """
    Celery task to send password reset email asynchronously
    
    Args:
        user_email (str): User's email address
        user_first_name (str): User's first name for personalization
        reset_token (str): Password reset token
        uid (str): User ID encoded in base64
        
    Returns:
        dict: Task result with status and message
        
    Retry Logic:
        - Automatically retries up to 3 times
        - Waits 60 seconds between retries
        - Logs failures for debugging
    """
    try:
        # Build reset link from frontend URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?uid={uid}&token={reset_token}"
        
        subject = "Password Reset Request"
        message = f"""
Hello {user_first_name},

We received a request to reset your password. Click the link below to create a new password:

{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
Ulrich E-Commerce Team
        """
        
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        
        logger.info(f"✓ Password reset email sent to {user_email}")
        return {
            "status": "success",
            "message": f"Password reset email sent to {user_email}",
            "email": user_email
        }
        
    except Exception as exc:
        logger.error(f"✗ Failed to send password reset email to {user_email}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_welcome_email_task(self, user_email, user_first_name):
    """
    Celery task to send welcome email to new users asynchronously
    
    Args:
        user_email (str): User's email address
        user_first_name (str): User's first name for personalization
        
    Returns:
        dict: Task result with status and message
    """
    try:
        subject = "Welcome to Your Best shop!"
        message = f"""
Hello {user_first_name},

Welcome to our E-commerce shop ! We're excited to have you on board.

Your account is now active and ready to use.

Best regards,
Ulrich - alx-project nexus
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        
        logger.info(f"✓ Welcome email sent to {user_email}")
        return {
            "status": "success",
            "message": f"Welcome email sent to {user_email}",
            "email": user_email
        }
        
    except Exception as exc:
        logger.error(f"✗ Failed to send welcome email to {user_email}: {str(exc)}")
        raise self.retry(exc=exc)
