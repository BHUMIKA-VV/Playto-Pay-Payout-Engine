#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py seed_merchants
python -m huey_consumer backend.huey_conf.huey &
exec gunicorn backend.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
