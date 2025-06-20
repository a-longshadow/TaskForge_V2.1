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
]

# Security settings for production
SECRET_KEY = config('SECRET_KEY')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = False  # Disabled for Railway deployment
SESSION_COOKIE_SECURE = False  # Disabled for Railway deployment
CSRF_COOKIE_SECURE = False  # Disabled for Railway deployment
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

# Database - use DATABASE_URL from environment
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
            'MAX_CONNECTIONS': 50,
        },
        'CONN_MAX_AGE': 600,  # 10 minutes
    }
}

# Cache - Redis from environment
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'taskforge',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

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

# Static files - WhiteNoise for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging - enhanced for production
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['handlers']['guardian_file']['level'] = 'INFO'
LOGGING['handlers']['celery_file']['level'] = 'WARNING'

# Add production-specific loggers
LOGGING['handlers'].update({
    'error_file': {
        'level': 'ERROR',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': BASE_DIR / 'logs' / 'errors.log',
        'maxBytes': 10485760,  # 10MB
        'backupCount': 5,
        'formatter': 'verbose',
    },
    'security_file': {
        'level': 'WARNING',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': BASE_DIR / 'logs' / 'security.log',
        'maxBytes': 10485760,  # 10MB
        'backupCount': 10,
        'formatter': 'verbose',
    },
})

LOGGING['loggers'].update({
    'django.security': {
        'handlers': ['security_file'],
        'level': 'WARNING',
        'propagate': False,
    },
    'django.request': {
        'handlers': ['error_file'],
        'level': 'ERROR',
        'propagate': False,
    },
})

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

# Render.com specific settings
if 'RENDER' in os.environ:
    ALLOWED_HOSTS.append(os.environ.get('RENDER_EXTERNAL_HOSTNAME'))
    
    # Use Render's database URL if available
    if 'DATABASE_URL' in os.environ:
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL']) 