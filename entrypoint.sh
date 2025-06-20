#!/usr/bin/env sh
echo ">>> PORT is: '${PORT:-<unset>}'"
echo ">>> All environment variables:"
env | grep -E "(PORT|DJANGO|DB_)" | sort
echo ">>> Starting Django..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput
echo ">>> Starting Gunicorn on port ${PORT:-8000}..."
gunicorn taskforge.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 