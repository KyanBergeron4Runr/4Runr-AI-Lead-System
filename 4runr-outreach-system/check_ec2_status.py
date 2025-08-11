#!/usr/bin/env python3
"""
EC2 Status Checker for Lead Database System

This script checks what's currently deployed on the EC2 instance
and provides a status report.
"""

import subprocess
import sys
import argparse
from typing import Tuple, Dict, List

class EC2StatusChecker:
    """Check status of deployment on EC2"""
    
    def __init__(self, ec2_host: str, ec2_user: str = "ubuntu", key_file: str = None):
        self.ec2_host = ec2_host
        self.ec2_user = ec2_user
        self.key_file = key_file
        self.remote_path = "/home/ubuntu/4runr-outreach-system"
    
    def run_ssh_command(self, command: str) -> Tuple[bool, str]:
        """Run command on EC2 instance via SSH"""
        ssh_cmd = ["ssh"]
        
        if self.key_file:
            ssh_cmd.extend(["-i", self.key_file])
        
        ssh_cmd.extend([
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            f"{self.ec2_user}@{self.ec2_host}",
            command
        ])
        
        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def check_connection(self) -> bool:
        """Check if we can connect to EC2"""
        print("🔍 Checking EC2 connection...")
        success, output = self.run_ssh_command("echo 'Connected successfully'")
        
        if success:
            print("✅ EC2 connection successful")
            return True
        else:
            print(f"❌ EC2 connection failed: {output}")
            return False
    
    def check_directory_structure(self) -> Dict[str, bool]:
        """Check if deployment directories exist"""
        print("\n📁 Checking directory structure...")
        
        directories = [
            "4runr-outreach-system",
            "4runr-outreach-system/data",
            "4runr-outreach-system/database_logs",
            "4runr-outreach-system/backups",
            "4runr-outreach-system/logs",
            "4runr-outreach-system/venv"
        ]
        
        results = {}
        for directory in directories:
            success, _ = self.run_ssh_command(f"test -d /home/ubuntu/{directory}")
            results[directory] = success
            status = "✅" if success else "❌"
            print(f"  {status} {directory}")
        
        return results
    
    def check_deployed_files(self) -> Dict[str, bool]:
        """Check which files are deployed"""
        print("\n📄 Checking deployed files...")
        
        key_files = [
            "lead_database.py",
            "database_connection_pool.py",
            "concurrent_access_manager.py",
            "database_logger.py",
            "database_config.py",
            "database_backup.py",
            "database_health.py",
            "migration_manager.py",
            "airtable_sync_manager.py",
            "daily_enricher_agent_updated.py",
            "sync_to_airtable_updated.py",
            "scraper_agent_database.py",
            "requirements.txt",
            ".env"
        ]
        
        results = {}
        for file_name in key_files:
            success, _ = self.run_ssh_command(f"test -f {self.remote_path}/{file_name}")
            results[file_name] = success
            status = "✅" if success else "❌"
            print(f"  {status} {file_name}")
        
        return results
    
    def check_python_environment(self) -> Dict[str, str]:
        """Check Python environment status"""
        print("\n🐍 Checking Python environment...")
        
        checks = {}
        
        # Check Python version
        success, output = self.run_ssh_command("python3 --version")
        checks["python_version"] = output if success else "Not found"
        print(f"  Python: {checks['python_version']}")
        
        # Check virtual environment
        success, output = self.run_ssh_command(f"test -f {self.remote_path}/venv/bin/python")
        checks["venv_exists"] = "✅ Exists" if success else "❌ Missing"
        print(f"  Virtual Environment: {checks['venv_exists']}")
        
        # Check if requirements are installed
        success, output = self.run_ssh_command(f"cd {self.remote_path} && source venv/bin/activate && pip list | grep -E '(sqlite|psutil|requests)'")
        checks["packages_installed"] = "✅ Some packages found" if success and output else "❌ No packages found"
        print(f"  Packages: {checks['packages_installed']}")
        
        return checks
    
    def check_services(self) -> Dict[str, str]:
        """Check systemd services status"""
        print("\n🔧 Checking systemd services...")
        
        services = ["4runr-sync", "4runr-enricher"]
        results = {}
        
        for service in services:
            # Check if service exists
            success, _ = self.run_ssh_command(f"systemctl list-unit-files | grep {service}")
            if success:
                # Check service status
                success, output = self.run_ssh_command(f"systemctl is-active {service}")
                status = output if success else "inactive"
                results[service] = f"✅ {status}" if status == "active" else f"⚠️ {status}"
            else:
                results[service] = "❌ Not installed"
            
            print(f"  {service}: {results[service]}")
        
        return results
    
    def check_database_status(self) -> Dict[str, str]:
        """Check database status"""
        print("\n🗄️ Checking database status...")
        
        results = {}
        
        # Check if database file exists
        success, _ = self.run_ssh_command(f"test -f {self.remote_path}/data/leads_cache.db")
        results["database_file"] = "✅ Exists" if success else "❌ Missing"
        print(f"  Database file: {results['database_file']}")
        
        # Try to get database stats
        db_check_cmd = f"""
        cd {self.remote_path} && 
        source venv/bin/activate && 
        python -c "
try:
    from lead_database import LeadDatabase
    db = LeadDatabase()
    stats = db.get_database_stats()
    print(f'Leads: {{stats.get(\"total_leads\", 0)}}')
except Exception as e:
    print(f'Error: {{e}}')
"
        """
        
        success, output = self.run_ssh_command(db_check_cmd)
        if success and "Error:" not in output:
            results["database_accessible"] = f"✅ {output}"
        else:
            results["database_accessible"] = f"❌ {output}"
        
        print(f"  Database access: {results['database_accessible']}")
        
        return results
    
    def check_logs(self) -> Dict[str, str]:
        """Check log files"""
        print("\n📋 Checking log files...")
        
        log_locations = [
            "logs",
            "database_logs",
            "/var/log/syslog"
        ]
        
        results = {}
        
        for location in log_locations:
            if location.startswith("/"):
                path = location
            else:
                path = f"{self.remote_path}/{location}"
            
            success, output = self.run_ssh_command(f"ls -la {path} 2>/dev/null | wc -l")
            if success and output and int(output) > 1:
                results[location] = f"✅ {int(output)-1} files"
            else:
                results[location] = "❌ Empty or missing"
            
            print(f"  {location}: {results[location]}")
        
        return results
    
    def check_cron_jobs(self) -> List[str]:
        """Check cron jobs"""
        print("\n⏰ Checking cron jobs...")
        
        success, output = self.run_ssh_command("crontab -l 2>/dev/null")
        
        if success and output:
            jobs = [line.strip() for line in output.split('\n') if line.strip() and not line.startswith('#')]
            for job in jobs:
                print(f"  ✅ {job}")
            return jobs
        else:
            print("  ❌ No cron jobs found")
            return []
    
    def run_health_check(self) -> bool:
        """Run system health check"""
        print("\n🏥 Running system health check...")
        
        health_cmd = f"""
        cd {self.remote_path} && 
        source venv/bin/activate && 
        python -c "
try:
    from lead_database import LeadDatabase
    from database_connection_pool import get_connection_pool
    
    # Test database
    db = LeadDatabase()
    print('✅ Database initialized')
    
    # Test connection pool
    pool = get_connection_pool(db.db_path)
    health = pool.health_check()
    print(f'✅ Connection pool: {{health[\"status\"]}}')
    
    print('✅ System health check passed')
except Exception as e:
    print(f'❌ Health check failed: {{e}}')
"
        """
        
        success, output = self.run_ssh_command(health_cmd)
        print(f"  {output}")
        
        return success and "❌" not in output
    
    def generate_status_report(self) -> Dict:
        """Generate comprehensive status report"""
        print("🔍 Generating comprehensive status report...")
        print("=" * 60)
        
        if not self.check_connection():
            return {"status": "connection_failed"}
        
        report = {
            "connection": "✅ Connected",
            "directories": self.check_directory_structure(),
            "files": self.check_deployed_files(),
            "python_env": self.check_python_environment(),
            "services": self.check_services(),
            "database": self.check_database_status(),
            "logs": self.check_logs(),
            "cron_jobs": self.check_cron_jobs(),
            "health_check": self.run_health_check()
        }
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT STATUS SUMMARY")
        print("=" * 60)
        
        # Calculate deployment completeness
        file_count = sum(1 for exists in report["files"].values() if exists)
        total_files = len(report["files"])
        dir_count = sum(1 for exists in report["directories"].values() if exists)
        total_dirs = len(report["directories"])
        
        print(f"📁 Directories: {dir_count}/{total_dirs} present")
        print(f"📄 Key files: {file_count}/{total_files} present")
        print(f"🐍 Python environment: {report['python_env']['venv_exists']}")
        print(f"🔧 Services: {len([s for s in report['services'].values() if '✅' in s])}/2 active")
        print(f"🗄️ Database: {report['database']['database_accessible']}")
        print(f"🏥 Health check: {'✅ Passed' if report['health_check'] else '❌ Failed'}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if file_count < total_files:
            missing_files = [f for f, exists in report["files"].items() if not exists]
            print(f"  - Deploy missing files: {', '.join(missing_files[:3])}{'...' if len(missing_files) > 3 else ''}")
        
        if "❌" in report['python_env']['venv_exists']:
            print("  - Set up Python virtual environment")
        
        if not any("✅" in s for s in report['services'].values()):
            print("  - Install and start systemd services")
        
        if "❌" in report['database']['database_accessible']:
            print("  - Initialize database system")
        
        if not report['health_check']:
            print("  - Run deployment script to fix issues")
        
        if file_count == total_files and report['health_check']:
            print("  ✅ System appears to be fully deployed and healthy!")
        
        return report

def main():
    """Main status checker"""
    parser = argparse.ArgumentParser(
        description="Check deployment status on EC2 instance"
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
    
    args = parser.parse_args()
    
    # Create status checker and run
    checker = EC2StatusChecker(args.host, args.user, args.key)
    
    try:
        report = checker.generate_status_report()
        return 0 if report.get("health_check", False) else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Status check interrupted by user (Ctrl+C)")
        return 130
        
    except Exception as e:
        print(f"\n💥 Status check error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())