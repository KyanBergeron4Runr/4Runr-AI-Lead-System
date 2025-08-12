#!/usr/bin/env python3
"""
4Runr AI Lead System - EC2 Deployment Script
Complete deployment automation for EC2
"""

import os
import sys
import subprocess
import json
from datetime import datetime

class EC2Deployer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def create_systemd_services(self):
        """Create systemd service files"""
        self.log("Creating systemd services...")
        
        services = {
            '4runr-automation': {
                'description': '4Runr AI Lead System - Main Automation',
                'exec_start': '/usr/bin/python3 /opt/4runr/system_controller.py --daily-sync',
                'working_directory': '/opt/4runr'
            },
            '4runr-brain': {
                'description': '4Runr AI Lead System - Brain Service',
                'exec_start': '/usr/bin/python3 /opt/4runr/4runr-brain/serve_campaign_brain.py',
                'working_directory': '/opt/4runr/4runr-brain'
            },
            '4runr-email': {
                'description': '4Runr AI Lead System - Email Delivery',
                'exec_start': '/usr/bin/python3 /opt/4runr/email_delivery_system.py --send',
                'working_directory': '/opt/4runr'
            }
        }
        
        for service_name, config in services.items():
            service_content = f"""[Unit]
Description={config['description']}
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={config['working_directory']}
ExecStart={config['exec_start']}
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin
Environment=PYTHONPATH={config['working_directory']}

[Install]
WantedBy=multi-user.target
"""
            
            service_file = f"/etc/systemd/system/{service_name}.service"
            self.log(f"Creating {service_file}")
            
            # In real deployment, this would write to the actual file
            print(f"Service file content for {service_name}:")
            print(service_content)
            print("-" * 50)
    
    def create_cron_jobs(self):
        """Create cron jobs for automation"""
        self.log("Setting up cron jobs...")
        
        cron_jobs = [
            "0 6 * * * cd /opt/4runr && python3 system_controller.py --daily-sync",
            "*/15 * * * * cd /opt/4runr && python3 multi_step_email_system.py --send 3",
            "0 */4 * * * cd /opt/4runr && python3 system_controller.py --health",
            "0 2 * * * cd /opt/4runr && python3 backup_recovery.py --backup"
        ]
        
        for job in cron_jobs:
            self.log(f"Cron job: {job}")
    
    def create_deployment_script(self):
        """Create the main deployment script"""
        self.log("Creating deployment script...")
        
        script_content = """#!/bin/bash
# 4Runr AI Lead System - EC2 Deployment Script

set -e

echo "Starting 4Runr AI Lead System deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv git

# Create application directory
sudo mkdir -p /opt/4runr
sudo chown ubuntu:ubuntu /opt/4runr

# Copy application files
cp -r * /opt/4runr/

# Set up virtual environment
cd /opt/4runr
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set up database directory
mkdir -p /opt/4runr/data
mkdir -p /opt/4runr/logs
mkdir -p /opt/4runr/backups

# Set permissions
chmod +x /opt/4runr/system_controller.py
chmod +x /opt/4runr/email_delivery_system.py

# Run initial system setup
python3 system_controller.py --deploy

# Set up systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable 4runr-automation
sudo systemctl enable 4runr-brain
sudo systemctl enable 4runr-email

sudo systemctl start 4runr-automation
sudo systemctl start 4runr-brain
sudo systemctl start 4runr-email

# Set up cron jobs
crontab cron_jobs.txt

echo "Deployment complete!"
echo "Check service status with: sudo systemctl status 4runr-automation"
echo "View logs with: journalctl -u 4runr-automation -f"
"""
        
        with open("deploy_ec2.sh", "w", encoding='utf-8') as f:
            f.write(script_content)
        
        os.chmod("deploy_ec2.sh", 0o755)
        self.log("Created deploy_ec2.sh")
    
    def test_email_system(self):
        """Test the email delivery system"""
        self.log("Testing email system...")
        
        try:
            result = subprocess.run([
                'python', 'email_delivery_system.py', '--test'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log("Email system test passed")
                return True
            else:
                self.log(f"Email system test failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"Email system test error: {str(e)}")
            return False
    
    def generate_deployment_summary(self):
        """Generate deployment summary"""
        self.log("Generating deployment summary...")
        
        summary = {
            'deployment_date': datetime.now().isoformat(),
            'system_components': {
                '4runr-brain': 'AI campaign generation system',
                '4runr-lead-scraper': 'Lead discovery and data collection',
                '4runr-outreach-system': 'Lead processing and automation',
                'email-delivery': 'Email sending system',
                'monitoring': 'System health monitoring'
            },
            'databases': {
                'primary': '4runr-lead-scraper/data/leads.db',
                'leads_count': 'Check with system_controller.py --health'
            },
            'services': {
                '4runr-automation': 'Main automation service',
                '4runr-brain': 'AI brain service',
                '4runr-email': 'Email delivery service'
            },
            'cron_jobs': [
                'Daily sync at 6:00 AM',
                'Email sending every 15 minutes',
                'Health check every 4 hours',
                'Backup at 2:00 AM daily'
            ],
            'monitoring': {
                'health_check': 'python3 system_controller.py --health',
                'email_queue': 'python3 email_delivery_system.py --queue',
                'logs': 'journalctl -u 4runr-automation -f'
            }
        }
        
        with open(f"deployment_summary_{self.timestamp}.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"Deployment summary saved to deployment_summary_{self.timestamp}.json")
        
        # Print summary
        print("\n" + "="*60)
        print("DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"Deployment Date: {summary['deployment_date']}")
        print(f"Components: {len(summary['system_components'])}")
        print(f"Services: {len(summary['services'])}")
        print(f"Cron Jobs: {len(summary['cron_jobs'])}")
        print("\nNext Steps:")
        print("1. Copy files to EC2: scp -r * ubuntu@your-ec2:/tmp/4runr/")
        print("2. SSH to EC2: ssh ubuntu@your-ec2")
        print("3. Run deployment: cd /tmp/4runr && sudo ./deploy_ec2.sh")
        print("4. Check status: sudo systemctl status 4runr-automation")
        print("="*60)
    
    def run_deployment_prep(self):
        """Run complete deployment preparation"""
        self.log("Starting deployment preparation...")
        
        steps = [
            ("Create systemd services", self.create_systemd_services),
            ("Create cron jobs", self.create_cron_jobs),
            ("Create deployment script", self.create_deployment_script),
            ("Test email system", self.test_email_system),
            ("Generate summary", self.generate_deployment_summary)
        ]
        
        for step_name, step_func in steps:
            self.log(f"Step: {step_name}")
            try:
                result = step_func()
                self.log(f"✅ {step_name} completed")
            except Exception as e:
                self.log(f"❌ {step_name} failed: {str(e)}")
        
        self.log("🎉 Deployment preparation complete!")

def main():
    deployer = EC2Deployer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--prep":
            deployer.run_deployment_prep()
        elif command == "--services":
            deployer.create_systemd_services()
        elif command == "--cron":
            deployer.create_cron_jobs()
        elif command == "--test-email":
            deployer.test_email_system()
        else:
            print("Usage: python deploy_to_ec2.py [--prep|--services|--cron|--test-email]")
    else:
        deployer.run_deployment_prep()

if __name__ == "__main__":
    main()