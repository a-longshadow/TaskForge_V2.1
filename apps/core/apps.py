from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core System (Lean)'
    
    def ready(self):
        """Initialize core components when Django starts"""
        # Import signal handlers for lean models
        from . import signals
        
        # Initialize Guardian integration
        from .guardian_integration import initialize_guardian
        initialize_guardian()
        
        # Initialize event bus
        from .event_bus import EventBus
        EventBus.initialize()
        
        # Initialize health monitor
        from .health_monitor import HealthMonitor
        HealthMonitor.initialize()
        
        # Start system components
        self.start_core_components()
    
    def start_core_components(self):
        """Start core system components"""
        try:
            # TODO: Use lean pipeline after migration is complete
            # from .lean_pipeline import LeanPipeline
            # Initialize lean pipeline for background tasks
            pass
        except ImportError:
            # Celery might not be available during migrations
            pass 