#!/bin/bash
# Script to test the 4Runr multi-agent system

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create a temporary .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating temporary .env file for testing..."
    cp .env.example .env
fi

# Clear any existing data
echo "Clearing existing data..."
rm -f shared/*.json

# Build the containers
echo "Building containers..."
docker-compose build

# Run the scraper in test mode
echo "Running scraper in test mode..."
docker-compose run --rm -e SCRAPER_LEAD_COUNT=3 -e SCRAPER_DELAY_SECONDS=10 scraper

# Wait for the scraper to finish
echo "Waiting for scraper to generate leads..."
sleep 15

# Check if scraped_leads.json was created
if [ ! -f shared/scraped_leads.json ]; then
    echo "Error: Scraper did not generate leads."
    exit 1
fi

echo "Scraper test passed! Leads were generated."

# Run the enricher in test mode
echo "Running enricher in test mode..."
docker-compose run --rm -e ENRICHER_DELAY_SECONDS=10 enricher

# Wait for the enricher to finish
echo "Waiting for enricher to process leads..."
sleep 15

# Check if enriched_leads.json was created
if [ ! -f shared/enriched_leads.json ]; then
    echo "Error: Enricher did not process leads."
    exit 1
fi

echo "Enricher test passed! Leads were enriched."

# Run the engager in test mode
echo "Running engager in test mode..."
docker-compose run --rm -e ENGAGER_DELAY_SECONDS=10 engager

# Wait for the engager to finish
echo "Waiting for engager to process leads..."
sleep 15

# Check if engaged_leads.json was created
if [ ! -f shared/engaged_leads.json ]; then
    echo "Error: Engager did not process leads."
    exit 1
fi

echo "Engager test passed! Leads were engaged."

echo "All tests passed! The 4Runr multi-agent system is working correctly."