"""
Simple Fireflies API raw response tester
"""

import requests
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Test Fireflies API and show raw response'
    
    def handle(self, *args, **options):
        """Test Fireflies API directly"""
        
        self.stdout.write('🔍 Testing Fireflies API - Raw Response')
        self.stdout.write('='*50)
        
        # API credentials
        api_key = "3482aac6-8fc3-4109-9ff9-31fef2a458eb"
        url = 'https://api.fireflies.ai/graphql'
        
        # Headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Simple user query
        query = """
        query {
            user {
                user_id
                name
                email
            }
        }
        """
        
        payload = {
            'query': query
        }
        
        self.stdout.write('📤 Request Details:')
        self.stdout.write(f'  URL: {url}')
        self.stdout.write(f'  Headers: {headers}')
        self.stdout.write(f'  Payload: {json.dumps(payload, indent=2)}')
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            self.stdout.write('\n📥 Response Details:')
            self.stdout.write(f'  Status Code: {response.status_code}')
            self.stdout.write(f'  Headers: {dict(response.headers)}')
            self.stdout.write(f'  Raw Response: {response.text}')
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.stdout.write('\n✅ Parsed JSON:')
                    self.stdout.write(json.dumps(data, indent=2))
                except:
                    self.stdout.write('\n❌ Could not parse response as JSON')
            else:
                self.stdout.write(f'\n❌ HTTP Error: {response.status_code}')
                
                # Try to parse error as JSON
                try:
                    error_data = response.json()
                    self.stdout.write('Error Details (JSON):')
                    self.stdout.write(json.dumps(error_data, indent=2))
                except:
                    self.stdout.write('Error Details (Raw):')
                    self.stdout.write(response.text)
                    
        except Exception as e:
            self.stdout.write(f'\n❌ Request Exception: {e}')
        
        # Also test today's transcripts query
        self.stdout.write('\n' + '='*50)
        self.stdout.write('🔍 Testing Today\'s Transcripts Query')
        self.stdout.write('='*50)
        
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        
        transcripts_query = """
        query GetTranscripts($startDate: Date!, $endDate: Date!) {
            transcripts(startDate: $startDate, endDate: $endDate) {
                id
                title
                date_uploaded
                duration
                summary {
                    overview
                    action_items
                }
                meeting_attendees {
                    displayName
                    email
                }
            }
        }
        """
        
        transcripts_payload = {
            'query': transcripts_query,
            'variables': {
                'startDate': today,
                'endDate': today
            }
        }
        
        self.stdout.write('📤 Transcripts Request:')
        self.stdout.write(f'  Query: {transcripts_query}')
        self.stdout.write(f'  Variables: {transcripts_payload["variables"]}')
        
        try:
            response = requests.post(url, json=transcripts_payload, headers=headers, timeout=30)
            
            self.stdout.write('\n📥 Transcripts Response:')
            self.stdout.write(f'  Status Code: {response.status_code}')
            self.stdout.write(f'  Raw Response: {response.text}')
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.stdout.write('\n✅ Parsed JSON:')
                    self.stdout.write(json.dumps(data, indent=2))
                    
                    # Count transcripts
                    transcripts = data.get('data', {}).get('transcripts', [])
                    self.stdout.write(f'\n📊 Found {len(transcripts)} transcripts for {today}')
                    
                except:
                    self.stdout.write('\n❌ Could not parse response as JSON')
            else:
                self.stdout.write(f'\n❌ HTTP Error: {response.status_code}')
                
        except Exception as e:
            self.stdout.write(f'\n❌ Request Exception: {e}') 