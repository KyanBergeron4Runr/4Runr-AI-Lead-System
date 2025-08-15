#!/usr/bin/env python3
"""
Deploy FINAL REAL 4Runr System to EC2
=====================================
Stop fake organism and deploy REAL organism with REAL data
"""

import os
import shutil
import json
from datetime import datetime

def create_deployment_package():
    """Create clean deployment package with REAL organism"""
    
    print("🚀 Creating FINAL REAL deployment package...")
    
    # Create deployment directory
    deployment_dir = "final_real_deployment"
    if os.path.exists(deployment_dir):
        shutil.rmtree(deployment_dir)
    os.makedirs(deployment_dir)
    
    # Copy the FINAL REAL organism
    shutil.copy("final_real_organism.py", f"{deployment_dir}/autonomous_4runr_organism.py")
    print("✅ Copied REAL organism as autonomous_4runr_organism.py")
    
    # Create requirements
    requirements = """google-search-results>=2.4.2
requests>=2.25.0
python-dotenv>=0.19.0
pyairtable>=1.5.0
"""
    
    with open(f"{deployment_dir}/requirements.txt", "w") as f:
        f.write(requirements)
    print("✅ Created requirements.txt")
    
    # Create EC2 deployment script
    deploy_script = """#!/bin/bash

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
"""
    
    with open(f"{deployment_dir}/deploy_real.sh", "w", encoding='utf-8') as f:
        f.write(deploy_script)
    
    # Make executable
    os.chmod(f"{deployment_dir}/deploy_real.sh", 0o755)
    print("✅ Created deploy_real.sh")
    
    # Create environment template
    env_template = """# 4Runr REAL Organism Environment Variables
# Copy this to .env or set in your shell

# Required: SerpAPI key for real LinkedIn scraping
SERPAPI_KEY=your_serpapi_key_here

# Required: Airtable API key for data sync
AIRTABLE_API_KEY=your_airtable_api_key_here

# Optional: Airtable base ID (defaults to appBZvPvNXGqtoJdc)
AIRTABLE_BASE_ID=appBZvPvNXGqtoJdc

# Optional: Airtable table name (defaults to "Table 1")
AIRTABLE_TABLE_NAME=Table 1
"""
    
    with open(f"{deployment_dir}/.env.example", "w", encoding='utf-8') as f:
        f.write(env_template)
    print("✅ Created .env.example")
    
    # Create README
    readme = """# FINAL REAL 4Runr Autonomous Organism

## 🎯 REAL DATA ONLY
This organism uses REAL SerpAPI searches to find REAL LinkedIn professionals.
NO MORE FAKE DATA!

## 🚀 Deployment

1. Copy this package to your EC2 instance
2. Set environment variables (SERPAPI_KEY, AIRTABLE_API_KEY)
3. Run: `chmod +x deploy_real.sh && sudo ./deploy_real.sh`
4. Start: `sudo systemctl start 4runr-real-organism`

## 📊 Rate Limiting
- 7 real leads per day
- 1 lead every ~3.4 hours
- Sustainable for long-term operation

## 🔍 What It Does
1. Searches LinkedIn via SerpAPI for real professionals
2. Validates LinkedIn URLs are working
3. Enriches with email guesses and AI messages
4. Saves to local SQLite database
5. Syncs to Airtable with all fields

## 📋 Monitoring
```bash
# Check if running
sudo systemctl status 4runr-real-organism

# Watch live logs
tail -f logs/organism-service.log

# Check systemd logs
journalctl -u 4runr-real-organism -f
```

## ⚠️ Environment Variables Required
- `SERPAPI_KEY`: Your SerpAPI key
- `AIRTABLE_API_KEY`: Your Airtable API key

## 🏆 Success Metrics
- REAL LinkedIn URLs that work
- REAL professional names and companies
- Valid email address patterns
- Complete Airtable field population
- No duplicate leads
"""
    
    with open(f"{deployment_dir}/README.md", "w", encoding='utf-8') as f:
        f.write(readme)
    print("✅ Created README.md")
    
    # Create manifest
    manifest = {
        "deployment": "final_real_4runr_organism",
        "version": "1.0.0",
        "created": datetime.now().isoformat(),
        "description": "FINAL REAL 4Runr Autonomous Organism with SerpAPI integration",
        "components": [
            "autonomous_4runr_organism.py - REAL organism with SerpAPI",
            "deploy_real.sh - EC2 deployment script", 
            "requirements.txt - Python dependencies",
            ".env.example - Environment variables template",
            "README.md - Deployment instructions"
        ],
        "features": [
            "REAL LinkedIn lead scraping via SerpAPI",
            "LinkedIn URL validation",
            "Professional email generation",
            "AI message creation",
            "Complete Airtable sync with all fields",
            "Rate limiting: 7 leads per day",
            "Duplicate prevention",
            "Autonomous operation with self-healing"
        ]
    }
    
    with open(f"{deployment_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print("✅ Created manifest.json")
    
    print(f"""
🎉 FINAL REAL DEPLOYMENT PACKAGE CREATED!
========================================

📁 Location: {deployment_dir}/
📋 Files created:
   ✅ autonomous_4runr_organism.py (REAL organism)
   ✅ deploy_real.sh (EC2 deployment script)
   ✅ requirements.txt (Python dependencies)
   ✅ .env.example (Environment template)
   ✅ README.md (Instructions)
   ✅ manifest.json (Deployment info)

🚀 DEPLOYMENT STEPS:
1. Copy {deployment_dir}/ to your EC2 instance
2. Set SERPAPI_KEY and AIRTABLE_API_KEY environment variables
3. Run: cd {deployment_dir} && chmod +x deploy_real.sh && sudo ./deploy_real.sh
4. Start: sudo systemctl start 4runr-real-organism

⚠️  This will STOP the fake organism and deploy REAL organism!
🏆 Result: REAL LinkedIn leads with REAL data in your Airtable!
""")

if __name__ == "__main__":
    create_deployment_package()
