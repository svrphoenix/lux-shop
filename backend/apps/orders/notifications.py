from django.conf import settings

from apps.core.emails import send_templated_email
from apps.orders.models import Order


def send_order_emails(order: Order, lang: str | None = None) -> None:
    """Send order confirmation to customer and notification to store admin.

    Language resolution priority:
    1. Explicitly passed `lang` argument (e.g., from request/headers).
    2. `order.language` field if/when added to the model in the future.
    3. Default language fallback via `core.emails.get_language()`.
    """
    resolved_lang = lang or getattr(order, "language", None)
    context = {"order": order}

    send_templated_email(
        template_prefix="order_customer",
        recipient=order.customer_email,
        context=context,
        lang=resolved_lang,
        recipient_kind=f"customer_order_{order.order_number}",
    )

    send_templated_email(
        template_prefix="order_admin",
        recipient=settings.SHOP_ADMIN_EMAIL,
        context=context,
        lang=settings.DEFAULT_LANGUAGE,
        recipient_kind=f"admin_order_{order.order_number}",
    )
