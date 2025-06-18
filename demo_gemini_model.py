#!/usr/bin/env python
"""
Demonstration of the GeminiProcessedTask model using the exact prompt.md specification.

This script shows how to:
1. Store Gemini-processed tasks in the exact format specified in temp/prompt.md
2. Validate tasks against prompt.md requirements
3. Convert tasks back to the exact JSON format for Monday.com delivery
"""

import os
import django
import json
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskforge.settings.development')
django.setup()

from django.utils import timezone
from apps.core.models import RawTranscriptCache, GeminiProcessedTask


def demo_gemini_model():
    """Demonstrate the GeminiProcessedTask model functionality"""
    
    print("🚀 GeminiProcessedTask Model Demonstration")
    print("=" * 50)
    
    # Get an existing transcript
    raw_transcript = RawTranscriptCache.objects.first()
    if not raw_transcript:
        print("❌ No RawTranscriptCache records found. Please run the system with real data first.")
        return
    
    print(f"📄 Using transcript: {raw_transcript.meeting_title}")
    print(f"   Fireflies ID: {raw_transcript.fireflies_id}")
    print()
    
    # Create a sample task following EXACT prompt.md specification
    print("📝 Creating GeminiProcessedTask with exact prompt.md format...")
    
    # Sample Gemini response in exact prompt.md format
    gemini_response = [
        {
            "task_item": "Complete comprehensive code review of the Gemini API integration module including error handling",
            "assignee_emails": "alice@taskforge.ai,bob@taskforge.ai",
            "assignee(s)_full_names": "Alice Johnson, Bob Wilson",
            "priority": "High",
            "brief_description": "Joe Smith asked Alice Johnson and Bob Wilson to conduct a comprehensive code review of the Gemini API integration module, focusing on error handling, rate limiting, and response validation to ensure production readiness.",
            "due_date": int((timezone.now() + timedelta(days=3)).timestamp() * 1000),
            "status": "To Do"
        },
        {
            "task_item": "Update documentation to reflect the new GeminiProcessedTask database model and its integration points",
            "assignee_emails": "joe@taskforge.ai",
            "assignee(s)_full_names": "Joe Smith",
            "priority": "Medium",
            "brief_description": "Team lead Joe Smith committed to updating the technical documentation to include the new GeminiProcessedTask database model, its field specifications, and integration points with the existing system architecture.",
            "due_date": None,
            "status": "Working on it"
        }
    ]
    
    created_tasks = []
    
    for i, task_data in enumerate(gemini_response):
        # Create GeminiProcessedTask using the exact prompt.md format
        task = GeminiProcessedTask.objects.create(
            raw_transcript=raw_transcript,
            
            # Exact prompt.md fields (in order)
            task_item=task_data["task_item"],
            assignee_emails=task_data["assignee_emails"],
            assignee_full_names=task_data["assignee(s)_full_names"],
            priority=task_data["priority"],
            brief_description=task_data["brief_description"],
            due_date_ms=task_data["due_date"],
            status=task_data["status"],
            
            # Processing metadata
            extraction_order=i,
            gemini_model_version="gemini-2.5-flash",
            extraction_confidence=0.92,
            raw_gemini_response={
                "full_response": gemini_response,
                "task_index": i,
                "model": "gemini-2.5-flash",
                "timestamp": timezone.now().isoformat()
            },
            source_sentences=[
                f"Extracted from meeting transcript at position {i}"
            ]
        )
        
        created_tasks.append(task)
        print(f"✅ Created task {i+1}: {task.task_item[:60]}...")
    
    print()
    print("📊 Validation Results:")
    print("-" * 30)
    
    for i, task in enumerate(created_tasks):
        print(f"\n🔍 Task {i+1}: {task.task_item[:50]}...")
        print(f"   ✓ Valid extraction: {task.is_valid_extraction}")
        print(f"   ✓ Word count (≥10): {task.meets_word_count_requirement} ({len(task.task_item.split())} words)")
        print(f"   ✓ Description (30-50): {task.meets_description_requirement} ({len(task.brief_description.split())} words)")
        print(f"   ✓ Priority: {task.priority}")
        print(f"   ✓ Status: {task.status}")
        print(f"   ✓ Assignees: {task.assignee_full_names}")
        print(f"   ✓ Due date: {task.due_date_datetime.strftime('%Y-%m-%d %H:%M UTC') if task.due_date_datetime else 'No due date'}")
    
    print()
    print("📤 Prompt.md Format Output (for Monday.com delivery):")
    print("-" * 50)
    
    # Convert back to exact prompt.md format
    prompt_format_output = []
    for task in created_tasks:
        prompt_format_output.append(task.to_prompt_format())
    
    print(json.dumps(prompt_format_output, indent=2))
    
    print()
    print("📈 Database Statistics:")
    print("-" * 25)
    print(f"Total GeminiProcessedTask records: {GeminiProcessedTask.objects.count()}")
    print(f"Valid extractions: {GeminiProcessedTask.objects.filter(meets_word_count_requirement=True, meets_description_requirement=True).count()}")
    print(f"High priority tasks: {GeminiProcessedTask.objects.filter(priority='High').count()}")
    print(f"Tasks with due dates: {GeminiProcessedTask.objects.filter(due_date_ms__isnull=False).count()}")
    
    print()
    print("🎉 Demonstration completed successfully!")
    print("   The GeminiProcessedTask model correctly stores and validates")
    print("   data using the exact prompt.md specification format.")


if __name__ == "__main__":
    demo_gemini_model() 