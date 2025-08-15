#!/bin/bash

echo "🚀 DEPLOYING FINAL REAL 4RUNR ORGANISM"
echo "======================================"

# Stop and disable fake organism
echo "🛑 Stopping fake organism..."
sudo systemctl stop 4runr-organism 2>/dev/null || true
sudo systemctl disable 4runr-organism 2>/dev/null || true

# Remove old organism
echo "🧹 Cleaning old deployment..."
rm -rf /home/ubuntu/4runr-organism

# Create new deployment directory
echo "📁 Creating deployment directory..."
mkdir -p /home/ubuntu/4runr-real-organism
cd /home/ubuntu/4runr-real-organism

# Copy files
echo "📋 Copying REAL organism files..."
cp /home/ubuntu/4Runr-AI-Lead-System/final_real_deployment/* .

# Install Python packages
echo "📦 Installing Python packages..."
pip3 install --user --break-system-packages -r requirements.txt

# Create logs directory
mkdir -p logs
mkdir -p data

# Create systemd service for REAL organism
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/4runr-real-organism.service > /dev/null << EOF
[Unit]
Description=4Runr REAL Autonomous Organism - Real LinkedIn Lead Generation
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/4runr-real-organism
Environment=PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 autonomous_4runr_organism.py --run --cycles 10000
Restart=always
RestartSec=30
StandardOutput=append:/home/ubuntu/4runr-real-organism/logs/organism-service.log
StandardError=append:/home/ubuntu/4runr-real-organism/logs/organism-error.log
KillMode=process
TimeoutStopSec=60
MemoryMax=512M

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable 4runr-real-organism

echo ""
echo "🎉 FINAL REAL 4RUNR DEPLOYMENT COMPLETE!"
echo "========================================"
echo ""
echo "🧬 The REAL Autonomous Organism is ready!"
echo ""
echo "📋 COMMANDS:"
echo "sudo systemctl start 4runr-real-organism    # Start REAL organism"
echo "sudo systemctl stop 4runr-real-organism     # Stop REAL organism"  
echo "sudo systemctl status 4runr-real-organism   # Check status"
echo "sudo systemctl restart 4runr-real-organism  # Restart REAL organism"
echo ""
echo "📊 MONITORING:"
echo "tail -f logs/organism-service.log           # Watch live logs"
echo "journalctl -u 4runr-real-organism -f      # Watch systemd logs"
echo ""
echo "📁 LOCATION: /home/ubuntu/4runr-real-organism"
echo "📋 LOGS: /home/ubuntu/4runr-real-organism/logs"
echo ""
echo "🚀 To start: sudo systemctl start 4runr-real-organism"
echo ""
echo "⚠️  IMPORTANT: This organism uses REAL SerpAPI and REAL LinkedIn data!"
echo "   Make sure SERPAPI_KEY and AIRTABLE_API_KEY are set in environment"
echo ""
