from django.core.management.base import BaseCommand
from apps.core.fireflies_client import MultiKeyFirefliesClient
import requests
import json


class Command(BaseCommand):
    help = 'Test new Fireflies API key before adding to failover system'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, required=True, help='API key to test')
        parser.add_argument('--verbose', action='store_true', help='Show detailed response')

    def handle(self, *args, **options):
        api_key = options['api_key']
        verbose = options['verbose']
        
        self.stdout.write("🔑 TESTING NEW FIREFLIES API KEY")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Key: ...{api_key[-8:]}")
        
        # Test 1: Basic connection test
        self.stdout.write("\n📡 Test 1: Basic Connection Test")
        success = self.test_basic_connection(api_key, verbose)
        
        if success:
            self.stdout.write("✅ Basic connection successful!")
            
            # Test 2: User info query
            self.stdout.write("\n👤 Test 2: User Info Query")
            user_success = self.test_user_info(api_key, verbose)
            
            if user_success:
                self.stdout.write("✅ User info query successful!")
                
                # Test 3: Transcript query
                self.stdout.write("\n📋 Test 3: Transcript Query")
                transcript_success = self.test_transcript_query(api_key, verbose)
                
                if transcript_success:
                    self.stdout.write("✅ Transcript query successful!")
                    self.stdout.write("\n🎉 NEW API KEY IS FULLY OPERATIONAL!")
                    self.stdout.write("✅ Ready to add to failover system")
                    return True
                else:
                    self.stdout.write("❌ Transcript query failed")
            else:
                self.stdout.write("❌ User info query failed")
        else:
            self.stdout.write("❌ Basic connection failed")
        
        self.stdout.write("\n❌ API KEY NOT SUITABLE FOR FAILOVER")
        return False

    def test_basic_connection(self, api_key, verbose):
        """Test basic API connection"""
        try:
            session = requests.Session()
            session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
            
            # Simple user query
            query = """
            query {
                user {
                    user_id
                    email
                    name
                }
            }
            """
            
            response = session.post(
                'https://api.fireflies.ai/graphql',
                json={'query': query},
                timeout=30
            )
            
            self.stdout.write(f"   Status Code: {response.status_code}")
            
            if verbose:
                self.stdout.write(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    self.stdout.write(f"   GraphQL Errors: {data['errors']}")
                    return False
                return True
            else:
                return False
                
        except Exception as e:
            self.stdout.write(f"   Exception: {str(e)}")
            return False

    def test_user_info(self, api_key, verbose):
        """Test user info retrieval"""
        try:
            session = requests.Session()
            session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
            
            query = """
            query {
                user {
                    user_id
                    email
                    name
                    integrations {
                        zoom
                        teams
                        webex
                        googlemeet
                    }
                }
            }
            """
            
            response = session.post(
                'https://api.fireflies.ai/graphql',
                json={'query': query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' not in data and 'data' in data:
                    user_data = data['data']['user']
                    self.stdout.write(f"   User: {user_data.get('name', 'Unknown')}")
                    self.stdout.write(f"   Email: {user_data.get('email', 'Unknown')}")
                    
                    if verbose:
                        self.stdout.write(f"   Full data: {json.dumps(user_data, indent=2)}")
                    
                    return True
                else:
                    self.stdout.write(f"   Errors: {data.get('errors', 'Unknown error')}")
                    return False
            else:
                self.stdout.write(f"   HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            self.stdout.write(f"   Exception: {str(e)}")
            return False

    def test_transcript_query(self, api_key, verbose):
        """Test transcript retrieval"""
        try:
            session = requests.Session()
            session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
            
            # Simple transcript list query
            query = """
            query {
                transcripts(mine: true, limit: 5) {
                    id
                    title
                    date
                    duration
                    organizer_email
                }
            }
            """
            
            response = session.post(
                'https://api.fireflies.ai/graphql',
                json={'query': query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' not in data and 'data' in data:
                    transcripts = data['data']['transcripts']
                    self.stdout.write(f"   Found {len(transcripts)} transcripts")
                    
                    if transcripts and verbose:
                        for i, transcript in enumerate(transcripts[:2]):
                            self.stdout.write(f"   {i+1}. {transcript.get('title', 'Untitled')} ({transcript.get('date', 'No date')})")
                    
                    return True
                else:
                    self.stdout.write(f"   Errors: {data.get('errors', 'Unknown error')}")
                    return False
            else:
                self.stdout.write(f"   HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            self.stdout.write(f"   Exception: {str(e)}")
            return False 