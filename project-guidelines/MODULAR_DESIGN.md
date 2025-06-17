# Modular Design & Independence

## Core Principle: "Completely Unpluggable"

Each stage/module is completely independent and can fail without cascading effects. Modules communicate through well-defined interfaces and can be deployed, scaled, and maintained separately.

## Module Architecture

### Directory Structure
```
TaskForge/
├── modules/
│   ├── ingestion/          # Fireflies API + storage
│   │   ├── __init__.py
│   │   ├── api.py         # Independent service
│   │   ├── health.py      # Health check endpoint
│   │   ├── config.py      # Module-specific config
│   │   ├── tests/         # Module-specific tests
│   │   └── requirements.txt
│   ├── processing/         # AI task extraction  
│   │   ├── __init__.py
│   │   ├── ai_service.py  # Independent service
│   │   ├── health.py      # Health check endpoint
│   │   ├── config.py      # Module-specific config
│   │   ├── tests/         # Module-specific tests
│   │   └── requirements.txt
│   ├── review/            # Human review dashboard
│   │   ├── __init__.py
│   │   ├── dashboard.py   # Independent service
│   │   ├── health.py      # Health check endpoint
│   │   ├── config.py      # Module-specific config
│   │   ├── tests/         # Module-specific tests
│   │   └── requirements.txt
│   └── delivery/          # Monday.com integration
│       ├── __init__.py
│       ├── monday_api.py  # Independent service
│       ├── health.py      # Health check endpoint
│       ├── config.py      # Module-specific config
│       ├── tests/         # Module-specific tests
│       └── requirements.txt
```

## Inter-Module Communication

### Event-Based Decoupling
```python
# core/event_bus.py
class EventBus:
    def __init__(self):
        self.subscribers = {}
        self.event_queue = []
    
    def publish(self, event_type: str, data: dict):
        """Publish event - modules subscribe to what they need"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow(),
            'id': str(uuid.uuid4())
        }
        
        # Queue event if subscribers are offline
        self.event_queue.append(event)
        
        # Notify active subscribers
        for subscriber in self.subscribers.get(event_type, []):
            try:
                subscriber.handle_event(event)
            except Exception:
                # Subscriber failure doesn't affect publisher
                logging.error(f"Subscriber {subscriber} failed")
    
    def subscribe(self, event_type: str, handler):
        """Subscribe to specific event types"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
```

### Event Types
```python
# Event catalog
EVENTS = {
    'transcript.ingested': 'New transcript available for processing',
    'task.extracted': 'AI extracted tasks from transcript',
    'task.reviewed': 'Human reviewed task (approved/rejected)',
    'task.delivered': 'Task pushed to Monday.com',
    'module.health_check': 'Module health status update'
}
```

### Module Interface Contract
```python
# core/module_interface.py
class ModuleInterface:
    def __init__(self, module_name: str):
        self.name = module_name
        self.event_bus = EventBus()
        
    def health_check(self) -> dict:
        """Standard health check - all modules must implement"""
        return {
            'module': self.name,
            'status': 'healthy',
            'timestamp': datetime.utcnow(),
            'dependencies': self.check_dependencies()
        }
    
    def check_dependencies(self) -> dict:
        """Check external dependencies (APIs, DB, etc.)"""
        raise NotImplementedError
    
    def start(self):
        """Start module services"""
        raise NotImplementedError
        
    def stop(self):
        """Graceful shutdown"""
        raise NotImplementedError
```

## Circuit Breaker Pattern

### Implementation
```python
# core/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
    
    def reset(self):
        self.failure_count = 0
        self.state = 'CLOSED'

# Usage decorator
@circuit_breaker(failure_threshold=3, timeout=30)
def call_processing_module():
    # If processing fails 3 times, skip and queue for later
    # System continues without this module
    pass
```

## Independent Deployment

### Module Versioning
```yaml
# deployment/module_versions.yml
modules:
  ingestion: 
    version: v1.2.3
    port: 5001
    replicas: 2
  processing: 
    version: v1.1.8
    port: 5002
    replicas: 3
  review: 
    version: v1.3.1
    port: 5003
    replicas: 1
  delivery: 
    version: v1.0.9
    port: 5004
    replicas: 2
```

### Module-Specific Deployment
```bash
# Deploy individual modules
./deploy.sh --module=ingestion --version=v1.2.4
./deploy.sh --module=processing --version=v1.2.0

# Rollback individual modules
./deploy.sh --module=ingestion --rollback --to-version=v1.2.3
```

## Failure Isolation

### Graceful Degradation
```python
# If ingestion module fails
class IngestionFailureHandler:
    def handle_failure(self):
        # Queue transcript requests for later
        # Continue with existing data
        # Alert operations team
        # System remains functional
        pass

# If processing module fails  
class ProcessingFailureHandler:
    def handle_failure(self):
        # Queue transcripts for processing
        # Use cached/previous tasks
        # Alert admin for manual review
        # Review module still works
        pass
```

### Health Monitoring
```python
# core/health_monitor.py
class HealthMonitor:
    def __init__(self):
        self.modules = ['ingestion', 'processing', 'review', 'delivery']
    
    def check_all_modules(self):
        health_status = {}
        for module in self.modules:
            try:
                status = self.check_module_health(module)
                health_status[module] = status
            except Exception:
                health_status[module] = {'status': 'unhealthy'}
                # Log but don't fail other checks
        return health_status
    
    def check_module_health(self, module_name):
        # Each module exposes /health endpoint
        response = requests.get(f'http://localhost:500{module_port}/health')
        return response.json()
```

## Data Isolation

### Module-Specific Tables
```sql
-- Each module owns its data
-- ingestion module
CREATE TABLE ingestion_logs (id, transcript_id, status, timestamp);
CREATE TABLE ingestion_queue (id, fireflies_id, retry_count);

-- processing module  
CREATE TABLE processing_logs (id, transcript_id, ai_response, timestamp);
CREATE TABLE processing_queue (id, transcript_id, priority);

-- review module
CREATE TABLE review_sessions (id, user_id, tasks_reviewed, timestamp);

-- delivery module
CREATE TABLE delivery_logs (id, task_id, monday_response, timestamp);
```

### Shared Data Access
```python
# Shared data through well-defined APIs only
class SharedDataAccess:
    def get_transcript(self, transcript_id):
        # Only expose what's needed
        return {
            'id': transcript_id,
            'content': self.sanitized_content(),
            'metadata': self.safe_metadata()
        }
    
    def update_task_status(self, task_id, status):
        # Controlled updates only
        allowed_statuses = ['pending', 'approved', 'rejected', 'delivered']
        if status in allowed_statuses:
            # Update through event bus
            self.event_bus.publish('task.status_changed', {
                'task_id': task_id,
                'status': status
            })
```

## Module Independence Testing

### Isolation Tests
```python
# Test each module independently
class TestModuleIsolation:
    def test_ingestion_without_processing(self):
        # Ingestion should work even if processing is down
        pass
    
    def test_processing_without_delivery(self):
        # Processing should queue results if delivery is down
        pass
    
    def test_review_without_delivery(self):
        # Review should work independently
        pass
```

### Integration Tests
```python
# Test module communication
class TestModuleCommunication:
    def test_event_bus_delivery(self):
        # Events should be delivered reliably
        pass
    
    def test_circuit_breaker_isolation(self):
        # Failures should not cascade
        pass
``` 