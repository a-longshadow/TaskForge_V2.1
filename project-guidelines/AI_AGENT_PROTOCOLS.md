# AI Agent Protocols & Governance

## Core Governance Principles

1. **Zero Direct Code Changes** - AI agents NEVER write code directly to production files
2. **Final Approval Gate** - Human approval required for ALL code changes
3. **Complete Context** - AI agents must demonstrate full project understanding
4. **Patch-Only Mode** - AI agents emit unified diffs, never write directly

## Development Workflow

### 1. Patch-Only Mode
```bash
# AI agent generates patches, not direct code changes
ai-agent --mode=patch --output=proposed-changes.patch

# Human reviews patch before applying
git apply proposed-changes.patch
```

### 2. Pull Request Workflow
```bash
# AI agent creates branch and PR
ai-agent --create-branch=feature/ai-enhancement
ai-agent --create-pr --title="AI Enhancement: Add error handling"

# Human must review and approve before merge
# No auto-merge allowed
```

### 3. Guardian Integration
```bash
# Every AI command wrapped in Guardian
./guardian.sh --ai-mode ai-agent generate-feature.patch

# Guardian validates:
# - AI knowledge state
# - Change impact
# - Regression risk
# - Human approval received
```

## Pre-Change Validation

### Knowledge Validation Protocol
Before ANY code changes, AI agent must pass knowledge tests:

```python
# Knowledge validation questions
KNOWLEDGE_TESTS = [
    {
        "question": "What is the Fireflies ingestion frequency?",
        "answer": "15 minutes",
        "category": "architecture"
    },
    {
        "question": "How long is the human review window?",
        "answer": "18 hours",
        "category": "business_logic"
    },
    {
        "question": "What triggers auto-push to Monday.com?",
        "answer": "Tasks pending >18 hours",
        "category": "automation"
    },
    {
        "question": "Which timezone does the backend use?",
        "answer": "UTC",
        "category": "technical"
    }
]
```

### Context Continuity Check
```python
def validate_ai_context():
    """AI must demonstrate complete project understanding"""
    checks = [
        "Can reconstruct system architecture from memory",
        "Knows all module dependencies",
        "Understands data flow between components",
        "Aware of current deployment state",
        "Familiar with recent changes"
    ]
    return all(check_passes(check) for check in checks)
```

## Change Impact Assessment

### Mandatory Impact Report
Before any changes, AI must generate:

```
AI CHANGE PROPOSAL
==================
Module Affected: ingestion
Files Modified: 2
  - modules/ingestion/api.py (+15, -3)
  - modules/ingestion/tests/test_api.py (+8, -0)

Change Summary:
- Add retry logic for failed API calls
- Implement exponential backoff
- Add comprehensive error logging

Dependencies Impact:
- No new dependencies added
- No version changes required

API Changes:
- No public API changes
- Internal retry behavior only

Database Changes:
- No schema modifications
- No data migrations needed

Performance Impact:
- Network calls: +2-5% latency (due to retries)
- Memory usage: Negligible
- CPU usage: Negligible

Risk Assessment:
- Risk Level: LOW
- Rollback Strategy: Git revert
- Monitoring Required: API call success rates

Test Coverage:
- New unit tests: 3
- Integration tests: Updated 1
- Coverage increase: +2.3%

Human Review Required For:
- Retry timeout values (currently 5s, 10s, 20s)
- Maximum retry attempts (currently 3)
- Error message format
```

## Approval Gate Process

### Human Approval Required
```bash
# AI submits change request
ai-agent --submit-change --id=CHG-001 --impact-report=impact.md

# Human reviews impact report
./review-change.sh --change-id=CHG-001 --approve

# Only then Guardian applies changes
./guardian.sh --apply-approved-change=CHG-001
```

