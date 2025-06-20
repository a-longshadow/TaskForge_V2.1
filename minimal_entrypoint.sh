#!/usr/bin/env sh
set -e

echo "=== RAILWAY DEBUGGING ==="
echo "PORT: ${PORT:-NOT_SET}"
echo "PWD: $(pwd)"
echo "USER: $(whoami)"
echo "ENV VARS:"
env | grep -E "(PORT|RAILWAY|DATABASE)" || echo "No Railway vars found"
echo "=========================="

# Test port binding
PORT_ENV=${PORT:-8000}
echo "Starting gunicorn on 0.0.0.0:$PORT_ENV"

exec gunicorn minimal_test:application \
     --bind 0.0.0.0:$PORT_ENV \
     --workers 1 \
     --access-logfile - \
     --error-logfile - \
     --log-level debug 