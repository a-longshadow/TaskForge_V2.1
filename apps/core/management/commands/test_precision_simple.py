"""
Simple test for N8N-Inspired Precision Pipeline
"""

import json
import os
from datetime import datetime, timezone
from django.core.management.base import BaseCommand

from apps.core.models import RawTranscriptCache, ProcessedTaskData
from apps.core.precision_extractor import PrecisionTaskExtractor


class Command(BaseCommand):
    help = 'Simple test of the precision pipeline with 7_meetings.json'

    def handle(self, *args, **options):
        self.stdout.write("🎯 SIMPLE PRECISION PIPELINE TEST")
        self.stdout.write("=" * 50)
        
        # Load test data
        file_path = 'temp/7_meetings.json'
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"❌ File not found: {file_path}"))
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.stdout.write(f"📄 Loaded data from {file_path}")
        
        # Extract first transcript for testing
        transcripts = self._extract_transcripts_from_data(data)
        if not transcripts:
            self.stdout.write("❌ No transcripts found")
            return
        
        test_transcript = transcripts[0]
        fireflies_id = test_transcript.get('id', 'test_001')
        
        self.stdout.write(f"🔍 Testing with: {test_transcript.get('title', 'Untitled')}")
        
        # Create cache item
        cache_item = self._create_cache_item(test_transcript, fireflies_id)
        if not cache_item:
            self.stdout.write("❌ Failed to create cache item")
            return
        
        self.stdout.write("✅ Cache item created")
        
        # Test precision extraction
        extractor = PrecisionTaskExtractor()
        
        try:
            processed_tasks = extractor.extract_tasks_from_cache(cache_item)
            
            if processed_tasks:
                self.stdout.write(f"✅ Extracted {len(processed_tasks)} tasks")
                
                # Save and display tasks
                for i, task in enumerate(processed_tasks, 1):
                    task.save()
                    self.stdout.write(f"\n📋 Task {i}:")
                    self.stdout.write(f"   • Item: {task.task_item}")
                    self.stdout.write(f"   • Assignee: {task.assignee_full_names}")
                    self.stdout.write(f"   • Email: {task.assignee_emails}")
                    self.stdout.write(f"   • Priority: {task.priority}")
                    self.stdout.write(f"   • Status: {task.status}")
                    self.stdout.write(f"   • Description: {task.brief_description[:100]}...")
                
                self.stdout.write(f"\n🎯 SUCCESS: Precision pipeline working!")
                self.stdout.write(f"📊 Database now has:")
                self.stdout.write(f"   • Cache items: {RawTranscriptCache.objects.count()}")
                self.stdout.write(f"   • Processed tasks: {ProcessedTaskData.objects.count()}")
                
            else:
                self.stdout.write("⚠️  No tasks extracted - check extraction logic")
                
        except Exception as e:
            self.stdout.write(f"❌ Extraction failed: {str(e)}")
            raise

    def _extract_transcripts_from_data(self, data):
        """Extract transcript objects from JSON data"""
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

    def _create_cache_item(self, transcript_data: dict, fireflies_id: str):
        """Create a cache item from transcript data"""
        try:
            # Parse meeting date
            date_value = transcript_data.get('date')
            if isinstance(date_value, (int, float)):
                meeting_date = datetime.fromtimestamp(date_value / 1000, tz=timezone.utc)
            else:
                meeting_date = datetime.now(timezone.utc)
            
            # Extract metadata safely
            meeting_title = transcript_data.get('title', 'Test Meeting')
            attendees = transcript_data.get('meeting_attendees') or []
            participant_count = len(attendees) if attendees else 0
            duration = transcript_data.get('duration', 0)
            duration_minutes = int(duration / 60) if duration else 0
            
            # Create or get cache item
            cache_item, created = RawTranscriptCache.objects.get_or_create(
                fireflies_id=fireflies_id,
                defaults={
                    'raw_fireflies_data': transcript_data,
                    'meeting_date': meeting_date,
                    'meeting_title': meeting_title,
                    'participant_count': participant_count,
                    'duration_minutes': duration_minutes,
                    'processed': False
                }
            )
            
            return cache_item
            
        except Exception as e:
            self.stdout.write(f"❌ Failed to create cache item: {str(e)}")
            return None 