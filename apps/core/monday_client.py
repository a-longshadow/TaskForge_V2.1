"""
Monday.com GraphQL API client for task delivery
"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional
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
            'Content-Type': 'application/json'
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
        """Create a new item in Monday.com from extracted task data"""
        
        # Extract task information
        task_title = task_data.get('task_item', 'Untitled Task')
        assignee_emails = task_data.get('assignee_emails', '')
        priority = task_data.get('priority', 'Medium')
        description = task_data.get('brief_description', '')
        status = task_data.get('status', 'To Do')
        
        # Map TaskForge status to Monday.com status (using actual board labels)
        status_mapping = {
            'To Do': 'To Do',
            'Working on it': 'Working on it', 
            'Stuck': 'Stuck',
            'Waiting for review': 'Waiting for review',
            'Review': 'Review',
            'Approved': 'Approved',
            'Done': 'Done',
            'Deprioritized': 'Deprioritized'
        }
        monday_status = status_mapping.get(status, 'To Do')
        
        # Map priority
        priority_mapping = {
            'Low': 'low',
            'Medium': 'medium', 
            'High': 'high'
        }
        monday_priority = priority_mapping.get(priority, 'medium')
        
        # Build column values
        column_values = {
            'status': monday_status,
            'priority': monday_priority
        }
        
        # Skip person column for demo (emails don't exist in Monday.com workspace)
        # if assignee_emails:
        #     column_values['person'] = assignee_emails
        
        # Add description as text column
        if description:
            column_values['text'] = description
        
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
        
        try:
            data = self._execute_query(mutation, variables)
            created_item = data.get('create_item')
            
            if created_item:
                item_id = created_item.get('id')
                item_name = created_item.get('name')
                logger.info(f"Created Monday.com item: {item_name} (ID: {item_id})")
                return item_id
            else:
                logger.error("No item returned from Monday.com create mutation")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create Monday.com item: {e}")
            return None
    
    def get_board_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the configured board"""
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
        created_items = []
        
        for task in tasks:
            item_id = self.create_task_item(task)
            created_items.append(item_id)
            
        successful_creates = [item_id for item_id in created_items if item_id is not None]
        logger.info(f"Successfully created {len(successful_creates)} out of {len(tasks)} tasks in Monday.com")
        
        return created_items


def get_monday_client() -> MondayClient:
    """Get configured Monday.com client"""
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUxMjQzODA4NiwiYWFpIjoxMSwidWlkIjo3MzMxNjk3OCwiaWFkIjoiMjAyNS0wNS0xM1QyMTozMDozNy4zODFaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6Mjg0NjkxNTUsInJnbiI6InVzZTEifQ.H-EfNBJS5SZ0PV3D9RffC_fuyuOnVwxVmgOWRvjg3f0"
    board_id = "9212659997"
    group_id = "group_mkqyryrz"
    
    return MondayClient(api_key, board_id, group_id) 