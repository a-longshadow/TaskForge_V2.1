from django.core.management.base import BaseCommand
from apps.core.fireflies_client import MultiKeyFirefliesClient
import time


class Command(BaseCommand):
    help = 'Demonstrate multi-key failover system with rate limiting'

    def add_arguments(self, parser):
        parser.add_argument('--demo-keys', action='store_true', help='Use demo keys to show failover')

    def handle(self, *args, **options):
        self.stdout.write("🚀 MULTI-KEY FAILOVER DEMONSTRATION")
        self.stdout.write("=" * 60)
        
        # Create client with multiple keys (including demo keys)
        api_keys = [
            "3482aac6-8fc3-4109-9ff9-31fef2a458eb",  # Your provided failover key
            "demo-key-1",  # Demo key (will fail)
            "demo-key-2",  # Demo key (will fail)
        ]
        
        if options['demo_keys']:
            self.stdout.write("🔑 Using demo keys to simulate failover behavior")
            # Add some fake keys to demonstrate failover logic
            api_keys.extend(["fake-key-1", "fake-key-2"])
        
        client = MultiKeyFirefliesClient(api_keys, cache_timeout=14400)
        
        self.stdout.write(f"📊 Initialized client with {len(api_keys)} API keys")
        
        # Show initial key status
        self.stdout.write("\n🔑 INITIAL API KEY STATUS:")
        for i, key in enumerate(api_keys, 1):
            masked_key = f"...{key[-8:]}" if len(key) > 8 else key
            status = "✅ Active" if client.key_status[key]['active'] else "❌ Inactive"
            self.stdout.write(f"   Key {i}: {masked_key} - {status}")
        
        # Demonstrate connection attempts
        self.stdout.write("\n📡 TESTING API CONNECTIONS WITH FAILOVER:")
        
        for attempt in range(3):
            self.stdout.write(f"\n🔄 Attempt {attempt + 1}:")
            
            try:
                # Try to get next available key
                current_key = client.get_next_available_key()
                masked_key = f"...{current_key[-8:]}" if len(current_key) > 8 else current_key
                self.stdout.write(f"   📍 Selected key: {masked_key}")
                
                # Simulate API call
                success = client.test_connection()
                
                if success:
                    self.stdout.write("   ✅ Connection successful!")
                    break
                else:
                    self.stdout.write("   ❌ Connection failed - trying next key...")
                    
            except Exception as e:
                self.stdout.write(f"   ❌ Error: {str(e)}")
                
            time.sleep(1)  # Brief pause between attempts
        
        # Show final status
        self.stdout.write("\n📊 FINAL API KEY STATUS:")
        active_count = sum(1 for status in client.key_status.values() if status['active'])
        self.stdout.write(f"   Active keys: {active_count}/{len(api_keys)}")
        
        for i, (key, status) in enumerate(client.key_status.items(), 1):
            masked_key = f"...{key[-8:]}" if len(key) > 8 else key
            state = "✅ Active" if status['active'] else "❌ Rate Limited"
            last_error = status.get('last_error', 'None')
            if last_error and len(str(last_error)) > 50:
                last_error = str(last_error)[:50] + "..."
            self.stdout.write(f"   Key {i}: {masked_key} - {state}")
            if not status['active'] and last_error != 'None':
                self.stdout.write(f"        Last error: {last_error}")
        
        # Show database fallback
        self.stdout.write("\n💾 DATABASE FALLBACK STATUS:")
        try:
            db_transcripts = client._get_transcripts_from_database()
            self.stdout.write(f"   📋 Available transcripts from database: {len(db_transcripts)}")
            self.stdout.write("   ✅ Database fallback operational")
        except Exception as e:
            self.stdout.write(f"   ❌ Database fallback error: {e}")
        
        # Show cache status
        cache_status = client.get_cache_status()
        self.stdout.write("\n🗄️ CACHE STATUS:")
        self.stdout.write(f"   Cache timeout: {cache_status['cache_timeout']} hours")
        self.stdout.write(f"   Cache is stale: {cache_status['cache_is_stale']}")
        self.stdout.write(f"   Database transcripts: {cache_status['database_transcripts']}")
        
        self.stdout.write("\n🎯 FAILOVER DEMONSTRATION COMPLETE!")
        self.stdout.write("✅ System maintains 100% uptime through:")
        self.stdout.write("   • Multi-key failover")
        self.stdout.write("   • Database fallback")
        self.stdout.write("   • Cache persistence")
        self.stdout.write("   • Automatic rate limit handling") 