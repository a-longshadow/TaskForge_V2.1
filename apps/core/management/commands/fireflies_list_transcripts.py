"""
Simple Fireflies transcript list command
"""

import requests
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'List transcripts from Fireflies with id, name, and timestamp'
    
    def handle(self, *args, **options):
        """List Fireflies transcripts"""
        
        self.stdout.write('🔍 Fetching Fireflies Transcripts')
        self.stdout.write('='*50)
        
        # API credentials
        api_key = "3482aac6-8fc3-4109-9ff9-31fef2a458eb"
        url = 'https://api.fireflies.ai/graphql'
        
        # Headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Corrected GraphQL query for transcripts
        query = """
        query GetTranscripts {
            transcripts {
                id
                title
                date
            }
        }
        """
        
        payload = {
            'query': query
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            self.stdout.write(f'📡 Response Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data:
                    self.stdout.write(f'❌ GraphQL Errors: {data["errors"]}')
                else:
                    transcripts = data.get('data', {}).get('transcripts', [])
                    
                    self.stdout.write(f'✅ Found {len(transcripts)} transcripts:')
                    self.stdout.write('')
                    
                    for i, transcript in enumerate(transcripts, 1):
                        transcript_id = transcript.get('id', 'N/A')
                        title = transcript.get('title', 'Untitled')
                        date = transcript.get('date', 'N/A')
                        
                        self.stdout.write(f'{i:2d}. ID: {transcript_id}')
                        self.stdout.write(f'    Name: {title}')
                        self.stdout.write(f'    Date: {date}')
                        self.stdout.write('')
                        
            else:
                self.stdout.write(f'❌ HTTP Error {response.status_code}')
                self.stdout.write(f'Response: {response.text}')
                
        except Exception as e:
            self.stdout.write(f'❌ Request failed: {str(e)}') 