#!/bin/bash
# 4Runr AI Lead System - Daily Sync Script
# Runs daily automation for lead scraping, enrichment, and messaging

set -e

# Set up environment
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

# Log file
LOG_FILE="logs/daily_sync_$(date +%Y%m%d).log"
mkdir -p logs

echo "$(date): Starting daily sync" >> "$LOG_FILE"

# Step 1: Run daily scraper to get new leads
echo "$(date): Running daily scraper..." >> "$LOG_FILE"
python 4runr-lead-scraper/scripts/daily_scraper.py --max-leads 5 >> "$LOG_FILE" 2>&1

# Step 2: Run enricher agent to enrich existing leads
echo "$(date): Running enricher agent..." >> "$LOG_FILE"
python 4runr-outreach-system/daily_enricher_agent_updated.py --max-leads 20 >> "$LOG_FILE" 2>&1

# Step 3: Run message generator for leads without AI messages
echo "$(date): Running message generator..." >> "$LOG_FILE"
python 4runr-outreach-system/message_generator/app.py --limit 20 >> "$LOG_FILE" 2>&1

# Step 4: Sync to Airtable
echo "$(date): Syncing to Airtable..." >> "$LOG_FILE"
python 4runr-lead-scraper/run_cli.py sync --to-airtable >> "$LOG_FILE" 2>&1

echo "$(date): Daily sync completed" >> "$LOG_FILE"
