#!/bin/bash
# 4Runr AI Lead Scraper System Setup and Test
# This script sets up and runs a full system test of the 4Runr AI Lead Scraper system

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
  
  echo -e "${color}[$(date +"%Y-%m-%d %H:%M:%S")] [${level}] ${message}${NC}"
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

# Check if Docker is running
log_message "INFO" "Checking if Docker is running..."
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
  log_message "ERROR" "Docker is not running. Please start Docker and try again."
  exit 1
fi
log_message "SUCCESS" "Docker is running."

# Check if docker-compose is available
log_message "INFO" "Checking if docker-compose is available..."
docker-compose --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
  log_message "ERROR" "docker-compose is not available. Please install it and try again."
  exit 1
fi
log_message "SUCCESS" "docker-compose is available."

# Rebuild Docker containers with updated dependencies
log_message "INFO" "Rebuilding Docker containers with updated dependencies..."
docker-compose build
check_status "Docker containers rebuilt successfully." "Failed to rebuild Docker containers."

# Start Docker containers
log_message "INFO" "Starting Docker containers..."
docker-compose up -d
check_status "Docker containers started successfully." "Failed to start Docker containers."

# Check if all containers are running
log_message "INFO" "Checking if all containers are running..."
docker-compose ps | grep -E 'scraper|enricher|engager|pipeline|cron' > /dev/null 2>&1
check_status "All required containers are running." "Some containers are not running."

# Run the system test
log_message "INFO" "Running system test..."
./run_full_system_test.sh
check_status "System test completed successfully." "System test failed."

log_message "SUCCESS" "Setup and test completed successfully."