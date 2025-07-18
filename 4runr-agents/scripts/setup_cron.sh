#!/bin/bash
# Script to set up a cron job for running the 4Runr lead pipeline

# Navigate to the project directory
cd "$(dirname "$0")/.."
PROJECT_DIR=$(pwd)

# Check if the project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Ask for the schedule
echo "Enter the cron schedule for running the pipeline (e.g., '0 9 * * *' for daily at 9 AM):"
read -p "> " CRON_SCHEDULE

# Validate the schedule
if [ -z "$CRON_SCHEDULE" ]; then
    echo "Error: No schedule provided"
    exit 1
fi

# Create the cron job command
CRON_CMD="cd $PROJECT_DIR && docker-compose run --rm pipeline >> $PROJECT_DIR/pipeline.log 2>&1"

# Create a temporary file with the current crontab
crontab -l > /tmp/current_crontab 2>/dev/null || echo "" > /tmp/current_crontab

# Check if the job already exists
if grep -q "$CRON_CMD" /tmp/current_crontab; then
    echo "Cron job already exists. Updating schedule..."
    sed -i "/$(echo $CRON_CMD | sed 's/\//\\\//g')/d" /tmp/current_crontab
fi

# Add the new job
echo "$CRON_SCHEDULE $CRON_CMD" >> /tmp/current_crontab

# Install the new crontab
crontab /tmp/current_crontab
rm /tmp/current_crontab

echo "Cron job set up successfully!"
echo "Schedule: $CRON_SCHEDULE"
echo "Command: $CRON_CMD"
echo "To view the crontab, run: crontab -l"