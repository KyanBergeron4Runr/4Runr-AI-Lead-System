#!/usr/bin/env python3
"""
Weekly AI Analysis Scheduler

This script sets up automatic weekly analysis of AI decisions to identify improvements.
Can be run as a standalone scheduler or integrated with system cron jobs.
"""

import os
import time
import schedule
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('weekly-scheduler')

def run_weekly_analysis():
    """Run the weekly AI analysis"""
    try:
        logger.info("🔍 Starting scheduled weekly AI analysis...")
        
        # Import and run the analyzer
        from weekly_ai_analysis import WeeklyAIAnalyzer
        
        analyzer = WeeklyAIAnalyzer()
        report_path = analyzer.generate_weekly_report()
        
        logger.info(f"✅ Weekly analysis completed successfully")
        logger.info(f"📊 Report saved to: {report_path}")
        
        # Optional: Send notification or email about the report
        # send_analysis_notification(report_path)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Weekly analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def send_analysis_notification(report_path: str):
    """Send notification about completed analysis (placeholder)"""
    # This could be extended to send email notifications, Slack messages, etc.
    logger.info(f"📧 Analysis notification sent for report: {report_path}")

def setup_weekly_schedule():
    """Set up the weekly analysis schedule"""
    # Schedule for every Sunday at 9:00 AM
    schedule.every().sunday.at("09:00").do(run_weekly_analysis)
    
    logger.info("📅 Weekly AI analysis scheduled for every Sunday at 9:00 AM")
    logger.info("🔄 Scheduler is now running...")
    
    return schedule

def run_scheduler():
    """Run the scheduler continuously"""
    setup_weekly_schedule()
    
    # Run initial analysis if none exists from this week
    analysis_dir = Path("ai_analysis_reports")
    if analysis_dir.exists():
        # Check if we have a report from this week
        current_week = datetime.now().strftime('%Y%m%d')
        recent_reports = list(analysis_dir.glob(f"weekly_summary_{current_week[:6]}*.txt"))
        
        if not recent_reports:
            logger.info("🚀 No recent analysis found. Running initial analysis...")
            run_weekly_analysis()
    else:
        logger.info("🚀 Running initial analysis...")
        run_weekly_analysis()
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

def create_cron_job():
    """Create a cron job for weekly analysis (Linux/Mac)"""
    cron_command = f"0 9 * * 0 cd {os.getcwd()} && python weekly_ai_analysis.py"
    
    print("🔧 To set up automatic weekly analysis, add this to your crontab:")
    print(f"   {cron_command}")
    print("\n📝 To edit crontab:")
    print("   crontab -e")
    print("\n⏰ This will run every Sunday at 9:00 AM")

def create_windows_task():
    """Instructions for creating Windows scheduled task"""
    script_path = Path(__file__).parent.absolute() / "weekly_ai_analysis.py"
    
    print("🔧 To set up automatic weekly analysis on Windows:")
    print("1. Open Task Scheduler")
    print("2. Create Basic Task")
    print("3. Set trigger: Weekly, Sunday, 9:00 AM")
    print(f"4. Set action: Start a program")
    print(f"5. Program: python")
    print(f"6. Arguments: {script_path}")
    print(f"7. Start in: {Path(__file__).parent.absolute()}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Weekly AI Analysis Scheduler')
    parser.add_argument('--run-now', action='store_true', help='Run analysis immediately')
    parser.add_argument('--schedule', action='store_true', help='Start the scheduler')
    parser.add_argument('--setup-cron', action='store_true', help='Show cron job setup instructions')
    parser.add_argument('--setup-windows', action='store_true', help='Show Windows task setup instructions')
    
    args = parser.parse_args()
    
    if args.run_now:
        print("🔍 Running weekly AI analysis now...")
        success = run_weekly_analysis()
        if success:
            print("✅ Analysis completed successfully!")
        else:
            print("❌ Analysis failed. Check logs for details.")
    
    elif args.schedule:
        print("📅 Starting weekly analysis scheduler...")
        run_scheduler()
    
    elif args.setup_cron:
        create_cron_job()
    
    elif args.setup_windows:
        create_windows_task()
    
    else:
        print("🤖 4Runr Weekly AI Analysis Scheduler")
        print("=" * 50)
        print("Options:")
        print("  --run-now      Run analysis immediately")
        print("  --schedule     Start the scheduler")
        print("  --setup-cron   Show cron job setup (Linux/Mac)")
        print("  --setup-windows Show Windows task setup")
        print("\nExample:")
        print("  python schedule_weekly_analysis.py --run-now")

if __name__ == "__main__":
    main()