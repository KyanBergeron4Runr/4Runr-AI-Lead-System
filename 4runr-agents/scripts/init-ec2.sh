#!/bin/bash
# Script to initialize the 4Runr multi-agent system on a new EC2 instance

# Exit on error
set -e

# Print commands before executing
set -x

# Update package lists
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Add the current user to the docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p ~/4runr-agents
cd ~/4runr-agents

# Clone the repository (if this is a real repository)
# git clone https://github.com/4runr/multi-agent-system.git .

# Create the directory structure
mkdir -p scraper enricher engager shared scripts

# Make the scripts executable
chmod +x scripts/*.sh

# Create a .env file from the example
cp .env.example .env

# Create a cron job to run the system daily
(crontab -l 2>/dev/null || echo "") | { cat; echo "0 9 * * * cd $HOME/4runr-agents && ./scripts/start.sh >> $HOME/4runr-cron.log 2>&1"; } | crontab -

echo "4Runr multi-agent system has been initialized!"
echo "Please log out and log back in for the docker group changes to take effect."
echo "Then, edit the .env file with your configuration and start the system:"
echo "cd ~/4runr-agents && ./scripts/start.sh"