#!/bin/bash
# 4Runr AI Lead System - EC2 Deployment Script

set -e

echo "Starting 4Runr AI Lead System deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv git

# Create application directory
sudo mkdir -p /opt/4runr
sudo chown ubuntu:ubuntu /opt/4runr

# Copy application files
cp -r * /opt/4runr/

# Set up virtual environment
cd /opt/4runr
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set up database directory
mkdir -p /opt/4runr/data
mkdir -p /opt/4runr/logs
mkdir -p /opt/4runr/backups

# Set permissions
chmod +x /opt/4runr/system_controller.py
chmod +x /opt/4runr/email_delivery_system.py

# Run initial system setup
python3 system_controller.py --deploy

# Set up systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable 4runr-automation
sudo systemctl enable 4runr-brain
sudo systemctl enable 4runr-email

sudo systemctl start 4runr-automation
sudo systemctl start 4runr-brain
sudo systemctl start 4runr-email

# Set up cron jobs
crontab cron_jobs.txt

echo "Deployment complete!"
echo "Check service status with: sudo systemctl status 4runr-automation"
echo "View logs with: journalctl -u 4runr-automation -f"
