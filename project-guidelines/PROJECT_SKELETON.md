# TaskForge Project Skeleton

## Complete Directory Structure

```
TaskForge_V2.1/
├── guardian.sh                           # Guardian system script
├── requirements.txt                      # Python dependencies
├── .python-version                       # Python version (3.11.7)
├── .gitignore                           # Git ignore patterns
├── README.md                            # Project documentation
├── render.yaml                          # Render.com deployment config
├── manage.py                            # Django management script
│
├── .ai-knowledge/                       # Guardian knowledge base
│   ├── PROJECT_STATE.md                 # Complete current state
│   ├── ARCHITECTURE_MAP.md              # System design & relationships
│   ├── API_CONTRACTS.md                 # All external integrations
│   ├── DEPLOYMENT_STATE.md              # Current deploy config & env
│   ├── CHANGE_MANIFEST.md               # Every change with context
│   ├── MODULE_STATUS.md                 # Individual module states
│   └── KNOWLEDGE_TESTS.md               # Validation questions for AI
│
├── project-guidelines/                  # Project guidelines (existing)
│   ├── README.md
│   ├── CORE_ARCHITECTURE.md
│   ├── GUARDIAN_SYSTEM.md
│   ├── MODULAR_DESIGN.md
│   ├── AI_AGENT_PROTOCOLS.md
│   ├── DEPLOYMENT_STRATEGY.md
│   ├── IMPLEMENTATION_PHASES.md
│   ├── PROJECT_SKELETON.md              # This file
│   └── DEVELOPMENT_WORKFLOW.md          # Development workflow
│
├── scripts/                             # Guardian & utility scripts
│   ├── create_snapshot.sh               # Backup creation
│   ├── export_ai_knowledge.sh           # Knowledge export
│   ├── validate_ai_knowledge.sh         # Knowledge validation
│   ├── import_ai_knowledge.sh           # Knowledge import
│   ├── pre_deploy_check.sh              # Pre-deployment validation
│   └── emergency_rollback.sh            # Emergency rollback
│
├── taskforge/                           # Django project root
│   ├── __init__.py
│   ├── wsgi.py                          # WSGI application
│   ├── asgi.py                          # ASGI application (for async)
│   ├── urls.py                          # Main URL configuration
│   ├── celery.py                        # Celery configuration
│   └── settings/                        # Settings package
│       ├── __init__.py
│       ├── base.py                      # Base settings
│       ├── development.py               # Development settings
│       ├── production.py                # Production settings
│       └── testing.py                   # Testing settings
│
├── apps/                                # Django applications
│   ├── __init__.py
│   ├── core/                           # Core Guardian integration
│   │   ├── __init__.py
│   │   ├── models.py                   # Core models
│   │   ├── admin.py                    # Admin customizations
│   │   ├── apps.py                     # App configuration
│   │   ├── guardian_integration.py     # Guardian Django integration
│   │   ├── event_bus.py                # Inter-module communication
│   │   ├── circuit_breaker.py          # Failure isolation
│   │   ├── health_monitor.py           # System health tracking
│   │   └── management/                 # Django management commands
│   │       └── commands/
│   │           ├── guardian_migrate.py # Guardian-wrapped migrations
│   │           └── health_check.py     # Health check command
│   │
│   ├── authentication/                  # Auth & user management
│   │   ├── __init__.py
│   │   ├── models.py                   # Custom User model
│   │   ├── admin.py                    # User admin interface
│   │   ├── views.py                    # Auth views
│   │   ├── forms.py                    # Security question forms
│   │   ├── urls.py                     # Auth URLs
│   │   ├── apps.py                     # App configuration
│   │   ├── migrations/                 # Database migrations
│   │   └── templates/                  # Auth templates
│   │       └── authentication/
│   │           ├── login.html
│   │           ├── security_questions.html
│   │           └── password_reset.html
│   │
│   ├── administration/                  # Admin panel extensions
│   │   ├── __init__.py
│   │   ├── models.py                   # API keys, system logs
│   │   ├── admin.py                    # Enhanced admin interface
│   │   ├── views.py                    # Admin dashboard views
│   │   ├── urls.py                     # Admin URLs
│   │   ├── apps.py                     # App configuration
│   │   ├── forms.py                    # Admin forms
│   │   ├── migrations/                 # Database migrations
│   │   └── templates/                  # Admin templates
│   │       └── administration/
│   │           ├── dashboard.html
│   │           ├── api_keys.html
│   │           ├── system_logs.html
│   │           └── user_management.html
│   │
│   ├── ingestion/                      # Fireflies integration
│   │   ├── __init__.py
│   │   ├── models.py                   # Transcript models
│   │   ├── admin.py                    # Ingestion admin
│   │   ├── services.py                 # Fireflies API client
│   │   ├── tasks.py                    # Celery tasks
│   │   ├── apps.py                     # App configuration
│   │   ├── urls.py                     # Module URLs
│   │   ├── views.py                    # Module views
│   │   ├── migrations/                 # Database migrations
│   │   └── tests/                      # Module tests
│   │       ├── test_models.py
│   │       ├── test_services.py
│   │       └── test_tasks.py
│   │
│   ├── processing/                     # AI processing
│   │   ├── __init__.py
│   │   ├── models.py                   # ActionItem models
│   │   ├── admin.py                    # Processing admin
│   │   ├── ai_service.py               # Gemini API integration
│   │   ├── tasks.py                    # Processing Celery tasks
│   │   ├── apps.py                     # App configuration
│   │   ├── urls.py                     # Module URLs
│   │   ├── views.py                    # Module views
│   │   ├── migrations/                 # Database migrations
│   │   └── tests/                      # Module tests
│   │       ├── test_models.py
│   │       ├── test_ai_service.py
│   │       └── test_tasks.py
│   │
│   ├── review/                         # Human review interface
│   │   ├── __init__.py
│   │   ├── models.py                   # Review session models
│   │   ├── admin.py                    # Review admin
│   │   ├── views.py                    # Review dashboard views
│   │   ├── urls.py                     # Review URLs
│   │   ├── apps.py                     # App configuration
│   │   ├── forms.py                    # Review forms
│   │   ├── migrations/                 # Database migrations
│   │   ├── static/                     # Static files
│   │   │   ├── css/
│   │   │   │   └── review_dashboard.css
│   │   │   └── js/
│   │   │       └── real_time_updates.js
│   │   ├── templates/                  # Review templates
│   │   │   └── review/
│   │   │       ├── dashboard.html
│   │   │       ├── task_detail.html
│   │   │       └── bulk_actions.html
│   │   └── tests/                      # Module tests
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_forms.py
│   │
│   └── delivery/                       # Monday.com integration
│       ├── __init__.py
│       ├── models.py                   # Delivery tracking models
│       ├── admin.py                    # Delivery admin
│       ├── services.py                 # Monday.com API client
│       ├── tasks.py                    # Delivery Celery tasks
│       ├── apps.py                     # App configuration
│       ├── urls.py                     # Module URLs
│       ├── views.py                    # Module views
│       ├── migrations/                 # Database migrations
│       └── tests/                      # Module tests
│           ├── test_models.py
│           ├── test_services.py
│           └── test_tasks.py
│
├── templates/                          # Global templates
│   ├── base.html                       # Base template
│   ├── admin/                          # Admin template overrides
│   │   ├── base_site.html             # Custom admin base
│   │   └── index.html                 # Custom admin dashboard
│   └── errors/                         # Error pages
│       ├── 404.html
│       ├── 500.html
│       └── maintenance.html
│
├── static/                             # Static files
│   ├── css/                           # Global CSS
│   │   ├── base.css
│   │   └── admin_custom.css
│   ├── js/                            # Global JavaScript
│   │   ├── base.js
│   │   └── htmx.min.js
│   └── images/                        # Images
│       └── logo.png
│
├── media/                             # User uploaded files
│   └── uploads/
│
├── logs/                              # Application logs
│   ├── django.log
│   ├── celery.log
│   └── guardian.log
│
├── tests/                             # Integration tests
│   ├── __init__.py
│   ├── test_integration.py            # End-to-end tests
│   ├── test_guardian_integration.py   # Guardian system tests
│   └── fixtures/                      # Test fixtures
│       └── sample_data.json
│
└── docs/                              # Documentation
    ├── api.md                         # API documentation
    ├── deployment.md                  # Deployment guide
    └── guardian_usage.md              # Guardian system usage
```

