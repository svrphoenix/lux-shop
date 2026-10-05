from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from apps.core.emails import send_templated_email

if TYPE_CHECKING:
    from apps.users.models import User
else:
    User = get_user_model()


def send_password_reset_email(
    user: User, reset_url: str, lang: str | None = None
) -> bool:
    """Send a password reset email using core email infrastructure."""
    context = {
        "user": user,
        "reset_url": reset_url,
    }
    user_email: str = getattr(user, "email", "")

    return send_templated_email(
        template_prefix="password_reset",
        recipient=user_email,
        context=context,
        lang=lang,
        recipient_kind=f"user_{user.pk}",
    )
