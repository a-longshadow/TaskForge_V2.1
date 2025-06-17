"""
Test specific Fireflies transcript
"""

import requests
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Test specific Fireflies transcript'
    
    def handle(self, *args, **options):
        """Test specific transcript"""
        
        self.stdout.write('🔍 Testing Specific Fireflies Transcript')
        self.stdout.write('='*50)
        
        # API credentials
        api_key = "3482aac6-8fc3-4109-9ff9-31fef2a458eb"
        url = 'https://api.fireflies.ai/graphql'
        
        # Headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Test the TaskForge meeting transcript
        transcript_id = "01JXNE8C52N195FCC2CKE2RHPW"  # Andrew <> Joe - TaskForge V2
        
                 query = """
         query GetTranscript($id: String!) {
             transcript(id: $id) {
                 id
                 title
                 date
                 duration
                 host_email
                 summary {
                     overview
                     action_items
                     keywords
                     bullet_gist
                 }
                 transcript_url
                 meeting_attendees {
                     displayName
                     email
                 }
                 organizer_email
                 sentences {
                     text
                     speaker_name
                     start_time
                 }
             }
         }
         """
        
        variables = {'id': transcript_id}
        payload = {
            'query': query,
            'variables': variables
        }
        
        self.stdout.write(f'📤 Querying transcript: {transcript_id}')
        self.stdout.write('📤 Query:')
        self.stdout.write(query)
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            self.stdout.write(f'\n📥 Response Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data:
                    self.stdout.write('❌ GraphQL Errors:')
                    for error in data['errors']:
                        self.stdout.write(f'   • {error.get("message", "Unknown error")}')
                else:
                    self.stdout.write('✅ Success! Complete transcript data:')
                    self.stdout.write('='*50)
                    self.stdout.write(json.dumps(data, indent=2))
                    
                    # Extract and display key information
                    transcript = data.get('data', {}).get('transcript', {})
                    if transcript:
                        self.stdout.write('\n📋 KEY INFORMATION:')
                        self.stdout.write(f'   Title: {transcript.get("title", "N/A")}')
                        self.stdout.write(f'   Date: {transcript.get("date", "N/A")}')
                        self.stdout.write(f'   Duration: {transcript.get("duration", "N/A")} seconds')
                        
                        attendees = transcript.get('meeting_attendees', [])
                        self.stdout.write(f'   Attendees: {len(attendees)}')
                        for attendee in attendees:
                            self.stdout.write(f'     • {attendee.get("displayName", "Unknown")} <{attendee.get("email", "no-email")}>')
                        
                        summary = transcript.get('summary', {})
                        if summary:
                            self.stdout.write(f'\n📝 SUMMARY:')
                            self.stdout.write(f'   Overview: {summary.get("overview", "N/A")[:200]}...')
                            self.stdout.write(f'   Action Items: {summary.get("action_items", "N/A")[:200]}...')
                            
                        sentences = transcript.get('sentences', [])
                        self.stdout.write(f'\n🗣️  TRANSCRIPT ({len(sentences)} sentences):')
                        for i, sentence in enumerate(sentences[:5]):  # Show first 5
                            speaker = sentence.get('speaker_name', 'Unknown')
                            text = sentence.get('text', '')
                            time_ms = sentence.get('start_time', 0)
                            self.stdout.write(f'   {i+1}. [{time_ms}ms] {speaker}: {text}')
                        
                        if len(sentences) > 5:
                            self.stdout.write(f'   ... and {len(sentences) - 5} more sentences')
                            
            else:
                self.stdout.write(f'❌ HTTP Error: {response.text}')
                
        except Exception as e:
            self.stdout.write(f'❌ Exception: {e}') 