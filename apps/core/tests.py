"""
Tests for TaskForge core functionality
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from .models import Transcript, ActionItem, DailyReport, SystemEvent
from .health_monitor import HealthMonitor
from .event_bus import EventBus, EventTypes
from .circuit_breaker import CircuitBreakerRegistry
import json
from datetime import datetime


class HealthMonitorTests(TestCase):
    """Test health monitoring system"""
    
    def setUp(self):
        self.health_monitor = HealthMonitor.get_instance()
    
    def test_database_health_check(self):
        """Test database connectivity check"""
        health_check = self.health_monitor.check_database()
        self.assertEqual(health_check.name, "database")
        self.assertEqual(health_check.status, "healthy")
    
    def test_cache_health_check(self):
        """Test cache connectivity check"""
        health_check = self.health_monitor.check_cache()
        self.assertEqual(health_check.name, "cache")
        self.assertEqual(health_check.status, "healthy")
    
    def test_system_health_endpoint(self):
        """Test /health/ endpoint"""
        client = Client()
        response = client.get('/health/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('overall_status', data)
        self.assertIn('checks', data)


class EventBusTests(TestCase):
    """Test event bus system"""
    
    def setUp(self):
        self.event_bus = EventBus.get_instance()
        EventBus.initialize()
    
    def test_event_publication(self):
        """Test event publishing"""
        event_id = self.event_bus.publish(
            EventTypes.TRANSCRIPT_INGESTED,
            {'transcript_id': 'test-123'},
            'test_module'
        )
        self.assertIsNotNone(event_id)
    
    def test_event_subscription(self):
        """Test event subscription"""
        received_events = []
        
        def test_handler(event):
            received_events.append(event)
            return True
        
        handler_id = self.event_bus.subscribe(
            EventTypes.TASK_CREATED,
            test_handler,
            'test_handler'
        )
        
        self.assertIsNotNone(handler_id)
        
        # Publish test event
        self.event_bus.publish(
            EventTypes.TASK_CREATED,
            {'task_id': 'test-task'},
            'test_module',
            sync=True
        )
        
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].event_type, EventTypes.TASK_CREATED)


class CircuitBreakerTests(TestCase):
    """Test circuit breaker functionality"""
    
    def setUp(self):
        self.registry = CircuitBreakerRegistry.get_instance()
    
    def test_circuit_breaker_creation(self):
        """Test circuit breaker creation"""
        breaker = self.registry.get_or_create('test_service')
        self.assertEqual(breaker.name, 'test_service')
        self.assertEqual(breaker.state.value, 'CLOSED')
    
    def test_circuit_breaker_stats(self):
        """Test circuit breaker statistics"""
        # Create a test breaker
        self.registry.get_or_create('test_service')
        
        stats = self.registry.get_all_stats()
        self.assertIn('total_breakers', stats)
        self.assertIn('breakers', stats)
        self.assertTrue(stats['total_breakers'] >= 1)


class ModelTests(TestCase):
    """Test core models"""
    
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_transcript_model(self):
        """Test Transcript model"""
        transcript = Transcript.objects.create(
            fireflies_id='test-transcript-123',
            title='Test Meeting',
            meeting_date=timezone.now(),
            duration_minutes=30,
            participant_count=3,
            content='Test transcript content'
        )
        
        self.assertEqual(transcript.fireflies_id, 'test-transcript-123')
        self.assertEqual(transcript.title, 'Test Meeting')
        self.assertFalse(transcript.is_processed)
        
        # Test mark_processed method
        transcript.mark_processed()
        self.assertTrue(transcript.is_processed)
        self.assertIsNotNone(transcript.processed_at)
    
    def test_action_item_model(self):
        """Test ActionItem model"""
        transcript = Transcript.objects.create(
            fireflies_id='test-transcript-456',
            title='Test Meeting',
            meeting_date=timezone.now(),
            content='Test content'
        )
        
        action_item = ActionItem.objects.create(
            transcript=transcript,
            title='Test Task',
            description='Complete the test task',
            assignee='test@example.com',
            priority='medium'
        )
        
        self.assertEqual(action_item.title, 'Test Task')
        self.assertEqual(action_item.status, 'pending')
        self.assertEqual(action_item.priority, 'medium')
        
        # Test approve method
        action_item.approve(user=self.user, notes="Approved for testing")
        self.assertEqual(action_item.status, 'approved')
        self.assertEqual(action_item.reviewed_by, self.user)
        self.assertIsNotNone(action_item.reviewed_at)
    
    def test_system_event_model(self):
        """Test SystemEvent model"""
        event = SystemEvent.objects.create(
            event_type='system_error',
            severity='error',
            message='Test error message',
            source_module='test_module',
            user=self.user
        )
        
        self.assertEqual(event.event_type, 'system_error')
        self.assertEqual(event.severity, 'error')
        self.assertEqual(event.user, self.user)


class ViewTests(TestCase):
    """Test core views"""
    
    def test_home_view(self):
        """Test home page view"""
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TaskForge')
    
    def test_health_check_view(self):
        """Test health check view"""
        client = Client()
        response = client.get('/health/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('overall_status', data)
        self.assertIn('timestamp', data)
        self.assertIn('checks', data)
    
    def test_system_stats_view(self):
        """Test system stats view"""
        client = Client()
        response = client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('transcripts', data)
        self.assertIn('action_items', data)
        self.assertIn('daily_reports', data)
        self.assertIn('system_events', data)
        self.assertIn('generated_at', data)


class GuardianIntegrationTests(TestCase):
    """Test Guardian system integration"""
    
    def test_guardian_enabled(self):
        """Test Guardian is properly enabled"""
        from django.conf import settings
        self.assertTrue(getattr(settings, 'GUARDIAN_ENABLED', False))
    
    def test_knowledge_directory_exists(self):
        """Test knowledge directory exists"""
        from django.conf import settings
        knowledge_dir = getattr(settings, 'GUARDIAN_KNOWLEDGE_DIR', None)
        self.assertIsNotNone(knowledge_dir)
        self.assertTrue(knowledge_dir.exists()) 