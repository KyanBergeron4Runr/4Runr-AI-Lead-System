#!/bin/bash
# Script to initialize an EC2 instance for the 4Runr Multi-Agent System
# This script installs Docker, Docker Compose, clones the repository, and sets up the environment

set -e  # Exit on error

# Print section header
print_header() {
  echo "============================================"
  echo "  $1"
  echo "============================================"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Update package lists
print_header "Updating package lists"
apt-get update

# Install prerequisites
print_header "Installing prerequisites"
apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  git \
  unzip \
  jq

# Install Docker
print_header "Installing Docker"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
print_header "Installing Docker Compose"
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r '.tag_name')
curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add ubuntu user to docker group
print_header "Adding user to docker group"
usermod -aG docker ubuntu

# Create project directory
print_header "Creating project directory"
PROJECT_DIR="/home/ubuntu/4runr-agents"
mkdir -p $PROJECT_DIR
chown ubuntu:ubuntu $PROJECT_DIR

# Clone the repository (if provided)
if [ -n "$1" ]; then
  print_header "Cloning repository"
  su - ubuntu -c "git clone $1 $PROJECT_DIR"
else
  echo "No repository URL provided, skipping clone"
  echo "You'll need to manually copy the project files to $PROJECT_DIR"
fi

# Create necessary directories
print_header "Creating necessary directories"
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/shared
chown -R ubuntu:ubuntu $PROJECT_DIR

# Create .env file from .env.example if it exists
if [ -f "$PROJECT_DIR/.env.example" ]; then
  print_header "Creating .env file"
  cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env
  echo "Created .env file from .env.example"
  echo "Please edit $PROJECT_DIR/.env with your actual configuration"
else
  echo "No .env.example file found, skipping .env creation"
  echo "You'll need to manually create a .env file in $PROJECT_DIR"
fi

# Set up cron job for log rotation
print_header "Setting up log rotation"
cat > /etc/logrotate.d/4runr-agents << EOF
$PROJECT_DIR/logs/*.log {
  daily
  missingok
  rotate 7
  compress
  delaycompress
  notifempty
  create 0640 ubuntu ubuntu
}
EOF

# Set up cron job for the pipeline
print_header "Setting up cron job"
CRON_JOB="0 */6 * * * cd $PROJECT_DIR && docker-compose run --rm pipeline >> $PROJECT_DIR/logs/pipeline.log 2>&1"
(crontab -u ubuntu -l 2>/dev/null || echo "") | grep -v "docker-compose run --rm pipeline" | { cat; echo "$CRON_JOB"; } | crontab -u ubuntu -

# Start the services
print_header "Starting services"
cd $PROJECT_DIR
docker-compose up -d

# Print completion message
print_header "Setup complete"
echo "The 4Runr Multi-Agent System has been set up on this EC2 instance."
echo ""
echo "Next steps:"
echo "1. Edit the .env file: nano $PROJECT_DIR/.env"
echo "2. Restart the services: cd $PROJECT_DIR && docker-compose restart"
echo "3. Check the logs: cd $PROJECT_DIR && docker-compose logs -f"
echo ""
echo "The pipeline will run automatically every 6 hours via cron."
echo "You can also run it manually: cd $PROJECT_DIR && docker-compose run --rm pipeline"
echo ""
echo "For more information, see the README.md file in the project directory."