#!/bin/bash
"""
Cron Setup Script for Campaign Brain Daily Processing

Sets up automated daily batch processing with proper logging and error handling.
"""

# Configuration
CAMPAIGN_BRAIN_DIR="/path/to/4runr-brain"  # Update this path
PYTHON_PATH="/usr/bin/python3"            # Update if needed
LOG_DIR="$CAMPAIGN_BRAIN_DIR/logs/cron"
BATCH_SIZE=20
DAILY_TIME="08:00"  # 8:00 AM

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Campaign Brain Cron Setup${NC}"
echo "=================================="

# Check if running as correct user
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: Running as root. Consider using a service user.${NC}"
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Check if Campaign Brain directory exists
if [ ! -d "$CAMPAIGN_BRAIN_DIR" ]; then
    echo -e "${RED}❌ Campaign Brain directory not found: $CAMPAIGN_BRAIN_DIR${NC}"
    echo "Please update CAMPAIGN_BRAIN_DIR in this script"
    exit 1
fi

# Check if Python exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo -e "${RED}❌ Python not found: $PYTHON_PATH${NC}"
    echo "Please update PYTHON_PATH in this script"
    exit 1
fi

# Create wrapper script
WRAPPER_SCRIPT="$CAMPAIGN_BRAIN_DIR/run_daily_batch.sh"

cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Campaign Brain Daily Batch Wrapper Script
# Generated on $(date)

# Set environment
export PATH="/usr/local/bin:/usr/bin:/bin"
cd "$CAMPAIGN_BRAIN_DIR"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export \$(cat .env | grep -v '^#' | xargs)
fi

# Set batch configuration
export DAILY_BATCH_SIZE=$BATCH_SIZE
export DAILY_DRY_RUN=false
export ENABLE_ERROR_NOTIFICATIONS=true

# Log file with date
LOG_FILE="$LOG_DIR/daily_batch_\$(date +%Y%m%d).log"

# Run daily batch processor
echo "\$(date): Starting daily batch processing" >> "\$LOG_FILE"

$PYTHON_PATH daily_batch_processor.py >> "\$LOG_FILE" 2>&1

EXIT_CODE=\$?

echo "\$(date): Daily batch processing completed with exit code \$EXIT_CODE" >> "\$LOG_FILE"

# If failed, create error flag file
if [ \$EXIT_CODE -ne 0 ]; then
    echo "\$(date): Daily batch processing FAILED" >> "$LOG_DIR/error_flag_\$(date +%Y%m%d).txt"
fi

exit \$EXIT_CODE
EOF

# Make wrapper script executable
chmod +x "$WRAPPER_SCRIPT"

echo -e "${GREEN}✅ Created wrapper script: $WRAPPER_SCRIPT${NC}"

# Create cron entry
CRON_ENTRY="0 8 * * * $WRAPPER_SCRIPT"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "$WRAPPER_SCRIPT"; then
    echo -e "${YELLOW}⚠️  Cron entry already exists${NC}"
    echo "Current cron entries for Campaign Brain:"
    crontab -l 2>/dev/null | grep -E "(campaign|brain|daily_batch)"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo -e "${GREEN}✅ Added cron entry: $CRON_ENTRY${NC}"
fi

# Create monitoring script
MONITOR_SCRIPT="$CAMPAIGN_BRAIN_DIR/monitor_daily_batch.sh"

cat > "$MONITOR_SCRIPT" << EOF
#!/bin/bash
# Campaign Brain Daily Batch Monitor
# Generated on $(date)

LOG_DIR="$LOG_DIR"
TODAY=\$(date +%Y%m%d)

echo "📊 Campaign Brain Daily Batch Status"
echo "===================================="

# Check if batch ran today
if [ -f "\$LOG_DIR/daily_batch_\$TODAY.log" ]; then
    echo "✅ Batch log found for today"
    
    # Check for errors
    if [ -f "\$LOG_DIR/error_flag_\$TODAY.txt" ]; then
        echo "❌ Batch failed today - check logs"
        echo "Error flag: \$LOG_DIR/error_flag_\$TODAY.txt"
    else
        echo "✅ Batch appears to have completed successfully"
    fi
    
    # Show last few lines of log
    echo ""
    echo "📝 Last 10 lines of today's log:"
    tail -10 "\$LOG_DIR/daily_batch_\$TODAY.log"
    
else
    echo "⚠️  No batch log found for today"
    echo "Expected: \$LOG_DIR/daily_batch_\$TODAY.log"
fi

# Show recent error flags
echo ""
echo "🚨 Recent error flags:"
find "\$LOG_DIR" -name "error_flag_*.txt" -mtime -7 | sort

# Show disk usage
echo ""
echo "💾 Log directory disk usage:"
du -sh "\$LOG_DIR"

# Show cron status
echo ""
echo "⏰ Cron entries:"
crontab -l 2>/dev/null | grep -E "(campaign|brain|daily_batch)" || echo "No cron entries found"
EOF

chmod +x "$MONITOR_SCRIPT"

echo -e "${GREEN}✅ Created monitoring script: $MONITOR_SCRIPT${NC}"

