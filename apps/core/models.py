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


class ProcessedTaskData(TimestampedModel):
    """Processed and validated task data ready for Monday.com delivery"""
    
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('Stuck', 'Stuck'),
        ('Deprioritized', 'Deprioritized'), 
        ('Working on it', 'Working on it'),
        ('Done', 'Done'),
        ('Waiting for review', 'Waiting for review'),
        ('Approved', 'Approved'),
        ('To Do', 'To Do'),
        ('Review', 'Review'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE, related_name='processed_tasks')
    
    # Exact N8N TaskForge MVP fields
    task_item = models.CharField(max_length=500)  # At least 10 natural, coherent words
    assignee_emails = models.CharField(max_length=500, blank=True)  # Comma-separated
    assignee_full_names = models.CharField(max_length=500, blank=True)  # Comma-separated
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    brief_description = models.TextField()  # 30-50 words, human tone
    due_date = models.DateTimeField(null=True, blank=True)  # UTC timestamp
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='To Do')
    
    # Processing metadata
    extraction_confidence = models.FloatField(default=0.0)
    source_sentences = models.JSONField(default=list, blank=True)  # Original sentences that generated this task
    processing_notes = models.TextField(blank=True)
    
    # Monday.com delivery tracking
    monday_item_id = models.CharField(max_length=100, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=50, default='pending')
    delivery_errors = models.JSONField(default=list)
    
    # Human review
    human_approved = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='reviewed_processed_tasks'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'core_processed_task_data'
        indexes = [
            models.Index(fields=['transcript', 'status']),
            models.Index(fields=['priority', 'due_date']),
            models.Index(fields=['human_approved', 'delivery_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Task: {self.task_item[:50]} ({self.status})"
    
    def approve_for_delivery(self, user=None, notes=""):
        """Approve task for delivery to Monday.com"""
        self.human_approved = True
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
    
    def mark_delivered(self, monday_item_id=None):
        """Mark task as delivered to Monday.com"""
        self.delivery_status = 'delivered'
        self.delivered_at = timezone.now()
        if monday_item_id:
            self.monday_item_id = monday_item_id
        self.save()
    
    @property
    def is_ready_for_delivery(self):
        """Check if task is ready for Monday.com delivery"""
        return (
            self.human_approved and 
            self.delivery_status == 'pending' and
            self.task_item and 
            self.assignee_emails
        )


class RawTranscriptCache(TimestampedModel):
    """Unassailable cache for raw Fireflies data - our knowledge base"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fireflies_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Raw Fireflies data - NEVER modify once stored
    raw_fireflies_data = models.JSONField()  # Complete, unmodified Fireflies response
    cache_timestamp = models.DateTimeField(auto_now_add=True)
    
    # Metadata for cache management
    meeting_date = models.DateTimeField()
    meeting_title = models.CharField(max_length=500, blank=True)
    participant_count = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=0)
    
    # Processing status
    processed = models.BooleanField(default=False)
    processing_errors = models.JSONField(default=list)
    
    # Cache validation
    data_hash = models.CharField(max_length=64, db_index=True)  # SHA256 of raw data
    is_valid = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'core_raw_transcript_cache'
        indexes = [
            models.Index(fields=['fireflies_id']),
            models.Index(fields=['meeting_date']),
            models.Index(fields=['processed']),
            models.Index(fields=['cache_timestamp']),
            models.Index(fields=['data_hash']),
        ]
    
    def __str__(self):
        return f"Cached Transcript {self.fireflies_id} - {self.meeting_title[:50]}"
    
    def save(self, *args, **kwargs):
        # Generate data hash for integrity validation
        import hashlib
        data_str = json.dumps(self.raw_fireflies_data, sort_keys=True)
        self.data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def validate_integrity(self):
        """Validate data integrity using hash"""
        import hashlib
        data_str = json.dumps(self.raw_fireflies_data, sort_keys=True)
        expected_hash = hashlib.sha256(data_str.encode()).hexdigest()
        return self.data_hash == expected_hash


class GeminiProcessedTask(TimestampedModel):
    """
    Stores tasks processed by Gemini using the exact prompt.md system specification.
    Each record represents one task extracted from a meeting transcript.
    
    This model follows the EXACT 7-field structure specified in temp/prompt.md:
    1. task_item (string, at least 10 natural, coherent words)
    2. assignee_emails (string, comma-separated if > 1)
    3. assignee(s)_full_names (string, comma-separated)
    4. priority ("High" | "Medium" | "Low")
    5. brief_description (string, 30-50 words, human tone)
    6. due_date (integer UTC ms | null)
    7. status ("To Do" | "Stuck" | "Working on it" | "Waiting for review" | "Approved" | "Done")
    """
    
    # Priority choices exactly as specified in prompt.md
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    
    # Status choices exactly as specified in prompt.md
    STATUS_CHOICES = [
        ('To Do', 'To Do'),
        ('Stuck', 'Stuck'),
        ('Working on it', 'Working on it'),
        ('Waiting for review', 'Waiting for review'),
        ('Approved', 'Approved'),
        ('Done', 'Done'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to source transcript
    raw_transcript = models.ForeignKey(
        RawTranscriptCache, 
        on_delete=models.CASCADE, 
        related_name='gemini_processed_tasks'
    )
    
    # === EXACT PROMPT.MD FIELDS (in order) ===
    
    # 1. task_item (string, at least 10 natural, coherent words) - REQUIRED
    task_item = models.CharField(
        max_length=1000,
        null=False,
        blank=True,  # Allow blank for admin editing
        help_text="At least 10 natural, coherent words describing the task"
    )
    
    # 2. assignee_emails (string, comma-separated if > 1) - REQUIRED
    assignee_emails = models.CharField(
        max_length=500,
        null=False,
        blank=True,  # Allow blank for admin editing
        default='',
        help_text="Comma-separated email addresses of assignees"
    )
    
    # 3. assignee(s)_full_names (string, comma-separated) - REQUIRED
    assignee_full_names = models.CharField(
        max_length=500,
        null=False,
        blank=True,  # Allow blank for admin editing
        default='',
        help_text="Comma-separated full names of assignees"
    )
    
    # 4. priority ("High" | "Medium" | "Low") - REQUIRED
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='Medium',
        null=False,
        blank=False,
        help_text="Task priority as determined by Gemini extraction logic"
    )
    
    # 5. brief_description (string, 30-50 words, human tone) - REQUIRED
    brief_description = models.TextField(
        null=False,
        blank=True,  # Allow blank for admin editing
        help_text="30-50 words, human tone, begins with '<Assigner Full Name> asked <Assignee First Name>...'"
    )
    
    # 6. due_date (integer UTC ms | null)
    due_date_ms = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Due date as UTC milliseconds timestamp, or null if no date specified"
    )
    
    # 7. status ("To Do" | "Stuck" | "Working on it" | "Waiting for review" | "Approved" | "Done") - REQUIRED
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='To Do',
        null=False,
        blank=False,
        help_text="Task status as determined by Gemini extraction logic"
    )
    
    # === PROCESSING METADATA ===
    
    # Gemini processing details
    gemini_model_version = models.CharField(
        max_length=100, 
        default='gemini-2.5-flash',
        null=False,
        blank=False,
        help_text="Gemini model version used for extraction"
    )
    processing_timestamp = models.DateTimeField(auto_now_add=True)
    extraction_confidence = models.FloatField(
        default=0.0,
        help_text="Confidence score from 0.0 to 1.0 for extraction quality"
    )
    
    # Raw Gemini response for debugging
    raw_gemini_response = models.JSONField(
        default=dict,
        help_text="Complete raw response from Gemini API for debugging"
    )
    
    # Source data tracking
    source_sentences = models.JSONField(
        default=list,
        help_text="Original transcript sentences that led to this task extraction"
    )
    
    # Processing order (to preserve chronological order as specified in prompt.md)
    extraction_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which this task appeared in the Gemini response array"
    )
    
    # Validation flags
    meets_word_count_requirement = models.BooleanField(
        default=False,
        help_text="True if task_item has at least 10 words"
    )
    
    meets_description_requirement = models.BooleanField(
        default=False,
        help_text="True if brief_description is 30-50 words"
    )
    
    # Monday.com delivery tracking
    monday_item_id = models.CharField(
        max_length=100, 
        blank=True,
        default='',
        help_text="Monday.com item ID after successful delivery"
    )
    delivered_to_monday = models.BooleanField(
        default=False,
        help_text="True if task has been delivered to Monday.com"
    )
    delivery_timestamp = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when task was delivered to Monday.com"
    )
    delivery_errors = models.JSONField(
        default=list,
        help_text="List of delivery errors if any occurred"
    )
    
    # Auto-push functionality
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    auto_push_enabled = models.BooleanField(
        default=False,
        help_text="Enable automatic pushing to Monday.com when approved"
    )
    auto_mute_enabled = models.BooleanField(
        default=False,
        help_text="Mute automatic pushing (disable auto-push)"
    )
    approval_status = models.CharField(
        max_length=10,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        help_text="Approval status for auto-push functionality"
    )
    rejection_reason = models.TextField(
        blank=True,
        default='',
        help_text="Reason for rejection if status is rejected"
    )
    
    class Meta:
        db_table = 'core_gemini_processed_tasks'
        indexes = [
            models.Index(fields=['raw_transcript']),
            models.Index(fields=['priority']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date_ms']),
            models.Index(fields=['processing_timestamp']),
            models.Index(fields=['extraction_order']),
            models.Index(fields=['delivered_to_monday']),
        ]
        ordering = ['raw_transcript', 'extraction_order']
    
    def __str__(self):
        return f"Gemini Task: {self.task_item[:50]}... ({self.priority})"
    
    def save(self, *args, **kwargs):
        """Override save to validate requirements"""
        # Check word count requirement
        word_count = len(self.task_item.split()) if self.task_item else 0
        self.meets_word_count_requirement = word_count >= 10
        
        # Check description word count requirement
        desc_word_count = len(self.brief_description.split()) if self.brief_description else 0
        self.meets_description_requirement = 30 <= desc_word_count <= 50
        
        super().save(*args, **kwargs)
    
    @property
    def due_date_datetime(self):
        """Convert due_date_ms to Python datetime object"""
        if self.due_date_ms:
            from datetime import datetime
            return datetime.fromtimestamp(self.due_date_ms / 1000, tz=timezone.utc)
        return None
    
    @property
    def assignee_email_list(self):
        """Return assignee emails as a list"""
        if not self.assignee_emails:
            return []
        return [email.strip() for email in self.assignee_emails.split(',') if email.strip()]
    
    @property
    def assignee_name_list(self):
        """Return assignee names as a list"""
        if not self.assignee_full_names:
            return []
        return [name.strip() for name in self.assignee_full_names.split(',') if name.strip()]
    
    @property
    def is_valid_extraction(self):
        """Check if extraction meets all prompt.md requirements"""
        return (
            self.meets_word_count_requirement and
            self.meets_description_requirement and
            self.priority in dict(self.PRIORITY_CHOICES) and
            self.status in dict(self.STATUS_CHOICES)
        )
    
    def mark_delivered_to_monday(self, monday_item_id):
        """Mark task as successfully delivered to Monday.com"""
        self.monday_item_id = monday_item_id
        self.delivered_to_monday = True
        self.delivery_timestamp = timezone.now()
        self.save(update_fields=['monday_item_id', 'delivered_to_monday', 'delivery_timestamp'])
    
    def to_prompt_format(self):
        """Return task in the exact JSON format specified by prompt.md"""
        return {
            "task_item": self.task_item,
            "assignee_emails": self.assignee_emails,
            "assignee(s)_full_names": self.assignee_full_names,
            "priority": self.priority,
            "brief_description": self.brief_description,
            "due_date": self.due_date_ms,
            "status": self.status
        } 