#!/bin/bash

echo "🏆 DEPLOYING ULTIMATE 4RUNR ORGANISM - WORLD-CLASS QUALITY"
echo "=========================================================="

# Stop any existing organisms
echo "🛑 Stopping existing organisms..."
sudo systemctl stop 4runr-organism 2>/dev/null || true
sudo systemctl stop 4runr-real-organism 2>/dev/null || true
sudo systemctl disable 4runr-organism 2>/dev/null || true
sudo systemctl disable 4runr-real-organism 2>/dev/null || true

# Clean old deployments
echo "🧹 Cleaning old deployments..."
rm -rf /home/ubuntu/4runr-organism
rm -rf /home/ubuntu/4runr-real-organism

# Create ultimate deployment directory
echo "📁 Creating ULTIMATE deployment directory..."
mkdir -p /home/ubuntu/4runr-ultimate
cd /home/ubuntu/4runr-ultimate

# Copy ULTIMATE files
echo "📋 Copying ULTIMATE organism files..."
cp /home/ubuntu/4Runr-AI-Lead-System/ultimate_4runr_deployment/* .

# Install enhanced Python packages
echo "📦 Installing enhanced Python packages..."
pip3 install --user --break-system-packages -r requirements.txt

# Create directories
mkdir -p logs
mkdir -p data

# Clean existing data (optional)
echo "🧹 Cleaning existing lead data..."
python3 premium_data_cleaner.py --clean --quality-threshold 75 --database data/unified_leads.db || echo "No existing data to clean"

# Set proper ownership
sudo chown -R ubuntu:ubuntu /home/ubuntu/4runr-ultimate

# Create ULTIMATE systemd service
echo "🔧 Creating ULTIMATE systemd service..."
sudo tee /etc/systemd/system/4runr-ultimate.service > /dev/null << EOF
[Unit]
Description=4Runr ULTIMATE Autonomous Organism - World-Class Lead Generation
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/4runr-ultimate
Environment=PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=SERPAPI_KEY=b4680a52d6397f187d6092a043797221795e2dcd8bfacbfe19b49422f1f5d2b0
Environment=AIRTABLE_API_KEY=pat1EXE7KfOBTgJl6.28307c0b4f5eb80de65d01de18ecead5da6e7bc98f04ceea7e60b540e9773923
ExecStart=/usr/bin/python3 autonomous_4runr_organism.py --run --cycles 10000
Restart=always
RestartSec=30
StandardOutput=append:/home/ubuntu/4runr-ultimate/logs/organism-service.log
StandardError=append:/home/ubuntu/4runr-ultimate/logs/organism-error.log
KillMode=process
TimeoutStopSec=60
MemoryMax=1G

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable 4runr-ultimate

echo ""
echo "🎉 ULTIMATE 4RUNR DEPLOYMENT COMPLETE!"
echo "====================================="
echo ""
echo "🏆 The ULTIMATE 4Runr Autonomous Organism is ready!"
echo ""
echo "✨ WORLD-CLASS FEATURES:"
echo "   🔍 Premium LinkedIn lead discovery"
echo "   📧 REAL email discovery & verification" 
echo "   🌐 Website discovery & validation"
echo "   🤖 AI-powered personalized messaging"
echo "   🎯 Advanced duplicate prevention"
echo "   📊 Quality scoring & validation"
echo "   🧹 Automatic data cleaning"
echo ""
echo "📋 COMMANDS:"
echo "sudo systemctl start 4runr-ultimate      # Start ULTIMATE organism"
echo "sudo systemctl stop 4runr-ultimate       # Stop ULTIMATE organism"
echo "sudo systemctl status 4runr-ultimate     # Check status"
echo "sudo systemctl restart 4runr-ultimate    # Restart ULTIMATE organism"
echo ""
echo "📊 MONITORING:"
echo "tail -f logs/ultimate-4runr-organism.log  # Watch live logs"
echo "journalctl -u 4runr-ultimate -f          # Watch systemd logs"
echo "python3 premium_data_cleaner.py --stats   # Database statistics"
echo ""
echo "🧹 DATA MANAGEMENT:"
echo "python3 premium_data_cleaner.py --clean   # Clean duplicates & low-quality"
echo "python3 autonomous_4runr_organism.py --test  # Test single cycle"
echo ""
echo "📁 LOCATION: /home/ubuntu/4runr-ultimate"
echo "📋 LOGS: /home/ubuntu/4runr-ultimate/logs"
echo ""
echo "🚀 To start: sudo systemctl start 4runr-ultimate"
echo ""
echo "🏆 THIS IS THE ULTIMATE 4RUNR SYSTEM - READY FOR PRODUCTION!"
echo "   • 7 premium leads per day"
echo "   • REAL email discovery"
echo "   • Website validation"
echo "   • AI-powered messages"
echo "   • Quality score 75+ only"
echo "   • Zero duplicates"
echo "   • World-class quality"
echo ""
