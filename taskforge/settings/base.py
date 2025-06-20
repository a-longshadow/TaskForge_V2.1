import os
from pathlib import Path

# Try to import decouple, but fall back to os.environ if not available
try:
    from decouple import config
except ImportError:
    def config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            if cast == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            return cast(value)
        return value

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Guardian Integration
GUARDIAN_ENABLED = True
GUARDIAN_KNOWLEDGE_DIR = BASE_DIR / '.ai-knowledge'

# Security
SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-your-secret-key-here')
DEBUG = config('DEBUG', default=True, cast=bool)
# ALLOWED_HOSTS - Following Railway tutorial approach
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'taskforge-web-production-d175.up.railway.app',  # Railway domain
]

# CSRF_TRUSTED_ORIGINS - Following Railway tutorial approach
CSRF_TRUSTED_ORIGINS = [
    'https://taskforge-web-production-d175.up.railway.app',  # Railway secure URL
]

# Django Apps
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'django_celery_beat',
    'django_celery_results',
]

# Only include core app for Phase 2
LOCAL_APPS = [
    'apps.core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.HealthCheckMiddleware',
    'apps.core.middleware.GuardianMiddleware',
]

ROOT_URLCONF = 'taskforge.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.guardian_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'taskforge.wsgi.application'

# Database - Following Railway tutorial approach
# Use DATABASE_URL when ENVIRONMENT=production or POSTGRES_LOCALLY=true
if config('ENVIRONMENT', default='development') == 'production' or config('POSTGRES_LOCALLY', default=False, cast=bool):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            conn_max_age=600,
        )
    }
else:
    # Local development database
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DATABASE_NAME', default='taskforge'),
            'USER': config('DATABASE_USER', default='joe'),
            'PASSWORD': config('DATABASE_PASSWORD', default=''),
            'HOST': config('DATABASE_HOST', default='localhost'),
            'PORT': config('DATABASE_PORT', default='5432'),
            'OPTIONS': {
                'connect_timeout': 20,
            },
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOG_ROOT = BASE_DIR / 'logs'
LOG_ROOT.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'cache': {
            'format': '[CACHE] {asctime} {levelname} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_ROOT / 'django.log'),
            'maxBytes': 1024*1024*50,  # 50 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'cache_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_ROOT / 'cache' / 'cache_operations.log'),
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 3,
            'formatter': 'cache',
        },
        'fireflies_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_ROOT / 'cache' / 'fireflies_cache.log'),
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 3,
            'formatter': 'cache',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps.core.fireflies_client': {
            'handlers': ['console', 'fireflies_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.core.cache': {
            'handlers': ['cache_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'cache_operations': {
            'handlers': ['cache_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Cache Configuration - Django Best Practices
CACHE_ROOT = BASE_DIR / 'cache'
CACHE_ROOT.mkdir(exist_ok=True)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHE_ROOT / 'django_cache'),
        'TIMEOUT': 14400,  # 4 hours default
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
            'CULL_FREQUENCY': 3,  # Remove 1/3 of entries when MAX_ENTRIES reached
        },
    },
    'fireflies': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHE_ROOT / 'fireflies_cache'),
        'TIMEOUT': 14400,  # 4 hours
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 4,
        },
    },
    'gemini': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHE_ROOT / 'gemini_cache'),
        'TIMEOUT': 1800,  # 30 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
            'CULL_FREQUENCY': 3,
        },
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHE_ROOT / 'sessions'),
        'TIMEOUT': 86400,  # 24 hours
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 2,
        },
    },
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Feature Flags
FEATURE_FLAGS = {
    'ENABLE_AI_PROCESSING': True,
    'ENABLE_AUTO_PUSH': True,
    'ENABLE_REAL_TIME_UPDATES': True,
    'ENABLE_ADVANCED_LOGGING': True,
    'ENABLE_CIRCUIT_BREAKER': True,
}

# Health Check Configuration
HEALTH_CHECK = {
    'ENABLED': True,
    'CHECK_DATABASE': True,
    'CHECK_CACHE': True,
    'CHECK_EXTERNAL_APIS': True,
    'TIMEOUT': 10,  # seconds
}

