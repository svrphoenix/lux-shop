from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env_file = BASE_DIR / ".env.dev"
if env_file.exists():
    environ.Env.read_env(env_file)

# noinspection PyUnresolvedReferences,PyUnusedCode
from .base import *
