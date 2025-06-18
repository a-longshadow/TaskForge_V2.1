#!/usr/bin/env python
"""
Test script to push a single ProcessedTaskData from database to Monday.com
"""

import os
import sys
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskforge.settings.development')
django.setup()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_task_push():
    """Test pushing a single ProcessedTaskData from database to Monday.com"""
    
    try:
        from apps.core.models import ProcessedTaskData
        from apps.core.precision_monday_client import get_precision_monday_client
        
        logger.info("🧪 Starting database task push test")
        
        # Check what's in the database
        total_tasks = ProcessedTaskData.objects.count()
        logger.info(f"📊 Total ProcessedTaskData records: {total_tasks}")
        
        if total_tasks == 0:
            logger.error("❌ No ProcessedTaskData found in database")
            return False
        
        # Try to find an approved task with email first
        task = ProcessedTaskData.objects.filter(
            human_approved=True,
            delivery_status='pending'
        ).exclude(assignee_emails='').first()
        
        if not task:
            logger.info("⚠️ No approved tasks with emails found, trying any approved task...")
            task = ProcessedTaskData.objects.filter(human_approved=True).first()
            
        if not task:
            logger.info("⚠️ No approved tasks found, using first task and approving it for test...")
            task = ProcessedTaskData.objects.first()
            
            # Temporarily approve and add email for testing
            task.human_approved = True
            if not task.assignee_emails:
                task.assignee_emails = "test@coophive.network"
            if not task.assignee_full_names:
                task.assignee_full_names = "Test User"
            task.save()
            logger.info("✅ Task temporarily approved and email added for testing")
        
        logger.info(f"📋 Selected task: {task.task_item[:60]}...")
        logger.info(f"   👤 Assignee: {task.assignee_full_names}")
        logger.info(f"   📧 Email: {task.assignee_emails}")
        logger.info(f"   🎯 Priority: {task.priority}")
        logger.info(f"   📊 Status: {task.status}")
        logger.info(f"   ✅ Approved: {task.human_approved}")
        logger.info(f"   📤 Delivery Status: {task.delivery_status}")
        logger.info(f"   🔗 Monday ID: {task.monday_item_id or 'None'}")
        logger.info(f"   🚀 Ready for delivery: {task.is_ready_for_delivery}")
        
        if not task.is_ready_for_delivery:
            logger.error("❌ Task is not ready for delivery!")
            logger.error(f"   - Human approved: {task.human_approved}")
            logger.error(f"   - Delivery status: {task.delivery_status}")
            logger.error(f"   - Has task item: {bool(task.task_item)}")
            logger.error(f"   - Has assignee emails: {bool(task.assignee_emails)}")
            return False
        
        # Get precision Monday client
        logger.info("🔧 Creating precision Monday.com client...")
        monday_client = get_precision_monday_client()
        logger.info("✅ Precision Monday.com client created successfully")
        
        # Test delivery
        logger.info("🚀 Attempting delivery to Monday.com...")
        logger.info(f"   📋 Task: {task.task_item}")
        logger.info(f"   📝 Description: {task.brief_description[:100]}...")
        
        success = monday_client.deliver_processed_task(task)
        
        # Refresh task from database to see changes
        task.refresh_from_db()
        
        if success:
            logger.info("✅ SUCCESS: Task delivered to Monday.com!")
            logger.info(f"   🔗 Monday.com Item ID: {task.monday_item_id}")
            logger.info(f"   📊 Delivery Status: {task.delivery_status}")
            logger.info(f"   📅 Delivered At: {task.delivered_at}")
            
            if task.delivery_errors:
                logger.warning(f"   ⚠️ Delivery warnings: {task.delivery_errors}")
            
            return True
        else:
            logger.error("❌ FAILED: Task delivery failed")
            logger.error(f"   📊 Delivery Status: {task.delivery_status}")
            if task.delivery_errors:
                logger.error(f"   🚨 Errors: {task.delivery_errors}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.exception("Full error details:")
        return False

def show_database_status():
    """Show current database status"""
    try:
        from apps.core.models import ProcessedTaskData, RawTranscriptCache
        
        logger.info("📊 DATABASE STATUS:")
        logger.info("-" * 40)
        
        # Show cache items
        cache_count = RawTranscriptCache.objects.count()
        logger.info(f"📄 Raw cache items: {cache_count}")
        
        # Show processed tasks
        processed_count = ProcessedTaskData.objects.count()
        approved_count = ProcessedTaskData.objects.filter(human_approved=True).count()
        delivered_count = ProcessedTaskData.objects.filter(delivery_status='delivered').count()
        pending_count = ProcessedTaskData.objects.filter(delivery_status='pending').count()
        ready_count = ProcessedTaskData.objects.filter(
            human_approved=True,
            delivery_status='pending'
        ).exclude(assignee_emails='').count()
        
        logger.info(f"🤖 Processed tasks: {processed_count}")
        logger.info(f"   ✅ Approved: {approved_count}")
        logger.info(f"   📤 Delivered: {delivered_count}")
        logger.info(f"   ⏳ Pending: {pending_count}")
        logger.info(f"   🚀 Ready for delivery: {ready_count}")
        
        # Show sample tasks
        if processed_count > 0:
            logger.info("\n📋 SAMPLE TASKS:")
            for i, task in enumerate(ProcessedTaskData.objects.all()[:3]):
                logger.info(f"   {i+1}. {task.task_item[:50]}...")
                logger.info(f"      Status: {task.delivery_status} | Approved: {task.human_approved}")
                logger.info(f"      Monday ID: {task.monday_item_id or 'None'}")
                logger.info(f"      Email: {task.assignee_emails or 'None'}")
                logger.info(f"      Ready: {task.is_ready_for_delivery}")
        
    except Exception as e:
        logger.error(f"❌ Error showing database status: {e}")

if __name__ == "__main__":
    logger.info("🔗 DATABASE TASK PUSH TEST")
    logger.info("=" * 50)
    
    # Show current status
    show_database_status()
    
    logger.info("\n🚀 TESTING MONDAY.COM PUSH")
    logger.info("=" * 50)
    
    success = test_database_task_push()
    
    if success:
        logger.info("\n🎉 TEST PASSED: Database task push functionality is working!")
        logger.info("✅ ProcessedTaskData can be successfully delivered to Monday.com")
    else:
        logger.info("\n💥 TEST FAILED: Database task push functionality has issues")
        logger.info("❌ Check logs above for error details")
    
    # Show final status
    logger.info("\n📊 FINAL DATABASE STATUS:")
    show_database_status()
    
    sys.exit(0 if success else 1) 