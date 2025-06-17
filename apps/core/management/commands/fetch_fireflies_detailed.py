"""
Comprehensive Fireflies transcript fetcher with detailed data
"""

import requests
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fetch detailed Fireflies transcripts with comprehensive data including summary, sentences, and meeting info'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Number of transcripts to fetch (default: 5)'
        )
        parser.add_argument(
            '--mine-only',
            action='store_true',
            help='Fetch only my transcripts (default: all accessible)'
        )
        parser.add_argument(
            '--transcript-id',
            type=str,
            help='Fetch specific transcript by ID'
        )
        parser.add_argument(
            '--show-sentences',
            action='store_true',
            help='Display full sentence data (can be very long)'
        )
        parser.add_argument(
            '--show-summary',
            action='store_true',
            help='Display detailed summary information'
        )
        parser.add_argument(
            '--export-json',
            type=str,
            help='Export results to JSON file'
        )
    
    def handle(self, *args, **options):
        """Fetch detailed Fireflies transcripts"""
        
        self.stdout.write('🔍 Fetching Detailed Fireflies Transcripts')
        self.stdout.write('='*60)
        
        # API credentials
        api_key = "3482aac6-8fc3-4109-9ff9-31fef2a458eb"
        url = 'https://api.fireflies.ai/graphql'
        
        # Headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        if options['transcript_id']:
            # Fetch specific transcript
            self.fetch_specific_transcript(url, headers, options['transcript_id'], options)
        else:
            # Fetch list of transcripts
            self.fetch_transcript_list(url, headers, options)
    
    def fetch_transcript_list(self, url, headers, options):
        """Fetch list of transcripts with detailed data"""
        
        # Comprehensive GraphQL query
        query = """
        query ListTranscripts($mine: Boolean!, $limit: Int!) {
          transcripts(mine: $mine, limit: $limit) {
            id
            title
            date
            duration
            transcript_url
            meeting_link
            organizer_email
            host_email
            meeting_info {
              silent_meeting
              fred_joined
              summary_status
            }
            summary {
              overview
              outline
              action_items
              keywords
              topics_discussed
              shorthand_bullet
              bullet_gist
              gist
              short_summary
              short_overview
              meeting_type
            }
            sentences {
              index
              speaker_id
              speaker_name
              raw_text
              text
              start_time
              end_time
              ai_filters {
                task
                pricing
                metric
                question
                date_and_time
                sentiment
              }
            }
            meeting_attendees {
              displayName
              email
              location
            }
          }
        }
        """
        
        variables = {
            'mine': options['mine_only'],
            'limit': options['limit']
        }
        
        payload = {
            'query': query,
            'variables': variables
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            self.stdout.write(f'📡 Response Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data:
                    self.stdout.write(f'❌ GraphQL Errors: {json.dumps(data["errors"], indent=2)}')
                else:
                    transcripts = data.get('data', {}).get('transcripts', [])
                    self.display_transcripts(transcripts, options)
                    
                    # Export to JSON if requested
                    if options['export_json']:
                        self.export_to_json(transcripts, options['export_json'])
                        
            else:
                self.stdout.write(f'❌ HTTP Error {response.status_code}')
                self.stdout.write(f'Response: {response.text}')
                
        except Exception as e:
            self.stdout.write(f'❌ Request failed: {str(e)}')
    
    def fetch_specific_transcript(self, url, headers, transcript_id, options):
        """Fetch a specific transcript by ID"""
        
        query = """
        query GetTranscript($id: String!) {
          transcript(id: $id) {
            id
            title
            date
            duration
            transcript_url
            meeting_link
            organizer_email
            host_email
            meeting_info {
              silent_meeting
              fred_joined
              summary_status
            }
            summary {
              overview
              outline
              action_items
              keywords
              topics_discussed
              shorthand_bullet
              bullet_gist
              gist
              short_summary
              short_overview
              meeting_type
            }
            sentences {
              index
              speaker_id
              speaker_name
              raw_text
              text
              start_time
              end_time
              ai_filters {
                task
                pricing
                metric
                question
                date_and_time
                sentiment
              }
            }
            meeting_attendees {
              displayName
              email
              location
            }
          }
        }
        """
        
        variables = {'id': transcript_id}
        payload = {
            'query': query,
            'variables': variables
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            self.stdout.write(f'📡 Response Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data:
                    self.stdout.write(f'❌ GraphQL Errors: {json.dumps(data["errors"], indent=2)}')
                else:
                    transcript = data.get('data', {}).get('transcript')
                    if transcript:
                        self.display_transcripts([transcript], options)
                        
                        # Export to JSON if requested
                        if options['export_json']:
                            self.export_to_json([transcript], options['export_json'])
                    else:
                        self.stdout.write(f'❌ Transcript {transcript_id} not found')
                        
            else:
                self.stdout.write(f'❌ HTTP Error {response.status_code}')
                self.stdout.write(f'Response: {response.text}')
                
        except Exception as e:
            self.stdout.write(f'❌ Request failed: {str(e)}')
    
    def display_transcripts(self, transcripts, options):
        """Display transcript data in a formatted way"""
        
        self.stdout.write(f'✅ Found {len(transcripts)} transcript(s):')
        self.stdout.write('')
        
        for i, transcript in enumerate(transcripts, 1):
            self.stdout.write(f'📄 TRANSCRIPT {i}')
            self.stdout.write('-' * 50)
            
            # Basic Info
            self.stdout.write(f'ID: {transcript.get("id", "N/A")}')
            self.stdout.write(f'Title: {transcript.get("title", "Untitled")}')
            self.stdout.write(f'Date: {transcript.get("date", "N/A")}')
            self.stdout.write(f'Duration: {transcript.get("duration", "N/A")} seconds')
            self.stdout.write(f'Organizer: {transcript.get("organizer_email", "N/A")}')
            self.stdout.write(f'Host: {transcript.get("host_email", "N/A")}')
            
            # Meeting Info
            meeting_info = transcript.get('meeting_info', {})
            if meeting_info:
                self.stdout.write('')
                self.stdout.write('📋 MEETING INFO:')
                self.stdout.write(f'  Silent Meeting: {meeting_info.get("silent_meeting", "N/A")}')
                self.stdout.write(f'  Fred Joined: {meeting_info.get("fred_joined", "N/A")}')
                self.stdout.write(f'  Summary Status: {meeting_info.get("summary_status", "N/A")}')
            
            # Attendees
            attendees = transcript.get('meeting_attendees', [])
            if attendees:
                self.stdout.write('')
                self.stdout.write(f'👥 ATTENDEES ({len(attendees)}):')
                for attendee in attendees:
                    name = attendee.get('displayName', 'Unknown')
                    email = attendee.get('email', 'no-email')
                    location = attendee.get('location', 'N/A')
                    self.stdout.write(f'  • {name} <{email}> [{location}]')
            
            # Summary (if requested)
            if options['show_summary']:
                summary = transcript.get('summary', {})
                if summary:
                    self.stdout.write('')
                    self.stdout.write('📝 SUMMARY:')
                    
                    fields = [
                        ('Meeting Type', 'meeting_type'),
                        ('Overview', 'overview'),
                        ('Short Summary', 'short_summary'),
                        ('Action Items', 'action_items'),
                        ('Keywords', 'keywords'),
                        ('Topics Discussed', 'topics_discussed'),
                        ('Outline', 'outline'),
                        ('Gist', 'gist'),
                        ('Bullet Gist', 'bullet_gist'),
                        ('Shorthand Bullet', 'shorthand_bullet'),
                    ]
                    
                    for field_name, field_key in fields:
                        value = summary.get(field_key)
                        if value:
                            self.stdout.write(f'  {field_name}: {self.truncate_text(str(value), 200)}')
            
            # Sentences (if requested and available)
            if options['show_sentences']:
                sentences = transcript.get('sentences', [])
                if sentences:
                    self.stdout.write('')
                    self.stdout.write(f'💬 SENTENCES ({len(sentences)}):')
                    
                    # Show first 5 sentences to avoid overwhelming output
                    for j, sentence in enumerate(sentences[:5]):
                        speaker = sentence.get('speaker_name', 'Unknown')
                        text = sentence.get('text', sentence.get('raw_text', 'No text'))
                        start_time = sentence.get('start_time', 0)
                        
                        self.stdout.write(f'  [{self.format_time(start_time)}] {speaker}: {self.truncate_text(text, 100)}')
                    
                    if len(sentences) > 5:
                        self.stdout.write(f'  ... and {len(sentences) - 5} more sentences')
            
            # Stats
            sentence_count = len(transcript.get('sentences', []))
            self.stdout.write('')
            self.stdout.write(f'📊 STATS: {sentence_count} sentences total')
            
            self.stdout.write('')
    
    def truncate_text(self, text, max_length):
        """Truncate text to max_length characters"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + '...'
    
    def format_time(self, milliseconds):
        """Format time in milliseconds to MM:SS format"""
        try:
            seconds = int(milliseconds) // 1000
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        except:
            return "00:00"
    
    def export_to_json(self, transcripts, filename):
        """Export transcripts to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(transcripts, f, indent=2, default=str)
            self.stdout.write(f'✅ Exported {len(transcripts)} transcript(s) to {filename}')
        except Exception as e:
            self.stdout.write(f'❌ Failed to export to {filename}: {str(e)}') 