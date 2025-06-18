import json
import os
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime
from apps.core.models import Transcript, RawTranscriptCache, ProcessedTaskData
from apps.core.precision_extractor import PrecisionTaskExtractor


class Command(BaseCommand):
    help = 'Populate database with REAL data from 7_meetings.json with proper chronological categorization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='temp/7_meetings.json',
            help='Path to JSON file with meeting data'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        self.stdout.write("🎯 POPULATING DATABASE WITH REAL MEETING DATA")
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
            
            # Extract transcripts from data
            transcripts = self._extract_transcripts_from_data(data)
            
            self.stdout.write(f"📊 Found {len(transcripts)} transcripts to process")
            
            # Process each transcript
            cache_items_created = 0
            processed_tasks_created = 0
            
            for transcript_data in transcripts:
                # Create cache item
                cache_item = self._create_cache_item(transcript_data)
                if cache_item:
                    cache_items_created += 1
                    
                    # Create transcript record
                    transcript = self._create_transcript_record(transcript_data, cache_item)
                    
                    # Create processed task data records
                    tasks_created = self._create_processed_tasks(transcript_data, transcript)
                    processed_tasks_created += tasks_created
                    
                    self.stdout.write(f"   ✅ {transcript.title}: {tasks_created} tasks extracted")
            
            # Display results
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("✅ REAL DATA POPULATION COMPLETED:")
            self.stdout.write(f"📝 Cache items created: {cache_items_created}")
            self.stdout.write(f"📋 Transcripts processed: {cache_items_created}")
            self.stdout.write(f"🎯 Processed tasks created: {processed_tasks_created}")
            
            # Show chronological organization
            self._show_chronological_organization()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error processing file: {str(e)}")
            )
            raise

    def _extract_transcripts_from_data(self, data: Any) -> List[Dict[str, Any]]:
        """Extract transcript objects from various JSON structures"""
        transcripts = []
        
        if isinstance(data, list):
            for item in data:
                if 'data' in item and 'transcripts' in item['data']:
                    transcripts.extend(item['data']['transcripts'])
                elif 'transcripts' in item:
                    transcripts.extend(item['transcripts'])
                else:
                    transcripts.append(item)
        elif isinstance(data, dict):
            if 'data' in data and 'transcripts' in data['data']:
                transcripts = data['data']['transcripts']
            elif 'transcripts' in data:
                transcripts = data['transcripts']
            else:
                transcripts = [data]
        
        return transcripts

    def _create_cache_item(self, transcript_data: Dict[str, Any]) -> RawTranscriptCache:
        """Create unassailable cache item from transcript data"""
        try:
            fireflies_id = transcript_data.get('id', '')
            if not fireflies_id:
                return None
            
            # Parse meeting date
            date_value = transcript_data.get('date')
            if isinstance(date_value, (int, float)):
                meeting_date = datetime.fromtimestamp(date_value / 1000, tz=timezone.utc)
            elif isinstance(date_value, str):
                meeting_date = parse_datetime(date_value) or datetime.now(timezone.utc)
            else:
                meeting_date = datetime.now(timezone.utc)
            
            # Extract metadata
            title = transcript_data.get('title', 'Untitled Meeting')
            meeting_attendees = transcript_data.get('meeting_attendees', [])
            participant_count = len(meeting_attendees) if meeting_attendees else 0
            
            # Generate hash for integrity
            raw_data_str = json.dumps(transcript_data, sort_keys=True)
            data_hash = hashlib.sha256(raw_data_str.encode()).hexdigest()
            
            # Create cache item
            cache_item, created = RawTranscriptCache.objects.get_or_create(
                fireflies_id=fireflies_id,
                defaults={
                    'raw_fireflies_data': transcript_data,
                    'meeting_date': meeting_date,
                    'meeting_title': title,
                    'participant_count': participant_count,
                    'data_hash': data_hash,
                    'is_valid': True,
                }
            )
            
            if created:
                self.stdout.write(f"   📦 Created cache: {title} ({meeting_date.strftime('%Y-%m-%d')})")
            
            return cache_item
            
        except Exception as e:
            self.stdout.write(f"   ❌ Error creating cache item: {str(e)}")
            return None

    def _create_transcript_record(self, transcript_data: Dict[str, Any], cache_item: RawTranscriptCache) -> Transcript:
        """Create transcript record linked to cache item"""
        
        # Extract content from sentences
        content_parts = []
        sentences = transcript_data.get('sentences', [])
        if sentences:
            for sentence in sentences:
                speaker = sentence.get('speaker_name', 'Unknown')
                text = sentence.get('text', sentence.get('raw_text', ''))
                if text:
                    content_parts.append(f"{speaker}: {text}")
        
        content = '\n'.join(content_parts) if content_parts else 'No content available'
        
        # Duration
        duration = transcript_data.get('duration', 0)
        duration_minutes = int(duration / 60) if duration else 0
        
        transcript, created = Transcript.objects.get_or_create(
            fireflies_id=cache_item.fireflies_id,
            defaults={
                'title': cache_item.meeting_title,
                'meeting_date': cache_item.meeting_date,
                'duration_minutes': duration_minutes,
                'participant_count': cache_item.participant_count,
                'raw_data': transcript_data,
                'content': content,
                'is_processed': True,
            }
        )
        
        return transcript

    def _create_processed_tasks(self, transcript_data: Dict[str, Any], transcript: Transcript) -> int:
        """Create ProcessedTaskData records from transcript action items"""
        
        summary = transcript_data.get('summary')
        if not summary:
            return 0
            
        action_items_text = summary.get('action_items', '')
        
        if not action_items_text:
            return 0
        
        # Parse action items from text
        lines = action_items_text.split('\n')
        current_assignee = None
        tasks_created = 0
        
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
                import re
                timestamp_pattern = r'\((\d{1,2}:\d{2})\)'
                match = re.search(timestamp_pattern, task_text)
                if match:
                    task_text = re.sub(timestamp_pattern, '', task_text).strip()
                
                if task_text and len(task_text.split()) >= 3:  # At least 3 words
                    # Determine priority based on keywords
                    priority = 'Medium'
                    if any(keyword in task_text.lower() for keyword in ['urgent', 'asap', 'immediately', 'critical']):
                        priority = 'High'
                    elif any(keyword in task_text.lower() for keyword in ['consider', 'evaluate', 'research', 'explore']):
                        priority = 'Low'
                    
                    # Create brief description (30-50 words)
                    words = task_text.split()
                    if len(words) > 50:
                        brief_description = ' '.join(words[:45]) + '...'
                    else:
                        brief_description = task_text
                    
                    # Extract email from assignee name
                    assignee_email = ""
                    if current_assignee:
                        # Try to find email in meeting attendees
                        attendees = transcript_data.get('meeting_attendees', [])
                        if attendees:
                            for attendee in attendees:
                                attendee_name = attendee.get('displayName', '') or ''
                                if current_assignee.lower() in attendee_name.lower():
                                    assignee_email = attendee.get('email', '')
                                    break
                    
                    # Create ProcessedTaskData
                    ProcessedTaskData.objects.create(
                        transcript=transcript,
                        task_item=task_text,
                        assignee_emails=assignee_email,
                        assignee_full_names=current_assignee or 'Unassigned',
                        priority=priority,
                        brief_description=brief_description,
                        status='To Do',
                        extraction_confidence=0.85,  # High confidence from manual parsing
                        source_sentences=[],  # Will be populated by precision extractor later
                        processing_notes=f'Extracted from Fireflies summary action items',
                        human_approved=False,
                        delivery_status='pending'
                    )
                    
                    tasks_created += 1
        
        return tasks_created

    def _show_chronological_organization(self):
        """Show how data is organized chronologically"""
        self.stdout.write("\n📅 CHRONOLOGICAL ORGANIZATION:")
        self.stdout.write("-" * 50)
        
        # Get all transcripts ordered by date
        transcripts = Transcript.objects.order_by('-meeting_date')
        
        for transcript in transcripts:
            task_count = transcript.processed_tasks.count()
            self.stdout.write(
                f"📋 {transcript.meeting_date.strftime('%Y-%m-%d %H:%M')} - "
                f"{transcript.title} ({task_count} tasks)"
            )
            
            # Show sample tasks
            for task in transcript.processed_tasks.all()[:2]:
                self.stdout.write(f"   • {task.task_item[:60]}...")
        
        self.stdout.write(f"\n🎯 Total: {ProcessedTaskData.objects.count()} processed tasks ready for review") 