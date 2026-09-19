from .base import *

env_file = BASE_DIR / ".env.dev"
if env_file.exists():
    environ.Env.read_env(env_file)

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
DATABASES = {"default": env.db("DATABASE_URL")}
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
