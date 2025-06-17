# Guardian System & Knowledge Management

## Guardian Script: Safeguarding AI-Driven Changes

Wrap every automated or "AI agent" command in `guardian.sh`:

1. **Pre-check:** Ensure a clean Git state or abort.
2. **(Optional) Backup:** Snapshot via `scripts/create_snapshot.sh`.
3. **Run:** Execute the provided command.
4. **Post-check:** If tracked files changed, alarm—and, if configured, restore.

## Guardian Commands

### Basic Usage
```bash
./guardian.sh --backup --strict ai-agent generate-changes.patch
```

### Auto-Guardian with Approval Gate
```bash
./guardian.sh --auto --report-only <command>
# ↓ Generates comprehensive change report
# ↓ Waits for explicit human approval
# ↓ Only then applies changes
```

### Module-Specific Guardian
```bash
./guardian.sh --module=ingestion --pre-check
./guardian.sh --module=ingestion --change --approval-gate
```

## Living Knowledge Repository

### Directory Structure
```
.ai-knowledge/
├── PROJECT_STATE.md          # Complete current state
├── ARCHITECTURE_MAP.md       # System design & relationships  
├── API_CONTRACTS.md          # All external integrations
├── DEPLOYMENT_STATE.md       # Current deploy config & env
├── CHANGE_MANIFEST.md        # Every change with context
├── MODULE_STATUS.md          # Individual module states
└── KNOWLEDGE_TESTS.md        # Validation questions for AI
```

### Knowledge Validation Protocol

#### Pre-Change Validation
- Guardian validates AI agent understanding before ANY code changes
- Knowledge Test Suite: Automated questions AI must answer correctly
- Context Continuity Check: Verifies AI can reconstruct full project

#### Knowledge Test Examples
```markdown
# KNOWLEDGE_TESTS.md
1. What is the Fireflies ingestion frequency? (Answer: 15 minutes)
2. How long is the human review window? (Answer: 18 hours)
3. What triggers auto-push to Monday.com? (Answer: >18h old pending tasks)
4. Which timezone does the backend use? (Answer: UTC)
```

## Change Impact Report Format

```
CHANGE IMPACT REPORT
===================
Files Modified: 3
Lines Changed: +47, -12
Dependencies Added: flask-socketio==5.1.0
API Endpoints: +2 new routes
Database: No schema changes
External APIs: No new integrations
Rollback Strategy: Git revert + DB migration down
Risk Level: LOW
Estimated Downtime: 0 minutes
Security Impact: None
Performance Impact: Minimal
```

## Cross-Device Migration Protocol

### Export Knowledge
```bash
./scripts/export_ai_knowledge.sh     # Generates complete context package
```

### Validate Knowledge
```bash
./scripts/validate_ai_knowledge.sh   # Tests AI understanding
```

### Import Knowledge
```bash
./scripts/import_ai_knowledge.sh     # Restores full context
```

## Automated Knowledge Maintenance

### Daily Knowledge Sync
- Updates all .ai-knowledge/ files automatically
- Runs at 00:10 UTC (after daily briefing)
- Commits changes to knowledge repository

### Regression Detection
- Compares current state vs. documented state
- Alerts on knowledge drift
- Validates AI understanding hasn't degraded

### Knowledge Drift Alerts
```bash
# Warns when documentation falls behind code
./guardian.sh --knowledge-check --alert-threshold=5
```

## Git Integration

### Knowledge-Enhanced Commits
```bash
git commit -m "feat: fireflies integration
- Added FirefliesAPI class
- Updated PROJECT_STATE.md with new dependencies
- AI-Knowledge: Fireflies processes transcripts every 15min"
```

### Knowledge Branch Protection
- All commits must update relevant .ai-knowledge/ files
- Pre-commit hooks validate knowledge consistency
- CI/CD fails if knowledge tests don't pass

## Zero Regression Guarantees

### Guardian Enforcement Levels

#### Level 1: Advisory
- Generates warnings
- Logs potential issues
- Continues execution

#### Level 2: Strict
- Halts on any tracked file changes
- Requires explicit override
- Creates automatic backups

#### Level 3: Lockdown
- No changes allowed without approval
- All changes must pass knowledge tests
- Automatic rollback on failure

### Rollback Procedures
```bash
./guardian.sh --rollback --to-snapshot=<snapshot-id>
./guardian.sh --rollback --to-commit=<commit-hash>
./guardian.sh --rollback --emergency  # Last known good state
``` 