### Approval Checklist
Human reviewer must verify:
- [ ] Impact report is complete and accurate
- [ ] Change aligns with project goals
- [ ] No security vulnerabilities introduced
- [ ] Test coverage is adequate
- [ ] Rollback plan is viable
- [ ] Documentation is updated
- [ ] Knowledge base is current

## AI Agent Constraints

### Prohibited Actions
- **Direct file modification** without approval
- **Database schema changes** without migration review
- **Dependency additions** without security review
- **Configuration changes** in production
- **API endpoint modifications** without contract review

### Required Actions
- **Update knowledge base** with every change
- **Run full test suite** before proposing changes
- **Generate comprehensive impact reports**
- **Validate against coding standards**
- **Check for security implications**

## Commit Standards

### AI-Generated Commits
```bash
# Required format for AI commits
git commit -m "feat(ingestion): add retry logic with exponential backoff

- Implements 3-retry strategy for API failures
- Uses exponential backoff (5s, 10s, 20s)
- Adds comprehensive error logging
- Updates unit tests for retry scenarios

AI-Agent: GPT-4-turbo
Change-ID: CHG-001
Approved-By: human-reviewer
Knowledge-Updated: PROJECT_STATE.md, API_CONTRACTS.md"
```

### Commit Metadata
Every AI commit must include:
- **AI-Agent**: Model/version used
- **Change-ID**: Unique change identifier
- **Approved-By**: Human approver
- **Knowledge-Updated**: Updated knowledge files
- **Risk-Level**: LOW/MEDIUM/HIGH

## Rollback Procedures

### AI-Initiated Rollback
```bash
# If AI detects issues post-deployment
ai-agent --detect-issues --auto-rollback=false --alert-human

# AI cannot auto-rollback, must request human approval
./guardian.sh --rollback-request --change-id=CHG-001 --reason="API failure rate increased"
```

### Rollback Validation
```python
def validate_rollback():
    """Ensure rollback is safe and complete"""
    checks = [
        "Database migrations reversed",
        "Configuration restored",
        "Dependencies reverted",
        "Tests passing",
        "Health checks green"
    ]
    return all(check_passes(check) for check in checks)
```

## Monitoring & Observability

### AI Action Logging
```python
# All AI actions must be logged
class AIActionLogger:
    def log_action(self, action, metadata):
        log_entry = {
            'timestamp': datetime.utcnow(),
            'ai_agent': 'GPT-4-turbo',
            'action': action,
            'metadata': metadata,
            'human_approved': False,
            'guardian_validated': False
        }
        self.store_log(log_entry)
```

### Performance Metrics
Track AI agent effectiveness:
- **Change success rate**
- **Rollback frequency**
- **Human approval time**
- **Knowledge test scores**
- **Impact report accuracy**

## Error Handling

### AI Agent Errors
```python
class AIAgentError(Exception):
    """Base exception for AI agent issues"""
    pass

class KnowledgeValidationError(AIAgentError):
    """AI failed knowledge validation"""
    pass

class ApprovalTimeoutError(AIAgentError):
    """Human approval not received within timeout"""
    pass

class ChangeRejectedError(AIAgentError):
    """Human rejected proposed change"""
    pass
```

### Recovery Procedures
1. **Knowledge Validation Failure**: Re-sync knowledge base
2. **Approval Timeout**: Alert human reviewer, queue change
3. **Change Rejection**: Log reason, update AI training data
4. **Rollback Required**: Immediate human notification

## Continuous Improvement

### AI Learning Loop
```python
def update_ai_knowledge(change_result):
    """Learn from change outcomes"""
    if change_result.success:
        # Reinforce successful patterns
        update_success_patterns(change_result.metadata)
    else:
        # Learn from failures
        update_failure_patterns(change_result.error_info)
        
    # Update knowledge base
    update_knowledge_base(change_result)
```

### Human Feedback Integration
- **Approval reasons** feed back to AI training
- **Rejection reasons** improve future proposals
- **Rollback causes** enhance risk assessment
- **Performance metrics** guide AI improvements 