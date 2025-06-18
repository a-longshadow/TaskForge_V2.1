"""
Comprehensive TaskForge Pipeline Test
Tests the complete workflow: Fireflies → AI → JSON → Monday.com
"""

import json
import logging
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from apps.core.fireflies_client import get_fireflies_client
from apps.core.gemini_client import get_gemini_client
from apps.core.monday_client import get_monday_client
from apps.core.models import Transcript, ActionItem

logger = logging.getLogger('apps.core.management.commands.test_comprehensive_pipeline')


class Command(BaseCommand):
    help = 'Comprehensive pipeline test: Fireflies → AI → JSON → Monday.com with full validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test without actually pushing to Monday.com',
        )
        parser.add_argument(
            '--save-json',
            action='store_true',
            help='Save intermediate JSON files for inspection',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Limit number of transcripts to process',
        )
        parser.add_argument(
            '--force-today',
            action='store_true',
            help='Force processing of today\'s transcripts even if none found',
        )

    def handle(self, *args, **options):
        """Execute comprehensive pipeline test"""
        self.dry_run = options['dry_run']
        self.save_json = options['save_json']
        self.limit = options['limit']
        self.force_today = options['force_today']
        
        # Initialize stats
        self.stats = {
            'transcripts_fetched': 0,
            'transcripts_processed': 0,
            'action_items_extracted': 0,
            'action_items_delivered': 0,
            'errors': [],
            'breakthroughs': [],
            'api_connections': {},
            'json_files_created': [],
            'monday_items_created': []
        }
        
        self.log_step("🚀 COMPREHENSIVE TASKFORGE PIPELINE TEST")
        self.log_step("=" * 60)
        
        try:
            # Step 1: Test API connections
            self.log_step("📡 Step 1: Testing API Connections")
            fireflies_client, gemini_client, monday_client = self.test_api_connections()
            
            # Step 2: Fetch today's meetings from Fireflies
            self.log_step("📄 Step 2: Fetching Today's Meetings from Fireflies")
            transcripts = self.fetch_todays_meetings(fireflies_client)
            
            # Step 3: Store raw data in clean JSON
            self.log_step("💾 Step 3: Storing Raw Data in Clean JSON")
            if self.save_json:
                self.save_raw_transcripts_json(transcripts)
            
            # Step 4: Extract action items using AI
            self.log_step("🤖 Step 4: Extracting Action Items with AI")
            all_action_items = self.extract_all_action_items(gemini_client, transcripts)
            
            # Step 4b: Package action items chronologically by meeting
            self.log_step("📋 Step 4b: Packaging Action Items Chronologically")
            organized_results = self.organize_action_items_by_meeting(all_action_items)
            if self.save_json:
                self.save_organized_action_items_json(organized_results)
            
            # Step 5: Push results to Monday.com
            self.log_step("📤 Step 5: Pushing Results to Monday.com")
            if not self.dry_run:
                self.deliver_to_monday(monday_client, all_action_items)
            else:
                self.log_info("🧪 DRY RUN: Skipping Monday.com delivery")
            
            # Final results
            self.display_final_results()
            
        except Exception as e:
            self.log_error(f"❌ Pipeline failed: {str(e)}")
            self.stats['errors'].append(f"Pipeline failure: {str(e)}")
            raise

    def test_api_connections(self):
        """Test all API connections"""
        self.log_info("Testing Fireflies API connection...")
        fireflies_client = get_fireflies_client()
        if fireflies_client.test_connection():
            self.log_breakthrough("✅ Fireflies API: Connected successfully")
            self.stats['api_connections']['fireflies'] = 'success'
        else:
            raise Exception("Fireflies API connection failed")
        
        self.log_info("Testing Gemini AI API connection...")
        gemini_client = get_gemini_client()
        if gemini_client.test_connection():
            self.log_breakthrough("✅ Gemini AI API: Connected successfully")
            self.stats['api_connections']['gemini'] = 'success'
        else:
            raise Exception("Gemini AI API connection failed")
        
        self.log_info("Testing Monday.com API connection...")
        monday_client = get_monday_client()
        if monday_client.test_connection():
            self.log_breakthrough("✅ Monday.com API: Connected successfully")
            self.stats['api_connections']['monday'] = 'success'
        else:
            raise Exception("Monday.com API connection failed")
        
        return fireflies_client, gemini_client, monday_client

    def fetch_todays_meetings(self, fireflies_client):
        """Fetch today's meetings with enhanced caching"""
        self.log_step("🔍 STEP 2: Fetch Today's Meetings with Enhanced Caching")
        
        try:
            # Use the enhanced comprehensive transcript fetching with pagination
            self.log_info("Using enhanced Fireflies client with multi-key failover...")
            
            # Check cache status first
            cache_status = fireflies_client.get_cache_status()
            self.log_info(f"Cache status: {cache_status['cached_transcript_count']} transcripts cached")
            self.log_info(f"Cache age: {cache_status['last_sync'] or 'No previous sync'}")
            self.log_info(f"Cache is {'stale' if cache_status['cache_is_stale'] else 'fresh'}")
            self.log_info(f"Active API keys: {cache_status['active_api_keys']}/{cache_status['total_api_keys']}")
            
            # Get comprehensive transcripts (will use cache if fresh, API if stale)
            transcripts = fireflies_client.get_comprehensive_transcripts_with_pagination()
            
            if not transcripts:
                self.log_error("No transcripts retrieved from Fireflies")
                return []
            
            self.log_breakthrough(f"✅ Retrieved {len(transcripts)} comprehensive transcripts")
            
            # Show data volume
            import json
            data_size = len(json.dumps(transcripts, default=str))
            self.log_info(f"📦 Total data volume: {data_size / 1024:.1f} KB")
            
            # Filter for today's meetings
            today_str = date.today().strftime('%Y-%m-%d')
            today_transcripts = []
            
            for transcript in transcripts:
                transcript_date = transcript.get('date', '')
                
                # Handle different date formats
                if isinstance(transcript_date, int):
                    transcript_date = datetime.fromtimestamp(transcript_date / 1000).strftime('%Y-%m-%d')
                elif isinstance(transcript_date, str) and transcript_date:
                    transcript_date = transcript_date[:10]
                
                if transcript_date == today_str:
                    today_transcripts.append(transcript)
            
            if today_transcripts:
                self.log_breakthrough(f"🎯 Found {len(today_transcripts)} meetings for today ({today_str})")
                return today_transcripts
            else:
                self.log_info(f"No meetings for today, using {min(5, len(transcripts))} recent meetings for testing")
                return transcripts[:5]  # Return recent meetings for testing
            
        except Exception as e:
            self.log_error(f"Failed to fetch meetings: {e}")
            
            # Try to get from cache even if stale
            try:
                cache_status = fireflies_client.get_cache_status()
                if cache_status['cached_transcript_count'] > 0:
                    self.log_info("Attempting to use stale cached data...")
                    cached_transcripts = fireflies_client.get_comprehensive_transcripts_with_pagination()
                    if cached_transcripts:
                        self.log_info(f"Using {len(cached_transcripts)} cached transcripts as fallback")
                        return cached_transcripts[:5]
            except Exception as cache_error:
                self.log_error(f"Cache fallback also failed: {cache_error}")
            
            return []

    def save_raw_transcripts_json(self, transcripts):
        """Save raw transcripts to JSON file"""
        try:
            filename = 'comprehensive_test_raw_transcripts.json'
            with open(filename, 'w') as f:
                json.dump(transcripts, f, indent=2, default=str)
            
            self.log_breakthrough(f"💾 Raw transcripts saved to {filename}")
            self.stats['json_files_created'].append(filename)
            
        except Exception as e:
            self.log_error(f"❌ Failed to save raw transcripts: {str(e)}")
            self.stats['errors'].append(f"JSON save error: {str(e)}")

    def extract_all_action_items(self, gemini_client, transcripts):
        """Extract action items from all transcripts and add meeting metadata"""
        all_action_items = []
        
        for i, transcript_data in enumerate(transcripts):
            try:
                title = transcript_data.get('title', f'Meeting {i+1}')
                self.log_info(f"🤖 Processing: {title}")
                
                # Extract action items using AI
                action_items = gemini_client.extract_tasks_from_transcript(transcript_data)
                
                if action_items:
                    # Add meeting metadata to each action item
                    for item in action_items:
                        item['meeting_title'] = title
                        item['meeting_date'] = self.format_transcript_date(transcript_data.get('date'))
                        item['meeting_id'] = transcript_data.get('id', f'meeting_{i+1}')
                        item['transcript_data'] = transcript_data  # Store full transcript for reference
                    
                    self.log_breakthrough(f"✅ Extracted {len(action_items)} action items from '{title}'")
                    all_action_items.extend(action_items)
                    self.stats['action_items_extracted'] += len(action_items)
                else:
                    self.log_info(f"ℹ️ No action items found in '{title}'")
                
                self.stats['transcripts_processed'] += 1
                
            except Exception as e:
                self.log_error(f"❌ Failed to process transcript '{title}': {str(e)}")
                self.stats['errors'].append(f"AI extraction error for '{title}': {str(e)}")
                continue
        
        return all_action_items

    def organize_action_items_by_meeting(self, all_action_items):
        """Organize action items chronologically by meeting with proper categorization"""
        try:
            # Group by meeting using the meeting metadata embedded in action items
            meetings_by_title = {}
            
            for item in all_action_items:
                # Each item is a dictionary from AI extraction, not a Django model
                meeting_title = item.get('meeting_title', 'Unknown Meeting')
                meeting_date = item.get('meeting_date', 'Unknown Date')
                meeting_id = item.get('meeting_id', 'unknown')
                
                # Create a unique key for each meeting
                meeting_key = f"{meeting_title}_{meeting_id}"
                
                if meeting_key not in meetings_by_title:
                    meetings_by_title[meeting_key] = {
                        'meeting_title': meeting_title,
                        'meeting_date': meeting_date,
                        'meeting_id': meeting_id,
                        'action_items': []
                    }
                
                # Normalize the action item data following prompt.md guidelines
                normalized_item = {
                    'task_item': item.get('task_item', 'Untitled Task'),
                    'assignee_emails': self.extract_email_from_assignee(item.get('assignee(s)_full_names', '')),
                    'assignee(s)_full_names': item.get('assignee(s)_full_names', 'Unassigned'),
                    'priority': self.normalize_priority(item.get('priority', 'Medium')),
                    'brief_description': item.get('brief_description', 'No description provided'),
                    'due_date': self.normalize_due_date(item.get('due_date'), meeting_date),
                    'status': self.normalize_status(item.get('status', 'To Do'))
                }
                
                meetings_by_title[meeting_key]['action_items'].append(normalized_item)
            
            # Sort meetings chronologically by date
            def parse_meeting_date(date_str):
                try:
                    if isinstance(date_str, str):
                        return datetime.strptime(date_str[:10], '%Y-%m-%d')
                    return datetime.min
                except:
                    return datetime.min
            
            sorted_meetings = sorted(
                meetings_by_title.values(),
                key=lambda m: parse_meeting_date(m['meeting_date'])
            )
            
            # Create the organized result with proper meeting separation
            organized_results = {
                'total_meetings': len(sorted_meetings),
                'total_action_items': len(all_action_items),
                'generated_at': datetime.utcnow().isoformat(),
                'meetings': []
            }
            
            for meeting_data in sorted_meetings:
                organized_results['meetings'].append({
                    'meeting_key': f"{meeting_data['meeting_title']} ({meeting_data['meeting_date']})",
                    'meeting_title': meeting_data['meeting_title'],
                    'meeting_date': meeting_data['meeting_date'],
                    'meeting_id': meeting_data['meeting_id'],
                    'action_items_count': len(meeting_data['action_items']),
                    'action_items': meeting_data['action_items']
                })
            
            self.log_breakthrough(f"📋 Organized {len(all_action_items)} action items across {len(sorted_meetings)} meetings chronologically")
            
            return organized_results
            
        except Exception as e:
            self.log_error(f"❌ Failed to organize action items: {str(e)}")
            self.stats['errors'].append(f"Organization error: {str(e)}")
            return {'meetings': [], 'total_action_items': len(all_action_items) if all_action_items else 0}
    
    def extract_email_from_assignee(self, assignee):
        """Extract email from assignee string if present"""
        if not assignee:
            return ""
        
        # Look for email patterns
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, assignee)
        return ','.join(emails) if emails else ""
    
    def normalize_priority(self, priority):
        """Normalize priority to realistic values following prompt.md"""
        if not priority:
            return "Medium"
        
        priority_lower = priority.lower()
        if priority_lower in ['high', 'urgent', 'critical', 'blocker']:
            return "High"
        elif priority_lower in ['low', 'minor', 'nice-to-have']:
            return "Low"
        else:
            return "Medium"
    
    def normalize_status(self, status):
        """Normalize status to realistic values following prompt.md"""
        if not status:
            return "To Do"
        
        status_lower = status.lower().replace('_', ' ')
        if 'done' in status_lower or 'complete' in status_lower or 'finished' in status_lower:
            return "Done"
        elif 'progress' in status_lower or 'working' in status_lower:
            return "Working on it"
        elif 'review' in status_lower or 'pending' in status_lower:
            return "Waiting for review"
        elif 'stuck' in status_lower or 'blocked' in status_lower:
            return "Stuck"
        elif 'approved' in status_lower:
            return "Approved"
        else:
            return "To Do"
    
    def normalize_due_date(self, due_date, meeting_date):
        """Normalize due date following prompt.md guidelines - NEVER null"""
        # If we have a valid due date, use it
        if due_date and hasattr(due_date, 'timestamp'):
            return int(due_date.timestamp() * 1000)
        
        # Follow prompt.md: if no due date, derive from meeting date
        if hasattr(meeting_date, 'timestamp'):
            # Add realistic timeframe based on task urgency (2-5 business days)
            from datetime import timedelta
            base_date = meeting_date
            
            # Skip weekends: if meeting is Fri/Sat/Sun, start from next Monday
            weekday = base_date.weekday()  # 0=Monday, 6=Sunday
            if weekday >= 4:  # Friday or later
                days_to_monday = 7 - weekday
                base_date = base_date + timedelta(days=days_to_monday)
            
            # Add 3 business days and set to end of day (17:00)
            due_datetime = base_date + timedelta(days=3)
            due_datetime = due_datetime.replace(hour=17, minute=0, second=0, microsecond=0)
            
            return int(due_datetime.timestamp() * 1000)
        
        # Fallback: use current time + 3 business days
        from datetime import datetime, timedelta
        now = datetime.now()
        fallback_date = now + timedelta(days=3)
        fallback_date = fallback_date.replace(hour=17, minute=0, second=0, microsecond=0)
        return int(fallback_date.timestamp() * 1000)

    def save_organized_action_items_json(self, organized_results):
        """Save organized action items to JSON file"""
        try:
            filename = 'comprehensive_test_organized_action_items.json'
            with open(filename, 'w') as f:
                json.dump(organized_results, f, indent=2, default=str)
            
            self.log_breakthrough(f"💾 Organized action items saved to {filename}")
            self.stats['json_files_created'].append(filename)
            
            # Display summary
            self.log_info(f"📊 JSON Summary:")
            self.log_info(f"  • Total meetings: {organized_results['total_meetings']}")
            self.log_info(f"  • Total action items: {organized_results['total_action_items']}")
            
            for meeting in organized_results['meetings'][:3]:  # Show first 3
                self.log_info(f"  • {meeting['meeting_title']}: {meeting['action_items_count']} items")
            
        except Exception as e:
            self.log_error(f"❌ Failed to save organized action items: {str(e)}")
            self.stats['errors'].append(f"JSON save error: {str(e)}")

    def save_prepared_items_json(self, prepared_items):
        """Save prepared Monday.com items to JSON file for inspection"""
        filename = 'comprehensive_test_prepared_monday_items.json'
        try:
            with open(filename, 'w') as f:
                json.dump(prepared_items, f, indent=2, default=str)
            self.log_breakthrough(f"💾 Prepared Monday.com items saved to {filename}")
            self.stats['json_files_created'].append(filename)
            
            # Display summary
            self.log_step("📊 Prepared Items Summary:")
            self.log_info(f"  • Total prepared items: {len(prepared_items)}")
            
            for item in prepared_items[:3]:  # Show first 3 items
                self.log_info(f"  • Item {item['index']}: {item['monday_data']['name'][:50]}...")
                
        except Exception as e:
            self.log_error(f"❌ Failed to save prepared items: {str(e)}")
            self.stats['errors'].append(f"Prepared items JSON save error: {str(e)}")

    def deliver_to_monday(self, monday_client, all_action_items):
        """Deliver action items to Monday.com with limits and duplicate prevention"""
        if not all_action_items:
            self.log_info("ℹ️ No action items to deliver")
            return
        
        # Apply safety limits
        MAX_ITEMS_TO_DELIVER = 5  # Reduced safety limit for debugging
        items_to_deliver = all_action_items[:MAX_ITEMS_TO_DELIVER]
        
        if len(all_action_items) > MAX_ITEMS_TO_DELIVER:
            self.log_info(f"⚠️ Limiting delivery to {MAX_ITEMS_TO_DELIVER} items (from {len(all_action_items)} total)")
        
        self.log_info(f"📤 Preparing {len(items_to_deliver)} action items for Monday.com...")
        
        # First, prepare all items and save to JSON for inspection
        prepared_items = []
        delivered_names = set()
        
        for i, item in enumerate(items_to_deliver):
            try:
                # Debug raw item (only first 2 to avoid spam)
                if i < 2:
                    self.log_info(f"🔍 Raw item {i+1}: {json.dumps(item, indent=2, default=str)}")
                
                # Extract task name and check for duplicates
                task_name = item.get('task_item', f'Untitled Task {i+1}')
                
                # Skip if we've already delivered this exact task
                if task_name in delivered_names:
                    self.log_info(f"⏭️ Skipping duplicate task: {task_name}")
                    continue
                
                delivered_names.add(task_name)
                
                # Prepare task data for Monday.com with proper field mapping
                task_data = {
                    'name': task_name,
                    'column_values': {
                        'text_mkr7jgkp': item.get('brief_description', 'No description provided'),
                        'status_1': self.map_priority_to_monday_status(item.get('priority', 'Medium')),
                        'status': self.map_status_to_monday(item.get('status', 'To Do')),
                        'long_text': f"Assignee: {item.get('assignee(s)_full_names', 'Unassigned')}\n\nTask: {item.get('task_item', 'No task specified')}\n\nDescription: {item.get('brief_description', 'No description provided')}",
                        'date_mkr7ymmh': self.format_due_date_for_monday(item.get('due_date'))
                    }
                }
                
                prepared_items.append({
                    'index': i + 1,
                    'raw_item': item,
                    'monday_data': task_data
                })
                
                self.log_info(f"✅ Prepared item {i+1}: {task_name[:50]}...")
                
            except Exception as e:
                self.log_error(f"❌ Error preparing item {i+1}: {str(e)}")
                continue
        
        # Save prepared items to JSON file for inspection
        self.save_prepared_items_json(prepared_items)
        
        # Now deliver to Monday.com
        self.log_info(f"📤 Delivering {len(prepared_items)} prepared items to Monday.com...")
        
        for prepared_item in prepared_items:
            try:
                task_data = prepared_item['monday_data']
                
                # Skip if dry run
                if self.dry_run:
                    self.log_info(f"🔍 [DRY RUN] Would create Monday.com item: {task_data['name']}")
                    self.stats['action_items_delivered'] += 1
                    continue
                
                # Create task in Monday.com
                monday_item_id = monday_client.create_task_item(task_data)
                
                if monday_item_id:
                    self.log_info(f"✅ Created Monday.com item: {monday_item_id} - {task_data['name']}")
                    self.stats['monday_items_created'].append({
                        'id': monday_item_id,
                        'name': task_data['name'],
                        'assignee': prepared_item['raw_item'].get('assignee(s)_full_names', 'Unassigned')
                    })
                    self.stats['action_items_delivered'] += 1
                else:
                    self.log_error(f"❌ Failed to create Monday.com item for: {task_data['name']}")
                    self.stats['errors'].append(f"Monday.com creation failed: {task_data['name']}")
                
            except Exception as e:
                self.log_error(f"❌ Failed to deliver task {prepared_item['index']}: {str(e)}")
                self.stats['errors'].append(f"Delivery error for task {prepared_item['index']}: {str(e)}")
                continue

    def display_final_results(self):
        """Display comprehensive final results with safety limits"""
        self.log_step("📊 COMPREHENSIVE PIPELINE TEST RESULTS")
        self.log_step("=" * 60)
        
        # API Connections
        self.log_step("🔗 API Connection Status:")
        for api, status in self.stats['api_connections'].items():
            status_emoji = "✅" if status == 'success' else "❌"
            self.log_info(f"  {status_emoji} {api.title()}: {status}")
        
        # Processing Statistics
        self.log_step("📈 Processing Statistics:")
        self.log_info(f"  📄 Transcripts fetched: {self.stats['transcripts_fetched']}")
        self.log_info(f"  🔄 Transcripts processed: {self.stats['transcripts_processed']}")
        self.log_info(f"  🤖 Action items extracted: {self.stats['action_items_extracted']}")
        self.log_info(f"  📤 Action items delivered: {self.stats['action_items_delivered']}")
        
        # Success Rate
        if self.stats['action_items_extracted'] > 0:
            delivery_rate = (self.stats['action_items_delivered'] / self.stats['action_items_extracted']) * 100
            self.log_info(f"  📊 Delivery success rate: {delivery_rate:.1f}%")
        
        # JSON Files Created
        if self.stats['json_files_created']:
            self.log_step("📄 JSON Files Created:")
            for filename in self.stats['json_files_created']:
                self.log_info(f"  💾 {filename}")
        
        # Monday.com Items Created (with limit)
        if self.stats['monday_items_created']:
            self.log_step("📋 Monday.com Items Created:")
            # Limit display to prevent infinite loops
            items_to_show = self.stats['monday_items_created'][:10]  # Show max 10 items
            for item in items_to_show:
                self.log_info(f"  ✅ ID: {item['id']} - {item['name']}")
                if item['assignee']:
                    self.log_info(f"      👤 Assigned to: {item['assignee']}")
            
            if len(self.stats['monday_items_created']) > 10:
                remaining = len(self.stats['monday_items_created']) - 10
                self.log_info(f"  ... and {remaining} more items")
        
        # Errors (with limit)
        if self.stats['errors']:
            self.log_step("⚠️ Errors Encountered:")
            errors_to_show = self.stats['errors'][:5]  # Show max 5 errors
            for error in errors_to_show:
                self.log_error(f"  ❌ {error}")
            
            if len(self.stats['errors']) > 5:
                remaining = len(self.stats['errors']) - 5
                self.log_error(f"  ... and {remaining} more errors")
        
        # Final Status
        overall_success = (
            len(self.stats['api_connections']) == 3 and
            all(status == 'success' for status in self.stats['api_connections'].values()) and
            self.stats['transcripts_fetched'] > 0 and
            self.stats['action_items_extracted'] > 0 and
            (self.dry_run or self.stats['action_items_delivered'] > 0)
        )
        
        if overall_success:
            self.log_step("🎉 COMPREHENSIVE PIPELINE TEST: SUCCESS!")
        else:
            self.log_step("❌ COMPREHENSIVE PIPELINE TEST: ISSUES DETECTED")
        
        self.log_step("=" * 60)

    def format_transcript_date(self, date_value):
        """Format transcript date for display"""
        if isinstance(date_value, int):
            try:
                return datetime.fromtimestamp(date_value / 1000).strftime('%Y-%m-%d %H:%M')
            except:
                return str(date_value)
        return str(date_value)

    def map_priority_to_monday_status(self, priority):
        """Map AI priority to Monday.com status"""
        priority_map = {
            'High': 'High',
            'Medium': 'Medium', 
            'Low': 'Low',
            'Urgent': 'Critical'
        }
        return priority_map.get(priority, 'Medium')

    def map_status_to_monday(self, status):
        """Map task status to Monday.com status"""
        status_map = {
            'To Do': 'Not Started',
            'Working on it': 'In Progress',
            'Done': 'Done',
            'Stuck': 'Stuck'
        }
        return status_map.get(status, 'Not Started')

    def format_due_date_for_monday(self, due_date):
        """Format due date for Monday.com"""
        if not due_date:
            return None
        
        try:
            if isinstance(due_date, int):
                # Convert timestamp to date
                return datetime.fromtimestamp(due_date / 1000).strftime('%Y-%m-%d')
            elif isinstance(due_date, str):
                # Parse date string
                return datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
        except:
            pass
        
        return None

    def log_step(self, message):
        """Log a major step"""
        self.stdout.write(self.style.SUCCESS(message))
        logger.info(message)

    def log_info(self, message):
        """Log information"""
        self.stdout.write(message)
        logger.info(message)

    def log_error(self, message):
        """Log error"""
        self.stdout.write(self.style.ERROR(message))
        logger.error(message)

    def log_breakthrough(self, message):
        """Log breakthrough/success without adding to stats to prevent loops"""
        self.stdout.write(self.style.SUCCESS(message))
        logger.info(message) 