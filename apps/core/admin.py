"""
Django admin interface for core models
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Transcript, ActionItem, DailyReport, SystemEvent


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    """Admin interface for Transcript model"""
    
    list_display = [
        'fireflies_id', 'title', 'meeting_date', 'duration_minutes', 
        'participant_count', 'is_processed', 'created_at'
    ]
    list_filter = ['is_processed', 'meeting_date', 'created_at']
    search_fields = ['fireflies_id', 'title', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'processed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('fireflies_id', 'title', 'meeting_date', 'duration_minutes', 'participant_count')
        }),
        ('Content', {
            'fields': ('content', 'raw_data'),
            'classes': ('collapse',)
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'processed_at', 'processing_errors')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Make fireflies_id readonly for existing objects
        if obj:
            return self.readonly_fields + ['fireflies_id']
        return self.readonly_fields


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    """Admin interface for ActionItem model"""
    
    list_display = [
        'title', 'status', 'priority', 'assignee', 'due_date',
        'confidence_score', 'reviewed_by', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'reviewed_by', 'created_at', 'due_date'
    ]
    search_fields = ['title', 'description', 'assignee']
    readonly_fields = [
        'id', 'confidence_score', 'ai_model_version', 'extraction_metadata',
        'created_at', 'updated_at', 'reviewed_at', 'delivered_at'
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'assignee', 'due_date', 'priority')
        }),
        ('Status & Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('AI Extraction', {
            'fields': ('confidence_score', 'ai_model_version', 'extraction_metadata'),
            'classes': ('collapse',)
        }),
        ('Delivery Tracking', {
            'fields': ('monday_item_id', 'delivered_at', 'delivery_errors', 'auto_push_after'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'transcript', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_tasks', 'reject_tasks']
    
    def approve_tasks(self, request, queryset):
        """Bulk approve tasks"""
        count = 0
        for task in queryset.filter(status='pending'):
            task.approve(user=request.user, notes="Bulk approved via admin")
            count += 1
        self.message_user(request, f"Approved {count} tasks.")
    approve_tasks.short_description = "Approve selected tasks"
    
    def reject_tasks(self, request, queryset):
        """Bulk reject tasks"""
        count = 0
        for task in queryset.filter(status='pending'):
            task.reject(user=request.user, notes="Bulk rejected via admin")
            count += 1
        self.message_user(request, f"Rejected {count} tasks.")
    reject_tasks.short_description = "Reject selected tasks"


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    """Admin interface for DailyReport model"""
    
    list_display = [
        'report_date', 'source_transcripts_count', 'source_tasks_count',
        'generation_duration', 'created_at'
    ]
    list_filter = ['report_date', 'created_at']
    search_fields = ['summary']
    readonly_fields = [
        'id', 'generation_duration', 'source_transcripts_count', 
        'source_tasks_count', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_date', 'summary')
        }),
        ('Insights & Statistics', {
            'fields': ('key_insights', 'task_statistics')
        }),
        ('Generation Metadata', {
            'fields': (
                'ai_model_version', 'generation_duration',
                'source_transcripts_count', 'source_tasks_count'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SystemEvent)
class SystemEventAdmin(admin.ModelAdmin):
    """Admin interface for SystemEvent model"""
    
    list_display = [
        'event_type', 'severity', 'message', 'source_module', 
        'user', 'created_at'
    ]
    list_filter = [
        'event_type', 'severity', 'source_module', 'created_at'
    ]
    search_fields = ['message', 'correlation_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'severity', 'message')
        }),
        ('Details', {
            'fields': ('details', 'correlation_id')
        }),
        ('Source', {
            'fields': ('source_module', 'user')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # System events should be created by the system, not manually
        return False
    
    def has_change_permission(self, request, obj=None):
        # System events should be read-only
        return False 