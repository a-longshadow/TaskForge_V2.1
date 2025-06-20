"""
Core views for TaskForge
"""

import logging
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.conf import settings
from .health_monitor import get_system_health
from .event_bus import EventBus
from .circuit_breaker import CircuitBreakerRegistry
from django.db import connection
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger('apps.core.views')


def home(request):
    """Home page view"""
    context = {
        'system_status': 'operational',
        'guardian_enabled': getattr(settings, 'GUARDIAN_ENABLED', False),
        'modules': [
            {'name': 'Core Infrastructure', 'status': 'active'},
            {'name': 'Authentication', 'status': 'development'},
            {'name': 'Administration', 'status': 'development'},
            {'name': 'Ingestion', 'status': 'pending'},
            {'name': 'Processing', 'status': 'pending'},
            {'name': 'Review', 'status': 'pending'},
            {'name': 'Delivery', 'status': 'pending'},
        ]
    }
    return render(request, 'core/home.html', context)


@require_GET
def health_check(request):
    """Health check endpoint for Railway monitoring"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Test cache
        cache.set('health_check', 'ok', 30)
        cache_status = cache.get('health_check') == 'ok'
        
        # Check if we can import our models
        from apps.core.models import GeminiProcessedTask
        task_count = GeminiProcessedTask.objects.count()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'operational' if cache_status else 'error',
            'tasks': task_count,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_GET
@cache_page(60)  # Cache for 1 minute
def system_stats(request):
    """
    System statistics endpoint
    Returns operational metrics and statistics
    """
    try:
        from .models import Transcript, ActionItem, DailyReport, SystemEvent
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Get basic counts
        stats = {
            'transcripts': {
                'total': Transcript.objects.count(),
                'processed': Transcript.objects.filter(is_processed=True).count(),
                'pending': Transcript.objects.filter(is_processed=False).count(),
            },
            'action_items': {
                'total': ActionItem.objects.count(),
                'pending': ActionItem.objects.filter(status='pending').count(),
                'approved': ActionItem.objects.filter(status='approved').count(),
                'delivered': ActionItem.objects.filter(status='delivered').count(),
            },
            'daily_reports': {
                'total': DailyReport.objects.count(),
                'last_generated': DailyReport.objects.order_by('-report_date').first(),
            },
            'system_events': {
                'total': SystemEvent.objects.count(),
                'last_24h': SystemEvent.objects.filter(
                    created_at__gte=timezone.now() - timedelta(hours=24)
                ).count(),
                'errors': SystemEvent.objects.filter(severity='error').count(),
            }
        }
        
        # Add timestamp
        stats['generated_at'] = timezone.now().isoformat()
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"System stats failed: {e}")
        return JsonResponse({
            'error': 'Failed to generate system statistics',
            'message': str(e)
        }, status=500)


# Error handlers
def handler404(request, exception):
    """Custom 404 handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Not Found',
            'message': 'The requested endpoint does not exist'
        }, status=404)
    
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Custom 500 handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }, status=500)
    
    return render(request, 'errors/500.html', status=500) 