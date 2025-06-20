#!/usr/bin/env sh
set -e

PORT_ENV=${PORT:-8000}
echo ">>> Railway injected PORT=$PORT_ENV"

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn taskforge.wsgi:application \
     --bind 0.0.0.0:$PORT_ENV \
     --workers 2 