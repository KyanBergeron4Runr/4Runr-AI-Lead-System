#!/usr/bin/env python3
"""
Setup Daily Automation

Creates all the automation scripts and configurations needed to run the system daily.
Sets up cron jobs, systemd services, and Windows tasks.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutomationSetup:
    """Setup daily automation for the lead system."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.automation_created = []
        
    def setup_all_automation(self):
        """Setup all automation components."""
        logger.info("🚀 SETTING UP DAILY AUTOMATION")
        logger.info("="*50)
        
        try:
            # 1. Create the main daily automation script
            self.create_daily_automation_script()
            
            # 2. Create Linux/Ubuntu automation (cron + systemd)
            self.create_linux_automation()
            
            # 3. Create Windows automation (Task Scheduler)
            self.create_windows_automation()
            
            # 4. Create monitoring and health checks
            self.create_monitoring_scripts()
            
            # 5. Create deployment guide
            self.create_deployment_guide()
            
            self.report_automation_setup()
            
        except Exception as e:
            logger.error(f"❌ Automation setup failed: {e}")
            return False
        
        return True
    
    def create_daily_automation_script(self):
        """Create the main daily automation script."""
        logger.info("📝 Creating main daily automation script...")
        
        daily_script_content = '''#!/usr/bin/env python3
"""
Daily Lead Generation Automation

Main script that runs daily to:
1. Scrape new leads
2. Enrich with emails and business data
3. Generate AI messages
4. Sync to Airtable
5. Monitor system health
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.append('4runr-outreach-system')
sys.path.append('4runr-lead-scraper')

# Import production components
from production_db_manager import db_manager
from improved_email_finder import email_finder
from company_size_validator import company_validator

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"daily_automation_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyAutomation:
    """Daily lead generation automation."""
    
    def __init__(self):
        self.stats = {
            'leads_scraped': 0,
            'leads_enriched': 0,
            'emails_found': 0,
            'ai_messages_generated': 0,
            'leads_synced': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
    def run_daily_pipeline(self):
        """Run the complete daily lead generation pipeline."""
        logger.info("🎯 STARTING DAILY LEAD GENERATION")
        logger.info("="*50)
        
        try:
            # Step 1: Scrape new leads
            self.scrape_new_leads()
            
            # Step 2: Enrich leads with emails and business data
            self.enrich_leads()
            
            # Step 3: Generate AI messages
            self.generate_ai_messages()
            
            # Step 4: Sync to Airtable
            self.sync_to_airtable()
            
            # Step 5: System health check
            self.system_health_check()
            
            self.stats['end_time'] = datetime.now()
            self.report_results()
            
        except Exception as e:
            logger.error(f"❌ Daily automation failed: {e}")
            logger.error(traceback.format_exc())
            self.stats['errors'] += 1
            return False
        
        return True
    
    def scrape_new_leads(self):
        """Scrape new leads using SerpAPI."""
        logger.info("🔍 Step 1: Scraping new leads...")
        
        try:
            # Import lead scraper
            from 4runr_lead_scraper.scraper.lead_finder import LeadFinder
            
            lead_finder = LeadFinder()
            new_leads = lead_finder.find_montreal_executives(max_leads=5)
            
            if not new_leads:
                logger.info("📭 No new leads found today")
                return
            
            logger.info(f"📋 Found {len(new_leads)} potential leads")
            
            # Add leads to database
            added_count = 0
            for lead_data in new_leads:
                # Validate company size before adding
                if lead_data.get('company'):
                    target_info = company_validator.is_good_outreach_target(
                        lead_data['company'], ""
                    )
                    
                    if not target_info['is_good_target']:
                        logger.info(f"⏭️ Skipping {lead_data['company']}: {target_info['reason']}")
                        continue
                
                # Add to database
                if db_manager.add_lead(lead_data):
                    added_count += 1
                    logger.info(f"✅ Added lead: {lead_data.get('full_name', 'Unknown')} at {lead_data.get('company', 'Unknown')}")
                else:
                    logger.warning(f"⚠️ Failed to add lead: {lead_data.get('full_name', 'Unknown')}")
            
            self.stats['leads_scraped'] = added_count
            logger.info(f"✅ Successfully added {added_count} new leads")
            
        except Exception as e:
            logger.error(f"❌ Lead scraping failed: {e}")
            self.stats['errors'] += 1
    
    def enrich_leads(self):
        """Enrich leads with emails and business data."""
        logger.info("🔧 Step 2: Enriching leads...")
        
        try:
            # Get leads that need enrichment
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, full_name, company, website, email 
                    FROM leads 
                    WHERE (email IS NULL OR email = '') 
                    AND website IS NOT NULL 
                    AND website != ''
                    LIMIT 10
                """)
                leads_to_enrich = cursor.fetchall()
            
            if not leads_to_enrich:
                logger.info("📭 No leads need enrichment")
                return
            
            logger.info(f"🔧 Enriching {len(leads_to_enrich)} leads...")
            
            enriched_count = 0
            emails_found = 0
            
            for lead in leads_to_enrich:
                lead_id = lead['id']
                website = lead['website']
                company = lead['company']
                
                try:
                    # Find emails
                    if website and not lead['email']:
                        emails = email_finder.find_business_emails(website, company)
                        
                        if emails:
                            # Update lead with first email found
                            update_data = {'email': emails[0]}
                            if db_manager.update_lead(lead_id, update_data):
                                emails_found += 1
                                logger.info(f"📧 Found email for {lead['full_name']}: {emails[0]}")
                    
                    # Mark as enriched
                    db_manager.update_lead(lead_id, {'enriched': 1})
                    enriched_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to enrich lead {lead_id}: {e}")
            
            self.stats['leads_enriched'] = enriched_count
            self.stats['emails_found'] = emails_found
            logger.info(f"✅ Enriched {enriched_count} leads, found {emails_found} emails")
            
        except Exception as e:
            logger.error(f"❌ Lead enrichment failed: {e}")
            self.stats['errors'] += 1
    
    def generate_ai_messages(self):
        """Generate AI messages for leads."""
        logger.info("🤖 Step 3: Generating AI messages...")
        
        try:
            # Get leads that need AI messages
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, full_name, company, business_type, email 
                    FROM leads 
                    WHERE (ai_message IS NULL OR ai_message = '') 
                    AND email IS NOT NULL 
                    AND email != ''
                    LIMIT 10
                """)
                leads_for_ai = cursor.fetchall()
            
            if not leads_for_ai:
                logger.info("📭 No leads need AI messages")
                return
            
            logger.info(f"🤖 Generating AI messages for {len(leads_for_ai)} leads...")
            
            messages_generated = 0
            
            for lead in leads_for_ai:
                lead_id = lead['id']
                
                try:
                    # Generate AI message (simplified for now)
                    ai_message = self._generate_simple_ai_message(lead)
                    
                    if ai_message:
                        update_data = {
                            'ai_message': ai_message,
                            'message_generated_at': datetime.now().isoformat()
                        }
                        
                        if db_manager.update_lead(lead_id, update_data):
                            messages_generated += 1
                            logger.info(f"🤖 Generated AI message for {lead['full_name']}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Failed to generate AI message for {lead_id}: {e}")
            
            self.stats['ai_messages_generated'] = messages_generated
            logger.info(f"✅ Generated {messages_generated} AI messages")
            
        except Exception as e:
            logger.error(f"❌ AI message generation failed: {e}")
            self.stats['errors'] += 1
    
    def _generate_simple_ai_message(self, lead):
        """Generate a simple AI message for a lead."""
        name = lead['full_name'] or 'there'
        company = lead['company'] or 'your company'
        business_type = lead['business_type'] or 'business'
        
        message = f"""Subject: Helping {company} Optimize Operations

Hi {name},

I noticed {company} and thought you might be interested in how we're helping {business_type} companies like yours optimize their operations and scale more efficiently.

Would you be open to a quick 15-minute call to discuss how we could potentially help {company}?

Best regards,
The 4Runr Team"""
        
        return message
    
    def sync_to_airtable(self):
        """Sync leads to Airtable."""
        logger.info("🔄 Step 4: Syncing to Airtable...")
        
        try:
            # Get leads ready for sync
            leads_for_sync = db_manager.get_leads_for_sync(limit=20)
            
            if not leads_for_sync:
                logger.info("📭 No leads to sync to Airtable")
                return
            
            logger.info(f"🔄 Syncing {len(leads_for_sync)} leads to Airtable...")
            
            # Import and use simple Airtable sync
            from simple_airtable_sync import sync_leads_to_airtable
            
            sync_result = sync_leads_to_airtable(leads_for_sync)
            
            if sync_result.get('success'):
                synced_count = sync_result.get('synced_count', 0)
                self.stats['leads_synced'] = synced_count
                logger.info(f"✅ Successfully synced {synced_count} leads to Airtable")
            else:
                logger.error(f"❌ Airtable sync failed: {sync_result.get('error')}")
                self.stats['errors'] += 1
            
        except Exception as e:
            logger.error(f"❌ Airtable sync failed: {e}")
            self.stats['errors'] += 1
    
    def system_health_check(self):
        """Perform system health check."""
        logger.info("🏥 Step 5: System health check...")
        
        try:
            # Get database stats
            stats = db_manager.get_database_stats()
            
            # Check for issues
            issues = []
            
            if stats['total_leads'] == 0:
                issues.append("No leads in database")
            
            if stats['email_percentage'] < 50:
                issues.append(f"Low email percentage: {stats['email_percentage']}%")
            
            if self.stats['errors'] > 0:
                issues.append(f"{self.stats['errors']} errors occurred")
            
            if issues:
                logger.warning(f"⚠️ Health check issues: {', '.join(issues)}")
            else:
                logger.info("✅ System health check passed")
            
            # Save health report
            health_report = {
                'timestamp': datetime.now().isoformat(),
                'database_stats': stats,
                'automation_stats': self.stats,
                'issues': issues
            }
            
            health_file = Path("logs") / f"health_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(health_file, 'w') as f:
                json.dump(health_report, f, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
    
    def report_results(self):
        """Report daily automation results."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("="*50)
        logger.info("📊 DAILY AUTOMATION RESULTS")
        logger.info("="*50)
        logger.info(f"⏱️ Duration: {duration}")
        logger.info(f"📋 Leads scraped: {self.stats['leads_scraped']}")
        logger.info(f"🔧 Leads enriched: {self.stats['leads_enriched']}")
        logger.info(f"📧 Emails found: {self.stats['emails_found']}")
        logger.info(f"🤖 AI messages generated: {self.stats['ai_messages_generated']}")
        logger.info(f"🔄 Leads synced to Airtable: {self.stats['leads_synced']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        
        # Save results
        results_file = Path("logs") / f"daily_results_{datetime.now().strftime('%Y%m%d')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        
        if self.stats['errors'] == 0:
            logger.info("🎉 Daily automation completed successfully!")
        else:
            logger.warning("⚠️ Daily automation completed with errors")

if __name__ == "__main__":
    automation = DailyAutomation()
    success = automation.run_daily_pipeline()
    
    if success:
        print("✅ Daily automation completed successfully")
        sys.exit(0)
    else:
        print("❌ Daily automation failed")
        sys.exit(1)
'''
        
        with open('daily_automation.py', 'w', encoding='utf-8') as f:
            f.write(daily_script_content)
        
        # Make it executable on Linux
        os.chmod('daily_automation.py', 0o755)
        
        self.automation_created.append("✅ Created daily_automation.py")
        logger.info("    - Complete daily pipeline (scrape, enrich, AI, sync)")
        logger.info("    - Health monitoring and error handling")
        logger.info("    - Detailed logging and reporting")
    
    def create_linux_automation(self):
        """Create Linux/Ubuntu automation files."""
        logger.info("🐧 Creating Linux automation...")
        
        # Create cron job script
        cron_script_content = '''#!/bin/bash
# Daily Lead Generation Cron Job
# Runs every day at 9:00 AM

# Set environment
cd /home/ubuntu/4Runr-AI-Lead-System
source .venv/bin/activate

# Run daily automation
python daily_automation.py

# Log completion
echo "$(date): Daily automation completed" >> logs/cron.log
'''
        
        with open('daily_cron.sh', 'w', encoding='utf-8') as f:
            f.write(cron_script_content)
        
        os.chmod('daily_cron.sh', 0o755)
        
        # Create systemd service
        systemd_service_content = '''[Unit]
Description=4Runr Daily Lead Generation
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/4Runr-AI-Lead-System
Environment=PATH=/home/ubuntu/4Runr-AI-Lead-System/.venv/bin
ExecStart=/home/ubuntu/4Runr-AI-Lead-System/.venv/bin/python daily_automation.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
        
        with open('4runr-daily.service', 'w', encoding='utf-8') as f:
            f.write(systemd_service_content)
        
        # Create systemd timer
        systemd_timer_content = '''[Unit]
