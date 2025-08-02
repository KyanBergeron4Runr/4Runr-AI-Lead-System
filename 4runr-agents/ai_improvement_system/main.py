#!/usr/bin/env python3
"""
AI Improvement System - Main Runner

Main entry point for the automated AI improvement system.
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the system modules
sys.path.append(str(Path(__file__).parent.parent))

from ai_improvement_system.config import get_config
from ai_improvement_system.logger import get_logger
from ai_improvement_system.analysis_engine import AIAnalysisEngine
from ai_improvement_system.recommendation_engine import RecommendationEngine
from ai_improvement_system.report_manager import ReportManager

class AIImprovementSystem:
    """Main AI Improvement System orchestrator"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("ai-improvement-main")
        
        # Initialize system components
        self.analysis_engine = AIAnalysisEngine()
        self.recommendation_engine = RecommendationEngine()
        self.report_manager = ReportManager()
        
        self.logger.info("🤖 AI Improvement System initialized")
    
    def run_weekly_analysis(self, days_back: int = 7) -> bool:
        """Run the complete weekly analysis workflow"""
        try:
            self.logger.info("🚀 Starting weekly AI improvement analysis")
            analysis_start = datetime.now()
            
            # Step 1: Perform analysis
            self.logger.info("📊 Step 1: Analyzing AI performance data")
            analysis_results = self.analysis_engine.analyze_weekly_performance(days_back)
            
            # Step 2: Generate recommendations
            self.logger.info("🎯 Step 2: Generating improvement recommendations")
            recommendations = self.recommendation_engine.generate_recommendations(analysis_results)
            
            # Update analysis results with recommendations
            analysis_results.recommendations = recommendations
            
            # Step 3: Generate reports
            self.logger.info("📋 Step 3: Generating analysis reports")
            report_paths = self.report_manager.generate_weekly_report(analysis_results, recommendations)
            
            # Log completion
            analysis_duration = (datetime.now() - analysis_start).total_seconds()
            
            self.logger.info("✅ Weekly analysis completed successfully")
            self.logger.info(f"   📊 Analysis duration: {analysis_duration:.2f} seconds")
            self.logger.info(f"   📈 System health: {analysis_results.overall_health}")
            self.logger.info(f"   🚨 Alerts generated: {len(analysis_results.alerts)}")
            self.logger.info(f"   💡 Recommendations: {len(recommendations)}")
            
            # Log report locations
            self.logger.info("📁 Reports generated:")
            for report_type, path in report_paths.items():
                self.logger.info(f"   {report_type}: {path}")
            
            # Log system health
            self.logger.log_system_health(analysis_results.overall_health, {
                "total_logs_analyzed": analysis_results.metadata.get("total_logs_analyzed", 0),
                "alerts_count": len(analysis_results.alerts),
                "recommendations_count": len(recommendations),
                "analysis_duration": analysis_duration
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Weekly analysis failed: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def get_system_status(self) -> dict:
        """Get current system status and recent performance"""
        try:
            # Get dashboard data
            dashboard_data = self.report_manager.generate_dashboard_data()
            
            # Add system configuration info
            status = {
                "system_info": {
                    "version": "1.0.0",
                    "status": "operational",
                    "last_check": datetime.now().isoformat(),
                    "config": {
                        "analysis_days_back": self.config.analysis.analysis_days_back,
                        "report_retention_days": self.config.analysis.report_retention_days,
                        "max_recommendations": self.config.analysis.max_recommendations
                    }
                },
                "dashboard_data": dashboard_data
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get system status: {str(e)}")
            return {"error": str(e)}
    
    def run_maintenance(self) -> bool:
        """Run system maintenance tasks"""
        try:
            self.logger.info("🧹 Running system maintenance")
            
            # Report manager handles its own maintenance
            # This could be extended to include other maintenance tasks
            
            self.logger.info("✅ System maintenance completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ System maintenance failed: {str(e)}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='4Runr AI Improvement System')
    parser.add_argument('--analyze', action='store_true', 
                       help='Run weekly analysis')
    parser.add_argument('--days-back', type=int, default=7,
                       help='Number of days to analyze (default: 7)')
    parser.add_argument('--status', action='store_true',
                       help='Show system status')
    parser.add_argument('--maintenance', action='store_true',
                       help='Run maintenance tasks')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Initialize system
    system = AIImprovementSystem()
    
    if args.verbose:
        system.logger.logger.setLevel("DEBUG")
    
    # Execute requested action
    if args.analyze:
        print("🔍 Running weekly AI analysis...")
        success = system.run_weekly_analysis(args.days_back)
        if success:
            print("✅ Analysis completed successfully!")
            print("📊 Check the ai_analysis_reports directory for detailed results")
        else:
            print("❌ Analysis failed. Check logs for details.")
            sys.exit(1)
    
    elif args.status:
        print("📊 Getting system status...")
        status = system.get_system_status()
        
        if "error" in status:
            print(f"❌ Error getting status: {status['error']}")
            sys.exit(1)
        
        # Display status information
        system_info = status.get("system_info", {})
        dashboard_data = status.get("dashboard_data", {})
        
        print(f"\n🤖 AI Improvement System Status")
        print(f"Version: {system_info.get('version', 'Unknown')}")
        print(f"Status: {system_info.get('status', 'Unknown')}")
        print(f"Last Check: {system_info.get('last_check', 'Unknown')}")
        
        if "latest_report" in dashboard_data and dashboard_data["latest_report"]:
            latest = dashboard_data["latest_report"]
            print(f"\n📋 Latest Report:")
            print(f"Date: {latest.get('date', 'Unknown')}")
            print(f"Health: {latest.get('overall_health', 'Unknown')}")
            print(f"Alerts: {latest.get('alerts_count', 0)}")
            print(f"Recommendations: {latest.get('recommendations_count', 0)}")
        
        health_trend = dashboard_data.get("health_trend", {})
        if health_trend.get("trend") != "insufficient_data":
            trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(health_trend.get("trend"), "❓")
            print(f"\n{trend_emoji} Health Trend: {health_trend.get('trend', 'Unknown')}")
    
    elif args.maintenance:
        print("🧹 Running system maintenance...")
        success = system.run_maintenance()
        if success:
            print("✅ Maintenance completed successfully!")
        else:
            print("❌ Maintenance failed. Check logs for details.")
            sys.exit(1)
    
    else:
        # Show help if no action specified
        parser.print_help()
        print("\n🤖 4Runr AI Improvement System")
        print("Examples:")
        print("  python main.py --analyze              # Run weekly analysis")
        print("  python main.py --status               # Show system status")
        print("  python main.py --maintenance          # Run maintenance")
        print("  python main.py --analyze --days-back 14  # Analyze last 14 days")

if __name__ == "__main__":
    main()