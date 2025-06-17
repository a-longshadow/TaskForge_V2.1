"""
Middleware for TaskForge core functionality
"""

import logging
import time
from django.http import JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .health_monitor import get_system_health

logger = logging.getLogger('apps.core.middleware')


class HealthCheckMiddleware(MiddlewareMixin):
    """Middleware to handle health check requests efficiently"""
    
    def process_request(self, request):
        # Quick health check without going through full Django routing
        if request.path == '/health/quick':
            try:
                # Basic health check - just verify we can respond
                return JsonResponse({
                    'status': 'healthy',
                    'timestamp': time.time(),
                    'quick_check': True
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'unhealthy',
                    'error': str(e),
                    'quick_check': True
                }, status=503)
        
        return None


class GuardianMiddleware(MiddlewareMixin):
    """Middleware for Guardian system integration"""
    
    def process_request(self, request):
        # Add Guardian context to request
        request.guardian_enabled = getattr(settings, 'GUARDIAN_ENABLED', False)
        request.guardian_phase = 'Phase 2 - Core Infrastructure'
        return None
    
    def process_exception(self, request, exception):
        # Log exceptions for Guardian monitoring
        if getattr(settings, 'GUARDIAN_ENABLED', False):
            logger.error(f"Guardian caught exception: {exception}", extra={
                'path': request.path,
                'method': request.method,
                'user': getattr(request, 'user', None),
                'guardian_alert': True
            })
        return None 