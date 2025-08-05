#!/bin/bash
# Script to reset the 4Runr multi-agent system and clear all data

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Stop the containers
echo "Stopping 4Runr multi-agent system..."
docker-compose down

# Clear the shared directory
echo "Clearing shared data..."
rm -f shared/*.json

# Rebuild and restart the containers
echo "Rebuilding and restarting the system..."
docker-compose up -d --build

# Show the status
echo "Container status:"
docker-compose ps

echo "System has been reset. To view logs, run: docker-compose logs -f"