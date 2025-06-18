"""
Test the GeminiProcessedTask model with sample data following prompt.md specification
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import RawTranscriptCache, GeminiProcessedTask
import json
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Test GeminiProcessedTask model with sample data following prompt.md specification'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample',
            action='store_true',
            help='Create sample GeminiProcessedTask records'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List existing GeminiProcessedTask records'
        )
    
    def handle(self, *args, **options):
        if options['create_sample']:
            self.create_sample_data()
        elif options['list']:
            self.list_records()
        else:
            self.stdout.write('Use --create-sample or --list')
    
    def create_sample_data(self):
        # Get existing transcript or create a test one
        raw_transcript = RawTranscriptCache.objects.first()
        if not raw_transcript:
            self.stdout.write(self.style.ERROR('No RawTranscriptCache records found. Please run the system with real data first.'))
            return
        
        # Create sample task following exact prompt.md specification
        task = GeminiProcessedTask.objects.create(
            raw_transcript=raw_transcript,
            task_item='Implement comprehensive Gemini API integration with error handling and rate limiting capabilities',
            assignee_emails='joe@taskforge.ai',
            assignee_full_names='Joe Smith',
            priority='High',
            brief_description='Joe Smith asked the development team to implement the Gemini API integration with comprehensive error handling, rate limiting, and proper response parsing by end of week to enable AI task extraction functionality.',
            due_date_ms=int((timezone.now() + timedelta(days=5)).timestamp() * 1000),
            status='Working on it',
            extraction_order=0,
            source_sentences=['Joe Smith: I will implement the Gemini API integration by end of week.'],
            gemini_model_version='gemini-2.5-flash',
            extraction_confidence=0.95,
            raw_gemini_response={
                'model': 'gemini-2.5-flash',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created GeminiProcessedTask: {task.task_item[:60]}...')
        )
        self.stdout.write(f'Valid extraction: {task.is_valid_extraction}')
        self.stdout.write(f'Word count requirement met: {task.meets_word_count_requirement}')
        self.stdout.write(f'Description requirement met: {task.meets_description_requirement}')
    
    def list_records(self):
        tasks = GeminiProcessedTask.objects.all()
        self.stdout.write(f'Found {tasks.count()} GeminiProcessedTask records:')
        
        for task in tasks:
            self.stdout.write(f'- {task.task_item[:80]}...')
            self.stdout.write(f'  Priority: {task.priority}, Status: {task.status}')
            self.stdout.write(f'  Valid: {task.is_valid_extraction}')
            self.stdout.write('') 