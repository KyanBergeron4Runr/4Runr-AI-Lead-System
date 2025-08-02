"""
Database models and schema for the lead cache system.
"""

import sqlite3
import os
from typing import Optional

class DatabaseSchema:
    """Manages database schema creation and migrations"""
    
    @staticmethod
    def create_tables(db_path: str) -> None:
        """Create all necessary tables if they don't exist"""
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Create leads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,           -- Airtable record ID
                    name TEXT,
                    company TEXT,
                    email TEXT,
                    status TEXT,
                    title TEXT,
                    linkedin_url TEXT,
                    website TEXT,
                    location TEXT,
                    data_json TEXT,               -- Full Airtable record as JSON
                    last_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_name ON leads(name)')
            
            # Create cache metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create pending sync table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_sync (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT,
                    action TEXT,                  -- 'update', 'create', 'delete'
                    changes_json TEXT,            -- JSON of what changed
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_at TIMESTAMP NULL
                )
            ''')
            
            # Initialize metadata if empty
            cursor.execute('''
                INSERT OR IGNORE INTO cache_meta (key, value) 
                VALUES ('cache_version', '1.0')
            ''')
            
            conn.commit()
            print(f"✅ Database initialized at {db_path}")
            
        except Exception as e:
            print(f"❌ Error creating database schema: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    @staticmethod
    def get_connection(db_path: str) -> sqlite3.Connection:
        """Get a database connection with proper configuration"""
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        conn.execute('PRAGMA journal_mode=WAL')  # Better concurrency
        conn.execute('PRAGMA synchronous=NORMAL')  # Good balance of safety/speed
        return conn