"""
Fireflies.ai GraphQL API client
"""

import logging
import requests
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger('apps.core.fireflies_client')


class FirefliesClient:
    """Client for Fireflies.ai GraphQL API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.fireflies.ai/graphql'
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        try:
            response = self.session.post(self.base_url, json=payload, timeout=30)
            
            # Log the raw response for debugging
            logger.info(f"Fireflies API Response Status: {response.status_code}")
            logger.info(f"Fireflies API Response Body: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"Fireflies API HTTP Error {response.status_code}: {response.text}")
                raise Exception(f"Fireflies API HTTP Error {response.status_code}: {response.text}")
            
            data = response.json()
            
            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            return data.get('data', {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fireflies API request failed: {e}")
            raise Exception(f"Fireflies API request failed: {e}")
    
    def get_today_transcripts(self) -> List[Dict[str, Any]]:
        """Get all transcripts from today"""
        today = date.today()
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        query = """
        query GetTranscripts($startDate: Date!, $endDate: Date!) {
            transcripts(startDate: $startDate, endDate: $endDate) {
                id
                title
                date
                duration
                summary {
                    overview
                    action_items
                    keywords
                }
                sentences {
                    speaker_name
                    text
                    start_time
                }
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
        
        try:
            data = self._execute_query(query, variables)
            transcripts = data.get('transcripts', [])
            
            logger.info(f"Retrieved {len(transcripts)} transcripts for {today}")
            return transcripts
            
        except Exception as e:
            logger.error(f"Failed to get today's transcripts: {e}")
            return []
    
    def get_transcript_by_id(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific transcript by ID"""
        query = """
        query GetTranscript($id: String!) {
            transcript(id: $id) {
                id
                title
                date
                duration
                summary {
                    overview
                    action_items
                    keywords
                }
                sentences {
                    speaker_name
                    text
                    start_time
                }
                meeting_attendees {
                    displayName
                    email
                }
                organizer_email
            }
        }
        """
        
        variables = {'id': transcript_id}
        
        try:
            data = self._execute_query(query, variables)
            return data.get('transcript')
            
        except Exception as e:
            logger.error(f"Failed to get transcript {transcript_id}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test connection to Fireflies API"""
        query = """
        query TestConnection {
            user {
                user_id
                name
            }
        }
        """
        
        try:
            data = self._execute_query(query)
            user = data.get('user')
            if user:
                logger.info(f"Connected to Fireflies API as: {user.get('name', 'Unknown')}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Fireflies connection test failed: {e}")
            return False


def get_fireflies_client() -> FirefliesClient:
    """Get configured Fireflies client"""
    api_key = "3482aac6-8fc3-4109-9ff9-31fef2a458eb"  # From user's credentials
    return FirefliesClient(api_key) 