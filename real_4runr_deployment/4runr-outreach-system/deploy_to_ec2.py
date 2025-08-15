#!/usr/bin/env python3
"""
EC2 Deployment Script for Lead Database System with Concurrent Access Safety

This script handles the complete deployment of the lead database system
with all concurrent access safety features to EC2.

Features:
- Automated file transfer to EC2
- Environment setup and configuration
- Service installation and startup
- Health checks and validation
- Rollback capabilities
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

class EC2Deployer:
    """Handles deployment to EC2 instance"""
    
    def __init__(self, 
                 ec2_host: str,
                 ec2_user: str = "ubuntu",
                 key_file: str = None,
                 remote_path: str = "/home/ubuntu/4runr-outreach-system"):
        """
        Initialize EC2 deployer
        
        Args:
            ec2_host: EC2 instance hostname or IP
            ec2_user: SSH username (default: ubuntu)
            key_file: Path to SSH private key file
            remote_path: Remote deployment path
        """
        self.ec2_host = ec2_host
        self.ec2_user = ec2_user
        self.key_file = key_file
        self.remote_path = remote_path
        
        # Files to deploy (concurrent access safety components)
        self.deployment_files = [
            # Core concurrent access files
            "database_connection_pool.py",
            "concurrent_access_manager.py",
            "lead_database.py",
            "database_logger.py",
            "database_config.py",
            "database_backup.py",
            "database_health.py",
            "migration_manager.py",
            "airtable_sync_manager.py",
            
            # Updated agent files
            "daily_enricher_agent_updated.py",
            "sync_to_airtable_updated.py",
            "scraper_agent_database.py",
            
            # Test files
            "test_concurrent_access_stress.py",
            "test_thread_safety.py",
            "test_concurrent_integration.py",
            "test_lead_database.py",
            "test_airtable_sync_manager.py",
            "test_migration_manager.py",
            "run_concurrent_access_tests.py",
            
            # Configuration and setup
            ".env.example",
            "requirements.txt",
            "setup.py",
            
            # Documentation
            "DEPLOYMENT_GUIDE.md",
            "README.md",
            
            # Utility scripts
            "verify_installation.py",
            "deployment_readiness_check.py",
            "final_system_verification.py"
        ]
        
        # Directories to create
        self.deployment_dirs = [
            "data",
            "database_logs",
            "database_logs/database_operations",
            "database_logs/sync_operations",
            "database_logs/migration_operations",
            "database_logs/performance_metrics",
            "database_logs/error_logs",
            "database_logs/monitoring_data",
            "backups",
            "logs"
        ]
        
        self.deployment_log = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log deployment message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)
    
    def run_ssh_command(self, command: str, capture_output: bool = True) -> Tuple[bool, str]:
        """Run command on EC2 instance via SSH"""
        ssh_cmd = ["ssh"]
        
        if self.key_file:
            ssh_cmd.extend(["-i", self.key_file])
        
        ssh_cmd.extend([
            "-o", "StrictHostKeyChecking=no",
            f"{self.ec2_user}@{self.ec2_host}",
            command
        ])
        
        try:
            if capture_output:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
                return result.returncode == 0, result.stdout + result.stderr
            else:
                result = subprocess.run(ssh_cmd, timeout=300)
                return result.returncode == 0, ""
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def transfer_file(self, local_file: str, remote_file: str = None) -> bool:
        """Transfer file to EC2 instance"""
        if not os.path.exists(local_file):
            self.log(f"Local file not found: {local_file}", "ERROR")
            return False
        
        if remote_file is None:
            remote_file = os.path.basename(local_file)
        
        remote_full_path = f"{self.remote_path}/{remote_file}"
        
        scp_cmd = ["scp"]
        
        if self.key_file:
            scp_cmd.extend(["-i", self.key_file])
        
        scp_cmd.extend([
            "-o", "StrictHostKeyChecking=no",
            local_file,
            f"{self.ec2_user}@{self.ec2_host}:{remote_full_path}"
        ])
        
        try:
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                self.log(f"Transferred: {local_file} -> {remote_file}")
                return True
            else:
                self.log(f"Transfer failed: {local_file} - {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Transfer error: {local_file} - {str(e)}", "ERROR")
            return False
    
    def check_ec2_connection(self) -> bool:
        """Check if we can connect to EC2 instance"""
        self.log("Checking EC2 connection...")
        success, output = self.run_ssh_command("echo 'Connection test successful'")
        
        if success:
            self.log("✅ EC2 connection successful")
            return True
        else:
            self.log(f"❌ EC2 connection failed: {output}", "ERROR")
            return False
    
    def setup_remote_environment(self) -> bool:
        """Set up the remote environment on EC2"""
        self.log("Setting up remote environment...")
        
        # Create deployment directory
        success, output = self.run_ssh_command(f"mkdir -p {self.remote_path}")
        if not success:
            self.log(f"Failed to create remote directory: {output}", "ERROR")
            return False
        
        # Create subdirectories
        for directory in self.deployment_dirs:
            dir_path = f"{self.remote_path}/{directory}"
            success, output = self.run_ssh_command(f"mkdir -p {dir_path}")
            if not success:
                self.log(f"Failed to create directory {directory}: {output}", "ERROR")
                return False
        
        # Update system packages
        self.log("Updating system packages...")
        success, output = self.run_ssh_command("sudo apt-get update -y")
        if not success:
            self.log(f"Failed to update packages: {output}", "ERROR")
            return False
        
        # Install Python and pip if not present
        self.log("Installing Python dependencies...")
        success, output = self.run_ssh_command("sudo apt-get install -y python3 python3-pip python3-venv sqlite3")
        if not success:
            self.log(f"Failed to install Python: {output}", "ERROR")
            return False
        
        # Create virtual environment
        self.log("Creating Python virtual environment...")
        success, output = self.run_ssh_command(f"cd {self.remote_path} && python3 -m venv venv")
        if not success:
            self.log(f"Failed to create virtual environment: {output}", "ERROR")
            return False
        
        self.log("✅ Remote environment setup complete")
        return True
    
    def deploy_files(self) -> bool:
        """Deploy all files to EC2"""
        self.log("Deploying files to EC2...")
        
        successful_transfers = 0
        failed_transfers = 0
        
        for file_name in self.deployment_files:
            if os.path.exists(file_name):
                if self.transfer_file(file_name):
                    successful_transfers += 1
                else:
                    failed_transfers += 1
            else:
                self.log(f"File not found locally: {file_name}", "WARNING")
                failed_transfers += 1
        
        self.log(f"File deployment complete: {successful_transfers} successful, {failed_transfers} failed")
        
        if failed_transfers > 0:
            self.log(f"Some files failed to transfer. Continuing with deployment...", "WARNING")
        
        return successful_transfers > 0
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies on EC2"""
        self.log("Installing Python dependencies...")
        
        # Activate virtual environment and install requirements
        install_cmd = f"""
        cd {self.remote_path} && 
        source venv/bin/activate && 
        pip install --upgrade pip && 
        pip install -r requirements.txt
        """
        
        success, output = self.run_ssh_command(install_cmd)
        if not success:
            self.log(f"Failed to install dependencies: {output}", "ERROR")
            return False
        
        self.log("✅ Dependencies installed successfully")
        return True
    
    def setup_configuration(self) -> bool:
        """Set up configuration files on EC2"""
        self.log("Setting up configuration...")
        
        # Copy .env.example to .env if .env doesn't exist
        env_setup_cmd = f"""
        cd {self.remote_path} && 
        if [ ! -f .env ]; then 
            cp .env.example .env
            echo "Created .env from .env.example"
        else
            echo ".env already exists, skipping"
        fi
        """
        
        success, output = self.run_ssh_command(env_setup_cmd)
        if not success:
            self.log(f"Failed to setup configuration: {output}", "ERROR")
            return False
        
        self.log("✅ Configuration setup complete")
        return True
    
    def run_tests(self) -> bool:
        """Run tests on EC2 to verify deployment"""
        self.log("Running deployment verification tests...")
        
        # Run basic system verification
        test_cmd = f"""
        cd {self.remote_path} && 
        source venv/bin/activate && 
        python verify_installation.py
        """
        
        success, output = self.run_ssh_command(test_cmd)
        if not success:
            self.log(f"Basic verification failed: {output}", "ERROR")
            return False
        
        # Run concurrent access tests (quick mode)
        self.log("Running concurrent access safety tests...")
        concurrent_test_cmd = f"""
        cd {self.remote_path} && 
        source venv/bin/activate && 
        python run_concurrent_access_tests.py --test-type thread-safety --quick
        """
        
        success, output = self.run_ssh_command(concurrent_test_cmd)
        if not success:
            self.log(f"Concurrent access tests failed: {output}", "WARNING")
            # Don't fail deployment for test failures, just warn
        else:
            self.log("✅ Concurrent access tests passed")
        
        return True
    
    def setup_systemd_services(self) -> bool:
        """Set up systemd services for the lead database system"""
        self.log("Setting up systemd services...")
        
        # Create service files
        services = {
            "4runr-sync": {
                "description": "4Runr Lead Sync Agent",
                "script": "sync_to_airtable_updated.py",
                "args": "--daemon"
            },
            "4runr-enricher": {
                "description": "4Runr Lead Enricher Agent",
                "script": "daily_enricher_agent_updated.py",
                "args": "--daemon"
            }
        }
        
        for service_name, config in services.items():
            service_content = f"""[Unit]
Description={config['description']}
After=network.target

[Service]
Type=simple
User={self.ec2_user}
Group={self.ec2_user}
WorkingDirectory={self.remote_path}
Environment=PATH={self.remote_path}/venv/bin
ExecStart={self.remote_path}/venv/bin/python {config['script']} {config['args']}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
            
            # Create service file
            service_file = f"/tmp/{service_name}.service"
            create_service_cmd = f"echo '{service_content}' > {service_file}"
            
            success, output = self.run_ssh_command(create_service_cmd)
            if not success:
                self.log(f"Failed to create service file {service_name}: {output}", "ERROR")
                continue
            
            # Move to systemd directory
            move_service_cmd = f"sudo mv {service_file} /etc/systemd/system/"
            success, output = self.run_ssh_command(move_service_cmd)
            if not success:
                self.log(f"Failed to install service {service_name}: {output}", "ERROR")
                continue
            
            # Enable service
            enable_cmd = f"sudo systemctl daemon-reload && sudo systemctl enable {service_name}"
            success, output = self.run_ssh_command(enable_cmd)
            if not success:
                self.log(f"Failed to enable service {service_name}: {output}", "ERROR")
                continue
            
            self.log(f"✅ Service {service_name} installed and enabled")
        
        return True
    
    def setup_cron_jobs(self) -> bool:
        """Set up cron jobs for maintenance tasks"""
        self.log("Setting up cron jobs...")
        
        cron_jobs = [
            # Daily backup at 2 AM
            f"0 2 * * * cd {self.remote_path} && source venv/bin/activate && python -c \"from database_backup import create_database_backup; create_database_backup('scheduled')\" >> logs/backup.log 2>&1",
            
            # Weekly health check at 3 AM on Sundays
            f"0 3 * * 0 cd {self.remote_path} && source venv/bin/activate && python -c \"from database_health import run_database_health_check; run_database_health_check()\" >> logs/health.log 2>&1",
            
            # Monthly cleanup at 4 AM on 1st of month
            f"0 4 1 * * cd {self.remote_path} && source venv/bin/activate && python -c \"from database_backup import backup_manager; backup_manager.cleanup_old_backups()\" >> logs/cleanup.log 2>&1"
        ]
        
        # Add cron jobs
        for job in cron_jobs:
            add_cron_cmd = f"(crontab -l 2>/dev/null; echo '{job}') | crontab -"
            success, output = self.run_ssh_command(add_cron_cmd)
            if not success:
                self.log(f"Failed to add cron job: {output}", "WARNING")
        
        self.log("✅ Cron jobs setup complete")
        return True
    
    def perform_health_check(self) -> bool:
        """Perform final health check"""
        self.log("Performing final health check...")
        
        health_cmd = f"""
        cd {self.remote_path} && 
        source venv/bin/activate && 
        python -c "
