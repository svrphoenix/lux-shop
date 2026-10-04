from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

test_env_file = BASE_DIR / ".env.test"
if test_env_file.exists():
    environ.Env.read_env(test_env_file, overwrite=False)

from .base import *

DEBUG = False

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgresql://postgres:postgres@127.0.0.1:5433/luxshop_test",
    )
}

if "postgresql" not in DATABASES["default"]["ENGINE"]:
    raise ImproperlyConfigured("DATABASE_URL must point to a PostgreSQL database.")

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    }
}
DEFAULT_FROM_EMAIL = "orders@example.com"
SHOP_ADMIN_EMAIL = "admin@example.com"

NOVA_POSHTA_API_KEY = (
    env("NOVA_POSHTA_API_KEY", default="test-mock-key") or "test-mock-key"
)
NOVA_POSHTA_API_URL = (
    env("NOVA_POSHTA_API_URL", default="https://mock.novaposhta.local/v2.0/json/")
    or "https://mock.novaposhta.local/v2.0/json/"
)
