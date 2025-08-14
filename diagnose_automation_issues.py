#!/usr/bin/env python3
"""
Diagnose Automation Issues - Comprehensive diagnostic script
Identifies why automation isn't working properly on EC2
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta

def check_cron_jobs():
    """Check if cron jobs are properly configured"""
    print("🔍 Checking Cron Jobs")
    print("=" * 50)
    
    try:
        # Check if crontab exists
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            cron_content = result.stdout
            print("✅ Crontab found")
            
            # Look for 4Runr automation jobs
            if '4runr' in cron_content.lower() or '4runr' in cron_content:
                print("✅ Found 4Runr automation jobs:")
                for line in cron_content.split('\n'):
                    if '4runr' in line.lower() or 'daily' in line.lower():
                        print(f"  - {line.strip()}")
            else:
                print("❌ No 4Runr automation jobs found in crontab")
                print("   Expected jobs for daily scraping, enrichment, and sync")
        else:
            print("❌ No crontab found or error accessing crontab")
            
    except Exception as e:
        print(f"❌ Error checking crontab: {e}")

def check_systemd_services():
    """Check if systemd services are running"""
    print("\n🔍 Checking Systemd Services")
    print("=" * 50)
    
    services_to_check = [
        '4runr-ai-system',
        '4runr-automation', 
        '4runr-brain',
        '4runr-email'
    ]
    
    for service in services_to_check:
        try:
            result = subprocess.run(['systemctl', 'is-active', service], 
                                  capture_output=True, text=True)
            status = result.stdout.strip()
            if status == 'active':
                print(f"✅ {service}: {status}")
            else:
                print(f"❌ {service}: {status}")
                
                # Check if service exists
                result = subprocess.run(['systemctl', 'status', service], 
                                      capture_output=True, text=True)
                if 'Unit not found' in result.stderr:
                    print(f"   - Service not installed")
                else:
                    print(f"   - Service exists but not running")
                    
        except Exception as e:
            print(f"❌ Error checking {service}: {e}")

def check_automation_scripts():
    """Check if automation scripts exist and are executable"""
    print("\n🔍 Checking Automation Scripts")
    print("=" * 50)
    
    scripts_to_check = [
        '4runr-lead-scraper/scripts/daily_scraper.py',
        '4runr-outreach-system/daily_enricher_agent_updated.py',
        '4runr-brain/daily_batch_processor.py',
        'system_controller.py'
    ]
    
    for script in scripts_to_check:
        script_path = Path(script)
        if script_path.exists():
            print(f"✅ {script}: Found")
            
            # Check if executable
            if os.access(script_path, os.X_OK):
                print(f"   - Executable: Yes")
            else:
                print(f"   - Executable: No")
                
            # Check file size
            size = script_path.stat().st_size
            print(f"   - Size: {size} bytes")
            
        else:
            print(f"❌ {script}: Not found")

def check_log_files():
    """Check recent log files for errors"""
    print("\n🔍 Checking Recent Log Files")
    print("=" * 50)
    
    log_dirs = [
        'logs',
        '4runr-lead-scraper/logs',
        '4runr-outreach-system/logs',
        '4runr-brain/logs'
    ]
    
    for log_dir in log_dirs:
        log_path = Path(log_dir)
        if log_path.exists():
            print(f"✅ {log_dir}: Found")
            
            # Find recent log files
            recent_logs = []
            for log_file in log_path.glob('*.log'):
                if log_file.stat().st_mtime > (datetime.now() - timedelta(days=7)).timestamp():
                    recent_logs.append(log_file)
            
            if recent_logs:
                print(f"   - Recent log files: {len(recent_logs)}")
                for log_file in sorted(recent_logs, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    print(f"     * {log_file.name} (modified: {mtime.strftime('%Y-%m-%d %H:%M')})")
            else:
                print(f"   - No recent log files")
        else:
            print(f"❌ {log_dir}: Not found")

def check_environment_config():
    """Check environment configuration"""
    print("\n🔍 Checking Environment Configuration")
    print("=" * 50)
    
    env_files = [
        '.env',
        '4runr-lead-scraper/.env',
        '4runr-outreach-system/.env',
        '4runr-brain/.env'
    ]
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            print(f"✅ {env_file}: Found")
            
            # Check for required variables
            with open(env_path, 'r') as f:
                content = f.read()
                
            required_vars = [
                'OPENAI_API_KEY',
                'AIRTABLE_API_KEY', 
                'SERPAPI_API_KEY',
                'LEAD_DATABASE_PATH'
            ]
            
            missing_vars = []
            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"   - Missing variables: {', '.join(missing_vars)}")
            else:
                print(f"   - All required variables present")
                
        else:
            print(f"❌ {env_file}: Not found")

def check_database_connectivity():
    """Check database connectivity"""
    print("\n🔍 Checking Database Connectivity")
    print("=" * 50)
    
    db_paths = [
        'data/unified_leads.db',
        '4runr-lead-scraper/data/leads.db',
        '4runr-outreach-system/data/leads_cache.db'
    ]
    
    for db_path in db_paths:
        db_file = Path(db_path)
        if db_file.exists():
            print(f"✅ {db_path}: Found ({db_file.stat().st_size} bytes)")
            
            # Try to connect
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM leads")
                count = cursor.fetchone()[0]
                conn.close()
                print(f"   - Connected successfully, {count} leads")
            except Exception as e:
                print(f"   - Connection failed: {e}")
        else:
            print(f"❌ {db_path}: Not found")

def check_api_keys():
    """Check if API keys are configured"""
    print("\n🔍 Checking API Keys")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'AIRTABLE_API_KEY': os.getenv('AIRTABLE_API_KEY'),
        'SERPAPI_API_KEY': os.getenv('SERPAPI_API_KEY')
    }
    
    for key_name, key_value in api_keys.items():
        if key_value:
            # Check if it looks like a valid key (not empty, has some length)
            if len(key_value) > 10:
                print(f"✅ {key_name}: Configured")
            else:
                print(f"⚠️ {key_name}: Too short (may be invalid)")
        else:
            print(f"❌ {key_name}: Not configured")

def generate_recommendations():
    """Generate recommendations based on findings"""
    print("\n🎯 Recommendations")
    print("=" * 50)
    
    print("1. **Fix Missing AI Messages**:")
    print("   - Run the message generator for leads without AI messages")
    print("   - Command: python 4runr-outreach-system/message_generator/app.py --limit 20")
    
    print("\n2. **Fix Incomplete Enrichment**:")
    print("   - Run the enricher agent for unenriched leads")
    print("   - Command: python 4runr-outreach-system/daily_enricher_agent_updated.py --max-leads 50")
    
    print("\n3. **Set Up Daily Automation**:")
    print("   - Add cron jobs for daily scraping and enrichment")
    print("   - Command: crontab -e")
    print("   - Add: 0 6 * * * cd /path/to/4runr && python 4runr-lead-scraper/scripts/daily_scraper.py")
    
    print("\n4. **Test Individual Components**:")
    print("   - Test lead scraper: python 4runr-lead-scraper/simple_cli.py scrape --limit 5")
    print("   - Test message generator: python 4runr-outreach-system/message_generator/app.py --limit 5")
    print("   - Test enricher: python 4runr-outreach-system/daily_enricher_agent_updated.py --max-leads 5")

def main():
    """Run all diagnostics"""
    print("🔍 4Runr AI Lead System - Automation Diagnostic")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    check_cron_jobs()
    check_systemd_services()
    check_automation_scripts()
    check_log_files()
    check_environment_config()
    check_database_connectivity()
    check_api_keys()
    generate_recommendations()
    
    print("\n✅ Diagnostic complete!")

if __name__ == "__main__":
    main()
