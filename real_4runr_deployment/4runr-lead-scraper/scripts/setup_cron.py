#!/usr/bin/env python3
"""
Cron Setup Script

Helper script to set up cron jobs for the 4runr-lead-scraper daily automation.
"""

import os
import sys
import subprocess
from pathlib import Path

def get_script_path():
    """Get the absolute path to the daily scraper script."""
    script_dir = Path(__file__).parent
    daily_scraper_path = script_dir / "daily_scraper.py"
    return str(daily_scraper_path.absolute())

def get_python_path():
    """Get the Python executable path."""
    return sys.executable

def generate_cron_entries():
    """Generate cron job entries for different schedules."""
    python_path = get_python_path()
    script_path = get_script_path()
    log_dir = Path(__file__).parent.parent / "logs" / "daily"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    cron_entries = {
        "daily_full": {
            "schedule": "0 9 * * *",  # 9 AM daily
            "command": f"{python_path} {script_path} --save-report",
            "description": "Full daily pipeline (scrape, enrich, sync)"
        },
        "enrichment_only": {
            "schedule": "0 14 * * *",  # 2 PM daily
            "command": f"{python_path} {script_path} --enrich-only --save-report",
            "description": "Enrichment only (afternoon run)"
        },
        "sync_frequent": {
            "schedule": "*/30 * * * *",  # Every 30 minutes
            "command": f"{python_path} {script_path} --sync-only",
            "description": "Frequent sync to Airtable"
        }
    }
    
    return cron_entries

def display_cron_setup():
    """Display cron setup instructions."""
    entries = generate_cron_entries()
    
    print("🕐 4Runr Lead Scraper - Cron Job Setup")
    print("=" * 50)
    print()
    print("To set up automated scheduling, add these entries to your crontab:")
    print("Run: crontab -e")
    print()
    
    for name, entry in entries.items():
        print(f"# {entry['description']}")
        print(f"{entry['schedule']} {entry['command']} >> {Path(__file__).parent.parent}/logs/daily/cron.log 2>&1")
        print()
    
    print("Alternative: Use the provided cron template file")
    print("1. Copy the template: cp cron_template.txt /tmp/4runr_cron")
    print("2. Install: crontab /tmp/4runr_cron")
    print()
    print("To view current cron jobs: crontab -l")
    print("To remove cron jobs: crontab -r")

def create_cron_template():
    """Create a cron template file."""
    entries = generate_cron_entries()
    template_path = Path(__file__).parent / "cron_template.txt"
    
    with open(template_path, 'w') as f:
        f.write("# 4Runr Lead Scraper - Automated Scheduling\n")
        f.write("# Generated on: " + str(Path(__file__).parent.parent) + "\n")
        f.write("# Python: " + get_python_path() + "\n")
        f.write("\n")
        
        for name, entry in entries.items():
            f.write(f"# {entry['description']}\n")
            f.write(f"{entry['schedule']} {entry['command']} >> {Path(__file__).parent.parent}/logs/daily/cron.log 2>&1\n")
            f.write("\n")
    
    print(f"📄 Cron template created: {template_path}")
    return str(template_path)

def test_daily_script():
    """Test the daily script to ensure it works."""
    print("🧪 Testing daily scraper script...")
    
    try:
        python_path = get_python_path()
        script_path = get_script_path()
        
        # Run dry-run test
        result = subprocess.run([
            python_path, script_path, "--dry-run", "--max-leads", "1"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Daily script test passed")
            return True
        else:
            print("❌ Daily script test failed")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ Daily script test timed out")
        return False
    except Exception as e:
        print(f"❌ Daily script test error: {str(e)}")
        return False

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up cron jobs for 4Runr Lead Scraper")
    parser.add_argument('--create-template', action='store_true', help='Create cron template file')
    parser.add_argument('--test', action='store_true', help='Test the daily script')
    parser.add_argument('--show-setup', action='store_true', help='Show cron setup instructions')
    
    args = parser.parse_args()
    
    if args.test:
        success = test_daily_script()
        return 0 if success else 1
    
    if args.create_template:
        create_cron_template()
    
    if args.show_setup or not any([args.create_template, args.test]):
        display_cron_setup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())