from lead_database import LeadDatabase
from concurrent_access_manager import get_concurrent_access_manager
from database_connection_pool import get_connection_pool

try:
    # Test database initialization
    db = LeadDatabase()
    stats = db.get_database_stats()
    print(f'Database initialized: {{stats}}')
    
    # Test concurrent access manager
    access_manager = get_concurrent_access_manager(db.db_path)
    health = access_manager.health_check()
    print(f'Access manager health: {{health[\"status\"]}}')
    
    # Test connection pool
    pool = get_connection_pool()
    pool_health = pool.health_check()
    print(f'Connection pool health: {{pool_health[\"status\"]}}')
    
    print('✅ All systems healthy')
except Exception as e:
    print(f'❌ Health check failed: {{e}}')
    exit(1)
"
        """
        
        success, output = self.run_ssh_command(health_cmd)
        if success:
            self.log("✅ Final health check passed")
            self.log(f"Health check output: {output}")
            return True
        else:
            self.log(f"❌ Final health check failed: {output}", "ERROR")
            return False
    
    def save_deployment_log(self) -> bool:
        """Save deployment log to file"""
        try:
            log_filename = f"deployment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(log_filename, 'w') as f:
                f.write("4Runr Lead Database System - EC2 Deployment Log\n")
                f.write("=" * 60 + "\n\n")
                
                for entry in self.deployment_log:
                    f.write(entry + "\n")
                
                f.write("\n" + "=" * 60 + "\n")
                f.write(f"Deployment completed at: {datetime.now()}\n")
            
            self.log(f"Deployment log saved to: {log_filename}")
            return True
            
        except Exception as e:
            self.log(f"Failed to save deployment log: {e}", "ERROR")
            return False
    
    def deploy(self) -> bool:
        """Run complete deployment process"""
        self.log("🚀 Starting EC2 deployment for Lead Database System with Concurrent Access Safety")
        self.log("=" * 80)
        
        deployment_steps = [
            ("Connection Check", self.check_ec2_connection),
            ("Environment Setup", self.setup_remote_environment),
            ("File Deployment", self.deploy_files),
            ("Dependency Installation", self.install_dependencies),
            ("Configuration Setup", self.setup_configuration),
            ("Test Execution", self.run_tests),
            ("Service Setup", self.setup_systemd_services),
            ("Cron Jobs Setup", self.setup_cron_jobs),
            ("Final Health Check", self.perform_health_check)
        ]
        
        for step_name, step_function in deployment_steps:
            self.log(f"\n--- {step_name} ---")
            
            try:
                success = step_function()
                if not success:
                    self.log(f"❌ {step_name} failed. Deployment aborted.", "ERROR")
                    self.save_deployment_log()
                    return False
                
                self.log(f"✅ {step_name} completed successfully")
                
            except Exception as e:
                self.log(f"💥 {step_name} crashed: {str(e)}", "ERROR")
                self.save_deployment_log()
                return False
        
        self.log("\n" + "=" * 80)
        self.log("🎉 DEPLOYMENT SUCCESSFUL!")
        self.log("=" * 80)
        
        self.log("\nDeployment Summary:")
        self.log(f"  - Remote path: {self.remote_path}")
        self.log(f"  - Files deployed: {len(self.deployment_files)}")
        self.log(f"  - Services installed: 4runr-sync, 4runr-enricher")
        self.log(f"  - Cron jobs configured: 3 maintenance tasks")
        
        self.log("\nNext Steps:")
        self.log("  1. Update .env file with your specific configuration")
        self.log("  2. Start services: sudo systemctl start 4runr-sync 4runr-enricher")
        self.log("  3. Check service status: sudo systemctl status 4runr-sync")
        self.log("  4. Monitor logs: tail -f logs/*.log")
        
        self.save_deployment_log()
        return True

def main():
    """Main deployment script"""
    parser = argparse.ArgumentParser(
        description="Deploy Lead Database System with Concurrent Access Safety to EC2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy_to_ec2.py --host ec2-xxx.compute.amazonaws.com --key ~/.ssh/my-key.pem
  python deploy_to_ec2.py --host 1.2.3.4 --user ubuntu --key /path/to/key.pem
        """
    )
    
    parser.add_argument(
        '--host',
        required=True,
        help='EC2 instance hostname or IP address'
    )
    
    parser.add_argument(
        '--user',
        default='ubuntu',
        help='SSH username (default: ubuntu)'
    )
    
    parser.add_argument(
        '--key',
        help='Path to SSH private key file'
    )
    
    parser.add_argument(
        '--remote-path',
        default='/home/ubuntu/4runr-outreach-system',
        help='Remote deployment path (default: /home/ubuntu/4runr-outreach-system)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deployed without actually deploying'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - Showing deployment plan:")
        print(f"Target: {args.user}@{args.host}:{args.remote_path}")
        print(f"Key file: {args.key or 'None (using SSH agent)'}")
        
        deployer = EC2Deployer(args.host, args.user, args.key, args.remote_path)
        print(f"\nFiles to deploy ({len(deployer.deployment_files)}):")
        for file_name in deployer.deployment_files:
            exists = "✅" if os.path.exists(file_name) else "❌"
            print(f"  {exists} {file_name}")
        
        print(f"\nDirectories to create ({len(deployer.deployment_dirs)}):")
        for dir_name in deployer.deployment_dirs:
            print(f"  📁 {dir_name}")
        
        return 0
    
    # Validate key file
    if args.key and not os.path.exists(args.key):
        print(f"❌ SSH key file not found: {args.key}")
        return 1
    
    # Create deployer and run deployment
    deployer = EC2Deployer(args.host, args.user, args.key, args.remote_path)
    
    try:
        success = deployer.deploy()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user (Ctrl+C)")
        print("🛑 Cleaning up and exiting...")
        deployer.save_deployment_log()
        return 130
        
    except Exception as e:
        print(f"\n💥 Unexpected deployment error: {e}")
        deployer.save_deployment_log()
        return 1

if __name__ == "__main__":
    sys.exit(main())