# Create log rotation script
LOGROTATE_SCRIPT="$CAMPAIGN_BRAIN_DIR/rotate_logs.sh"

cat > "$LOGROTATE_SCRIPT" << EOF
#!/bin/bash
# Campaign Brain Log Rotation
# Generated on $(date)

LOG_DIR="$LOG_DIR"
TRACE_DIR="$CAMPAIGN_BRAIN_DIR/trace_logs"
RESULTS_DIR="$CAMPAIGN_BRAIN_DIR/logs/daily_results"

echo "🔄 Rotating Campaign Brain logs..."

# Compress logs older than 7 days
find "\$LOG_DIR" -name "*.log" -mtime +7 -exec gzip {} \;

# Remove compressed logs older than 30 days
find "\$LOG_DIR" -name "*.log.gz" -mtime +30 -delete

# Remove error flags older than 30 days
find "\$LOG_DIR" -name "error_flag_*.txt" -mtime +30 -delete

# Compress trace logs older than 7 days
find "\$TRACE_DIR" -name "*.json" -mtime +7 -exec gzip {} \;

# Remove compressed trace logs older than 90 days
find "\$TRACE_DIR" -name "*.json.gz" -mtime +90 -delete

# Compress daily results older than 30 days
find "\$RESULTS_DIR" -name "*.json" -mtime +30 -exec gzip {} \;

# Remove compressed results older than 180 days
find "\$RESULTS_DIR" -name "*.json.gz" -mtime +180 -delete

echo "✅ Log rotation completed"
EOF

chmod +x "$LOGROTATE_SCRIPT"

# Add weekly log rotation to cron
LOGROTATE_CRON="0 2 * * 0 $LOGROTATE_SCRIPT"

if ! crontab -l 2>/dev/null | grep -q "$LOGROTATE_SCRIPT"; then
    (crontab -l 2>/dev/null; echo "$LOGROTATE_CRON") | crontab -
    echo -e "${GREEN}✅ Added log rotation cron entry${NC}"
fi

echo -e "${GREEN}✅ Created log rotation script: $LOGROTATE_SCRIPT${NC}"

# Create health check script
HEALTH_SCRIPT="$CAMPAIGN_BRAIN_DIR/health_check.sh"

cat > "$HEALTH_SCRIPT" << EOF
#!/bin/bash
# Campaign Brain Health Check
# Generated on $(date)

cd "$CAMPAIGN_BRAIN_DIR"

# Load environment
if [ -f ".env" ]; then
    export \$(cat .env | grep -v '^#' | xargs)
fi

echo "🏥 Campaign Brain Health Check"
echo "============================="

# Check service health
$PYTHON_PATH serve_campaign_brain.py --health-check

EXIT_CODE=\$?

if [ \$EXIT_CODE -eq 0 ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
fi

exit \$EXIT_CODE
EOF

chmod +x "$HEALTH_SCRIPT"

echo -e "${GREEN}✅ Created health check script: $HEALTH_SCRIPT${NC}"

# Summary
echo ""
echo -e "${GREEN}🎉 Cron Setup Complete!${NC}"
echo "========================"
echo ""
echo "📅 Daily Processing:"
echo "  • Time: 8:00 AM daily"
echo "  • Batch Size: $BATCH_SIZE leads"
echo "  • Wrapper: $WRAPPER_SCRIPT"
echo ""
echo "📊 Monitoring:"
echo "  • Monitor: $MONITOR_SCRIPT"
echo "  • Health Check: $HEALTH_SCRIPT"
echo "  • Log Rotation: $LOGROTATE_SCRIPT"
echo ""
echo "📝 Log Locations:"
echo "  • Daily Logs: $LOG_DIR"
echo "  • Trace Logs: $CAMPAIGN_BRAIN_DIR/trace_logs"
echo "  • Results: $CAMPAIGN_BRAIN_DIR/logs/daily_results"
echo ""
echo "🔧 Management Commands:"
echo "  • Check Status: $MONITOR_SCRIPT"
echo "  • Health Check: $HEALTH_SCRIPT"
echo "  • Manual Run: $WRAPPER_SCRIPT"
echo "  • View Cron: crontab -l"
echo ""
echo "⚠️  Next Steps:"
echo "  1. Update CAMPAIGN_BRAIN_DIR path in this script if needed"
echo "  2. Ensure .env file is configured with API keys"
echo "  3. Test manual run: $WRAPPER_SCRIPT"
echo "  4. Monitor first automated run tomorrow"

# Test the setup
echo ""
echo -e "${YELLOW}🧪 Testing setup...${NC}"

# Test wrapper script
if [ -x "$WRAPPER_SCRIPT" ]; then
    echo "✅ Wrapper script is executable"
else
    echo "❌ Wrapper script is not executable"
fi

# Test health check
if "$HEALTH_SCRIPT" > /dev/null 2>&1; then
    echo "✅ Health check script works"
else
    echo "⚠️  Health check script needs configuration"
fi

echo ""
echo -e "${GREEN}Setup complete! 🚀${NC}"