"""
Corrected Fireflies API test with proper GraphQL schema
"""

import requests
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Test Fireflies API with corrected GraphQL schema'
    
    def handle(self, *args, **options):
        """Test Fireflies API with correct schema"""
        
        self.stdout.write('🔍 Testing Fireflies API - Corrected Schema')
        self.stdout.write('='*50)
        
        # API credentials
        api_key = "3482aac6-8fc3-4109-9ff9-31fef2a458eb"
        url = 'https://api.fireflies.ai/graphql'
        
        # Headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Test 1: Get user info (we know this works)
        self.test_user_info(url, headers)
        
        # Test 2: Try to discover the transcripts schema
        self.test_schema_introspection(url, headers)
        
        # Test 3: Try different transcript queries
        self.test_transcript_queries(url, headers)
    
    def test_user_info(self, url, headers):
        """Test user info query (known to work)"""
        self.stdout.write('\n📋 USER INFO (Working Query)')
        self.stdout.write('='*30)
        
        query = """
        query {
            user {
                user_id
                name
                email
            }
        }
        """
        
        response = self.make_request(url, headers, query)
        if response:
            self.stdout.write('✅ User info retrieved successfully')
            self.stdout.write(f'   User: {response.get("data", {}).get("user", {}).get("name", "Unknown")}')
            self.stdout.write(f'   Email: {response.get("data", {}).get("user", {}).get("email", "Unknown")}')
    
    def test_schema_introspection(self, url, headers):
        """Try to get schema information"""
        self.stdout.write('\n🔍 SCHEMA INTROSPECTION')
        self.stdout.write('='*30)
        
        # Basic introspection query
        query = """
        query {
            __schema {
                queryType {
                    fields {
                        name
                        description
                        args {
                            name
                            type {
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        
        response = self.make_request(url, headers, query)
        if response and 'data' in response:
            query_fields = response['data']['__schema']['queryType']['fields']
            transcript_fields = [f for f in query_fields if 'transcript' in f['name'].lower()]
            
            self.stdout.write(f'📊 Found {len(transcript_fields)} transcript-related fields:')
            for field in transcript_fields:
                self.stdout.write(f'   • {field["name"]}: {field.get("description", "No description")}')
                if field.get('args'):
                    for arg in field['args']:
                        self.stdout.write(f'     - {arg["name"]}: {arg.get("type", {}).get("name", "Unknown type")}')
    
    def test_transcript_queries(self, url, headers):
        """Try different transcript query variations"""
        self.stdout.write('\n📋 TRANSCRIPT QUERIES (Testing Variations)')
        self.stdout.write('='*30)
        
        # Test 1: Simple transcripts query without parameters
        self.stdout.write('\n🔸 Test 1: Basic transcripts query')
        query1 = """
        query {
            transcripts {
                id
                title
            }
        }
        """
        self.make_request(url, headers, query1, "Basic transcripts")
        
        # Test 2: Try with fromDate/toDate (based on error suggestions)
        self.stdout.write('\n🔸 Test 2: With fromDate/toDate parameters')
        query2 = """
        query {
            transcripts(fromDate: "2025-06-17", toDate: "2025-06-17") {
                id
                title
            }
        }
        """
        self.make_request(url, headers, query2, "fromDate/toDate")
        
        # Test 3: Try with different field names
        self.stdout.write('\n🔸 Test 3: Different field names')
        query3 = """
        query {
            transcripts {
                id
                title
                date
                duration
            }
        }
        """
        self.make_request(url, headers, query3, "Different fields")
        
        # Test 4: Try recent transcripts
        self.stdout.write('\n🔸 Test 4: Recent transcripts')
        query4 = """
        query {
            transcripts(limit: 5) {
                id
                title
                date
            }
        }
        """
        self.make_request(url, headers, query4, "Recent with limit")
    
    def make_request(self, url, headers, query, test_name="Request"):
        """Make a GraphQL request and return response"""
        payload = {'query': query}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            self.stdout.write(f'📥 {test_name} - Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    self.stdout.write(f'❌ GraphQL Errors:')
                    for error in data['errors']:
                        self.stdout.write(f'   • {error.get("message", "Unknown error")}')
                else:
                    self.stdout.write(f'✅ Success!')
                    self.stdout.write(json.dumps(data, indent=2)[:500] + '...' if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
                    return data
            else:
                self.stdout.write(f'❌ HTTP Error: {response.text[:200]}...')
                
        except Exception as e:
            self.stdout.write(f'❌ Exception: {e}')
        
        return None 