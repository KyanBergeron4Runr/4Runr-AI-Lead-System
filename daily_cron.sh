#!/bin/bash
# Daily Lead Generation Cron Job
# Runs every day at 9:00 AM

# Set environment
cd /home/ubuntu/4Runr-AI-Lead-System
source .venv/bin/activate

# Run daily automation
python daily_automation.py

# Log completion
echo "$(date): Daily automation completed" >> logs/cron.log
