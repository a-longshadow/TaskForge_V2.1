#!/usr/bin/env sh
echo ">>> PORT is: '${PORT:-<unset>}'"
echo ">>> All environment variables:"
env | grep -E "(PORT|RAILWAY)" | sort
echo ">>> Starting Django migrations..."
python manage.py migrate --noinput
echo ">>> Collecting static files..."
python manage.py collectstatic --noinput
echo ">>> Starting gunicorn on 0.0.0.0:${PORT:-8000}..."
gunicorn taskforge.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 