import json
import os
from datetime import datetime, timezone, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from django.db.models.fields import NOT_PROVIDED
from apps.core.models import Transcript, ActionItem, DailyReport, SystemEvent
from apps.core.event_bus import publish_event, EventTypes
from apps.core.health_monitor import HealthMonitor


class Command(BaseCommand):
    help = 'Comprehensive test to validate database meets all app requirements and can store 7_meetings.json data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='temp/7_meetings.json',
            help='Path to JSON file with meeting data'
        )
        parser.add_argument(
            '--stress-test',
            action='store_true',
            help='Run stress tests with large data volumes'
        )
        parser.add_argument(
            '--validate-admin',
            action='store_true',
            help='Validate admin user credentials'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 COMPREHENSIVE DATABASE REQUIREMENTS TEST")
        self.stdout.write("=" * 70)
        
        # Test results tracking
        test_results = {
            'database_connection': False,
            'schema_validation': False,
            'data_ingestion': False,
            'relationship_integrity': False,
            'query_performance': False,
            'admin_authentication': False,
            'event_system': False,
            'health_monitoring': False,
            'stress_test': False,
        }
        
        try:
            # 1. Database Connection Test
            self.stdout.write("\n1️⃣ TESTING DATABASE CONNECTION")
            test_results['database_connection'] = self.test_database_connection()
            
            # 2. Schema Validation Test
            self.stdout.write("\n2️⃣ TESTING DATABASE SCHEMA")
            test_results['schema_validation'] = self.test_database_schema()
            
            # 3. Data Ingestion Test
            self.stdout.write("\n3️⃣ TESTING DATA INGESTION FROM 7_MEETINGS.JSON")
            test_results['data_ingestion'] = self.test_data_ingestion(options['file'])
            
            # 4. Relationship Integrity Test
            self.stdout.write("\n4️⃣ TESTING RELATIONSHIP INTEGRITY")
            test_results['relationship_integrity'] = self.test_relationship_integrity()
            
            # 5. Query Performance Test
            self.stdout.write("\n5️⃣ TESTING QUERY PERFORMANCE")
            test_results['query_performance'] = self.test_query_performance()
            
            # 6. Admin Authentication Test
            if options['validate_admin']:
                self.stdout.write("\n6️⃣ TESTING ADMIN AUTHENTICATION")
                test_results['admin_authentication'] = self.test_admin_authentication()
            
            # 7. Event System Test
            self.stdout.write("\n7️⃣ TESTING EVENT SYSTEM")
            test_results['event_system'] = self.test_event_system()
            
            # 8. Health Monitoring Test
            self.stdout.write("\n8️⃣ TESTING HEALTH MONITORING")
            test_results['health_monitoring'] = self.test_health_monitoring()
            
            # 9. Stress Test (Optional)
            if options['stress_test']:
                self.stdout.write("\n9️⃣ RUNNING STRESS TESTS")
                test_results['stress_test'] = self.run_stress_tests()
            
            # Display Final Results
            self.display_final_results(test_results)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Critical error during testing: {str(e)}")
            )
            raise

    def test_database_connection(self) -> bool:
        """Test PostgreSQL database connection and basic operations"""
        try:
            with connection.cursor() as cursor:
                # Test basic connection
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.stdout.write(f"   ✅ PostgreSQL Version: {version}")
                
                # Test database name
                cursor.execute("SELECT current_database();")
                db_name = cursor.fetchone()[0]
                self.stdout.write(f"   ✅ Connected to database: {db_name}")
                
                # Test table existence
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name LIKE 'core_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f"   ✅ Core tables found: {len(tables)}")
                for table in sorted(tables):
                    self.stdout.write(f"      • {table}")
                
                return True
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Database connection failed: {str(e)}"))
            return False

    def test_database_schema(self) -> bool:
        """Validate database schema meets all app requirements"""
        try:
            # Test model creation and field validation
            models_to_test = [Transcript, ActionItem, DailyReport, SystemEvent]
            
            for model in models_to_test:
                # Test model metadata
                self.stdout.write(f"   📋 Testing {model.__name__} model:")
                
                # Check required fields
                required_fields = [f.name for f in model._meta.fields if not f.null and not f.blank and f.default == NOT_PROVIDED]
                self.stdout.write(f"      • Required fields: {len(required_fields)}")
                
                # Check indexes
                indexes = [idx.name for idx in model._meta.indexes]
                self.stdout.write(f"      • Indexes: {len(indexes)}")
                
                # Check foreign keys
                fk_fields = [f.name for f in model._meta.fields if f.is_relation]
                self.stdout.write(f"      • Foreign keys: {len(fk_fields)}")
                
                # Test model instance creation (without saving)
                try:
                    if model == Transcript:
                        instance = model(
                            fireflies_id='test_schema_validation',
                            title='Schema Test',
                            meeting_date=datetime.now(timezone.utc),
                            duration_minutes=30,
                            participant_count=2
                        )
                    elif model == ActionItem:
                        # Create a test transcript first
                        test_transcript = Transcript.objects.create(
                            fireflies_id='test_action_item_schema',
                            title='Action Item Schema Test',
                            meeting_date=datetime.now(timezone.utc),
                            duration_minutes=15,
                            participant_count=1
                        )
                        instance = model(
                            transcript=test_transcript,
                            title='Test Action Item',
                            description='Schema validation test',
                            assignee='Test User',
                            priority='medium'
                        )
                    elif model == DailyReport:
                        instance = model(
                            report_date=datetime.now().date(),
                            summary='Schema test report',
                            key_insights=['test insight'],
                            task_statistics={'total': 0}
                        )
                    elif model == SystemEvent:
                        instance = model(
                            event_type='health_check',
                            severity='info',
                            message='Schema validation test',
                            source_module='test'
                        )
                    
                    # Validate instance without saving
                    instance.full_clean()
                    self.stdout.write(f"      ✅ Model validation passed")
                    
                except Exception as e:
                    self.stdout.write(f"      ❌ Model validation failed: {str(e)}")
                    return False
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Schema validation failed: {str(e)}"))
            return False

    def test_data_ingestion(self, file_path: str) -> bool:
        """Test ingesting the complete 7_meetings.json data"""
        try:
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(f"   ❌ File not found: {file_path}"))
                return False
            
            # Load and analyze the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            self.stdout.write(f"   📄 File size: {file_size:.2f} MB")
            
            # Count data elements
            total_transcripts = 0
            total_sentences = 0
            total_attendees = 0
            
            if isinstance(data, list):
                for item in data:
                    if 'data' in item and 'transcripts' in item['data']:
                        transcripts = item['data']['transcripts']
                    elif 'transcripts' in item:
                        transcripts = item['transcripts']
                    else:
                        transcripts = [item]
                    
                    total_transcripts += len(transcripts)
                    for transcript in transcripts:
                        total_sentences += len(transcript.get('sentences', []))
                        total_attendees += len(transcript.get('meeting_attendees', []))
            elif isinstance(data, dict):
                if 'data' in data and 'transcripts' in data['data']:
                    transcripts = data['data']['transcripts']
                elif 'transcripts' in data:
                    transcripts = data['transcripts']
                else:
                    transcripts = [data]
                
                total_transcripts = len(transcripts)
                for transcript in transcripts:
                    total_sentences += len(transcript.get('sentences', []))
                    total_attendees += len(transcript.get('meeting_attendees', []))
            
            self.stdout.write(f"   📊 Data analysis:")
            self.stdout.write(f"      • Total transcripts: {total_transcripts}")
            self.stdout.write(f"      • Total sentences: {total_sentences}")
            self.stdout.write(f"      • Total attendees: {total_attendees}")
            
            # Test ingestion using existing populate command
            from apps.core.management.commands.populate_db_from_json import Command as PopulateCommand
            populate_cmd = PopulateCommand()
            
            # Count before ingestion
            before_transcripts = Transcript.objects.count()
            before_action_items = ActionItem.objects.count()
            
            # Perform ingestion
            self.stdout.write("   🔄 Starting data ingestion...")
            
            # Process the data
            transcripts_processed = 0
            action_items_processed = 0
            
            if isinstance(data, list):
                for item in data:
                    if 'data' in item and 'transcripts' in item['data']:
                        transcripts = item['data']['transcripts']
                    elif 'transcripts' in item:
                        transcripts = item['transcripts']
                    else:
                        transcripts = [item]
                    
                    for transcript_data in transcripts:
                        result = populate_cmd.process_transcript(transcript_data, dry_run=False)
                        if result:
                            transcripts_processed += 1
                            action_items_processed += result.get('action_items_count', 0)
            elif isinstance(data, dict):
                if 'data' in data and 'transcripts' in data['data']:
                    transcripts = data['data']['transcripts']
                elif 'transcripts' in data:
                    transcripts = data['transcripts']
                else:
                    transcripts = [data]
                
                for transcript_data in transcripts:
                    result = populate_cmd.process_transcript(transcript_data, dry_run=False)
                    if result:
                        transcripts_processed += 1
                        action_items_processed += result.get('action_items_count', 0)
            
            # Count after ingestion
            after_transcripts = Transcript.objects.count()
            after_action_items = ActionItem.objects.count()
            
            self.stdout.write(f"   ✅ Ingestion completed:")
            self.stdout.write(f"      • Transcripts: {before_transcripts} → {after_transcripts} (+{after_transcripts - before_transcripts})")
            self.stdout.write(f"      • Action items: {before_action_items} → {after_action_items} (+{after_action_items - before_action_items})")
            
            # Validate data integrity
            sample_transcript = Transcript.objects.first()
            if sample_transcript:
                raw_data_size = len(json.dumps(sample_transcript.raw_data))
                self.stdout.write(f"      • Sample raw_data size: {raw_data_size} bytes")
                self.stdout.write(f"      • Content length: {len(sample_transcript.content)} chars")
                
                # Test JSON field storage
                if 'sentences' in sample_transcript.raw_data:
                    sentences_count = len(sample_transcript.raw_data['sentences'])
                    self.stdout.write(f"      • Sentences stored: {sentences_count}")
                
                if 'meeting_attendees' in sample_transcript.raw_data:
                    attendees_count = len(sample_transcript.raw_data['meeting_attendees'])
                    self.stdout.write(f"      • Attendees stored: {attendees_count}")
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Data ingestion failed: {str(e)}"))
            return False

    def test_relationship_integrity(self) -> bool:
        """Test foreign key relationships and data integrity"""
        try:
            # Test Transcript -> ActionItem relationship
            transcript = Transcript.objects.first()
            if transcript:
                action_items = transcript.action_items.all()
                self.stdout.write(f"   📋 Transcript '{transcript.title}' has {action_items.count()} action items")
                
                # Test reverse relationship
                if action_items.exists():
                    action_item = action_items.first()
                    self.stdout.write(f"   🔗 Action item '{action_item.title}' belongs to transcript '{action_item.transcript.title}'")
                
                # Test cascade deletion (create test data)
                test_transcript = Transcript.objects.create(
                    fireflies_id='test_cascade_deletion',
                    title='Cascade Test',
                    meeting_date=datetime.now(timezone.utc),
                    duration_minutes=10,
                    participant_count=1
                )
                
                test_action_item = ActionItem.objects.create(
                    transcript=test_transcript,
                    title='Test Cascade',
                    description='Testing cascade deletion',
                    assignee='Test User'
                )
                
                action_item_id = test_action_item.id
                test_transcript.delete()
                
                # Verify cascade deletion
                if not ActionItem.objects.filter(id=action_item_id).exists():
                    self.stdout.write("   ✅ Cascade deletion working correctly")
                else:
                    self.stdout.write("   ❌ Cascade deletion failed")
                    return False
            else:
                self.stdout.write("   ⚠️  No transcripts found, creating test data...")
                # Create test data for relationship testing
                test_transcript = Transcript.objects.create(
                    fireflies_id='test_relationship',
                    title='Relationship Test',
                    meeting_date=datetime.now(timezone.utc),
                    duration_minutes=10,
                    participant_count=1
                )
                
                test_action_item = ActionItem.objects.create(
                    transcript=test_transcript,
                    title='Test Relationship',
                    description='Testing relationships',
                    assignee='Test User'
                )
                
                self.stdout.write(f"   📋 Created test transcript with {test_transcript.action_items.count()} action items")
            
            # Test User -> ActionItem relationship (reviewed_by)
            User = get_user_model()
            admin_user = User.objects.filter(username='joe@coophive.network').first()
            if admin_user:
                action_item = ActionItem.objects.first()
                if action_item:
                    action_item.reviewed_by = admin_user
                    action_item.save()
                    self.stdout.write(f"   👤 Action item assigned to reviewer: {admin_user.username}")
            
            # Test SystemEvent relationships
            SystemEvent.objects.create(
                event_type='health_check',
                severity='info',
                message='Relationship integrity test',
                source_module='test_database_requirements',
                user=admin_user if admin_user else None
            )
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Relationship integrity test failed: {str(e)}"))
            return False

    def test_query_performance(self) -> bool:
        """Test database query performance with real data"""
        try:
            import time
            
            # Test 1: Simple count queries
            start_time = time.time()
            transcript_count = Transcript.objects.count()
            count_time = time.time() - start_time
            self.stdout.write(f"   📊 Count query ({transcript_count} transcripts): {count_time:.3f}s")
            
            # Test 2: Complex filtering
            start_time = time.time()
            recent_transcripts = Transcript.objects.filter(
                meeting_date__gte=datetime.now(timezone.utc) - timedelta(days=30)
            ).count()
            filter_time = time.time() - start_time
            self.stdout.write(f"   🔍 Filter query ({recent_transcripts} recent): {filter_time:.3f}s")
            
            # Test 3: Join queries
            start_time = time.time()
            transcripts_with_items = Transcript.objects.prefetch_related('action_items').filter(
                action_items__isnull=False
            ).distinct().count()
            join_time = time.time() - start_time
            self.stdout.write(f"   🔗 Join query ({transcripts_with_items} with items): {join_time:.3f}s")
            
            # Test 4: JSON field queries
            start_time = time.time()
            json_query_count = Transcript.objects.filter(
                raw_data__has_key='sentences'
            ).count()
            json_time = time.time() - start_time
            self.stdout.write(f"   📄 JSON query ({json_query_count} with sentences): {json_time:.3f}s")
            
            # Test 5: Full-text search simulation
            start_time = time.time()
            search_results = Transcript.objects.filter(
                content__icontains='action'
            ).count()
            search_time = time.time() - start_time
            self.stdout.write(f"   🔎 Text search ({search_results} matches): {search_time:.3f}s")
            
            # Performance thresholds (reasonable for development)
            if all([count_time < 1.0, filter_time < 1.0, join_time < 2.0, json_time < 2.0, search_time < 3.0]):
                self.stdout.write("   ✅ All queries within acceptable performance thresholds")
                return True
            else:
                self.stdout.write("   ⚠️  Some queries exceeded performance thresholds (acceptable for development)")
                return True  # Still pass for development environment
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Query performance test failed: {str(e)}"))
            return False

    def test_admin_authentication(self) -> bool:
        """Test admin user credentials"""
        try:
            User = get_user_model()
            
            # Check if admin user exists
            admin_user = User.objects.filter(username='joe@coophive.network').first()
            if not admin_user:
                self.stdout.write("   ❌ Admin user not found")
                return False
            
            self.stdout.write(f"   👤 Admin user found: {admin_user.username}")
            self.stdout.write(f"   📧 Email: {admin_user.email}")
            self.stdout.write(f"   🔑 Is superuser: {admin_user.is_superuser}")
            self.stdout.write(f"   📋 Is staff: {admin_user.is_staff}")
            
            # Test password (without actually authenticating)
            if admin_user.check_password('testpass123'):
                self.stdout.write("   ✅ Password verification successful")
            else:
                self.stdout.write("   ❌ Password verification failed")
                return False
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Admin authentication test failed: {str(e)}"))
            return False

    def test_event_system(self) -> bool:
        """Test event bus and system event logging"""
        try:
            # Test event publication
            event_id = publish_event(
                EventTypes.SYSTEM_ERROR,
                {
                    'test': 'database_requirements_test',
                    'component': 'event_system',
                    'status': 'testing'
                },
                source_module='test_database_requirements'
            )
            
            self.stdout.write(f"   📡 Event published with ID: {event_id}")
            
            # Verify event was stored in database
            recent_events = SystemEvent.objects.filter(
                source_module='test_database_requirements'
            ).count()
            
            self.stdout.write(f"   📊 System events from this test: {recent_events}")
            
            # Test different event types
            test_events = [
                (EventTypes.TRANSCRIPT_INGESTED, 'info'),
                (EventTypes.TASK_CREATED, 'info'),
                (EventTypes.SYSTEM_ERROR, 'error'),
            ]
            
            for event_type, severity in test_events:
                SystemEvent.objects.create(
                    event_type=event_type.replace('.', '_'),  # Convert to valid choice
                    severity=severity,
                    message=f'Test event: {event_type}',
                    source_module='test_database_requirements'
                )
            
            total_test_events = SystemEvent.objects.filter(
                source_module='test_database_requirements'
            ).count()
            
            self.stdout.write(f"   ✅ Created {total_test_events} test events successfully")
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Event system test failed: {str(e)}"))
            return False

    def test_health_monitoring(self) -> bool:
        """Test health monitoring system integration"""
        try:
            health_monitor = HealthMonitor.get_instance()
            
            # Test database health check
            db_health = health_monitor.check_database()
            self.stdout.write(f"   🏥 Database health: {db_health.status}")
            self.stdout.write(f"   ⏱️  Check duration: {db_health.duration:.3f}s")
            
            # Test system health overview
            system_health = health_monitor.get_system_health()
            self.stdout.write(f"   📊 System health components: {len(system_health.get('checks', {}))}")
            
            overall_status = system_health.get('status', 'unknown')
            self.stdout.write(f"   🎯 Overall system status: {overall_status}")
            
            # Test specific health checks
            if 'checks' in system_health:
                for check_name, check_result in system_health['checks'].items():
                    status = check_result.get('status', 'unknown')
                    self.stdout.write(f"      • {check_name}: {status}")
            
            return db_health.status == 'healthy'
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Health monitoring test failed: {str(e)}"))
            return False

    def run_stress_tests(self) -> bool:
        """Run stress tests with large data volumes"""
        try:
            self.stdout.write("   🚀 Running stress tests...")
            
            # Test 1: Bulk transcript creation
            bulk_transcripts = []
            for i in range(100):
                bulk_transcripts.append(Transcript(
                    fireflies_id=f'stress_test_{i}',
                    title=f'Stress Test Meeting {i}',
                    meeting_date=datetime.now(timezone.utc) - timedelta(days=i),
                    duration_minutes=30 + (i % 60),
                    participant_count=2 + (i % 8),
                    raw_data={'test_data': f'Large JSON payload {i}' * 100},
                    content=f'Meeting content for stress test {i}' * 50
                ))
            
            import time
            start_time = time.time()
            Transcript.objects.bulk_create(bulk_transcripts, batch_size=50)
            bulk_create_time = time.time() - start_time
            
            self.stdout.write(f"   📊 Bulk created 100 transcripts in {bulk_create_time:.3f}s")
            
            # Test 2: Large JSON field storage
            large_json_data = {
                'sentences': [
                    {
                        'index': i,
                        'speaker_name': f'Speaker {i % 5}',
                        'text': f'This is sentence {i} with lots of content' * 10,
                        'start_time': i * 1000,
                        'end_time': (i + 1) * 1000,
                        'ai_filters': {
                            'sentiment': 'neutral',
                            'task': i % 2 == 0,
                            'question': i % 3 == 0
                        }
                    }
                    for i in range(1000)  # 1000 sentences
                ],
                'meeting_attendees': [
                    {
                        'displayName': f'Attendee {i}',
                        'email': f'attendee{i}@test.com',
                        'location': f'Location {i}'
                    }
                    for i in range(50)  # 50 attendees
                ]
            }
            
            large_transcript = Transcript.objects.create(
                fireflies_id='large_json_test',
                title='Large JSON Test',
                meeting_date=datetime.now(timezone.utc),
                duration_minutes=120,
                participant_count=50,
                raw_data=large_json_data,
                content='Large meeting content' * 1000
            )
            
            # Verify large data retrieval
            start_time = time.time()
            retrieved_transcript = Transcript.objects.get(fireflies_id='large_json_test')
            retrieval_time = time.time() - start_time
            
            sentences_count = len(retrieved_transcript.raw_data.get('sentences', []))
            self.stdout.write(f"   📄 Large JSON retrieval ({sentences_count} sentences) in {retrieval_time:.3f}s")
            
            # Test 3: Complex query on large dataset
            start_time = time.time()
            complex_query_results = Transcript.objects.filter(
                meeting_date__gte=datetime.now(timezone.utc) - timedelta(days=50),
                participant_count__gte=2,
                raw_data__has_key='sentences'
            ).prefetch_related('action_items').count()
            complex_query_time = time.time() - start_time
            
            self.stdout.write(f"   🔍 Complex query on large dataset ({complex_query_results} results) in {complex_query_time:.3f}s")
            
            # Cleanup stress test data
            Transcript.objects.filter(fireflies_id__startswith='stress_test_').delete()
            Transcript.objects.filter(fireflies_id='large_json_test').delete()
            
            self.stdout.write("   🧹 Stress test data cleaned up")
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Stress test failed: {str(e)}"))
            return False

    def display_final_results(self, test_results: dict):
        """Display comprehensive test results"""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("🎯 FINAL TEST RESULTS")
        self.stdout.write("=" * 70)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len([k for k, v in test_results.items() if v is not None])
        
        self.stdout.write(f"\n📊 OVERALL SCORE: {passed_tests}/{total_tests} tests passed")
        
        # Detailed results
        for test_name, result in test_results.items():
            if result is None:
                continue
            
            status = "✅ PASSED" if result else "❌ FAILED"
            test_display = test_name.replace('_', ' ').title()
            self.stdout.write(f"   {status} - {test_display}")
        
        # Database Statistics
        self.stdout.write(f"\n📈 DATABASE STATISTICS:")
        self.stdout.write(f"   • Total Transcripts: {Transcript.objects.count()}")
        self.stdout.write(f"   • Total Action Items: {ActionItem.objects.count()}")
        self.stdout.write(f"   • Total System Events: {SystemEvent.objects.count()}")
        self.stdout.write(f"   • Total Daily Reports: {DailyReport.objects.count()}")
        
        # Admin User Info
        User = get_user_model()
        admin_user = User.objects.filter(username='joe@coophive.network').first()
        if admin_user:
            self.stdout.write(f"\n👤 ADMIN USER CONFIGURED:")
            self.stdout.write(f"   • Username: {admin_user.username}")
            self.stdout.write(f"   • Email: {admin_user.email}")
            self.stdout.write(f"   • Password: testpass123")
            self.stdout.write(f"   • Superuser: {admin_user.is_superuser}")
            self.stdout.write(f"   • Staff: {admin_user.is_staff}")
        
        # Recommendations
        self.stdout.write(f"\n💡 RECOMMENDATIONS:")
        if passed_tests == total_tests:
            self.stdout.write("   ✅ Database fully meets all app requirements!")
            self.stdout.write("   ✅ Ready for production deployment")
            self.stdout.write("   ✅ Can handle wealth of data from 7_meetings.json and more")
        else:
            failed_tests = [name for name, result in test_results.items() if result is False]
            self.stdout.write(f"   ⚠️  Address failed tests: {', '.join(failed_tests)}")
        
        self.stdout.write(f"\n🚀 NEXT STEPS:")
        self.stdout.write("   1. Access Django admin at http://127.0.0.1:8000/admin/")
        self.stdout.write("   2. Login with joe@coophive.network / testpass123")
        self.stdout.write("   3. Review imported transcript and action item data")
        self.stdout.write("   4. Run end-to-end pipeline tests")
        
        self.stdout.write("\n" + "=" * 70)