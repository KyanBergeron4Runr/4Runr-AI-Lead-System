#!/bin/bash
# 4Runr AI Lead Scraper Full System Test
# This script runs a full system test of the 4Runr AI Lead Scraper system

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set timestamp for logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TEST_DIR="test_results_${TIMESTAMP}"
LOG_FILE="${TEST_DIR}/system_test.log"

# Function to log messages
log_message() {
  local level=$1
  local message=$2
  local color=$NC
  
  case $level in
    "INFO") color=$BLUE ;;
    "SUCCESS") color=$GREEN ;;
    "WARNING") color=$YELLOW ;;
    "ERROR") color=$RED ;;
  esac
  
  echo -e "${color}[$(date +"%Y-%m-%d %H:%M:%S")] [${level}] ${message}${NC}" | tee -a $LOG_FILE
}

# Function to check if a command was successful
check_status() {
  if [ $? -eq 0 ]; then
    log_message "SUCCESS" "$1"
    return 0
  else
    log_message "ERROR" "$2"
    return 1
  fi
}

# Create test results directory
mkdir -p $TEST_DIR

# Start the test
log_message "INFO" "Starting 4Runr AI Lead Scraper Full System Test"
log_message "INFO" "Test results will be saved to: $TEST_DIR"

# Step 1: Validate environment
log_message "INFO" "Step 1: Validating environment..."

# Check if we're in the correct directory
if [[ ! -d "shared" || ! -f "docker-compose.yml" ]]; then
  log_message "ERROR" "Not in the correct directory. Please run this script from the 4runr-agents directory."
  exit 1
fi

# Check if Docker is running
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
  log_message "ERROR" "Docker is not running. Please start Docker and try again."
  exit 1
fi

# Check if required containers are running
log_message "INFO" "Checking Docker containers..."
docker-compose ps | grep -E 'scraper|enricher|engager|pipeline|cron' > /dev/null 2>&1
check_status "All required containers are running." "Some containers are not running. Please start them with 'docker-compose up -d'."

# Check if .env file exists
if [ ! -f ".env" ]; then
  log_message "ERROR" ".env file not found. Please create it from .env.example."
  exit 1
fi

# Check if .env file contains required API keys
log_message "INFO" "Checking .env file for required API keys..."
grep -E 'AIRTABLE_API_KEY|OPENAI_API_KEY' .env > /dev/null 2>&1
check_status "Required API keys found in .env file." "Required API keys not found in .env file."

log_message "SUCCESS" "Environment validation completed successfully."

# Step 2: Prepare test data
log_message "INFO" "Step 2: Preparing test data..."

# Create test data templates directory if it doesn't exist
if [ ! -d "test_data_templates" ]; then
  log_message "INFO" "Creating test data templates directory..."
  mkdir -p test_data_templates
fi

# Create test lead template if it doesn't exist
if [ ! -f "test_data_templates/test_lead.json" ]; then
  log_message "INFO" "Creating test lead template..."
  cat > test_data_templates/test_lead.json << EOF
{
  "name": "John Test",
  "company": "Acme AI",
  "linkedin_url": "https://linkedin.com/in/fakejohnsmith"
}
EOF
fi

# Check if shared/leads.json exists
if [ ! -f "shared/leads.json" ]; then
  log_message "WARNING" "shared/leads.json not found. Creating new file."
  echo "[]" > shared/leads.json
else
  # Backup existing leads.json
  log_message "INFO" "Backing up existing leads.json..."
  cp shared/leads.json "${TEST_DIR}/leads.json.backup"
  check_status "Backup created: ${TEST_DIR}/leads.json.backup" "Failed to create backup of leads.json."
fi

# Inject test lead data
log_message "INFO" "Injecting test lead data..."
if [ -f "inject_test_data.py" ]; then
  python inject_test_data.py --template test_data_templates/test_lead.json --output shared/leads.json --backup
  check_status "Test lead data injected successfully." "Failed to inject test lead data."
else
  # Fallback to direct file creation
  cat > shared/leads.json << EOF
[{"name": "John Test","company": "Acme AI","linkedin_url": "https://linkedin.com/in/fakejohnsmith"}]
EOF
  check_status "Test lead data created successfully." "Failed to create test lead data."
fi

log_message "SUCCESS" "Test data preparation completed successfully."

# Step 3: Run the pipeline
log_message "INFO" "Step 3: Running the pipeline..."

