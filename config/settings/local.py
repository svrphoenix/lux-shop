from .base import *

environ.Env.read_env(BASE_DIR / ".env.local")

# Variables from environment
DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
DATABASES = {"default": env.db("DATABASE_URL")}
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
