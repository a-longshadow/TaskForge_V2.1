"""
Monday.com GraphQL API client with comprehensive rate limiting and retry logic
"""

import logging
import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.conf import settings

from .circuit_breaker import CircuitBreakerRegistry

logger = logging.getLogger('apps.core.monday_client')


class EnhancedMondayClient:
    """Enhanced Monday.com client with rate limiting, retry logic, and quota tracking"""
    
    def __init__(self, api_key: str, board_id: str, group_id: str, rate_limit_per_minute: int = 30):
        self.api_key = api_key
        self.board_id = board_id
        self.group_id = group_id
        self.base_url = 'https://api.monday.com/v2'
        
        # Rate limiting configuration
        self.rate_limit_per_minute = rate_limit_per_minute
        self.min_request_interval = 60.0 / rate_limit_per_minute  # seconds between requests
        self.last_request_time = 0
        
        # Retry configuration
        self.retry_attempts = settings.EXTERNAL_APIS['MONDAY'].get('RETRY_ATTEMPTS', 3)
        self.backoff_factor = settings.EXTERNAL_APIS['MONDAY'].get('BACKOFF_FACTOR', 2.0)
        self.max_backoff_time = settings.EXTERNAL_APIS['MONDAY'].get('MAX_BACKOFF_TIME', 300)
        
        # Quota tracking
        self.quota_tracker = {
            'requests_today': 0,
            'last_reset': datetime.now().date(),
            'warning_threshold': settings.EXTERNAL_APIS['MONDAY'].get('QUOTA_WARNING_THRESHOLD', 80)
        }
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreakerRegistry.get_instance().get_or_create(
            'monday_api',
            failure_threshold=5,
            timeout=300  # 5 minutes
        )
        
        # Session configuration
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': api_key,
            'Content-Type': 'application/json',
            'API-Version': '2023-10'
        })
        
        logger.info(f"Initialized EnhancedMondayClient with {rate_limit_per_minute}/min rate limit")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Monday.com rate limiting: sleeping {sleep_time:.2f}s")
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
        
        # Check for quota warnings (assuming 10000 requests/day limit for Monday.com)
        daily_limit = 10000  # Monday.com typical daily limit
        usage_percentage = (self.quota_tracker['requests_today'] / daily_limit) * 100
        
        if usage_percentage >= self.quota_tracker['warning_threshold']:
            logger.warning(f"Monday.com API quota warning: {usage_percentage:.1f}% used ({self.quota_tracker['requests_today']}/{daily_limit})")
    
    def _execute_query_with_retry(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a GraphQL query with retry logic and circuit breaker"""
        
        def make_request():
            self._enforce_rate_limit()
            self._update_quota_tracker()
            
            payload = {
                'query': query,
                'variables': variables or {}
            }
            
            response = self.session.post(self.base_url, json=payload, timeout=30)
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '60')
                raise requests.exceptions.RequestException(f"Rate limited. Retry after {retry_after} seconds")
            
            response.raise_for_status()
            
            data = response.json()
            
            if 'errors' in data:
                error_msg = data['errors']
                logger.error(f"Monday.com GraphQL errors: {error_msg}")
                
                # Check for rate limiting in GraphQL errors
                error_str = str(error_msg).lower()
                if 'rate' in error_str or 'limit' in error_str or 'quota' in error_str:
                    raise requests.exceptions.RequestException(f"Rate limit/quota error: {error_msg}")
                
                raise Exception(f"Monday.com GraphQL errors: {error_msg}")
            
            return data.get('data', {})
        
        # Implement retry with exponential backoff
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                return self.circuit_breaker.call(make_request)
            except requests.exceptions.RequestException as e:
                last_exception = e
                
                if attempt < self.retry_attempts - 1:  # Don't sleep on last attempt
                    backoff_time = min(
                        self.backoff_factor ** attempt,
                        self.max_backoff_time
                    )
                    logger.warning(f"Monday.com API attempt {attempt + 1} failed: {e}. Retrying in {backoff_time:.1f}s")
                    time.sleep(backoff_time)
                else:
                    logger.error(f"Monday.com API failed after {self.retry_attempts} attempts")
            except Exception as e:
                logger.error(f"Monday.com API non-retryable error: {e}")
                raise
        
        # If we get here, all retries failed
        raise last_exception
    
    def create_task_item(self, task_data: Dict[str, Any]) -> Optional[str]:
        """Create a new item in Monday.com from extracted task data with enhanced error handling
        
        Expected task_data format (from Gemini AI extraction):
        {
            "task_item": "Task name/title",
            "assignee_emails": "email1@domain.com,email2@domain.com",
            "assignee(s)_full_names": "John Doe,Jane Smith", 
            "priority": "High|Medium|Low",
            "brief_description": "30-50 word description",
            "due_date": 1234567890000,  # UTC milliseconds or null
            "status": "To Do|Stuck|Working on it|Waiting for review|Approved|Done"
        }
        
        Monday.com field mappings:
        1. task name -> item_name (built-in)
        2. team member -> text_mkr7jgkp (text column)
        3. priority -> status_1 (status column)  
        4. Status -> status (status column)
        5. brief description -> long_text (long text column)
        6. date expected -> date_mkr7ymmh (date column)
        """
        
        # Extract task information
        task_title = task_data.get('task_item', 'Untitled Task')
        assignee_emails = task_data.get('assignee_emails', '')
        assignee_names = task_data.get('assignee(s)_full_names', '')
        priority = task_data.get('priority', 'Medium')
        description = task_data.get('brief_description', '')
        status = task_data.get('status', 'To Do')
        due_date_ms = task_data.get('due_date')
        
        # Build column values using the correct field IDs
        column_values = {}
        
        # 1. Task name is handled by item_name parameter
        
        # 2. Team member (full name) - text_mkr7jgkp
        if assignee_names:
            column_values['text_mkr7jgkp'] = assignee_names
        
        # 3. Priority - status_1 (map to Monday.com priority values)
        priority_mapping = {
            'High': 'High',
            'Medium': 'Medium', 
            'Low': 'Low'
        }
        if priority in priority_mapping:
            column_values['status_1'] = priority_mapping[priority]
        
        # 4. Status - status (map to Monday.com status values)
        status_mapping = {
            'To Do': 'To Do',
            'Working on it': 'Working on it', 
            'Stuck': 'Stuck',
            'Waiting for review': 'Waiting for review',
            'Approved': 'Approved',
            'Done': 'Done'
        }
        if status in status_mapping:
            column_values['status'] = status_mapping[status]
        
        # 5. Brief description - long_text
        if description:
            column_values['long_text'] = description
            
        # 6. Date expected - date_mkr7ymmh (convert from UTC ms to date string)
        if due_date_ms:
            try:
                # Convert UTC milliseconds to date string (YYYY-MM-DD format)
                due_date = datetime.fromtimestamp(due_date_ms / 1000.0)
                column_values['date_mkr7ymmh'] = due_date.strftime('%Y-%m-%d')
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid due_date format: {due_date_ms}, error: {e}")
        
        mutation = """
        mutation CreateItem($boardId: ID!, $groupId: String!, $itemName: String!, $columnValues: JSON!) {
            create_item(
                board_id: $boardId,
                group_id: $groupId,
                item_name: $itemName,
                column_values: $columnValues
            ) {
                id
                name
            }
        }
        """
        
        variables = {
            'boardId': self.board_id,
            'groupId': self.group_id,
            'itemName': task_title,
            'columnValues': json.dumps(column_values)
        }
        
        logger.info(f"Creating Monday.com item: {task_title}")
        logger.debug(f"Column values: {column_values}")
        
        try:
            data = self._execute_query_with_retry(mutation, variables)
            created_item = data.get('create_item')
            
            if created_item:
                item_id = created_item.get('id')
                item_name = created_item.get('name')
                logger.info(f"Successfully created Monday.com item: {item_name} (ID: {item_id})")
                return item_id
            else:
                logger.error("No item returned from Monday.com create mutation")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create Monday.com item '{task_title}': {e}")
            return None
    
    def get_board_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the configured board including column details"""
        query = """
        query GetBoard($boardId: ID!) {
            boards(ids: [$boardId]) {
                id
                name
                description
                groups {
                    id
                    title
                }
                columns {
                    id
                    title
                    type
                    settings_str
                }
            }
        }
        """
        
        variables = {'boardId': self.board_id}
        
        try:
            data = self._execute_query_with_retry(query, variables)
            boards = data.get('boards', [])
            
            if boards:
                board = boards[0]
                logger.info(f"Board info: {board.get('name', 'Unknown')} (ID: {board.get('id')})")
                
                # Log column information for debugging
                columns = board.get('columns', [])
                logger.info("Available columns:")
                for col in columns:
                    logger.info(f"  - {col.get('title')} (ID: {col.get('id')}, Type: {col.get('type')})")
                
                return board
            else:
                logger.warning(f"Board {self.board_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get board info: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test connection to Monday.com API"""
        query = """
        query TestConnection {
            me {
                id
                name
                email
            }
        }
        """
        
        try:
            data = self._execute_query_with_retry(query)
            user = data.get('me')
            
            if user:
                logger.info(f"Connected to Monday.com as: {user.get('name', 'Unknown')} ({user.get('email', 'No email')})")
                return True
            else:
                logger.warning("Monday.com connection test failed - no user data")
                return False
                
        except Exception as e:
            logger.error(f"Monday.com connection test failed: {e}")
            return False
    
    def bulk_create_tasks(self, tasks: List[Dict[str, Any]]) -> List[Optional[str]]:
        """Create multiple tasks with rate limiting between requests"""
        results = []
        
        logger.info(f"Creating {len(tasks)} tasks in Monday.com with rate limiting")
        
        for i, task in enumerate(tasks):
            logger.info(f"Creating task {i+1}/{len(tasks)}: {task.get('task_item', 'Unknown')}")
            
            result = self.create_task_item(task)
            results.append(result)
            
            # Rate limiting is handled in create_task_item, but add extra delay for bulk operations
            if i < len(tasks) - 1:  # Don't sleep after last task
                time.sleep(1)  # Extra 1-second delay between bulk operations
        
        successful_creates = sum(1 for r in results if r is not None)
        logger.info(f"Bulk creation completed: {successful_creates}/{len(tasks)} successful")
        
        return results
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota and rate limiting status"""
        return {
            'requests_today': self.quota_tracker['requests_today'],
            'last_reset': self.quota_tracker['last_reset'].isoformat(),
            'warning_threshold': self.quota_tracker['warning_threshold'],
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'retry_attempts': self.retry_attempts,
            'backoff_factor': self.backoff_factor,
            'max_backoff_time': self.max_backoff_time,
            'circuit_breaker_state': self.circuit_breaker.state.value
        }


def get_monday_client() -> EnhancedMondayClient:
    """Get enhanced Monday.com client with rate limiting"""
    # Use the working API key provided by the user
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUxMjQzODA4NiwiYWFpIjoxMSwidWlkIjo3MzMxNjk3OCwiaWFkIjoiMjAyNS0wNS0xM1QyMTozMDozNy4zODFaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6Mjg0NjkxNTUsInJnbiI6InVzZTEifQ.H-EfNBJS5SZ0PV3D9RffC_fuyuOnVwxVmgOWRvjg3f0"
    board_id = "9212659997"
    group_id = "group_mkqyryrz"
    
    # Get rate limiting configuration from settings
    monday_config = settings.EXTERNAL_APIS['MONDAY']
    rate_limit = monday_config.get('RATE_LIMIT_PER_MINUTE', 30)
    
    return EnhancedMondayClient(api_key, board_id, group_id, rate_limit) 