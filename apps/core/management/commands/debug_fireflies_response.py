"""
Django management command to debug Fireflies API responses
"""

import json
import logging
from django.core.management.base import BaseCommand
from apps.core.fireflies_client import get_fireflies_client

logger = logging.getLogger('apps.core.management.commands.debug_fireflies_response')


class Command(BaseCommand):
    help = 'Debug Fireflies API responses - show raw query and response data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--query-type',
            type=str,
            default='today',
            help='Type of query: today, user, or transcript-id',
        )
        parser.add_argument(
            '--transcript-id',
            type=str,
            help='Specific transcript ID to query',
        )
    
    def handle(self, *args, **options):
        """Execute Fireflies API debug queries"""
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Debugging Fireflies API Responses')
        )
        
        # Initialize client
        fireflies_client = get_fireflies_client()
        
        query_type = options['query_type']
        
        if query_type == 'user':
            self.debug_user_query(fireflies_client)
        elif query_type == 'today':
            self.debug_today_transcripts(fireflies_client)
        elif query_type == 'transcript-id' and options['transcript_id']:
            self.debug_specific_transcript(fireflies_client, options['transcript_id'])
        else:
            self.stdout.write(
                self.style.ERROR('❌ Invalid query type or missing transcript ID')
            )
    
    def debug_user_query(self, client):
        """Debug user info query"""
        self.stdout.write('\n📋 USER INFO QUERY')
        self.stdout.write('='*50)
        
        query = """
        query TestConnection {
            user {
                user_id
                name
                email
                integrations {
                    name
                    status
                }
            }
        }
        """
        
        self.stdout.write('📤 GraphQL Query:')
        self.stdout.write(query)
        
        try:
            data = client._execute_query(query)
            self.stdout.write('\n📥 API Response:')
            self.stdout.write(json.dumps(data, indent=2))
            
        except Exception as e:
            self.stdout.write(f'\n❌ Error: {e}')
    
    def debug_today_transcripts(self, client):
        """Debug today's transcripts query"""
        from datetime import date
        
        self.stdout.write('\n📋 TODAY\'S TRANSCRIPTS QUERY')
        self.stdout.write('='*50)
        
        today = date.today()
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        query = """
        query GetTranscripts($startDate: Date!, $endDate: Date!) {
            transcripts(startDate: $startDate, endDate: $endDate) {
                id
                title
                date_uploaded
                duration
                host_email
                summary {
                    overview
                    action_items
                    keywords
                    sentences_count
                }
                transcript_text
                meeting_attendees {
                    displayName
                    email
                }
                organizer_email
            }
        }
        """
        
        variables = {
            'startDate': start_date,
            'endDate': end_date
        }
        
        self.stdout.write('📤 GraphQL Query:')
        self.stdout.write(query)
        self.stdout.write(f'\n📤 Variables:')
        self.stdout.write(json.dumps(variables, indent=2))
        
        try:
            data = client._execute_query(query, variables)
            self.stdout.write('\n📥 API Response:')
            self.stdout.write(json.dumps(data, indent=2))
            
            # Show count and summary
            transcripts = data.get('transcripts', [])
            self.stdout.write(f'\n📊 Found {len(transcripts)} transcripts for {today}')
            
            if transcripts:
                for i, transcript in enumerate(transcripts):
                    self.stdout.write(f'\n📄 Transcript {i+1}:')
                    self.stdout.write(f'  ID: {transcript.get("id")}')
                    self.stdout.write(f'  Title: {transcript.get("title")}')
                    self.stdout.write(f'  Date: {transcript.get("date_uploaded")}')
                    self.stdout.write(f'  Duration: {transcript.get("duration")} seconds')
                    self.stdout.write(f'  Attendees: {len(transcript.get("meeting_attendees", []))}')
                    
                    summary = transcript.get('summary', {})
                    if summary:
                        self.stdout.write(f'  Overview: {summary.get("overview", "N/A")[:100]}...')
                        self.stdout.write(f'  Action Items: {summary.get("action_items", "N/A")[:100]}...')
            else:
                self.stdout.write('  No transcripts found for today')
                
        except Exception as e:
            self.stdout.write(f'\n❌ Error: {e}')
    
    def debug_specific_transcript(self, client, transcript_id):
        """Debug specific transcript query"""
        self.stdout.write(f'\n📋 SPECIFIC TRANSCRIPT QUERY: {transcript_id}')
        self.stdout.write('='*50)
        
        query = """
        query GetTranscript($id: String!) {
            transcript(id: $id) {
                id
                title
                date_uploaded
                duration
                host_email
                summary {
                    overview
                    action_items
                    keywords
                    sentences_count
                    bullet_points
                }
                transcript_text
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
        
        self.stdout.write('📤 GraphQL Query:')
        self.stdout.write(query)
        self.stdout.write(f'\n📤 Variables:')
        self.stdout.write(json.dumps(variables, indent=2))
        
        try:
            data = client._execute_query(query, variables)
            self.stdout.write('\n📥 API Response:')
            self.stdout.write(json.dumps(data, indent=2))
            
            transcript = data.get('transcript')
            if transcript:
                self.stdout.write(f'\n📄 Transcript Details:')
                self.stdout.write(f'  ID: {transcript.get("id")}')
                self.stdout.write(f'  Title: {transcript.get("title")}')
                self.stdout.write(f'  Date: {transcript.get("date_uploaded")}')
                self.stdout.write(f'  Duration: {transcript.get("duration")} seconds')
                
                sentences = transcript.get('sentences', [])
                self.stdout.write(f'  Sentences: {len(sentences)}')
                
                if sentences:
                    self.stdout.write('\n🗣️  First 3 sentences:')
                    for i, sentence in enumerate(sentences[:3]):
                        speaker = sentence.get('speaker_name', 'Unknown')
                        text = sentence.get('text', '')
                        time_ms = sentence.get('start_time', 0)
                        self.stdout.write(f'    {i+1}. [{time_ms}ms] {speaker}: {text}')
            else:
                self.stdout.write('  Transcript not found')
                
        except Exception as e:
            self.stdout.write(f'\n❌ Error: {e}') 