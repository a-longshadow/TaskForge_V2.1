from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core System'
    
    def ready(self):
        """Initialize core components when Django starts"""
        # Import signal handlers
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
            from .tasks import start_background_monitoring
            start_background_monitoring.delay()
        except ImportError:
            # Celery might not be available during migrations
            pass 