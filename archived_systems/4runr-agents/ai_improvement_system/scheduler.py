#!/usr/bin/env python3
"""
AI Improvement System Scheduler

Automated scheduler for running weekly AI analysis.
"""

import time
import schedule
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ai_improvement_system.main import AIImprovementSystem
from ai_improvement_system.logger import get_logger

class AIImprovementScheduler:
    """Scheduler for automated AI improvement analysis"""
    
    def __init__(self):
        self.system = AIImprovementSystem()
        self.logger = get_logger("ai-scheduler")
        
    def run_scheduled_analysis(self):
        """Run the scheduled weekly analysis"""
        self.logger.log_scheduler_event("weekly_analysis_started", {
            "scheduled_time": datetime.now().isoformat(),
            "trigger": "automatic_weekly"
        })
        
        try:
            success = self.system.run_weekly_analysis()
            
            if success:
                self.logger.log_scheduler_event("weekly_analysis_completed", {
                    "status": "success",
                    "completed_time": datetime.now().isoformat()
                })
            else:
                self.logger.log_scheduler_event("weekly_analysis_failed", {
                    "status": "failed",
                    "completed_time": datetime.now().isoformat()
                })
                
                # Retry once after 1 hour if failed
                self.logger.info("⏰ Scheduling retry in 1 hour")
                schedule.every(1).hours.do(self._retry_analysis).tag('retry')
                
        except Exception as e:
            self.logger.error(f"❌ Scheduled analysis failed with exception: {str(e)}")
            self.logger.log_scheduler_event("weekly_analysis_error", {
                "status": "error",
                "error": str(e),
                "completed_time": datetime.now().isoformat()
            })
    
    def _retry_analysis(self):
        """Retry failed analysis (runs once)"""
        self.logger.log_scheduler_event("retry_analysis_started")
        
        try:
            success = self.system.run_weekly_analysis()
            
            if success:
                self.logger.log_scheduler_event("retry_analysis_completed", {"status": "success"})
            else:
                self.logger.log_scheduler_event("retry_analysis_failed", {"status": "failed"})
                
        except Exception as e:
            self.logger.error(f"❌ Retry analysis failed: {str(e)}")
        
        # Clear retry job after execution
        schedule.clear('retry')
    
    def setup_schedule(self):
        """Set up the weekly analysis schedule"""
        # Schedule for every Sunday at 9:00 AM
        schedule.every().sunday.at("09:00").do(self.run_scheduled_analysis)
        
        self.logger.log_scheduler_event("schedule_configured", {
            "schedule": "Every Sunday at 9:00 AM",
            "next_run": schedule.next_run().isoformat() if schedule.jobs else "No jobs scheduled"
        })
        
        return schedule
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        self.setup_schedule()
        
        self.logger.info("📅 AI Improvement System scheduler started")
        self.logger.info("⏰ Next analysis scheduled for: " + 
                        (schedule.next_run().strftime('%Y-%m-%d %H:%M:%S') if schedule.jobs else "No jobs"))
        
        # Run initial analysis if no recent reports exist
        recent_reports = self.system.report_manager.get_recent_reports(7)
        if not recent_reports:
            self.logger.info("🚀 No recent reports found. Running initial analysis...")
            self.run_scheduled_analysis()
        
        # Keep scheduler running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Scheduler error: {str(e)}")

def main():
    """Main entry point for scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Improvement System Scheduler')
    parser.add_argument('--run-now', action='store_true', 
                       help='Run analysis immediately instead of scheduling')
    parser.add_argument('--setup-only', action='store_true',
                       help='Show setup instructions without running')
    
    args = parser.parse_args()
    
    scheduler = AIImprovementScheduler()
    
    if args.run_now:
        print("🔍 Running analysis immediately...")
        scheduler.run_scheduled_analysis()
        print("✅ Analysis completed")
        
    elif args.setup_only:
        print("🔧 AI Improvement System Scheduler Setup")
        print("=" * 50)
        print("The scheduler will run weekly analysis every Sunday at 9:00 AM")
        print()
        print("To run the scheduler:")
        print("  python scheduler.py")
        print()
        print("To run analysis immediately:")
        print("  python scheduler.py --run-now")
        print()
        print("For production deployment, consider using:")
        print("- Windows Task Scheduler")
        print("- Linux/Mac cron jobs")
        print("- Docker containers with restart policies")
        print("- Process managers like PM2 or systemd")
        
    else:
        print("🤖 Starting AI Improvement System Scheduler...")
        print("Press Ctrl+C to stop")
        scheduler.run_scheduler()

if __name__ == "__main__":
    main()