#!/usr/bin/env python3
"""
Pipeline Dashboard - Local monitoring interface for EC2 pipeline
Simple web dashboard to monitor the remote pipeline
"""

import json
import time
from datetime import datetime
from ec2_pipeline_monitor import EC2PipelineMonitor
import threading
import os

class PipelineDashboard:
    def __init__(self):
        self.monitor = EC2PipelineMonitor()
        self.last_update = None
        self.status_data = {}
        
    def get_dashboard_data(self):
        """Get all dashboard data"""
        try:
            pipeline_status = self.monitor.check_pipeline_status()
            system_metrics = self.monitor.get_system_metrics()
            database_stats = self.monitor.get_database_stats()
            recent_logs = self.monitor.get_pipeline_logs(20)
            
            self.status_data = {
                'timestamp': datetime.now().isoformat(),
                'pipeline': pipeline_status,
                'system': system_metrics,
                'database': database_stats,
                'logs': recent_logs,
                'connection_status': 'connected'
            }
            self.last_update = datetime.now()
            
        except Exception as e:
            self.status_data = {
                'timestamp': datetime.now().isoformat(),
                'connection_status': 'error',
                'error': str(e)
            }
        
        return self.status_data
    
    def print_dashboard(self):
        """Print a text-based dashboard"""
        os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
        
        print("🚀 4RUNR AI PIPELINE DASHBOARD")
        print("=" * 80)
        
        data = self.get_dashboard_data()
        
        if data.get('connection_status') == 'error':
            print(f"❌ CONNECTION ERROR: {data.get('error', 'Unknown error')}")
            print("\n💡 Make sure to:")
            print("   1. Update .env with your EC2_HOST and EC2_KEY_PATH")
            print("   2. Ensure SSH key has correct permissions (chmod 600)")
            print("   3. Verify EC2 instance is running and accessible")
            return
        
        print(f"🕐 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🖥️  EC2 Host: {self.monitor.ec2_host}")
        print()
        
        # Pipeline Status
        pipeline = data.get('pipeline', {})
        status_icon = "🟢" if pipeline.get('running') else "🔴"
        print(f"🚀 PIPELINE: {status_icon} {'RUNNING' if pipeline.get('running') else 'STOPPED'}")
        if pipeline.get('running'):
            print(f"   📍 PID: {pipeline.get('pid')}")
        else:
            print(f"   ❌ Error: {pipeline.get('error', 'Process not found')}")
        print()
        
        # System Health
        system = data.get('system', {})
        print("💻 SYSTEM HEALTH:")
        print(f"   🔥 CPU: {system.get('cpu', 'N/A')}%")
        print(f"   🧠 Memory: {system.get('memory', 'N/A')}%")
        print(f"   💾 Disk: {system.get('disk', 'N/A')}")
        print(f"   ⚖️  Load: {system.get('load', 'N/A')}")
        print()
        
        # Database Stats
        database = data.get('database', {})
        if database.get('success'):
            print("🗄️ DATABASE:")
            print(f"   📊 Total Leads: {database.get('total_leads', 0)}")
            print(f"   🔄 Recent Updates: {database.get('recent_updates', 0)}")
            stages = database.get('stage_distribution', {})
            if stages:
                print("   📈 Lead Stages:")
                for stage, count in stages.items():
                    print(f"      • {stage}: {count}")
        else:
            print(f"🗄️ DATABASE: ❌ {database.get('error', 'Unknown error')}")
        print()
        
        # Recent Activity
        logs = data.get('logs', {})
        if logs.get('success'):
            print("📋 RECENT ACTIVITY:")
            recent_logs = logs.get('logs', [])[-5:]  # Last 5 lines
            for log_line in recent_logs:
                if log_line.strip():
                    # Truncate long lines
                    display_line = log_line[:70] + "..." if len(log_line) > 70 else log_line
                    print(f"   {display_line}")
        else:
            print(f"📋 LOGS: ❌ {logs.get('error', 'Cannot access logs')}")
        
        print("\n" + "=" * 80)
        print("💡 Commands: [R]efresh | [L]ogs | [S]top Pipeline | [Q]uit")
    
    def interactive_dashboard(self):
        """Run interactive dashboard"""
        print("🚀 Starting Pipeline Dashboard...")
        print("💡 Make sure your .env file is configured with EC2 details")
        time.sleep(2)
        
        while True:
            self.print_dashboard()
            
            print("\nEnter command (or wait 30s for auto-refresh): ", end='', flush=True)
            
            # Non-blocking input with timeout
            import select
            import sys
            
            if select.select([sys.stdin], [], [], 30) == ([sys.stdin], [], []):
                command = input().strip().lower()
                
                if command == 'q' or command == 'quit':
                    print("👋 Dashboard closed.")
                    break
                elif command == 'r' or command == 'refresh':
                    continue  # Will refresh on next loop
                elif command == 'l' or command == 'logs':
                    self.show_full_logs()
                elif command == 's' or command == 'stop':
                    self.stop_pipeline_interactive()
                elif command == 'restart':
                    self.restart_pipeline_interactive()
                else:
                    print(f"Unknown command: {command}")
                    time.sleep(1)
            # If no input, continue to auto-refresh
    
    def show_full_logs(self):
        """Show full pipeline logs"""
        print("\n📋 FETCHING FULL LOGS...")
        logs = self.monitor.get_pipeline_logs(100)
        
        if logs['success']:
            print("\n" + "="*80)
            print("📋 PIPELINE LOGS (Last 100 lines)")
            print("="*80)
            for line in logs['logs']:
                if line.strip():
                    print(line)
            print("="*80)
        else:
            print(f"❌ Error getting logs: {logs['error']}")
        
        input("\nPress Enter to return to dashboard...")
    
    def stop_pipeline_interactive(self):
        """Interactive pipeline stop"""
        print(f"\n⚠️  Are you sure you want to stop pipeline PID {self.monitor.pipeline_pid}? (y/N): ", end='')
        confirm = input().strip().lower()
        
        if confirm == 'y' or confirm == 'yes':
            print("🛑 Stopping pipeline...")
            result = self.monitor.stop_pipeline()
            print(f"📝 Result: {result['message']}")
        else:
            print("❌ Pipeline stop cancelled.")
        
        time.sleep(2)
    
    def restart_pipeline_interactive(self):
        """Interactive pipeline restart"""
        print(f"\n🔄 Are you sure you want to restart the pipeline? (y/N): ", end='')
        confirm = input().strip().lower()
        
        if confirm == 'y' or confirm == 'yes':
            print("🔄 Restarting pipeline...")
            result = self.monitor.restart_pipeline()
            print(f"📝 Result: {result['message']}")
            if result['success']:
                self.monitor.pipeline_pid = int(result['new_pid'])
        else:
            print("❌ Pipeline restart cancelled.")
        
        time.sleep(2)

def main():
    """Main dashboard function"""
    import sys
    
    dashboard = PipelineDashboard()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # Output JSON for programmatic use
        data = dashboard.get_dashboard_data()
        print(json.dumps(data, indent=2))
    else:
        # Run interactive dashboard
        try:
            dashboard.interactive_dashboard()
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard closed by user.")

if __name__ == "__main__":
    main()