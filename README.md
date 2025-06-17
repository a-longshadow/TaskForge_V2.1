# TaskForge V2.1

**AI-Powered Task Management with Guardian System Protection**

TaskForge is a Django-based application that automatically extracts tasks from meeting transcripts using AI, provides human review capabilities, and delivers approved tasks to Monday.com. Built with zero-regression guarantees through the integrated Guardian system.

## 🚀 Quick Start

### Prerequisites
- Python 3.11.7
- PostgreSQL 15+
- Redis (for Celery)
- Git

### Installation

1. **Clone and Setup**
   ```bash
   git clone https://github.com/[username]/TaskForge_V2.1.git
   cd TaskForge_V2.1
   
   # Set up Python environment
   pyenv install 3.11.7
   pyenv local 3.11.7
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Install PostgreSQL (macOS)
   brew install postgresql@15
   brew services start postgresql@15
   
   # Create database
   createdb taskforge_local
   ```

3. **Guardian System Initialization**
   ```bash
   # Initialize Guardian safeguards
   ./guardian.sh --init
   
   # Validate Guardian setup
   ./guardian.sh --health-check
   ```

4. **Django Setup**
   ```bash
   # Run migrations with Guardian protection
   ./guardian.sh --migrate
   
   # Create superuser
   ./guardian.sh --django-command "createsuperuser"
   
   # Collect static files
   ./guardian.sh --collectstatic
   ```

5. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

## 🛡️ Guardian System

TaskForge includes a comprehensive Guardian system that ensures:
- **Zero Regressions**: All changes are protected by automated safeguards
- **AI Knowledge Persistence**: Complete project understanding maintained across devices
- **Human Approval Gates**: All code changes require explicit approval
- **Automatic Snapshots**: System state backed up before every change
- **Module Independence**: Each component can fail without cascading effects

### Guardian Commands
```bash
./guardian.sh --init                    # Initialize Guardian system
./guardian.sh --migrate                 # Protected Django migrations
./guardian.sh --django-command "cmd"    # Execute any Django command with protection
./guardian.sh --emergency-rollback     # Emergency system restoration
./guardian.sh --health-check           # Comprehensive system health check
```

## 🏗️ Architecture

### Core Philosophy: Human-on-Exception
- System defaults to "action first"
- Human intervention only for edge cases
- 18-hour review window for all extracted tasks
- Automatic processing with manual oversight

### System Components

1. **Ingestion Module** (Fireflies API)
   - 15-minute automated sync
   - Transcript storage in PostgreSQL JSONB
   - Error handling and retry logic

2. **Processing Module** (Gemini AI)
   - 5-minute AI processing cycles
   - Task extraction and post-processing
   - Daily briefing generation

3. **Review Module** (Human Dashboard)
   - Real-time task review interface
   - 18-hour review window tracking
   - Approve/reject/edit functionality

4. **Delivery Module** (Monday.com API)
   - Automatic task delivery >18 hours
   - Comprehensive logging and tracking
   - Error handling and retries

### Technology Stack
- **Framework**: Django 4.2.7
- **Database**: PostgreSQL 15+
- **Background Jobs**: Celery + Redis
- **Frontend**: Django Templates + HTMX + Tailwind CSS
- **Deployment**: Render.com
- **Monitoring**: Guardian System + Django Logging

## 📁 Project Structure

```
TaskForge_V2.1/
├── guardian.sh                 # Guardian system script
├── .ai-knowledge/             # AI knowledge base
├── project-guidelines/        # Development guidelines
├── taskforge/                 # Django project
├── apps/                      # Django applications
│   ├── core/                 # Guardian integration
│   ├── authentication/       # User management
│   ├── administration/       # Admin panel
│   ├── ingestion/            # Fireflies integration
│   ├── processing/           # AI processing
│   ├── review/               # Human review
│   └── delivery/             # Monday.com integration
├── templates/                # Global templates
├── static/                   # Static files
└── tests/                    # Integration tests
```

