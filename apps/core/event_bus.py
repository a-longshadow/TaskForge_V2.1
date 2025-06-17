"""
Event Bus System for Inter-Module Communication
"""

import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('apps.core.event_bus')


class Event:
    """Event object for inter-module communication"""
    
    def __init__(self, event_type: str, data: Dict[str, Any], 
                 source_module: str = None, correlation_id: str = None):
        self.id = str(uuid.uuid4())
        self.event_type = event_type
        self.data = data
        self.source_module = source_module
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.processed = False
        self.processing_errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'data': self.data,
            'source_module': self.source_module,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'processing_errors': self.processing_errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        event = cls(
            event_type=data['event_type'],
            data=data['data'],
            source_module=data.get('source_module'),
            correlation_id=data.get('correlation_id')
        )
        event.id = data['id']
        event.timestamp = datetime.fromisoformat(data['timestamp'])
        event.processed = data.get('processed', False)
        event.processing_errors = data.get('processing_errors', [])
        return event


class EventHandler:
    """Base class for event handlers"""
    
    def __init__(self, handler_id: str, handler_func: Callable):
        self.handler_id = handler_id
        self.handler_func = handler_func
        self.success_count = 0
        self.error_count = 0
        self.last_error = None
    
    def handle(self, event: Event) -> bool:
        """Handle an event, return True if successful"""
        try:
            result = self.handler_func(event)
            self.success_count += 1
            return bool(result)
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Event handler {self.handler_id} failed: {e}")
            return False


class EventBus:
    """Event Bus for inter-module communication"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.subscribers: Dict[str, List[EventHandler]] = {}
        self.event_queue: List[Event] = []
        self.processed_events: List[Event] = []
        self.is_initialized = False
        
    @classmethod
    def get_instance(cls) -> 'EventBus':
        """Get singleton instance of EventBus"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def initialize(cls):
        """Initialize the event bus"""
        instance = cls.get_instance()
        if not instance.is_initialized:
            instance.is_initialized = True
            logger.info("EventBus initialized successfully")
    
    def subscribe(self, event_type: str, handler_func: Callable, 
                 handler_id: str = None, module_name: str = None) -> str:
        """Subscribe to events of a specific type"""
        if handler_id is None:
            handler_id = f"{module_name or 'unknown'}_{event_type}_{uuid.uuid4().hex[:8]}"
        
        handler = EventHandler(handler_id, handler_func)
        
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler {handler_id} to event type {event_type}")
        return handler_id
    
    def publish(self, event_type: str, data: Dict[str, Any], 
               source_module: str = None, correlation_id: str = None,
               sync: bool = False) -> str:
        """Publish an event to all subscribers"""
        event = Event(
            event_type=event_type,
            data=data,
            source_module=source_module,
            correlation_id=correlation_id
        )
        
        logger.info(f"Publishing event {event.id} of type {event_type} from {source_module}")
        
        if sync:
            self._process_event(event)
        else:
            self.event_queue.append(event)
        
        return event.id
    
    def _process_event(self, event: Event) -> bool:
        """Process a single event by notifying all subscribers"""
        if event.event_type not in self.subscribers:
            logger.warning(f"No subscribers for event type {event.event_type}")
            return False
        
        handlers = self.subscribers[event.event_type]
        success_count = 0
        
        for handler in handlers:
            success = handler.handle(event)
            if success:
                success_count += 1
            else:
                event.processing_errors.append(f"Handler {handler.handler_id} failed")
        
        event.processed = True
        self.processed_events.append(event)
        
        return success_count > 0


class EventTypes:
    """Standard event types for TaskForge"""
    
    # Ingestion events
    TRANSCRIPT_INGESTED = 'transcript.ingested'
    TRANSCRIPT_SYNC_STARTED = 'transcript.sync_started'
    TRANSCRIPT_SYNC_COMPLETED = 'transcript.sync_completed'
    
    # Processing events
    TASKS_EXTRACTED = 'tasks.extracted'
    TASK_CREATED = 'task.created'
    TASK_UPDATED = 'task.updated'
    
    # Review events
    TASK_REVIEWED = 'task.reviewed'
    TASK_APPROVED = 'task.approved'
    TASK_REJECTED = 'task.rejected'
    
    # Delivery events
    TASK_DELIVERED = 'task.delivered'
    TASK_DELIVERY_FAILED = 'task.delivery_failed'
    
    # System events
    SYSTEM_ERROR = 'system.error'
    GUARDIAN_ALERT = 'guardian.alert'


# Convenience functions
def publish_event(event_type: str, data: Dict[str, Any], 
                 source_module: str = None, correlation_id: str = None,
                 sync: bool = False) -> str:
    """Convenience function to publish an event"""
    event_bus = EventBus.get_instance()
    return event_bus.publish(event_type, data, source_module, correlation_id, sync)


def subscribe_to_event(event_type: str, handler_func: Callable,
                      handler_id: str = None, module_name: str = None) -> str:
    """Convenience function to subscribe to an event"""
    event_bus = EventBus.get_instance()
    return event_bus.subscribe(event_type, handler_func, handler_id, module_name) 