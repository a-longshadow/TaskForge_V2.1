import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskforge.settings.development')

app = Celery('taskforge')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'sync-fireflies-transcripts': {
        'task': 'apps.ingestion.tasks.sync_fireflies_transcripts',
        'schedule': 900.0,  # 15 minutes
    },
    'process-transcripts': {
        'task': 'apps.processing.tasks.process_pending_transcripts',
        'schedule': 300.0,  # 5 minutes
    },
    'auto-push-tasks': {
        'task': 'apps.delivery.tasks.auto_push_stale_tasks',
        'schedule': 3600.0,  # 60 minutes
    },
    'daily-briefing': {
        'task': 'apps.processing.tasks.generate_daily_briefing',
        'schedule': 86400.0,  # 24 hours
        'options': {'eta': '00:05'},  # Run at 00:05 UTC
    },
    'guardian-knowledge-update': {
        'task': 'apps.core.tasks.update_guardian_knowledge',
        'schedule': 300.0,  # 5 minutes
    },
    'system-health-check': {
        'task': 'apps.core.tasks.system_health_check',
        'schedule': 60.0,  # 1 minute
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 