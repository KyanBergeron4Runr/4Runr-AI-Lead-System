#!/bin/bash
# Script to view logs from the 4Runr multi-agent system

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Check if an agent name was provided
if [ -z "$1" ]; then
    # View all logs
    docker-compose logs -f
else
    # View logs for a specific agent
    if [ "$1" == "scraper" ] || [ "$1" == "enricher" ] || [ "$1" == "engager" ]; then
        docker-compose logs -f "$1"
    else
        echo "Error: Invalid agent name. Choose from: scraper, enricher"
        exit 1
    fi
fi