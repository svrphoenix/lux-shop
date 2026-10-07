#!/bin/sh

set -e

python manage.py migrate --noinput
python manage.py create_superuser_from_env

exec "$@"