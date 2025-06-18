"""
TaskForge Cache Manager
Centralized cache operations following Django best practices
"""

import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from django.core.cache import caches, cache
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings
from django.utils import timezone as django_timezone

logger = logging.getLogger('cache_operations')


class CacheManager:
    """
    Centralized cache manager for TaskForge
    Handles multiple cache backends with proper key management
    """
    
    def __init__(self):
        self.default_cache = caches['default']
        self.fireflies_cache = caches['fireflies']
        self.gemini_cache = caches['gemini']
        self.sessions_cache = caches['sessions']
        
        # Cache key prefixes from settings
        self.prefixes = getattr(settings, 'CACHE_KEY_PREFIXES', {})
        self.timeouts = getattr(settings, 'CACHE_TIMEOUTS', {})
    
    def _generate_cache_key(self, prefix: str, identifier: str, **kwargs) -> str:
        """
        Generate a consistent cache key with optional parameters
        """
        key_parts = [prefix, identifier]
        
        # Add optional parameters to key
        for key, value in sorted(kwargs.items()):
            if value is not None:
                key_parts.append(f"{key}:{value}")
        
        cache_key = "".join(key_parts)
        
        # Ensure key length doesn't exceed limits (memcached has 250 char limit)
        if len(cache_key) > 200:
            # Hash long keys to ensure consistency
            hash_key = hashlib.md5(cache_key.encode()).hexdigest()
            cache_key = f"{prefix}{hash_key}"
        
        return cache_key
    
    def _log_cache_operation(self, operation: str, key: str, hit: bool = None, size: int = None):
        """
        Log cache operations for monitoring and debugging
        """
        log_data = {
            'operation': operation,
            'key': key[:50] + '...' if len(key) > 50 else key,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        if hit is not None:
            log_data['hit'] = hit
        if size is not None:
            log_data['size_bytes'] = size
            
        logger.info(f"Cache {operation}: {log_data}")
    
    # Fireflies Cache Operations
    def get_fireflies_transcripts(self, force_refresh: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached Fireflies transcripts
        """
        key = self._generate_cache_key(
            self.prefixes.get('FIREFLIES_COMPREHENSIVE', 'fireflies:comprehensive:'),
            'all_transcripts'
        )
        
        if force_refresh:
            self.fireflies_cache.delete(key)
            self._log_cache_operation('DELETE', key)
            return None
        
        data = self.fireflies_cache.get(key)
        hit = data is not None
        self._log_cache_operation('GET', key, hit=hit)
        
        return data
    
    def set_fireflies_transcripts(self, transcripts: List[Dict[str, Any]], timeout: Optional[int] = None) -> bool:
        """
        Cache Fireflies transcripts with optional custom timeout
        """
        key = self._generate_cache_key(
            self.prefixes.get('FIREFLIES_COMPREHENSIVE', 'fireflies:comprehensive:'),
            'all_transcripts'
        )
        
        if timeout is None:
            timeout = self.timeouts.get('FIREFLIES_COMPREHENSIVE', 14400)  # 4 hours default
        
        try:
            # Add metadata
            cache_data = {
                'transcripts': transcripts,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'count': len(transcripts),
                'expires_at': (datetime.now(timezone.utc) + timedelta(seconds=timeout)).isoformat()
            }
            
            self.fireflies_cache.set(key, cache_data, timeout)
            
            data_size = len(json.dumps(cache_data, default=str))
            self._log_cache_operation('SET', key, size=data_size)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cache Fireflies transcripts: {e}")
            return False
    
    def get_fireflies_today(self, date: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get today's cached Fireflies transcripts
        """
        if date is None:
            date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        key = self._generate_cache_key(
            self.prefixes.get('FIREFLIES_TODAY', 'fireflies:today:'),
            date
        )
        
        data = self.fireflies_cache.get(key)
        hit = data is not None
        self._log_cache_operation('GET', key, hit=hit)
        
        return data
    
    def set_fireflies_today(self, transcripts: List[Dict[str, Any]], date: Optional[str] = None) -> bool:
        """
        Cache today's Fireflies transcripts
        """
        if date is None:
            date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        key = self._generate_cache_key(
            self.prefixes.get('FIREFLIES_TODAY', 'fireflies:today:'),
            date
        )
        
        timeout = self.timeouts.get('FIREFLIES_TODAY', 3600)  # 1 hour default
        
        try:
            cache_data = {
                'transcripts': transcripts,
                'date': date,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'count': len(transcripts)
            }
            
            self.fireflies_cache.set(key, cache_data, timeout)
            
            data_size = len(json.dumps(cache_data, default=str))
            self._log_cache_operation('SET', key, size=data_size)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cache today's Fireflies transcripts: {e}")
            return False
    
    # Gemini Cache Operations
    def get_gemini_extraction(self, transcript_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get cached Gemini extraction result
        """
        key = self._generate_cache_key(
            self.prefixes.get('GEMINI_EXTRACTION', 'gemini:extract:'),
            transcript_hash
        )
        
        data = self.gemini_cache.get(key)
        hit = data is not None
        self._log_cache_operation('GET', key, hit=hit)
        
        return data
    
    def set_gemini_extraction(self, transcript_hash: str, extraction_result: Dict[str, Any]) -> bool:
        """
        Cache Gemini extraction result
        """
        key = self._generate_cache_key(
            self.prefixes.get('GEMINI_EXTRACTION', 'gemini:extract:'),
            transcript_hash
        )
        
        timeout = self.timeouts.get('GEMINI_EXTRACTION', 1800)  # 30 minutes default
        
        try:
            cache_data = {
                'result': extraction_result,
                'transcript_hash': transcript_hash,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': (datetime.now(timezone.utc) + timedelta(seconds=timeout)).isoformat()
            }
            
            self.gemini_cache.set(key, cache_data, timeout)
            
            data_size = len(json.dumps(cache_data, default=str))
            self._log_cache_operation('SET', key, size=data_size)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cache Gemini extraction: {e}")
            return False
    
    # System Health Cache Operations
    def get_system_health(self) -> Optional[Dict[str, Any]]:
        """
        Get cached system health status
        """
        key = self._generate_cache_key(
            self.prefixes.get('SYSTEM_HEALTH', 'system:health:'),
            'status'
        )
        
        data = self.default_cache.get(key)
        hit = data is not None
        self._log_cache_operation('GET', key, hit=hit)
        
        return data
    
    def set_system_health(self, health_data: Dict[str, Any]) -> bool:
        """
        Cache system health status
        """
        key = self._generate_cache_key(
            self.prefixes.get('SYSTEM_HEALTH', 'system:health:'),
            'status'
        )
        
        timeout = self.timeouts.get('SYSTEM_HEALTH', 300)  # 5 minutes default
        
        try:
            cache_data = {
                'health': health_data,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': (datetime.now(timezone.utc) + timedelta(seconds=timeout)).isoformat()
            }
            
            self.default_cache.set(key, cache_data, timeout)
            self._log_cache_operation('SET', key)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cache system health: {e}")
            return False
    
    # API Status Cache Operations
    def get_api_status(self, api_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached API status
        """
        key = self._generate_cache_key(
            self.prefixes.get('API_STATUS', 'api:status:'),
            api_name
        )
        
        data = self.default_cache.get(key)
        hit = data is not None
        self._log_cache_operation('GET', key, hit=hit)
        
        return data
    
    def set_api_status(self, api_name: str, status_data: Dict[str, Any]) -> bool:
        """
        Cache API status
        """
        key = self._generate_cache_key(
            self.prefixes.get('API_STATUS', 'api:status:'),
            api_name
        )
        
        timeout = self.timeouts.get('API_STATUS', 600)  # 10 minutes default
        
        try:
            cache_data = {
                'status': status_data,
                'api_name': api_name,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': (datetime.now(timezone.utc) + timedelta(seconds=timeout)).isoformat()
            }
            
            self.default_cache.set(key, cache_data, timeout)
            self._log_cache_operation('SET', key)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cache API status for {api_name}: {e}")
            return False
    
    # Cache Management Operations
    def clear_all_caches(self) -> Dict[str, bool]:
        """
        Clear all cache backends
        """
        results = {}
        
        try:
            self.default_cache.clear()
            results['default'] = True
            self._log_cache_operation('CLEAR', 'default_cache')
        except Exception as e:
            logger.error(f"Failed to clear default cache: {e}")
            results['default'] = False
        
        try:
            self.fireflies_cache.clear()
            results['fireflies'] = True
            self._log_cache_operation('CLEAR', 'fireflies_cache')
        except Exception as e:
            logger.error(f"Failed to clear Fireflies cache: {e}")
            results['fireflies'] = False
        
        try:
            self.gemini_cache.clear()
            results['gemini'] = True
            self._log_cache_operation('CLEAR', 'gemini_cache')
        except Exception as e:
            logger.error(f"Failed to clear Gemini cache: {e}")
            results['gemini'] = False
        
        try:
            self.sessions_cache.clear()
            results['sessions'] = True
            self._log_cache_operation('CLEAR', 'sessions_cache')
        except Exception as e:
            logger.error(f"Failed to clear sessions cache: {e}")
            results['sessions'] = False
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and health information
        """
        stats = {
            'cache_backends': {
                'default': {
                    'location': str(settings.CACHES['default']['LOCATION']),
                    'timeout': settings.CACHES['default']['TIMEOUT'],
                },
                'fireflies': {
                    'location': str(settings.CACHES['fireflies']['LOCATION']),
                    'timeout': settings.CACHES['fireflies']['TIMEOUT'],
                },
                'gemini': {
                    'location': str(settings.CACHES['gemini']['LOCATION']),
                    'timeout': settings.CACHES['gemini']['TIMEOUT'],
                },
                'sessions': {
                    'location': str(settings.CACHES['sessions']['LOCATION']),
                    'timeout': settings.CACHES['sessions']['TIMEOUT'],
                },
            },
            'cache_health': {
                'default': self._test_cache_backend(self.default_cache),
                'fireflies': self._test_cache_backend(self.fireflies_cache),
                'gemini': self._test_cache_backend(self.gemini_cache),
                'sessions': self._test_cache_backend(self.sessions_cache),
            },
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        return stats
    
    def _test_cache_backend(self, cache_backend) -> Dict[str, Any]:
        """
        Test a cache backend's health
        """
        test_key = f"health_check_{datetime.now().timestamp()}"
        test_value = {"test": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        
        try:
            # Test set operation
            cache_backend.set(test_key, test_value, 60)
            
            # Test get operation
            retrieved = cache_backend.get(test_key)
            
            # Test delete operation
            cache_backend.delete(test_key)
            
            return {
                'healthy': retrieved is not None and retrieved.get('test') is True,
                'operations': ['set', 'get', 'delete'],
                'last_tested': datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'last_tested': datetime.now(timezone.utc).isoformat(),
            }
    
    def is_cache_stale(self, cache_type: str, identifier: str) -> bool:
        """
        Check if a cached item is stale based on its type and timeout settings
        """
        prefix_map = {
            'fireflies_comprehensive': 'FIREFLIES_COMPREHENSIVE',
            'fireflies_today': 'FIREFLIES_TODAY',
            'gemini_extraction': 'GEMINI_EXTRACTION',
            'system_health': 'SYSTEM_HEALTH',
            'api_status': 'API_STATUS',
        }
        
        if cache_type not in prefix_map:
            return True
        
        prefix_key = prefix_map[cache_type]
        prefix = self.prefixes.get(prefix_key, f"{cache_type}:")
        
        key = self._generate_cache_key(prefix, identifier)
        
        # Get the appropriate cache backend
        cache_backend = self.default_cache
        if cache_type.startswith('fireflies'):
            cache_backend = self.fireflies_cache
        elif cache_type.startswith('gemini'):
            cache_backend = self.gemini_cache
        
        data = cache_backend.get(key)
        
        if data is None:
            return True
        
        # Check if data has expiration info
        if isinstance(data, dict) and 'expires_at' in data:
            try:
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
                return datetime.now(timezone.utc) > expires_at
            except (ValueError, TypeError):
                return True
        
        # If no expiration info, consider it stale
        return True


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# Convenience functions for common operations
def cache_fireflies_transcripts(transcripts: List[Dict[str, Any]], timeout: Optional[int] = None) -> bool:
    """Cache Fireflies transcripts"""
    return get_cache_manager().set_fireflies_transcripts(transcripts, timeout)

def get_cached_fireflies_transcripts(force_refresh: bool = False) -> Optional[List[Dict[str, Any]]]:
    """Get cached Fireflies transcripts"""
    return get_cache_manager().get_fireflies_transcripts(force_refresh)

def cache_gemini_extraction(transcript_hash: str, result: Dict[str, Any]) -> bool:
    """Cache Gemini extraction result"""
    return get_cache_manager().set_gemini_extraction(transcript_hash, result)

def get_cached_gemini_extraction(transcript_hash: str) -> Optional[Dict[str, Any]]:
    """Get cached Gemini extraction result"""
    return get_cache_manager().get_gemini_extraction(transcript_hash)

def clear_all_caches() -> Dict[str, bool]:
    """Clear all cache backends"""
    return get_cache_manager().clear_all_caches()

def get_cache_stats() -> Dict[str, Any]:
    """Get comprehensive cache statistics"""
    return get_cache_manager().get_cache_stats() 