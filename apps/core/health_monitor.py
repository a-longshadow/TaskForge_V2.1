"""
Health Monitoring System
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import requests

logger = logging.getLogger('apps.core.health_monitor')


class HealthCheck:
    """Individual health check result"""
    
    def __init__(self, name: str, status: str, message: str = "", 
                 details: Dict[str, Any] = None, duration: float = 0.0):
        self.name = name
        self.status = status  # 'healthy', 'unhealthy', 'warning'
        self.message = message
        self.details = details or {}
        self.duration = duration
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'duration': self.duration,
            'timestamp': self.timestamp.isoformat()
        }


class HealthMonitor:
    """Health monitoring system for all components"""
    
    _instance = None
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.is_initialized = False
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def initialize(cls):
        instance = cls.get_instance()
        if not instance.is_initialized:
            instance.is_initialized = True
            logger.info("HealthMonitor initialized")
    
    def check_database(self) -> HealthCheck:
        """Check database connectivity"""
        start_time = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            duration = time.time() - start_time
            return HealthCheck(
                name="database",
                status="healthy",
                message="Database connection successful",
                details={"query_duration": duration},
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheck(
                name="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                duration=duration
            )
    
    def check_cache(self) -> HealthCheck:
        """Check cache connectivity"""
        start_time = time.time()
        try:
            test_key = f"health_check_{int(time.time())}"
            test_value = "test"
            
            cache.set(test_key, test_value, timeout=10)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            duration = time.time() - start_time
            
            if retrieved_value == test_value:
                return HealthCheck(
                    name="cache",
                    status="healthy",
                    message="Cache working correctly",
                    duration=duration
                )
            else:
                return HealthCheck(
                    name="cache",
                    status="unhealthy",
                    message="Cache not storing/retrieving correctly",
                    duration=duration
                )
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheck(
                name="cache",
                status="unhealthy",
                message=f"Cache error: {str(e)}",
                duration=duration
            )
    
    def check_external_api(self, api_name: str, url: str, timeout: int = 10) -> HealthCheck:
        """Check external API connectivity"""
        start_time = time.time()
        try:
            response = requests.get(url, timeout=timeout)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                return HealthCheck(
                    name=f"api_{api_name}",
                    status="healthy",
                    message=f"{api_name} API is accessible",
                    details={"status_code": response.status_code, "response_time": duration},
                    duration=duration
                )
            else:
                return HealthCheck(
                    name=f"api_{api_name}",
                    status="warning",
                    message=f"{api_name} API returned status {response.status_code}",
                    details={"status_code": response.status_code},
                    duration=duration
                )
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheck(
                name=f"api_{api_name}",
                status="unhealthy",
                message=f"{api_name} API error: {str(e)}",
                duration=duration
            )
    
    def check_all_modules(self) -> Dict[str, HealthCheck]:
        """Check health of all system modules"""
        checks = {}
        
        # Core system checks
        checks['database'] = self.check_database()
        checks['cache'] = self.check_cache()
        
        # External API checks
        api_configs = getattr(settings, 'EXTERNAL_APIS', {})
        for api_name, config in api_configs.items():
            if config.get('BASE_URL'):
                checks[f'api_{api_name.lower()}'] = self.check_external_api(
                    api_name.lower(), 
                    config['BASE_URL'],
                    config.get('TIMEOUT', 10)
                )
        
        return checks
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        checks = self.check_all_modules()
        
        # Determine overall status
        statuses = [check.status for check in checks.values()]
        if any(status == 'unhealthy' for status in statuses):
            overall_status = 'unhealthy'
        elif any(status == 'warning' for status in statuses):
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {name: check.to_dict() for name, check in checks.items()},
            'summary': {
                'total_checks': len(checks),
                'healthy': sum(1 for check in checks.values() if check.status == 'healthy'),
                'warnings': sum(1 for check in checks.values() if check.status == 'warning'),
                'unhealthy': sum(1 for check in checks.values() if check.status == 'unhealthy'),
            }
        }


# Convenience functions
def get_system_health() -> Dict[str, Any]:
    """Get current system health"""
    monitor = HealthMonitor.get_instance()
    return monitor.get_system_health()


def check_database_health() -> HealthCheck:
    """Check database health"""
    monitor = HealthMonitor.get_instance()
    return monitor.check_database()


def check_cache_health() -> HealthCheck:
    """Check cache health"""
    monitor = HealthMonitor.get_instance()
    return monitor.check_cache() 