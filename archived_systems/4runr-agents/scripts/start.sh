#!/bin/bash
# Script to start the 4Runr Multi-Agent System for local development

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Error: .env file not found"
  echo "Creating .env file from .env.example..."
  cp .env.example .env
  echo "Please edit the .env file with your actual configuration"
  exit 1
fi

# Create necessary directories
mkdir -p logs
mkdir -p shared

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running"
  echo "Please start Docker and try again"
  exit 1
fi

# Build and start the services
echo "Building and starting services..."
docker-compose up -d

# Print status
echo "Services started successfully"
echo "To view logs: docker-compose logs -f"
echo "To stop services: ./scripts/stop.sh"