#!/bin/bash
# Script to stop the 4Runr Multi-Agent System

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Stop the services
echo "Stopping services..."
docker-compose down

# Print status
echo "Services stopped successfully"