## Key Files & Configurations

### 1. Guardian System Integration

#### guardian.sh
```bash
#!/bin/bash
# Guardian system for Django
# Wraps all Django management commands with safeguards

DJANGO_MANAGE="python manage.py"
KNOWLEDGE_DIR=".ai-knowledge"

guardian_django_command() {
    local command="$1"
    
    # Pre-check: Clean git state
    if [[ -n $(git status --porcelain) ]]; then
        echo "ERROR: Working directory not clean"
        exit 1
    fi
    
    # Create snapshot
    ./scripts/create_snapshot.sh
    
    # Update knowledge base
    python manage.py update_knowledge_base
    
    # Execute command with approval gate
    echo "Executing: $DJANGO_MANAGE $command"
    read -p "Approve execution? (y/N): " approval
    
    if [[ $approval == "y" || $approval == "Y" ]]; then
        $DJANGO_MANAGE $command
        
        # Post-check: Update knowledge if files changed
        if [[ -n $(git status --porcelain) ]]; then
            python manage.py update_knowledge_base --post-change
        fi
    else
        echo "Command execution cancelled"
        exit 1
    fi
}

# Command routing
case "$1" in
    --django-command)
        guardian_django_command "$2"
        ;;
    --migrate)
        guardian_django_command "migrate"
        ;;
    --collectstatic)
        guardian_django_command "collectstatic --noinput"
        ;;
    *)
        echo "Usage: $0 --django-command 'command' | --migrate | --collectstatic"
        exit 1
        ;;
esac
```

