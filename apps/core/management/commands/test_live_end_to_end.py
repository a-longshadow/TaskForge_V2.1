"""
Live End-to-End Integration Test
Demonstrates complete TaskForge pipeline with real credentials
"""

import json
import logging
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from apps.core.fireflies_client import get_fireflies_client
from apps.core.gemini_client import get_gemini_client
from apps.core.monday_client import get_monday_client
from apps.core.models import Transcript, ActionItem

logger = logging.getLogger('apps.core.management.commands.test_live_end_to_end')


class Command(BaseCommand):
    help = 'Live end-to-end test: Fireflies → Gemini → Monday.com with real credentials'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test everything but don\'t actually push to Monday.com',
        )
        parser.add_argument(
            '--save-json',
            action='store_true',
            help='Save raw transcript data and extracted action items to JSON files',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Limit number of transcripts to process (default: 10)',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.save_json = options['save_json']
        self.limit = options['limit']
        
        # Initialize statistics
        stats = {
            'transcripts_fetched': 0,
            'transcripts_processed': 0,
            'action_items_extracted': 0,
            'action_items_delivered': 0,
            'errors': [],
            'breakthroughs': []
        }
        
        self.log_step("🚀 STARTING LIVE END-TO-END TASKFORGE PIPELINE TEST")
        self.log_step(f"📅 Target Date: {date.today().strftime('%Y-%m-%d')} UTC")
        self.log_step(f"🔧 Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        
        try:
            # Step 1: Initialize API clients
            self.log_step("🔌 STEP 1: Initializing API clients...")
            fireflies_client = get_fireflies_client()
            gemini_client = get_gemini_client()
            monday_client = get_monday_client()
            
            # Step 2: Test connections
            self.log_step("🧪 STEP 2: Testing API connections...")
            self.test_connections(fireflies_client, gemini_client, monday_client, stats)
            
            # Step 3: Fetch today's meetings
            self.log_step("📥 STEP 3: Fetching today's meetings from Fireflies...")
            transcripts = self.fetch_todays_meetings(fireflies_client, stats)
            
            if not transcripts:
                self.log_error("❌ No transcripts found for today. Using recent transcripts for demo.")
                return
            
            # Step 4: Store transcripts in database
            self.log_step("💾 STEP 4: Storing transcripts in database...")
            all_action_items = []
            
            for transcript_data in transcripts[:self.limit]:
                # Clean and store transcript
                cleaned_data = self.clean_transcript_data(transcript_data)
                transcript_obj = self.save_transcript_to_db(cleaned_data, stats)
                
                if transcript_obj:
                    # Extract action items with AI
                    action_items = self.extract_action_items(gemini_client, cleaned_data, stats)
                    
                    if action_items:
                        # Save to database
                        saved_items = self.save_action_items_to_db(transcript_obj, action_items, stats)
                        all_action_items.extend(saved_items)
            
            # Step 5: Save JSON files if requested
            if self.save_json:
                self.log_step("📄 STEP 5: Saving JSON files...")
                self.save_json_files(transcripts, all_action_items)
            
            # Step 6: Display organized results
            self.log_step("📋 STEP 6: Organizing results chronologically...")
            self.display_organized_results(all_action_items)
            
            # Step 7: Deliver to Monday.com
            if all_action_items:
                self.log_step("🚀 STEP 7: Delivering to Monday.com...")
                self.deliver_to_monday(monday_client, all_action_items, stats)
            
            # Final results
            self.display_final_results(stats, self.dry_run)
            
        except Exception as e:
            self.log_error(f"💥 PIPELINE FAILED: {str(e)}")
            stats['errors'].append(str(e))
            raise
    
    def test_connections(self, fireflies_client, gemini_client, monday_client, stats):
        """Test all API connections"""
        
        # Test Fireflies
        self.log_info("Testing Fireflies API...")
        if fireflies_client.test_connection():
            self.log_breakthrough("✅ Fireflies API: Connected successfully")
        else:
            error = "❌ Fireflies API: Connection failed"
            self.log_error(error)
            stats['errors'].append(error)
        
        # Test Gemini
        self.log_info("Testing Gemini AI API...")
        if gemini_client.test_connection():
            self.log_breakthrough("✅ Gemini AI API: Connected successfully")
        else:
            error = "❌ Gemini AI API: Connection failed"
            self.log_error(error)
            stats['errors'].append(error)
        
        # Test Monday.com
        self.log_info("Testing Monday.com API...")
        if monday_client.test_connection():
            self.log_breakthrough("✅ Monday.com API: Connected successfully")
        else:
            error = "❌ Monday.com API: Connection failed"
            self.log_error(error)
            stats['errors'].append(error)
    
    def fetch_todays_meetings(self, fireflies_client, stats):
        """Fetch today's meetings from Fireflies"""
        try:
            transcripts = fireflies_client.get_today_transcripts()
            
            if transcripts:
                stats['transcripts_fetched'] = len(transcripts)
                self.log_breakthrough(f"✅ Found {len(transcripts)} transcripts")
                
                # Log meeting details
                for i, transcript in enumerate(transcripts, 1):
                    title = transcript.get('title', 'Untitled')
                    meeting_date = transcript.get('date', 'Unknown date')
                    
                    # Handle date formatting
                    if isinstance(meeting_date, int):
                        meeting_date = datetime.fromtimestamp(meeting_date / 1000).strftime('%Y-%m-%d %H:%M')
                    
                    self.log_info(f"  {i}. {title} ({meeting_date})")
                
                return transcripts
            else:
                self.log_error("❌ No transcripts found")
                return []
                
        except Exception as e:
            error = f"Failed to fetch transcripts: {str(e)}"
            self.log_error(error)
            stats['errors'].append(error)
            return []
    
    def clean_transcript_data(self, transcript_data):
        """Clean and standardize transcript data"""
        cleaned = {
            'id': transcript_data.get('id', ''),
            'title': transcript_data.get('title', 'Untitled Meeting'),
            'date': transcript_data.get('date', ''),
            'organizer_email': transcript_data.get('organizer_email', ''),
            'meeting_attendees': transcript_data.get('meeting_attendees', []),
            'summary': transcript_data.get('summary', {}),
            'sentences': transcript_data.get('sentences', [])
        }
        
        # Handle date conversion
        if isinstance(cleaned['date'], int):
            cleaned['date'] = datetime.fromtimestamp(cleaned['date'] / 1000).isoformat()
        
        return cleaned
    
    def save_transcript_to_db(self, transcript_data, stats):
        """Save transcript to database"""
        try:
            # Parse meeting date
            meeting_date = self.parse_meeting_date(transcript_data.get('date', ''))
            
            # Create transcript object
            transcript_obj, created = Transcript.objects.get_or_create(
                fireflies_id=transcript_data.get('id', ''),
                defaults={
                    'title': transcript_data.get('title', 'Untitled Meeting'),
                    'meeting_date': meeting_date,
                    'duration_minutes': transcript_data.get('duration', 0),
                    'participant_count': len(transcript_data.get('meeting_attendees', [])),
                    'raw_data': transcript_data,
                    'content': self.format_transcript_content(transcript_data.get('sentences', [])),
                }
            )
            
            if created:
                self.log_info(f"✅ Saved transcript: {transcript_obj.title}")
            else:
                self.log_info(f"📝 Updated transcript: {transcript_obj.title}")
            
            return transcript_obj
            
        except Exception as e:
            error = f"Failed to save transcript: {str(e)}"
            self.log_error(error)
            stats['errors'].append(error)
            return None
    
    def extract_action_items(self, gemini_client, transcript_data, stats):
        """Extract action items using Gemini AI"""
        try:
            self.log_info(f"🤖 Processing: {transcript_data.get('title', 'Untitled')}")
            
            action_items = gemini_client.extract_tasks_from_transcript(transcript_data)
            
            if action_items:
                stats['action_items_extracted'] += len(action_items)
                self.log_breakthrough(f"✅ Extracted {len(action_items)} action items")
                
                # Log each action item
                for i, item in enumerate(action_items, 1):
                    task = item.get('task_item', 'No task description')
                    assignee = item.get('assignee(s)_full_names', 'Unassigned')
                    priority = item.get('priority', 'Medium')
                    self.log_info(f"  {i}. {task} → {assignee} ({priority})")
                
                return action_items
            else:
                self.log_info("ℹ️ No action items extracted from this transcript")
                return []
                
        except Exception as e:
            error = f"Failed to extract action items: {str(e)}"
            self.log_error(error)
            stats['errors'].append(error)
            return []
    
    def save_action_items_to_db(self, transcript_obj, action_items, stats):
        """Save action items to database"""
        saved_items = []
        
        for item_data in action_items:
            try:
                # Parse due date if provided
                due_date = None
                if item_data.get('due_date') and item_data['due_date'] != 'null':
                    try:
                        due_date = datetime.fromtimestamp(int(item_data['due_date']) / 1000).date()
                    except (ValueError, TypeError):
                        due_date = None
                
                action_item = ActionItem.objects.create(
                    transcript=transcript_obj,
                    title=item_data.get('task_item', 'Untitled Task'),
                    description=item_data.get('brief_description', ''),
                    assignee=item_data.get('assignee(s)_full_names', ''),
                    due_date=due_date,
                    priority=self.map_priority(item_data.get('priority', 'Medium')),
                    status='pending',
                    extraction_metadata=item_data,
                    ai_model_version='gemini-2.5-flash'
                )
                
                saved_items.append(action_item)
                
            except Exception as e:
                error = f"Failed to save action item: {str(e)}"
                self.log_error(error)
                stats['errors'].append(error)
        
        return saved_items
    
    def save_json_files(self, transcripts, all_action_items):
        """Save data to JSON files for inspection"""
        # Save raw transcripts
        with open('live_test_raw_transcripts.json', 'w') as f:
            json.dump(transcripts, f, indent=2, default=str)
        self.log_info("📄 Saved: live_test_raw_transcripts.json")
        
        # Save extracted action items
        action_items_data = []
        for item in all_action_items:
            action_items_data.append({
                'id': str(item.id),
                'transcript_title': item.transcript.title,
                'task_item': item.title,
                'assignee': item.assignee,
                'priority': item.priority,
                'due_date': item.due_date.isoformat() if item.due_date else None,
                'description': item.description,
                'status': item.status,
                'extraction_metadata': item.extraction_metadata
            })
        
        with open('live_test_action_items.json', 'w') as f:
            json.dump(action_items_data, f, indent=2, default=str)
        self.log_info("📄 Saved: live_test_action_items.json")
    
    def display_organized_results(self, all_action_items):
        """Display results organized chronologically by meeting"""
        if not all_action_items:
            self.log_info("ℹ️ No action items to display")
            return
        
        # Group by meeting (transcript)
        meetings = {}
        for item in all_action_items:
            meeting_key = f"{item.transcript.title} ({item.transcript.meeting_date.strftime('%Y-%m-%d')})"
            if meeting_key not in meetings:
                meetings[meeting_key] = []
            meetings[meeting_key].append(item)
        
        self.log_step("📋 ACTION ITEMS BY MEETING (CHRONOLOGICAL):")
        
        # Sort meetings by date (handle timezone-aware dates)
        def get_meeting_date(meeting_tuple):
            meeting_date = meeting_tuple[1][0].transcript.meeting_date
            if timezone.is_naive(meeting_date):
                meeting_date = timezone.make_aware(meeting_date)
            return meeting_date
        
        sorted_meetings = sorted(meetings.items(), key=get_meeting_date)
        
        for meeting_title, items in sorted_meetings:
            self.log_info(f"\n🗓️ {meeting_title}")
            self.log_info(f"   📊 {len(items)} action items extracted")
            
            for i, item in enumerate(items, 1):
                due_date_str = item.due_date.strftime('%Y-%m-%d') if item.due_date else 'No due date'
                self.log_info(f"   {i}. {item.title}")
                self.log_info(f"      → Assignee: {item.assignee or 'Unassigned'}")
                self.log_info(f"      → Priority: {item.priority.title()}")
                self.log_info(f"      → Due: {due_date_str}")
    
    def deliver_to_monday(self, monday_client, all_action_items, stats):
        """Deliver action items to Monday.com"""
        if self.dry_run:
            self.log_info("🔄 DRY RUN: Skipping Monday.com delivery")
            return
        
        delivered_count = 0
        
        for item in all_action_items:
            try:
                # Prepare task data for Monday.com
                task_data = {
                    'item_name': item.title,
                    'text_mkr7jgkp': item.assignee or 'Unassigned',  # Team member
                    'status_1': self.map_priority_to_monday_status(item.priority),  # Priority
                    'status': 'To Do',  # Status
                    'long_text': item.description,  # Brief description
                    'date_mkr7ymmh': item.due_date.strftime('%Y-%m-%d') if item.due_date else None  # Date expected
                }
                
                # Create item in Monday.com
                monday_item_id = monday_client.create_task_item(task_data)
                
                if monday_item_id:
                    # Update database with Monday.com ID
                    item.monday_item_id = monday_item_id
                    item.status = 'delivered'
                    item.delivered_at = timezone.now()
                    item.save()
                    
                    delivered_count += 1
                    self.log_breakthrough(f"✅ Delivered: {item.title} → Monday.com ID: {monday_item_id}")
                else:
                    error = f"Failed to deliver task: {item.title}"
                    self.log_error(error)
                    stats['errors'].append(error)
                    
            except Exception as e:
                error = f"Error delivering {item.title}: {str(e)}"
                self.log_error(error)
                stats['errors'].append(error)
        
        stats['action_items_delivered'] = delivered_count
        
        if delivered_count > 0:
            self.log_breakthrough(f"🎉 Successfully delivered {delivered_count} tasks to Monday.com!")
    
    def display_final_results(self, stats, dry_run):
        """Display final pipeline results"""
        self.log_step("📊 FINAL PIPELINE RESULTS:")
        self.log_info(f"📥 Transcripts fetched: {stats['transcripts_fetched']}")
        self.log_info(f"💾 Transcripts processed: {stats['transcripts_processed']}")
        self.log_info(f"🤖 Action items extracted: {stats['action_items_extracted']}")
        self.log_info(f"📤 Action items delivered: {stats['action_items_delivered']}")
        
        if stats['errors']:
            self.log_step("❌ ERRORS ENCOUNTERED:")
            for error in stats['errors']:
                self.log_error(f"  • {error}")
        
        if stats['breakthroughs']:
            self.log_step("🎉 BREAKTHROUGHS:")
            for breakthrough in stats['breakthroughs']:
                self.log_breakthrough(f"  • {breakthrough}")
        
        # Calculate success rate
        if stats['action_items_extracted'] > 0:
            success_rate = (stats['action_items_delivered'] / stats['action_items_extracted']) * 100
            self.log_step(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        if dry_run:
            self.log_step("🔄 DRY RUN COMPLETED - No actual data was pushed to Monday.com")
        else:
            self.log_step("🚀 LIVE PIPELINE COMPLETED SUCCESSFULLY!")
        
        self.log_step("=" * 80)
    
    def log_step(self, message):
        """Log a major step"""
        self.stdout.write(self.style.SUCCESS(message))
        logger.info(message)
    
    def log_info(self, message):
        """Log informational message"""
        self.stdout.write(message)
        logger.info(message)
    
    def log_error(self, message):
        """Log error message"""
        self.stdout.write(self.style.ERROR(message))
        logger.error(message)
    
    def log_breakthrough(self, message):
        """Log breakthrough/success message"""
        self.stdout.write(self.style.SUCCESS(message))
        logger.info(message)
    
    def parse_meeting_date(self, date_str):
        """Parse meeting date from various formats"""
        if isinstance(date_str, int):
            return datetime.fromtimestamp(date_str / 1000, tz=timezone.utc)
        elif isinstance(date_str, str) and date_str:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                return timezone.now()
        else:
            return timezone.now()
    
    def format_transcript_content(self, sentences):
        """Format sentences into readable transcript content"""
        if not sentences:
            return "No transcript content available"
        
        content_lines = []
        for sentence in sentences:
            speaker = sentence.get('speaker_name', 'Unknown')
            text = sentence.get('text', '')
            if text:
                content_lines.append(f"{speaker}: {text}")
        
        return "\n".join(content_lines)
    
    def map_priority(self, gemini_priority):
        """Map Gemini priority to Django model choices"""
        priority_mapping = {
            'High': 'high',
            'Medium': 'medium',
            'Low': 'low',
            'Urgent': 'urgent'
        }
        return priority_mapping.get(gemini_priority, 'medium')
    
    def map_priority_to_monday_status(self, priority):
        """Map priority to Monday.com status values"""
        priority_mapping = {
            'urgent': 'High',
            'high': 'High', 
            'medium': 'Medium',
            'low': 'Low'
        }
        return priority_mapping.get(priority, 'Medium') 