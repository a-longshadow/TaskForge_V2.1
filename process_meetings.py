#!/usr/bin/env python
"""
Process meetings through simulated Gemini extraction and store results in GeminiProcessedTask
"""

import os
import django
import json
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskforge.settings.development')
django.setup()

from apps.core.models import RawTranscriptCache, GeminiProcessedTask
from django.utils import timezone

def process_meetings():
    """Process recent meetings through simulated Gemini and store results"""
    
    print("🚀 PROCESSING MEETINGS THROUGH GEMINI SIMULATION")
    print("=" * 55)
    
    # Get recent meetings (last 5 for demonstration)
    recent_meetings = RawTranscriptCache.objects.all().order_by('-meeting_date')[:5]
    
    print(f"📄 Found {recent_meetings.count()} recent meetings to process")
    print()
    
    total_tasks_created = 0
    
    for i, meeting in enumerate(recent_meetings, 1):
        print(f"🔄 Processing Meeting {i}: {meeting.meeting_title}")
        print(f"   Date: {meeting.meeting_date}")
        print(f"   Fireflies ID: {meeting.fireflies_id}")
        
        # Check if already processed
        existing_tasks = GeminiProcessedTask.objects.filter(raw_transcript=meeting).count()
        if existing_tasks > 0:
            print(f"   ⚠️  Already has {existing_tasks} processed tasks - skipping")
            print()
            continue
        
        try:
            # Create sample tasks based on meeting content (simulating Gemini processing)
            sample_tasks = create_sample_tasks_for_meeting(meeting, i)
            
            tasks_created = 0
            for task_order, task_data in enumerate(sample_tasks):
                task = GeminiProcessedTask.objects.create(
                    raw_transcript=meeting,
                    task_item=task_data['task_item'],
                    assignee_emails=task_data['assignee_emails'],
                    assignee_full_names=task_data['assignee_full_names'],
                    priority=task_data['priority'],
                    brief_description=task_data['brief_description'],
                    due_date_ms=task_data['due_date_ms'],
                    status=task_data['status'],
                    extraction_order=task_order,
                    gemini_model_version='gemini-2.5-flash-simulated',
                    extraction_confidence=task_data['confidence'],
                    source_sentences=task_data['source_sentences'],
                    raw_gemini_response={
                        'simulated_response': task_data,
                        'meeting_id': meeting.fireflies_id,
                        'processing_timestamp': timezone.now().isoformat()
                    }
                )
                tasks_created += 1
            
            print(f"   ✅ Created {tasks_created} tasks")
            total_tasks_created += tasks_created
            
        except Exception as e:
            print(f"   ❌ Error processing meeting: {str(e)}")
        
        print()
    
    print(f"🎉 PROCESSING COMPLETE!")
    print(f"   Total tasks created: {total_tasks_created}")
    print()
    
    # Show all action items
    show_action_items()

