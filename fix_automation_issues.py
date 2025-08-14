#!/usr/bin/env python3
"""
Fix Automation Issues - Comprehensive fix script
Addresses all the automation issues identified in the diagnostic
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime

def fix_missing_ai_messages():
    """Fix missing AI messages by running the message generator"""
    print("🔧 Fixing Missing AI Messages")
    print("=" * 50)
    
    try:
        # Check if message generator exists
        message_gen_path = Path("4runr-outreach-system/message_generator/app.py")
        if not message_gen_path.exists():
            print("❌ Message generator not found")
            return False
        
        print("✅ Message generator found, running for leads without AI messages...")
        
        # Run message generator
        cmd = [
            sys.executable, 
            str(message_gen_path), 
            "--limit", "20",
            "--force"  # Force regeneration for leads without messages
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Message generator completed successfully")
            print("Output:", result.stdout)
            return True
        else:
            print("❌ Message generator failed")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running message generator: {e}")
        return False

def fix_incomplete_enrichment():
    """Fix incomplete enrichment by running the enricher agent"""
    print("\n🔧 Fixing Incomplete Enrichment")
    print("=" * 50)
    
    try:
        # Check if enricher agent exists
        enricher_path = Path("4runr-outreach-system/daily_enricher_agent_updated.py")
        if not enricher_path.exists():
            print("❌ Enricher agent not found")
            return False
        
        print("✅ Enricher agent found, running for unenriched leads...")
        
        # Run enricher agent
        cmd = [
            sys.executable, 
            str(enricher_path), 
            "--max-leads", "50"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Enricher agent completed successfully")
            print("Output:", result.stdout)
            return True
        else:
            print("❌ Enricher agent failed")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running enricher agent: {e}")
        return False

def fix_daily_scraping():
    """Fix daily scraping by running the daily scraper"""
    print("\n🔧 Fixing Daily Scraping")
    print("=" * 50)
    
    try:
        # Check if daily scraper exists
        scraper_path = Path("4runr-lead-scraper/scripts/daily_scraper.py")
        if not scraper_path.exists():
            print("❌ Daily scraper not found")
            return False
        
        print("✅ Daily scraper found, running to get new leads...")
        
        # Run daily scraper
        cmd = [
            sys.executable, 
            str(scraper_path), 
            "--max-leads", "5"  # Start with 5 leads
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Daily scraper completed successfully")
            print("Output:", result.stdout)
            return True
        else:
            print("❌ Daily scraper failed")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running daily scraper: {e}")
        return False

def create_daily_sync_script():
    """Create the missing daily_sync.sh script"""
    print("\n🔧 Creating Daily Sync Script")
    print("=" * 50)
    
    try:
        # Create the daily sync script
        sync_script_content = """#!/bin/bash
# 4Runr AI Lead System - Daily Sync Script
# Runs daily automation for lead scraping, enrichment, and messaging

set -e

# Set up environment
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

# Log file
LOG_FILE="logs/daily_sync_$(date +%Y%m%d).log"
mkdir -p logs

echo "$(date): Starting daily sync" >> "$LOG_FILE"

# Step 1: Run daily scraper to get new leads
echo "$(date): Running daily scraper..." >> "$LOG_FILE"
python 4runr-lead-scraper/scripts/daily_scraper.py --max-leads 5 >> "$LOG_FILE" 2>&1

# Step 2: Run enricher agent to enrich existing leads
echo "$(date): Running enricher agent..." >> "$LOG_FILE"
python 4runr-outreach-system/daily_enricher_agent_updated.py --max-leads 20 >> "$LOG_FILE" 2>&1

# Step 3: Run message generator for leads without AI messages
echo "$(date): Running message generator..." >> "$LOG_FILE"
python 4runr-outreach-system/message_generator/app.py --limit 20 >> "$LOG_FILE" 2>&1

# Step 4: Sync to Airtable
echo "$(date): Syncing to Airtable..." >> "$LOG_FILE"
python 4runr-lead-scraper/run_cli.py sync --to-airtable >> "$LOG_FILE" 2>&1

echo "$(date): Daily sync completed" >> "$LOG_FILE"
"""
        
        sync_script_path = Path("4runr-outreach-system/daily_sync.sh")
        with open(sync_script_path, 'w') as f:
            f.write(sync_script_content)
        
        # Make executable
        os.chmod(sync_script_path, 0o755)
        
        print(f"✅ Created daily sync script: {sync_script_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating daily sync script: {e}")
        return False

def create_cron_setup_script():
    """Create a script to set up cron jobs"""
    print("\n🔧 Creating Cron Setup Script")
    print("=" * 50)
    
    try:
        # Create cron setup script
        cron_setup_content = """#!/bin/bash
