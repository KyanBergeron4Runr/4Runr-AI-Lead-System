#!/usr/bin/env python3
"""
Comprehensive Backup and Recovery System for 4Runr Lead System
"""

import os
import sqlite3
import shutil
import json
import gzip
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import logging

class BackupRecoverySystem:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/backup_recovery.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_full_backup(self):
        """Create a complete system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"4runr_full_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        self.logger.info(f"Starting full system backup: {backup_name}")
        
        try:
            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            
            # 1. Backup database
            self._backup_database(backup_path)
            
            # 2. Backup configuration files
            self._backup_configs(backup_path)
            
            # 3. Backup logs (last 30 days)
            self._backup_logs(backup_path)
            
            # 4. Backup code (if needed)
            self._backup_code(backup_path)
            
            # 5. Create backup manifest
            self._create_backup_manifest(backup_path, timestamp)
            
            # 6. Compress backup
            compressed_backup = self._compress_backup(backup_path)
            
            # 7. Cleanup uncompressed backup
            shutil.rmtree(backup_path)
            
            self.logger.info(f"Full backup completed: {compressed_backup}")
            return compressed_backup
            
        except Exception as e:
            self.logger.error(f"Full backup failed: {e}")
            return None
    
    def _backup_database(self, backup_path):
        """Backup the SQLite database"""
        db_backup_dir = backup_path / "database"
        db_backup_dir.mkdir(exist_ok=True)
        
        # Main database
        db_path = Path("data/leads_cache.db")
        if db_path.exists():
            # Create SQL dump
            dump_path = db_backup_dir / "leads_cache_dump.sql"
            with open(dump_path, 'w') as f:
                subprocess.run(['sqlite3', str(db_path), '.dump'], stdout=f)
            
            # Copy database file
            shutil.copy2(db_path, db_backup_dir / "leads_cache.db")
            
            # Backup database logs
            if Path("database_logs").exists():
                shutil.copytree("database_logs", db_backup_dir / "database_logs")
        
        self.logger.info("Database backup completed")
    
    def _backup_configs(self, backup_path):
        """Backup configuration files"""
        config_backup_dir = backup_path / "configs"
        config_backup_dir.mkdir(exist_ok=True)
        
        config_files = [
            ".env",
            "shared/data_cleaner_config/cleaning_rules.yaml",
            "shared/data_cleaner_config/validation_rules.yaml",
            "daily_sync.sh"
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                dest_path = config_backup_dir / Path(config_file).name
                shutil.copy2(config_file, dest_path)
        
        # Backup systemd service files
        service_files = [
            "/etc/systemd/system/4runr-automation.service",
            "/etc/systemd/system/4runr-sync.service",
            "/etc/systemd/system/4runr-enricher.service"
        ]
        
        services_dir = config_backup_dir / "services"
        services_dir.mkdir(exist_ok=True)
        
        for service_file in service_files:
            if Path(service_file).exists():
                dest_path = services_dir / Path(service_file).name
                try:
                    shutil.copy2(service_file, dest_path)
                except PermissionError:
                    self.logger.warning(f"Could not backup {service_file} - permission denied")
        
        self.logger.info("Configuration backup completed")
    
    def _backup_logs(self, backup_path, days=30):
        """Backup recent log files"""
        logs_backup_dir = backup_path / "logs"
        logs_backup_dir.mkdir(exist_ok=True)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Backup application logs
        if Path("logs").exists():
            for log_file in Path("logs").glob("*.log"):
                if log_file.stat().st_mtime > cutoff_date.timestamp():
                    shutil.copy2(log_file, logs_backup_dir)
        
        self.logger.info(f"Logs backup completed (last {days} days)")
    
    def _backup_code(self, backup_path):
        """Backup critical code files"""
        code_backup_dir = backup_path / "code"
        code_backup_dir.mkdir(exist_ok=True)
        
        critical_files = [
            "automation_engine.py",
            "sync_airtable_to_db.py",
            "monitoring_dashboard.py",
            "shared/data_cleaner.py",
            "outreach/google_enricher/app.py"
        ]
        
        for code_file in critical_files:
            if Path(code_file).exists():
                dest_dir = code_backup_dir / Path(code_file).parent
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(code_file, dest_dir / Path(code_file).name)
        
        self.logger.info("Code backup completed")
    
    def _create_backup_manifest(self, backup_path, timestamp):
        """Create backup manifest with metadata"""
        manifest = {
            "backup_timestamp": timestamp,
            "backup_type": "full_system",
            "system_info": {
                "hostname": os.uname().nodename,
                "python_version": subprocess.check_output(['python3', '--version']).decode().strip(),
                "git_commit": self._get_git_commit(),
            },
            "database_info": self._get_database_info(),
            "files_backed_up": self._count_backup_files(backup_path),
            "backup_size_mb": self._get_directory_size(backup_path)
        }
        
        manifest_path = backup_path / "backup_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        self.logger.info("Backup manifest created")
    
    def _get_git_commit(self):
        """Get current git commit hash"""
        try:
            return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        except:
            return "unknown"
    
    def _get_database_info(self):
        """Get database statistics"""
        try:
            conn = sqlite3.connect("data/leads_cache.db")
            cursor = conn.execute("SELECT COUNT(*) FROM leads")
            lead_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_leads": lead_count,
                "total_tables": table_count,
                "database_size_mb": round(Path("data/leads_cache.db").stat().st_size / 1024 / 1024, 2)
            }
        except:
            return {"error": "Could not access database"}
    
    def _count_backup_files(self, backup_path):
        """Count files in backup"""
        return sum(1 for _ in backup_path.rglob("*") if _.is_file())
    
    def _get_directory_size(self, path):
        """Get directory size in MB"""
        total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return round(total_size / 1024 / 1024, 2)
    
    def _compress_backup(self, backup_path):
        """Compress backup directory"""
        compressed_path = f"{backup_path}.tar.gz"
        
        with tarfile.open(compressed_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        return compressed_path
    
    def restore_from_backup(self, backup_file):
        """Restore system from backup"""
        self.logger.info(f"Starting restore from: {backup_file}")
        
        if not Path(backup_file).exists():
            self.logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            # Create restore directory
            restore_dir = Path("restore_temp")
            restore_dir.mkdir(exist_ok=True)
            
            # Extract backup
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(restore_dir)
            
            # Find the backup directory
            backup_contents = list(restore_dir.iterdir())[0]
            
            # Read manifest
            manifest_path = backup_contents / "backup_manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                self.logger.info(f"Restoring backup from {manifest['backup_timestamp']}")
            
            # Restore database
            self._restore_database(backup_contents)
            
            # Restore configurations
            self._restore_configs(backup_contents)
            
            # Cleanup
            shutil.rmtree(restore_dir)
            
            self.logger.info("Restore completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
    
    def _restore_database(self, backup_contents):
        """Restore database from backup"""
        db_backup_dir = backup_contents / "database"
        
        if not db_backup_dir.exists():
            self.logger.warning("No database backup found")
            return
        
        # Stop any running services first
        self.logger.info("Stopping services for database restore...")
        subprocess.run(['sudo', 'systemctl', 'stop', '4runr-automation'], check=False)
        
        # Backup current database
        current_db = Path("data/leads_cache.db")
        if current_db.exists():
            backup_current = f"data/leads_cache_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(current_db, backup_current)
            self.logger.info(f"Current database backed up to: {backup_current}")
        
        # Restore database
        restored_db = db_backup_dir / "leads_cache.db"
        if restored_db.exists():
            shutil.copy2(restored_db, current_db)
            self.logger.info("Database restored")
        
        # Restore database logs
        if (db_backup_dir / "database_logs").exists():
            if Path("database_logs").exists():
                shutil.rmtree("database_logs")
            shutil.copytree(db_backup_dir / "database_logs", "database_logs")
            self.logger.info("Database logs restored")
        
        # Restart services
        subprocess.run(['sudo', 'systemctl', 'start', '4runr-automation'], check=False)
    
    def _restore_configs(self, backup_contents):
        """Restore configuration files"""
        config_backup_dir = backup_contents / "configs"
        
        if not config_backup_dir.exists():
            self.logger.warning("No configuration backup found")
            return
        
        # Restore main config files
        for config_file in config_backup_dir.glob("*"):
            if config_file.is_file() and config_file.name != "services":
                dest_path = Path(config_file.name)
                if dest_path.name == ".env":
                    # Backup current .env
                    if dest_path.exists():
                        backup_env = f".env.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copy2(dest_path, backup_env)
                
                shutil.copy2(config_file, dest_path)
                self.logger.info(f"Restored config: {config_file.name}")
    
    def cleanup_old_backups(self, keep_days=30):
        """Remove old backup files"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        removed_count = 0
        for backup_file in self.backup_dir.glob("4runr_full_backup_*.tar.gz"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                removed_count += 1
                self.logger.info(f"Removed old backup: {backup_file.name}")
        
        self.logger.info(f"Cleanup completed: {removed_count} old backups removed")
    
    def list_backups(self):
        """List available backups"""
        backups = []
        for backup_file in sorted(self.backup_dir.glob("4runr_full_backup_*.tar.gz")):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return backups
    
    def verify_backup(self, backup_file):
        """Verify backup integrity"""
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                # Check if all expected files are present
                members = tar.getnames()
                
                required_files = [
                    "backup_manifest.json",
                    "database/leads_cache.db",
                    "configs/.env"
                ]
                
                missing_files = []
                for required in required_files:
                    if not any(required in member for member in members):
                        missing_files.append(required)
                
                if missing_files:
                    self.logger.error(f"Backup verification failed - missing files: {missing_files}")
                    return False
                
                self.logger.info("Backup verification passed")
                return True
                
        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False

def main():
    """Main backup/recovery interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="4Runr Backup & Recovery System")
    parser.add_argument("action", choices=["backup", "restore", "list", "cleanup", "verify"])
    parser.add_argument("--file", help="Backup file for restore/verify operations")
    parser.add_argument("--keep-days", type=int, default=30, help="Days to keep backups (cleanup)")
    
    args = parser.parse_args()
    
    backup_system = BackupRecoverySystem()
    
    if args.action == "backup":
        backup_file = backup_system.create_full_backup()
        if backup_file:
            print(f"✅ Backup created: {backup_file}")
        else:
            print("❌ Backup failed")
    
    elif args.action == "restore":
        if not args.file:
            print("❌ Please specify backup file with --file")
            return
        
        success = backup_system.restore_from_backup(args.file)
        if success:
            print("✅ Restore completed")
        else:
            print("❌ Restore failed")
    
    elif args.action == "list":
        backups = backup_system.list_backups()
        if backups:
            print("📋 Available backups:")
            for backup in backups:
                print(f"  {backup['filename']} ({backup['size_mb']} MB) - {backup['created']}")
        else:
            print("No backups found")
    
    elif args.action == "cleanup":
        backup_system.cleanup_old_backups(args.keep_days)
        print(f"✅ Cleanup completed (kept last {args.keep_days} days)")
    
    elif args.action == "verify":
        if not args.file:
            print("❌ Please specify backup file with --file")
            return
        
        if backup_system.verify_backup(args.file):
            print("✅ Backup verification passed")
        else:
            print("❌ Backup verification failed")

if __name__ == "__main__":
    main()