"""
Django management command for cache operations
Provides comprehensive cache management functionality
"""

import json
from datetime import datetime, timezone
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import caches
from django.conf import settings
from apps.core.cache_manager import get_cache_manager
from apps.core.fireflies_client import get_fireflies_client


class Command(BaseCommand):
    help = 'Manage TaskForge cache system - view stats, clear caches, refresh data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show comprehensive cache statistics'
        )
        parser.add_argument(
            '--clear',
            choices=['all', 'default', 'fireflies', 'gemini', 'sessions'],
            help='Clear specified cache backend'
        )
        parser.add_argument(
            '--refresh-fireflies',
            action='store_true',
            help='Force refresh Fireflies cache from API'
        )
        parser.add_argument(
            '--test-health',
            action='store_true',
            help='Test all cache backend health'
        )
        parser.add_argument(
            '--show-keys',
            choices=['fireflies', 'gemini', 'default', 'sessions'],
            help='Show cache keys for specified backend (if supported)'
        )
        parser.add_argument(
            '--export-stats',
            type=str,
            help='Export cache stats to JSON file'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        
        self.verbose = options.get('verbose', False)
        cache_manager = get_cache_manager()
        
        try:
            if options.get('stats'):
                self.show_cache_stats(cache_manager)
            
            elif options.get('clear'):
                self.clear_cache(cache_manager, options['clear'])
            
            elif options.get('refresh_fireflies'):
                self.refresh_fireflies_cache(cache_manager)
            
            elif options.get('test_health'):
                self.test_cache_health(cache_manager)
            
            elif options.get('show_keys'):
                self.show_cache_keys(options['show_keys'])
            
            elif options.get('export_stats'):
                self.export_cache_stats(cache_manager, options['export_stats'])
            
            else:
                self.stdout.write(
                    self.style.WARNING('No action specified. Use --help for available options.')
                )
                self.show_quick_status(cache_manager)
                
        except Exception as e:
            raise CommandError(f'Cache operation failed: {str(e)}')

    def show_cache_stats(self, cache_manager):
        """Show comprehensive cache statistics"""
        
        self.stdout.write(self.style.SUCCESS('\n🗄️  TASKFORGE CACHE STATISTICS'))
        self.stdout.write('=' * 60)
        
        stats = cache_manager.get_cache_stats()
        
        # Cache Backend Information
        self.stdout.write(self.style.HTTP_INFO('\n📊 CACHE BACKENDS:'))
        for backend_name, backend_info in stats['cache_backends'].items():
            health = stats['cache_health'][backend_name]
            status_icon = '✅' if health['healthy'] else '❌'
            
            self.stdout.write(f"  {status_icon} {backend_name.upper()}:")
            self.stdout.write(f"    Location: {backend_info['location']}")
            self.stdout.write(f"    Timeout: {backend_info['timeout']}s ({backend_info['timeout']/3600:.1f}h)")
            
            if not health['healthy'] and 'error' in health:
                self.stdout.write(self.style.ERROR(f"    Error: {health['error']}"))
        
        # Cache Health Summary
        healthy_count = sum(1 for h in stats['cache_health'].values() if h['healthy'])
        total_count = len(stats['cache_health'])
        
        self.stdout.write(self.style.HTTP_INFO(f'\n🏥 HEALTH SUMMARY:'))
        self.stdout.write(f"  Healthy backends: {healthy_count}/{total_count}")
        
        if healthy_count == total_count:
            self.stdout.write(self.style.SUCCESS("  ✅ All cache backends are healthy"))
        else:
            self.stdout.write(self.style.WARNING("  ⚠️  Some cache backends have issues"))
        
        # Cache Configuration
        self.stdout.write(self.style.HTTP_INFO('\n⚙️  CACHE CONFIGURATION:'))
        
        prefixes = getattr(settings, 'CACHE_KEY_PREFIXES', {})
        if prefixes:
            self.stdout.write("  Key Prefixes:")
            for key, prefix in prefixes.items():
                self.stdout.write(f"    {key}: {prefix}")
        
        timeouts = getattr(settings, 'CACHE_TIMEOUTS', {})
        if timeouts:
            self.stdout.write("  Timeout Settings:")
            for key, timeout in timeouts.items():
                hours = timeout / 3600
                self.stdout.write(f"    {key}: {timeout}s ({hours:.1f}h)")
        
        self.stdout.write(f"\n📅 Generated: {stats['timestamp']}")

    def clear_cache(self, cache_manager, cache_type):
        """Clear specified cache backend"""
        
        self.stdout.write(self.style.WARNING(f'\n🧹 CLEARING CACHE: {cache_type.upper()}'))
        
        if cache_type == 'all':
            results = cache_manager.clear_all_caches()
            
            for backend, success in results.items():
                if success:
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Cleared {backend} cache"))
                else:
                    self.stdout.write(self.style.ERROR(f"  ❌ Failed to clear {backend} cache"))
            
            successful = sum(results.values())
            total = len(results)
            
            if successful == total:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully cleared all {total} cache backends"))
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠️  Cleared {successful}/{total} cache backends"))
        
        else:
            try:
                cache_backend = caches[cache_type]
                cache_backend.clear()
                self.stdout.write(self.style.SUCCESS(f"✅ Successfully cleared {cache_type} cache"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to clear {cache_type} cache: {str(e)}"))

    def refresh_fireflies_cache(self, cache_manager):
        """Force refresh Fireflies cache from API"""
        
        self.stdout.write(self.style.HTTP_INFO('\n🔄 REFRESHING FIREFLIES CACHE'))
        self.stdout.write('=' * 50)
        
        try:
            # Get Fireflies client
            fireflies_client = get_fireflies_client()
            
            self.stdout.write("📡 Connecting to Fireflies API...")
            
            # Force refresh from API
            transcripts = fireflies_client.force_cache_refresh()
            
            if transcripts:
                self.stdout.write(self.style.SUCCESS(f"✅ Successfully fetched {len(transcripts)} transcripts"))
                
                # Cache the results
                success = cache_manager.set_fireflies_transcripts(transcripts)
                
                if success:
                    self.stdout.write(self.style.SUCCESS("✅ Successfully cached transcripts"))
                else:
                    self.stdout.write(self.style.WARNING("⚠️  Fetched transcripts but failed to cache"))
                
                # Show summary
                if self.verbose and transcripts:
                    self.stdout.write(self.style.HTTP_INFO('\n📋 TRANSCRIPT SUMMARY:'))
                    for i, transcript in enumerate(transcripts[:5], 1):
                        title = transcript.get('title', 'Untitled')[:50]
                        date = transcript.get('date', 'Unknown date')
                        self.stdout.write(f"  {i}. {title} ({date})")
                    
                    if len(transcripts) > 5:
                        self.stdout.write(f"  ... and {len(transcripts) - 5} more")
            
            else:
                self.stdout.write(self.style.WARNING("⚠️  No transcripts fetched from API"))
                
                # Check cache status
                cache_status = fireflies_client.get_cache_status()
                self.stdout.write(f"Cache status: {cache_status}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to refresh Fireflies cache: {str(e)}"))

    def test_cache_health(self, cache_manager):
        """Test all cache backend health"""
        
        self.stdout.write(self.style.HTTP_INFO('\n🏥 TESTING CACHE HEALTH'))
        self.stdout.write('=' * 50)
        
        stats = cache_manager.get_cache_stats()
        
        for backend_name, health_info in stats['cache_health'].items():
            self.stdout.write(f"\n🧪 Testing {backend_name.upper()} cache:")
            
            if health_info['healthy']:
                self.stdout.write(self.style.SUCCESS("  ✅ HEALTHY"))
                
                if 'operations' in health_info:
                    ops = ', '.join(health_info['operations'])
                    self.stdout.write(f"  📋 Tested operations: {ops}")
                
                self.stdout.write(f"  🕐 Last tested: {health_info['last_tested']}")
            
            else:
                self.stdout.write(self.style.ERROR("  ❌ UNHEALTHY"))
                
                if 'error' in health_info:
                    self.stdout.write(self.style.ERROR(f"  💥 Error: {health_info['error']}"))
                
                self.stdout.write(f"  🕐 Last tested: {health_info['last_tested']}")

    def show_cache_keys(self, backend_name):
        """Show cache keys for specified backend (if supported)"""
        
        self.stdout.write(self.style.HTTP_INFO(f'\n🔑 CACHE KEYS: {backend_name.upper()}'))
        self.stdout.write('=' * 50)
        
        try:
            cache_backend = caches[backend_name]
            
            # File-based cache can show directory contents
            if hasattr(cache_backend, '_dir'):
                import os
                cache_dir = cache_backend._dir
                
                if os.path.exists(cache_dir):
                    files = os.listdir(cache_dir)
                    
                    if files:
                        self.stdout.write(f"📁 Cache directory: {cache_dir}")
                        self.stdout.write(f"📄 Cache files: {len(files)}")
                        
                        if self.verbose:
                            for file in sorted(files)[:10]:
                                file_path = os.path.join(cache_dir, file)
                                size = os.path.getsize(file_path)
                                modified = datetime.fromtimestamp(
                                    os.path.getmtime(file_path), 
                                    tz=timezone.utc
                                ).strftime('%Y-%m-%d %H:%M:%S UTC')
                                
                                self.stdout.write(f"  📄 {file} ({size} bytes, {modified})")
                            
                            if len(files) > 10:
                                self.stdout.write(f"  ... and {len(files) - 10} more files")
                    else:
                        self.stdout.write("📭 No cache files found")
                else:
                    self.stdout.write(self.style.WARNING("⚠️  Cache directory doesn't exist"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  Cache backend doesn't support key listing"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to show cache keys: {str(e)}"))

    def export_cache_stats(self, cache_manager, filename):
        """Export cache stats to JSON file"""
        
        self.stdout.write(self.style.HTTP_INFO(f'\n💾 EXPORTING CACHE STATS: {filename}'))
        
        try:
            stats = cache_manager.get_cache_stats()
            
            with open(filename, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully exported cache stats to {filename}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to export cache stats: {str(e)}"))

    def show_quick_status(self, cache_manager):
        """Show quick cache status overview"""
        
        self.stdout.write(self.style.HTTP_INFO('\n⚡ QUICK CACHE STATUS'))
        self.stdout.write('=' * 40)
        
        stats = cache_manager.get_cache_stats()
        
        # Health summary
        healthy_backends = [name for name, health in stats['cache_health'].items() if health['healthy']]
        total_backends = len(stats['cache_health'])
        
        if len(healthy_backends) == total_backends:
            self.stdout.write(self.style.SUCCESS(f"✅ All {total_backends} cache backends healthy"))
        else:
            unhealthy = total_backends - len(healthy_backends)
            self.stdout.write(self.style.WARNING(f"⚠️  {len(healthy_backends)}/{total_backends} backends healthy ({unhealthy} issues)"))
        
        # Cache locations
        self.stdout.write(f"📁 Cache root: {settings.BASE_DIR / 'cache'}")
        
        # Quick actions
        self.stdout.write(self.style.HTTP_INFO('\n🔧 AVAILABLE ACTIONS:'))
        self.stdout.write("  --stats              Show detailed statistics")
        self.stdout.write("  --clear all          Clear all caches")
        self.stdout.write("  --refresh-fireflies  Refresh from Fireflies API")
        self.stdout.write("  --test-health        Test cache backend health")
        self.stdout.write("  --help               Show all options") 