from .base import *
import os

# Production settings
DEBUG = False
ALLOWED_HOSTS = [
    'taskforge-v2-1.onrender.com',
    '.render.com',
    'taskforge.com',
    'www.taskforge.com',
    '.railway.app',
    '.up.railway.app',
    'taskforge-web-production-d175.up.railway.app',
    '*',  # Allow all hosts for Railway deployment
]

# Security settings for production - simplified for Railway
SECRET_KEY = config('SECRET_KEY')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Database - simplified for Railway
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 600,
    }
}

# Cache - simplified Redis configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

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

# Railway-specific settings
if 'RAILWAY_ENVIRONMENT' in os.environ:
    # Railway automatically provides DATABASE_URL
    if 'DATABASE_URL' in os.environ:
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'])
        DATABASES['default']['CONN_MAX_AGE'] = 600

# Celery - Redis from environment
CELERY_BROKER_URL = config('REDIS_URL')
CELERY_RESULT_BACKEND = config('REDIS_URL')

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Guardian settings for production
GUARDIAN_SETTINGS.update({
    'APPROVAL_TIMEOUT': 7200,  # 2 hours in production
    'AUTO_KNOWLEDGE_UPDATE': True,
    'REGRESSION_CHECK_ENABLED': True,
    'BACKUP_RETENTION_DAYS': 90,  # 3 months in production
})

# Feature flags - production configuration
FEATURE_FLAGS.update({
    'ENABLE_DEBUG_TOOLBAR': False,
    'ENABLE_EXTENSIONS': False,
    'ENABLE_PRODUCTION_MONITORING': True,
})

# Performance optimizations
CONN_MAX_AGE = 600  # 10 minutes
DATABASES['default']['CONN_MAX_AGE'] = CONN_MAX_AGE 