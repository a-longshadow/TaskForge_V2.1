import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime
from apps.core.models import Transcript, ActionItem
from apps.core.event_bus import publish_event, EventTypes


class Command(BaseCommand):
    help = 'Populate database with detailed meeting data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='temp/7_meetings.json',
            help='Path to JSON file with meeting data'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        
        self.stdout.write("🚀 POPULATING DATABASE FROM DETAILED MEETING DATA")
        self.stdout.write("=" * 60)
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f"❌ File not found: {file_path}")
            )
            return
        
        try:
            # Load JSON data
            self.stdout.write(f"📄 Loading data from {file_path}...")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process transcripts
            transcripts_processed = 0
            action_items_processed = 0
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of transcript objects
                for item in data:
                    if 'data' in item and 'transcripts' in item['data']:
                        # Fireflies API response format
                        transcripts = item['data']['transcripts']
                    elif 'transcripts' in item:
                        # Direct transcripts array
                        transcripts = item['transcripts']
                    else:
                        # Single transcript object
                        transcripts = [item]
                    
                    for transcript_data in transcripts:
                        result = self.process_transcript(transcript_data, dry_run)
                        if result:
                            transcripts_processed += 1
                            action_items_processed += result.get('action_items_count', 0)
            
            elif isinstance(data, dict):
                if 'data' in data and 'transcripts' in data['data']:
                    # Single Fireflies API response
                    transcripts = data['data']['transcripts']
                elif 'transcripts' in data:
                    # Direct transcripts object
                    transcripts = data['transcripts']
                else:
                    # Single transcript
                    transcripts = [data]
                
                for transcript_data in transcripts:
                    result = self.process_transcript(transcript_data, dry_run)
                    if result:
                        transcripts_processed += 1
                        action_items_processed += result.get('action_items_count', 0)
            
            # Display results
            self.stdout.write("\n" + "=" * 60)
            if dry_run:
                self.stdout.write("🔍 DRY RUN RESULTS:")
            else:
                self.stdout.write("✅ IMPORT COMPLETED:")
            
            self.stdout.write(f"📝 Transcripts processed: {transcripts_processed}")
            self.stdout.write(f"🎯 Action items extracted: {action_items_processed}")
            
            if not dry_run:
                self.stdout.write("\n💾 Database populated successfully!")
                self.stdout.write("🔍 Use Django admin or API to view the imported data")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error processing file: {str(e)}")
            )
            raise

    def process_transcript(self, transcript_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Process a single transcript and extract action items"""
        
        try:
            # Extract basic info
            fireflies_id = transcript_data.get('id', '')
            title = transcript_data.get('title', 'Untitled Meeting')
            
            # Parse meeting date
            date_value = transcript_data.get('date')
            if isinstance(date_value, (int, float)):
                # Unix timestamp in milliseconds
                meeting_date = datetime.fromtimestamp(date_value / 1000, tz=timezone.utc)
            elif isinstance(date_value, str):
                # ISO date string
                meeting_date = parse_datetime(date_value) or datetime.now(timezone.utc)
            else:
                meeting_date = datetime.now(timezone.utc)
            
            # Extract duration and participants
            duration = transcript_data.get('duration', 0)
            duration_minutes = int(duration / 60) if duration else 0
            
            # Count participants from sentences or attendees
            participants = set()
            sentences = transcript_data.get('sentences', [])
            for sentence in sentences:
                speaker_name = sentence.get('speaker_name')
                if speaker_name:
                    participants.add(speaker_name)
            
            # Also check meeting_attendees
            attendees = transcript_data.get('meeting_attendees', [])
            for attendee in attendees:
                name = attendee.get('displayName') or attendee.get('name')
                if name:
                    participants.add(name)
            
            participant_count = len(participants)
            
            # Extract content from sentences
            content_parts = []
            for sentence in sentences:
                speaker = sentence.get('speaker_name', 'Unknown')
                text = sentence.get('text', sentence.get('raw_text', ''))
                if text:
                    content_parts.append(f"{speaker}: {text}")
            
            content = '\n'.join(content_parts)
            
            self.stdout.write(f"\n📝 Processing: {title}")
            self.stdout.write(f"   📅 Date: {meeting_date.strftime('%Y-%m-%d %H:%M')}")
            self.stdout.write(f"   ⏱️  Duration: {duration_minutes} minutes")
            self.stdout.write(f"   👥 Participants: {participant_count}")
            
            if dry_run:
                self.stdout.write("   🔍 [DRY RUN] Would create transcript record")
                action_items_count = self.extract_action_items_count(transcript_data)
                self.stdout.write(f"   🎯 [DRY RUN] Would extract {action_items_count} action items")
                return {'action_items_count': action_items_count}
            
            # Create or update transcript
            with transaction.atomic():
                transcript, created = Transcript.objects.get_or_create(
                    fireflies_id=fireflies_id,
                    defaults={
                        'title': title,
                        'meeting_date': meeting_date,
                        'duration_minutes': duration_minutes,
                        'participant_count': participant_count,
                        'raw_data': transcript_data,
                        'content': content,
                        'is_processed': False,
                    }
                )
                
                if created:
                    self.stdout.write("   ✅ Created new transcript record")
                    
                    # Publish event
                    publish_event(
                        EventTypes.TRANSCRIPT_INGESTED,
                        {
                            'transcript_id': str(transcript.id),
                            'fireflies_id': fireflies_id,
                            'title': title,
                            'participant_count': participant_count,
                            'duration_minutes': duration_minutes,
                        },
                        source_module='database_import'
                    )
                else:
                    self.stdout.write("   ⚠️  Transcript already exists, updating data")
                    transcript.raw_data = transcript_data
                    transcript.content = content
                    transcript.save()
                
                # Extract and create action items
                action_items_count = self.extract_action_items(transcript, transcript_data)
                
                # Mark as processed
                transcript.mark_processed()
                
                self.stdout.write(f"   🎯 Extracted {action_items_count} action items")
                
                return {'action_items_count': action_items_count}
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error processing transcript: {str(e)}")
            )
            return None

    def extract_action_items_count(self, transcript_data: Dict[str, Any]) -> int:
        """Count action items without creating them (for dry run)"""
        summary = transcript_data.get('summary', {})
        action_items_text = summary.get('action_items', '')
        
        if not action_items_text:
            return 0
        
        # Simple count based on line breaks and bullet points
        lines = action_items_text.split('\n')
        action_items = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or 
                        line.startswith('•') or '(' in line):
                # Looks like an action item
                action_items.append(line)
        
        return len(action_items)

    def extract_action_items(self, transcript: Transcript, transcript_data: Dict[str, Any]) -> int:
        """Extract action items from transcript summary"""
        
        summary = transcript_data.get('summary', {})
        action_items_text = summary.get('action_items', '')
        
        if not action_items_text:
            return 0
        
        # Parse action items from text
        lines = action_items_text.split('\n')
        current_assignee = None
        action_items_created = 0
        
        for line in lines:
            line = line.strip()
            
            # Check if this is an assignee header (e.g., "**Vardhan Shorewala**")
            if line.startswith('**') and line.endswith('**'):
                current_assignee = line.strip('*').strip()
                continue
            
            # Check if this is an action item
            if line and (line.startswith('-') or line.startswith('*') or 
                        line.startswith('•') or '(' in line):
                
                # Extract task description and timestamp
                task_text = line.lstrip('-*• ').strip()
                
                # Extract timestamp if present (format like "(02:14)")
                timestamp_match = None
                import re
                timestamp_pattern = r'\((\d{1,2}:\d{2})\)'
                match = re.search(timestamp_pattern, task_text)
                if match:
                    timestamp_match = match.group(1)
                    task_text = re.sub(timestamp_pattern, '', task_text).strip()
                
                if task_text:
                    # Determine priority based on keywords
                    priority = 'medium'
                    if any(keyword in task_text.lower() for keyword in ['urgent', 'asap', 'immediately']):
                        priority = 'high'
                    elif any(keyword in task_text.lower() for keyword in ['consider', 'evaluate', 'research']):
                        priority = 'low'
                    
                    # Create action item
                    action_item = ActionItem.objects.create(
                        transcript=transcript,
                        title=task_text[:200],  # Truncate if too long
                        description=task_text,
                        assignee=current_assignee or 'Unassigned',
                        priority=priority,
                        status='pending',
                        confidence_score=0.8,  # Good confidence from manual extraction
                        ai_model_version='manual_extraction_v1',
                        extraction_metadata={
                            'source': 'fireflies_summary',
                            'timestamp': timestamp_match,
                            'extraction_method': 'text_parsing'
                        }
                    )
                    
                    action_items_created += 1
                    
                    # Publish event
                    publish_event(
                        EventTypes.TASK_CREATED,
                        {
                            'task_id': str(action_item.id),
                            'transcript_id': str(transcript.id),
                            'title': action_item.title,
                            'assignee': action_item.assignee,
                            'priority': action_item.priority,
                        },
                        source_module='database_import'
                    )
        
        return action_items_created 