#!/bin/bash

# TaskForge Guardian System
# Safeguarding AI-driven Django development with zero regressions
# Version: 1.0

set -euo pipefail

# Configuration
GUARDIAN_DIR=".guardian"
KNOWLEDGE_DIR=".ai-knowledge"
DJANGO_MANAGE="python manage.py"
BACKUP_DIR="guardian_snapshots"
LOG_FILE="logs/guardian.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

# Guardian initialization
init_guardian() {
    log "INFO" "${BLUE}Initializing Guardian System...${NC}"
    
    # Create directories
    mkdir -p "$GUARDIAN_DIR" "$KNOWLEDGE_DIR" "$BACKUP_DIR" "logs"
    
    # Initialize knowledge base
    create_knowledge_base
    
    # Set up git hooks
    setup_git_hooks
    
    log "INFO" "${GREEN}Guardian System initialized successfully${NC}"
}

# Create knowledge base structure
create_knowledge_base() {
    log "INFO" "Creating AI knowledge base..."
    
    cat > "$KNOWLEDGE_DIR/PROJECT_STATE.md" << 'EOF'
# TaskForge Project State

## Current Status
- **Framework**: Django 4.2.7
- **Database**: PostgreSQL
- **Background Jobs**: Celery + Redis
- **Deployment**: Render.com
- **Guardian System**: Active

## Modules Status
- [ ] Core Infrastructure
- [ ] Authentication System
- [ ] Administration Panel
- [ ] Ingestion Module (Fireflies API)
- [ ] Processing Module (Gemini AI)
- [ ] Review Module (Dashboard)
- [ ] Delivery Module (Monday.com API)

## Last Updated
EOF
    echo "Last Updated: $(date)" >> "$KNOWLEDGE_DIR/PROJECT_STATE.md"
    
    cat > "$KNOWLEDGE_DIR/KNOWLEDGE_TESTS.md" << 'EOF'
# AI Knowledge Validation Tests

## Architecture Questions
1. What framework is TaskForge built on? (Answer: Django)
2. What database system does TaskForge use? (Answer: PostgreSQL)
3. What is the background job system? (Answer: Celery with Redis)
4. Where is TaskForge deployed? (Answer: Render.com)

## Business Logic Questions
5. What is the Fireflies ingestion frequency? (Answer: 15 minutes)
6. How long is the human review window? (Answer: 18 hours)
7. What triggers auto-push to Monday.com? (Answer: Tasks pending >18 hours)
8. Which timezone does the backend use? (Answer: UTC)

## Guardian System Questions
9. What protects against regressions? (Answer: Guardian System)
10. Where is AI knowledge stored? (Answer: .ai-knowledge/ directory)
11. What requires human approval? (Answer: All code changes)
12. How are modules isolated? (Answer: Independent Django apps with event bus)
EOF

    cat > "$KNOWLEDGE_DIR/API_CONTRACTS.md" << 'EOF'
# External API Contracts

## Fireflies API
- **Purpose**: Transcript ingestion
- **Frequency**: Every 15 minutes
- **Endpoint**: https://api.fireflies.ai/graphql
- **Rate Limit**: 100 requests/minute

## Gemini API  
- **Purpose**: AI task extraction
- **Frequency**: Every 5 minutes
- **Endpoint**: https://generativelanguage.googleapis.com/v1beta
- **Rate Limit**: 60 requests/minute

## Monday.com API
- **Purpose**: Task delivery
- **Frequency**: Hourly (for tasks >18h old)
- **Endpoint**: https://api.monday.com/v2
- **Rate Limit**: 100 requests/minute
EOF

    log "INFO" "${GREEN}Knowledge base created${NC}"
}

# Set up git hooks for Guardian integration
setup_git_hooks() {
    log "INFO" "Setting up git hooks..."
    
    cat > ".git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# Guardian pre-commit hook
./guardian.sh --pre-commit-check
EOF
    
    cat > ".git/hooks/post-commit" << 'EOF'
#!/bin/bash
# Guardian post-commit hook
./guardian.sh --post-commit-update
EOF
    
    chmod +x ".git/hooks/pre-commit" ".git/hooks/post-commit"
    
    log "INFO" "${GREEN}Git hooks configured${NC}"
}

