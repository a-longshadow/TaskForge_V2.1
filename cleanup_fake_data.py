#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskforge.settings.development')
django.setup()

from apps.core.models import GeminiProcessedTask

print('🧹 CLEANING UP FAKE TEST DATA')
print('=' * 35)

# Find and delete fake tasks
fake_tasks = GeminiProcessedTask.objects.filter(
    assignee_full_names__icontains='Joe Smith'
)
count = fake_tasks.count()
print(f'Found {count} fake tasks to delete')

for task in fake_tasks:
    print(f'   • Deleting: {task.task_item[:50]}... (Created: {task.created_at})')
    
fake_tasks.delete()
print(f'✅ Deleted {count} fake tasks')

# Verify cleanup
remaining_fake = GeminiProcessedTask.objects.filter(
    assignee_full_names__icontains='Joe Smith'
).count()
print(f'✅ Remaining fake tasks: {remaining_fake}')

# Show current total
total_tasks = GeminiProcessedTask.objects.count()
print(f'✅ Total clean tasks remaining: {total_tasks}')

print('\n🎯 VERIFICATION: REAL ATTENDEES ONLY')
print('=' * 40)

# Get unique assignees to verify they're all real
unique_assignees = set()
for task in GeminiProcessedTask.objects.all():
    unique_assignees.add(task.assignee_full_names)

print('✅ Current assignees in database:')
for assignee in sorted(unique_assignees):
    print(f'   • {assignee}')

print(f'\n🎉 DATABASE CLEANED - {total_tasks} tasks with real attendees only') 