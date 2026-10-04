from typing import TypedDict

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email


class EmailSettings(TypedDict):
    MAILERS: dict[str, dict[str, object]]
    DEFAULT_FROM_EMAIL: str
    SHOP_ADMIN_EMAIL: str


def build_email_settings(env) -> EmailSettings:
    site_name = env("SITE_NAME", default="LuxShop Store").strip() or "LuxShop Store"
    resend_api_key = env("RESEND_API_KEY", default="").strip()
    from_email = env("RESEND_FROM_EMAIL", default="").strip()
    admin_email = env("SHOP_ADMIN_EMAIL", default="").strip()

    mailers: dict[str, dict[str, object]]
    if resend_api_key:
        if not from_email or not admin_email:
            raise ImproperlyConfigured(
                "RESEND_FROM_EMAIL and SHOP_ADMIN_EMAIL must be configured "
                "when RESEND_API_KEY is set."
            )
        for setting_name, address in (
            ("RESEND_FROM_EMAIL", from_email),
            ("SHOP_ADMIN_EMAIL", admin_email),
        ):
            try:
                validate_email(address)
            except ValidationError as error:
                raise ImproperlyConfigured(
                    f"{setting_name} must contain a valid email address."
                ) from error

        mailers = {
            "default": {
                "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
                "OPTIONS": {
                    "host": "smtp.resend.com",
                    "port": 587,
                    "username": "resend",
                    "password": resend_api_key,
                    "use_tls": True,
                    "timeout": 10,
                },
            }
        }
    else:
        mailers = {
            "default": {
                "BACKEND": "django.core.mail.backends.console.EmailBackend",
            }
        }

    if from_email:
        default_from_email = (
            from_email if "<" in from_email else f"{site_name} <{from_email}>"
        )
    else:
        default_from_email = f"{site_name} <webmaster@localhost>"

    return {
        "MAILERS": mailers,
        "DEFAULT_FROM_EMAIL": default_from_email,
        "SHOP_ADMIN_EMAIL": admin_email,
    }
