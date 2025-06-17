"""
Google Gemini API client for task extraction
"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger('apps.core.gemini_client')


class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
        self.session = requests.Session()
    
    def _execute_request(self, prompt: str) -> Dict[str, Any]:
        """Execute a Gemini API request"""
        url = f"{self.base_url}?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Gemini API error: {data['error']}")
                raise Exception(f"Gemini API error: {data['error']}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request failed: {e}")
            raise Exception(f"Gemini API request failed: {e}")
    
    def extract_tasks_from_transcript(self, transcript_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract action items from meeting transcript using the TaskForge prompt"""
        
        # Convert sentences to transcript text
        transcript_text = self._format_sentences(transcript_data.get('sentences', []))
        
        # Build the prompt using the TaskForge format from temp/prompt.md
        prompt = f"""=== System ===
You are **TaskForge**, an expert AI assistant whose only objective is to extract
actionable to-do items from meeting-transcript JSON with maximum factual
accuracy and natural-sounding output.  
Return **only** a JSON array (no markdown, comments, or prose) where each
object has **exactly** the following keys, in this order:

1. "task_item"                   – string, at least 10 natural, coherent words  
2. "assignee_emails"             – string (comma-separated if > 1)  
3. "assignee(s)_full_names"      – string (comma-separated ⇡)  
4. "priority"                    – "High" | "Medium" | "Low"  
5. "brief_description"           – string, 30–50 words, human tone  
6. "due_date"                    – integer (UTC ms) | null  
7. "status"                      – "To Do" | "Stuck" | "Working on it" | "Waiting for review" | "Approved" | "Done"

No other keys are permitted. Preserve the order in which tasks appear in the
source material.

=== User ===
Process only this meeting-transcript JSON:

* title                → {transcript_data.get('title', 'Untitled Meeting')}  
* meeting_date_ms      → {transcript_data.get('date', '')}  
* organizer_email      → {transcript_data.get('organizer_email', '')}  

Attendees (name ↔ email):  
{self._format_attendees(transcript_data.get('meeting_attendees', []))}

Explicit Action Items:  
{transcript_data.get('summary', {}).get('action_items', 'None specified')}

Meeting Overview:  
{transcript_data.get('summary', {}).get('overview', 'No overview available')}

Full Transcript:  
{transcript_text}

Return ONLY the JSON array described above."""
        
        try:
            response = self._execute_request(prompt)
            
            # Extract the generated text
            candidates = response.get('candidates', [])
            if not candidates:
                logger.warning("No candidates in Gemini response")
                return []
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                logger.warning("No parts in Gemini response")
                return []
            
            generated_text = parts[0].get('text', '')
            
            # Parse the JSON response
            try:
                # Clean the response (remove markdown formatting if present)
                cleaned_text = generated_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                tasks = json.loads(cleaned_text)
                
                if not isinstance(tasks, list):
                    logger.warning("Gemini response is not a list")
                    return []
                
                logger.info(f"Extracted {len(tasks)} tasks from transcript")
                return tasks
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.error(f"Raw response: {generated_text}")
                return []
            
        except Exception as e:
            logger.error(f"Failed to extract tasks: {e}")
            return []
    
    def _format_sentences(self, sentences: List[Dict[str, Any]]) -> str:
        """Format sentences into transcript text"""
        if not sentences:
            return "No transcript available"
        
        formatted_sentences = []
        for sentence in sentences:
            speaker = sentence.get('speaker_name', 'Unknown')
            text = sentence.get('text', '')
            start_time = sentence.get('start_time', 0)
            
            if text:
                formatted_sentences.append(f"{speaker}: {text}")
        
        return "\n".join(formatted_sentences)
    
    def _format_attendees(self, attendees: List[Dict[str, Any]]) -> str:
        """Format attendees for the prompt"""
        if not attendees:
            return "No attendees listed"
        
        formatted = []
        for attendee in attendees:
            name = attendee.get('displayName', 'Unknown')
            email = attendee.get('email', 'no-email')
            formatted.append(f"- {name} <{email}>")
        
        return "\n".join(formatted)
    
    def test_connection(self) -> bool:
        """Test connection to Gemini API"""
        test_prompt = "Respond with 'OK' if you can read this message."
        
        try:
            response = self._execute_request(test_prompt)
            candidates = response.get('candidates', [])
            
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    text = parts[0].get('text', '').strip().upper()
                    if 'OK' in text:
                        logger.info("Gemini API connection test successful")
                        return True
            
            logger.warning("Gemini API connection test failed - unexpected response")
            return False
            
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False


def get_gemini_client() -> GeminiClient:
    """Get configured Gemini client"""
    api_key = "AIzaSyBWArylUmDVmRuASiZMQ6DiI5IDDsG9bfw"  # From user's credentials
    return GeminiClient(api_key) 