# Run the pipeline
log_message "INFO" "Executing pipeline..."
if [ -f "run_pipeline_test.py" ]; then
  python run_pipeline_test.py --docker --output-dir $TEST_DIR
  pipeline_status=$?
else
  # Fallback to direct execution
  docker-compose exec -T 4runr-pipeline python run_pipeline.py > "${TEST_DIR}/pipeline_output.log" 2>&1
  pipeline_status=$?
fi

if [ $pipeline_status -eq 0 ]; then
  log_message "SUCCESS" "Pipeline execution completed successfully."
else
  log_message "ERROR" "Pipeline execution failed. Check logs for details."
fi

# Step 4: Monitor logs
log_message "INFO" "Step 4: Collecting logs..."

# Collect logs from all containers
log_message "INFO" "Collecting logs from all containers..."
if [ -f "monitor_logs.py" ]; then
  python monitor_logs.py --output "${TEST_DIR}/container_logs.log"
else
  # Fallback to direct log collection
  docker-compose logs --no-color > "${TEST_DIR}/container_logs.log" 2>&1
fi
check_status "Logs collected successfully." "Failed to collect logs."

# Step 5: Verify results
log_message "INFO" "Step 5: Verifying results..."

# Check if the enricher processed the test lead
log_message "INFO" "Checking if enricher processed the test lead..."
grep -E "Enriching lead.*John Test|Successfully enriched lead" "${TEST_DIR}/container_logs.log" > /dev/null 2>&1
enricher_status=$?

# Check if the engager processed the test lead
log_message "INFO" "Checking if engager processed the test lead..."
grep -E "Engaging with lead.*John Test|Message sent to John Test" "${TEST_DIR}/container_logs.log" > /dev/null 2>&1
engager_status=$?

# Check for container crashes or API failures
log_message "INFO" "Checking for container crashes or API failures..."
grep -E "Error|Exception|Failed|Crash" "${TEST_DIR}/container_logs.log" > "${TEST_DIR}/errors.log" 2>&1
error_count=$(wc -l < "${TEST_DIR}/errors.log")

# Generate test results
log_message "INFO" "Generating test results..."

# Create test results file
cat > "${TEST_DIR}/test_results.md" << EOF
# 4Runr AI Lead Scraper System Test Results

**Date:** $(date +"%Y-%m-%d %H:%M:%S")
**Test ID:** ${TIMESTAMP}

## Test Summary

EOF

# Add test summary based on results
if [ $enricher_status -eq 0 ] && [ $engager_status -eq 0 ] && [ $error_count -eq 0 ]; then
  echo "**Status:** ✅ PASS" >> "${TEST_DIR}/test_results.md"
  log_message "SUCCESS" "Test completed successfully!"
else
  echo "**Status:** ❌ FAIL" >> "${TEST_DIR}/test_results.md"
  log_message "ERROR" "Test failed. See ${TEST_DIR}/test_results.md for details."
fi

# Add component results
cat >> "${TEST_DIR}/test_results.md" << EOF

## Component Results

### Enricher
**Status:** $([ $enricher_status -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
**Details:** $([ $enricher_status -eq 0 ] && echo "Successfully enriched test lead" || echo "Failed to enrich test lead")

### Engager
**Status:** $([ $engager_status -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
**Details:** $([ $engager_status -eq 0 ] && echo "Successfully processed test lead for outreach" || echo "Failed to process test lead for outreach")

### System Health
**Status:** $([ $error_count -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
**Details:** $([ $error_count -eq 0 ] && echo "No errors detected" || echo "${error_count} errors detected")

## Log Files

- Full container logs: ${TEST_DIR}/container_logs.log
- Pipeline output: ${TEST_DIR}/pipeline_output.log
- Error log: ${TEST_DIR}/errors.log

EOF

# Add error details if any
if [ $error_count -gt 0 ]; then
  cat >> "${TEST_DIR}/test_results.md" << EOF
## Error Details

\`\`\`
$(head -n 20 "${TEST_DIR}/errors.log")
$([ $error_count -gt 20 ] && echo "... $(($error_count - 20)) more errors ..." || echo "")
\`\`\`
EOF
fi

log_message "INFO" "Test results saved to ${TEST_DIR}/test_results.md"

# Step 6: Clean up (optional)
log_message "INFO" "Test execution completed."
log_message "INFO" "To restore the original leads.json file, run:"
log_message "INFO" "cp ${TEST_DIR}/leads.json.backup shared/leads.json"

# Final message
log_message "SUCCESS" "System test completed. Please review the test results in ${TEST_DIR}/test_results.md"