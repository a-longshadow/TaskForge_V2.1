#!/usr/bin/env sh
set -e

# Railway automatically provides PORT environment variable
PORT_ENV=${PORT:-8000}
echo ">>> Railway injected PORT=$PORT_ENV"

# Run Django management commands
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start gunicorn with proper Railway-compatible format
exec gunicorn taskforge.wsgi:application --bind 0.0.0.0:$PORT_ENV --workers 2 --timeout 120 