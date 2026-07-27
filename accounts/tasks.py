import logging

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.signing import TimestampSigner
from django.template.loader import render_to_string

from accounts.models import CustomUser

logger = logging.getLogger(__name__)
signer = TimestampSigner()


def send_verification_email(email, code):
    try:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        token = signer.sign(email)
        verify_link = f"{frontend_url}/verify-email/link?token={token}"

        send_mail(
            subject="Verify your email \u2014 Nexus",
            message=f"""
Hello,

Welcome to Nexus! Please verify your email address.

Option 1: Click the link below to verify instantly:
{verify_link}

Option 2: Enter the 6-digit code on the verification page:
Code: {code}

This code and link will expire in 5 minutes.

If you didn't create an account, please ignore this email.

Best regards,
Nexus Team
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info(f"Verification email sent to {email}")
        return {
            "status": "success",
            "message": f"Verification email sent to {email}",
            "email": email,
        }

    except Exception as exc:
        logger.error(f"Failed to send verification email to {email}: {str(exc)}")
        return {
            "status": "error",
            "message": f"Failed to send verification email: {str(exc)}",
        }


def send_password_reset_email(user_email, user_first_name, reset_token, uid):
    try:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?uid={uid}&token={reset_token}"

        send_mail(
            subject="Password Reset Request",
            message=f"""
Hello {user_first_name},

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
            recipient_list=[user_email],
            fail_silently=False,
        )

        logger.info(f"Password reset email sent to {user_email}")
        return {
            "status": "success",
            "message": f"Password reset email sent to {user_email}",
            "email": user_email,
        }

    except Exception as exc:
        logger.error(f"Failed to send password reset email to {user_email}: {str(exc)}")
        return {
            "status": "error",
            "message": f"Failed to send password reset email: {str(exc)}",
        }


def send_welcome_email(user_email, user_first_name):
    try:
        send_mail(
            subject="Welcome to Your Best shop!",
            message=f"""
Hello {user_first_name},

Welcome to our E-commerce shop! We're excited to have you on board.

Your account is now active and ready to use.

Best regards,
Ulrich - alx-project nexus
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )

        logger.info(f"Welcome email sent to {user_email}")
        return {
            "status": "success",
            "message": f"Welcome email sent to {user_email}",
            "email": user_email,
        }

    except Exception as exc:
        logger.error(f"Failed to send welcome email to {user_email}: {str(exc)}")
        return {
            "status": "error",
            "message": f"Failed to send welcome email: {str(exc)}",
        }


# Payment event emails

def send_payment_attempt_email(email, first_name, order_id, amount, currency, checkout_url):
    try:
        send_mail(
            subject="Payment Initiated \u2014 Nexus",
            message=f"""
Hello {first_name},

We have received your payment request.

Order ID: {order_id}
Amount: {amount} {currency}

Please complete your payment using the secure checkout link below:
{checkout_url}

If you didn't initiate this payment, please ignore this email.

Best regards,
Nexus Team
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Payment attempt email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send payment attempt email: {str(e)}")


def send_payment_success_email(email, first_name, order_id, tx_ref, amount, currency):
    try:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        order_link = f"{frontend_url}/orders/{order_id}"

        send_mail(
            subject="Payment Successful \u2014 Nexus",
            message=f"""
Hello {first_name},

Your payment was successful!

Transaction Reference: {tx_ref}
Order ID: {order_id}
Amount Paid: {amount} {currency}

View your order details here:
{order_link}

Your order is being processed and you will receive a shipping confirmation soon.

Thank you for shopping with us!

Best regards,
Nexus Team
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Payment success email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send payment success email: {str(e)}")


def send_payment_failed_email(email, first_name, order_id, tx_ref, amount, currency):
    try:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        retry_link = f"{frontend_url}/orders/{order_id}"

        send_mail(
            subject="Payment Failed \u2014 Nexus",
            message=f"""
Hello {first_name},

Unfortunately, your payment could not be completed.

Transaction Reference: {tx_ref}
Order ID: {order_id}
Amount: {amount} {currency}

What you can do:
1. Check your card details and try again
2. Use a different payment method
3. Contact your bank if the issue persists

You can retry or view your order here:
{retry_link}

If you need assistance, please contact our support team.

Best regards,
Nexus Team
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Payment failed email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send payment failed email: {str(e)}")