### 2. Django Settings Structure

#### taskforge/settings/base.py
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Guardian Integration
GUARDIAN_ENABLED = True
GUARDIAN_KNOWLEDGE_DIR = BASE_DIR / '.ai-knowledge'

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
    'celery',
    'django_celery_beat',
    'django_celery_results',
]

LOCAL_APPS = [
    'apps.core',
    'apps.authentication',
    'apps.administration',
    'apps.ingestion',
    'apps.processing',
    'apps.review',
    'apps.delivery',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'taskforge'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Guardian Settings
GUARDIAN_SETTINGS = {
    'KNOWLEDGE_UPDATE_INTERVAL': 300,  # 5 minutes
    'APPROVAL_TIMEOUT': 3600,  # 1 hour
    'BACKUP_RETENTION_DAYS': 30,
    'REGRESSION_CHECK_ENABLED': True,
}

# API Keys (managed through admin)
EXTERNAL_APIS = {
    'FIREFLIES': {
        'BASE_URL': 'https://api.fireflies.ai/graphql',
        'RATE_LIMIT': 100,  # requests per minute
    },
    'GEMINI': {
        'BASE_URL': 'https://generativelanguage.googleapis.com/v1beta',
        'RATE_LIMIT': 60,  # requests per minute
    },
    'MONDAY': {
        'BASE_URL': 'https://api.monday.com/v2',
        'RATE_LIMIT': 100,  # requests per minute
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'guardian': {
            'format': '[GUARDIAN] {levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'guardian_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'guardian.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'guardian',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'guardian': {
            'handlers': ['guardian_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 3. Custom User Model

#### apps/authentication/models.py
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model with security questions"""
    
    # Security Questions for Password Reset
    security_question_1 = models.CharField(
        max_length=200,
        help_text="First security question"
    )
    security_answer_1 = models.CharField(
        max_length=200,
        help_text="Answer to first security question"
    )
    security_question_2 = models.CharField(
        max_length=200,
        help_text="Second security question"
    )
    security_answer_2 = models.CharField(
        max_length=200,
        help_text="Answer to second security question"
    )
    
    # Registration Control
    whitelisted_for_registration = models.BooleanField(
        default=False,
        help_text="Allow this user to complete registration"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user_custom'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email or self.username
    
    def is_superadmin(self):
        """Check if user is the superadmin"""
        return self.email == 'joe@coophive.network' and self.is_superuser
```

### 4. Guardian Django Integration

#### apps/core/guardian_integration.py
```python
import os
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger('guardian')

class GuardianMixin:
    """Mixin for Django management commands with Guardian integration"""
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--guardian-bypass',
            action='store_true',
            help='Bypass Guardian validation (emergency only)',
        )
        parser.add_argument(
            '--guardian-approval',
            type=str,
            help='Guardian approval token',
        )
    
    def handle(self, *args, **options):
        if not options.get('guardian_bypass'):
            self.guardian_pre_check()
            
        # Execute the actual command
        result = self.guardian_handle(*args, **options)
        
        if not options.get('guardian_bypass'):
            self.guardian_post_check()
            
        return result
    
    def guardian_pre_check(self):
        """Pre-execution Guardian checks"""
        logger.info("Guardian pre-check initiated")
        
        # Check knowledge base is up to date
        if not self.validate_knowledge_base():
            raise Exception("Knowledge base validation failed")
            
        # Check system health
        if not self.check_system_health():
            raise Exception("System health check failed")
            
        logger.info("Guardian pre-check passed")
    
    def guardian_post_check(self):
        """Post-execution Guardian checks"""
        logger.info("Guardian post-check initiated")
        
        # Update knowledge base if changes detected
        self.update_knowledge_base()
        
        logger.info("Guardian post-check completed")
    
    def validate_knowledge_base(self):
        """Validate AI knowledge base is current"""
        knowledge_dir = settings.GUARDIAN_KNOWLEDGE_DIR
        
        # Check if knowledge files exist and are recent
        required_files = [
            'PROJECT_STATE.md',
            'ARCHITECTURE_MAP.md',
            'MODULE_STATUS.md'
        ]
        
        for filename in required_files:
            filepath = knowledge_dir / filename
            if not filepath.exists():
                logger.error(f"Missing knowledge file: {filename}")
                return False
                
        return True
    
    def check_system_health(self):
        """Check system health before changes"""
        from apps.core.health_monitor import HealthMonitor
        
        monitor = HealthMonitor()
        health_status = monitor.check_all_modules()
        
        critical_modules = ['database', 'redis']
        for module in critical_modules:
            if health_status.get(module, {}).get('status') != 'healthy':
                logger.error(f"Critical module unhealthy: {module}")
                return False
                
        return True
    
    def update_knowledge_base(self):
        """Update AI knowledge base with current state"""
        from apps.core.knowledge_manager import KnowledgeManager
        
        manager = KnowledgeManager()
        manager.update_all_knowledge_files()
        
        logger.info("Knowledge base updated")
    
    def guardian_handle(self, *args, **options):
        """Override this method instead of handle()"""
        raise NotImplementedError("Subclasses must implement guardian_handle()")
```

### 5. Requirements File

#### requirements.txt
```
Django==4.2.7
psycopg2-binary==2.9.7
celery==5.3.4
redis==5.0.1
django-celery-beat==2.5.0
django-celery-results==2.5.1
gunicorn==21.2.0
whitenoise==6.6.0
requests==2.31.0
python-dotenv==1.0.0
django-extensions==3.2.3
django-debug-toolbar==4.2.0
pytest==7.4.3
pytest-django==4.7.0
coverage==7.3.2
flake8==6.1.0
black==23.11.0
isort==5.12.0
```

This skeleton provides:
- ✅ **Guardian-integrated Django structure**
- ✅ **Modular app organization**
- ✅ **Custom user model with security questions**
- ✅ **Admin panel customization**
- ✅ **Celery background job integration**
- ✅ **Comprehensive logging**
- ✅ **Knowledge base management**
- ✅ **Health monitoring**
- ✅ **Zero regression safeguards** 