Description=Run 4Runr Daily Lead Generation
Requires=4runr-daily.service

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
'''
        
        with open('4runr-daily.timer', 'w', encoding='utf-8') as f:
            f.write(systemd_timer_content)
        
        self.automation_created.append("✅ Created Linux automation files")
        logger.info("    - daily_cron.sh (cron job script)")
        logger.info("    - 4runr-daily.service (systemd service)")
        logger.info("    - 4runr-daily.timer (systemd timer)")
    
    def create_windows_automation(self):
        """Create Windows automation files."""
        logger.info("🪟 Creating Windows automation...")
        
        # Create Windows batch script
        windows_batch_content = '''@echo off
REM Daily Lead Generation for Windows
REM Run this script with Windows Task Scheduler

cd /d "C:\\Users\\kyanb\\4Runr AI Lead System"

REM Activate virtual environment
call .venv\\Scripts\\activate.bat

REM Run daily automation
python daily_automation.py

REM Log completion
echo %date% %time%: Daily automation completed >> logs\\windows_cron.log

pause
'''
        
        with open('daily_automation.bat', 'w', encoding='utf-8') as f:
            f.write(windows_batch_content)
        
        # Create PowerShell script
        powershell_content = '''# Daily Lead Generation PowerShell Script
# Run this with Windows Task Scheduler

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Activate virtual environment
& ".venv\\Scripts\\Activate.ps1"

