#!/usr/bin/env python
"""
Minimal Django test for Railway health check debugging
Run this to bypass all complex app logic and test Railway basics
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set minimal Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minimal_settings')

# Minimal settings module
import django
from django.conf import settings
from django.http import HttpResponse
from django.urls import path
from django.core.wsgi import get_wsgi_application

# Configure minimal Django
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='minimal-test-key-for-railway-debugging',
        ALLOWED_HOSTS=['*'],  # Allow all hosts
        ROOT_URLCONF=__name__,
        USE_TZ=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',  # In-memory SQLite - no external deps
            }
        },
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
        ],
    )

django.setup()

# Minimal URL patterns
def health_view(request):
    port = os.environ.get('PORT', 'unknown')
    return HttpResponse(f"OK - Railway PORT: {port}")

def debug_view(request):
    return HttpResponse(f"""
DEBUG INFO:
PORT: {os.environ.get('PORT', 'NOT_SET')}
HOST: {request.get_host()}
PATH: {request.path}
METHOD: {request.method}
HEADERS: {dict(request.headers)}
""")

urlpatterns = [
    path('health/', health_view),
    path('debug/', debug_view),
]

# WSGI application
application = get_wsgi_application()

if __name__ == '__main__':
    # For local testing
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000']) 