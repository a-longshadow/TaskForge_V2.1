"""
Context processors for Django templates
"""

from django.conf import settings


def guardian_context(request):
    """Add Guardian system context to templates"""
    return {
        'guardian_enabled': getattr(settings, 'GUARDIAN_ENABLED', False),
        'guardian_phase': 'Phase 2 - Core Infrastructure',
        'guardian_knowledge_dir': getattr(settings, 'GUARDIAN_KNOWLEDGE_DIR', None),
    } 