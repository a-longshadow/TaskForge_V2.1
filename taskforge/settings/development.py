from .base import *

# Development-specific settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - SQLite for Phase 2 development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache - in-memory for Phase 2
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery - in-memory for Phase 2
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

# Development logging
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['guardian']['level'] = 'DEBUG' 