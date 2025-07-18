#!/bin/bash
# Script to test the Docker setup

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Create a log file
LOG_FILE="docker_test_$(date +%Y%m%d_%H%M%S).log"

echo "Testing Docker setup..."
echo "Log file: $LOG_FILE"

# Build the Docker images
echo "Building Docker images..." | tee -a "$LOG_FILE"
docker-compose build 2>&1 | tee -a "$LOG_FILE"

# Check if the build was successful
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "❌ Docker build failed" | tee -a "$LOG_FILE"
    exit 1
fi

echo "✅ Docker build successful" | tee -a "$LOG_FILE"

# Run the pipeline
echo "Running the pipeline..." | tee -a "$LOG_FILE"
docker-compose run --rm pipeline 2>&1 | tee -a "$LOG_FILE"

# Check if the pipeline run was successful
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "❌ Pipeline run failed" | tee -a "$LOG_FILE"
    exit 1
fi

echo "✅ Pipeline run successful" | tee -a "$LOG_FILE"

# Check if the leads.json file was created
if [ -f "shared/leads.json" ]; then
    echo "✅ Leads file created: shared/leads.json" | tee -a "$LOG_FILE"
    echo "Contents:" | tee -a "$LOG_FILE"
    cat shared/leads.json | tee -a "$LOG_FILE"
else
    echo "❌ Leads file not created" | tee -a "$LOG_FILE"
    exit 1
fi

echo -e "\n✅ Docker test completed successfully!" | tee -a "$LOG_FILE"
echo "See $LOG_FILE for details" | tee -a "$LOG_FILE"