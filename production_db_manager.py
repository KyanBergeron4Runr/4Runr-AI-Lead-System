#!/usr/bin/env python3
"""
Production Database Manager

Direct SQLite access without connection pooling for production reliability.
No timeouts, no complexity, just fast database operations.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

class ProductionDatabaseManager:
    """Production-ready database manager with direct SQLite access."""
    
    def __init__(self, db_path: str = "data/unified_leads.db"):
        """Initialize with database path."""
        self.db_path = db_path
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if needed
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist and add missing columns."""
        with self.get_connection() as conn:
            # Create table with basic schema first
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    full_name TEXT,
                    email TEXT,
                    company TEXT,
                    title TEXT,
                    linkedin_url TEXT,
                    company_website TEXT,
                    phone TEXT,
                    location TEXT,
                    industry TEXT,
                    company_size TEXT,
                    business_type TEXT,
                    ai_message TEXT,
                    message_generated_at TIMESTAMP,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add missing columns if they don't exist
            self._add_missing_columns(conn)
            conn.commit()
    
    def _add_missing_columns(self, conn):
        """Add missing columns to existing database."""
        missing_columns = [
            ('sync_status', 'TEXT DEFAULT "pending"'),
            ('message_generated_at', 'TIMESTAMP'),
            ('company_website', 'TEXT')
        ]
        
        # Get existing columns
        cursor = conn.execute("PRAGMA table_info(leads)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns
        for col_name, col_def in missing_columns:
            if col_name not in existing_columns:
                try:
                    conn.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_def}")
                    logger.info(f"Added missing column: {col_name}")
                except Exception as e:
                    logger.warning(f"Could not add column {col_name}: {e}")
        
        # Log the actual schema
        logger.info("Current database schema:")
        cursor = conn.execute("PRAGMA table_info(leads)")
        for row in cursor.fetchall():
            logger.info(f"  {row[1]} ({row[2]})")
    
    def add_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Add lead to database."""
        try:
            with self.get_connection() as conn:
                # Remove ID from lead_data if present (let database auto-increment)
                clean_data = {k: v for k, v in lead_data.items() if k != 'id'}
                
                if not clean_data:
                    logger.error("No data to insert")
                    return False
                
                columns = ', '.join(clean_data.keys())
                placeholders = ', '.join(['?' for _ in clean_data])
                
                cursor = conn.execute(
                    f"INSERT INTO leads ({columns}) VALUES ({placeholders})",
                    list(clean_data.values())
                )
                conn.commit()
                
                # Get the inserted ID
                inserted_id = cursor.lastrowid
                logger.info(f"Added lead with ID: {inserted_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to add lead: {e}")
            return False
    
    def get_lead(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """Get lead by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM leads WHERE id = ?", (lead_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get lead: {e}")
            return None
    
    def get_leads_for_sync(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get leads ready for Airtable sync."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM leads 
                    WHERE sync_status = 'pending' 
                    AND email IS NOT NULL 
                    AND email != ''
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get leads for sync: {e}")
            return []
    
    def update_lead(self, lead_id: int, updates: Dict[str, Any]) -> bool:
        """Update lead data."""
        try:
            with self.get_connection() as conn:
                set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [lead_id]
                
                conn.execute(
                    f"UPDATE leads SET {set_clause} WHERE id = ?",
                    values
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update lead: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) as total FROM leads")
                total = cursor.fetchone()['total']
                
                cursor = conn.execute("SELECT COUNT(*) as with_email FROM leads WHERE email IS NOT NULL AND email != ''")
                with_email = cursor.fetchone()['with_email']
                
                cursor = conn.execute("SELECT COUNT(*) as ready FROM leads WHERE ready_for_outreach = 1")
                ready = cursor.fetchone()['ready']
                
                return {
                    'total_leads': total,
                    'leads_with_email': with_email,
                    'leads_ready_for_outreach': ready,
                    'email_percentage': round((with_email / total * 100) if total > 0 else 0, 1)
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

# Global instance
db_manager = ProductionDatabaseManager()
