#!/bin/bash
# Script to run the 4Runr multi-agent system using Docker Compose

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one from .env.example"
    echo "cp .env.example .env"
    exit 1
fi

# Build and start the containers
echo "Building and starting 4Runr multi-agent system..."
docker-compose up --build -d

# Show the logs
echo "Showing logs (press Ctrl+C to exit)..."
docker-compose logs -f