# Pre-check: Ensure clean state
pre_check() {
    log "INFO" "Running Guardian pre-check..."
    
    # Check git status
    if [[ -n $(git status --porcelain) ]]; then
        log "ERROR" "${RED}Working directory not clean. Commit or stash changes first.${NC}"
        git status --short
        exit 1
    fi
    
    # Check if virtual environment is active
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log "WARN" "${YELLOW}No virtual environment detected. Recommendation: activate venv${NC}"
    fi
    
    # Check Django installation
    if ! python -c "import django" 2>/dev/null; then
        log "ERROR" "${RED}Django not installed or accessible${NC}"
        exit 1
    fi
    
    log "INFO" "${GREEN}Pre-check passed${NC}"
}

# Create system snapshot
create_snapshot() {
    local snapshot_id="snapshot_$(date +%Y%m%d_%H%M%S)"
    local snapshot_dir="$BACKUP_DIR/$snapshot_id"
    
    log "INFO" "Creating snapshot: $snapshot_id"
    
    mkdir -p "$snapshot_dir"
    
    # Backup code
    tar -czf "$snapshot_dir/code.tar.gz" \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='logs' \
        --exclude="$BACKUP_DIR" \
        .
    
    # Backup database schema
    if command -v pg_dump &> /dev/null; then
        $DJANGO_MANAGE dumpdata --natural-foreign --natural-primary > "$snapshot_dir/data.json" 2>/dev/null || true
    fi
    
    # Backup knowledge base
    cp -r "$KNOWLEDGE_DIR" "$snapshot_dir/"
    
    echo "$snapshot_id" > "$GUARDIAN_DIR/last_snapshot"
    
    log "INFO" "${GREEN}Snapshot created: $snapshot_id${NC}"
}

# Validate AI knowledge
validate_knowledge() {
    log "INFO" "Validating AI knowledge..."
    
    local knowledge_files=("PROJECT_STATE.md" "KNOWLEDGE_TESTS.md" "API_CONTRACTS.md")
    
    for file in "${knowledge_files[@]}"; do
        if [[ ! -f "$KNOWLEDGE_DIR/$file" ]]; then
            log "ERROR" "${RED}Missing knowledge file: $file${NC}"
            exit 1
        fi
        
        # Check if file is recent (updated within last 24 hours)
        if [[ $(find "$KNOWLEDGE_DIR/$file" -mtime +1) ]]; then
            log "WARN" "${YELLOW}Knowledge file may be stale: $file${NC}"
        fi
    done
    
    log "INFO" "${GREEN}Knowledge validation passed${NC}"
}

# Django command wrapper with Guardian protection
django_command() {
    local command="$1"
    
    log "INFO" "Executing Guardian-protected Django command: $command"
    
    # Pre-check
    pre_check
    
    # Create snapshot
    create_snapshot
    
    # Validate knowledge
    validate_knowledge
    
    # Generate change impact report
    generate_impact_report "$command"
    
    # Approval gate
    if [[ "${GUARDIAN_BYPASS:-false}" != "true" ]]; then
        echo -e "${YELLOW}Command: $DJANGO_MANAGE $command${NC}"
        echo -e "${YELLOW}Impact report generated in $GUARDIAN_DIR/impact_report.md${NC}"
        read -p "Approve execution? (y/N): " approval
        
        if [[ $approval != "y" && $approval != "Y" ]]; then
            log "INFO" "Command execution cancelled by user"
            exit 1
        fi
    fi
    
    # Execute command
    log "INFO" "Executing: $DJANGO_MANAGE $command"
    $DJANGO_MANAGE $command
    
    # Post-check
    post_check "$command"
    
    log "INFO" "${GREEN}Command completed successfully${NC}"
}

