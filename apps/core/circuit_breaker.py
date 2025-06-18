"""
Circuit Breaker Pattern Implementation
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger('apps.core.circuit_breaker')


class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, 
                 timeout: int = 60, success_threshold: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        
        self._lock = threading.Lock()
    
    def can_execute(self) -> bool:
        with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            elif self.state == CircuitBreakerState.OPEN:
                if (self.last_failure_time and 
                    datetime.utcnow() - self.last_failure_time >= timedelta(seconds=self.timeout)):
                    self.state = CircuitBreakerState.HALF_OPEN
                    return True
                return False
            elif self.state == CircuitBreakerState.HALF_OPEN:
                return True
            return False
    
    def record_success(self):
        with self._lock:
            self.last_success_time = datetime.utcnow()
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
    
    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            if (self.state == CircuitBreakerState.CLOSED and 
                self.failure_count >= self.failure_threshold):
                self.state = CircuitBreakerState.OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        if not self.can_execute():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise e


class CircuitBreakerRegistry:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_or_create(self, name: str, **kwargs) -> CircuitBreaker:
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self.circuit_breakers[name]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuit breakers"""
        stats = {}
        for name, breaker in self.circuit_breakers.items():
            stats[name] = {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'success_count': breaker.success_count,
                'last_failure_time': breaker.last_failure_time.isoformat() if breaker.last_failure_time else None,
                'last_success_time': breaker.last_success_time.isoformat() if breaker.last_success_time else None,
                'failure_threshold': breaker.failure_threshold,
                'timeout': breaker.timeout
            }
        
        return {
            'total_breakers': len(self.circuit_breakers),
            'breakers': stats
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Alias for get_all_stats for backward compatibility"""
        return self.get_all_stats() 