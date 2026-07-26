import logging
import random
import string
import time
from threading import Lock

logger = logging.getLogger(__name__)

VERIFICATION_CODES = {}
_CODE_LOCK = Lock()

CODE_EXPIRATION_TIME = 5 * 60  # 5 minutes
RESEND_COOLDOWN_TIME = 60  # 1 minute


def generate_verification_code():
    return "".join(random.choices(string.digits, k=6))


def store_verification_code(email):
    code = generate_verification_code()
    current_time = time.time()

    with _CODE_LOCK:
        if email in VERIFICATION_CODES:
            VERIFICATION_CODES[email]["code"] = code
            VERIFICATION_CODES[email]["resend_at"] = current_time
        else:
            VERIFICATION_CODES[email] = {
                "code": code,
                "created_at": current_time,
                "resend_at": None,
            }
    return code


def verify_code(email, code):
    with _CODE_LOCK:
        stored_data = VERIFICATION_CODES.get(email)

    if not stored_data:
        return False, "No verification code found for this email"

    current_time = time.time()
    stored_code = stored_data.get("code")
    created_at = stored_data.get("created_at")

    if current_time - created_at > CODE_EXPIRATION_TIME:
        with _CODE_LOCK:
            VERIFICATION_CODES.pop(email, None)
        return False, "Verification code has expired. Please request a new code."

    if stored_code == code:
        with _CODE_LOCK:
            VERIFICATION_CODES.pop(email, None)
        return True, "Code verified successfully"

    return False, "Invalid verification code"


def can_resend_code(email):
    with _CODE_LOCK:
        stored_data = VERIFICATION_CODES.get(email)

    if not stored_data:
        return True, 0

    current_time = time.time()
    created_at = stored_data.get("created_at")
    resend_at = stored_data.get("resend_at")

    if current_time - created_at > CODE_EXPIRATION_TIME:
        with _CODE_LOCK:
            VERIFICATION_CODES.pop(email, None)
        return True, 0

    if resend_at is None:
        return True, 0

    time_since_resend = current_time - resend_at
    if time_since_resend < RESEND_COOLDOWN_TIME:
        wait_time = int(RESEND_COOLDOWN_TIME - time_since_resend)
        return False, wait_time

    return True, 0


def send_verification_email(email, code):
    try:
        import smtplib
        from email.mime.text import MIMEText

        from django.conf import settings

        msg = MIMEText(
            "\n".join(
                [
                    "Hello,",
                    "",
                    f"Your email verification code is: {code}",
                    "",
                    "This code will expire in 5 minutes.",
                    "",
                    "If you didn't request this, please ignore this email.",
                    "",
                    "Best regards,",
                    "Ulrich E-Commerce Team",
                ]
            )
        )
        msg["Subject"] = "Email Verification Code"
        msg["From"] = settings.DEFAULT_FROM_EMAIL
        msg["To"] = email

        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(settings.DEFAULT_FROM_EMAIL, [email], msg.as_string())
        server.quit()

        logger.info(f"Verification email sent to {email}")
        return True, "Verification email sent"

    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False, f"Failed to send verification email: {str(e)}"


def send_password_reset_email(user, reset_token, uid):
    try:
        from django.conf import settings
        from django.core.mail import send_mail

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?uid={uid}&token={reset_token}"

        send_mail(
            subject="Password Reset Request",
            message=f"""
Hello {user.first_name or 'User'},

We received a request to reset your password.
Click the link below to create a new password:

{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.
Your password will remain unchanged.

Best regards,
Ulrich E-Commerce Team
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Password reset email sent to {user.email}")
        return True, "Password reset email sent successfully"

    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return False, f"Failed to send password reset email: {str(e)}"


def send_welcome_email(email, first_name):
    try:
        from django.conf import settings
        from django.core.mail import send_mail

        send_mail(
            subject="Welcome to Your Best shop!",
            message=f"""
Hello {first_name},

Welcome to our E-commerce shop! We're excited to have you on board.

Your account is now active and ready to use.

Best regards,
Ulrich - alx-project nexus
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info(f"Welcome email sent to {email}")
        return True, "Welcome email sent successfully"

    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False, f"Failed to send welcome email: {str(e)}"
