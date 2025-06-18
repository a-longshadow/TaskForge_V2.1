from .base import *

# Development-specific settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - Using PostgreSQL from base.py (production-ready)

# Override cache settings for development - use file-based but with shorter timeouts
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHE_ROOT / 'dev_django_cache'),
        'TIMEOUT': 3600,  # 1 hour in development
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        },
    },
    'fireflies': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHE_ROOT / 'dev_fireflies_cache'),
        'TIMEOUT': 1800,  # 30 minutes in development
        'OPTIONS': {
            'MAX_ENTRIES': 100,
            'CULL_FREQUENCY': 4,
        },
    },
    'gemini': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHE_ROOT / 'dev_gemini_cache'),
        'TIMEOUT': 900,  # 15 minutes in development
        'OPTIONS': {
            'MAX_ENTRIES': 500,
            'CULL_FREQUENCY': 3,
        },
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHE_ROOT / 'dev_sessions'),
        'TIMEOUT': 3600,  # 1 hour in development
        'OPTIONS': {
            'MAX_ENTRIES': 100,
            'CULL_FREQUENCY': 2,
        },
    },
}

# Celery - in-memory for development
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Email - console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Security - relaxed for development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Development tools (add when needed)
# INSTALLED_APPS += [
#     'django_extensions',
#     'debug_toolbar',
# ]

# MIDDLEWARE += [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ]

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Guardian settings for development
if 'GUARDIAN_SETTINGS' in globals():
    GUARDIAN_SETTINGS.update({
        'APPROVAL_TIMEOUT': 1800,  # 30 minutes in development
        'AUTO_KNOWLEDGE_UPDATE': True,
        'REGRESSION_CHECK_ENABLED': True,
    })

# Development logging - override specific loggers for more verbose output
LOGGING['loggers']['apps.core.fireflies_client']['level'] = 'DEBUG'
LOGGING['loggers']['cache_operations']['level'] = 'DEBUG'

# Add console handler to cache operations for development
LOGGING['loggers']['cache_operations']['handlers'] = ['console', 'cache_file']

# Development cache timeouts (shorter for faster iteration)
CACHE_TIMEOUTS.update({
    'FIREFLIES_COMPREHENSIVE': 1800,  # 30 minutes in development
    'FIREFLIES_TODAY': 900,           # 15 minutes in development
    'GEMINI_EXTRACTION': 600,         # 10 minutes in development
    'SYSTEM_HEALTH': 60,              # 1 minute in development
    'API_STATUS': 120,                # 2 minutes in development
}) 