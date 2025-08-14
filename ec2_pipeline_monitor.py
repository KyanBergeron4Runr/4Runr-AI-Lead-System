#!/usr/bin/env python3
"""
EC2 Pipeline Monitor - Remote monitoring for 4Runr AI Lead System
Monitors the autonomous pipeline running on EC2 from local environment
"""

import subprocess
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

class EC2PipelineMonitor:
    def __init__(self):
        load_dotenv()
        self.ec2_host = os.getenv('EC2_HOST', 'ubuntu@your-ec2-instance.amazonaws.com')
        self.ec2_key_path = os.getenv('EC2_KEY_PATH', '~/.ssh/your-key.pem')
        self.pipeline_pid = 21443  # The process ID from the nohup command
        self.remote_path = '/home/ubuntu/4Runr-AI-Lead-System/4runr-outreach-system'
        
    def ssh_command(self, command):
        """Execute SSH command on EC2 instance"""
        try:
            full_command = [
                'ssh', '-i', self.ec2_key_path, 
                '-o', 'StrictHostKeyChecking=no',
                self.ec2_host, 
                command
            ]
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'SSH command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def check_pipeline_status(self):
        """Check if the pipeline process is still running"""
        command = f"ps -p {self.pipeline_pid} -o pid,ppid,cmd --no-headers"
        result = self.ssh_command(command)
        
        if result['success'] and result['stdout']:
            return {
                'running': True,
                'pid': self.pipeline_pid,
                'process_info': result['stdout']
            }
        else:
            return {
                'running': False,
                'pid': self.pipeline_pid,
                'error': result['stderr'] or 'Process not found'
            }
    
    def get_pipeline_logs(self, lines=50):
        """Get the latest pipeline logs"""
        command = f"cd {self.remote_path} && tail -n {lines} pipeline.log"
        result = self.ssh_command(command)
        
        if result['success']:
            return {
                'success': True,
                'logs': result['stdout'].split('\n'),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': result['stderr'],
                'logs': []
            }
    
    def get_system_metrics(self):
        """Get EC2 system metrics"""
        commands = {
            'cpu': "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1",
            'memory': "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'",
            'disk': "df -h / | awk 'NR==2{printf \"%s\", $5}'",
            'load': "uptime | awk -F'load average:' '{print $2}'"
        }
        
        metrics = {}
        for metric, command in commands.items():
            result = self.ssh_command(command)
            if result['success']:
                metrics[metric] = result['stdout']
            else:
                metrics[metric] = 'N/A'
        
        return metrics
    
    def get_database_stats(self):
        """Get database statistics from EC2"""
        command = f"""cd {self.remote_path} && python3 -c "
import sqlite3
import os
db_path = 'data/leads_cache.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM leads')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT engagement_status, COUNT(*) FROM leads GROUP BY engagement_status')
    stages = dict(cursor.fetchall())
    cursor.execute('SELECT COUNT(*) FROM leads WHERE updated_at > datetime(\\'now\\', \\'-1 hour\\')')
    recent = cursor.fetchone()[0]
    conn.close()
    print(f'total:{total},recent:{recent},stages:{stages}')
else:
    print('database_not_found')
" """
        
        result = self.ssh_command(command)
        if result['success'] and 'total:' in result['stdout']:
            try:
                data = result['stdout']
                total = int(data.split('total:')[1].split(',')[0])
                recent = int(data.split('recent:')[1].split(',')[0])
                stages_str = data.split('stages:')[1]
                stages = eval(stages_str) if stages_str != '{}' else {}
                
                return {
                    'success': True,
                    'total_leads': total,
                    'recent_updates': recent,
                    'stage_distribution': stages
                }
            except Exception as e:
                return {'success': False, 'error': f'Parse error: {e}'}
        else:
            return {'success': False, 'error': result['stderr']}
    
    def restart_pipeline(self):
        """Restart the pipeline process"""
        # First kill the existing process
        kill_result = self.ssh_command(f"kill {self.pipeline_pid}")
        time.sleep(2)
        
        # Start new pipeline
        start_command = f"cd {self.remote_path} && nohup python run_outreach_pipeline.py > pipeline.log 2>&1 & echo $!"
        start_result = self.ssh_command(start_command)
        
        if start_result['success']:
            new_pid = start_result['stdout'].strip()
            return {
                'success': True,
                'old_pid': self.pipeline_pid,
                'new_pid': new_pid,
                'message': f'Pipeline restarted. New PID: {new_pid}'
            }
        else:
            return {
                'success': False,
                'error': start_result['stderr'],
                'message': 'Failed to restart pipeline'
            }
    
    def stop_pipeline(self):
        """Stop the pipeline process"""
        result = self.ssh_command(f"kill {self.pipeline_pid}")
        
        if result['success']:
            return {
                'success': True,
                'message': f'Pipeline process {self.pipeline_pid} stopped'
            }
        else:
            return {
                'success': False,
                'error': result['stderr'],
                'message': 'Failed to stop pipeline'
            }
    
    def generate_status_report(self):
        """Generate comprehensive status report"""
        print("🔍 EC2 PIPELINE MONITORING REPORT")
        print("=" * 60)
        print(f"📅 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🖥️  EC2 Host: {self.ec2_host}")
        print()
        
        # Pipeline Status
        pipeline_status = self.check_pipeline_status()
        print(f"🚀 PIPELINE STATUS: {'🟢 RUNNING' if pipeline_status['running'] else '🔴 STOPPED'}")
        if pipeline_status['running']:
            print(f"   Process ID: {pipeline_status['pid']}")
            print(f"   Command: {pipeline_status['process_info']}")
        else:
            print(f"   Error: {pipeline_status.get('error', 'Unknown')}")
        print()
        
        # System Metrics
        metrics = self.get_system_metrics()
        print("💻 SYSTEM METRICS:")
        print(f"   CPU Usage: {metrics.get('cpu', 'N/A')}%")
        print(f"   Memory Usage: {metrics.get('memory', 'N/A')}%")
        print(f"   Disk Usage: {metrics.get('disk', 'N/A')}")
        print(f"   Load Average: {metrics.get('load', 'N/A')}")
        print()
        
        # Database Stats
        db_stats = self.get_database_stats()
        print("🗄️ DATABASE STATUS:")
        if db_stats['success']:
            print(f"   Total Leads: {db_stats['total_leads']}")
            print(f"   Recent Updates (1h): {db_stats['recent_updates']}")
            print(f"   Stage Distribution: {db_stats['stage_distribution']}")
        else:
            print(f"   Error: {db_stats['error']}")
        print()
        
        # Recent Logs
        logs = self.get_pipeline_logs(10)
        print("📋 RECENT PIPELINE LOGS:")
        if logs['success']:
            for line in logs['logs'][-5:]:  # Show last 5 lines
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"   Error: {logs['error']}")
        
        print("\n" + "=" * 60)
        
        return {
            'pipeline': pipeline_status,
            'system': metrics,
            'database': db_stats,
            'logs': logs
        }
    
    def watch_pipeline(self, interval=30):
        """Continuously monitor pipeline with updates every interval seconds"""
        print(f"👀 Watching EC2 pipeline (updates every {interval}s). Press Ctrl+C to stop.")
        print()
        
        try:
            while True:
                self.generate_status_report()
                print(f"\n⏰ Next update in {interval} seconds...")
                time.sleep(interval)
                print("\n" + "🔄 REFRESHING..." + "\n")
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user.")

def main():
    """Main monitoring function"""
    import sys
    
    monitor = EC2PipelineMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'status':
            monitor.generate_status_report()
        elif command == 'watch':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            monitor.watch_pipeline(interval)
        elif command == 'logs':
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            logs = monitor.get_pipeline_logs(lines)
            if logs['success']:
                for line in logs['logs']:
                    print(line)
            else:
                print(f"Error getting logs: {logs['error']}")
        elif command == 'restart':
            result = monitor.restart_pipeline()
            print(result['message'])
        elif command == 'stop':
            result = monitor.stop_pipeline()
            print(result['message'])
        else:
            print("Usage: python ec2_pipeline_monitor.py [status|watch|logs|restart|stop]")
    else:
        monitor.generate_status_report()

if __name__ == "__main__":
    main()