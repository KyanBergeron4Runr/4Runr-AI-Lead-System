#!/usr/bin/env python3
"""
Database Connection Manager

Enhanced SQLite database connection manager for the 4runr-lead-scraper system.
Handles connections, initialization, migrations, and backup functionality.
"""

import os
import sqlite3
import threading
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

# Configure logging
logger = logging.getLogger('database-connection')

class DatabaseConnection:
    """
    Thread-safe SQLite database connection manager with enhanced functionality.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        self.db_path = self._get_database_path(db_path)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialized = False
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database schema
        self._initialize_database()
        
        logger.info(f"Database connection manager initialized: {self.db_path}")
    
    def _get_database_path(self, db_path: Optional[str]) -> str:
        """
        Determine the database file path.
        
        Args:
            db_path: Optional custom database path
            
        Returns:
            str: Full path to database file
        """
        if db_path:
            return os.path.abspath(db_path)
        
        # Check environment variable
        env_path = os.getenv('LEAD_DATABASE_PATH')
        if env_path:
            return os.path.abspath(env_path)
        
        # Default to data directory relative to this file
        script_dir = Path(__file__).parent.parent
        return str(script_dir / 'data' / 'leads.db')
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get thread-local database connection.
        
        Returns:
            sqlite3.Connection: Database connection for current thread
        """
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout
                check_same_thread=False
            )
            
            # Configure connection for optimal performance
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute('PRAGMA foreign_keys = ON')
            self._local.connection.execute('PRAGMA journal_mode = WAL')
            self._local.connection.execute('PRAGMA synchronous = NORMAL')
            self._local.connection.execute('PRAGMA cache_size = -64000')  # 64MB cache
            
        return self._local.connection
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with automatic transaction handling.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
    
    def _initialize_database(self):
        """
        Initialize database schema if not already done.
        """
        with self._lock:
            if self._initialized:
                return
            
            try:
                # Create schema directly (no external file dependency)
                schema_sql = self._get_schema_sql()
                
                with self.get_connection() as conn:
                    # Execute schema creation
                    conn.executescript(schema_sql)
                    
                    # Verify tables were created
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name IN ('leads', 'sync_log', 'migration_log')
                    """)
                    
                    tables = [row[0] for row in cursor.fetchall()]
                    expected_tables = {'leads', 'sync_log', 'migration_log'}
                    
                    if not expected_tables.issubset(set(tables)):
                        missing = expected_tables - set(tables)
                        raise RuntimeError(f"Failed to create tables: {missing}")
                    
                    logger.info("Database schema initialized successfully")
                    self._initialized = True
                    
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
    
    def _get_schema_sql(self) -> str:
        """Get the database schema SQL."""
        return """
        -- Leads table with comprehensive fields
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            company TEXT,
            title TEXT,
            linkedin_url TEXT UNIQUE,
            company_website TEXT,
            phone TEXT,
            
            -- Scraping metadata
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scraping_source TEXT DEFAULT 'serpapi',
            search_query TEXT,
            search_context TEXT,
            
            -- Enrichment status
            enriched BOOLEAN DEFAULT FALSE,
            enrichment_attempts INTEGER DEFAULT 0,
            enrichment_last_attempt TIMESTAMP,
            enrichment_method TEXT,
            
            -- Lead qualification
            qualified BOOLEAN DEFAULT FALSE,
            qualification_date TIMESTAMP,
            qualification_criteria TEXT,
            lead_score INTEGER,
            company_size TEXT,
            industry TEXT,
            location TEXT,
            
            -- Engagement tracking
            status TEXT DEFAULT 'scraped', -- scraped, enriched, ready, contacted, responded
            ready_for_outreach BOOLEAN DEFAULT FALSE,
            last_contacted TIMESTAMP,
            
            -- Sync tracking
            airtable_id TEXT,
            airtable_synced TIMESTAMP,
            sync_status TEXT DEFAULT 'pending',
            
            -- Verification
            verified BOOLEAN DEFAULT FALSE,
            verification_date TIMESTAMP,
            
            -- Metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Sync log table for tracking synchronization operations
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL, -- 'to_airtable', 'from_airtable'
            lead_id TEXT,
            status TEXT NOT NULL, -- 'success', 'failed', 'conflict'
            error_message TEXT,
            sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        );
        
        -- Migration log table for tracking data migrations
        CREATE TABLE IF NOT EXISTS migration_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_type TEXT NOT NULL,
            source_system TEXT,
            leads_migrated INTEGER DEFAULT 0,
            leads_merged INTEGER DEFAULT 0,
            migration_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            migration_details TEXT
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
        CREATE INDEX IF NOT EXISTS idx_leads_enriched ON leads(enriched);
        CREATE INDEX IF NOT EXISTS idx_leads_ready_for_outreach ON leads(ready_for_outreach);
        CREATE INDEX IF NOT EXISTS idx_leads_scraped_at ON leads(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
        CREATE INDEX IF NOT EXISTS idx_leads_linkedin_url ON leads(linkedin_url);
        CREATE INDEX IF NOT EXISTS idx_leads_airtable_id ON leads(airtable_id);
        CREATE INDEX IF NOT EXISTS idx_sync_log_lead_id ON sync_log(lead_id);
        CREATE INDEX IF NOT EXISTS idx_sync_log_timestamp ON sync_log(sync_timestamp);
        """
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SELECT query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            sqlite3.Cursor: Query cursor
        """
        with self.get_connection() as conn:
            return conn.execute(query, params)
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            int: Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute a query with multiple parameter sets.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            int: Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for backup file. If None, generates timestamp-based name.
            
        Returns:
            str: Path to backup file
        """
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(self.db_path).parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            backup_path = str(backup_dir / f'leads_backup_{timestamp}.db')
        
        try:
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if restore successful
        """
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Close existing connections
            self.close_connections()
            
            # Create backup of current database
            current_backup = self.backup_database()
            logger.info(f"Current database backed up to: {current_backup}")
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            
            # Reinitialize
            self._initialized = False
            self._initialize_database()
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            dict: Database information
        """
        try:
            with self.get_connection() as conn:
                # Get table counts
                cursor = conn.execute("SELECT COUNT(*) FROM leads")
                leads_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE enriched = 1")
                enriched_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE ready_for_outreach = 1")
                ready_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sync_log")
                sync_log_count = cursor.fetchone()[0]
                
                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'database_path': self.db_path,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                    'leads_count': leads_count,
                    'enriched_count': enriched_count,
                    'ready_for_outreach_count': ready_count,
                    'sync_log_count': sync_log_count,
                    'initialized': self._initialized,
                    'last_checked': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {
                'database_path': self.db_path,
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check.
        
        Returns:
            dict: Health check results
        """
        try:
            start_time = datetime.now()
            
            with self.get_connection() as conn:
                # Test basic query
                cursor = conn.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result[0] != 1:
                    raise RuntimeError("Basic query failed")
                
                # Test table access
                cursor = conn.execute("SELECT COUNT(*) FROM leads")
                leads_count = cursor.fetchone()[0]
                
                # Test write operation
                test_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='leads'"
                cursor = conn.execute(test_query)
                table_exists = cursor.fetchone() is not None
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                return {
                    'status': 'healthy',
                    'response_time_seconds': response_time,
                    'leads_count': leads_count,
                    'tables_accessible': table_exists,
                    'database_path': self.db_path,
                    'checked_at': end_time.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_path': self.db_path,
                'checked_at': datetime.now().isoformat()
            }
    
    def close_connections(self):
        """
        Close all thread-local connections.
        """
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
        
        logger.info("Database connections closed")


# Global database connection instances (keyed by path)
_db_connections: Dict[str, DatabaseConnection] = {}
_db_lock = threading.Lock()

def get_database_connection(db_path: Optional[str] = None) -> DatabaseConnection:
    """
    Get database connection instance (singleton pattern per path).
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        DatabaseConnection: Database connection manager
    """
    global _db_connections
    
    # Determine the actual path that will be used
    temp_conn = DatabaseConnection.__new__(DatabaseConnection)
    actual_path = temp_conn._get_database_path(db_path)
    
    with _db_lock:
        if actual_path not in _db_connections:
            _db_connections[actual_path] = DatabaseConnection(db_path)
        
        return _db_connections[actual_path]

def close_database_connections():
    """
    Close all database connections.
    """
    global _db_connections
    
    with _db_lock:
        for conn in _db_connections.values():
            conn.close_connections()
        _db_connections.clear()


if __name__ == "__main__":
    # Test the database connection
    db = get_database_connection()
    
    print("🧪 Testing Database Connection...")
    
    # Health check
    health = db.health_check()
    print(f"Health Status: {health['status']}")
    
    # Database info
    info = db.get_database_info()
    print(f"Database: {info['database_path']}")
    print(f"Leads Count: {info['leads_count']}")
    print(f"Size: {info['database_size_mb']} MB")
    
    print("✅ Database connection test completed")