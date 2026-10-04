import logging
import smtplib

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.orders.models import Order

logger = logging.getLogger(__name__)


def get_language(lang: str | None) -> str:
    """Resolve valid language code or fallback to default."""
    if lang:
        clean_lang = lang.split("-")[0].lower()
        if clean_lang in settings.SUPPORTED_LANGUAGES:
            return clean_lang
    return settings.DEFAULT_LANGUAGE


def render_email(
    template_prefix: str, lang: str | None, context: dict
) -> tuple[str, str]:
    """Render subject and body for a given template and language."""
    language = get_language(lang)
    email_context = {
        "site_name": settings.SITE_NAME,
        **context,
    }
    subject = render_to_string(
        f"emails/{language}/{template_prefix}_subject.txt", email_context
    ).strip()
    body = render_to_string(f"emails/{language}/{template_prefix}.txt", email_context)
    return subject, body


def send_order_emails(order: Order) -> None:
    """Send an order confirmation and a shop notification independently."""
    context = {"order": order}

    cust_subject, cust_body = render_email(
        "order_customer", getattr(order, "language", None), context
    )
    admin_subject, admin_body = render_email(
        "order_admin", settings.DEFAULT_LANGUAGE, context
    )

    messages = (
        (order.customer_email, cust_subject, cust_body, "customer"),
        (settings.SHOP_ADMIN_EMAIL, admin_subject, admin_body, "admin"),
    )

    for recipient, subject, body, recipient_kind in messages:
        if not recipient:
            logger.error(
                "Cannot send %s notification for order %s: recipient is not configured.",
                recipient_kind,
                order.order_number,
            )
            continue

        try:
            sent_count = send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
            )
        except (OSError, smtplib.SMTPException):
            logger.exception(
                "Could not send %s notification for order %s to %s.",
                recipient_kind,
                order.order_number,
                recipient,
            )
            continue

        if sent_count != 1:
            logger.error(
                "Email backend did not send %s notification for order %s to %s.",
                recipient_kind,
                order.order_number,
                recipient,
            )
