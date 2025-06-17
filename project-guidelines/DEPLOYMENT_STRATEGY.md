# Deployment Strategy & Rollback Procedures

## Deployment Architecture (No Docker)

### Production Environment: Render.com
- **Web Service**: Django application
- **Database**: PostgreSQL managed service  
- **Background Jobs**: Celery with Redis
- **Static Assets**: Served by Django + WhiteNoise
- **Environment**: Python 3.11+

### Local Development Environment
- **Database**: PostgreSQL (Homebrew/native install)
- **Runtime**: Python 3.11+ (pyenv recommended)
- **Background Jobs**: Celery workers
- **Development Server**: Django development server

## Environment Parity Strategy

### Runtime Alignment
```bash
# Local environment setup
pyenv install 3.11.7
pyenv local 3.11.7
pip install -r requirements.txt

# Match production Python version exactly
echo "python-3.11.7" > .python-version
```

### Database Parity
```bash
# Local PostgreSQL matches production version
brew install postgresql@15
brew services start postgresql@15

# Same schema, same data types
psql -c "CREATE DATABASE taskforge_local;"
python manage.py migrate
```

### Configuration Management
```python
# config.py - Environment-specific settings
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URL = 'postgresql://localhost/taskforge_local'
    
class ProductionConfig(Config):
    DEBUG = False
    # Uses Render's environment variables
```

## Render.com Deployment Configuration

### render.yaml
```yaml
services:
  - type: web
    name: taskforge-web
    env: python
    plan: starter
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate"
    startCommand: "gunicorn taskforge.wsgi:application"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.7
      - key: DATABASE_URL
        fromDatabase:
          name: taskforge-db
          property: connectionString
      - key: DJANGO_SETTINGS_MODULE
        value: taskforge.settings.production
        
  - type: worker
    name: taskforge-worker
    env: python
    plan: starter
    buildCommand: "pip install -r requirements.txt"
    startCommand: "celery -A taskforge worker -l info"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: taskforge-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: taskforge-redis

databases:
  - name: taskforge-db
    databaseName: taskforge
    user: taskforge_user
    plan: starter
    
cron:
  - name: daily-sync
    schedule: "59 23 * * *"
    command: "python scripts/daily_sync.py"
  - name: auto-push
    schedule: "0 * * * *"
    command: "python scripts/auto_push.py"
```

## Deployment Pipeline

### Git-Based Deployment
```bash
# Deploy to production
git push origin main
# → Triggers automatic Render deployment
# → Zero-downtime rolling deployment
# → Health checks validate deployment
```

### Pre-Deployment Checks
```bash
# Local validation before pushing
./scripts/pre_deploy_check.sh

# Checks performed:
# - All tests pass
# - Linting clean
# - Database migrations ready
# - Environment variables set
# - Dependencies up to date
```

### Health Check Endpoint
```python
# app/routes/health.py
@app.route('/health')
def health_check():
    """Comprehensive health check for deployment validation"""
    checks = {
        'database': check_database_connection(),
        'fireflies_api': check_fireflies_api(),
        'gemini_api': check_gemini_api(),
        'monday_api': check_monday_api(),
        'scheduler': check_scheduler_status()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat(),
        'version': get_app_version()
    }), status_code
```

## Database Migration Strategy

### Migration Management
```bash
# Create migration
flask db migrate -m "Add new table for feature X"

# Review migration before applying
cat migrations/versions/[migration_file].py

# Apply migration (local)
flask db upgrade

# Apply migration (production - automatic on deploy)
# Render runs flask db upgrade during deployment
```

### Migration Safety
```python
# Safe migration patterns
def upgrade():
    # Add new columns as nullable first
    op.add_column('action_items', sa.Column('priority', sa.String(20), nullable=True))
    
    # Populate data
    op.execute("UPDATE action_items SET priority = 'medium' WHERE priority IS NULL")
    
    # Then make NOT NULL if needed
    op.alter_column('action_items', 'priority', nullable=False)

def downgrade():
    # Always provide downgrade path
    op.drop_column('action_items', 'priority')
```

## Rollback Procedures

### Git-Based Rollback
```bash
# Quick rollback to last known good state
git log --oneline -10  # Find last good commit
git revert <commit-hash>
git push origin main

# Or rollback to specific tag
git checkout tags/v1.2.3
git checkout -b rollback-v1.2.3
git push origin rollback-v1.2.3
```

### Render Dashboard Rollback
```bash
# One-click rollback in Render UI
# 1. Go to Render dashboard
# 2. Select service
# 3. Choose "Rollback" from deployments
# 4. Select previous deployment
# 5. Confirm rollback
```

