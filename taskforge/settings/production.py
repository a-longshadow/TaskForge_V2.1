from .base import *
import os

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['*']  # Allow all hosts for Railway deployment testing

# Security settings for production - simplified for Railway
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-testing')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Database - Railway provides DATABASE_URL automatically
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ['DATABASE_URL'])
    }
    DATABASES['default']['CONN_MAX_AGE'] = 600
else:
    # Fallback for manual configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'taskforge'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': 'require',
            },
            'CONN_MAX_AGE': 600,
        }
    }

# Cache - CRITICAL FIX: Add sessions cache backend
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Session configuration - use database instead of cache for Railway
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 hours

# Static files - WhiteNoise for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging - simplified for Railway
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# API Keys - required for functionality
FIREFLIES_API_KEY = os.environ.get('FIREFLIES_API_KEY', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
MONDAY_API_KEY = os.environ.get('MONDAY_API_KEY', '')
MONDAY_BOARD_ID = os.environ.get('MONDAY_BOARD_ID', '')
MONDAY_GROUP_ID = os.environ.get('MONDAY_GROUP_ID', '')

# Celery - only if Redis is available
REDIS_URL = os.environ.get('REDIS_URL', '')
if REDIS_URL:
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
else:
    # Disable Celery if no Redis
    CELERY_TASK_ALWAYS_EAGER = True

# Email settings - optional for Railway
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Console for testing
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Guardian settings - simplified for Railway
GUARDIAN_SETTINGS = {
    'APPROVAL_TIMEOUT': 7200,  # 2 hours in production
    'AUTO_KNOWLEDGE_UPDATE': True,
    'REGRESSION_CHECK_ENABLED': True,
    'BACKUP_RETENTION_DAYS': 90,  # 3 months in production
}

# Feature flags - production configuration
FEATURE_FLAGS = {
    'ENABLE_DEBUG_TOOLBAR': False,
    'ENABLE_EXTENSIONS': False,
    'ENABLE_PRODUCTION_MONITORING': True,
}

# Performance optimizations
CONN_MAX_AGE = 600  # 10 minutes
DATABASES['default']['CONN_MAX_AGE'] = CONN_MAX_AGE 