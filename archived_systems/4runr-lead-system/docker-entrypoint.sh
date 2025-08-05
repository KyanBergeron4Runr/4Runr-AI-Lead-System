#!/bin/sh
set -e

# Print environment information
echo "Node.js version: $(node -v)"
echo "NPM version: $(npm -v)"
echo "Working directory: $(pwd)"

# Check if .env file exists
if [ -f .env ]; then
  echo "Using .env file for configuration"
else
  echo "No .env file found. Using environment variables from the system."
fi

# Execute the command passed to docker run
exec "$@"