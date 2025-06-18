"""
TaskForge Precision Extraction Engine
Based on N8N TaskForge MVP - Laser-focused, no-nonsense task extraction
"""

import json
import logging
import re
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from django.utils import timezone as django_timezone
from django.utils.dateparse import parse_datetime
from django.conf import settings

from .gemini_client import get_gemini_client
from .models import RawTranscriptCache, ProcessedTaskData, Transcript

logger = logging.getLogger(__name__)


class PrecisionTaskExtractor:
    """
    N8N TaskForge MVP-inspired precision task extractor
    Uses exact prompt.md logic for maximum accuracy
    """
    
    def __init__(self):
        self.gemini_client = get_gemini_client()
    
    def extract_tasks_from_cache(self, cache_item: RawTranscriptCache) -> List[ProcessedTaskData]:
        """
        Extract tasks from cached Fireflies data using N8N precision prompt
        ALWAYS runs AI extraction - never echoes Fireflies action items directly
        """
        try:
            fireflies_data = cache_item.raw_fireflies_data
            
            # CRITICAL: Always use N8N prompt regardless of what Fireflies provides
            # Never echo Fireflies action_items directly - always run through AI
            n8n_prompt = self._build_n8n_prompt_from_file(fireflies_data)
            
            logger.info(f"🎯 PRECISION EXTRACTION: Running N8N prompt on {cache_item.fireflies_id}")
            logger.info(f"📝 Prompt length: {len(n8n_prompt)} characters")
            
            # Get Gemini client and run extraction
            gemini_client = get_gemini_client()
            
            # Force AI extraction - never skip this step
            ai_response = gemini_client._execute_request_with_retry(n8n_prompt)
            
            if not ai_response or 'candidates' not in ai_response:
                logger.error(f"❌ No AI response for {cache_item.fireflies_id}")
                return []
            
            # Extract the AI-generated content
            ai_content = ai_response['candidates'][0]['content']['parts'][0]['text']
            logger.info(f"🤖 AI Response length: {len(ai_content)} characters")
            
            # Parse AI output into structured tasks
            tasks_data = self._parse_ai_output(ai_content)
            logger.info(f"📋 Parsed {len(tasks_data)} tasks from AI output")
            
            # Create ProcessedTaskData objects
            processed_tasks = []
            for task_data in tasks_data:
                processed_task = self._create_processed_task(task_data, cache_item, ai_content)
                if processed_task:
                    processed_tasks.append(processed_task)
            
            logger.info(f"✅ Created {len(processed_tasks)} ProcessedTaskData objects")
            return processed_tasks
            
        except Exception as e:
            logger.error(f"❌ Error extracting tasks from cache {cache_item.fireflies_id}: {str(e)}")
            return []
    
    def _build_n8n_prompt_from_file(self, fireflies_data: Dict[str, Any]) -> str:
        """
        Build the exact N8N TaskForge MVP prompt from temp/prompt.md file
        """
        
        # Read the prompt template from file
        prompt_file_path = os.path.join(settings.BASE_DIR, 'temp', 'prompt.md')
        
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {prompt_file_path}, using fallback")
            return self._build_n8n_prompt_fallback(fireflies_data)
        
        # Extract meeting data
        meeting_title = fireflies_data.get('title', 'Untitled Meeting')
        meeting_date_ms = fireflies_data.get('date', 0)
        organizer_email = fireflies_data.get('organizer_email', '')
        
        # Format attendees
        attendees = fireflies_data.get('meeting_attendees', [])
        if attendees is None:
            attendees = []
        attendees_text = '\n'.join([
            f"- {attendee.get('displayName', 'Unknown')} <{attendee.get('email', 'no-email')}>"
            for attendee in attendees
        ])
        
        # Extract action items
        summary = fireflies_data.get('summary', {})
        if summary is None:
            summary = {}
        action_items = summary.get('action_items', 'No explicit action items listed.')
        overview = summary.get('overview', 'No overview available.')
        
        # Format transcript
        sentences = fireflies_data.get('sentences', [])
        if sentences is None:
            sentences = []
        transcript_text = '\n'.join([
            f"{sentence.get('speaker_name', 'Unknown')}: {sentence.get('text', '')} (t={sentence.get('start_time', 0)})"
            for sentence in sentences
        ])
        
        # Replace template variables in the prompt
        final_prompt = prompt_template.replace('{{ $json.title }}', meeting_title)
        final_prompt = final_prompt.replace('{{ $json.date }}', str(meeting_date_ms))
        final_prompt = final_prompt.replace('{{ $json.organizer_email }}', organizer_email)
        final_prompt = final_prompt.replace('{{ $json.meeting_attendees.map(a => `- ${a.displayName} <${a.email}>`).join("\\n") }}', attendees_text)
        final_prompt = final_prompt.replace('{{ $json.summary.action_items }}', str(action_items))
        final_prompt = final_prompt.replace('{{ $json.summary.overview }}', str(overview))
        final_prompt = final_prompt.replace('{{ $json.sentences.map(s => `${s.speaker_name}: ${s.text} (t=${s.start_time_ms})`).join("\\n") }}', transcript_text)
        
        return final_prompt

    def _build_n8n_prompt_fallback(self, fireflies_data: Dict[str, Any]) -> str:
        """
        Fallback N8N prompt if file not found - FIXED VERSION
        """
        
        # Extract meeting data
        meeting_title = fireflies_data.get('title', 'Untitled Meeting')
        meeting_date_ms = fireflies_data.get('date', 0)
        organizer_email = fireflies_data.get('organizer_email', '')
        
        # Format attendees
        attendees = fireflies_data.get('meeting_attendees', [])
        if attendees is None:
            attendees = []
        attendees_text = '\n'.join([
            f"- {attendee.get('displayName', 'Unknown')} <{attendee.get('email', 'no-email')}>"
            for attendee in attendees
        ])
        
        # Extract action items
        summary = fireflies_data.get('summary', {})
        if summary is None:
            summary = {}
        action_items = summary.get('action_items', 'No explicit action items listed.')
        overview = summary.get('overview', 'No overview available.')
        
        # Format transcript
        sentences = fireflies_data.get('sentences', [])
        if sentences is None:
            sentences = []
        transcript_text = '\n'.join([
            f"{sentence.get('speaker_name', 'Unknown')}: {sentence.get('text', '')} (t={sentence.get('start_time', 0)})"
            for sentence in sentences
        ])
        
        # Build the exact N8N prompt - FIXED VERSION
        prompt = f"""=== System ===
You are **TaskForge**, an expert AI assistant whose only objective is to extract
actionable to-do items from meeting-transcript JSON with maximum factual
accuracy and natural-sounding output.  
Return **only** a JSON array (no markdown, comments, or prose) where each
object has **exactly** the following keys, in this order:

1. "task_item"                   – *string, at least 10 natural, coherent words*  
2. "assignee_emails"             – *string* (comma-separated if > 1)  
3. "assignee(s)_full_names"      – *string* (comma-separated ⇡)  
4. "priority"                    – "High" | "Medium" | "Low"  
5. "brief_description"           – *string, 30–50 words, human tone*  
6. "due_date"                    – *integer* (UTC ms) | null  
7. "status"                      – "To Do" | "Stuck" | "Working on it" | "Waiting for review" | "Approved" | "Done"

No other keys are permitted. Preserve the order in which tasks appear in the
source material.

--------------------------------------------------------------------
EXTRACTION LOGIC
--------------------------------------------------------------------
A. **Source hierarchy**  
   1. `summary.action_items` list  
   2. Sentences that contain actionable cues  
      ("X will …", "Can you …", "Let's have X …", "I'll …", "Please …")  
   3. `summary.overview` for implicit commitments

B. **Assignee resolution & deduplication**  
   • Map names to `meeting_attendees[].{{displayName,email}}` 
   • If wording clearly assigns several people, include them all
     (comma-separated).  
   • Never repeat the same email within a task.

C. **Validity filter**  
   • Extract wording contains a future deliverable or request including completed work (be clear to mark it as done) but ignore vague discussion unless it still requires action.

D. **Priority rules**  
   • Hard deadline / blocker → High  
   • Multi-day / strategic   → Medium  
   • Informational / minor   → Low

--------------------------------------------------------------------
ROBUST DUE-DATE ENGINE (WEEKEND-AWARE)
--------------------------------------------------------------------
1. **Absolute phrases** – parse and convert to 23 : 59 : 59 local, then to UTC ms.  
2. **Relative phrases** – anchor to meeting date `M` (local) and skip weekends:

phrase                          → computed due date (17 : 00 local unless noted)
───────────────────────────────────────────────────────────────────────────────
"today" / "tonight"             → M  
"tomorrow" / "ASAP"             → next calendar day; if Sat/Sun, roll to Monday  
"this week"                     → Friday of M's week; if Fri/Sat/Sun, roll to next Monday  
"next week"                     → next Monday  
"within N days"                 → add N *business* days (skip Sat/Sun)  
"after the meeting"             → end-of-day M  
explicit weekday ("on Tuesday") → next occurrence; if ≤ M, +7 days  

If multiple cues conflict, keep the earliest resulting business day.  
If no temporal cue exists, set `"due_date": null`.

**Best Practices:**
- Never set a due date to a day before the meeting date (`M`).
- Unless the phrase is explicitly "today" or "EOD", the due date should be at least `M + 1 day`.

--------------------------------------------------------------------
TASK-ITEM LENGTH RULE
--------------------------------------------------------------------
If the original sentence has < 10 words, append context from the same or
adjacent sentence(s) until the threshold is met.  
Do **not** pad with meaningless words.

--------------------------------------------------------------------
BRIEF DESCRIPTION GUIDELINES
--------------------------------------------------------------------
• 30–50 words.  
• Begin with "<Assigner Full Name> asked <Assignee First Name> …".  
• Quote 1–2 short phrases directly from the transcript for a human tone.  
• Explain purpose, method, collaborators, and timing.

--------------------------------------------------------------------
COUNT & ORDER
--------------------------------------------------------------------
• Output ≈ |`summary.action_items`| ± 2 tasks.  
• Preserve chronological order of appearance.  
• Skip duplicates (normalise case, whitespace, timestamps).

If no items meet these rules, return `[]`. OR any done items discussed. Not all meeting generate action items. Be aware of meeting marked "silent" but do not fail to scrutinize in order to verify if the tag is correct.

--------------------------------------------------------------------
=== User ===
Process only this meeting-transcript JSON:

* title                → {meeting_title}  
* meeting_date_ms      → {meeting_date_ms}  
* organizer_email      → {organizer_email}  

Attendees (name ↔ email):  
{attendees_text}

Explicit Action Items:  
{action_items}

Meeting Overview:  
{overview}

Full Transcript:  
{transcript_text}

Return ONLY the JSON array described above."""

        return prompt
    
    def _parse_ai_output(self, ai_output: str) -> List[Dict[str, Any]]:
        """
        Parse AI output using N8N approach - handle fenced code blocks
        """
        cleaned_output = ai_output.strip()
        
        # Remove markdown fencing like N8N does
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]
        elif cleaned_output.startswith("```"):
            cleaned_output = cleaned_output[3:]
        
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]
        
        cleaned_output = cleaned_output.strip()
        
        try:
            tasks_data = json.loads(cleaned_output)
            
            # Handle single object (wrap in array like N8N)
            if isinstance(tasks_data, dict):
                tasks_data = [tasks_data]
            
            # Validate it's an array
            if not isinstance(tasks_data, list):
                return []
            
            return tasks_data
            
        except json.JSONDecodeError:
            return []
    
    def _create_processed_task(
        self, 
        task_data: Dict[str, Any], 
        cache_item: RawTranscriptCache,
        ai_output: str
    ) -> Optional[ProcessedTaskData]:
        """
        Create ProcessedTaskData from parsed task data
        """
        try:
            # Validate required N8N fields
            required_fields = [
                'task_item', 'assignee_emails', 'assignee(s)_full_names',
                'priority', 'brief_description', 'status'
            ]
            
            for field in required_fields:
                if field not in task_data:
                    return None
            
            # Get or create corresponding Transcript
            transcript, _ = Transcript.objects.get_or_create(
                fireflies_id=cache_item.fireflies_id,
                defaults={
                    'title': cache_item.meeting_title,
                    'meeting_date': cache_item.meeting_date,
                    'duration_minutes': cache_item.duration_minutes,
                    'participant_count': cache_item.participant_count,
                    'raw_data': cache_item.raw_fireflies_data,
                    'content': self._extract_content_from_sentences(
                        cache_item.raw_fireflies_data.get('sentences', [])
                    ),
                    'is_processed': True,
                }
            )
            
            # Parse due date
            due_date = None
            if task_data.get('due_date') and task_data['due_date'] != 'null':
                try:
                    if isinstance(task_data['due_date'], (int, float)):
                        due_date = datetime.fromtimestamp(
                            task_data['due_date'] / 1000, 
                            tz=timezone.utc
                        )
                except (ValueError, TypeError):
                    pass
            
            # Create ProcessedTaskData
            processed_task = ProcessedTaskData(
                transcript=transcript,
                task_item=task_data['task_item'][:500],  # Ensure max length
                assignee_emails=task_data['assignee_emails'][:500],
                assignee_full_names=task_data['assignee(s)_full_names'][:500],
                priority=task_data['priority'] if task_data['priority'] in ['High', 'Medium', 'Low'] else 'Medium',
                brief_description=task_data['brief_description'],
                due_date=due_date,
                status=task_data['status'] if task_data['status'] in [
                    'To Do', 'Stuck', 'Working on it', 'Waiting for review', 'Approved', 'Done'
                ] else 'To Do',
                extraction_confidence=0.9,  # High confidence for N8N approach
                source_sentences=self._find_source_sentences(
                    task_data['task_item'], 
                    cache_item.raw_fireflies_data.get('sentences', [])
                ),
                processing_notes=f"Extracted using N8N precision approach. AI output length: {len(ai_output)} chars."
            )
            
            return processed_task
            
        except Exception as e:
            return None
    
    def _extract_content_from_sentences(self, sentences: List[Dict[str, Any]]) -> str:
        """Extract readable content from sentences"""
        content_parts = []
        for sentence in sentences:
            speaker = sentence.get('speaker_name', 'Unknown')
            text = sentence.get('text', sentence.get('raw_text', ''))
            if text:
                content_parts.append(f"{speaker}: {text}")
        
        return '\n'.join(content_parts)
    
    def _find_source_sentences(self, task_item: str, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find sentences that likely generated this task"""
        source_sentences = []
        task_words = set(task_item.lower().split())
        
        for sentence in sentences:
            sentence_text = sentence.get('text', '').lower()
            sentence_words = set(sentence_text.split())
            
            # Check for word overlap
            overlap = len(task_words.intersection(sentence_words))
            if overlap >= 2:  # At least 2 words in common
                source_sentences.append({
                    'speaker_name': sentence.get('speaker_name'),
                    'text': sentence.get('text'),
                    'start_time': sentence.get('start_time'),
                    'overlap_score': overlap
                })
        
        # Sort by overlap score and return top 3
        source_sentences.sort(key=lambda x: x['overlap_score'], reverse=True)
        return source_sentences[:3]


def process_raw_cache_item(cache_item: RawTranscriptCache) -> List[ProcessedTaskData]:
    """
    Process a raw cache item and extract precision tasks
    """
    extractor = PrecisionTaskExtractor()
    tasks = extractor.extract_tasks_from_cache(cache_item)
    
    # Save tasks to database
    saved_tasks = []
    for task in tasks:
        task.save()
        saved_tasks.append(task)
    
    # Mark cache item as processed
    cache_item.processed = True
    cache_item.save()
    
    return saved_tasks 