"""
Django management command for end-to-end TaskForge pipeline
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.core.fireflies_client import get_fireflies_client
from apps.core.gemini_client import get_gemini_client
from apps.core.monday_client import get_monday_client
from apps.core.models import Transcript, ActionItem, SystemEvent

logger = logging.getLogger('apps.core.management.commands.run_end_to_end_pipeline')


class Command(BaseCommand):
    help = 'Run the complete end-to-end TaskForge pipeline: Fireflies → Gemini → Monday.com'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-apis',
            action='store_true',
            help='Test API connections only, do not process data',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Process data but do not create Monday.com items',
        )
        parser.add_argument(
            '--transcript-id',
            type=str,
            help='Process a specific transcript by ID instead of today\'s meetings',
        )
    
    def handle(self, *args, **options):
        """Execute the end-to-end pipeline"""
        
        if options['test_apis']:
            self.test_api_connections()
            return
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting TaskForge End-to-End Pipeline')
        )
        
        # Initialize clients
        fireflies_client = get_fireflies_client()
        gemini_client = get_gemini_client()
        monday_client = get_monday_client()
        
        # Track pipeline statistics
        stats = {
            'transcripts_processed': 0,
            'tasks_extracted': 0,
            'tasks_delivered': 0,
            'errors': []
        }
        
        try:
            # Step 1: Retrieve transcripts from Fireflies
            if options['transcript_id']:
                self.stdout.write('📄 Retrieving specific transcript...')
                transcript_data = fireflies_client.get_transcript_by_id(options['transcript_id'])
                transcripts = [transcript_data] if transcript_data else []
            else:
                self.stdout.write('📄 Retrieving today\'s meetings from Fireflies...')
                transcripts = fireflies_client.get_today_transcripts()
            
            if not transcripts:
                self.stdout.write(
                    self.style.WARNING('⚠️  No transcripts found')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Retrieved {len(transcripts)} transcripts from Fireflies')
            )
            
            # Process each transcript
            for transcript_data in transcripts:
                try:
                    stats['transcripts_processed'] += 1
                    self.process_transcript(
                        transcript_data, 
                        gemini_client, 
                        monday_client, 
                        stats, 
                        options['dry_run']
                    )
                    
                except Exception as e:
                    error_msg = f"Failed to process transcript {transcript_data.get('id', 'unknown')}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
                    self.stdout.write(
                        self.style.ERROR(f'❌ {error_msg}')
                    )
            
            # Display final results
            self.display_results(stats, options['dry_run'])
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {e}"
            logger.error(error_msg)
            self.stdout.write(
                self.style.ERROR(f'❌ {error_msg}')
            )
            
            # Log system event
            SystemEvent.objects.create(
                event_type='system_error',
                severity='error',
                message='End-to-end pipeline failed',
                details={'error': str(e)},
                source_module='pipeline'
            )
    
    def process_transcript(self, transcript_data, gemini_client, monday_client, stats, dry_run):
        """Process a single transcript through the pipeline"""
        
        transcript_id = transcript_data.get('id')
        transcript_title = transcript_data.get('title', 'Untitled Meeting')
        
        self.stdout.write(f'🔄 Processing: {transcript_title}')
        
        # Step 2: Store transcript in database
        with transaction.atomic():
            transcript, created = Transcript.objects.get_or_create(
                fireflies_id=transcript_id,
                defaults={
                    'title': transcript_title,
                    'meeting_date': self.parse_meeting_date(transcript_data.get('date_uploaded')),
                    'duration_minutes': transcript_data.get('duration', 0),
                    'participant_count': len(transcript_data.get('meeting_attendees', [])),
                    'content': transcript_data.get('transcript_text', ''),
                    'raw_data': transcript_data
                }
            )
            
            if created:
                self.stdout.write(f'  💾 Stored transcript in database')
            else:
                self.stdout.write(f'  💾 Transcript already exists in database')
        
        # Step 3: Extract tasks using Gemini AI
        self.stdout.write(f'  🤖 Extracting tasks with Gemini AI...')
        extracted_tasks = gemini_client.extract_tasks_from_transcript(transcript_data)
        
        if not extracted_tasks:
            self.stdout.write(f'  ⚠️  No tasks extracted from transcript')
            return
        
        self.stdout.write(f'  ✅ Extracted {len(extracted_tasks)} tasks')
        stats['tasks_extracted'] += len(extracted_tasks)
        
        # Step 4: Store tasks in database
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
                    confidence_score=0.8,  # Default confidence
                    ai_model_version='gemini-pro',
                    extraction_metadata=task_data
                )
                created_action_items.append(action_item)
                
            except Exception as e:
                logger.error(f"Failed to store task: {e}")
                stats['errors'].append(f"Failed to store task: {e}")
        
        self.stdout.write(f'  💾 Stored {len(created_action_items)} tasks in database')
        
        # Step 5: Deliver tasks to Monday.com
        if not dry_run:
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
            
        else:
            self.stdout.write(f'  🚫 Dry run: Skipping Monday.com delivery')
        
        # Mark transcript as processed
        transcript.mark_processed()
    
    def test_api_connections(self):
        """Test connections to all external APIs"""
        self.stdout.write(
            self.style.SUCCESS('🔧 Testing API Connections')
        )
        
        # Test Fireflies
        self.stdout.write('  📄 Testing Fireflies API...')
        fireflies_client = get_fireflies_client()
        if fireflies_client.test_connection():
            self.stdout.write('    ✅ Fireflies API: Connected')
        else:
            self.stdout.write('    ❌ Fireflies API: Failed')
        
        # Test Gemini
        self.stdout.write('  🤖 Testing Gemini API...')
        gemini_client = get_gemini_client()
        if gemini_client.test_connection():
            self.stdout.write('    ✅ Gemini API: Connected')
        else:
            self.stdout.write('    ❌ Gemini API: Failed')
        
        # Test Monday.com
        self.stdout.write('  📤 Testing Monday.com API...')
        monday_client = get_monday_client()
        if monday_client.test_connection():
            self.stdout.write('    ✅ Monday.com API: Connected')
            
            # Get board info
            board_info = monday_client.get_board_info()
            if board_info:
                self.stdout.write(f'    📋 Board: {board_info.get("name", "Unknown")}')
        else:
            self.stdout.write('    ❌ Monday.com API: Failed')
    
    def parse_meeting_date(self, date_str):
        """Parse meeting date from Fireflies format"""
        if not date_str:
            return timezone.now()
        
        try:
            # Handle various date formats
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return timezone.now()
    
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
            self.style.SUCCESS('📊 PIPELINE EXECUTION RESULTS')
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
        
        self.stdout.write('\n' + self.style.SUCCESS('🎉 Pipeline execution completed!')) 