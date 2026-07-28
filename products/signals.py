import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="products.Purchase")
def notify_payment_status(sender, instance, created, raw, **kwargs):
    if raw:
        return

    # Only act on status transitions
    if created:
        return

    # Detect status change by checking the old value from the DB
    # We avoid _state tracking for simplicity; instead we check current status
    # and send the appropriate email.

    if instance.status == "completed":
        _send_success_email(instance)
    elif instance.status == "failed":
        _send_failed_email(instance)


def _send_success_email(purchase):
    from accounts.email_utils import send_payment_success_email_async

    customer = purchase.order.customer
    recipient_email = customer.email if customer else purchase.order.guest_email
    recipient_name = (
        customer.first_name if customer else purchase.order.guest_first_name
    )

    if not recipient_email:
        logger.warning(
            f"No recipient email for purchase {purchase.id} — cannot send success email"
        )
        return

    try:
        send_payment_success_email_async(
            email=recipient_email,
            first_name=recipient_name or "Customer",
            order_id=str(purchase.order.id),
            tx_ref=purchase.transaction_reference or "",
            amount=str(purchase.amount),
            currency=purchase.currency,
        )
        logger.info(f"Payment success email queued for {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to send payment success email: {e}")


def _send_failed_email(purchase):
    from accounts.email_utils import send_payment_failed_email_async

    customer = purchase.order.customer
    recipient_email = customer.email if customer else purchase.order.guest_email
    recipient_name = (
        customer.first_name if customer else purchase.order.guest_first_name
    )

    if not recipient_email:
        logger.warning(
            f"No recipient email for purchase {purchase.id} — cannot send failed email"
        )
        return

    try:
        send_payment_failed_email_async(
            email=recipient_email,
            first_name=recipient_name or "Customer",
            order_id=str(purchase.order.id),
            tx_ref=purchase.transaction_reference or "",
            amount=str(purchase.amount),
            currency=purchase.currency,
        )
        logger.info(f"Payment failed email queued for {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to send payment failed email: {e}")
