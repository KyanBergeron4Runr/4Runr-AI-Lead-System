"""
Local Database Manager for the 4Runr Email Engager Upgrade.

Handles local database operations for engagement tracking, including schema
management, data synchronization, and engagement history logging.
"""

import os
import sqlite3
import json
import datetime
import shutil
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

from shared.logging_utils import get_logger


class LocalDatabaseManager:
    """Handles local database operations for engagement tracking."""
    
    def __init__(self, db_path: str = "data/leads_cache.db"):
        """
        Initialize the Local Database Manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Ensure we use the correct database path relative to the script location
        if not os.path.isabs(db_path):
            script_dir = Path(__file__).parent.parent  # Go up to 4runr-outreach-system
            self.db_path = str(script_dir / db_path)
        else:
            self.db_path = db_path
            
        self.logger = get_logger('engager')
        
        # Ensure data directory exists
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up backup directory
        self.backup_dir = db_file.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize database schema
        self._ensure_schema()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with automatic cleanup.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.log_error(e, {'action': 'database_connection', 'db_path': self.db_path})
            raise
        finally:
            if conn:
                conn.close()
    
    def _ensure_schema(self) -> None:
        """Ensure database has required engagement tracking fields and tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create leads table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leads (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        email TEXT,
                        company TEXT,
                        company_website TEXT,
                        engagement_stage TEXT DEFAULT '1st degree',
                        last_contacted TIMESTAMP,
                        engagement_history TEXT,
                        follow_up_stage TEXT,
                        response_status TEXT DEFAULT 'No Response',
                        eligible_for_reengagement BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create engagement_tracking table for detailed history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS engagement_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        lead_id TEXT NOT NULL,
                        engagement_level TEXT NOT NULL,
                        previous_level TEXT,
                        contacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_sent TEXT,
                        company_summary TEXT,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        airtable_synced BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (lead_id) REFERENCES leads(id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_leads_engagement_stage 
                    ON leads(engagement_stage)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_leads_last_contacted 
                    ON leads(last_contacted)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_engagement_tracking_lead_id 
                    ON engagement_tracking(lead_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_engagement_tracking_contacted_at 
                    ON engagement_tracking(contacted_at)
                """)
                
                # Check if we need to add new columns to existing leads table
                self._migrate_schema_if_needed(cursor)
                
                conn.commit()
                
                self.logger.log_module_activity('engager', 'system', 'success', {
                    'message': 'Database schema ensured successfully',
                    'db_path': self.db_path
                })
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'ensure_schema', 'db_path': self.db_path})
            raise
    
    def _migrate_schema_if_needed(self, cursor: sqlite3.Cursor) -> None:
        """
        Migrate existing schema to add new engagement tracking fields.
        
        Args:
            cursor: Database cursor
        """
        try:
            # Get existing columns in leads table
            cursor.execute("PRAGMA table_info(leads)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns
            required_columns = {
                'engagement_stage': 'TEXT DEFAULT "1st degree"',
                'last_contacted': 'TIMESTAMP',
                'engagement_history': 'TEXT',
                'follow_up_stage': 'TEXT',
                'response_status': 'TEXT DEFAULT "No Response"',
                'eligible_for_reengagement': 'BOOLEAN DEFAULT FALSE'
            }
            
            for column_name, column_def in required_columns.items():
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE leads ADD COLUMN {column_name} {column_def}")
                    self.logger.log_module_activity('engager', 'system', 'info', {
                        'message': f'Added column {column_name} to leads table'
                    })
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'migrate_schema'})
            # Don't raise - schema migration failures shouldn't stop the system
    
    def update_engagement_data(self, lead_id: str, engagement_data: Dict[str, Any]) -> bool:
        """
        Update local database with engagement information.
        
        Args:
            lead_id: Lead identifier
            engagement_data: Dictionary with engagement information
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Update or insert lead record with complete data
                cursor.execute("""
                    INSERT OR REPLACE INTO leads (
                        id, name, email, company, company_website,
                        engagement_stage, last_contacted, engagement_history, 
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 
                             COALESCE((SELECT created_at FROM leads WHERE id = ?), ?), ?)
                """, (
                    lead_id,
                    engagement_data.get('name', ''),
                    engagement_data.get('email', ''),
                    engagement_data.get('company', ''),
                    engagement_data.get('company_website', ''),
                    engagement_data.get('engagement_stage', '1st degree'),
                    engagement_data.get('last_contacted'),
                    engagement_data.get('engagement_history'),
                    lead_id,  # For COALESCE check
                    datetime.datetime.now().isoformat(),  # Default created_at
                    datetime.datetime.now().isoformat()   # updated_at
                ))
                
                # Insert detailed engagement tracking record
                cursor.execute("""
                    INSERT INTO engagement_tracking (
                        lead_id, engagement_level, previous_level, contacted_at,
                        message_sent, company_summary, success, error_message, airtable_synced
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead_id,
                    engagement_data.get('engagement_stage'),
                    engagement_data.get('previous_stage'),
                    engagement_data.get('last_contacted'),
                    engagement_data.get('message_sent', ''),
                    engagement_data.get('company_summary', ''),
                    engagement_data.get('success', True),
                    engagement_data.get('error_message'),
                    engagement_data.get('airtable_synced', False)
                ))
                
                # Commit transaction
                conn.commit()
                
                self.logger.log_module_activity('engager', lead_id, 'success', {
                    'message': 'Updated local database with complete lead data',
                    'name': engagement_data.get('name', 'Unknown'),
                    'email': engagement_data.get('email', 'No email'),
                    'company': engagement_data.get('company', 'Unknown'),
                    'engagement_stage': engagement_data.get('engagement_stage'),
                    'success': engagement_data.get('success', True)
                })
                
                return True
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'update_engagement_data',
                'lead_id': lead_id,
                'engagement_data': engagement_data
            })
            return False
    
    def get_engagement_history(self, lead_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve engagement history for a lead.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            List of engagement history records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM engagement_tracking 
                    WHERE lead_id = ? 
                    ORDER BY contacted_at DESC
                """, (lead_id,))
                
                rows = cursor.fetchall()
                
                history = []
                for row in rows:
                    history.append({
                        'id': row['id'],
                        'lead_id': row['lead_id'],
                        'engagement_level': row['engagement_level'],
                        'previous_level': row['previous_level'],
                        'contacted_at': row['contacted_at'],
                        'message_sent': row['message_sent'],
                        'company_summary': row['company_summary'],
                        'success': bool(row['success']),
                        'error_message': row['error_message'],
                        'airtable_synced': bool(row['airtable_synced']),
                        'created_at': row['created_at']
                    })
                
                return history
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'get_engagement_history',
                'lead_id': lead_id
            })
            return []
    
    def get_lead_engagement_status(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current engagement status for a lead.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            Dictionary with current engagement status or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM leads WHERE id = ?
                """, (lead_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row['id'],
                        'name': row['name'],
                        'email': row['email'],
                        'company': row['company'],
                        'company_website': row['company_website'],
                        'engagement_stage': row['engagement_stage'],
                        'last_contacted': row['last_contacted'],
                        'engagement_history': row['engagement_history'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                
                return None
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'get_lead_engagement_status',
                'lead_id': lead_id
            })
            return None
    
    def get_engagement_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive engagement statistics from local database.
        
        Returns:
            Dictionary with engagement statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total leads
                cursor.execute("SELECT COUNT(*) FROM leads")
                stats['total_leads'] = cursor.fetchone()[0]
                
                # Leads by engagement stage
                cursor.execute("""
                    SELECT engagement_stage, COUNT(*) 
                    FROM leads 
                    GROUP BY engagement_stage
                """)
                stats['by_stage'] = dict(cursor.fetchall())
                
                # Recent engagement activity (last 7 days)
                cursor.execute("""
                    SELECT COUNT(*) FROM engagement_tracking 
                    WHERE contacted_at >= datetime('now', '-7 days')
                """)
                stats['recent_engagements'] = cursor.fetchone()[0]
                
                # Success rate
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                        COUNT(*) as total
                    FROM engagement_tracking
                """)
                result = cursor.fetchone()
                if result['total'] > 0:
                    stats['success_rate'] = result['successful'] / result['total']
                else:
                    stats['success_rate'] = 0.0
                
                # Airtable sync status
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN airtable_synced = 1 THEN 1 ELSE 0 END) as synced,
                        COUNT(*) as total
                    FROM engagement_tracking
                """)
                result = cursor.fetchone()
                stats['airtable_sync_rate'] = result['synced'] / result['total'] if result['total'] > 0 else 0.0
                
                return stats
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_engagement_statistics'})
            return {'error': str(e)}
    
    def cleanup_old_records(self, days_to_keep: int = 365) -> int:
        """
        Clean up old engagement tracking records.
        
        Args:
            days_to_keep: Number of days of records to keep
            
        Returns:
            Number of records deleted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM engagement_tracking 
                    WHERE contacted_at < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.log_module_activity('engager', 'system', 'info', {
                    'message': f'Cleaned up {deleted_count} old engagement records',
                    'days_to_keep': days_to_keep
                })
                
                return deleted_count
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'cleanup_old_records',
                'days_to_keep': days_to_keep
            })
            return 0
    
    def export_engagement_data(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Export engagement data for analysis.
        
        Args:
            start_date: Start date in ISO format (optional)
            end_date: End date in ISO format (optional)
            
        Returns:
            List of engagement records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        et.*,
                        l.name,
                        l.email,
                        l.company,
                        l.company_website
                    FROM engagement_tracking et
                    LEFT JOIN leads l ON et.lead_id = l.id
                """
                
                params = []
                conditions = []
                
                if start_date:
                    conditions.append("et.contacted_at >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("et.contacted_at <= ?")
                    params.append(end_date)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY et.contacted_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                export_data = []
                for row in rows:
                    export_data.append({
                        'tracking_id': row['id'],
                        'lead_id': row['lead_id'],
                        'name': row['name'],
                        'email': row['email'],
                        'company': row['company'],
                        'company_website': row['company_website'],
                        'engagement_level': row['engagement_level'],
                        'previous_level': row['previous_level'],
                        'contacted_at': row['contacted_at'],
                        'message_sent': row['message_sent'],
                        'company_summary': row['company_summary'],
                        'success': bool(row['success']),
                        'error_message': row['error_message'],
                        'airtable_synced': bool(row['airtable_synced']),
                        'created_at': row['created_at']
                    })
                
                return export_data
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'export_engagement_data',
                'start_date': start_date,
                'end_date': end_date
            })
            return []
    
    def create_engagement_tables(self) -> bool:
        """
        Create engagement tracking tables if they don't exist.
        
        Returns:
            True if tables created successfully, False otherwise
        """
        try:
            self._ensure_schema()
            return True
        except Exception as e:
            self.logger.log_error(e, {'action': 'create_engagement_tables'})
            return False
    
    def upsert_lead(self, lead_data: Dict[str, Any]) -> bool:
        """
        Insert or update a lead with complete data, preventing duplicates.
        
        Args:
            lead_data: Complete lead information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                lead_id = lead_data.get('id') or lead_data.get('airtable_id')
                email = lead_data.get('email', '')
                
                # Check for existing lead by email to prevent duplicates
                if email:
                    cursor.execute("SELECT id FROM leads WHERE email = ? AND id != ?", (email, lead_id or ''))
                    existing = cursor.fetchone()
                    if existing:
                        self.logger.log_module_activity('engager', lead_id or 'unknown', 'warning', {
                            'message': f'Duplicate email found, updating existing lead: {existing["id"]}',
                            'email': email
                        })
                        lead_id = existing['id']
                
                # Insert or update with complete data
                cursor.execute("""
                    INSERT OR REPLACE INTO leads (
                        id, name, email, company, company_website,
                        engagement_stage, last_contacted, engagement_history,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?,
                             COALESCE((SELECT created_at FROM leads WHERE id = ?), ?), ?)
                """, (
                    lead_id,
                    lead_data.get('name') or lead_data.get('full_name', ''),
                    email,
                    lead_data.get('company', ''),
                    lead_data.get('website') or lead_data.get('company_website', ''),
                    lead_data.get('engagement_stage', '1st degree'),
                    lead_data.get('last_contacted'),
                    lead_data.get('engagement_history'),
                    lead_id,  # For COALESCE check
                    datetime.datetime.now().isoformat(),  # Default created_at
                    datetime.datetime.now().isoformat()   # updated_at
                ))
                
                conn.commit()
                
                self.logger.log_module_activity('engager', lead_id, 'success', {
                    'message': 'Lead upserted successfully',
                    'name': lead_data.get('name') or lead_data.get('full_name', ''),
                    'email': email,
                    'company': lead_data.get('company', ''),
                    'action': 'upsert'
                })
                
                return True
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'upsert_lead',
                'lead_data': lead_data
            })
            return False
    
    def test_database_connection(self) -> bool:
        """
        Test database connection and basic operations.
        
        Returns:
            True if database is working correctly, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Test basic query
                cursor.execute("SELECT COUNT(*) FROM leads")
                count = cursor.fetchone()[0]
                
                # Test write operation
                test_id = f"test_{datetime.datetime.now().isoformat()}"
                cursor.execute("""
                    INSERT INTO leads (id, name, email, company) 
                    VALUES (?, ?, ?, ?)
                """, (test_id, "Test Lead", "test@example.com", "Test Company"))
                
                # Clean up test record
                cursor.execute("DELETE FROM leads WHERE id = ?", (test_id,))
                conn.commit()
                
                self.logger.log_module_activity('engager', 'system', 'success', {
                    'message': 'Database connection test successful',
                    'total_leads': count
                })
                
                return True
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'test_database_connection'})
            return False
    
    def create_database_backup(self) -> bool:
        """
        Create a timestamped backup of the leads database.
        
        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            # Check if database file exists and has content
            db_file = Path(self.db_path)
            if not db_file.exists():
                self.logger.log_module_activity('engager', 'system', 'warning', {
                    'message': 'Database file does not exist, skipping backup',
                    'db_path': self.db_path
                })
                return False
            
            # Check file size (should be > 0)
            if db_file.stat().st_size == 0:
                self.logger.log_module_activity('engager', 'system', 'warning', {
                    'message': 'Database file is empty, skipping backup',
                    'db_path': self.db_path
                })
                return False
            
            # Create timestamped backup filename
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"leads_cache_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Create backup using shutil.copy2 to preserve metadata
            shutil.copy2(self.db_path, backup_path)
            
            # Verify backup integrity
            if not self._verify_backup_integrity(backup_path):
                backup_path.unlink()  # Delete corrupted backup
                raise Exception("Backup integrity verification failed")
            
            # Clean up old backups (keep only latest 10)
            self._cleanup_old_backups()
            
            backup_size = backup_path.stat().st_size
            
            self.logger.log_module_activity('engager', 'system', 'success', {
                'message': 'Database backup created successfully',
                'backup_path': str(backup_path),
                'backup_size_bytes': backup_size,
                'original_size_bytes': db_file.stat().st_size
            })
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'create_database_backup',
                'db_path': self.db_path,
                'backup_dir': str(self.backup_dir)
            })
            return False
    
    def _verify_backup_integrity(self, backup_path: Path) -> bool:
        """
        Verify that a backup file is a valid SQLite database.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if backup is valid, False otherwise
        """
        try:
            # Check file size
            if backup_path.stat().st_size == 0:
                return False
            
            # Try to open and query the backup database
            with sqlite3.connect(str(backup_path)) as conn:
                cursor = conn.cursor()
                
                # Test basic query
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                # Verify expected tables exist
                table_names = [table[0] for table in tables]
                expected_tables = ['leads', 'engagement_tracking']
                
                for expected_table in expected_tables:
                    if expected_table not in table_names:
                        self.logger.log_module_activity('engager', 'system', 'warning', {
                            'message': f'Expected table {expected_table} not found in backup',
                            'backup_path': str(backup_path),
                            'found_tables': table_names
                        })
                        return False
                
                # Test a simple query on each table
                for table in expected_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    cursor.fetchone()
                
                return True
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'verify_backup_integrity',
                'backup_path': str(backup_path)
            })
            return False
    
    def _cleanup_old_backups(self, max_backups: int = 10) -> None:
        """
        Clean up old backup files, keeping only the most recent ones.
        
        Args:
            max_backups: Maximum number of backups to keep
        """
        try:
            # Get all backup files
            backup_pattern = str(self.backup_dir / "leads_cache_*.db")
            backup_files = glob.glob(backup_pattern)
            
            if len(backup_files) <= max_backups:
                return  # No cleanup needed
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Delete old backups
            files_to_delete = backup_files[max_backups:]
            deleted_count = 0
            
            for old_backup in files_to_delete:
                try:
                    os.unlink(old_backup)
                    deleted_count += 1
                except Exception as e:
                    self.logger.log_error(e, {
                        'action': 'delete_old_backup',
                        'backup_file': old_backup
                    })
            
            if deleted_count > 0:
                self.logger.log_module_activity('engager', 'system', 'info', {
                    'message': f'Cleaned up {deleted_count} old backup files',
                    'max_backups': max_backups,
                    'remaining_backups': len(backup_files) - deleted_count
                })
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'cleanup_old_backups',
                'backup_dir': str(self.backup_dir),
                'max_backups': max_backups
            })
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available database backups.
        
        Returns:
            List of backup information dictionaries
        """
        try:
            backup_pattern = str(self.backup_dir / "leads_cache_*.db")
            backup_files = glob.glob(backup_pattern)
            
            backups = []
            for backup_file in backup_files:
                backup_path = Path(backup_file)
                stat = backup_path.stat()
                
                backups.append({
                    'filename': backup_path.name,
                    'path': str(backup_path),
                    'size_bytes': stat.st_size,
                    'created_at': datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'list_backups'})
            return []
    
    def restore_from_backup(self, backup_filename: str) -> bool:
        """
        Restore database from a backup file.
        
        Args:
            backup_filename: Name of the backup file to restore from
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                self.logger.log_module_activity('engager', 'system', 'error', {
                    'message': f'Backup file not found: {backup_filename}',
                    'backup_path': str(backup_path)
                })
                return False
            
            # Verify backup integrity before restore
            if not self._verify_backup_integrity(backup_path):
                self.logger.log_module_activity('engager', 'system', 'error', {
                    'message': f'Backup file is corrupted: {backup_filename}',
                    'backup_path': str(backup_path)
                })
                return False
            
            # Create a backup of current database before restore
            current_backup_created = self.create_database_backup()
            if not current_backup_created:
                self.logger.log_module_activity('engager', 'system', 'warning', {
                    'message': 'Could not create backup of current database before restore'
                })
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            
            # Verify restored database
            if not self.test_database_connection():
                raise Exception("Restored database failed connection test")
            
            self.logger.log_module_activity('engager', 'system', 'success', {
                'message': f'Database restored successfully from backup: {backup_filename}',
                'backup_path': str(backup_path),
                'restored_to': self.db_path
            })
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'restore_from_backup',
                'backup_filename': backup_filename
            })
            return False
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about database backups.
        
        Returns:
            Dictionary with backup statistics
        """
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'total_size_bytes': 0,
                    'oldest_backup': None,
                    'newest_backup': None,
                    'backup_dir': str(self.backup_dir)
                }
            
            total_size = sum(backup['size_bytes'] for backup in backups)
            
            return {
                'total_backups': len(backups),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_backup': backups[-1]['filename'] if backups else None,
                'newest_backup': backups[0]['filename'] if backups else None,
                'backup_dir': str(self.backup_dir),
                'backups': backups
            }
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_backup_statistics'})
            return {'error': str(e)}