# Generate change impact report
generate_impact_report() {
    local command="$1"
    local report_file="$GUARDIAN_DIR/impact_report.md"
    
    cat > "$report_file" << EOF
# Guardian Change Impact Report

**Command**: \`$command\`  
**Timestamp**: $(date)  
**User**: $(whoami)  

## Pre-Change State
- **Git Status**: Clean
- **Virtual Environment**: ${VIRTUAL_ENV:-"Not detected"}
- **Django Version**: $(python -c "import django; print(django.get_version())" 2>/dev/null || echo "Unknown")

## Risk Assessment
EOF

    # Analyze command risk
    case "$command" in
        "migrate")
            echo "- **Risk Level**: MEDIUM" >> "$report_file"
            echo "- **Database Changes**: YES" >> "$report_file"
            echo "- **Rollback Strategy**: Django migration rollback" >> "$report_file"
            ;;
        "makemigrations"*)
            echo "- **Risk Level**: LOW" >> "$report_file"
            echo "- **Database Changes**: NO (migration files only)" >> "$report_file"
            echo "- **Rollback Strategy**: Git revert" >> "$report_file"
            ;;
        "collectstatic"*)
            echo "- **Risk Level**: LOW" >> "$report_file"
            echo "- **Database Changes**: NO" >> "$report_file"
            echo "- **Rollback Strategy**: Git revert" >> "$report_file"
            ;;
        *)
            echo "- **Risk Level**: LOW" >> "$report_file"
            echo "- **Database Changes**: UNKNOWN" >> "$report_file"
            echo "- **Rollback Strategy**: Snapshot restoration" >> "$report_file"
            ;;
    esac
    
    cat >> "$report_file" << EOF

## Monitoring Required
- Database integrity check
- Application health check
- Knowledge base update

## Approval Required
- [ ] Human reviewer approval
- [ ] Knowledge base updated
- [ ] Backup created
EOF

    log "INFO" "Impact report generated: $report_file"
}

# Post-change checks and knowledge update
post_check() {
    local command="$1"
    
    log "INFO" "Running Guardian post-check..."
    
    # Check if files changed
    if [[ -n $(git status --porcelain) ]]; then
        log "INFO" "Changes detected, updating knowledge base..."
        update_knowledge_base "$command"
    fi
    
    # Run Django checks
    if $DJANGO_MANAGE check --deploy 2>/dev/null; then
        log "INFO" "${GREEN}Django deployment checks passed${NC}"
    else
        log "WARN" "${YELLOW}Django deployment checks failed${NC}"
    fi
    
    log "INFO" "${GREEN}Post-check completed${NC}"
}

# Update knowledge base
update_knowledge_base() {
    local command="${1:-manual_update}"
    
    log "INFO" "Updating AI knowledge base..."
    
    # Update PROJECT_STATE.md
    cat >> "$KNOWLEDGE_DIR/PROJECT_STATE.md" << EOF

## Recent Change
- **Command**: $command
- **Timestamp**: $(date)
- **Files Changed**: $(git status --porcelain | wc -l) files
EOF
    
    # Update CHANGE_MANIFEST.md
    if [[ ! -f "$KNOWLEDGE_DIR/CHANGE_MANIFEST.md" ]]; then
        echo "# Change Manifest" > "$KNOWLEDGE_DIR/CHANGE_MANIFEST.md"
        echo "" >> "$KNOWLEDGE_DIR/CHANGE_MANIFEST.md"
    fi
    
    cat >> "$KNOWLEDGE_DIR/CHANGE_MANIFEST.md" << EOF
## $(date '+%Y-%m-%d %H:%M:%S')
- **Command**: $command
- **Git Status**: $(git rev-parse --short HEAD 2>/dev/null || echo "No commits")
- **Changes**: 
$(git status --porcelain | sed 's/^/  - /')

EOF
    
    log "INFO" "${GREEN}Knowledge base updated${NC}"
}

# Emergency rollback
emergency_rollback() {
    log "WARN" "${RED}EMERGENCY ROLLBACK INITIATED${NC}"
    
    local last_snapshot
    if [[ -f "$GUARDIAN_DIR/last_snapshot" ]]; then
        last_snapshot=$(cat "$GUARDIAN_DIR/last_snapshot")
        log "INFO" "Rolling back to snapshot: $last_snapshot"
        
        # Restore from snapshot
        if [[ -d "$BACKUP_DIR/$last_snapshot" ]]; then
            tar -xzf "$BACKUP_DIR/$last_snapshot/code.tar.gz" -C /tmp/guardian_restore
            
            echo -e "${YELLOW}Snapshot found. This will overwrite current code.${NC}"
            read -p "Continue with rollback? (y/N): " confirm
            
            if [[ $confirm == "y" || $confirm == "Y" ]]; then
                # Backup current state first
                create_snapshot
                
                # Restore files
                rsync -av --exclude='.git' /tmp/guardian_restore/ ./
                
                # Restore knowledge base
                cp -r "$BACKUP_DIR/$last_snapshot/.ai-knowledge/" ./
                
                log "INFO" "${GREEN}Rollback completed${NC}"
            else
                log "INFO" "Rollback cancelled"
            fi
            
            rm -rf /tmp/guardian_restore
        else
            log "ERROR" "${RED}Snapshot not found: $last_snapshot${NC}"
            exit 1
        fi
    else
        log "ERROR" "${RED}No snapshot record found${NC}"
        exit 1
    fi
}

# Health check
health_check() {
    log "INFO" "Running Guardian health check..."
    
    local checks_passed=0
    local total_checks=5
    
    # Check 1: Django installation
    if python -c "import django" 2>/dev/null; then
        log "INFO" "${GREEN}✓ Django installation${NC}"
        ((checks_passed++))
    else
        log "ERROR" "${RED}✗ Django installation${NC}"
    fi
    
    # Check 2: Database connection
    if $DJANGO_MANAGE check --database default 2>/dev/null; then
        log "INFO" "${GREEN}✓ Database connection${NC}"
        ((checks_passed++))
    else
        log "ERROR" "${RED}✗ Database connection${NC}"
    fi
    
    # Check 3: Knowledge base
    if [[ -d "$KNOWLEDGE_DIR" ]] && [[ $(ls "$KNOWLEDGE_DIR"/*.md 2>/dev/null | wc -l) -gt 0 ]]; then
        log "INFO" "${GREEN}✓ Knowledge base${NC}"
        ((checks_passed++))
    else
        log "ERROR" "${RED}✗ Knowledge base${NC}"
    fi
    
    # Check 4: Git repository
    if git rev-parse --git-dir >/dev/null 2>&1; then
        log "INFO" "${GREEN}✓ Git repository${NC}"
        ((checks_passed++))
    else
        log "ERROR" "${RED}✗ Git repository${NC}"
    fi
    
    # Check 5: Guardian directories
    if [[ -d "$GUARDIAN_DIR" ]] && [[ -d "$BACKUP_DIR" ]]; then
        log "INFO" "${GREEN}✓ Guardian directories${NC}"
        ((checks_passed++))
    else
        log "ERROR" "${RED}✗ Guardian directories${NC}"
    fi
    
    log "INFO" "Health check: $checks_passed/$total_checks checks passed"
    
    if [[ $checks_passed -eq $total_checks ]]; then
        log "INFO" "${GREEN}All health checks passed${NC}"
        return 0
    else
        log "WARN" "${YELLOW}Some health checks failed${NC}"
        return 1
    fi
}

# Pre-commit check
pre_commit_check() {
    log "INFO" "Guardian pre-commit check..."
    
    # Validate knowledge base is updated
    validate_knowledge
    
    # Run Django checks
    $DJANGO_MANAGE check
    
    # Update knowledge base with commit info
    update_knowledge_base "pre-commit"
    
    log "INFO" "${GREEN}Pre-commit check passed${NC}"
}

# Post-commit update
post_commit_update() {
    log "INFO" "Guardian post-commit update..."
    
    # Update knowledge base with commit hash
    local commit_hash=$(git rev-parse --short HEAD)
    
    cat >> "$KNOWLEDGE_DIR/PROJECT_STATE.md" << EOF

## Latest Commit
- **Hash**: $commit_hash
- **Timestamp**: $(date)
- **Message**: $(git log -1 --pretty=%B | head -1)
EOF
    
    log "INFO" "${GREEN}Post-commit update completed${NC}"
}

# Main command router
main() {
    case "${1:-}" in
        "--init"|"--create-knowledge-base")
            init_guardian
            ;;
        "--django-command")
            if [[ -z "${2:-}" ]]; then
                log "ERROR" "Django command required"
                exit 1
            fi
            django_command "$2"
            ;;
        "--migrate")
            django_command "migrate"
            ;;
        "--makemigrations")
            django_command "makemigrations"
            ;;
        "--collectstatic")
            django_command "collectstatic --noinput"
            ;;
        "--emergency-rollback")
            emergency_rollback
            ;;
        "--health-check")
            health_check
            ;;
        "--pre-commit-check")
            pre_commit_check
            ;;
        "--post-commit-update")
            post_commit_update
            ;;
        "--update-knowledge")
            update_knowledge_base "manual"
            ;;
        "--validate-knowledge")
            validate_knowledge
            ;;
        "--create-snapshot")
            create_snapshot
            ;;
        *)
            cat << 'EOF'
TaskForge Guardian System v1.0

Usage:
  ./guardian.sh [COMMAND]

Commands:
  --init                     Initialize Guardian system
  --django-command "cmd"     Execute Django command with Guardian protection
  --migrate                  Run Django migrations with Guardian protection
  --makemigrations          Create Django migrations with Guardian protection
  --collectstatic           Collect static files with Guardian protection
  --emergency-rollback      Emergency rollback to last snapshot
  --health-check            Run Guardian system health check
  --update-knowledge        Update AI knowledge base
  --validate-knowledge      Validate AI knowledge base
  --create-snapshot         Create system snapshot

Environment Variables:
  GUARDIAN_BYPASS=true      Bypass approval gates (emergency only)

Examples:
  ./guardian.sh --init
  ./guardian.sh --migrate
  ./guardian.sh --django-command "createsuperuser"
  ./guardian.sh --health-check

EOF
            ;;
    esac
}

# Execute main function with all arguments
main "$@" 