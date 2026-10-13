from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env_file = BASE_DIR / ".env.dev"
if env_file.exists():
    environ.Env.read_env(env_file)

# noinspection PyUnresolvedReferences,PyUnusedCode
from .base import *
from .email import build_email_settings

_email_settings = build_email_settings(env)
MAILERS = _email_settings["MAILERS"]  # type: ignore[assignment]
DEFAULT_FROM_EMAIL = _email_settings["DEFAULT_FROM_EMAIL"]
SHOP_ADMIN_EMAIL = _email_settings["SHOP_ADMIN_EMAIL"]