# External APIs (Enhanced with caching and rate limiting)
EXTERNAL_APIS = {
    'FIREFLIES': {
        'BASE_URL': 'https://api.fireflies.ai/graphql',
        'API_KEY': config('FIREFLIES_API_KEY', default=''),
        'FAILOVER_KEY': '3482aac6-8fc3-4109-9ff9-31fef2a458eb',  # Primary failover key
        'SECONDARY_KEY': 'c908d0c7-c4eb-4d7b-a303-3b5673464e2e',  # Secondary failover key (Joe Maina)
        'TIMEOUT': 60,
        'CACHE_TIMEOUT': 14400,  # 4 hours
        'RATE_LIMIT_PER_MINUTE': 20,
        'PAGINATION_SIZE': 50,
        'MAX_PAGES': 10,
        'MIN_REQUEST_INTERVAL': 3.0,
    },
    'GEMINI': {
        'BASE_URL': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
        'API_KEY': config('GEMINI_API_KEY', default='AIzaSyBWArylUmDVmRuASiZMQ6DiI5IDDsG9bfw'),
        'RATE_LIMIT_PER_MINUTE': 15,
        'MIN_REQUEST_INTERVAL': 4.0,
        'CACHE_TIMEOUT': 1800,  # 30 minutes
        'QUOTA_WARNING_THRESHOLD': 80,
        'RETRY_ATTEMPTS': 3,
        'BACKOFF_FACTOR': 2.0,
        'TIMEOUT': 60,
    },
    'MONDAY': {
        'BASE_URL': 'https://api.monday.com/v2',
        'API_KEY': config('MONDAY_API_KEY', default='eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQxNzI1MzIwNiwiYWFpIjoxMSwidWlkIjo2NzYwNTQ5NCwiaWFkIjoiMjAyNS0wNS0xM1QxNDoxNToyNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjY5NTEzNjQsInJnbiI6InVzZTEifQ.PYgTgWyVfMq8-bBQRlCGBBRZFHI0VEGnIgwYjWp-sZM'),
        'BOARD_ID': config('MONDAY_BOARD_ID', default='9212659997'),
        'GROUP_ID': config('MONDAY_GROUP_ID', default='group_mkqyryrz'),
        'TIMEOUT': 30,
        'RETRY_ATTEMPTS': 3,
        'RATE_LIMIT_PER_MINUTE': 30,
        'MIN_REQUEST_INTERVAL': 2.0,
        'QUOTA_WARNING_THRESHOLD': 80,
        'BACKOFF_FACTOR': 2.0,
        'MAX_BACKOFF_TIME': 300,
    },
}

# TaskForge specific settings
SYSTEM_CONFIG = {
    'AUTO_PUSH_HOURS': config('AUTO_PUSH_HOURS', default=18, cast=int),
    'CIRCUIT_BREAKER_FAILURE_THRESHOLD': 5,
    'CIRCUIT_BREAKER_TIMEOUT': 60,
    'HEALTH_CHECK_INTERVAL': 300,  # 5 minutes
}

# Guardian Settings
GUARDIAN_SETTINGS = {
    'KNOWLEDGE_UPDATE_INTERVAL': 300,  # 5 minutes
    'APPROVAL_TIMEOUT': 3600,  # 1 hour
    'BACKUP_RETENTION_DAYS': 30,
    'REGRESSION_CHECK_ENABLED': True,
    'AUTO_KNOWLEDGE_UPDATE': True,
}

# Email Configuration (for notifications)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Development
DEFAULT_FROM_EMAIL = 'noreply@taskforge.com'

# CSRF Protection
CSRF_COOKIE_SECURE = False  # Will be True in production
CSRF_COOKIE_HTTPONLY = True

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Celery Configuration (for Phase 2 - basic setup)
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Cache Key Prefixes
CACHE_KEY_PREFIXES = {
    'FIREFLIES_COMPREHENSIVE': 'fireflies:comprehensive:',
    'FIREFLIES_TODAY': 'fireflies:today:',
    'FIREFLIES_PAGINATION': 'fireflies:pagination:',
    'FIREFLIES_SYNC': 'fireflies:sync:',
    'GEMINI_EXTRACTION': 'gemini:extract:',
    'GEMINI_QUOTA': 'gemini:quota:',
    'MONDAY_DELIVERY': 'monday:delivery:',
    'SYSTEM_HEALTH': 'system:health:',
    'API_STATUS': 'api:status:',
}

# Cache Timeout Settings
CACHE_TIMEOUTS = {
    'FIREFLIES_COMPREHENSIVE': 14400,  # 4 hours
    'FIREFLIES_TODAY': 3600,           # 1 hour
    'GEMINI_EXTRACTION': 1800,         # 30 minutes
    'SYSTEM_HEALTH': 300,              # 5 minutes
    'API_STATUS': 600,                 # 10 minutes
} 