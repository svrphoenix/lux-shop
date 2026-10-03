from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

test_env_file = BASE_DIR / ".env.test"
if test_env_file.exists():
    environ.Env.read_env(test_env_file, overwrite=False)

from .base import *

DEBUG = False

if "postgresql" not in DATABASES["default"]["ENGINE"]:
    raise ImproperlyConfigured("DATABASE_URL must point to a PostgreSQL database.")

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
