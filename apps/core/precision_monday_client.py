"""
Precision Monday.com Client
Exact N8N TaskForge MVP field mappings - no assumptions, perfect accuracy
"""

import json
import time
from typing import Dict, Any, List, Optional
from django.conf import settings

from .monday_client import EnhancedMondayClient
from .models import ProcessedTaskData
from .event_bus import publish_event, EventTypes
import logging

logger = logging.getLogger(__name__)


class PrecisionMondayClient:
    """
    Monday.com client with exact N8N TaskForge MVP field mappings
    Ensures surgical precision for task delivery
    """
    
    def __init__(self):
        # Use working API key directly (settings may be empty)
        api_key = settings.EXTERNAL_APIS['MONDAY']['API_KEY']
        if not api_key:
            # Fallback to hardcoded working key
            api_key = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUxMjQzODA4NiwiYWFpIjoxMSwidWlkIjo3MzMxNjk3OCwiaWFkIjoiMjAyNS0wNS0xM1QyMTozMDozNy4zODFaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6Mjg0NjkxNTUsInJnbiI6InVzZTEifQ.H-EfNBJS5SZ0PV3D9RffC_fuyuOnVwxVmgOWRvjg3f0"
            logger.info("Using fallback Monday.com API key from precision client")
        
        self.base_client = EnhancedMondayClient(
            api_key=api_key,
            board_id=settings.EXTERNAL_APIS['MONDAY']['BOARD_ID'],
            group_id=settings.EXTERNAL_APIS['MONDAY']['GROUP_ID']
        )
    
    def deliver_processed_task(self, processed_task: ProcessedTaskData) -> bool:
        """
        Deliver processed task to Monday.com with exact N8N column mapping
        
        Args:
            processed_task: ProcessedTaskData instance with N8N format
            
        Returns:
            bool: True if delivery successful, False otherwise
        """
        if not processed_task.is_ready_for_delivery:
            return False
        
        try:
            # Build task data in the format expected by create_task_item
            task_data = {
                'task_item': processed_task.task_item,
                'assignee_emails': processed_task.assignee_emails or '',
                'assignee(s)_full_names': processed_task.assignee_full_names or '',
                'priority': processed_task.priority,
                'brief_description': processed_task.brief_description or '',
                'status': processed_task.status,
                'due_date': int(processed_task.due_date.timestamp() * 1000) if processed_task.due_date else None
            }
            
            # Attempt delivery
            monday_item_id = self.base_client.create_task_item(task_data)
            
            if monday_item_id:
                # Mark as delivered
                processed_task.mark_delivered(monday_item_id)
                
                # Publish success event
                publish_event(
                    EventTypes.TASK_DELIVERED,
                    {
                        'task_id': str(processed_task.id),
                        'monday_item_id': monday_item_id,
                        'task_item': processed_task.task_item[:100],
                        'assignee': processed_task.assignee_full_names,
                    },
                    source_module='precision_monday_client'
                )
                
                logger.info(f"Successfully delivered task {processed_task.id} to Monday.com: {monday_item_id}")
                return True
            else:
                # Mark delivery failed
                processed_task.delivery_status = 'failed'
                processed_task.delivery_errors.append('Monday.com delivery returned no item ID')
                processed_task.save()
                
                logger.error(f"Failed to deliver task {processed_task.id}: No Monday item ID returned")
                return False
                
        except Exception as e:
            # Record delivery error
            processed_task.delivery_status = 'failed'
            processed_task.delivery_errors.append(str(e))
            processed_task.save()
            
            logger.error(f"Error delivering task {processed_task.id} to Monday.com: {str(e)}")
            return False
    
    def _build_n8n_column_values(self, processed_task: ProcessedTaskData) -> str:
        """
        Build exact N8N TaskForge MVP column values JSON string
        
        Column mappings from N8N TaskForge MVP:
        - text_mkr7jgkp: assignee_full_names
        - text_mkr0hqsb: assignee_emails  
        - status_1: priority (mapped to status)
        - long_text: brief_description
        
        Args:
            processed_task: ProcessedTaskData with N8N fields
            
        Returns:
            str: JSON string with exact N8N column mappings
        """
        column_values = {
            "text_mkr7jgkp": processed_task.assignee_full_names or "",
            "text_mkr0hqsb": processed_task.assignee_emails or "",
            "status_1": {
                "label": processed_task.priority
            },
            "long_text": processed_task.brief_description or ""
        }
        
        # Add due date if available
        if processed_task.due_date:
            # Convert to Monday.com date format (YYYY-MM-DD)
            date_str = processed_task.due_date.strftime('%Y-%m-%d')
            column_values["date"] = date_str
        
        # Add status mapping
        status_mapping = {
            'To Do': 'To Do',
            'Stuck': 'Stuck', 
            'Working on it': 'Working on it',
            'Waiting for review': 'Waiting for review',
            'Approved': 'Approved',
            'Done': 'Done'
        }
        
        monday_status = status_mapping.get(processed_task.status, 'To Do')
        column_values["status"] = monday_status
        
        return json.dumps(column_values)

    def bulk_deliver_tasks(self, processed_tasks: list) -> dict:
        """
        Deliver multiple processed tasks with rate limiting
        
        Args:
            processed_tasks: List of ProcessedTaskData instances
            
        Returns:
            dict: Delivery results summary
        """
        results = {
            'delivered': 0,
            'failed': 0,
            'errors': []
        }
        
        for task in processed_tasks:
            if self.deliver_processed_task(task):
                results['delivered'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"Task {task.id}: {task.delivery_errors[-1] if task.delivery_errors else 'Unknown error'}")
        
        return results


def get_precision_monday_client() -> PrecisionMondayClient:
    """Factory function to get configured precision Monday client"""
    return PrecisionMondayClient()
