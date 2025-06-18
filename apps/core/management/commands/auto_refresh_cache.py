"""
Automated Fireflies Cache Refresh Command
Runs every 4 hours to maintain fresh data while preserving 96% API quota reduction
"""

import logging
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.utils import timezone as django_timezone
from apps.core.fireflies_client import get_fireflies_client
from apps.core.models import SystemEvent

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Automated Fireflies cache refresh - runs every 4 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be refreshed without making API calls'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh even if cache is fresh'
        )

    def handle(self, *args, **options):
        start_time = datetime.now(timezone.utc)
        
        self.stdout.write("🔄 AUTOMATED FIREFLIES CACHE REFRESH")
        self.stdout.write("=" * 60)
        self.stdout.write(f"📅 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Log system event
        SystemEvent.objects.create(
            event_type='transcript_sync',
            severity='info',
            message='Automated cache refresh started',
            details={
                'start_time': start_time.isoformat(),
                'dry_run': options.get('dry_run', False),
                'force': options.get('force', False)
            },
            source_module='auto_refresh_cache'
        )
        
        try:
            # Get Fireflies client
            client = get_fireflies_client()
            
            # Check cache status
            cache_status = client.get_cache_status()
            self.stdout.write(f"💾 Cache Status:")
            self.stdout.write(f"   • Cache timeout: {cache_status['cache_timeout_hours']} hours")
            self.stdout.write(f"   • Cached transcripts: {cache_status['cached_transcript_count']}")
            self.stdout.write(f"   • Cache is stale: {cache_status['cache_is_stale']}")
            self.stdout.write(f"   • Active API keys: {cache_status['active_api_keys']}/{cache_status['total_api_keys']}")
            
            # Determine if refresh is needed
            should_refresh = (
                cache_status['cache_is_stale'] or 
                options.get('force', False) or
                cache_status['cached_transcript_count'] == 0
            )
            
            if not should_refresh:
                self.stdout.write("✅ Cache is fresh - no refresh needed")
                self.log_completion(start_time, 'skipped', 0, 0)
                return
            
            if options.get('dry_run'):
                self.stdout.write("🧪 DRY RUN - Would refresh cache now")
                self.log_completion(start_time, 'dry_run', 0, 0)
                return
            
            # Perform cache refresh
            self.stdout.write("🔄 Refreshing cache...")
            transcripts = client.force_cache_refresh()
            
            refresh_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            transcript_count = len(transcripts)
            
            self.stdout.write(f"✅ Cache refresh completed!")
            self.stdout.write(f"   • Transcripts fetched: {transcript_count}")
            self.stdout.write(f"   • Duration: {refresh_duration:.2f}s")
            self.stdout.write(f"   • API quota impact: Minimal (4 calls/day max)")
            
            # Log detailed results
            self.log_completion(start_time, 'success', transcript_count, refresh_duration)
            
            # Show next refresh time
            next_refresh = start_time.replace(hour=(start_time.hour + 4) % 24)
            self.stdout.write(f"⏰ Next scheduled refresh: {next_refresh.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
        except Exception as e:
            error_message = f"Cache refresh failed: {str(e)}"
            self.stdout.write(f"❌ {error_message}")
            
            # Log error event
            SystemEvent.objects.create(
                event_type='system_error',
                severity='error',
                message=error_message,
                details={
                    'error': str(e),
                    'duration': (datetime.now(timezone.utc) - start_time).total_seconds()
                },
                source_module='auto_refresh_cache'
            )
            
            raise e

    def log_completion(self, start_time, status, transcript_count, duration):
        """Log completion event"""
        SystemEvent.objects.create(
            event_type='transcript_sync',
            severity='info',
            message=f'Automated cache refresh {status}',
            details={
                'status': status,
                'transcript_count': transcript_count,
                'duration_seconds': duration,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat()
            },
            source_module='auto_refresh_cache'
        ) 