"""
Test command to demonstrate the end-to-end pipeline with mock data
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.core.gemini_client import get_gemini_client
from apps.core.monday_client import get_monday_client
from apps.core.models import Transcript, ActionItem, SystemEvent

logger = logging.getLogger('apps.core.management.commands.test_pipeline')


class Command(BaseCommand):
    help = 'Test the end-to-end TaskForge pipeline with mock transcript data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Process data but do not create Monday.com items',
        )
    
    def handle(self, *args, **options):
        """Execute the test pipeline with mock data"""
        
        self.stdout.write(
            self.style.SUCCESS('🧪 Starting TaskForge Test Pipeline with Mock Data')
        )
        
        # Initialize clients
        gemini_client = get_gemini_client()
        monday_client = get_monday_client()
        
        # Create mock transcript data
        mock_transcript = {
            'id': 'test-transcript-123',
            'title': 'Weekly Team Standup - TaskForge Demo',
            'date_uploaded': '2025-01-17T10:00:00Z',
            'duration': 45,
            'meeting_attendees': [
                {'displayName': 'Alice Johnson', 'email': 'alice@taskforge.com'},
                {'displayName': 'Bob Smith', 'email': 'bob@taskforge.com'},
                {'displayName': 'Carol Davis', 'email': 'carol@taskforge.com'}
            ],
            'organizer_email': 'alice@taskforge.com',
            'summary': {
                'overview': 'Weekly team standup covering project progress, blockers, and upcoming tasks.',
                'action_items': 'Review API documentation, Fix authentication bug, Schedule client demo',
                'keywords': ['API', 'authentication', 'demo', 'progress']
            },
            'transcript_text': '''
Alice: Good morning everyone! Let's start our weekly standup. Bob, can you share your progress?

Bob: Hi team! This week I've been working on the API integration. I've completed the Fireflies connection but I'm blocked on the authentication bug in the Gemini client. I need to review the API documentation more thoroughly. Alice, could you help me with that?

Alice: Absolutely! I'll review the API documentation with you this afternoon. Carol, what about your progress?

Carol: I've finished the Monday.com integration and it's working well. I think we're ready to schedule a client demo for next week. Bob, once you fix that authentication issue, we should be good to go.

Bob: Perfect! I'll prioritize fixing the authentication bug today so we can move forward with the demo.

Alice: Great! So our action items are: Bob will fix the authentication bug, I'll help review the API documentation, and Carol will schedule the client demo for next week. Let's reconvene tomorrow to check progress.

Carol: Sounds good! I'll reach out to the client today to set up the demo.

Alice: Thanks everyone, have a great day!
            '''
        }
        
        self.stdout.write(f'📄 Processing mock transcript: {mock_transcript["title"]}')
        
        # Track pipeline statistics
        stats = {
            'transcripts_processed': 0,
            'tasks_extracted': 0,
            'tasks_delivered': 0,
            'errors': []
        }
        
        try:
            # Step 1: Store transcript in database
            with transaction.atomic():
                transcript, created = Transcript.objects.get_or_create(
                    fireflies_id=mock_transcript['id'],
                    defaults={
                        'title': mock_transcript['title'],
                        'meeting_date': timezone.now(),
                        'duration_minutes': mock_transcript['duration'],
                        'participant_count': len(mock_transcript['meeting_attendees']),
                        'content': mock_transcript['transcript_text'],
                        'raw_data': mock_transcript
                    }
                )
                
                if created:
                    self.stdout.write(f'  💾 Created new transcript in database')
                else:
                    self.stdout.write(f'  💾 Transcript already exists in database')
            
            stats['transcripts_processed'] += 1
            
            # Step 2: Extract tasks using Gemini AI
            self.stdout.write(f'  🤖 Extracting tasks with Gemini AI...')
            extracted_tasks = gemini_client.extract_tasks_from_transcript(mock_transcript)
            
            if not extracted_tasks:
                self.stdout.write(f'  ⚠️  No tasks extracted from transcript')
                return
            
            self.stdout.write(f'  ✅ Extracted {len(extracted_tasks)} tasks')
            stats['tasks_extracted'] += len(extracted_tasks)
            
            # Display extracted tasks
            for i, task in enumerate(extracted_tasks, 1):
                self.stdout.write(f'    {i}. {task.get("task_item", "Unknown task")}')
                self.stdout.write(f'       Assignee: {task.get("assignee_emails", "Unassigned")}')
                self.stdout.write(f'       Priority: {task.get("priority", "Medium")}')
                self.stdout.write(f'       Description: {task.get("brief_description", "No description")}')
                self.stdout.write('')
            
            # Step 3: Store tasks in database
            created_action_items = []
            for task_data in extracted_tasks:
                try:
                    action_item = ActionItem.objects.create(
                        transcript=transcript,
                        title=task_data.get('task_item', 'Untitled Task'),
                        description=task_data.get('brief_description', ''),
                        assignee=task_data.get('assignee_emails', ''),
                        priority=self.map_priority(task_data.get('priority', 'Medium')),
                        status='pending',
                        confidence_score=0.9,  # High confidence for demo
                        ai_model_version='gemini-2.5-flash',
                        extraction_metadata=task_data
                    )
                    created_action_items.append(action_item)
                    
                except Exception as e:
                    logger.error(f"Failed to store task: {e}")
                    stats['errors'].append(f"Failed to store task: {e}")
            
            self.stdout.write(f'  💾 Stored {len(created_action_items)} tasks in database')
            
            # Step 4: Deliver tasks to Monday.com
            if not options['dry_run']:
                self.stdout.write(f'  📤 Delivering tasks to Monday.com...')
                
                delivered_items = monday_client.bulk_create_tasks(extracted_tasks)
                successful_deliveries = [item_id for item_id in delivered_items if item_id is not None]
                
                # Update action items with Monday.com IDs
                for i, item_id in enumerate(delivered_items):
                    if item_id and i < len(created_action_items):
                        created_action_items[i].monday_item_id = item_id
                        created_action_items[i].status = 'delivered'
                        created_action_items[i].delivered_at = timezone.now()
                        created_action_items[i].save()
                
                stats['tasks_delivered'] += len(successful_deliveries)
                self.stdout.write(f'  ✅ Delivered {len(successful_deliveries)} tasks to Monday.com')
                
                # Display Monday.com item IDs
                for i, item_id in enumerate(successful_deliveries):
                    task_title = extracted_tasks[i].get('task_item', 'Unknown task')
                    self.stdout.write(f'    📋 "{task_title}" → Monday.com ID: {item_id}')
                
            else:
                self.stdout.write(f'  🚫 Dry run: Skipping Monday.com delivery')
            
            # Mark transcript as processed
            transcript.mark_processed()
            
            # Display final results
            self.display_results(stats, options['dry_run'])
            
        except Exception as e:
            error_msg = f"Test pipeline execution failed: {e}"
            logger.error(error_msg)
            self.stdout.write(
                self.style.ERROR(f'❌ {error_msg}')
            )
    
    def map_priority(self, gemini_priority):
        """Map Gemini priority to Django model priority"""
        priority_map = {
            'High': 'high',
            'Medium': 'medium',
            'Low': 'low'
        }
        return priority_map.get(gemini_priority, 'medium')
    
    def display_results(self, stats, dry_run):
        """Display pipeline execution results"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS('📊 TEST PIPELINE RESULTS')
        )
        self.stdout.write('='*50)
        
        self.stdout.write(f'📄 Transcripts processed: {stats["transcripts_processed"]}')
        self.stdout.write(f'🤖 Tasks extracted: {stats["tasks_extracted"]}')
        
        if not dry_run:
            self.stdout.write(f'📤 Tasks delivered: {stats["tasks_delivered"]}')
            success_rate = (stats["tasks_delivered"] / stats["tasks_extracted"] * 100) if stats["tasks_extracted"] > 0 else 0
            self.stdout.write(f'✅ Success rate: {success_rate:.1f}%')
        else:
            self.stdout.write('🚫 Dry run: No tasks delivered')
        
        if stats['errors']:
            self.stdout.write(f'❌ Errors: {len(stats["errors"])}')
            for error in stats['errors']:
                self.stdout.write(f'   • {error}')
        
        self.stdout.write('\n' + self.style.SUCCESS('🎉 Test pipeline completed successfully!'))
        self.stdout.write('\n' + self.style.WARNING('💡 This demonstrates the full TaskForge workflow:'))
        self.stdout.write('   1. 📄 Transcript ingestion (from Fireflies)')
        self.stdout.write('   2. 🤖 AI task extraction (via Gemini)')
        self.stdout.write('   3. 💾 Database storage (Django models)')
        self.stdout.write('   4. 📤 Task delivery (to Monday.com)')
        self.stdout.write('   5. 📊 Complete audit trail and monitoring') 