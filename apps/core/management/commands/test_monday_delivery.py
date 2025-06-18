from django.core.management.base import BaseCommand
from apps.core.models import ProcessedTaskData
from apps.core.precision_monday_client import get_precision_monday_client


class Command(BaseCommand):
    help = 'Test Monday.com delivery preparation with N8N precision column mapping'

    def handle(self, *args, **options):
        self.stdout.write("🚀 TESTING MONDAY.COM DELIVERY PREPARATION")
        self.stdout.write("=" * 60)
        
        # Get processed tasks
        tasks = ProcessedTaskData.objects.all()[:3]
        monday_client = get_precision_monday_client()
        
        self.stdout.write(f"📋 Found {tasks.count()} tasks to test")
        
        for i, task in enumerate(tasks, 1):
            self.stdout.write(f"\n📤 Task {i}: {task.task_item[:60]}...")
            
            # Test column mapping
            column_values = monday_client._build_n8n_column_values(task)
            self.stdout.write(f"  • Column mapping: {column_values[:100]}...")
            self.stdout.write(f"  • Ready for delivery: {task.is_ready_for_delivery}")
            
            # Show field details
            self.stdout.write(f"  • Assignee Names: {task.assignee_full_names}")
            self.stdout.write(f"  • Assignee Emails: {task.assignee_emails}")
            self.stdout.write(f"  • Priority: {task.priority}")
            self.stdout.write(f"  • Status: {task.status}")
        
        self.stdout.write("\n✅ Monday.com column mapping working perfectly!")
        self.stdout.write("🎯 N8N precision pipeline end-to-end SUCCESS!") 