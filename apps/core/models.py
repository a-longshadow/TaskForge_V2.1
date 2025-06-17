"""
Core models for TaskForge
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import json


class TimestampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Transcript(TimestampedModel):
    """Store raw transcripts from Fireflies API"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fireflies_id = models.CharField(max_length=255, unique=True, db_index=True)
    title = models.CharField(max_length=500, blank=True)
    meeting_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=0)
    participant_count = models.PositiveIntegerField(default=0)
    
    # Store raw JSON data from Fireflies
    raw_data = models.JSONField(default=dict)
    content = models.TextField(blank=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_errors = models.JSONField(default=list)
    
    class Meta:
        db_table = 'core_transcripts'
        indexes = [
            models.Index(fields=['fireflies_id']),
            models.Index(fields=['meeting_date']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Transcript {self.fireflies_id} - {self.title[:50]}"
    
    def mark_processed(self):
        """Mark transcript as processed"""
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['is_processed', 'processed_at'])


class ActionItem(TimestampedModel):
    """Individual tasks extracted from transcripts"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('delivered', 'Delivered to Monday.com'),
        ('failed', 'Delivery Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE, related_name='action_items')
    
    # Task details
    title = models.CharField(max_length=200)
    description = models.TextField()
    assignee = models.CharField(max_length=100, blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # AI extraction metadata
    confidence_score = models.FloatField(default=0.0)
    ai_model_version = models.CharField(max_length=50, blank=True)
    extraction_metadata = models.JSONField(default=dict)
    
    # Review and approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='reviewed_tasks'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Delivery tracking
    monday_item_id = models.CharField(max_length=100, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_errors = models.JSONField(default=list)
    
    # Auto-push tracking
    auto_push_after = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'core_action_items'
        indexes = [
            models.Index(fields=['transcript']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority']),
            models.Index(fields=['auto_push_after']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Task: {self.title[:50]} ({self.status})"
    
    def approve(self, user=None, notes=""):
        """Approve the task"""
        self.status = 'approved'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
    
    def reject(self, user=None, notes=""):
        """Reject the task"""
        self.status = 'rejected'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
    
    def mark_delivered(self, monday_item_id=None):
        """Mark task as delivered to Monday.com"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        if monday_item_id:
            self.monday_item_id = monday_item_id
        self.save()
    
    @property
    def is_stale(self):
        """Check if task is past auto-push deadline"""
        if not self.auto_push_after:
            return False
        return timezone.now() > self.auto_push_after
    
    @property
    def time_until_auto_push(self):
        """Time remaining until auto-push"""
        if not self.auto_push_after:
            return None
        return self.auto_push_after - timezone.now()


class DailyReport(TimestampedModel):
    """Daily AI-generated summaries"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_date = models.DateField(unique=True, db_index=True)
    
    # Report content
    summary = models.TextField()
    key_insights = models.JSONField(default=list)
    task_statistics = models.JSONField(default=dict)
    
    # AI generation metadata
    ai_model_version = models.CharField(max_length=50, blank=True)
    generation_duration = models.FloatField(default=0.0)
    source_transcripts_count = models.PositiveIntegerField(default=0)
    source_tasks_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'core_daily_reports'
        indexes = [
            models.Index(fields=['report_date']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Daily Report - {self.report_date}"


class SystemEvent(TimestampedModel):
    """System events for auditing and monitoring"""
    
    EVENT_TYPES = [
        ('transcript_sync', 'Transcript Sync'),
        ('task_extraction', 'Task Extraction'),
        ('task_review', 'Task Review'),
        ('task_delivery', 'Task Delivery'),
        ('system_error', 'System Error'),
        ('guardian_alert', 'Guardian Alert'),
        ('health_check', 'Health Check'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    
    # Event details
    message = models.CharField(max_length=500)
    details = models.JSONField(default=dict)
    correlation_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Source information
    source_module = models.CharField(max_length=50, blank=True)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='system_events'
    )
    
    class Meta:
        db_table = 'core_system_events'
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['source_module']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.severity} - {self.message[:50]}" 