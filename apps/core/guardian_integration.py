"""
Guardian Integration for Django
"""

import logging
import os
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger('guardian')


def initialize_guardian():
    """Initialize Guardian system integration with Django"""
    if not getattr(settings, 'GUARDIAN_ENABLED', False):
        return
    
    logger.info("Initializing Guardian integration with Django")
    
    # Ensure knowledge directory exists
    knowledge_dir = getattr(settings, 'GUARDIAN_KNOWLEDGE_DIR', None)
    if knowledge_dir and not knowledge_dir.exists():
        knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize knowledge base if needed
    update_django_knowledge_base()
    
    logger.info("Guardian integration initialized")


def update_django_knowledge_base():
    """Update knowledge base with Django-specific information"""
    knowledge_dir = getattr(settings, 'GUARDIAN_KNOWLEDGE_DIR')
    if not knowledge_dir:
        return
    
    # Update MODULE_STATUS.md with Django apps
    module_status_file = knowledge_dir / 'MODULE_STATUS.md'
    
    django_apps_status = """
# Django Application Status

## Core Infrastructure ✅
- **Status**: Active
- **Components**: Event bus, Circuit breaker, Health monitor
- **Guardian Integration**: Active

## Authentication System 🚧
- **Status**: In Development
- **Features**: Custom user model, Security questions
- **Guardian Protection**: Enabled

## Administration Panel 🚧
- **Status**: In Development
- **Features**: Enhanced Django admin, API key management
- **Guardian Protection**: Enabled

## Ingestion Module ⏳
- **Status**: Pending
- **Integration**: Fireflies API
- **Guardian Protection**: Ready

## Processing Module ⏳
- **Status**: Pending
- **Integration**: Gemini AI
- **Guardian Protection**: Ready

## Review Module ⏳
- **Status**: Pending
- **Features**: Dashboard, Real-time updates
- **Guardian Protection**: Ready

## Delivery Module ⏳
- **Status**: Pending
- **Integration**: Monday.com API
- **Guardian Protection**: Ready
"""
    
    with open(module_status_file, 'w') as f:
        f.write(django_apps_status)
    
    logger.info("Django knowledge base updated")


class GuardianMixin:
    """Mixin for Django management commands with Guardian integration"""
    
    def add_arguments(self, parser):
        super().add_arguments(parser) if hasattr(super(), 'add_arguments') else None
        parser.add_argument(
            '--guardian-bypass',
            action='store_true',
            help='Bypass Guardian validation (emergency only)',
        )
    
    def handle(self, *args, **options):
        if not options.get('guardian_bypass'):
            self.guardian_pre_check()
        
        result = self.guardian_handle(*args, **options)
        
        if not options.get('guardian_bypass'):
            self.guardian_post_check()
        
        return result
    
    def guardian_pre_check(self):
        """Pre-execution Guardian checks"""
        logger.info("Guardian pre-check initiated")
        
        if not self.validate_system_health():
            raise Exception("System health check failed")
        
        logger.info("Guardian pre-check passed")
    
    def guardian_post_check(self):
        """Post-execution Guardian checks"""
        logger.info("Guardian post-check initiated")
        update_django_knowledge_base()
        logger.info("Guardian post-check completed")
    
    def validate_system_health(self):
        """Check system health before changes"""
        try:
            from .health_monitor import get_system_health
            health = get_system_health()
            return health['overall_status'] != 'unhealthy'
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def guardian_handle(self, *args, **options):
        """Override this method instead of handle()"""
        raise NotImplementedError("Subclasses must implement guardian_handle()") 