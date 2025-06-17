"""
Monday.com GraphQL API client for task delivery
"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.conf import settings

logger = logging.getLogger('apps.core.monday_client')


class MondayClient:
    """Client for Monday.com GraphQL API"""
    
    def __init__(self, api_key: str, board_id: str, group_id: str):
        self.api_key = api_key
        self.board_id = board_id
        self.group_id = group_id
        self.base_url = 'https://api.monday.com/v2'
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': api_key,
            'Content-Type': 'application/json',
            'API-Version': '2023-10'
        })
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        try:
            response = self.session.post(self.base_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'errors' in data:
                logger.error(f"Monday.com GraphQL errors: {data['errors']}")
                raise Exception(f"Monday.com GraphQL errors: {data['errors']}")
            
            return data.get('data', {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Monday.com API request failed: {e}")
            raise Exception(f"Monday.com API request failed: {e}")
    
    def create_task_item(self, task_data: Dict[str, Any]) -> Optional[str]:
        """Create a new item in Monday.com from extracted task data
        
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
        logger.info(f"Column values: {column_values}")
        
        try:
            data = self._execute_query(mutation, variables)
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
            data = self._execute_query(query, variables)
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
            data = self._execute_query(query)
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
        """Create multiple tasks in Monday.com"""
        results = []
        
        for i, task in enumerate(tasks):
            logger.info(f"Creating task {i+1}/{len(tasks)}: {task.get('task_item', 'Untitled')}")
            item_id = self.create_task_item(task)
            results.append(item_id)
            
        return results


def get_monday_client() -> MondayClient:
    """Get configured Monday.com client"""
    # Use the working API key provided by the user
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUxMjQzODA4NiwiYWFpIjoxMSwidWlkIjo3MzMxNjk3OCwiaWFkIjoiMjAyNS0wNS0xM1QyMTozMDozNy4zODFaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6Mjg0NjkxNTUsInJnbiI6InVzZTEifQ.H-EfNBJS5SZ0PV3D9RffC_fuyuOnVwxVmgOWRvjg3f0"
    board_id = "9212659997"
    group_id = "group_mkqyryrz"
    
    return MondayClient(api_key, board_id, group_id) 