def create_sample_tasks_for_meeting(meeting, meeting_index):
    """Create sample tasks based on meeting content"""
    
    meeting_title = meeting.meeting_title
    base_timestamp = int((timezone.now() + timedelta(days=3)).timestamp() * 1000)
    
    # Generate contextual tasks based on meeting type
    if "weekly" in meeting_title.lower():
        return [
            {
                'task_item': f'Follow up on action items discussed in {meeting_title} weekly sync meeting',
                'assignee_emails': 'team@coophive.network',
                'assignee_full_names': 'Team Lead',
                'priority': 'Medium',
                'brief_description': f'Team lead requested follow-up on action items from {meeting_title} to ensure progress tracking and accountability for weekly deliverables and commitments made during the sync.',
                'due_date_ms': base_timestamp,
                'status': 'To Do',
                'confidence': 0.85,
                'source_sentences': [f'Action items discussed in {meeting_title}']
            }
        ]
    
    elif "ops" in meeting_title.lower():
        return [
            {
                'task_item': f'Review operational metrics and KPIs discussed in {meeting_title} operations meeting',
                'assignee_emails': 'ops@coophive.network',
                'assignee_full_names': 'Operations Team',
                'priority': 'High',
                'brief_description': f'Operations manager asked team to review the key performance indicators and operational metrics discussed during {meeting_title} to identify improvement areas and optimization opportunities.',
                'due_date_ms': base_timestamp,
                'status': 'To Do',
                'confidence': 0.90,
                'source_sentences': [f'Operational review items from {meeting_title}']
            },
            {
                'task_item': f'Implement process improvements identified during {meeting_title} operational review',
                'assignee_emails': 'andrew@coophive.network',
                'assignee_full_names': 'Andrew Hemingway',
                'priority': 'Medium',
                'brief_description': f'Andrew Hemingway committed to implementing the process improvements and operational enhancements identified during {meeting_title} to streamline workflows and increase team efficiency.',
                'due_date_ms': base_timestamp + (24 * 60 * 60 * 1000),  # Next day
                'status': 'Working on it',
                'confidence': 0.88,
                'source_sentences': [f'Process improvement discussion in {meeting_title}']
            }
        ]
    
    elif "team meeting" in meeting_title.lower():
        return [
            {
                'task_item': f'Coordinate cross-team collaboration initiatives discussed in {meeting_title} team meeting',
                'assignee_emails': 'levi@coophive.network,yang@coophive.network',
                'assignee_full_names': 'Levi Rybalov, Yang Zheng',
                'priority': 'High',
                'brief_description': f'Team leads Levi Rybalov and Yang Zheng agreed to coordinate the cross-team collaboration initiatives discussed in {meeting_title} to improve project delivery and team communication.',
                'due_date_ms': base_timestamp,
                'status': 'To Do',
                'confidence': 0.92,
                'source_sentences': [f'Team collaboration discussion in {meeting_title}']
            }
        ]
    
    else:
        # Generic 1:1 or partnership meeting
        return [
            {
                'task_item': f'Complete deliverables and commitments made during {meeting_title} discussion session',
                'assignee_emails': 'team@coophive.network',
                'assignee_full_names': 'Meeting Participants',
                'priority': 'Medium',
                'brief_description': f'Meeting participants committed to completing the deliverables and action items discussed during {meeting_title} to maintain project momentum and meet agreed-upon deadlines.',
                'due_date_ms': base_timestamp + (2 * 24 * 60 * 60 * 1000),  # 2 days later
                'status': 'To Do',
                'confidence': 0.80,
                'source_sentences': [f'Commitments made in {meeting_title}']
            }
        ]

def show_action_items():
    """Display all action items from the database"""
    
    print("📋 ALL ACTION ITEMS IN DATABASE")
    print("=" * 40)
    
    # Get all GeminiProcessedTask items
    gemini_tasks = GeminiProcessedTask.objects.all().order_by('-created_at')
    
    print(f"🤖 GeminiProcessedTask Records: {gemini_tasks.count()}")
    print("-" * 30)
    
    for i, task in enumerate(gemini_tasks, 1):
        print(f"Task {i}:")
        print(f"  📝 Item: {task.task_item}")
        print(f"  👥 Assignees: {task.assignee_full_names}")
        print(f"  📧 Emails: {task.assignee_emails}")
        print(f"  🎯 Priority: {task.priority}")
        print(f"  📊 Status: {task.status}")
        print(f"  📅 Due: {task.due_date_datetime.strftime('%Y-%m-%d %H:%M UTC') if task.due_date_datetime else 'No due date'}")
        print(f"  ✅ Valid: {task.is_valid_extraction}")
        print(f"  🔗 Meeting: {task.raw_transcript.meeting_title}")
        print(f"  📈 Confidence: {task.extraction_confidence:.2f}")
        print(f"  🚀 Delivered: {task.delivered_to_monday}")
        print()
    
    # Summary statistics
    print("📊 SUMMARY STATISTICS")
    print("-" * 20)
    print(f"Total Action Items: {gemini_tasks.count()}")
    print(f"High Priority: {gemini_tasks.filter(priority='High').count()}")
    print(f"Medium Priority: {gemini_tasks.filter(priority='Medium').count()}")
    print(f"Low Priority: {gemini_tasks.filter(priority='Low').count()}")
    print(f"To Do: {gemini_tasks.filter(status='To Do').count()}")
    print(f"Working on it: {gemini_tasks.filter(status='Working on it').count()}")
    print(f"Done: {gemini_tasks.filter(status='Done').count()}")
    print(f"Valid Extractions: {gemini_tasks.filter(meets_word_count_requirement=True, meets_description_requirement=True).count()}")
    print(f"With Due Dates: {gemini_tasks.filter(due_date_ms__isnull=False).count()}")
    print(f"Delivered to Monday: {gemini_tasks.filter(delivered_to_monday=True).count()}")

if __name__ == "__main__":
    process_meetings() 