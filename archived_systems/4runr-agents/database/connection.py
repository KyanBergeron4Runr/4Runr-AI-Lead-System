#!/usr/bin/env python3
"""
Database Connection Manager

Handles SQLite database connections, initialization, and connection pooling
for the 4Runr lead management system.
"""

import os
import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Thread-safe SQLite database connection manager with connection pooling
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection manager
        
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
        Determine the database file path
        
        Args:
            db_path: Optional custom database path
            
        Returns:
            str: Full path to database file
        """
        if db_path:
            return db_path
        
        # Check environment variable
        env_path = os.getenv('LEAD_DATABASE_PATH')
        if env_path:
            return env_path
        
        # Default to data directory
        script_dir = Path(__file__).parent.parent
        return str(script_dir / 'data' / 'leads.db')
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get thread-local database connection
        
        Returns:
            sqlite3.Connection: Database connection for current thread
        """
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout
                check_same_thread=False
            )
            
            # Configure connection
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute('PRAGMA foreign_keys = ON')
            self._local.connection.execute('PRAGMA journal_mode = WAL')
            self._local.connection.execute('PRAGMA synchronous = NORMAL')
            
        return self._local.connection
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with automatic transaction handling
        
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
        Initialize database schema if not already done
        """
        with self._lock:
            if self._initialized:
                return
            
            try:
                schema_path = Path(__file__).parent / 'schema.sql'
                
                if not schema_path.exists():
                    raise FileNotFoundError(f"Schema file not found: {schema_path}")
                
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                with self.get_connection() as conn:
                    # Execute schema creation
                    conn.executescript(schema_sql)
                    
                    # Verify tables were created
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name IN ('leads', 'sync_status', 'migration_log')
                    """)
                    
                    tables = [row[0] for row in cursor.fetchall()]
                    expected_tables = {'leads', 'sync_status', 'migration_log'}
                    
                    if not expected_tables.issubset(set(tables)):
                        missing = expected_tables - set(tables)
                        raise RuntimeError(f"Failed to create tables: {missing}")
                    
                    logger.info("Database schema initialized successfully")
                    self._initialized = True
                    
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SELECT query
        
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
        Execute an INSERT, UPDATE, or DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            int: Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: list) -> int:
        """
        Execute a query with multiple parameter sets
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            int: Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics
        
        Returns:
            dict: Database information
        """
        try:
            with self.get_connection() as conn:
                # Get table counts
                cursor = conn.execute("SELECT COUNT(*) FROM leads")
                leads_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sync_status")
                sync_status_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM migration_log")
                migration_log_count = cursor.fetchone()[0]
                
                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'database_path': self.db_path,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                    'leads_count': leads_count,
                    'sync_status_count': sync_status_count,
                    'migration_log_count': migration_log_count,
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
        Perform database health check
        
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
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                return {
                    'status': 'healthy',
                    'response_time_seconds': response_time,
                    'leads_count': leads_count,
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
        Close all thread-local connections
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
    Get database connection instance (singleton pattern per path)
    
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
    Close all database connections
    """
    global _db_connections
    
    with _db_lock:
        for conn in _db_connections.values():
            conn.close_connections()
        _db_connections.clear()