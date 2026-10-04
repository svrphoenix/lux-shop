"""
Django settings for config project.
"""

from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Default environment initialization for project
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY.strip():
    raise ImproperlyConfigured("SECRET_KEY must be set to a non-empty value.")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Database settings
DATABASES = {"default": env.db("DATABASE_URL")}

# Frontend & External Links
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

SITE_NAME = env("SITE_NAME", default="LuxShop Store")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "apps.core",
    "apps.users",
    "apps.products",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.reviews",
    "apps.delivery",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
LANGUAGES = [
    ("uk", "Ukrainian"),
    ("en", "English"),
]
# For directories (emails/en/) and frontend
SUPPORTED_LANGUAGES = {code for code, _ in LANGUAGES}
DEFAULT_LANGUAGE = (LANGUAGE_CODE or "en").split("-")[0].lower() or "en"
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Custom User Model
AUTH_USER_MODEL = "users.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "LuxShop Store API",
    "DESCRIPTION": (
        "REST API for the LuxShop store. Authenticate with a JWT access token "
        "using the Bearer authorization scheme."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "PaymentMethodEnum": "apps.payments.models.PaymentMethod.choices",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

CORS_ALLOW_HEADERS = [
    "content-type",
    "authorization",
]

# Email
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

# Third-party Services
NOVA_POSHTA_API_URL = env(
    "NOVA_POSHTA_API_URL", default="https://api.novaposhta.ua/v2.0/json/"
)
NOVA_POSHTA_API_KEY = env("NOVA_POSHTA_API_KEY", default="")
