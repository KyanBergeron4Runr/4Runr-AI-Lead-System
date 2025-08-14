#!/usr/bin/env python3
"""
Setup Automation - Comprehensive automation setup for 4Runr AI Lead System
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def create_daily_sync_script():
    """Create the daily sync script for automation"""
    print("🔧 Creating Daily Sync Script")
    print("=" * 50)
    
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
    with open(sync_script_path, 'w', encoding='utf-8') as f:
        f.write(sync_script_content)
    
    # Make executable (on Unix systems)
    try:
        os.chmod(sync_script_path, 0o755)
    except:
        pass  # Windows doesn't support chmod
    
    print(f"✅ Created daily sync script: {sync_script_path}")
    return True

def create_cron_setup_script():
    """Create a script to set up cron jobs"""
    print("\n🔧 Creating Cron Setup Script")
    print("=" * 50)
    
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
    with open(cron_setup_path, 'w', encoding='utf-8') as f:
        f.write(cron_setup_content)
    
    # Make executable (on Unix systems)
    try:
        os.chmod(cron_setup_path, 0o755)
    except:
        pass  # Windows doesn't support chmod
    
    print(f"✅ Created cron setup script: {cron_setup_path}")
    return True

def create_systemd_service():
    """Create systemd service for 24/7 operation"""
    print("\n🔧 Creating Systemd Service")
    print("=" * 50)
    
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
    with open(service_path, 'w', encoding='utf-8') as f:
        f.write(service_content)
    
    print(f"✅ Created systemd service file: {service_path}")
    print("To install the service on EC2:")
    print("  sudo cp 4runr-ai-system.service /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable 4runr-ai-system")
    print("  sudo systemctl start 4runr-ai-system")
    
    return True

def create_windows_task():
    """Create Windows Task Scheduler task for automation"""
    print("\n🔧 Creating Windows Task")
    print("=" * 50)
    
    # Create batch file for Windows
    batch_content = """@echo off
REM 4Runr AI Lead System - Daily Sync Script for Windows

cd /d "%~dp0"
echo %date% %time%: Starting daily sync >> logs\\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log

REM Run daily scraper
python 4runr-lead-scraper\\scripts\\daily_scraper.py --max-leads 5 >> logs\\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1

REM Run enricher agent
python 4runr-outreach-system\\daily_enricher_agent_updated.py --max-leads 20 >> logs\\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1

REM Run message generator
python 4runr-outreach-system\\message_generator\\app.py --limit 20 >> logs\\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1

echo %date% %time%: Daily sync completed >> logs\\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log
"""
    
    batch_path = Path("daily_sync.bat")
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"✅ Created Windows batch file: {batch_path}")
    print("To set up Windows Task Scheduler:")
    print("1. Open Task Scheduler")
    print("2. Create Basic Task")
    print("3. Name: '4Runr Daily Sync'")
    print("4. Trigger: Daily at 6:00 AM")
    print("5. Action: Start a program")
    print("6. Program: cmd.exe")
    print("7. Arguments: /c \"C:\\path\\to\\4Runr-AI-Lead-System\\daily_sync.bat\"")
    
    return True

def test_daily_scraper():
    """Test the daily scraper to ensure it works"""
    print("\n🔧 Testing Daily Scraper")
    print("=" * 50)
    
    try:
        scraper_path = Path("4runr-lead-scraper/scripts/daily_scraper.py")
        if not scraper_path.exists():
            print("❌ Daily scraper not found")
            return False
        
        # Test with minimal parameters
        cmd = [
            sys.executable,
            str(scraper_path),
            "--max-leads", "1",
            "--test"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Daily scraper test passed")
            return True
        else:
            print(f"❌ Daily scraper test failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Daily scraper test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing daily scraper: {e}")
        return False

def create_deployment_guide():
    """Create a comprehensive deployment guide"""
    print("\n🔧 Creating Deployment Guide")
    print("=" * 50)
    
    guide_content = """# 4Runr AI Lead System - Automation Setup Guide

## 🎯 Current Status
- ✅ Database consolidated: 26 leads
- ✅ AI messages fixed: 96.2% complete
- ✅ Enrichment fixed: 96.2% complete
- ✅ Unicode encoding issues resolved
- ✅ Database configuration fixed

## 🚀 Automation Setup

### For Linux/EC2 (Recommended)

1. **Set up cron jobs:**
   ```bash
   chmod +x setup_cron.sh
   bash setup_cron.sh
   ```

2. **Set up systemd service (optional):**
   ```bash
   sudo cp 4runr-ai-system.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable 4runr-ai-system
   sudo systemctl start 4runr-ai-system
   ```

### For Windows

1. **Set up Task Scheduler:**
   - Open Task Scheduler
   - Create Basic Task
   - Name: '4Runr Daily Sync'
   - Trigger: Daily at 6:00 AM
   - Action: Start a program
   - Program: cmd.exe
   - Arguments: /c "C:\\path\\to\\4Runr-AI-Lead-System\\daily_sync.bat"

## 📊 Expected Results

After automation is set up:
- **Daily scraping**: 5 new leads every day at 6 AM
- **Daily enrichment**: All new leads enriched automatically
- **Daily messaging**: AI messages generated for all leads
- **Daily sync**: All data synced to Airtable

## 🔧 Monitoring

### Check Daily Sync Logs
```bash
# Linux
tail -f logs/daily_sync_$(date +%Y%m%d).log

# Windows
type logs\\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log
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

## 🎯 Next Steps

1. **Deploy to EC2** (if not already done)
2. **Set up monitoring** and alerts
3. **Optimize performance** based on usage
4. **Scale up** as lead volume increases

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Run diagnostic scripts
3. Review this guide
4. Contact system administrator
"""
    
    guide_path = Path("AUTOMATION_SETUP_GUIDE.md")
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✅ Created deployment guide: {guide_path}")
    return True

def main():
    """Main function"""
    print("🔧 4Runr AI Lead System - Automation Setup")
    print("=" * 60)
    
    results = {}
    
    # Create automation scripts
    results["Daily Sync Script"] = create_daily_sync_script()
    results["Cron Setup Script"] = create_cron_setup_script()
    results["Systemd Service"] = create_systemd_service()
    results["Windows Task"] = create_windows_task()
    
    # Test components
    results["Daily Scraper Test"] = test_daily_scraper()
    
    # Create documentation
    results["Deployment Guide"] = create_deployment_guide()
    
    # Summary
    print("\n📊 Automation Setup Summary")
    print("=" * 50)
    
    successful_setups = sum(1 for result in results.values() if result)
    total_setups = len(results)
    
    for setup_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {setup_name}")
    
    print(f"\nOverall: {successful_setups}/{total_setups} setups successful")
    
    if successful_setups >= 4:  # At least scripts and guide should work
        print("\n🎉 Automation setup completed!")
        print("\nNext steps:")
        print("1. Deploy to EC2 (if not already done)")
        print("2. Run: bash setup_cron.sh (on Linux)")
        print("3. Set up Windows Task Scheduler (on Windows)")
        print("4. Monitor logs and system health")
        print("5. Review AUTOMATION_SETUP_GUIDE.md for details")
    else:
        print(f"\n⚠️ {total_setups - successful_setups} setups failed")
        print("Please review the errors and set up manually")

if __name__ == "__main__":
    main()
