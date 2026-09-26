from django.core.exceptions import ImproperlyConfigured

from .base import *

test_env_file = BASE_DIR / ".env.test"
if test_env_file.exists():
    environ.Env.read_env(test_env_file)

DEBUG = False
SECRET_KEY = env("TEST_SECRET_KEY", default="test-secret-key")
TEST_DATABASE_URL = env("TEST_DATABASE_URL", default="")
if not TEST_DATABASE_URL.startswith(("postgres://", "postgresql://")):
    raise ImproperlyConfigured("TEST_DATABASE_URL must point to a PostgreSQL database.")

DATABASES = {"default": env.db("TEST_DATABASE_URL")}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
