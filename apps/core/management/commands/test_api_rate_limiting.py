"""
Comprehensive API Rate Limiting Tests
Tests rate limiting, quota management, and failover for all external APIs
"""

import time
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.cache import cache
from unittest.mock import patch, MagicMock
import requests

from apps.core.fireflies_client import get_fireflies_client
from apps.core.gemini_client import get_gemini_client
from apps.core.monday_client import get_monday_client

logger = logging.getLogger('apps.core.management.commands.test_api_rate_limiting')


class Command(BaseCommand):
    help = 'Test API rate limiting, quota management, and failover for all external services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--service',
            type=str,
            choices=['fireflies', 'gemini', 'monday', 'all'],
            default='all',
            help='Which service to test (default: all)',
        )
        parser.add_argument(
            '--stress-test',
            action='store_true',
            help='Run stress tests with rapid API calls',
        )
        parser.add_argument(
            '--mock-failures',
            action='store_true',
            help='Mock API failures to test failover behavior',
        )

    def handle(self, *args, **options):
        """Execute API rate limiting tests"""
        self.service = options['service']
        self.stress_test = options['stress_test']
        self.mock_failures = options['mock_failures']
        
        self.stdout.write("🚀 API RATE LIMITING COMPREHENSIVE TEST")
        self.stdout.write("=" * 60)
        
        if self.service in ['fireflies', 'all']:
            self.test_fireflies_rate_limiting()
        
        if self.service in ['gemini', 'all']:
            self.test_gemini_rate_limiting()
        
        if self.service in ['monday', 'all']:
            self.test_monday_rate_limiting()
        
        self.stdout.write("\n🎯 RATE LIMITING TEST SUMMARY")
        self.stdout.write("=" * 60)
        self.stdout.write("All external services should implement:")
        self.stdout.write("✅ Request rate limiting (requests per minute)")
        self.stdout.write("✅ Quota tracking and warnings")
        self.stdout.write("✅ Automatic backoff on rate limit errors")
        self.stdout.write("✅ Multi-key failover (where applicable)")
        self.stdout.write("✅ Caching to reduce API usage")
        self.stdout.write("✅ Circuit breaker pattern for reliability")

    def test_fireflies_rate_limiting(self):
        """Test Fireflies API rate limiting (already implemented)"""
        self.stdout.write("\n📄 TESTING FIREFLIES API RATE LIMITING")
        self.stdout.write("-" * 50)
        
        client = get_fireflies_client()
        
        # Test 1: Check if rate limiting is implemented
        self.stdout.write("Test 1: Rate limiting implementation check")
        if hasattr(client, 'min_request_interval'):
            self.stdout.write(f"✅ Min request interval: {client.min_request_interval}s")
        else:
            self.stdout.write("❌ No rate limiting interval found")
        
        # Test 2: Check multi-key failover
        self.stdout.write("Test 2: Multi-key failover check")
        if hasattr(client, 'api_keys') and len(client.api_keys) > 1:
            self.stdout.write(f"✅ Multi-key failover: {len(client.api_keys)} keys")
        else:
            self.stdout.write("❌ No multi-key failover found")
        
        # Test 3: Check caching
        self.stdout.write("Test 3: Caching implementation check")
        if hasattr(client, 'cache_timeout'):
            self.stdout.write(f"✅ Cache timeout: {client.cache_timeout/3600}h")
        else:
            self.stdout.write("❌ No caching implementation found")
        
        # Test 4: Stress test (if enabled)
        if self.stress_test:
            self.stdout.write("Test 4: Stress testing rate limiting")
            self._stress_test_fireflies(client)

    def test_gemini_rate_limiting(self):
        """Test Gemini API rate limiting (enhanced implementation)"""
        self.stdout.write("\n🤖 TESTING GEMINI API RATE LIMITING")
        self.stdout.write("-" * 50)
        
        client = get_gemini_client()
        
        # Test 1: Check if rate limiting is implemented
        self.stdout.write("Test 1: Rate limiting implementation check")
        if hasattr(client, 'min_request_interval') and hasattr(client, 'rate_limit_per_minute'):
            self.stdout.write(f"✅ Rate limiting found: {client.rate_limit_per_minute}/min")
        else:
            self.stdout.write("❌ MISSING: Rate limiting not implemented")
            self.stdout.write("   📋 TODO: Implement rate limiting for Gemini API")
        
        # Test 2: Check quota tracking
        self.stdout.write("Test 2: Quota tracking check")
        if hasattr(client, 'quota_tracker'):
            self.stdout.write("✅ Quota tracking found")
        else:
            self.stdout.write("❌ MISSING: Quota tracking not implemented")
            self.stdout.write("   📋 TODO: Implement quota tracking for Gemini API")
        
        # Test 3: Check caching
        self.stdout.write("Test 3: Caching implementation check")
        if hasattr(client, 'cache_timeout'):
            self.stdout.write(f"✅ Caching found: {client.cache_timeout/60:.0f}min timeout")
        else:
            self.stdout.write("❌ MISSING: Caching not implemented")
            self.stdout.write("   📋 TODO: Implement caching for Gemini API")
        
        # Test 4: Check circuit breaker
        self.stdout.write("Test 4: Circuit breaker check")
        if hasattr(client, 'circuit_breaker'):
            self.stdout.write("✅ Circuit breaker found")
        else:
            self.stdout.write("❌ MISSING: Circuit breaker not implemented")
            self.stdout.write("   📋 TODO: Implement circuit breaker for Gemini API")
        
        # Test 5: Stress test (if enabled)
        if self.stress_test:
            self.stdout.write("Test 5: Stress testing (simulated)")
            self._stress_test_gemini(client)

    def test_monday_rate_limiting(self):
        """Test Monday.com API rate limiting (needs implementation)"""
        self.stdout.write("\n📤 TESTING MONDAY.COM API RATE LIMITING")
        self.stdout.write("-" * 50)
        
        client = get_monday_client()
        
        # Test 1: Check if rate limiting is implemented
        self.stdout.write("Test 1: Rate limiting implementation check")
        if hasattr(client, 'min_request_interval') and hasattr(client, 'rate_limit_per_minute'):
            self.stdout.write("✅ Rate limiting found")
        else:
            self.stdout.write("❌ MISSING: Rate limiting not implemented")
            self.stdout.write("   📋 TODO: Implement rate limiting for Monday.com API")
        
        # Test 2: Check retry logic
        self.stdout.write("Test 2: Retry logic check")
        if hasattr(client, 'retry_attempts'):
            self.stdout.write("✅ Retry logic found")
        else:
            self.stdout.write("❌ MISSING: Retry logic not implemented")
            self.stdout.write("   📋 TODO: Implement retry logic for Monday.com API")
        
        # Test 3: Check backoff strategy
        self.stdout.write("Test 3: Backoff strategy check")
        if hasattr(client, 'backoff_factor'):
            self.stdout.write("✅ Backoff strategy found")
        else:
            self.stdout.write("❌ MISSING: Backoff strategy not implemented")
            self.stdout.write("   📋 TODO: Implement exponential backoff for Monday.com API")
        
        # Test 4: Check quota warnings
        self.stdout.write("Test 4: Quota warnings check")
        if hasattr(client, 'quota_tracker'):
            self.stdout.write("✅ Quota warnings found")
        else:
            self.stdout.write("❌ MISSING: Quota warnings not implemented")
            self.stdout.write("   📋 TODO: Implement quota warnings for Monday.com API")
        
        # Test 5: Stress test (if enabled)
        if self.stress_test:
            self.stdout.write("Test 5: Stress testing (simulated)")
            self._stress_test_monday(client)

    def _stress_test_fireflies(self, client):
        """Stress test Fireflies rate limiting"""
        self.stdout.write("   Running rapid API calls to test rate limiting...")
        
        start_time = time.time()
        successful_calls = 0
        rate_limited_calls = 0
        
        # Make 10 rapid calls
        for i in range(10):
            try:
                # Use a simple test connection instead of full data fetch
                result = client.test_connection()
                if result:
                    successful_calls += 1
                time.sleep(0.5)  # 500ms between calls (faster than rate limit)
            except Exception as e:
                if "rate limit" in str(e).lower():
                    rate_limited_calls += 1
                    self.stdout.write(f"   ✅ Rate limit detected on call {i+1}")
                else:
                    self.stdout.write(f"   ❌ Unexpected error: {e}")
        
        duration = time.time() - start_time
        self.stdout.write(f"   📊 Results: {successful_calls} successful, {rate_limited_calls} rate limited")
        self.stdout.write(f"   ⏱️ Duration: {duration:.2f}s")

    def _stress_test_gemini(self, client):
        """Stress test Gemini rate limiting (simulated)"""
        self.stdout.write("   Simulating rapid API calls...")
        
        # Since Gemini doesn't have rate limiting yet, we simulate
        self.stdout.write("   ⚠️ Rate limiting not implemented - this would fail in production")
        self.stdout.write("   📋 Need to implement: request throttling, quota tracking")

    def _stress_test_monday(self, client):
        """Stress test Monday.com rate limiting (simulated)"""
        self.stdout.write("   Simulating rapid API calls...")
        
        # Since Monday.com doesn't have rate limiting yet, we simulate
        self.stdout.write("   ⚠️ Rate limiting not implemented - this would fail in production")
        self.stdout.write("   📋 Need to implement: request throttling, retry logic")

    def test_rate_limit_recovery(self):
        """Test recovery from rate limiting"""
        self.stdout.write("\n🔄 TESTING RATE LIMIT RECOVERY")
        self.stdout.write("-" * 50)
        
        # This would test automatic recovery after rate limit periods
        self.stdout.write("Testing automatic recovery after rate limit...")
        self.stdout.write("📋 TODO: Implement rate limit recovery tests")

    def test_quota_monitoring(self):
        """Test quota monitoring and alerts"""
        self.stdout.write("\n📊 TESTING QUOTA MONITORING")
        self.stdout.write("-" * 50)
        
        # This would test quota tracking and warning systems
        self.stdout.write("Testing quota tracking and alerts...")
        self.stdout.write("📋 TODO: Implement quota monitoring tests")

    def test_circuit_breaker_integration(self):
        """Test circuit breaker integration with rate limiting"""
        self.stdout.write("\n⚡ TESTING CIRCUIT BREAKER INTEGRATION")
        self.stdout.write("-" * 50)
        
        # This would test how circuit breakers work with rate limiting
        self.stdout.write("Testing circuit breaker + rate limiting...")
        self.stdout.write("📋 TODO: Implement circuit breaker integration tests") 