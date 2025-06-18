"""
Enhanced Fireflies API Client with Multi-Key Failover and Intelligent Caching
Integrates with Django's cache framework for optimal performance
"""

import json
import time
import logging
import hashlib
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import requests
from django.core.cache import caches
from django.conf import settings
from django.db import transaction
from django.utils import timezone as django_timezone

from .models import Transcript
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class MultiKeyFirefliesClient:
    """
    Enhanced Fireflies client with multi-key failover and Django cache integration
    """
    
    def __init__(self, api_keys: List[str], cache_timeout: int = 14400):  # 4 hours default
        self.api_keys = api_keys
        self.cache_timeout = cache_timeout
        self.key_status = {key: {'active': True, 'last_error': None} for key in api_keys}
        self.current_key_index = 0
        self.min_request_interval = 3.0  # 3 seconds between requests
        self.last_request_time = {}
        
        # Django cache integration
        self.cache_manager = get_cache_manager()
        self.fireflies_cache = caches['fireflies']
        
        # Cache keys
        self.cache_keys = {
            'comprehensive_transcripts': 'fireflies:comprehensive:all_transcripts',
            'today_transcripts': 'fireflies:today:',
            'pagination_status': 'fireflies:pagination:status',
            'sync_status': 'fireflies:sync:last_sync',
        }
        
        logger.info(f"Initialized MultiKeyFirefliesClient with {len(api_keys)} API keys")
    
    def get_next_available_key(self) -> str:
        """
        Get the next available API key using round-robin with availability checking
        """
        max_attempts = len(self.api_keys) * 2  # Allow multiple rounds
        attempts = 0
        
        while attempts < max_attempts:
            key = self.api_keys[self.current_key_index]
            
            # Check if key is currently active
            if self.key_status[key]['active']:
                # Check rate limiting
                last_request = self.last_request_time.get(key, 0)
                time_since_last = time.time() - last_request
                
                if time_since_last >= self.min_request_interval:
                    self.last_request_time[key] = time.time()
                    return key
                else:
                    # Wait for rate limit to clear
                    sleep_time = self.min_request_interval - time_since_last
                    time.sleep(sleep_time)
                    self.last_request_time[key] = time.time()
                    return key
            
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            attempts += 1
        
        # If no keys are available, return the first one anyway (will likely fail)
        return self.api_keys[0]
    
    def mark_key_unavailable(self, api_key: str, error: str, duration: int = 300):
        """
        Mark an API key as unavailable for a specified duration
        """
        self.key_status[api_key]['active'] = False
        self.key_status[api_key]['last_error'] = error
        
        logger.warning(f"API key marked unavailable: {error}")
        
        # Schedule reactivation
        def reactivate_key():
            time.sleep(duration)
            self.key_status[api_key]['active'] = True
            self.key_status[api_key]['last_error'] = None
            logger.info(f"API key reactivated after {duration}s cooldown")
        
        thread = threading.Thread(target=reactivate_key)
        thread.daemon = True
        thread.start()
    
    def _create_session(self, api_key: str) -> requests.Session:
        """Create a requests session with proper headers"""
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        })
        return session
    
    def _execute_query_with_failover(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute GraphQL query with automatic failover between API keys
        """
        if variables is None:
            variables = {}
        
        payload = {
            'query': query,
            'variables': variables
        }
        
        last_error = None
        
        # Try each API key
        for attempt in range(len(self.api_keys)):
            api_key = self.get_next_available_key()
            session = self._create_session(api_key)
            
            try:
                logger.info(f"API Request (attempt {attempt + 1})")
                response = session.post(
                    'https://api.fireflies.ai/graphql',
                    json=payload,
                    timeout=60
                )
                
                logger.info(f"API Response Status: {response.status_code} (Key: ...{api_key[-8:]})")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for GraphQL errors (including rate limiting)
                    if 'errors' in data:
                        error_messages = [error.get('message', '') for error in data['errors']]
                        error_text = '; '.join(error_messages)
                        
                        # Check for rate limiting
                        if any('too many requests' in msg.lower() for msg in error_messages):
                            logger.warning(f"GraphQL errors: {error_text}")
                            
                            # Extract retry timestamp if available
                            retry_duration = 300  # Default 5 minutes
                            for error in data['errors']:
                                if 'retryAfter' in error.get('extensions', {}):
                                    retry_after_ms = error['extensions']['retryAfter']
                                    retry_duration = max(60, (retry_after_ms - int(time.time() * 1000)) // 1000)
                            
                            self.mark_key_unavailable(api_key, f"GraphQL rate limited until {datetime.fromtimestamp(time.time() + retry_duration)}", retry_duration)
                            continue
                        else:
                            logger.error(f"GraphQL errors: {error_text}")
                            last_error = f"GraphQL errors: {error_text}"
                            continue
                    
                    return data
                
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    last_error = error_msg
                    
                    if response.status_code == 429:  # Rate limited
                        self.mark_key_unavailable(api_key, "HTTP 429 rate limited", 300)
                    
                    continue
            
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error(error_msg)
                last_error = error_msg
                continue
        
        # All keys failed
        raise Exception(f"All API keys failed. Last error: {last_error}")
    
    def is_cache_stale(self) -> bool:
        """
        Check if the comprehensive transcripts cache is stale
        """
        return self.cache_manager.is_cache_stale('fireflies_comprehensive', 'all_transcripts')
    
    def get_comprehensive_transcripts_with_pagination(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get comprehensive transcripts with intelligent caching and pagination
        """
        # Check cache first (unless forcing refresh)
        if not force_refresh:
            cached_data = self.cache_manager.get_fireflies_transcripts()
            if cached_data and 'transcripts' in cached_data:
                logger.info(f"Retrieved {len(cached_data['transcripts'])} transcripts from cache")
                return cached_data['transcripts']
        
        logger.info("Cache miss or forced refresh - fetching from API")
        return self._fetch_with_pagination()
    
    def _fetch_with_pagination(self) -> List[Dict[str, Any]]:
        """
        Fetch transcripts with pagination using the comprehensive GraphQL query
        """
        logger.info("Starting comprehensive transcript fetch with pagination...")
        
        all_transcripts = []
        page = 1
        limit = 50  # Reasonable page size
        max_pages = 10  # Safety limit
        
        # Comprehensive GraphQL query
        query = """
        query ListTranscripts($mine: Boolean!, $limit: Int!) {
          transcripts(mine: $mine, limit: $limit) {
            id
            title
            date
            duration
            transcript_url
            meeting_link
            organizer_email
            host_email
            meeting_info {
              silent_meeting
              fred_joined
              summary_status
            }
            summary {
              overview
              outline
              action_items
              keywords
              topics_discussed
              shorthand_bullet
              bullet_gist
              gist
              short_summary
              short_overview
              meeting_type
            }
            sentences {
              index
              speaker_id
              speaker_name
              raw_text
              text
              start_time
              end_time
              ai_filters {
                task
                pricing
                metric
                question
                date_and_time
                sentiment
              }
            }
            meeting_attendees {
              displayName
              email
              location
            }
          }
        }
        """
        
        while page <= max_pages:
            logger.info(f"Fetching page {page} (limit: {limit})")
            
            variables = {
                "mine": False,
                "limit": limit
            }
            
            try:
                response_data = self._execute_query_with_failover(query, variables)
                
                if 'data' in response_data and 'transcripts' in response_data['data']:
                    transcripts = response_data['data']['transcripts']
                    
                    if not transcripts:
                        logger.info("No more transcripts available")
                        break
                    
                    all_transcripts.extend(transcripts)
                    logger.info(f"Retrieved {len(transcripts)} transcripts (total: {len(all_transcripts)})")
                    
                    # If we got fewer than the limit, we've reached the end
                    if len(transcripts) < limit:
                        logger.info("Reached end of available transcripts")
                        break
                    
                    page += 1
                else:
                    logger.error(f"Unexpected response structure: {response_data}")
                    break
            
            except Exception as e:
                logger.error(f"Failed to fetch page {page}: {str(e)}")
                break
        
        logger.info(f"Completed pagination fetch: {len(all_transcripts)} total transcripts")
        
        # Cache the results
        if all_transcripts:
            success = self.cache_manager.set_fireflies_transcripts(all_transcripts, self.cache_timeout)
            if success:
                logger.info(f"Successfully cached {len(all_transcripts)} comprehensive transcripts")
            else:
                logger.warning("Failed to cache transcripts")
        
        # Save to database
        self._save_transcripts_to_database(all_transcripts)
        
        return all_transcripts
    
    def _save_transcripts_to_database(self, transcripts: List[Dict[str, Any]]) -> None:
        """
        Save transcripts to database for persistence and offline access
        """
        if not transcripts:
            return
        
        try:
            with transaction.atomic():
                saved_count = 0
                for transcript_data in transcripts:
                    fireflies_id = transcript_data.get('id')
                    if not fireflies_id:
                        continue
                    
                    # Parse meeting date
                    meeting_date = None
                    if transcript_data.get('date'):
                        try:
                            # Convert milliseconds to datetime
                            timestamp = int(transcript_data['date']) / 1000
                            meeting_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        except (ValueError, TypeError):
                            meeting_date = django_timezone.now()
                    else:
                        meeting_date = django_timezone.now()
                    
                    # Extract content from sentences
                    content = self._extract_content(transcript_data)
                    
                    # Calculate duration and participant count
                    duration_minutes = transcript_data.get('duration', 0) // 60000 if transcript_data.get('duration') else 0
                    attendees = transcript_data.get('meeting_attendees', []) or []
                    participant_count = len(attendees)
                    
                    # Create or update transcript
                    transcript, created = Transcript.objects.get_or_create(
                        fireflies_id=fireflies_id,
                        defaults={
                            'title': transcript_data.get('title', 'Untitled Meeting')[:500],
                            'meeting_date': meeting_date,
                            'duration_minutes': duration_minutes,
                            'participant_count': participant_count,
                            'raw_data': transcript_data,
                            'content': content,
                            'is_processed': False,
                        }
                    )
                    
                    if created:
                        saved_count += 1
                
                logger.info(f"Saved {saved_count} new transcripts to database")
        
        except Exception as e:
            logger.error(f"Failed to save transcripts to database: {str(e)}")
    
    def _extract_content(self, transcript_data: Dict[str, Any]) -> str:
        """
        Extract readable content from transcript data
        """
        content_parts = []
        
        # Add summary if available
        summary = transcript_data.get('summary', {})
        if summary and summary.get('overview'):
            content_parts.append(f"Overview: {summary['overview']}")
        
        # Add sentences if available
        sentences = transcript_data.get('sentences', [])
        if sentences:
            content_parts.append("\nTranscript:")
            for sentence in sentences[:100]:  # Limit to first 100 sentences
                speaker = sentence.get('speaker_name', 'Unknown')
                text = sentence.get('text', sentence.get('raw_text', ''))
                if text:
                    content_parts.append(f"{speaker}: {text}")
        
        return '\n'.join(content_parts)
    
    def _get_transcripts_from_database(self) -> List[Dict[str, Any]]:
        """
        Get transcripts from database as fallback
        """
        try:
            transcripts = Transcript.objects.all().order_by('-meeting_date')[:100]
            return [transcript.raw_data for transcript in transcripts if transcript.raw_data]
        except Exception as e:
            logger.error(f"Failed to get transcripts from database: {str(e)}")
            return []
    
    def get_today_transcripts(self) -> List[Dict[str, Any]]:
        """
        Get today's transcripts with caching
        """
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        # Check cache first
        cached_data = self.cache_manager.get_fireflies_today(today)
        if cached_data and 'transcripts' in cached_data:
            logger.info(f"Retrieved {len(cached_data['transcripts'])} today's transcripts from cache")
            return cached_data['transcripts']
        
        # Get from comprehensive cache or API
        all_transcripts = self.get_comprehensive_transcripts_with_pagination()
        
        # Filter for today
        today_transcripts = []
        for transcript in all_transcripts:
            if transcript.get('date'):
                try:
                    timestamp = int(transcript['date']) / 1000
                    transcript_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    if transcript_date.strftime('%Y-%m-%d') == today:
                        today_transcripts.append(transcript)
                except (ValueError, TypeError):
                    continue
        
        # Cache today's results
        self.cache_manager.set_fireflies_today(today_transcripts, today)
        
        return today_transcripts
    
    def test_connection(self) -> bool:
        """
        Test connection to Fireflies API
        """
        query = """
        query {
          user {
            user_id
            email
          }
        }
        """
        
        try:
            response = self._execute_query_with_failover(query)
            return 'data' in response and 'user' in response['data']
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def force_cache_refresh(self) -> List[Dict[str, Any]]:
        """
        Force a complete cache refresh
        """
        logger.info("Forcing cache refresh...")
        return self.get_comprehensive_transcripts_with_pagination(force_refresh=True)
    
    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get comprehensive cache status
        """
        # Get cached data to check status
        cached_data = self.cache_manager.get_fireflies_transcripts()
        
        status = {
            'cache_timeout_hours': self.cache_timeout / 3600,
            'cached_transcript_count': len(cached_data['transcripts']) if cached_data and 'transcripts' in cached_data else 0,
            'cache_is_stale': self.is_cache_stale(),
            'active_api_keys': sum(1 for status in self.key_status.values() if status['active']),
            'total_api_keys': len(self.api_keys),
            'last_sync': cached_data.get('cached_at') if cached_data else None,
            'next_refresh': None,  # Will be calculated based on last_sync + timeout
        }
        
        # Calculate next refresh time
        if status['last_sync']:
            try:
                last_sync_dt = datetime.fromisoformat(status['last_sync'].replace('Z', '+00:00'))
                next_refresh = last_sync_dt + timedelta(seconds=self.cache_timeout)
                status['next_refresh'] = next_refresh.isoformat()
            except (ValueError, TypeError):
                pass
        
        return status


class FirefliesClient:
    """Legacy compatibility wrapper"""
    
    def __init__(self, api_key: str, cache_timeout: int = 14400):
        self.client = MultiKeyFirefliesClient([api_key], cache_timeout)
    
    def get_today_transcripts(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        return self.client.get_today_transcripts()
    
    def test_connection(self) -> bool:
        return self.client.test_connection()


def get_fireflies_client() -> MultiKeyFirefliesClient:
    """
    Get configured Fireflies client with multi-key failover
    """
    fireflies_config = settings.EXTERNAL_APIS.get('FIREFLIES', {})
    
    api_keys = []
    
    # Primary API key
    if fireflies_config.get('API_KEY'):
        api_keys.append(fireflies_config['API_KEY'])
    
    # Failover keys
    if fireflies_config.get('FAILOVER_KEY'):
        api_keys.append(fireflies_config['FAILOVER_KEY'])
    
    if fireflies_config.get('SECONDARY_KEY'):
        api_keys.append(fireflies_config['SECONDARY_KEY'])
    
    if not api_keys:
        raise ValueError("No Fireflies API keys configured")
    
    cache_timeout = fireflies_config.get('CACHE_TIMEOUT', 14400)
    
    return MultiKeyFirefliesClient(api_keys, cache_timeout) 