# Run daily automation
python daily_automation.py

# Log completion
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"$timestamp : Daily automation completed" | Out-File -FilePath "logs\\powershell_cron.log" -Append
'''
        
        with open('daily_automation.ps1', 'w', encoding='utf-8') as f:
            f.write(powershell_content)
        
        self.automation_created.append("✅ Created Windows automation files")
        logger.info("    - daily_automation.bat (batch script)")
        logger.info("    - daily_automation.ps1 (PowerShell script)")
    
    def create_monitoring_scripts(self):
        """Create monitoring and health check scripts."""
        logger.info("📊 Creating monitoring scripts...")
        
        # Create health check script
        health_check_content = '''#!/usr/bin/env python3
"""
System Health Check

Quick health check to verify the system is working properly.
"""

import sys
import json
from pathlib import Path
from production_db_manager import db_manager

def check_system_health():
    """Check system health and report issues."""
    issues = []
    warnings = []
    
    # Check database
    try:
        stats = db_manager.get_database_stats()
        
        if stats['total_leads'] == 0:
            issues.append("No leads in database")
        elif stats['total_leads'] < 10:
            warnings.append(f"Low lead count: {stats['total_leads']}")
        
        if stats['email_percentage'] < 50:
            warnings.append(f"Low email percentage: {stats['email_percentage']}%")
        
        print(f"✅ Database: {stats['total_leads']} leads, {stats['email_percentage']}% with emails")
        
    except Exception as e:
        issues.append(f"Database error: {e}")
    
    # Check log files
    log_dir = Path("logs")
    if log_dir.exists():
        recent_logs = list(log_dir.glob("*.log"))
        if recent_logs:
            print(f"✅ Logs: {len(recent_logs)} log files found")
        else:
            warnings.append("No recent log files")
    else:
        warnings.append("Log directory not found")
    
    # Report results
    if issues:
        print(f"❌ Issues found: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
        return False
    elif warnings:
        print(f"⚠️ Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
        return True
    else:
        print("🎉 System health check passed!")
        return True

if __name__ == "__main__":
    healthy = check_system_health()
    sys.exit(0 if healthy else 1)
'''
        
        with open('health_check.py', 'w', encoding='utf-8') as f:
            f.write(health_check_content)
        
        # Create status report script
        status_report_content = '''#!/usr/bin/env python3
"""
System Status Report

Generate a comprehensive status report of the lead generation system.
"""

import json
from datetime import datetime
from production_db_manager import db_manager

def generate_status_report():
    """Generate comprehensive status report."""
    
    # Get database stats
    stats = db_manager.get_database_stats()
    
    # Get recent activity
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) as recent_leads 
            FROM leads 
            WHERE created_at >= datetime('now', '-7 days')
        """)
        recent_leads = cursor.fetchone()['recent_leads']
        
        cursor = conn.execute("""
            SELECT COUNT(*) as ready_leads 
            FROM leads 
            WHERE ready_for_outreach = 1
        """)
        ready_leads = cursor.fetchone()['ready_leads']
    
    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'database_stats': stats,
        'recent_activity': {
            'leads_added_7_days': recent_leads,
            'leads_ready_for_outreach': ready_leads
        },
        'system_status': 'healthy' if stats['total_leads'] > 0 else 'needs_attention'
    }
    
    # Save report
    report_file = f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("📊 SYSTEM STATUS REPORT")
    print("="*40)
    print(f"Total Leads: {stats['total_leads']}")
    print(f"With Emails: {stats['leads_with_email']} ({stats['email_percentage']}%)")
    print(f"Ready for Outreach: {ready_leads}")
    print(f"Recent Activity (7 days): {recent_leads} new leads")
    print(f"System Status: {report['system_status']}")
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    generate_status_report()
'''
        
        with open('status_report.py', 'w', encoding='utf-8') as f:
            f.write(status_report_content)
        
        self.automation_created.append("✅ Created monitoring scripts")
        logger.info("    - health_check.py (system health check)")
        logger.info("    - status_report.py (comprehensive status report)")
    
    def create_deployment_guide(self):
        """Create deployment guide."""
        logger.info("📖 Creating deployment guide...")
        
        deployment_guide = '''# 🚀 AUTOMATION DEPLOYMENT GUIDE

## Overview
This guide shows you how to set up daily automation for your 4Runr Lead Generation System.

## Files Created
- `daily_automation.py` - Main automation script
- `daily_cron.sh` - Linux cron job script
- `4runr-daily.service` - Linux systemd service
- `4runr-daily.timer` - Linux systemd timer
- `daily_automation.bat` - Windows batch script
- `daily_automation.ps1` - Windows PowerShell script
- `health_check.py` - System health check
- `status_report.py` - Status report generator

## 🐧 Linux/Ubuntu Setup

### Option 1: Cron Job (Recommended)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9:00 AM
0 9 * * * /home/ubuntu/4Runr-AI-Lead-System/daily_cron.sh
```

### Option 2: Systemd Timer
```bash
# Copy service and timer files
sudo cp 4runr-daily.service /etc/systemd/system/
sudo cp 4runr-daily.timer /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable 4runr-daily.timer
sudo systemctl start 4runr-daily.timer

# Check status
sudo systemctl status 4runr-daily.timer
```

## 🪟 Windows Setup

### Option 1: Task Scheduler (Recommended)
1. Open Task Scheduler
2. Create Basic Task
3. Name: "4Runr Daily Automation"
4. Trigger: Daily at 9:00 AM
5. Action: Start a program
6. Program: `C:\\Users\\kyanb\\4Runr AI Lead System\\daily_automation.bat`

### Option 2: PowerShell
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "C:\\Users\\kyanb\\4Runr AI Lead System\\daily_automation.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -TaskName "4Runr Daily Automation" -Action $action -Trigger $trigger
```

## 📊 Monitoring

### Health Check
```bash
python health_check.py
```

### Status Report
```bash
python status_report.py
```

### Manual Run
```bash
python daily_automation.py
```

## 🔧 Troubleshooting

### Check Logs
- Daily logs: `logs/daily_automation_YYYYMMDD.log`
- Health reports: `logs/health_report_YYYYMMDD.json`
- Results: `logs/daily_results_YYYYMMDD.json`

### Common Issues
1. **Permission denied**: Make scripts executable (`chmod +x *.sh`)
2. **Python not found**: Ensure virtual environment is activated
3. **Database errors**: Check database file permissions
4. **API errors**: Verify API keys in .env file

### Manual Testing
```bash
# Test the automation script
python daily_automation.py

# Check system health
python health_check.py

# Generate status report
python status_report.py
```

## 🎯 Expected Results
- **Daily**: 5 new leads scraped
- **Enrichment**: Emails found for 70%+ of leads
- **AI Messages**: Generated for all leads with emails
- **Airtable Sync**: All leads synced successfully
- **Health**: System running smoothly with no errors

## 📞 Support
If automation fails:
1. Check logs in `logs/` directory
2. Run `python health_check.py`
3. Verify API keys and database access
4. Test manually with `python daily_automation.py`
'''
        
        with open('AUTOMATION_DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(deployment_guide)
        
        self.automation_created.append("✅ Created AUTOMATION_DEPLOYMENT_GUIDE.md")
        logger.info("    - Complete setup instructions for Linux and Windows")
        logger.info("    - Troubleshooting guide and monitoring tips")
    
    def report_automation_setup(self):
        """Report automation setup completion."""
        logger.info("\n" + "="*60)
        logger.info("🚀 AUTOMATION SETUP COMPLETE!")
        logger.info("="*60)
        
        for automation in self.automation_created:
            logger.info(f"  {automation}")
        
        logger.info("\n📋 AUTOMATION FILES CREATED:")
        logger.info("  - daily_automation.py (main automation script)")
        logger.info("  - daily_cron.sh (Linux cron job)")
        logger.info("  - 4runr-daily.service (Linux systemd service)")
        logger.info("  - 4runr-daily.timer (Linux systemd timer)")
        logger.info("  - daily_automation.bat (Windows batch)")
        logger.info("  - daily_automation.ps1 (Windows PowerShell)")
        logger.info("  - health_check.py (system monitoring)")
        logger.info("  - status_report.py (status reporting)")
        logger.info("  - AUTOMATION_DEPLOYMENT_GUIDE.md (setup guide)")
        
        logger.info("\n🎯 NEXT STEPS:")
        logger.info("  1. Choose your platform (Linux/Windows)")
        logger.info("  2. Follow the deployment guide")
        logger.info("  3. Set up the automation to run daily")
        logger.info("  4. Monitor with health_check.py")
        logger.info("  5. Check logs for any issues")
        
        logger.info("\n✅ Your system is now ready for automated daily operation!")

if __name__ == "__main__":
    setup = AutomationSetup()
    success = setup.setup_all_automation()
    
    if success:
        print("\n🎉 AUTOMATION SETUP COMPLETE!")
        print("Follow AUTOMATION_DEPLOYMENT_GUIDE.md to deploy.")
    else:
        print("\n❌ Automation setup failed. Check logs for details.")
