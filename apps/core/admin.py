"""
Django admin interface for core models
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    Transcript, ActionItem, DailyReport, SystemEvent, 
    ProcessedTaskData, RawTranscriptCache, GeminiProcessedTask
)


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


@admin.register(ProcessedTaskData)
class ProcessedTaskDataAdmin(admin.ModelAdmin):
    """Admin interface for ProcessedTaskData model"""
    
    list_display = [
        'task_item_short', 'priority', 'status', 'assignee_names_short',
        'due_date', 'human_approved', 'delivered_at', 'created_at'
    ]
    list_filter = [
        'priority', 'status', 'human_approved', 'delivery_status',
        'due_date', 'created_at'
    ]
    search_fields = [
        'task_item', 'assignee_emails', 'assignee_full_names', 
        'brief_description'
    ]
    readonly_fields = [
        'id', 'extraction_confidence', 'created_at', 'updated_at',
        'reviewed_at', 'delivered_at'
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': (
                'task_item', 'assignee_emails', 'assignee_full_names',
                'priority', 'brief_description', 'due_date', 'status'
            )
        }),
        ('Processing Metadata', {
            'fields': ('extraction_confidence', 'source_sentences', 'processing_notes'),
            'classes': ('collapse',)
        }),
        ('Human Review', {
            'fields': (
                'human_approved', 'reviewed_by', 'reviewed_at', 'review_notes'
            )
        }),
        ('Monday.com Delivery', {
            'fields': (
                'monday_item_id', 'delivered_at', 'delivery_status', 'delivery_errors'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'transcript', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_for_delivery', 'mark_as_delivered']
    
    def task_item_short(self, obj):
        """Truncated task item for list display"""
        return obj.task_item[:60] + '...' if len(obj.task_item) > 60 else obj.task_item
    task_item_short.short_description = 'Task Item'
    
    def assignee_names_short(self, obj):
        """Truncated assignee names for list display"""
        return obj.assignee_full_names[:30] + '...' if len(obj.assignee_full_names) > 30 else obj.assignee_full_names
    assignee_names_short.short_description = 'Assignees'
    
    def approve_for_delivery(self, request, queryset):
        """Bulk approve tasks for delivery"""
        count = 0
        for task in queryset.filter(human_approved=False):
            task.approve_for_delivery(user=request.user, notes="Bulk approved via admin")
            count += 1
        self.message_user(request, f"Approved {count} tasks for delivery.")
    approve_for_delivery.short_description = "Approve selected tasks for delivery"
    
    def mark_as_delivered(self, request, queryset):
        """Bulk mark tasks as delivered"""
        count = 0
        for task in queryset.filter(delivery_status='pending'):
            task.mark_delivered()
            count += 1
        self.message_user(request, f"Marked {count} tasks as delivered.")
    mark_as_delivered.short_description = "Mark selected tasks as delivered"


@admin.register(RawTranscriptCache)
class RawTranscriptCacheAdmin(admin.ModelAdmin):
    """Admin interface for RawTranscriptCache model"""
    
    list_display = [
        'fireflies_id', 'meeting_title_short', 'meeting_date',
        'participant_count', 'duration_minutes', 'processed',
        'is_valid', 'cache_timestamp'
    ]
    list_filter = [
        'processed', 'is_valid', 'meeting_date', 'cache_timestamp'
    ]
    search_fields = ['fireflies_id', 'meeting_title']
    readonly_fields = [
        'id', 'data_hash', 'cache_timestamp', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Cache Information', {
            'fields': (
                'fireflies_id', 'meeting_title', 'meeting_date',
                'participant_count', 'duration_minutes'
            )
        }),
        ('Processing Status', {
            'fields': ('processed', 'processing_errors')
        }),
        ('Cache Validation', {
            'fields': ('is_valid', 'data_hash'),
            'classes': ('collapse',)
        }),
        ('Raw Data', {
            'fields': ('raw_fireflies_data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'cache_timestamp', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['validate_integrity', 'mark_as_processed']
    
    def meeting_title_short(self, obj):
        """Truncated meeting title for list display"""
        return obj.meeting_title[:40] + '...' if len(obj.meeting_title) > 40 else obj.meeting_title
    meeting_title_short.short_description = 'Meeting Title'
    
    def validate_integrity(self, request, queryset):
        """Validate data integrity for selected transcripts"""
        valid_count = 0
        invalid_count = 0
        for transcript in queryset:
            if transcript.validate_integrity():
                valid_count += 1
            else:
                invalid_count += 1
                transcript.is_valid = False
                transcript.save()
        
        self.message_user(request, f"Validated {valid_count} transcripts. Found {invalid_count} invalid.")
    validate_integrity.short_description = "Validate data integrity"
    
    def mark_as_processed(self, request, queryset):
        """Mark selected transcripts as processed"""
        count = queryset.filter(processed=False).update(processed=True)
        self.message_user(request, f"Marked {count} transcripts as processed.")
    mark_as_processed.short_description = "Mark as processed"
    
    def has_add_permission(self, request):
        # Raw cache should be populated by the system, not manually
        return False


@admin.register(GeminiProcessedTask)
class GeminiProcessedTaskAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for GeminiProcessedTask model
    Mirrors Monday.com columns and provides comprehensive task management
    """
    
    # List display mirroring Monday.com columns
    list_display = [
        'task_name_display',           # Monday.com: item_name
        'team_member_display',         # Monday.com: text_mkr7jgkp
        'priority_display',            # Monday.com: status_1
        'status_display',              # Monday.com: status
        'date_expected_display',       # Monday.com: date_mkr7ymmh
        'meeting_source',              # Categorization
        'auto_push_status',            # Auto-push indicator
        'monday_delivery_status'       # Delivery status
    ]
    
    # Filters for easy categorization and management
    list_filter = [
        'raw_transcript__meeting_title',  # Meeting categorization (simple filter)
        'priority',                    # Monday.com priority
        'status',                      # Monday.com status
        'delivered_to_monday',         # Delivery status
        'processing_timestamp',        # When processed
        'raw_transcript__meeting_date', # Meeting date (simple filter)
        'meets_word_count_requirement',
        'meets_description_requirement',
        'approval_status',             # Auto-push approval status
        'auto_push_enabled',           # Auto-push enabled
        'auto_mute_enabled'            # Auto-mute enabled
    ]
    
    # Search across Monday.com relevant fields
    search_fields = [
        'task_item',                   # Task name
        'assignee_full_names',         # Team member
        'assignee_emails',             # Email
        'brief_description',           # Description
        'raw_transcript__meeting_title', # Meeting
        'monday_item_id'               # Monday.com ID
    ]
    
    # Ordering by meeting date (newest first) then by extraction order
    ordering = ['-raw_transcript__meeting_date', 'extraction_order']
    
    # Readonly fields (auto-calculated and Monday.com assigned)
    readonly_fields = [
        'id', 'processing_timestamp', 'meets_word_count_requirement', 
        'meets_description_requirement', 'delivery_timestamp', 
        'created_at', 'updated_at', 'due_date_datetime',
        'monday_item_id'  # Monday.com assigns this automatically
    ]
    
    # Fieldsets organized like Monday.com columns
    fieldsets = (
        ('📋 Monday.com Task Details', {
            'fields': (
                ('task_item',),                    # Task Name
                ('assignee_full_names', 'assignee_emails'),  # Team Member + Email
                ('priority', 'status'),            # Priority + Status
                ('brief_description',),            # Description
                ('due_date_ms', 'due_date_datetime'),  # Date Expected
            ),
            'description': 'Core task fields that mirror Monday.com columns. All editable.'
        }),
        ('🎯 Auto-Push Settings', {
            'fields': (
                ('auto_push_enabled', 'auto_mute_enabled'),
                ('approval_status', 'rejection_reason'),
            ),
            'description': 'Control automatic pushing to Monday.com'
        }),
        ('📊 Meeting Source', {
            'fields': (
                'raw_transcript',
                ('extraction_order', 'extraction_confidence'),
                'gemini_model_version'
            ),
            'description': 'Source meeting and processing details'
        }),
        ('✅ Quality Validation', {
            'fields': (
                'meets_word_count_requirement', 
                'meets_description_requirement'
            ),
            'description': 'Automatic quality checks (read-only)'
        }),
        ('🚀 Monday.com Delivery', {
            'fields': (
                'monday_item_id', 
                'delivered_to_monday', 
                'delivery_timestamp',
                'delivery_errors'
            ),
            'description': 'Monday.com integration status'
        }),
        ('🔧 Technical Details', {
            'fields': (
                'source_sentences',
                'raw_gemini_response'
            ),
            'classes': ('collapse',),
            'description': 'Technical processing details (collapsible)'
        }),
        ('📅 Timestamps', {
            'fields': (
                'processing_timestamp', 
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',),
            'description': 'System timestamps (read-only)'
        }),
    )
    
    # Comprehensive bulk actions
    actions = [
        'approve_for_auto_push',       # Approve for auto-push
        'enable_auto_push',            # Enable auto-push
        'disable_auto_push',           # Disable auto-push (mute)
        'reject_tasks',                # Reject tasks
        'push_to_monday_now',          # Immediate push to Monday.com
        'mark_as_delivered',           # Mark as delivered
        'validate_requirements',       # Validate quality
        'export_to_monday_format',     # Export in Monday.com format
        'categorize_by_meeting'        # Group by meeting
    ]
    
    # Custom display methods for Monday.com columns
    def task_name_display(self, obj):
        """Task Name (Monday.com: item_name)"""
        name = obj.task_item[:50] + '...' if len(obj.task_item) > 50 else obj.task_item
        
        # Add quality indicators
        indicators = []
        if not obj.meets_word_count_requirement:
            indicators.append('📝')  # Word count issue
        if not obj.meets_description_requirement:
            indicators.append('📄')  # Description issue
        if obj.delivered_to_monday:
            indicators.append('✅')  # Delivered
        elif getattr(obj, 'approval_status', 'pending') == 'approved':
            indicators.append('🚀')  # Ready for delivery
        elif getattr(obj, 'approval_status', 'pending') == 'rejected':
            indicators.append('❌')  # Rejected
        
        indicator_str = ''.join(indicators)
        return f"{indicator_str} {name}" if indicators else name
    task_name_display.short_description = 'Task Name'
    task_name_display.admin_order_field = 'task_item'
    
    def team_member_display(self, obj):
        """Team Member (Monday.com: text_mkr7jgkp)"""
        names = obj.assignee_full_names[:30] + '...' if len(obj.assignee_full_names) > 30 else obj.assignee_full_names
        emails = obj.assignee_emails[:25] + '...' if len(obj.assignee_emails) > 25 else obj.assignee_emails
        return f"{names}\n📧 {emails}" if emails else names
    team_member_display.short_description = 'Team Member'
    team_member_display.admin_order_field = 'assignee_full_names'
    
    def priority_display(self, obj):
        """Priority (Monday.com: status_1)"""
        priority_colors = {
            'High': '🔴 High',
            'Medium': '🟡 Medium', 
            'Low': '🟢 Low'
        }
        return priority_colors.get(obj.priority, f"⚪ {obj.priority}")
    priority_display.short_description = 'Priority'
    priority_display.admin_order_field = 'priority'
    
    def status_display(self, obj):
        """Status (Monday.com: status)"""
        status_icons = {
            'To Do': '📋 To Do',
            'Stuck': '🚫 Stuck',
            'Working on it': '⚡ Working on it',
            'Waiting for review': '👀 Waiting for review',
            'Approved': '✅ Approved',
            'Done': '🎉 Done'
        }
        return status_icons.get(obj.status, f"❓ {obj.status}")
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def date_expected_display(self, obj):
        """Date Expected (Monday.com: date_mkr7ymmh)"""
        if obj.due_date_datetime:
            return obj.due_date_datetime.strftime('%Y-%m-%d %H:%M UTC')
        return '📅 No due date'
    date_expected_display.short_description = 'Date Expected'
    date_expected_display.admin_order_field = 'due_date_ms'
    
    def meeting_source(self, obj):
        """Meeting Source (Categorization)"""
        meeting = obj.raw_transcript
        date_str = meeting.meeting_date.strftime('%m/%d')
        return f"📅 {date_str} - {meeting.meeting_title[:25]}{'...' if len(meeting.meeting_title) > 25 else ''}"
    meeting_source.short_description = 'Meeting Source'
    meeting_source.admin_order_field = 'raw_transcript__meeting_date'
    
    def auto_push_status(self, obj):
        """Auto-Push Status"""
        if getattr(obj, 'auto_push_enabled', False):
            if getattr(obj, 'approval_status', 'pending') == 'approved':
                return '🚀 Auto-Push Ready'
            elif getattr(obj, 'approval_status', 'pending') == 'rejected':
                return '❌ Rejected'
            else:
                return '⏳ Pending Approval'
        elif getattr(obj, 'auto_mute_enabled', False):
            return '🔇 Muted'
        else:
            return '⚪ Manual'
    auto_push_status.short_description = 'Auto-Push'
    
    def monday_delivery_status(self, obj):
        """Monday.com Delivery Status"""
        if obj.delivered_to_monday and obj.monday_item_id:
            return f"✅ Delivered\n🆔 {obj.monday_item_id}"
        elif obj.delivery_errors:
            return "❌ Failed"
        elif getattr(obj, 'approval_status', 'pending') == 'approved':
            return "🚀 Ready"
        else:
            return "⏳ Pending"
    monday_delivery_status.short_description = 'Monday.com Status'
    
    # Bulk action implementations
    def approve_for_auto_push(self, request, queryset):
        """Approve selected tasks for auto-push to Monday.com"""
        count = 0
        for task in queryset:
            if hasattr(task, 'approval_status'):
                task.approval_status = 'approved'
            if hasattr(task, 'auto_push_enabled'):
                task.auto_push_enabled = True
            task.save()
            count += 1
        
        self.message_user(request, f"✅ Approved {count} tasks for auto-push to Monday.com")
    approve_for_auto_push.short_description = "✅ Approve for auto-push"
    
    def enable_auto_push(self, request, queryset):
        """Enable auto-push for selected tasks"""
        count = 0
        for task in queryset:
            if hasattr(task, 'auto_push_enabled'):
                task.auto_push_enabled = True
            if hasattr(task, 'auto_mute_enabled'):
                task.auto_mute_enabled = False
            task.save()
            count += 1
        
        self.message_user(request, f"🚀 Enabled auto-push for {count} tasks")
    enable_auto_push.short_description = "🚀 Enable auto-push"
    
    def disable_auto_push(self, request, queryset):
        """Disable auto-push (mute) for selected tasks"""
        count = 0
        for task in queryset:
            if hasattr(task, 'auto_push_enabled'):
                task.auto_push_enabled = False
            if hasattr(task, 'auto_mute_enabled'):
                task.auto_mute_enabled = True
            task.save()
            count += 1
        
        self.message_user(request, f"🔇 Muted auto-push for {count} tasks")
    disable_auto_push.short_description = "🔇 Mute auto-push"
    
    def reject_tasks(self, request, queryset):
        """Reject selected tasks"""
        count = 0
        for task in queryset:
            if hasattr(task, 'approval_status'):
                task.approval_status = 'rejected'
                task.rejection_reason = 'Bulk rejected via admin'
            if hasattr(task, 'auto_push_enabled'):
                task.auto_push_enabled = False
            task.save()
            count += 1
        
        self.message_user(request, f"❌ Rejected {count} tasks")
    reject_tasks.short_description = "❌ Reject tasks"
    
    def push_to_monday_now(self, request, queryset):
        """Immediately push selected tasks to Monday.com"""
        from .monday_client import get_monday_client
        
        monday_client = get_monday_client()
        success_count = 0
        error_count = 0
        
        for task in queryset.filter(delivered_to_monday=False):
            try:
                # Convert to Monday.com format
                task_data = {
                    'task_item': task.task_item,
                    'assignee_emails': task.assignee_emails,
                    'assignee(s)_full_names': task.assignee_full_names,
                    'priority': task.priority,
                    'brief_description': task.brief_description,
                    'due_date': task.due_date_ms,
                    'status': task.status
                }
                
                # Push to Monday.com
                monday_item_id = monday_client.create_task_item(task_data)
                
                if monday_item_id:
                    task.monday_item_id = monday_item_id
                    task.delivered_to_monday = True
                    task.delivery_timestamp = timezone.now()
                    task.delivery_errors = ''
                    task.save()
                    success_count += 1
                else:
                    task.delivery_errors = 'Failed to create Monday.com item'
                    task.save()
                    error_count += 1
                    
            except Exception as e:
                task.delivery_errors = str(e)
                task.save()
                error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"🚀 Successfully pushed {success_count} tasks to Monday.com")
        if error_count > 0:
            self.message_user(request, f"❌ Failed to push {error_count} tasks", level='ERROR')
    push_to_monday_now.short_description = "🚀 Push to Monday.com now"
    
    def mark_as_delivered(self, request, queryset):
        """Mark selected tasks as delivered (manual override)"""
        count = queryset.filter(delivered_to_monday=False).update(
            delivered_to_monday=True,
            delivery_timestamp=timezone.now()
        )
        self.message_user(request, f"✅ Marked {count} tasks as delivered")
    mark_as_delivered.short_description = "✅ Mark as delivered"
    
    def validate_requirements(self, request, queryset):
        """Validate quality requirements for selected tasks"""
        valid_count = 0
        invalid_count = 0
        
        for task in queryset:
            # This will trigger the property calculations
            is_valid = task.is_valid_extraction
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
            task.save()  # Save to update calculated fields
        
        self.message_user(request, f"✅ Validated: {valid_count} valid, {invalid_count} invalid tasks")
    validate_requirements.short_description = "✅ Validate requirements"
    
    def export_to_monday_format(self, request, queryset):
        """Export selected tasks in Monday.com format"""
        import json
        from django.http import HttpResponse
        
        tasks_data = []
        for task in queryset:
            tasks_data.append({
                'task_item': task.task_item,
                'assignee_emails': task.assignee_emails,
                'assignee(s)_full_names': task.assignee_full_names,
                'priority': task.priority,
                'brief_description': task.brief_description,
                'due_date': task.due_date_ms,
                'status': task.status,
                'monday_item_id': task.monday_item_id,
                'meeting_source': task.raw_transcript.meeting_title,
                'meeting_date': task.raw_transcript.meeting_date.isoformat()
            })
        
        response = HttpResponse(
            json.dumps(tasks_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="monday_tasks_export.json"'
        
        self.message_user(request, f"📄 Exported {len(tasks_data)} tasks in Monday.com format")
        return response
    export_to_monday_format.short_description = "📄 Export to Monday.com format"
    
    def categorize_by_meeting(self, request, queryset):
        """Show categorization by meeting"""
        from collections import defaultdict
        
        meetings = defaultdict(int)
        for task in queryset:
            meeting_title = task.raw_transcript.meeting_title
            meetings[meeting_title] += 1
        
        message_parts = ["📊 Tasks by meeting:"]
        for meeting, count in sorted(meetings.items()):
            message_parts.append(f"• {meeting}: {count} tasks")
        
        self.message_user(request, "\n".join(message_parts))
    categorize_by_meeting.short_description = "📊 Categorize by meeting"
    
    # Custom queryset to optimize database queries
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'raw_transcript'
        ).prefetch_related(
            'raw_transcript__gemini_processed_tasks'
        )
    
    # Custom changelist view to group by meetings
    def changelist_view(self, request, extra_context=None):
        """Enhanced changelist with meeting categorization"""
        extra_context = extra_context or {}
        
        # Add meeting statistics
        from collections import defaultdict
        from django.db.models import Count
        
        meeting_stats = (
            self.get_queryset(request)
            .values('raw_transcript__meeting_title', 'raw_transcript__meeting_date')
            .annotate(task_count=Count('id'))
            .order_by('-raw_transcript__meeting_date')
        )
        
        extra_context['meeting_stats'] = meeting_stats
        extra_context['total_tasks'] = self.get_queryset(request).count()
        extra_context['delivered_tasks'] = self.get_queryset(request).filter(delivered_to_monday=True).count()
        extra_context['pending_tasks'] = self.get_queryset(request).filter(delivered_to_monday=False).count()
        
        return super().changelist_view(request, extra_context)
    
    # Add custom fields to the model if they don't exist
    def get_form(self, request, obj=None, **kwargs):
        """Add custom fields for auto-push functionality"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add auto-push fields if they don't exist in the model
        if obj and not hasattr(obj, 'auto_push_enabled'):
            obj.auto_push_enabled = False
        if obj and not hasattr(obj, 'auto_mute_enabled'):
            obj.auto_mute_enabled = False
        if obj and not hasattr(obj, 'approval_status'):
            obj.approval_status = 'pending'
        if obj and not hasattr(obj, 'rejection_reason'):
            obj.rejection_reason = ''
            
        return form 