import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Guardian Integration
GUARDIAN_ENABLED = True
GUARDIAN_KNOWLEDGE_DIR = BASE_DIR / '.ai-knowledge'

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']  # Will be restricted in production

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

# Database - SQLite for Phase 2 development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'guardian': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery Configuration (for Phase 2 - basic setup)
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# External APIs (placeholders for Phase 2)
EXTERNAL_APIS = {
    'FIREFLIES': {
        'BASE_URL': 'https://api.fireflies.ai/graphql',
        'API_KEY': config('FIREFLIES_API_KEY', default=''),
        'TIMEOUT': 30,
    },
    'GEMINI': {
        'API_KEY': config('GEMINI_API_KEY', default=''),
        'MODEL': 'gemini-pro',
        'TIMEOUT': 30,
    },
    'MONDAY': {
        'BASE_URL': 'https://api.monday.com/v2',
        'API_KEY': config('MONDAY_API_KEY', default=''),
        'TIMEOUT': 30,
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

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = False  # Will be True in production
SESSION_COOKIE_HTTPONLY = True

# CSRF Protection
CSRF_COOKIE_SECURE = False  # Will be True in production
CSRF_COOKIE_HTTPONLY = True

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