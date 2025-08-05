#!/usr/bin/env python3
"""
Database Migrations

Handles database schema migrations and version management for the 4runr-lead-scraper system.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from .connection import get_database_connection

logger = logging.getLogger('database-migrations')

class DatabaseMigration:
    """
    Database migration manager for schema updates and data migrations.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize migration manager.
        
        Args:
            db_path: Optional database path
        """
        self.db = get_database_connection(db_path)
        self._ensure_migration_table()
        logger.info("Database migration manager initialized")
    
    def _ensure_migration_table(self):
        """Ensure migration tracking table exists."""
        try:
            query = """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rollback_sql TEXT
                )
            """
            self.db.execute_update(query)
            logger.info("Migration tracking table ensured")
            
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise
    
    def get_current_version(self) -> str:
        """
        Get the current database schema version.
        
        Returns:
            str: Current version or '0.0.0' if no migrations applied
        """
        try:
            cursor = self.db.execute_query("""
                SELECT version FROM schema_migrations 
                ORDER BY applied_at DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            return row[0] if row else '0.0.0'
            
        except Exception as e:
            logger.error(f"Failed to get current version: {e}")
            return '0.0.0'
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """
        Get list of applied migrations.
        
        Returns:
            List of migration records
        """
        try:
            cursor = self.db.execute_query("""
                SELECT version, description, applied_at 
                FROM schema_migrations 
                ORDER BY applied_at ASC
            """)
            
            return [
                {
                    'version': row[0],
                    'description': row[1],
                    'applied_at': row[2]
                }
                for row in cursor.fetchall()
            ]
            
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def apply_migration(self, version: str, description: str, sql: str, rollback_sql: str = None) -> bool:
        """
        Apply a database migration.
        
        Args:
            version: Migration version (e.g., '1.0.1')
            description: Migration description
            sql: SQL to execute
            rollback_sql: Optional rollback SQL
            
        Returns:
            bool: True if migration successful
        """
        try:
            # Check if migration already applied
            cursor = self.db.execute_query(
                "SELECT COUNT(*) FROM schema_migrations WHERE version = ?", 
                (version,)
            )
            
            if cursor.fetchone()[0] > 0:
                logger.info(f"Migration {version} already applied")
                return True
            
            # Apply migration
            with self.db.get_connection() as conn:
                # Execute migration SQL
                conn.executescript(sql)
                
                # Record migration
                conn.execute("""
                    INSERT INTO schema_migrations (version, description, rollback_sql)
                    VALUES (?, ?, ?)
                """, (version, description, rollback_sql))
            
            logger.info(f"Applied migration {version}: {description}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            return False
    
    def rollback_migration(self, version: str) -> bool:
        """
        Rollback a specific migration.
        
        Args:
            version: Migration version to rollback
            
        Returns:
            bool: True if rollback successful
        """
        try:
            # Get migration details
            cursor = self.db.execute_query("""
                SELECT rollback_sql FROM schema_migrations 
                WHERE version = ?
            """, (version,))
            
            row = cursor.fetchone()
            if not row:
                logger.error(f"Migration {version} not found")
                return False
            
            rollback_sql = row[0]
            if not rollback_sql:
                logger.error(f"No rollback SQL for migration {version}")
                return False
            
            # Execute rollback
            with self.db.get_connection() as conn:
                conn.executescript(rollback_sql)
                
                # Remove migration record
                conn.execute(
                    "DELETE FROM schema_migrations WHERE version = ?", 
                    (version,)
                )
            
            logger.info(f"Rolled back migration {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            return False
    
    def migrate_to_latest(self) -> bool:
        """
        Apply all pending migrations to bring database to latest version.
        
        Returns:
            bool: True if all migrations successful
        """
        migrations = self._get_pending_migrations()
        
        if not migrations:
            logger.info("Database is up to date")
            return True
        
        logger.info(f"Applying {len(migrations)} pending migrations")
        
        for migration in migrations:
            success = self.apply_migration(
                migration['version'],
                migration['description'],
                migration['sql'],
                migration.get('rollback_sql')
            )
            
            if not success:
                logger.error(f"Migration failed at version {migration['version']}")
                return False
        
        logger.info("All migrations applied successfully")
        return True
    
    def _get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of pending migrations."""
        current_version = self.get_current_version()
        all_migrations = self._get_all_migrations()
        
        # Filter out already applied migrations
        applied_versions = {m['version'] for m in self.get_applied_migrations()}
        
        return [
            m for m in all_migrations 
            if m['version'] not in applied_versions
        ]
    
    def _get_all_migrations(self) -> List[Dict[str, Any]]:
        """
        Get all available migrations.
        
        Returns:
            List of migration definitions
        """
        return [
            {
                'version': '1.0.0',
                'description': 'Initial schema with enhanced lead fields',
                'sql': '''
                    -- This migration is handled by the connection.py initialization
                    -- Just mark as applied
                    SELECT 1;
                ''',
                'rollback_sql': '''
                    DROP TABLE IF EXISTS leads;
                    DROP TABLE IF EXISTS sync_log;
                    DROP TABLE IF EXISTS migration_log;
                '''
            },
            {
                'version': '1.0.1',
                'description': 'Add indexes for performance optimization',
                'sql': '''
                    CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company);
                    CREATE INDEX IF NOT EXISTS idx_leads_title ON leads(title);
                    CREATE INDEX IF NOT EXISTS idx_leads_location ON leads(location);
                    CREATE INDEX IF NOT EXISTS idx_leads_qualification_date ON leads(qualification_date);
                ''',
                'rollback_sql': '''
                    DROP INDEX IF EXISTS idx_leads_company;
                    DROP INDEX IF EXISTS idx_leads_title;
                    DROP INDEX IF EXISTS idx_leads_location;
                    DROP INDEX IF EXISTS idx_leads_qualification_date;
                '''
            },
            {
                'version': '1.0.2',
                'description': 'Add full-text search support',
                'sql': '''
                    CREATE VIRTUAL TABLE IF NOT EXISTS leads_fts USING fts5(
                        name, company, title, search_context,
                        content='leads',
                        content_rowid='rowid'
                    );
                    
                    -- Populate FTS table
                    INSERT INTO leads_fts(rowid, name, company, title, search_context)
                    SELECT rowid, name, company, title, search_context FROM leads;
                    
                    -- Create triggers to keep FTS in sync
                    CREATE TRIGGER IF NOT EXISTS leads_fts_insert AFTER INSERT ON leads BEGIN
                        INSERT INTO leads_fts(rowid, name, company, title, search_context)
                        VALUES (new.rowid, new.name, new.company, new.title, new.search_context);
                    END;
                    
                    CREATE TRIGGER IF NOT EXISTS leads_fts_delete AFTER DELETE ON leads BEGIN
                        INSERT INTO leads_fts(leads_fts, rowid, name, company, title, search_context)
                        VALUES ('delete', old.rowid, old.name, old.company, old.title, old.search_context);
                    END;
                    
                    CREATE TRIGGER IF NOT EXISTS leads_fts_update AFTER UPDATE ON leads BEGIN
                        INSERT INTO leads_fts(leads_fts, rowid, name, company, title, search_context)
                        VALUES ('delete', old.rowid, old.name, old.company, old.title, old.search_context);
                        INSERT INTO leads_fts(rowid, name, company, title, search_context)
                        VALUES (new.rowid, new.name, new.company, new.title, new.search_context);
                    END;
                ''',
                'rollback_sql': '''
                    DROP TRIGGER IF EXISTS leads_fts_update;
                    DROP TRIGGER IF EXISTS leads_fts_delete;
                    DROP TRIGGER IF EXISTS leads_fts_insert;
                    DROP TABLE IF EXISTS leads_fts;
                '''
            }
        ]
    
    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate current database schema.
        
        Returns:
            Dictionary with validation results
        """
        try:
            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'tables': {},
                'indexes': {}
            }
            
            # Check required tables
            required_tables = ['leads', 'sync_log', 'migration_log', 'schema_migrations']
            
            cursor = self.db.execute_query("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            for table in required_tables:
                if table in existing_tables:
                    results['tables'][table] = 'exists'
                else:
                    results['tables'][table] = 'missing'
                    results['errors'].append(f"Required table '{table}' is missing")
                    results['valid'] = False
            
            # Check indexes
            cursor = self.db.execute_query("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """)
            
            existing_indexes = {row[0] for row in cursor.fetchall()}
            results['indexes'] = list(existing_indexes)
            
            # Check for common issues
            if 'leads' in existing_tables:
                # Check for required columns
                cursor = self.db.execute_query("PRAGMA table_info(leads)")
                columns = {row[1] for row in cursor.fetchall()}
                
                required_columns = ['id', 'name', 'email', 'company', 'linkedin_url']
                for col in required_columns:
                    if col not in columns:
                        results['errors'].append(f"Required column '{col}' missing from leads table")
                        results['valid'] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': [],
                'tables': {},
                'indexes': {}
            }
    
    def repair_schema(self) -> bool:
        """
        Attempt to repair common schema issues.
        
        Returns:
            bool: True if repair successful
        """
        try:
            logger.info("Starting schema repair")
            
            # Validate current schema
            validation = self.validate_schema()
            
            if validation['valid']:
                logger.info("Schema is valid, no repair needed")
                return True
            
            # Apply all pending migrations
            success = self.migrate_to_latest()
            
            if success:
                # Re-validate
                validation = self.validate_schema()
                if validation['valid']:
                    logger.info("Schema repair completed successfully")
                    return True
                else:
                    logger.error(f"Schema repair failed: {validation['errors']}")
                    return False
            else:
                logger.error("Schema repair failed during migration")
                return False
                
        except Exception as e:
            logger.error(f"Schema repair failed: {e}")
            return False


# Convenience function
def get_migration_manager(db_path: str = None) -> DatabaseMigration:
    """
    Get DatabaseMigration instance.
    
    Args:
        db_path: Optional database path
        
    Returns:
        DatabaseMigration instance
    """
    return DatabaseMigration(db_path)


if __name__ == "__main__":
    # Test migrations
    migration_manager = get_migration_manager()
    
    print("🧪 Testing Database Migrations...")
    
    # Check current version
    version = migration_manager.get_current_version()
    print(f"Current version: {version}")
    
    # Validate schema
    validation = migration_manager.validate_schema()
    print(f"Schema valid: {validation['valid']}")
    
    if not validation['valid']:
        print(f"Errors: {validation['errors']}")
    
    # Apply migrations
    success = migration_manager.migrate_to_latest()
    print(f"Migration success: {success}")
    
    print("✅ Migration test completed")