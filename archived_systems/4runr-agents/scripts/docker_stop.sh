#!/bin/bash
# Script to stop the 4Runr multi-agent system running in Docker Compose

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Stop the containers
echo "Stopping 4Runr multi-agent system..."
docker-compose down

# Show the status
echo "Container status:"
docker ps