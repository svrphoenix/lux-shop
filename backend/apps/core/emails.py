import logging
import smtplib
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.request import Request

logger = logging.getLogger(__name__)


def get_language(lang: str | None) -> str:
    """Resolve valid language code or fallback to default."""
    if lang:
        clean_lang = lang.split("-")[0].lower()
        if clean_lang in settings.SUPPORTED_LANGUAGES:
            return clean_lang
    return settings.DEFAULT_LANGUAGE


def render_email(
    template_prefix: str, lang: str | None, context: dict[str, Any]
) -> tuple[str, str]:
    """Render subject and body for a given template prefix and language."""
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


def send_templated_email(
    template_prefix: str,
    recipient: str | None,
    context: dict[str, Any],
    lang: str | None = None,
    recipient_kind: str = "recipient",
) -> bool:
    """Universal wrapper to render and send transactional emails."""
    if not recipient:
        logger.error(
            "Cannot send %s email (%s): recipient address is empty.",
            template_prefix,
            recipient_kind,
        )
        return False

    subject, body = render_email(template_prefix, lang, context)

    try:
        sent_count = send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
        )
        if sent_count != 1:
            logger.error(
                "Email backend did not confirm delivery for %s to %s.",
                template_prefix,
                recipient,
            )
            return False
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception(
            "Failed to send %s email to %s.",
            template_prefix,
            recipient,
        )
        return False


def get_request_language(request: Request | None) -> str | None:
    """Extract language preference from DRF Request object."""
    if not request:
        return None

    lang_from_data = None
    data = request.data
    if isinstance(data, dict):
        lang_from_data = data.get("lang")

    return (
        lang_from_data
        or getattr(request, "LANGUAGE_CODE", None)
        or request.headers.get("Accept-Language")
    )
