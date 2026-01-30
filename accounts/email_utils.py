"""
Email utilities for verification code management
Delegates actual email sending to Celery background tasks
"""
import random
import string
import time
import logging

logger = logging.getLogger(__name__)


# In-memory storage for verification codes with timestamps
# Format: {email: {'code': '123456', 'created_at': timestamp, 'resend_at': timestamp}}
VERIFICATION_CODES = {}

# Configuration (in seconds)
CODE_EXPIRATION_TIME = 5 * 60  # 5 minutes
RESEND_COOLDOWN_TIME = 60  # 1 minute


def generate_verification_code():
    """Generate a 6-digit random verification code"""
    return ''.join(random.choices(string.digits, k=6))


def store_verification_code(email):
    """Generate and store a verification code for an email with timestamp"""
    code = generate_verification_code()
    current_time = time.time()
    
    # If code already exists, update resend_at to track resend attempts
    if email in VERIFICATION_CODES:
        VERIFICATION_CODES[email]['code'] = code
        VERIFICATION_CODES[email]['resend_at'] = current_time
    else:
        # New code, don't set resend_at yet (first send allowed immediately)
        VERIFICATION_CODES[email] = {
            'code': code,
            'created_at': current_time,
            'resend_at': None
        }
    return code


def verify_code(email, code):
    """Verify the code for an email with expiration check"""
    stored_data = VERIFICATION_CODES.get(email)
    
    if not stored_data:
        return False, "No verification code found for this email"
    
    current_time = time.time()
    stored_code = stored_data.get('code')
    created_at = stored_data.get('created_at')
    
    # Check if code has expired (5 minutes)
    if current_time - created_at > CODE_EXPIRATION_TIME:
        del VERIFICATION_CODES[email]
        return False, "Verification code has expired. Please request a new code."
    
    # Check if code matches
    if stored_code == code:
        del VERIFICATION_CODES[email]  # Remove code after successful verification
        return True, "Code verified successfully"
    
    return False, "Invalid verification code"


def can_resend_code(email):
    """Check if user can resend verification code (cooldown: 1 minute after first resend)"""
    stored_data = VERIFICATION_CODES.get(email)
    
    if not stored_data:
        return True, 0  # Can send if no code exists
    
    current_time = time.time()
    created_at = stored_data.get('created_at')
    resend_at = stored_data.get('resend_at')
    
    # Check if code has expired (5 minutes)
    if current_time - created_at > CODE_EXPIRATION_TIME:
        return True, 0  # Can send new code if old one expired
    
    # If resend_at is None, this is the first code (no resend yet)
    if resend_at is None:
        return True, 0  # First send allowed
    
    # Check resend cooldown (1 minute between resends)
    time_since_resend = current_time - resend_at
    if time_since_resend < RESEND_COOLDOWN_TIME:
        wait_time = int(RESEND_COOLDOWN_TIME - time_since_resend)
        return False, wait_time  # Cannot resend, return wait time
    
    return True, 0  # Can resend


def send_verification_email(email, code):
    """
    Queue verification email to be sent via Celery background task
    Does not block the request - email is sent asynchronously
    
    Args:
        email (str): User's email address
        code (str): 6-digit verification code
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Import here to avoid circular imports
        from accounts.tasks import send_verification_email_task
        
        # Queue the task - returns immediately without waiting
        task = send_verification_email_task.delay(email, code)
        
        logger.info(f"⏳ Verification email queued for {email} (Task ID: {task.id})")
        return True, "Verification email has been queued and will be sent shortly"
        
    except Exception as e:
        logger.error(f"✗ Failed to queue verification email: {str(e)}")
        return False, f"Failed to queue verification email: {str(e)}"


def send_password_reset_email(user, reset_token, uid):
    """
    Queue password reset email to be sent via Celery background task
    Does not block the request - email is sent asynchronously
    
    Args:
        user: User object with email and first_name
        reset_token (str): Password reset token
        uid (str): Encoded user ID for reset link
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Import here to avoid circular imports
        from accounts.tasks import send_password_reset_email_task
        
        # Queue the task - returns immediately without waiting
        task = send_password_reset_email_task.delay(
            user.email,
            user.first_name or "User",
            reset_token,
            uid
        )
        
        logger.info(f"⏳ Password reset email queued for {user.email} (Task ID: {task.id})")
        return True, "Password reset email has been queued and will be sent shortly"
        
    except Exception as e:
        logger.error(f"✗ Failed to queue password reset email: {str(e)}")
        return False, f"Failed to queue password reset email: {str(e)}"


def send_welcome_email(email, first_name):
    """
    Queue welcome email to be sent via Celery background task
    Does not block the request - email is sent asynchronously
    
    Args:
        email (str): User's email address
        first_name (str): User's first name
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Import here to avoid circular imports
        from accounts.tasks import send_welcome_email_task
        
        # Queue the task - returns immediately without waiting
        task = send_welcome_email_task.delay(email, first_name)
        
        logger.info(f"⏳ Welcome email queued for {email} (Task ID: {task.id})")
        return True, "Welcome email has been queued and will be sent shortly"
        
    except Exception as e:
        logger.error(f"✗ Failed to queue welcome email: {str(e)}")
        return False, f"Failed to queue welcome email: {str(e)}"

