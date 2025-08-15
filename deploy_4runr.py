#!/usr/bin/env python3
"""
4Runr Lead System - Production Deployment Script
Automated lead generation system for SMB prospects
"""

import os
import sys
from datetime import datetime

def deploy_4runr_system():
    """Deploy the complete 4Runr lead system"""
    
    print("DEPLOYING 4RUNR LEAD GENERATION SYSTEM")
    print("=" * 60)
    print(f"Deployment started: {datetime.now()}")
    print()
    
    # Check requirements
    print("Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required")
        return False
    print("SUCCESS: Python version OK")
    
    # Check required files
    required_files = [
        'production_lead_scraper.py',
        'ml_data_enricher.py', 
        'complete_data_pipeline.py',
        'safe_complete_sync.py',
        'data/unified_leads.db'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"SUCCESS: {file} found")
        else:
            print(f"ERROR: {file} missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"Cannot deploy - missing files: {missing_files}")
        return False
    
    # Check API configuration
    env_file = "4runr-lead-scraper/.env"
    if os.path.exists(env_file):
        print("SUCCESS: API configuration found")
    else:
        print("ERROR: API configuration missing")
        return False
    
    print("\nSYSTEM READY FOR DEPLOYMENT!")
    return True

def run_production_cycle():
    """Run a complete production cycle"""
    
    print("\nRUNNING PRODUCTION CYCLE")
    print("=" * 40)
    
    try:
        # Import and run production scraper
        from production_lead_scraper import run_production_scraper
        
        print("1. Running production lead scraper...")
        success = run_production_scraper(max_leads=5)
        
        if success:
            print("SUCCESS: Production cycle completed")
            print("New leads scraped, processed, and synced to Airtable")
            return True
        else:
            print("WARNING: Production cycle completed with warnings")
            return True
            
    except Exception as e:
        print(f"ERROR: Production cycle failed: {e}")
        return False

def show_system_status():
    """Show current system status"""
    
    print("\nSYSTEM STATUS")
    print("=" * 30)
    
    try:
        import sqlite3
        conn = sqlite3.connect('data/unified_leads.db')
        cursor = conn.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE ai_message IS NOT NULL")
        leads_with_ai = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE ready_for_outreach = 1")
        ready_leads = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"Total leads in system: {total_leads}")
        print(f"Leads with AI messages: {leads_with_ai}")
        print(f"Ready for outreach: {ready_leads}")
        
    except Exception as e:
        print(f"Error checking status: {e}")

def setup_automation():
    """Show automation setup instructions"""
    
    print("\nAUTOMATION SETUP")
    print("=" * 30)
    print("To run automatically, add to crontab:")
    print("# Run every day at 9 AM")
    print("0 9 * * * cd /path/to/4runr && python deploy_4runr.py --auto")
    print()
    print("Or run manually:")
    print("python deploy_4runr.py --cycle")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Lead System Deployment')
    parser.add_argument('--deploy', action='store_true', help='Check deployment readiness')
    parser.add_argument('--cycle', action='store_true', help='Run production cycle')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--auto', action='store_true', help='Automated run (cron mode)')
    
    args = parser.parse_args()
    
    if args.deploy or not any(vars(args).values()):
        deploy_ready = deploy_4runr_system()
        if deploy_ready:
            print("\nDEPLOYMENT READY!")
            print("System is configured and ready for production use")
            show_system_status()
        else:
            print("\nDEPLOYMENT FAILED")
            print("Fix the issues above before deploying")
    
    if args.status:
        show_system_status()
    
    if args.cycle or args.auto:
        cycle_success = run_production_cycle()
        if not args.auto:  # Don't show setup in auto mode
            setup_automation()
    
    if args.auto and cycle_success:
        print(f"Automated cycle completed: {datetime.now()}")