### Database Rollback
```bash
# Database rollback (if needed)
# 1. Enable maintenance mode
flask maintenance enable

# 2. Backup current state
pg_dump $DATABASE_URL > backup_before_rollback.sql

# 3. Rollback migrations
flask db downgrade <revision>

# 4. Verify rollback
flask db current

# 5. Disable maintenance mode
flask maintenance disable
```

### Emergency Rollback Script
```bash
#!/bin/bash
# scripts/emergency_rollback.sh

echo "EMERGENCY ROLLBACK INITIATED"
echo "Timestamp: $(date)"

# 1. Enable maintenance mode
echo "Enabling maintenance mode..."
curl -X POST "$APP_URL/admin/maintenance/enable"

# 2. Rollback to last good deployment
echo "Rolling back code..."
git reset --hard $LAST_GOOD_COMMIT
git push --force origin main

# 3. Wait for deployment
echo "Waiting for deployment..."
sleep 60

# 4. Health check
echo "Performing health check..."
if curl -f "$APP_URL/health"; then
    echo "Health check passed"
    curl -X POST "$APP_URL/admin/maintenance/disable"
    echo "Rollback completed successfully"
else
    echo "Health check failed - manual intervention required"
    exit 1
fi
```

## Monitoring & Observability

### Deployment Monitoring
```python
# Track deployment metrics
class DeploymentMetrics:
    def __init__(self):
        self.start_time = datetime.utcnow()
        
    def record_deployment_start(self):
        logger.info(f"Deployment started at {self.start_time}")
        
    def record_deployment_complete(self):
        duration = datetime.utcnow() - self.start_time
        logger.info(f"Deployment completed in {duration.total_seconds()}s")
        
    def record_health_check(self, status):
        logger.info(f"Health check: {status}")
```

### Structured Logging
```python
# Logging configuration
import logging
from logging.handlers import RotatingFileHandler

# Production logging
if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/taskforge.log', 
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Performance Monitoring
```python
# Request timing middleware
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        app.logger.info(f"Request duration: {duration:.3f}s")
    return response
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest
    - name: Run linter
      run: flake8 .
    - name: Type check
      run: mypy .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to Render
      run: |
        # Render automatically deploys on push to main
        echo "Deployment triggered by push to main"
```

## Feature Flags & Gradual Rollouts

### Feature Flag Implementation
```python
# Feature flag system
class FeatureFlags:
    def __init__(self):
        self.flags = {
            'new_ai_model': False,
            'enhanced_dashboard': False,
            'monday_v2_api': False
        }
    
    def is_enabled(self, flag_name, user_id=None):
        # Check environment variable override
        env_flag = os.environ.get(f'FEATURE_{flag_name.upper()}')
        if env_flag:
            return env_flag.lower() == 'true'
            
        # Check user-specific flags
        if user_id and self.is_beta_user(user_id):
            return True
            
        return self.flags.get(flag_name, False)
```

### Canary Deployment Strategy
```python
# Gradual rollout decorator
def canary_deployment(percentage=10):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if random.randint(1, 100) <= percentage:
                return func(*args, **kwargs)
            else:
                return legacy_function(*args, **kwargs)
        return wrapper
    return decorator

@canary_deployment(percentage=25)
def new_ai_processing_logic():
    # New feature rolled out to 25% of users
    pass
```

## Maintenance Mode

### Maintenance Mode Implementation
```python
# Maintenance mode middleware
class MaintenanceMode:
    def __init__(self, app):
        self.app = app
        self.enabled = False
        
    def __call__(self, environ, start_response):
        if self.enabled:
            response = self.maintenance_response()
            start_response('503 Service Unavailable', [
                ('Content-Type', 'text/html'),
                ('Retry-After', '3600')
            ])
            return [response.encode('utf-8')]
        return self.app(environ, start_response)
    
    def maintenance_response(self):
        return """
        <html>
        <head><title>Maintenance Mode</title></head>
        <body>
            <h1>System Maintenance</h1>
            <p>TaskForge is currently undergoing maintenance.</p>
            <p>Please try again in a few minutes.</p>
        </body>
        </html>
        """
```

## Backup & Recovery

### Database Backup Strategy
```bash
# Automated daily backups
pg_dump $DATABASE_URL > backups/taskforge_$(date +%Y%m%d).sql
aws s3 cp backups/taskforge_$(date +%Y%m%d).sql s3://taskforge-backups/

# Retention policy: 30 days
find backups/ -name "*.sql" -mtime +30 -delete
```

### Recovery Procedures
```bash
# Restore from backup
pg_restore --verbose --clean --no-acl --no-owner -h localhost -U postgres -d taskforge backup.sql

# Verify restore
psql -d taskforge -c "SELECT COUNT(*) FROM transcripts;"
``` 