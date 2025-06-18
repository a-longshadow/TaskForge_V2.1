from django.core.management.base import BaseCommand
from apps.core.models import RawTranscriptCache, ProcessedTaskData, Transcript
from datetime import datetime, timezone, timedelta
import json


class Command(BaseCommand):
    help = 'Create sample ProcessedTaskData records for admin interface testing'

    def handle(self, *args, **options):
        self.stdout.write("🎯 CREATING SAMPLE PROCESSED TASK DATA")
        self.stdout.write("=" * 50)
        
        # Get or create a transcript
        cache_item = RawTranscriptCache.objects.first()
        transcript = None
        
        if cache_item:
            # Try to get associated transcript
            try:
                transcript = Transcript.objects.get(fireflies_id=cache_item.fireflies_id)
            except Transcript.DoesNotExist:
                # Create transcript from cache
                transcript = Transcript.objects.create(
                    fireflies_id=cache_item.fireflies_id,
                    title=cache_item.meeting_title,
                    meeting_date=cache_item.meeting_date,
                    duration_minutes=cache_item.duration_minutes,
                    participant_count=cache_item.participant_count,
                    raw_data=cache_item.raw_fireflies_data,
                    content=str(cache_item.raw_fireflies_data)[:1000]
                )
                self.stdout.write(f"✅ Created transcript: {transcript.title}")
        
        if not transcript:
            self.stdout.write("❌ No transcript available - creating dummy transcript")
            transcript = Transcript.objects.create(
                fireflies_id="DEMO_TRANSCRIPT",
                title="Demo Meeting for Admin Testing",
                meeting_date=datetime.now(timezone.utc),
                duration_minutes=30,
                participant_count=3,
                raw_data={"demo": True},
                content="Demo meeting content"
            )
        
        # Clear existing processed tasks
        ProcessedTaskData.objects.all().delete()
        
        # Create sample tasks
        tasks = [
            {
                'task_item': 'Research and understand the specific requirements for creating custom agents and the detailed process for deploying them on the Olas network',
                'assignee_emails': 'vardhan@coophive.network',
                'assignee_full_names': 'Vardhan Shorewala',
                'priority': 'High',
                'brief_description': 'Investigate the necessary steps and technical specifications to develop and launch custom agents on the Olas network, moving beyond pre-configured solutions.',
                'status': 'To Do',
                'due_date': datetime.now(timezone.utc) + timedelta(days=2)
            },
            {
                'task_item': 'Initiate the process of embedding all papers located in the first designated Google Drive folder today',
                'assignee_emails': 'vardhan@coophive.network',
                'assignee_full_names': 'Vardhan Shorewala', 
                'priority': 'High',
                'brief_description': 'Begin the embedding process for documents from the first Google Drive folder, ensuring initial progress on data processing for the database demonstration.',
                'status': 'Working on it',
                'due_date': datetime.now(timezone.utc) + timedelta(days=1)
            },
            {
                'task_item': 'Configure and set up eight distinct databases following a 2x2x2 configuration to enable comprehensive testing',
                'assignee_emails': 'levi@coophive.network',
                'assignee_full_names': 'Levi Rybalov',
                'priority': 'Medium', 
                'brief_description': 'Design and implement eight unique databases to showcase the system versatility and performance across different configurations.',
                'status': 'Stuck'
            },
            {
                'task_item': 'Integrate and implement web scraping capabilities into the platform to allow for automated extraction',
                'assignee_emails': 'joe@coophive.network',
                'assignee_full_names': 'Joe Cooper',
                'priority': 'Low',
                'brief_description': 'Develop and incorporate comprehensive web scraping features into the existing platform architecture to enhance data acquisition.',
                'status': 'Review'
            },
            {
                'task_item': 'Identify and select at least one qualified developer candidate suitable for the automated scientist project',
                'assignee_emails': 'vardhan@coophive.network,levi@coophive.network',
                'assignee_full_names': 'Vardhan Shorewala, Levi Rybalov',
                'priority': 'High',
                'brief_description': 'Search for and interview potential candidates to hire for the automated scientist role, leveraging newly approved funding.',
                'status': 'Waiting for review',
                'due_date': datetime.now(timezone.utc) + timedelta(days=7)
            }
        ]
        
        created_count = 0
        for task_data in tasks:
            task = ProcessedTaskData.objects.create(
                transcript=transcript,
                **task_data
            )
            created_count += 1
            self.stdout.write(f"  • Created: {task.task_item[:60]}...")
        
        self.stdout.write(f"\n✅ Created {created_count} sample ProcessedTaskData records")
        self.stdout.write(f"📊 Total processed tasks: {ProcessedTaskData.objects.count()}")
        self.stdout.write(f"🎯 Admin interface ready at: http://127.0.0.1:8001/admin/")
        self.stdout.write(f"📋 Navigate to: Core > Processed task datas") 