## 🔧 Development Workflow

All development must follow the Guardian-protected workflow:

1. **Before Changes**
   ```bash
   git status                           # Ensure clean state
   ./guardian.sh --validate-knowledge   # Validate AI understanding
   ./guardian.sh --create-snapshot     # Create backup
   ```

2. **Making Changes**
   ```bash
   # All Django commands use Guardian protection
   ./guardian.sh --django-command "startapp myapp"
   ./guardian.sh --makemigrations
   ./guardian.sh --migrate
   ```

3. **Testing & Deployment**
   ```bash
   python manage.py test                # Run tests
   ./guardian.sh --health-check        # Validate system
   git commit -m "feat: new feature"   # Guardian auto-updates knowledge
   ```

## 🔑 Key Features

### Authentication & Security
- Custom user model with security questions
- No public registration (admin-created users only)
- Role-based access (admin/superadmin)
- Password reset via security questions

### Admin Panel
- Enhanced Django admin interface
- API key management
- System log viewing
- User management
- Real-time health monitoring

### Real-time Updates
- Live task status updates
- Countdown timers for review deadlines
- WebSocket integration for notifications
- Responsive mobile-first design

### API Integrations
- **Fireflies**: Automated transcript ingestion
- **Gemini AI**: Task extraction and processing
- **Monday.com**: Task delivery and tracking

## 🚀 Deployment

### Render.com (Production)
```bash
# Deploy with Guardian protection
./guardian.sh --deploy-production --approval-required

# Validate deployment
./guardian.sh --validate-production
```

### Environment Variables
```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
DJANGO_SECRET_KEY=...
FIREFLIES_API_KEY=...
GEMINI_API_KEY=...
MONDAY_API_KEY=...
```

## 📊 Monitoring

### Health Checks
- `/health` endpoint for system status
- Database connectivity
- External API availability
- Background job status
- Guardian system integrity

### Logging
- Structured logging with rotation
- Guardian action logging
- Performance monitoring
- Error tracking and alerting

## 🔄 Backup & Recovery

### Automatic Snapshots
- Guardian creates snapshots before every change
- 30-day retention policy
- One-click restoration capability

### Emergency Procedures
```bash
./guardian.sh --emergency-rollback    # Immediate rollback
./guardian.sh --restore-snapshot <id> # Restore specific snapshot
```

## 🧪 Testing

### Test Coverage
```bash
python manage.py test                 # All tests
python manage.py test apps.ingestion # Module tests
coverage run --source='.' manage.py test
coverage report
```

### Guardian Testing
```bash
./guardian.sh --test-integration     # Integration tests
./guardian.sh --validate-knowledge   # AI knowledge tests
```

## 📚 Documentation

- [`project-guidelines/`](project-guidelines/) - Complete development guidelines
- [`project-guidelines/DEVELOPMENT_WORKFLOW.md`](project-guidelines/DEVELOPMENT_WORKFLOW.md) - Development process
- [`project-guidelines/GUARDIAN_SYSTEM.md`](project-guidelines/GUARDIAN_SYSTEM.md) - Guardian system documentation
- [`project-guidelines/PROJECT_SKELETON.md`](project-guidelines/PROJECT_SKELETON.md) - Project structure

## 🤝 Contributing

All contributions must follow the Guardian system workflow:

1. Read all files in `project-guidelines/`
2. Use Guardian protection for all changes
3. Ensure AI knowledge is updated
4. Get human approval for all modifications
5. Validate all tests pass

## 📄 License

[MIT License](LICENSE)

## 🆘 Support

For issues or questions:
1. Check Guardian system health: `./guardian.sh --health-check`
2. Review logs: `tail -f logs/guardian.log`
3. Emergency rollback: `./guardian.sh --emergency-rollback`

---

**Built with Guardian System Protection - Zero Regressions Guaranteed** 🛡️ 