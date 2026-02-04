"""
Email utilities for verification code management
"""
import logging
import random
import string
import time

logger = logging.getLogger(__name__)


# In-memory storage for verification codes
VERIFICATION_CODES = {}

# Expiration times (seconds)
CODE_EXPIRATION_TIME = 5 * 60  # 5 minutes
RESEND_COOLDOWN_TIME = 60  # 1 minute


def generate_verification_code():
    """Generate 6-digit verification code"""
    return "".join(random.choices(string.digits, k=6))


def store_verification_code(email):
    """Store verification code with timestamp"""
    code = generate_verification_code()
    current_time = time.time()

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
    """Verify code with expiration check"""
    stored_data = VERIFICATION_CODES.get(email)

    if not stored_data:
        return False, "No verification code found for this email"

    current_time = time.time()
    stored_code = stored_data.get("code")
    created_at = stored_data.get("created_at")

    # Check if code expired
    if current_time - created_at > CODE_EXPIRATION_TIME:
        del VERIFICATION_CODES[email]
        return False, "Verification code has expired. Please request a new code."

    # Check if code matches
    if stored_code == code:
        del VERIFICATION_CODES[email]  # Remove after successful verification
        return True, "Code verified successfully"

    return False, "Invalid verification code"


def can_resend_code(email):
    """Check if user can resend verification code"""
    stored_data = VERIFICATION_CODES.get(email)

    if not stored_data:
        return True, 0  # Can send if no code exists

    current_time = time.time()
    created_at = stored_data.get("created_at")
    resend_at = stored_data.get("resend_at")

    # Check if code expired
    if current_time - created_at > CODE_EXPIRATION_TIME:
        return True, 0  # Can send new code if old one expired

    # If resend_at is None, this is the first code
    if resend_at is None:
        return True, 0  # First send allowed

    # Check resend cooldown
    time_since_resend = current_time - resend_at
    if time_since_resend < RESEND_COOLDOWN_TIME:
        wait_time = int(RESEND_COOLDOWN_TIME - time_since_resend)
        return False, wait_time  

    return True, 0  


def send_verification_email(email, code):
    """Queue verification email via Celery"""
    try:
        from accounts.tasks import send_verification_email_task

        task = send_verification_email_task.delay(email, code)

        logger.info(f"⏳ Verification email queued for {email} (Task ID: {task.id})")
        return True, "Verification email has been queued and will be sent shortly"

    except Exception as e:
        logger.error(f"✗ Failed to queue verification email: {str(e)}")
        return False, f"Failed to queue verification email: {str(e)}"


def send_password_reset_email(user, reset_token, uid):
    """Queue password reset email via Celery"""
    try:
        from accounts.tasks import send_password_reset_email_task

        task = send_password_reset_email_task.delay(
            user.email, user.first_name or "User", reset_token, uid
        )

        logger.info(
            f"⏳ Password reset email queued for {user.email} (Task ID: {task.id})"
        )
        return True, "Password reset email has been queued and will be sent shortly"

    except Exception as e:
        logger.error(f"✗ Failed to queue password reset email: {str(e)}")
        return False, f"Failed to queue password reset email: {str(e)}"


def send_welcome_email(email, first_name):
    """Queue welcome email via Celery"""
    try:
        from accounts.tasks import send_welcome_email_task

        task = send_welcome_email_task.delay(email, first_name)

        logger.info(f"⏳ Welcome email queued for {email} (Task ID: {task.id})")
        return True, "Welcome email has been queued and will be sent shortly"

    except Exception as e:
        logger.error(f"✗ Failed to queue welcome email: {str(e)}")
        return False, f"Failed to queue welcome email: {str(e)}"
