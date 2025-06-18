"""
Google Gemini API client with comprehensive rate limiting and caching
"""

import logging
import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .circuit_breaker import CircuitBreakerRegistry

logger = logging.getLogger('apps.core.gemini_client')


class EnhancedGeminiClient:
    """Enhanced Gemini client with rate limiting, caching, and circuit breaker"""
    
    def __init__(self, api_key: str, rate_limit_per_minute: int = 15, cache_timeout: int = 1800):
        self.api_key = api_key
        self.base_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
        self.session = requests.Session()
        
        # Rate limiting configuration
        self.rate_limit_per_minute = rate_limit_per_minute
        self.min_request_interval = 60.0 / rate_limit_per_minute  # seconds between requests
        self.last_request_time = 0
        
        # Caching configuration
        self.cache_timeout = cache_timeout  # 30 minutes default
        self.cache_prefix = 'gemini_'
        
        # Quota tracking
        self.quota_tracker = {
            'requests_today': 0,
            'last_reset': datetime.now().date(),
            'warning_threshold': settings.EXTERNAL_APIS['GEMINI'].get('QUOTA_WARNING_THRESHOLD', 80)
        }
        
        # Retry configuration
        self.retry_attempts = settings.EXTERNAL_APIS['GEMINI'].get('RETRY_ATTEMPTS', 3)
        self.backoff_factor = settings.EXTERNAL_APIS['GEMINI'].get('BACKOFF_FACTOR', 2.0)
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreakerRegistry.get_instance().get_or_create(
            'gemini_api',
            failure_threshold=5,
            timeout=300  # 5 minutes
        )
        
        logger.info(f"Initialized EnhancedGeminiClient with {rate_limit_per_minute}/min rate limit")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _update_quota_tracker(self):
        """Update quota tracking"""
        today = datetime.now().date()
        
        # Reset daily counter if it's a new day
        if self.quota_tracker['last_reset'] != today:
            self.quota_tracker['requests_today'] = 0
            self.quota_tracker['last_reset'] = today
        
        self.quota_tracker['requests_today'] += 1
        
        # Check for quota warnings (assuming 1000 requests/day limit)
        daily_limit = 1000  # Gemini API typical daily limit
        usage_percentage = (self.quota_tracker['requests_today'] / daily_limit) * 100
        
        if usage_percentage >= self.quota_tracker['warning_threshold']:
            logger.warning(f"Gemini API quota warning: {usage_percentage:.1f}% used ({self.quota_tracker['requests_today']}/{daily_limit})")
    
    def _get_cache_key(self, prompt_hash: str) -> str:
        """Generate cache key for prompt"""
        return f"{self.cache_prefix}extract_{prompt_hash}"
    
    def _generate_prompt_hash(self, transcript_data: Dict[str, Any]) -> str:
        """Generate hash for transcript data to use as cache key"""
        import hashlib
        
        # Create a stable hash from key transcript data
        key_data = {
            'title': transcript_data.get('title', ''),
            'date': transcript_data.get('date', ''),
            'sentences_count': len(transcript_data.get('sentences', [])),
            'organizer': transcript_data.get('organizer_email', '')
        }
        
        data_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(data_string.encode()).hexdigest()
    
    def _execute_request_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Execute Gemini API request with retry logic and circuit breaker"""
        
        def make_request():
            self._enforce_rate_limit()
            self._update_quota_tracker()
            
            url = f"{self.base_url}?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                error_msg = data['error']
                logger.error(f"Gemini API error: {error_msg}")
                
                # Check for rate limiting errors
                if 'quota' in str(error_msg).lower() or 'rate' in str(error_msg).lower():
                    raise requests.exceptions.RequestException(f"Rate limit/quota error: {error_msg}")
                
                raise Exception(f"Gemini API error: {error_msg}")
            
            return data
        
        # Use circuit breaker for the request
        try:
            return self.circuit_breaker.call(make_request)
        except Exception as e:
            logger.error(f"Gemini API request failed after circuit breaker: {e}")
            raise
    
    def extract_tasks_from_transcript(self, transcript_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract action items from meeting transcript with caching"""
        
        # Check cache first
        prompt_hash = self._generate_prompt_hash(transcript_data)
        cache_key = self._get_cache_key(prompt_hash)
        
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"Using cached Gemini result for transcript {prompt_hash[:8]}")
            return cached_result
        
        # Convert sentences to transcript text
        transcript_text = self._format_sentences(transcript_data.get('sentences', []))
        
        # Build the prompt using the TaskForge format
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
            response = self._execute_request_with_retry(prompt)
            
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
                
                # Cache the successful result
                cache.set(cache_key, tasks, self.cache_timeout)
                logger.info(f"Cached Gemini result for transcript {prompt_hash[:8]} (expires in {self.cache_timeout/60:.0f}min)")
                
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
            response = self._execute_request_with_retry(test_prompt)
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
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        return {
            'requests_today': self.quota_tracker['requests_today'],
            'last_reset': self.quota_tracker['last_reset'].isoformat(),
            'warning_threshold': self.quota_tracker['warning_threshold'],
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'cache_timeout_minutes': self.cache_timeout / 60,
            'circuit_breaker_state': self.circuit_breaker.state.value
        }


def get_gemini_client() -> EnhancedGeminiClient:
    """Get enhanced Gemini client with rate limiting"""
    api_key = "AIzaSyBWArylUmDVmRuASiZMQ6DiI5IDDsG9bfw"  # From user's credentials
    
    # Get configuration from settings
    gemini_config = settings.EXTERNAL_APIS['GEMINI']
    rate_limit = gemini_config.get('RATE_LIMIT_PER_MINUTE', 15)
    cache_timeout = gemini_config.get('CACHE_TIMEOUT', 1800)
    
    return EnhancedGeminiClient(api_key, rate_limit, cache_timeout) 