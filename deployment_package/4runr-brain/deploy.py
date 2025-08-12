#!/usr/bin/env python3
"""
Campaign Brain Deployment and Monitoring Script

Handles deployment, monitoring, and management of the Campaign Brain service.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class CampaignBrainDeployment:
    """Manages Campaign Brain deployment and monitoring"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.docker_compose_file = self.project_dir / "docker-compose.yml"
        self.env_file = self.project_dir / ".env"
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        
        print("🔍 Checking prerequisites...")
        
        issues = []
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                issues.append("Docker is not installed or not accessible")
            else:
                print(f"  ✅ Docker: {result.stdout.strip()}")
        except FileNotFoundError:
            issues.append("Docker is not installed")
        
        # Check Docker Compose
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                issues.append("Docker Compose is not installed or not accessible")
            else:
                print(f"  ✅ Docker Compose: {result.stdout.strip()}")
        except FileNotFoundError:
            issues.append("Docker Compose is not installed")
        
        # Check environment file
        if not self.env_file.exists():
            issues.append(f"Environment file not found: {self.env_file}")
            print(f"  ❌ Create .env file from .env.example")
        else:
            print(f"  ✅ Environment file: {self.env_file}")
        
        # Check configuration
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                env_content = f.read()
                
            if 'OPENAI_API_KEY=your-openai-api-key' in env_content:
                issues.append("OpenAI API key not configured in .env file")
            else:
                print("  ✅ OpenAI API key configured")
        
        if issues:
            print("\n❌ Prerequisites not met:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        
        print("✅ All prerequisites met!")
        return True
    
    def deploy(self, mode: str = "production") -> bool:
        """Deploy the Campaign Brain service"""
        
        print(f"🚀 Deploying Campaign Brain in {mode} mode...")
        
        if not self.check_prerequisites():
            return False
        
        try:
            # Build and start services
            cmd = ['docker-compose', 'up', '-d', '--build']
            
            if mode == "development":
                cmd.extend(['--profile', 'api'])
            
            result = subprocess.run(cmd, cwd=self.project_dir)
            
            if result.returncode == 0:
                print("✅ Campaign Brain deployed successfully!")
                
                # Wait for services to start
                print("⏳ Waiting for services to start...")
                time.sleep(10)
                
                # Check health
                health_status = self.health_check()
                if health_status:
                    print("✅ Health check passed!")
                    self.show_status()
                    return True
                else:
                    print("❌ Health check failed!")
                    return False
            else:
                print("❌ Deployment failed!")
                return False
                
        except Exception as e:
            print(f"❌ Deployment error: {str(e)}")
            return False
    
    def health_check(self) -> bool:
        """Perform health check on deployed service"""
        
        try:
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'campaign-brain',
                'python', 'serve_campaign_brain.py', '--health-check'
            ], cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                health_data = json.loads(result.stdout)
                status = health_data.get('status', 'unknown')
                
                print(f"🏥 Health Status: {status.upper()}")
                
                if 'issues' in health_data:
                    print("⚠️  Issues:")
                    for issue in health_data['issues']:
                        print(f"  • {issue}")
                
                return status == 'healthy'
            else:
                print(f"❌ Health check failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    def show_status(self):
        """Show service status and statistics"""
        
        print("\n📊 Service Status:")
        
        try:
            # Get container status
            result = subprocess.run([
                'docker-compose', 'ps'
            ], cwd=self.project_dir, capture_output=True, text=True)
            
            print(result.stdout)
            
            # Get service statistics
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'campaign-brain',
                'python', 'serve_campaign_brain.py', '--stats'
            ], cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                stats = json.loads(result.stdout)
                print(f"📈 Statistics:")
                print(f"  Runtime: {stats.get('runtime_seconds', 0):.0f} seconds")
                print(f"  Processed: {stats.get('processed', 0)} leads")
                print(f"  Approved: {stats.get('approved', 0)} campaigns")
                print(f"  Manual Review: {stats.get('manual_review', 0)} campaigns")
                print(f"  Errors: {stats.get('errors', 0)}")
                print(f"  Approval Rate: {stats.get('approval_rate', 0):.1f}%")
            
        except Exception as e:
            print(f"❌ Error getting status: {str(e)}")
    
    def stop(self):
        """Stop the Campaign Brain service"""
        
        print("🛑 Stopping Campaign Brain service...")
        
        try:
            result = subprocess.run([
                'docker-compose', 'down'
            ], cwd=self.project_dir)
            
            if result.returncode == 0:
                print("✅ Service stopped successfully!")
            else:
                print("❌ Error stopping service!")
                
        except Exception as e:
            print(f"❌ Stop error: {str(e)}")
    
    def restart(self):
        """Restart the Campaign Brain service"""
        
        print("🔄 Restarting Campaign Brain service...")
        self.stop()
        time.sleep(5)
        return self.deploy()
    
    def logs(self, follow: bool = False, tail: int = 100):
        """Show service logs"""
        
        cmd = ['docker-compose', 'logs']
        
        if follow:
            cmd.append('-f')
        
        cmd.extend(['--tail', str(tail)])
        cmd.append('campaign-brain')
        
        try:
            subprocess.run(cmd, cwd=self.project_dir)
        except KeyboardInterrupt:
            print("\n📋 Log viewing stopped")
    
    def process_leads(self, batch_size: int = 10, dry_run: bool = False):
        """Process leads through the deployed service"""
        
        print(f"🧠 Processing {batch_size} leads...")
        
        cmd = [
            'docker-compose', 'exec', '-T', 'campaign-brain',
            'python', 'serve_campaign_brain.py',
            '--batch-size', str(batch_size)
        ]
        
        if dry_run:
            cmd.append('--dry-run')
            print("🧪 DRY RUN MODE")
        
        try:
            result = subprocess.run(cmd, cwd=self.project_dir)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Processing error: {str(e)}")
            return False
    
    def backup_data(self):
        """Backup logs and trace data"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.project_dir / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        print(f"💾 Creating backup: {backup_dir}")
        
        try:
            # Copy logs and traces
            import shutil
            
            for dir_name in ['logs', 'trace_logs', 'queue']:
                src_dir = self.project_dir / dir_name
                if src_dir.exists():
                    dst_dir = backup_dir / dir_name
                    shutil.copytree(src_dir, dst_dir)
                    print(f"  ✅ Backed up {dir_name}")
            
            print(f"✅ Backup completed: {backup_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Backup error: {str(e)}")
            return False


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Campaign Brain Deployment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy in production mode
  python deploy.py deploy

  # Deploy in development mode (with API)
  python deploy.py deploy --mode development

  # Check health
  python deploy.py health

  # Show status
  python deploy.py status

  # Process leads
  python deploy.py process --batch-size 5

  # View logs
  python deploy.py logs --follow

  # Restart service
  python deploy.py restart
        """
    )
    
    parser.add_argument('action', choices=[
        'deploy', 'health', 'status', 'stop', 'restart', 'logs', 'process', 'backup'
    ], help='Action to perform')
    
    parser.add_argument('--mode', choices=['production', 'development'], 
                       default='production', help='Deployment mode')
    parser.add_argument('--batch-size', type=int, default=10, 
                       help='Number of leads to process')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Dry run mode for processing')
    parser.add_argument('--follow', action='store_true', 
                       help='Follow logs in real-time')
    parser.add_argument('--tail', type=int, default=100, 
                       help='Number of log lines to show')
    
    args = parser.parse_args()
    
    deployment = CampaignBrainDeployment()
    
    try:
        if args.action == 'deploy':
            success = deployment.deploy(args.mode)
        elif args.action == 'health':
            success = deployment.health_check()
        elif args.action == 'status':
            deployment.show_status()
            success = True
        elif args.action == 'stop':
            deployment.stop()
            success = True
        elif args.action == 'restart':
            success = deployment.restart()
        elif args.action == 'logs':
            deployment.logs(args.follow, args.tail)
            success = True
        elif args.action == 'process':
            success = deployment.process_leads(args.batch_size, args.dry_run)
        elif args.action == 'backup':
            success = deployment.backup_data()
        else:
            success = False
        
        return success
        
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)