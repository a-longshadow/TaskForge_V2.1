"""
Django management command to test Monday.com integration with correct field mappings
"""

from django.core.management.base import BaseCommand
from apps.core.monday_client import get_monday_client
import json
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Test Monday.com integration with correct field mappings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test API connection only'
        )
        parser.add_argument(
            '--get-board-info',
            action='store_true',
            help='Get board and column information'
        )
        parser.add_argument(
            '--create-test-task',
            action='store_true',
            help='Create a test task with all field mappings'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔗 Testing Monday.com Integration'))
        self.stdout.write('=' * 50)
        
        # Get Monday.com client
        monday_client = get_monday_client()
        
        # Test connection
        if options['test_connection'] or not any([options['get_board_info'], options['create_test_task']]):
            self.test_connection(monday_client)
        
        # Get board info
        if options['get_board_info'] or not any([options['test_connection'], options['create_test_task']]):
            self.get_board_info(monday_client)
        
        # Create test task
        if options['create_test_task'] or not any([options['test_connection'], options['get_board_info']]):
            self.create_test_task(monday_client, options['dry_run'])
    
    def test_connection(self, monday_client):
        """Test Monday.com API connection"""
        self.stdout.write('\n🔍 Testing API Connection...')
        
        try:
            success = monday_client.test_connection()
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Connection successful'))
            else:
                self.stdout.write(self.style.ERROR('❌ Connection failed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Connection error: {e}'))
    
    def get_board_info(self, monday_client):
        """Get board and column information"""
        self.stdout.write('\n📋 Getting Board Information...')
        
        try:
            board_info = monday_client.get_board_info()
            if board_info:
                self.stdout.write(f"Board: {board_info.get('name', 'Unknown')}")
                self.stdout.write(f"ID: {board_info.get('id')}")
                
                # Show groups
                groups = board_info.get('groups', [])
                self.stdout.write(f"\nGroups ({len(groups)}):")
                for group in groups:
                    self.stdout.write(f"  - {group.get('title')} (ID: {group.get('id')})")
                
                # Show columns with field mappings
                columns = board_info.get('columns', [])
                self.stdout.write(f"\nColumns ({len(columns)}):")
                
                field_mappings = {
                    'text_mkr7jgkp': 'Team Member',
                    'status_1': 'Priority', 
                    'status': 'Status',
                    'long_text': 'Brief Description',
                    'date_mkr7ymmh': 'Date Expected'
                }
                
                for col in columns:
                    col_id = col.get('id')
                    col_title = col.get('title')
                    col_type = col.get('type')
                    
                    mapping_info = ""
                    if col_id in field_mappings:
                        mapping_info = f" → {field_mappings[col_id]}"
                    
                    self.stdout.write(f"  - {col_title} (ID: {col_id}, Type: {col_type}){mapping_info}")
                
            else:
                self.stdout.write(self.style.ERROR('❌ Could not retrieve board information'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Board info error: {e}'))
    
    def create_test_task(self, monday_client, dry_run=False):
        """Create a test task with all field mappings"""
        self.stdout.write('\n🚀 Creating Test Task...')
        
        # Create sample task data matching Gemini AI extraction format
        due_date = datetime.now() + timedelta(days=3)
        due_date_ms = int(due_date.timestamp() * 1000)
        
        test_task = {
            "task_item": "Test TaskForge Integration with All Fields",
            "assignee_emails": "joe@coophive.network",
            "assignee(s)_full_names": "Joe Maina",
            "priority": "High",
            "brief_description": "This is a comprehensive test task to verify all Monday.com field mappings are working correctly with the TaskForge integration system.",
            "due_date": due_date_ms,
            "status": "Working on it"
        }
        
        self.stdout.write('\nTask Data:')
        self.stdout.write(json.dumps(test_task, indent=2))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN - Task would be created with above data'))
            return
        
        try:
            item_id = monday_client.create_task_item(test_task)
            if item_id:
                self.stdout.write(self.style.SUCCESS(f'✅ Test task created successfully!'))
                self.stdout.write(f'Monday.com Item ID: {item_id}')
                self.stdout.write(f'Board URL: https://coophive.monday.com/boards/{monday_client.board_id}')
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to create test task'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Task creation error: {e}'))
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('Test completed. Check Monday.com board to verify field mappings.') 