import logging
import random
import string
import threading
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
    from .tasks import send_verification_email as _send

    try:
        result = _send(email, code)
        if result.get("status") == "success":
            logger.info(f"Verification email sent to {email}")
            return True, "Verification email sent"
        else:
            logger.error(f"Failed to send verification email: {result.get('message')}")
            return False, result.get("message", "Failed to send verification email")
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False, f"Failed to send verification email: {str(e)}"


def send_password_reset_email(user, reset_token, uid):
    from .tasks import send_password_reset_email as _send

    try:
        result = _send(user.email, user.first_name, reset_token, uid)
        if result.get("status") == "success":
            logger.info(f"Password reset email sent to {user.email}")
            return True, "Password reset email sent successfully"
        else:
            logger.error(f"Failed to send password reset email: {result.get('message')}")
            return False, result.get("message", "Failed to send password reset email")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return False, f"Failed to send password reset email: {str(e)}"


def send_welcome_email(email, first_name):
    from .tasks import send_welcome_email

    try:
        result = send_welcome_email(email, first_name)
        if result.get("status") == "success":
            logger.info(f"Welcome email sent to {email}")
            return True, "Welcome email sent successfully"
        else:
            logger.error(f"Failed to send welcome email: {result.get('message')}")
            return False, result.get("message", "Failed to send welcome email")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False, f"Failed to send welcome email: {str(e)}"


# Payment event email helpers

def send_payment_attempt_email(email, first_name, order_id, amount, currency, checkout_url):
    from .tasks import send_payment_attempt_email as _send

    try:
        _send(email, first_name, order_id, amount, currency, checkout_url)
        return True, "Payment attempt email sent"
    except Exception as e:
        logger.error(f"Failed to send payment attempt email: {str(e)}")
        return False, str(e)


def send_payment_success_email(email, first_name, order_id, tx_ref, amount, currency):
    from .tasks import send_payment_success_email as _send

    try:
        _send(email, first_name, order_id, tx_ref, amount, currency)
        return True, "Payment success email sent"
    except Exception as e:
        logger.error(f"Failed to send payment success email: {str(e)}")
        return False, str(e)


def send_payment_failed_email(email, first_name, order_id, tx_ref, amount, currency):
    from .tasks import send_payment_failed_email as _send

    try:
        _send(email, first_name, order_id, tx_ref, amount, currency)
        return True, "Payment failed email sent"
    except Exception as e:
        logger.error(f"Failed to send payment failed email: {str(e)}")
        return False, str(e)