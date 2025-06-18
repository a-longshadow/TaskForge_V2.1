#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskforge.settings.development')
django.setup()

from apps.core.models import RawTranscriptCache
from datetime import datetime

# Meetings from Fireflies screenshot (Jun 15 - Today, 8 Meetings)
fireflies_meetings = [
    "CoopHive <> Varmeta | Weekly Meeting",  # Yang Zheng, Wed Jun 18, 05:00 AM, 11 mins
    "Yang x Nakib weekly",                   # Yang Zheng, Wed Jun 18, 04:00 AM, 27 mins  
    "Vardhan <> Levi",                       # Levi Rybalov, Wed Jun 18, 12:45 AM, 23 mins
    "Ops meeting",                           # Andrew Hemingway, Tue Jun 17, 10:00 PM, 38 mins
    "Vardhan <> Levi",                       # Levi Rybalov, Tue Jun 17, 06:30 AM, 22 mins
    "CoopHive Team Meeting"                  # Levi Rybalov, Tue Jun 17, 04:00 AM, 43 mins
]

print("🔍 FIREFLIES MEETINGS vs DATABASE CHECK")
print("=" * 50)

# Get all meetings from database
db_meetings = RawTranscriptCache.objects.all().order_by('-meeting_date')
print(f"📊 Database Status:")
print(f"   Total meetings in DB: {db_meetings.count()}")
print()

print("📄 MEETINGS IN DATABASE:")
print("-" * 30)
for i, meeting in enumerate(db_meetings, 1):
    print(f"{i}. {meeting.meeting_title}")
    print(f"   Date: {meeting.meeting_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Fireflies ID: {meeting.fireflies_id}")
    print(f"   Duration: {meeting.duration_minutes} mins")
    print(f"   Participants: {meeting.participant_count}")
    print()

print("🎯 FIREFLIES SCREENSHOT MEETINGS:")
print("-" * 35)
for i, meeting in enumerate(fireflies_meetings, 1):
    print(f"{i}. {meeting}")

print()
print("✅ MATCH ANALYSIS:")
print("-" * 20)

# Check for matches
matches_found = 0
for ff_meeting in fireflies_meetings:
    found = False
    for db_meeting in db_meetings:
        if ff_meeting.lower() in db_meeting.meeting_title.lower() or db_meeting.meeting_title.lower() in ff_meeting.lower():
            print(f"✓ FOUND: '{ff_meeting}' matches '{db_meeting.meeting_title}'")
            matches_found += 1
            found = True
            break
    if not found:
        print(f"✗ MISSING: '{ff_meeting}' not found in database")

print()
print(f"📈 SUMMARY:")
print(f"   Fireflies meetings shown: {len(fireflies_meetings)}")
print(f"   Database meetings: {db_meetings.count()}")
print(f"   Matches found: {matches_found}")
print(f"   Missing from DB: {len(fireflies_meetings) - matches_found}")

if matches_found == len(fireflies_meetings):
    print("🎉 All Fireflies meetings are in the database!")
else:
    print("⚠️  Some meetings from Fireflies are missing from the database.")
    print("   Consider running data refresh to sync latest meetings.") 