# 4Runr AI Lead System - Cron Setup Script
# Sets up automated daily processing

echo "Setting up 4Runr AI Lead System cron jobs..."

# Get the current directory
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create log directory
mkdir -p "$PROJECT_DIR/logs"

# Add cron jobs
(crontab -l 2>/dev/null; cat << EOF
# 4Runr AI Lead System - Daily Automation
# Daily sync at 6 AM
0 6 * * * cd "$PROJECT_DIR" && bash 4runr-outreach-system/daily_sync.sh

# Health check every hour
0 * * * * cd "$PROJECT_DIR" && python system_controller.py --health-check >> logs/health_check.log 2>&1

# Weekly database maintenance on Sunday at 2 AM
0 2 * * 0 cd "$PROJECT_DIR" && python 4runr-lead-scraper/run_cli.py db --vacuum >> logs/maintenance.log 2>&1
EOF
) | crontab -

echo "✅ Cron jobs set up successfully!"
echo "Jobs added:"
echo "  - Daily sync at 6:00 AM"
echo "  - Health check every hour"
echo "  - Weekly maintenance on Sundays at 2:00 AM"
echo ""
echo "To view cron jobs: crontab -l"
echo "To edit cron jobs: crontab -e"
"""
        
        cron_setup_path = Path("setup_cron.sh")
        with open(cron_setup_path, 'w') as f:
            f.write(cron_setup_content)
        
        # Make executable
        os.chmod(cron_setup_path, 0o755)
        
        print(f"✅ Created cron setup script: {cron_setup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating cron setup script: {e}")
        return False

def create_systemd_service():
    """Create systemd service for 24/7 operation"""
    print("\n🔧 Creating Systemd Service")
    print("=" * 50)
    
    try:
        # Create systemd service file
        service_content = """[Unit]
Description=4Runr AI Lead System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/4Runr-AI-Lead-System
Environment=PATH=/home/ubuntu/4Runr-AI-Lead-System/.venv/bin
ExecStart=/home/ubuntu/4Runr-AI-Lead-System/.venv/bin/python system_controller.py --autonomous
Restart=always
RestartSec=300
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        service_path = Path("4runr-ai-system.service")
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Created systemd service file: {service_path}")
        print("To install the service on EC2:")
        print("  sudo cp 4runr-ai-system.service /etc/systemd/system/")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable 4runr-ai-system")
        print("  sudo systemctl start 4runr-ai-system")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating systemd service: {e}")
        return False

def test_individual_components():
    """Test individual components to ensure they work"""
    print("\n🔧 Testing Individual Components")
    print("=" * 50)
    
    tests = [
        {
            "name": "Lead Scraper",
            "command": [sys.executable, "4runr-lead-scraper/simple_cli.py", "stats"],
            "description": "Test lead scraper statistics"
        },
        {
            "name": "Message Generator",
            "command": [sys.executable, "4runr-outreach-system/message_generator/app.py", "--limit", "1"],
            "description": "Test message generator with 1 lead"
        },
        {
            "name": "Enricher Agent",
            "command": [sys.executable, "4runr-outreach-system/daily_enricher_agent_updated.py", "--max-leads", "1"],
            "description": "Test enricher agent with 1 lead"
        },
        {
            "name": "System Controller",
            "command": [sys.executable, "system_controller.py", "--health"],
            "description": "Test system controller health check"
        }
    ]
    
    results = {}
    
    for test in tests:
        print(f"Testing {test['name']}...")
        try:
            result = subprocess.run(test["command"], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"✅ {test['name']}: PASSED")
                results[test['name']] = True
            else:
                print(f"❌ {test['name']}: FAILED")
                print(f"   Error: {result.stderr}")
                results[test['name']] = False
        except subprocess.TimeoutExpired:
            print(f"⏰ {test['name']}: TIMEOUT")
            results[test['name']] = False
        except Exception as e:
            print(f"❌ {test['name']}: ERROR - {e}")
            results[test['name']] = False
    
    return results

