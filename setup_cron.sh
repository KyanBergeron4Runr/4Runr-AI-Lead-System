#!/bin/bash
# 4Runr AI Lead System - Cron Setup Script
# Sets up automated daily processing

echo "Setting up 4Runr AI Lead System cron jobs..."

# Get the current directory
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create log directory
mkdir -p "$PROJECT_DIR/logs"

# Add cron jobs
(crontab -l 2>/dev/null; cat << EOF
# 4Runr AI Lead System - Daily Automation
# Daily sync at 6 AM
0 6 * * * cd "$PROJECT_DIR" && bash 4runr-outreach-system/daily_sync.sh

# Health check every hour
0 * * * * cd "$PROJECT_DIR" && python system_controller.py --health-check >> logs/health_check.log 2>&1

# Weekly database maintenance on Sunday at 2 AM
0 2 * * 0 cd "$PROJECT_DIR" && python 4runr-lead-scraper/run_cli.py db --vacuum >> logs/maintenance.log 2>&1
EOF
) | crontab -

echo "✅ Cron jobs set up successfully!"
echo "Jobs added:"
echo "  - Daily sync at 6:00 AM"
echo "  - Health check every hour"
echo "  - Weekly maintenance on Sundays at 2:00 AM"
echo ""
echo "To view cron jobs: crontab -l"
echo "To edit cron jobs: crontab -e"
