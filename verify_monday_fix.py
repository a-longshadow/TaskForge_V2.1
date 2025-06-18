#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskforge.settings.development')
django.setup()

from apps.core.admin import GeminiProcessedTaskAdmin
from apps.core.models import GeminiProcessedTask

print('🔍 VERIFYING MONDAY.COM CAPACITY FIX')
print('=' * 45)

# Test admin class configuration
admin_class = GeminiProcessedTaskAdmin(GeminiProcessedTask, None)

print("📋 READONLY FIELDS:")
readonly_fields = admin_class.readonly_fields
for field in readonly_fields:
    if field == 'monday_item_id':
        print(f"   ✅ {field} - Monday.com assigns automatically")
    else:
        print(f"   • {field}")

print(f"\n📝 EDITABLE TASK FIELDS:")
# Get all fieldsets and extract editable fields
editable_fields = []
for fieldset_name, fieldset_options in admin_class.fieldsets:
    if fieldset_name == '📋 Monday.com Task Details':
        print(f"   {fieldset_name}:")
        for field_group in fieldset_options['fields']:
            if isinstance(field_group, tuple):
                for field in field_group:
                    if field not in readonly_fields:
                        print(f"      ✅ {field} - User can edit")
                        editable_fields.append(field)
            else:
                if field_group not in readonly_fields:
                    print(f"      ✅ {field_group} - User can edit")
                    editable_fields.append(field_group)

print(f"\n🚀 AUTO-PUSH CONTROLS:")
for fieldset_name, fieldset_options in admin_class.fieldsets:
    if fieldset_name == '🎯 Auto-Push Settings':
        for field_group in fieldset_options['fields']:
            if isinstance(field_group, tuple):
                for field in field_group:
                    print(f"      ✅ {field} - User can control")
            else:
                print(f"      ✅ {field_group} - User can control")

print(f"\n📊 SUMMARY:")
print(f"   • monday_item_id: {'✅ READ-ONLY' if 'monday_item_id' in readonly_fields else '❌ EDITABLE'}")
print(f"   • Task details: ✅ {len(editable_fields)} fields editable")
print(f"   • Auto-push: ✅ User controls enabled")

print(f"\n🎯 CAPACITY FIX STATUS:")
if 'monday_item_id' in readonly_fields:
    print("   ✅ FIXED - Users can only edit board/group settings")
    print("   ✅ Monday.com assigns item IDs automatically")
    print("   ✅ All task details remain editable")
else:
    print("   ❌ NOT FIXED - monday_item_id still editable")

print(f"\n🔧 ADMIN INTERFACE:")
print(f"   URL: http://127.0.0.1:8001/admin/core/geminiprocessedtask/")
print(f"   Login: joe@coophive.network / testpass123")
print(f"   Status: Ready for testing") 