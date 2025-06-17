# Development Workflow

## Overview

This document outlines the complete development workflow for TaskForge using Django with Guardian system integration. Every development action must follow this workflow to ensure zero regressions and maintain AI knowledge continuity.

## Pre-Development Setup

### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/[username]/TaskForge_V2.1.git
cd TaskForge_V2.1

# Set up Python environment
pyenv install 3.11.7
pyenv local 3.11.7
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
brew install postgresql@15
brew services start postgresql@15
createdb taskforge_local

# Initialize Guardian system
./guardian.sh --init --create-knowledge-base
```

### 2. Django Initial Setup
```bash
# Guardian-protected Django setup
./guardian.sh --django-command "migrate"
./guardian.sh --django-command "createsuperuser"
./guardian.sh --django-command "collectstatic --noinput"

# Validate setup
python manage.py health_check
```

### 3. Knowledge Base Initialization
```bash
# Initialize AI knowledge base
python manage.py update_knowledge_base --initial
./scripts/validate_ai_knowledge.sh

# Verify Guardian integration
./guardian.sh --validate-knowledge --ai-agent-test
```

## Daily Development Workflow

### Phase 1: Guardian Foundation (COMPLETED FIRST)

#### Step 1.1: Initialize Guardian System
```bash
# Create Guardian script
./guardian.sh --setup-foundation --approval-required

# Verify Guardian functionality
./guardian.sh --test-all-safeguards
```

#### Step 1.2: Knowledge Base Setup
```bash
# Create knowledge structure
mkdir -p .ai-knowledge
./guardian.sh --create-knowledge-base

# Initialize knowledge files
python manage.py update_knowledge_base --initial
```

#### Step 1.3: Basic Django Project
```bash
# Create Django project with Guardian protection
./guardian.sh --django-command "startproject taskforge ."

# Create core app
./guardian.sh --django-command "startapp core apps/core"

# Run initial migrations
./guardian.sh --migrate
```

### Phase 2: Core Infrastructure

#### Step 2.1: Authentication Setup
```bash
# Create authentication app
./guardian.sh --django-command "startapp authentication apps/authentication"

# Create custom user model
# Edit apps/authentication/models.py (Guardian will track changes)

# Create and run migrations
./guardian.sh --django-command "makemigrations authentication"
./guardian.sh --migrate
```

#### Step 2.2: Admin Panel Customization
```bash
# Create administration app
./guardian.sh --django-command "startapp administration apps/administration"

# Customize admin interface
# Edit apps/administration/admin.py

# Create admin templates
mkdir -p templates/admin
# Edit templates as needed
```

#### Step 2.3: Database Schema
```bash
# Create models for each app
# Guardian tracks all file changes

# Generate migrations
./guardian.sh --django-command "makemigrations"

