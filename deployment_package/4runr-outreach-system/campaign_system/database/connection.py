"""
Database connection management for campaign system
"""

import sqlite3
import os
from typing import Optional
from contextlib import contextmanager


class DatabaseManager:
    """Manages database connections for the campaign system"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to campaigns.db in the campaign_system directory
            db_path = os.path.join(os.path.dirname(__file__), '..', 'campaigns.db')
        
        self.db_path = os.path.abspath(db_path)
        self.ensure_directory_exists()
    
    def ensure_directory_exists(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        """Execute a single query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall()
    
    def execute_many(self, query: str, params_list: list):
        """Execute multiple queries with different parameters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount


# Global database manager instance
_db_manager = None


def get_database_connection():
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database(db_path: Optional[str] = None):
    """Initialize the database with custom path"""
    global _db_manager
    _db_manager = DatabaseManager(db_path)
    return _db_manager