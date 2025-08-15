#!/bin/bash
"""
EC2 Deployment Script for 4Runr Autonomous Organism
Deploy the living organism system to production EC2 instance
"""

echo "🚀 DEPLOYING 4RUNR AUTONOMOUS ORGANISM TO EC2"
echo "=============================================="

# Set deployment variables
DEPLOY_DIR="/home/ubuntu/4runr-organism"
SERVICE_NAME="4runr-organism"
LOG_DIR="/home/ubuntu/4runr-organism/logs"

# Create deployment directory
echo "📁 Creating deployment directory..."
sudo mkdir -p $DEPLOY_DIR
sudo mkdir -p $LOG_DIR
sudo chown ubuntu:ubuntu $DEPLOY_DIR
sudo chown ubuntu:ubuntu $LOG_DIR

# Copy essential files
echo "📋 Copying organism files..."
cp autonomous_4runr_organism.py $DEPLOY_DIR/
cp final_working_system.py $DEPLOY_DIR/
cp smart_search_strategy.md $DEPLOY_DIR/
cp AUTONOMOUS_ORGANISM_DEPLOYMENT.md $DEPLOY_DIR/

# Create EC2-specific configuration
echo "⚙️ Creating EC2 configuration..."
cat > $DEPLOY_DIR/ec2_config.py << 'EOF'
"""
EC2 Configuration for 4Runr Autonomous Organism
"""

import os

class EC2Config:
    """Production configuration for EC2 deployment"""
    
    # Database path
    DATABASE_PATH = "/home/ubuntu/4runr-organism/data/unified_leads.db"
    
    # API Keys (these should be set via environment variables)
    AIRTABLE_API_KEY = "pat1EXE7KfOBTgJl6.28307c0b4f5eb80de65d01de18ecead5da6e7bc98f04ceea7e60b540e9773923"
    AIRTABLE_BASE_ID = "appBZvPvNXGqtoJdc"
    SERPAPI_KEY = "f37d76b91b6fbb5b92ae62c6cf6a1ccfba8b7b6e4a98dd2cbf5bf4c5fe6a07d6"
    
    # Production settings
    MAX_CYCLES = 10000  # Run virtually forever
    CYCLE_INTERVAL = 300  # 5 minutes between cycles
    MAX_LEADS_PER_CYCLE = 3
    MIN_LEADS_TARGET = 5
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_ROTATION = True
    
    # Health monitoring
    HEALTH_CHECK_INTERVAL = 300  # 5 minutes
    CRITICAL_HEALTH_THRESHOLD = 2
    
    # Performance
    ADAPTIVE_SLEEP = True
    MIN_SLEEP_TIME = 30
    MAX_SLEEP_TIME = 600
EOF

# Create systemd service file
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/4runr-organism.service > /dev/null << EOF
[Unit]
Description=4Runr Autonomous Organism - Lead Generation System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/bin/python3 autonomous_4runr_organism.py --run --cycles 10000 --interval 300
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/organism-service.log
StandardError=append:$LOG_DIR/organism-error.log

# Environment variables
Environment=PYTHONPATH=$DEPLOY_DIR
Environment=PYTHONUNBUFFERED=1

# Resource limits
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# Create data directory and copy database
echo "💾 Setting up database..."
mkdir -p $DEPLOY_DIR/data
if [ -f "data/unified_leads.db" ]; then
    cp data/unified_leads.db $DEPLOY_DIR/data/
    echo "✅ Database copied to EC2"
else
    echo "⚠️ Database not found locally - will be created on first run"
fi

# Install Python dependencies
echo "📦 Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip sqlite3

# Install Python packages
pip3 install requests python-dotenv

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R ubuntu:ubuntu $DEPLOY_DIR
chmod +x $DEPLOY_DIR/autonomous_4runr_organism.py

# Create startup script
echo "🚀 Creating startup script..."
cat > $DEPLOY_DIR/start_organism.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/4runr-organism
echo "🧬 Starting 4Runr Autonomous Organism..."
echo "Time: $(date)"
python3 autonomous_4runr_organism.py --run --cycles 10000 --interval 300
EOF

chmod +x $DEPLOY_DIR/start_organism.sh

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > $DEPLOY_DIR/monitor_organism.sh << 'EOF'
#!/bin/bash
echo "🧬 4RUNR ORGANISM STATUS"
echo "======================"
echo "Time: $(date)"
echo ""

# Check if service is running
if systemctl is-active --quiet 4runr-organism; then
    echo "✅ Service Status: RUNNING"
else
    echo "❌ Service Status: STOPPED"
fi

# Check recent logs
echo ""
echo "📋 Recent Activity (last 10 lines):"
tail -n 10 /home/ubuntu/4runr-organism/logs/organism-service.log 2>/dev/null || echo "No logs found"

# Check database
echo ""
echo "💾 Database Status:"
if [ -f "/home/ubuntu/4runr-organism/data/unified_leads.db" ]; then
    LEAD_COUNT=$(sqlite3 /home/ubuntu/4runr-organism/data/unified_leads.db "SELECT COUNT(*) FROM leads;" 2>/dev/null || echo "Error")
    echo "Total leads in database: $LEAD_COUNT"
else
    echo "❌ Database not found"
fi

# Check system resources
echo ""
echo "💻 System Resources:"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
EOF

chmod +x $DEPLOY_DIR/monitor_organism.sh

# Enable and start service
echo "🔄 Enabling systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable 4runr-organism.service

echo ""
echo "🎉 EC2 DEPLOYMENT COMPLETE!"
echo "=========================="
echo ""
echo "🧬 The 4Runr Autonomous Organism is ready to deploy on EC2!"
echo ""
echo "📋 DEPLOYMENT COMMANDS:"
echo "sudo systemctl start 4runr-organism    # Start the organism"
echo "sudo systemctl stop 4runr-organism     # Stop the organism"
echo "sudo systemctl status 4runr-organism   # Check organism status"
echo "sudo systemctl restart 4runr-organism  # Restart the organism"
echo ""
echo "📊 MONITORING COMMANDS:"
echo "./monitor_organism.sh                   # Check organism health"
echo "tail -f logs/organism-service.log       # Watch live logs"
echo "journalctl -u 4runr-organism -f        # Watch systemd logs"
echo ""
echo "📁 DEPLOYMENT LOCATION: $DEPLOY_DIR"
echo "📋 LOG LOCATION: $LOG_DIR"
echo ""
echo "🚀 To start the organism: sudo systemctl start 4runr-organism"