# Review migrations before applying
cat apps/*/migrations/*.py

# Apply migrations with Guardian protection
./guardian.sh --migrate
```

### Phase 3: Individual Modules

#### Step 3.1: Ingestion Module
```bash
# Create ingestion app
./guardian.sh --django-command "startapp ingestion apps/ingestion"

# Implement Fireflies integration
# Edit apps/ingestion/services.py
# Edit apps/ingestion/models.py
# Edit apps/ingestion/tasks.py

# Guardian validates each change
./guardian.sh --module=ingestion --validate-integration

# Test Fireflies API connection
python manage.py test_fireflies_api --dry-run
```

#### Step 3.2: Processing Module
```bash
# Create processing app
./guardian.sh --django-command "startapp processing apps/processing"

# Implement Gemini AI integration
# Edit apps/processing/ai_service.py
# Edit apps/processing/models.py
# Edit apps/processing/tasks.py

# Guardian validates AI integration
./guardian.sh --module=processing --test-ai-integration

# Test AI processing
python manage.py test_ai_processing --sample-data
```

#### Step 3.3: Review Module
```bash
# Create review app
./guardian.sh --django-command "startapp review apps/review"

# Implement review dashboard
# Edit apps/review/views.py
# Edit apps/review/templates/
# Edit apps/review/static/

# Guardian validates UI components
./guardian.sh --module=review --test-ui-components

# Test review workflow
python manage.py test_review_workflow
```

#### Step 3.4: Delivery Module
```bash
# Create delivery app
./guardian.sh --django-command "startapp delivery apps/delivery"

# Implement Monday.com integration
# Edit apps/delivery/services.py
# Edit apps/delivery/models.py
# Edit apps/delivery/tasks.py

# Guardian validates external API
./guardian.sh --module=delivery --test-monday-integration

# Test delivery system
python manage.py test_delivery_system --dry-run
```

### Phase 4: Integration & Deployment

#### Step 4.1: System Integration
```bash
# Run full integration tests
./guardian.sh --integration-test --full-workflow

# Test inter-module communication
python manage.py test_module_communication

# Validate event bus
python manage.py test_event_bus
```

#### Step 4.2: Production Deployment
```bash
# Pre-deployment checks
./scripts/pre_deploy_check.sh

# Deploy with Guardian protection
./guardian.sh --deploy-production --with-rollback-plan

# Validate production deployment
./guardian.sh --validate-production --health-check-all
```

## Code Change Workflow

### 1. Before Making Changes
```bash
# Ensure clean git state
git status

# Update knowledge base
python manage.py update_knowledge_base

# Validate AI understanding
./scripts/validate_ai_knowledge.sh

# Create backup snapshot
./scripts/create_snapshot.sh
```

### 2. Making Changes
```bash
# All changes must be Guardian-protected
./guardian.sh --start-change-session

# Make your code changes
# Edit files as needed

# Guardian tracks all changes automatically
```

### 3. Testing Changes
```bash
# Run module-specific tests
python manage.py test apps.ingestion

# Run integration tests
python manage.py test tests.test_integration

# Guardian validates tests pass
./guardian.sh --validate-tests --all-modules
```

### 4. Committing Changes
```bash
# Guardian generates change impact report
./guardian.sh --generate-impact-report

# Review impact report
cat .guardian/impact_report.md

# Commit with Guardian protection
./guardian.sh --commit --message "feat: add new feature"

# Guardian updates knowledge base automatically
```

### 5. Deployment
```bash
# Guardian pre-deployment validation
./guardian.sh --pre-deploy-check

# Deploy to staging
./guardian.sh --deploy-staging

# Run production tests
./guardian.sh --test-production-readiness

# Deploy to production (with approval gate)
./guardian.sh --deploy-production --approval-required
```

## Django Management Commands

### Guardian-Enhanced Commands

#### Database Operations
```bash
# Migrations with Guardian protection
./guardian.sh --migrate
./guardian.sh --django-command "makemigrations"
./guardian.sh --django-command "showmigrations"

# Database management
./guardian.sh --django-command "dbshell"
./guardian.sh --django-command "dumpdata > backup.json"
./guardian.sh --django-command "loaddata backup.json"
```

#### User Management
```bash
# Create superuser
./guardian.sh --django-command "createsuperuser"

# Create regular admin user
python manage.py create_admin_user --email admin@example.com

# Whitelist user for registration
python manage.py whitelist_user --email user@example.com
```

#### System Administration
```bash
# Health checks
python manage.py health_check --comprehensive
python manage.py check_api_connections

# System maintenance
python manage.py cleanup_old_logs
python manage.py update_api_keys
python manage.py system_status
```

#### Development Tools
```bash
# Start development server
python manage.py runserver

# Start Celery worker
celery -A taskforge worker -l info

# Start Celery beat (scheduler)
celery -A taskforge beat -l info

# Django shell
python manage.py shell
```

## Testing Workflow

### 1. Unit Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.authentication
python manage.py test apps.ingestion

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### 2. Integration Tests
```bash
# Full system integration test
python manage.py test tests.test_integration

# API integration tests
python manage.py test_api_integrations

# Guardian system tests
python manage.py test tests.test_guardian_integration
```

### 3. Performance Tests
```bash
# Load testing
python manage.py test_performance --load-test

# Database performance
python manage.py test_db_performance

# API response times
python manage.py test_api_performance
```

## Monitoring & Maintenance

### 1. Daily Maintenance
```bash
# Update knowledge base
python manage.py update_knowledge_base --daily

# Check system health
python manage.py health_check --comprehensive

# Clean up logs
python manage.py cleanup_logs --older-than 30

# Backup database
python manage.py backup_database
```

### 2. Weekly Maintenance
```bash
# Update dependencies
pip list --outdated
./guardian.sh --update-dependencies --approval-required

# Security audit
python manage.py check --deploy
python manage.py audit_security

# Performance review
python manage.py performance_report --weekly
```

### 3. Monthly Maintenance
```bash
# Full system backup
./scripts/full_system_backup.sh

# Knowledge base validation
./scripts/validate_ai_knowledge.sh --comprehensive

# Guardian system audit
./guardian.sh --system-audit --monthly
```

## Emergency Procedures

### 1. Rollback
```bash
# Emergency rollback
./guardian.sh --emergency-rollback

# Rollback to specific commit
./guardian.sh --rollback --to-commit=<commit-hash>

# Rollback specific module
./guardian.sh --rollback-module=ingestion --to-version=v1.2.3
```

### 2. System Recovery
```bash
# Restore from backup
./scripts/restore_from_backup.sh --backup-id=<backup-id>

# Rebuild knowledge base
./scripts/rebuild_knowledge_base.sh

# Validate system integrity
./guardian.sh --validate-system-integrity
```

### 3. Hot Fixes
```bash
# Emergency hot fix
./guardian.sh --hotfix --bypass-approval

# Validate hot fix
./guardian.sh --validate-hotfix

# Deploy hot fix
./guardian.sh --deploy-hotfix --immediate
```

## Success Criteria Checklist

### Phase 1: Guardian Foundation
- [ ] Guardian script operational
- [ ] Knowledge base auto-maintained
- [ ] AI agent passes knowledge tests
- [ ] Basic Django app running
- [ ] Zero-regression guarantees active

### Phase 2: Core Infrastructure
- [ ] Authentication system working
- [ ] Admin panel customized
- [ ] Database migrations working
- [ ] Logging configured
- [ ] Health monitoring active

### Phase 3: Individual Modules
- [ ] Ingestion module operational
- [ ] Processing module working
- [ ] Review dashboard functional
- [ ] Delivery module working
- [ ] All modules independently deployable

### Phase 4: Integration & Deployment
- [ ] End-to-end workflow operational
- [ ] Production deployment successful
- [ ] Monitoring and alerting active
- [ ] Rollback procedures validated

This workflow ensures:
- **Guardian protection** at every step
- **Zero regression** guarantees
- **Complete AI knowledge** maintenance
- **Modular independence** 
- **Production readiness** 