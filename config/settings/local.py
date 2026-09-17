from .base import *

DEBUG = True
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Database connection (uri from environment
DATABASES = {"default": env.db("DATABASE_URL")}
# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
