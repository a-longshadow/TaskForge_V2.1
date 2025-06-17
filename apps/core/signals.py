"""
Django signals for core event handling
"""

import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import ActionItem, Transcript, SystemEvent
from .event_bus import publish_event, EventTypes

logger = logging.getLogger('apps.core.signals')


@receiver(post_save, sender=Transcript)
def transcript_saved(sender, instance, created, **kwargs):
    """Handle transcript save events"""
    if created:
        # New transcript ingested
        publish_event(
            EventTypes.TRANSCRIPT_INGESTED,
            {
                'transcript_id': str(instance.id),
                'fireflies_id': instance.fireflies_id,
                'title': instance.title,
                'meeting_date': instance.meeting_date.isoformat(),
                'duration_minutes': instance.duration_minutes
            },
            source_module='ingestion'
        )
        logger.info(f"New transcript ingested: {instance.fireflies_id}")


@receiver(post_save, sender=ActionItem)
def action_item_saved(sender, instance, created, **kwargs):
    """Handle action item save events"""
    if created:
        # New task created
        publish_event(
            EventTypes.TASK_CREATED,
            {
                'task_id': str(instance.id),
                'title': instance.title,
                'status': instance.status,
                'priority': instance.priority,
                'transcript_id': str(instance.transcript.id)
            },
            source_module='processing'
        )
        logger.info(f"New task created: {instance.title}")
    else:
        # Task updated
        publish_event(
            EventTypes.TASK_UPDATED,
            {
                'task_id': str(instance.id),
                'title': instance.title,
                'status': instance.status,
                'priority': instance.priority
            },
            source_module='review'
        )
        
        # Check for status changes
        if hasattr(instance, '_state') and instance._state.adding is False:
            if instance.status == 'approved':
                publish_event(
                    EventTypes.TASK_APPROVED,
                    {
                        'task_id': str(instance.id),
                        'title': instance.title,
                        'reviewed_by': instance.reviewed_by.username if instance.reviewed_by else None
                    },
                    source_module='review'
                )
            elif instance.status == 'rejected':
                publish_event(
                    EventTypes.TASK_REJECTED,
                    {
                        'task_id': str(instance.id),
                        'title': instance.title,
                        'reviewed_by': instance.reviewed_by.username if instance.reviewed_by else None
                    },
                    source_module='review'
                )
            elif instance.status == 'delivered':
                publish_event(
                    EventTypes.TASK_DELIVERED,
                    {
                        'task_id': str(instance.id),
                        'title': instance.title,
                        'monday_item_id': instance.monday_item_id
                    },
                    source_module='delivery'
                )


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Handle user login events"""
    SystemEvent.objects.create(
        event_type='user_login',
        severity='info',
        message=f'User {user.username} logged in',
        source_module='authentication',
        user=user,
        details={
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
        }
    )
    logger.info(f"User logged in: {user.username}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Handle user logout events"""
    if user:
        SystemEvent.objects.create(
            event_type='user_logout',
            severity='info',
            message=f'User {user.username} logged out',
            source_module='authentication',
            user=user
        )
        logger.info(f"User logged out: {user.username}")


# Signal for Guardian alerts
def guardian_alert(message, severity='warning', details=None):
    """Create Guardian alert system event"""
    SystemEvent.objects.create(
        event_type='guardian_alert',
        severity=severity,
        message=message,
        source_module='guardian',
        details=details or {}
    )
    
    publish_event(
        EventTypes.GUARDIAN_ALERT,
        {
            'message': message,
            'severity': severity,
            'details': details or {}
        },
        source_module='guardian'
    )
    
    logger.warning(f"Guardian alert: {message}") 