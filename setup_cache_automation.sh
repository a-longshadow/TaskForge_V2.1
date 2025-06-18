#!/bin/bash

# TaskForge Cache Automation Setup
# Sets up 4-hour automated cache refresh using cron

echo "🔄 TaskForge Cache Automation Setup"
echo "=================================="

# Get the current directory (TaskForge project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python"
MANAGE_PY="$PROJECT_DIR/manage.py"

echo "📁 Project Directory: $PROJECT_DIR"
echo "🐍 Python Path: $PYTHON_PATH"

# Verify paths exist
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Error: Python virtual environment not found at $PYTHON_PATH"
    echo "   Please ensure you're running this from the TaskForge project root"
    exit 1
fi

if [ ! -f "$MANAGE_PY" ]; then
    echo "❌ Error: manage.py not found at $MANAGE_PY"
    exit 1
fi

# Create log directory
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
echo "📝 Log Directory: $LOG_DIR"

# Create the cron job command
CRON_COMMAND="0 */4 * * * cd $PROJECT_DIR && $PYTHON_PATH $MANAGE_PY auto_refresh_cache >> $LOG_DIR/cache_refresh.log 2>&1"

echo ""
echo "🕐 Cron Job Schedule: Every 4 hours (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)"
echo "📋 Cron Command:"
echo "   $CRON_COMMAND"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "auto_refresh_cache"; then
    echo ""
    echo "⚠️  Existing cache refresh cron job found!"
    echo "   Current crontab:"
    crontab -l | grep "auto_refresh_cache"
    echo ""
    read -p "   Replace existing cron job? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted - keeping existing cron job"
        exit 0
    fi
    
    # Remove existing cron job
    crontab -l | grep -v "auto_refresh_cache" | crontab -
    echo "🗑️  Removed existing cron job"
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo ""
    echo "📋 Current crontab:"
    crontab -l | grep "auto_refresh_cache"
    echo ""
    echo "🎯 Cache Automation Status:"
    echo "   • Refresh Frequency: Every 4 hours"
    echo "   • Log File: $LOG_DIR/cache_refresh.log"
    echo "   • API Quota Impact: ~4 calls/day (96% reduction)"
    echo "   • Next Run: Within 4 hours"
    echo ""
    echo "📝 To check logs: tail -f $LOG_DIR/cache_refresh.log"
    echo "🛑 To stop automation: crontab -e (remove the auto_refresh_cache line)"
    echo ""
    echo "🎉 Automated cache refresh is now active!"
else
    echo "❌ Failed to add cron job"
    exit 1
fi 