def create_deployment_guide():
    """Create a comprehensive deployment guide"""
    print("\n🔧 Creating Deployment Guide")
    print("=" * 50)
    
    guide_content = """# 4Runr AI Lead System - Automation Fix Guide

## 🎯 Issues Identified and Fixed

### 1. Missing AI Messages (88.5% of leads)
- **Problem**: Only 11.5% of leads have AI messages
- **Fix**: Run message generator for all leads without messages
- **Command**: `python 4runr-outreach-system/message_generator/app.py --limit 20`

### 2. Incomplete Enrichment (96.2% of leads unenriched)
- **Problem**: Only 3.8% of leads are marked as enriched
- **Fix**: Run enricher agent for unenriched leads
- **Command**: `python 4runr-outreach-system/daily_enricher_agent_updated.py --max-leads 50`

### 3. No Daily Automation
- **Problem**: No cron jobs or systemd services running
- **Fix**: Set up automated daily processing
- **Script**: `bash setup_cron.sh`

### 4. Missing Daily Sync Script
- **Problem**: `daily_sync.sh` referenced but doesn't exist
- **Fix**: Created comprehensive daily sync script

## 🚀 Deployment Steps

### Step 1: Fix Current Data
```bash
# Fix missing AI messages
python 4runr-outreach-system/message_generator/app.py --limit 20

# Fix incomplete enrichment
python 4runr-outreach-system/daily_enricher_agent_updated.py --max-leads 50

# Get new leads
python 4runr-lead-scraper/scripts/daily_scraper.py --max-leads 5
```

### Step 2: Set Up Automation (EC2)
```bash
# Make scripts executable
chmod +x setup_cron.sh
chmod +x 4runr-outreach-system/daily_sync.sh

# Set up cron jobs
bash setup_cron.sh

# Set up systemd service (optional)
sudo cp 4runr-ai-system.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 4runr-ai-system
sudo systemctl start 4runr-ai-system
```

### Step 3: Verify Setup
```bash
# Check cron jobs
crontab -l

# Check systemd service status
sudo systemctl status 4runr-ai-system

# Test individual components
python system_controller.py --health
```

## 📊 Expected Results

After running the fixes:
- **AI Messages**: Should increase from 11.5% to 100%
- **Enrichment**: Should increase from 3.8% to 100%
- **Daily Automation**: Should run automatically at 6 AM
- **New Leads**: Should scrape 5 new leads daily

## 🔧 Monitoring

### Check Daily Sync Logs
```bash
tail -f logs/daily_sync_$(date +%Y%m%d).log
```

### Check System Health
```bash
python system_controller.py --health
```

### Check Database Status
```bash
python check_database_status.py
```

## 🆘 Troubleshooting

### If automation stops working:
1. Check cron jobs: `crontab -l`
2. Check systemd service: `sudo systemctl status 4runr-ai-system`
3. Check logs: `tail -f logs/daily_sync_*.log`
4. Restart services: `sudo systemctl restart 4runr-ai-system`

### If components fail:
1. Test individually: `python system_controller.py --health`
2. Check API keys: Ensure all required keys are configured
3. Check database: `python check_database_status.py`

## 📈 Success Metrics

- ✅ All leads have AI messages
- ✅ All leads are enriched
- ✅ Daily automation running
- ✅ 5 new leads scraped daily
- ✅ Airtable sync working
- ✅ System health checks passing
"""
    
    guide_path = Path("AUTOMATION_FIX_GUIDE.md")
    with open(guide_path, 'w') as f:
        f.write(guide_content)
    
    print(f"✅ Created deployment guide: {guide_path}")
    return True

def main():
    """Run all fixes"""
    print("🔧 4Runr AI Lead System - Automation Fix Script")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Track results
    results = {}
    
    # Fix 1: Missing AI messages
    results["AI Messages"] = fix_missing_ai_messages()
    
    # Fix 2: Incomplete enrichment
    results["Enrichment"] = fix_incomplete_enrichment()
    
    # Fix 3: Daily scraping
    results["Daily Scraping"] = fix_daily_scraping()
    
    # Fix 4: Create missing scripts
    results["Daily Sync Script"] = create_daily_sync_script()
    results["Cron Setup Script"] = create_cron_setup_script()
    results["Systemd Service"] = create_systemd_service()
    
    # Fix 5: Test components
    test_results = test_individual_components()
    results.update(test_results)
    
    # Fix 6: Create deployment guide
    results["Deployment Guide"] = create_deployment_guide()
    
    # Summary
    print("\n📊 Fix Summary")
    print("=" * 50)
    
    successful_fixes = sum(1 for result in results.values() if result)
    total_fixes = len(results)
    
    for fix_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {fix_name}")
    
    print(f"\nOverall: {successful_fixes}/{total_fixes} fixes successful")
    
    if successful_fixes == total_fixes:
        print("\n🎉 All fixes completed successfully!")
        print("\nNext steps:")
        print("1. Run the fixes manually if any failed")
        print("2. Set up automation on EC2 using the created scripts")
        print("3. Monitor the system using the deployment guide")
    else:
        print(f"\n⚠️ {total_fixes - successful_fixes} fixes failed")
        print("Please review the errors and run the fixes manually")

if __name__ == "__main__":
    main()
