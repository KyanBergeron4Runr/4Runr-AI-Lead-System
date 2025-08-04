#!/usr/bin/env python3
"""
Deploy Auto Lead Processing System

Sets up the automated lead detection, enrichment, and processing system
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

def create_systemd_service():
    """Create systemd service for continuous processing"""
    
    service_content = f"""[Unit]
Description=4Runr Auto Lead Processor
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={Path(__file__).parent.absolute()}
Environment=PATH={os.getenv('PATH')}
ExecStart={sys.executable} auto_lead_processor.py --continuous --interval 10
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path('/etc/systemd/system/4runr-auto-processor.service')
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Created systemd service: {service_file}")
        return True
    except PermissionError:
        print(f"❌ Permission denied. Run with sudo to create systemd service")
        return False
    except Exception as e:
        print(f"❌ Error creating service: {e}")
        return False

def create_cron_job():
    """Create cron job for periodic processing"""
    
    cron_command = f"*/10 * * * * cd {Path(__file__).parent.absolute()} && {sys.executable} auto_lead_processor.py --once >> logs/auto_processor.log 2>&1"
    
    try:
        # Add to crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        if cron_command not in current_cron:
            new_cron = current_cron + f"\n{cron_command}\n"
            
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_cron)
            
            if process.returncode == 0:
                print("✅ Added cron job for auto processing (every 10 minutes)")
                return True
            else:
                print("❌ Failed to add cron job")
                return False
        else:
            print("✅ Cron job already exists")
            return True
            
    except Exception as e:
        print(f"❌ Error setting up cron job: {e}")
        return False

def create_docker_compose():
    """Create Docker Compose for containerized deployment"""
    
    docker_compose_content = """version: '3.8'

services:
  auto-processor:
    build: .
    container_name: 4runr-auto-processor
    restart: unless-stopped
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    command: python auto_lead_processor.py --continuous --interval 10
    
  campaign-brain:
    build: ../4runr-brain
    container_name: 4runr-campaign-brain
    restart: unless-stopped
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./data:/app/data
      - ../4runr-brain/logs:/app/logs
    ports:
      - "8080:8080"
    command: python serve_campaign_brain.py --batch-size 5
    depends_on:
      - auto-processor

networks:
  default:
    name: 4runr-network
"""
    
    docker_compose_file = Path(__file__).parent / 'docker-compose.auto.yml'
    
    try:
        with open(docker_compose_file, 'w') as f:
            f.write(docker_compose_content)
        
        print(f"✅ Created Docker Compose: {docker_compose_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating Docker Compose: {e}")
        return False

def create_monitoring_script():
    """Create monitoring script to check system health"""
    
    monitoring_script = '''#!/usr/bin/env python3
"""
Monitor Auto Lead Processing System
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from database.lead_database import get_lead_database

def check_system_health():
    """Check system health and report issues"""
    
    print(f"🔍 System Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        db = get_lead_database()
        stats = db.get_database_stats()
        
        # Database health
        print(f"📊 Database: {stats.get('total_leads', 0)} leads")
        print(f"🎯 Ready for outreach: {len(db.search_leads({'status': 'Ready for Outreach'}))}")
        print(f"⏳ Needs enrichment: {stats.get('needs_enrichment', 0)}")
        
        # Check for stale leads (not updated in 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        stale_leads = db.search_leads({'needs_enrichment': True})
        stale_count = 0
        
        for lead in stale_leads:
            updated_at = lead.get('updated_at', '')
            if updated_at:
                try:
                    updated_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    if updated_time < yesterday:
                        stale_count += 1
                except:
                    pass
        
        if stale_count > 0:
            print(f"⚠️  Warning: {stale_count} leads haven't been processed in 24+ hours")
        else:
            print("✅ All leads are being processed regularly")
        
        # Check recent activity
        recent_leads = db.get_recent_leads(days=1, limit=10)
        print(f"📈 Recent activity: {len(recent_leads)} leads updated today")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == '__main__':
    check_system_health()
'''
    
    monitoring_file = Path(__file__).parent / 'monitor_system.py'
    
    try:
        with open(monitoring_file, 'w') as f:
            f.write(monitoring_script)
        
        # Make executable
        monitoring_file.chmod(0o755)
        
        print(f"✅ Created monitoring script: {monitoring_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating monitoring script: {e}")
        return False

def setup_log_directory():
    """Set up log directory"""
    
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Create log rotation script
    logrotate_config = f"""
{log_dir}/auto_processor.log {{
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 {os.getenv('USER', 'ubuntu')} {os.getenv('USER', 'ubuntu')}
}}
"""
    
    logrotate_file = Path('/etc/logrotate.d/4runr-auto-processor')
    
    try:
        with open(logrotate_file, 'w') as f:
            f.write(logrotate_config)
        print(f"✅ Created log rotation config: {logrotate_file}")
    except PermissionError:
        print("⚠️  Could not create log rotation (run with sudo for this feature)")
    except Exception as e:
        print(f"⚠️  Log rotation setup failed: {e}")
    
    print(f"✅ Log directory ready: {log_dir}")
    return True

def main():
    """Main deployment function"""
    
    print("🚀 Deploying 4Runr Auto Lead Processing System")
    print("=" * 60)
    
    # Setup log directory
    setup_log_directory()
    
    # Create monitoring script
    create_monitoring_script()
    
    # Create Docker Compose
    create_docker_compose()
    
    print("\n📋 Deployment Options:")
    print("1. Systemd Service (Linux)")
    print("2. Cron Job (Unix/Linux)")
    print("3. Docker Compose")
    print("4. Manual (run scripts manually)")
    
    choice = input("\nChoose deployment method (1-4): ").strip()
    
    if choice == '1':
        if create_systemd_service():
            print("\n🎯 Next steps for systemd:")
            print("sudo systemctl daemon-reload")
            print("sudo systemctl enable 4runr-auto-processor")
            print("sudo systemctl start 4runr-auto-processor")
            print("sudo systemctl status 4runr-auto-processor")
    
    elif choice == '2':
        if create_cron_job():
            print("\n🎯 Cron job setup complete!")
            print("Check with: crontab -l")
            print("View logs: tail -f logs/auto_processor.log")
    
    elif choice == '3':
        print("\n🎯 Next steps for Docker:")
        print("docker-compose -f docker-compose.auto.yml up -d")
        print("docker-compose -f docker-compose.auto.yml logs -f")
    
    elif choice == '4':
        print("\n🎯 Manual deployment:")
        print("Run once: python auto_lead_processor.py --once")
        print("Run continuous: python auto_lead_processor.py --continuous")
        print("Monitor: python monitor_system.py")
    
    else:
        print("❌ Invalid choice")
        return 1
    
    print("\n✅ Deployment setup complete!")
    print("\n📊 Monitor your system:")
    print("python monitor_system.py")
    print("python quick_db_view.py")
    
    return 0

if __name__ == '__main__':
    exit(main())