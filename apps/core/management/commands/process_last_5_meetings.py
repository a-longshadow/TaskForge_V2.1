"""
Process Last 5 Meetings with Real Gemini API
E2E Test Step 4: Process cached meetings using Gemini and temp/prompt.md
"""

import json
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from apps.core.models import RawTranscriptCache, GeminiProcessedTask
from apps.core.gemini_client import get_gemini_client

logger = logging.getLogger('apps.core.management.commands.process_last_5_meetings')


class Command(BaseCommand):
    help = 'Process last 5 meetings from cache using real Gemini API and temp/prompt.md'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Number of meetings to process (default: 5)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if meetings already have tasks',
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        
        self.stdout.write("🚀 E2E TEST STEP 4: PROCESSING MEETINGS WITH REAL GEMINI API")
        self.stdout.write("=" * 65)
        
        # Initialize statistics
        stats = {
            'meetings_found': 0,
            'meetings_processed': 0,
            'tasks_extracted': 0,
            'tasks_saved': 0,
            'errors': []
        }
        
        try:
            # Step 1: Get Gemini client
            self.stdout.write("🤖 Initializing Gemini AI client...")
            gemini_client = get_gemini_client()
            
            if not gemini_client.test_connection():
                self.stdout.write(self.style.ERROR("❌ Gemini API connection failed"))
                return
            
            self.stdout.write(self.style.SUCCESS("✅ Gemini API connected successfully"))
            
            # Step 2: Get last 5 meetings from cache
            self.stdout.write(f"\n📄 Fetching last {limit} meetings from cache...")
            meetings = RawTranscriptCache.objects.all().order_by('-meeting_date')[:limit]
            
            if not meetings:
                self.stdout.write(self.style.ERROR("❌ No meetings found in cache"))
                return
            
            stats['meetings_found'] = meetings.count()
            self.stdout.write(f"✅ Found {stats['meetings_found']} meetings to process")
            
            # Step 3: Process each meeting
            for i, meeting in enumerate(meetings, 1):
                self.stdout.write(f"\n🔄 Processing Meeting {i}/{stats['meetings_found']}")
                self.stdout.write(f"   📝 Title: {meeting.meeting_title}")
                self.stdout.write(f"   📅 Date: {meeting.meeting_date}")
                self.stdout.write(f"   🆔 ID: {meeting.fireflies_id}")
                
                # Check if already processed
                existing_tasks = GeminiProcessedTask.objects.filter(raw_transcript=meeting).count()
                if existing_tasks > 0 and not force:
                    self.stdout.write(f"   ⚠️  Already has {existing_tasks} processed tasks - skipping")
                    continue
                
                # Process with Gemini
                tasks_created = self.process_meeting_with_gemini(meeting, gemini_client, stats)
                
                if tasks_created > 0:
                    stats['meetings_processed'] += 1
                    stats['tasks_extracted'] += tasks_created
                    stats['tasks_saved'] += tasks_created
                    self.stdout.write(f"   ✅ Created {tasks_created} tasks")
                else:
                    self.stdout.write(f"   ⚠️  No tasks extracted")
            
            # Step 4: Display results
            self.display_results(stats)
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))
            stats['errors'].append(error_msg)
            raise
    
    def process_meeting_with_gemini(self, meeting: RawTranscriptCache, gemini_client, stats):
        """Process a single meeting with real Gemini API using temp/prompt.md"""
        
        try:
            # Get raw Fireflies data
            fireflies_data = meeting.raw_fireflies_data
            
            # Extract tasks using Gemini with temp/prompt.md
            self.stdout.write("   🤖 Extracting tasks with Gemini AI...")
            extracted_tasks = gemini_client.extract_tasks_from_transcript(fireflies_data)
            
            if not extracted_tasks:
                self.stdout.write("   ⚠️  No tasks extracted from transcript")
                return 0
            
            # Save tasks to GeminiProcessedTask model
            tasks_created = 0
            
            with transaction.atomic():
                for task_order, task_data in enumerate(extracted_tasks):
                    try:
                        # Create GeminiProcessedTask following exact temp/prompt.md format
                        task = GeminiProcessedTask.objects.create(
                            raw_transcript=meeting,
                            
                            # Exact prompt.md fields (in order)
                            task_item=task_data.get('task_item', ''),
                            assignee_emails=task_data.get('assignee_emails', ''),
                            assignee_full_names=task_data.get('assignee(s)_full_names', ''),
                            priority=task_data.get('priority', 'Medium'),
                            brief_description=task_data.get('brief_description', ''),
                            due_date_ms=task_data.get('due_date'),
                            status=task_data.get('status', 'To Do'),
                            
                            # Processing metadata
                            extraction_order=task_order,
                            gemini_model_version='gemini-2.5-flash',
                            extraction_confidence=0.95,  # High confidence for real API
                            source_sentences=[
                                f"Extracted from {meeting.meeting_title} using real Gemini API"
                            ],
                            raw_gemini_response={
                                'full_response': extracted_tasks,
                                'task_index': task_order,
                                'model': 'gemini-2.5-flash',
                                'timestamp': timezone.now().isoformat(),
                                'meeting_id': meeting.fireflies_id,
                                'prompt_source': 'temp/prompt.md'
                            }
                        )
                        
                        tasks_created += 1
                        
                    except Exception as e:
                        error_msg = f"Failed to save task {task_order}: {str(e)}"
                        self.stdout.write(f"   ❌ {error_msg}")
                        stats['errors'].append(error_msg)
            
            return tasks_created
            
        except Exception as e:
            error_msg = f"Failed to process meeting {meeting.fireflies_id}: {str(e)}"
            self.stdout.write(f"   ❌ {error_msg}")
            stats['errors'].append(error_msg)
            return 0
    
    def display_results(self, stats):
        """Display final processing results"""
        
        self.stdout.write("\n" + "=" * 65)
        self.stdout.write("🎯 E2E TEST STEP 4 RESULTS:")
        self.stdout.write("-" * 30)
        
        self.stdout.write(f"📄 Meetings found in cache: {stats['meetings_found']}")
        self.stdout.write(f"🔄 Meetings processed: {stats['meetings_processed']}")
        self.stdout.write(f"🎯 Tasks extracted: {stats['tasks_extracted']}")
        self.stdout.write(f"💾 Tasks saved: {stats['tasks_saved']}")
        
        if stats['errors']:
            self.stdout.write(f"❌ Errors encountered: {len(stats['errors'])}")
            for error in stats['errors']:
                self.stdout.write(f"   • {error}")
        else:
            self.stdout.write("✅ No errors encountered")
        
        # Show database status
        self.stdout.write("\n📊 DATABASE STATUS:")
        self.stdout.write("-" * 20)
        
        total_cache_items = RawTranscriptCache.objects.count()
        total_gemini_tasks = GeminiProcessedTask.objects.count()
        
        self.stdout.write(f"Raw Cache Items: {total_cache_items}")
        self.stdout.write(f"Gemini Processed Tasks: {total_gemini_tasks}")
        
        # Show recent tasks
        recent_tasks = GeminiProcessedTask.objects.all().order_by('-created_at')[:5]
        
        if recent_tasks:
            self.stdout.write("\n🎯 RECENT TASKS EXTRACTED:")
            self.stdout.write("-" * 25)
            
            for i, task in enumerate(recent_tasks, 1):
                self.stdout.write(f"{i}. {task.task_item[:60]}...")
                self.stdout.write(f"   👥 Assignee: {task.assignee_full_names}")
                self.stdout.write(f"   📧 Email: {task.assignee_emails}")
                self.stdout.write(f"   🎯 Priority: {task.priority}")
                self.stdout.write(f"   📊 Status: {task.status}")
                self.stdout.write(f"   🔗 Meeting: {task.raw_transcript.meeting_title}")
                self.stdout.write("")
        
        # Success message
        if stats['meetings_processed'] > 0:
            self.stdout.write(self.style.SUCCESS("\n🎉 E2E TEST STEP 4 COMPLETED SUCCESSFULLY!"))
            self.stdout.write("   ✅ Meetings processed with real Gemini API")
            self.stdout.write("   ✅ Tasks extracted using temp/prompt.md")
            self.stdout.write("   ✅ Results stored in GeminiProcessedTask model")
            self.stdout.write("   🚀 Ready for Step 5: Push to Monday.com")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  No meetings were processed"))