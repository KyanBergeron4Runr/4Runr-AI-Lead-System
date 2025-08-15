#!/usr/bin/env python3
"""
Database Sync Triggers

Provides automatic sync triggers that fire when leads are created or updated
in the database, ensuring immediate synchronization to Airtable.
"""

import sqlite3
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.sync_scheduler import get_sync_scheduler
from utils.logging import get_logger

class DatabaseSyncTriggers:
    """
    Database trigger system for automatic sync operations.
    """
    
    def __init__(self, db_connection):
        """
        Initialize database sync triggers.
        
        Args:
            db_connection: SQLite database connection
        """
        self.db = db_connection
        self.logger = get_logger('db-sync-triggers')
        self.sync_scheduler = get_sync_scheduler()
        
        # Track pending syncs to avoid duplicate triggers
        self._pending_syncs = set()
        self._sync_lock = threading.Lock()
        
        self.logger.info("🔗 Database sync triggers initialized")
    
    def setup_triggers(self):
        """Set up database triggers for automatic sync."""
        try:
            self.logger.info("⚙️ Setting up database sync triggers")
            
            # Create trigger for lead insertions
            self.db.execute("""
                CREATE TRIGGER IF NOT EXISTS sync_on_lead_insert
                AFTER INSERT ON leads
                FOR EACH ROW
                BEGIN
                    UPDATE leads 
                    SET sync_status = 'pending', updated_at = datetime('now')
                    WHERE id = NEW.id;
                END;
            """)
            
            # Create trigger for lead updates
            self.db.execute("""
                CREATE TRIGGER IF NOT EXISTS sync_on_lead_update
                AFTER UPDATE ON leads
                FOR EACH ROW
                WHEN NEW.sync_status != 'syncing'
                BEGIN
                    UPDATE leads 
                    SET sync_status = 'pending', updated_at = datetime('now')
                    WHERE id = NEW.id;
                END;
            """)
            
            self.db.commit()
            self.logger.info("✅ Database sync triggers created successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup database triggers: {str(e)}")
            raise
    
    def remove_triggers(self):
        """Remove database sync triggers."""
        try:
            self.logger.info("🗑️ Removing database sync triggers")
            
            self.db.execute("DROP TRIGGER IF EXISTS sync_on_lead_insert")
            self.db.execute("DROP TRIGGER IF EXISTS sync_on_lead_update")
            
            self.db.commit()
            self.logger.info("✅ Database sync triggers removed")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to remove database triggers: {str(e)}")
    
    def trigger_immediate_sync(self, lead_id: str, operation: str = 'update'):
        """
        Trigger immediate sync for a specific lead.
        
        Args:
            lead_id: ID of the lead to sync
            operation: Type of operation ('insert', 'update', 'delete')
        """
        with self._sync_lock:
            # Avoid duplicate sync requests
            if lead_id in self._pending_syncs:
                self.logger.debug(f"⏭️ Sync already pending for lead {lead_id}")
                return
            
            self._pending_syncs.add(lead_id)
        
        try:
            self.logger.debug(f"🔄 Triggering immediate sync for lead {lead_id} ({operation})")
            
            # Mark lead as syncing to prevent trigger loops
            self.db.execute(
                "UPDATE leads SET sync_status = 'syncing' WHERE id = ?",
                (lead_id,)
            )
            self.db.commit()
            
            # Perform the sync in a separate thread to avoid blocking
            sync_thread = threading.Thread(
                target=self._perform_sync,
                args=(lead_id, operation),
                daemon=True
            )
            sync_thread.start()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to trigger sync for lead {lead_id}: {str(e)}")
            # Remove from pending syncs on error
            with self._sync_lock:
                self._pending_syncs.discard(lead_id)
    
    def _perform_sync(self, lead_id: str, operation: str):
        """
        Perform the actual sync operation.
        
        Args:
            lead_id: ID of the lead to sync
            operation: Type of operation
        """
        try:
            # Perform the sync
            result = self.sync_scheduler.sync_lead_to_airtable_immediately(lead_id)
            
            # Update sync status based on result
            if result.get('success'):
                sync_status = 'synced'
                self.logger.debug(f"✅ Lead {lead_id} synced successfully")
            else:
                sync_status = 'failed'
                self.logger.warning(f"⚠️ Lead {lead_id} sync failed: {result.get('error', 'Unknown error')}")
            
            # Update the database with sync result
            self.db.execute(
                "UPDATE leads SET sync_status = ?, airtable_synced = ? WHERE id = ?",
                (sync_status, datetime.now().isoformat(), lead_id)
            )
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"❌ Sync operation failed for lead {lead_id}: {str(e)}")
            
            # Mark as failed
            try:
                self.db.execute(
                    "UPDATE leads SET sync_status = 'failed' WHERE id = ?",
                    (lead_id,)
                )
                self.db.commit()
            except Exception:
                pass  # Ignore secondary errors
        
        finally:
            # Remove from pending syncs
            with self._sync_lock:
                self._pending_syncs.discard(lead_id)


class SyncAwareConnection:
    """
    Database connection wrapper that automatically triggers sync operations.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize sync-aware database connection.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        # Initialize sync triggers
        self.sync_triggers = DatabaseSyncTriggers(self.connection)
        self.sync_triggers.setup_triggers()
        
        self.logger = get_logger('sync-aware-db')
        self.logger.info(f"🔗 Sync-aware database connection established: {db_path}")
    
    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Execute a database query."""
        if params:
            return self.connection.execute(query, params)
        else:
            return self.connection.execute(query)
    
    def executemany(self, query: str, params_list) -> sqlite3.Cursor:
        """Execute a database query with multiple parameter sets."""
        return self.connection.executemany(query, params_list)
    
    def commit(self):
        """Commit the current transaction."""
        self.connection.commit()
    
    def rollback(self):
        """Rollback the current transaction."""
        self.connection.rollback()
    
    def close(self):
        """Close the database connection."""
        try:
            self.sync_triggers.remove_triggers()
        except Exception:
            pass  # Ignore errors during cleanup
        
        self.connection.close()
        self.logger.info("🔗 Sync-aware database connection closed")
    
    def create_lead_with_sync(self, lead_data: Dict[str, Any]) -> str:
        """
        Create a lead and trigger immediate sync.
        
        Args:
            lead_data: Lead data dictionary
            
        Returns:
            Lead ID
        """
        try:
            # Generate lead ID
            import uuid
            lead_id = str(uuid.uuid4())
            
            # Prepare lead data with sync status
            lead_data_with_sync = {
                **lead_data,
                'id': lead_id,
                'sync_status': 'pending',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert lead
            columns = ', '.join(lead_data_with_sync.keys())
            placeholders = ', '.join(['?' for _ in lead_data_with_sync])
            values = tuple(lead_data_with_sync.values())
            
            query = f"INSERT INTO leads ({columns}) VALUES ({placeholders})"
            self.execute(query, values)
            self.commit()
            
            # Trigger immediate sync
            self.sync_triggers.trigger_immediate_sync(lead_id, 'insert')
            
            self.logger.info(f"✅ Lead created with immediate sync: {lead_id}")
            return lead_id
            
        except Exception as e:
            self.rollback()
            self.logger.error(f"❌ Failed to create lead with sync: {str(e)}")
            raise
    
    def update_lead_with_sync(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a lead and trigger immediate sync.
        
        Args:
            lead_id: Lead ID
            updates: Dictionary of updates
            
        Returns:
            True if successful
        """
        try:
            # Add sync status and timestamp
            updates_with_sync = {
                **updates,
                'sync_status': 'pending',
                'updated_at': datetime.now().isoformat()
            }
            
            # Build update query
            set_clause = ', '.join([f"{key} = ?" for key in updates_with_sync.keys()])
            values = tuple(updates_with_sync.values()) + (lead_id,)
            
            query = f"UPDATE leads SET {set_clause} WHERE id = ?"
            cursor = self.execute(query, values)
            
            if cursor.rowcount == 0:
                self.logger.warning(f"⚠️ No lead found with ID {lead_id}")
                return False
            
            self.commit()
            
            # Trigger immediate sync
            self.sync_triggers.trigger_immediate_sync(lead_id, 'update')
            
            self.logger.info(f"✅ Lead updated with immediate sync: {lead_id}")
            return True
            
        except Exception as e:
            self.rollback()
            self.logger.error(f"❌ Failed to update lead with sync: {str(e)}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.rollback()
        self.close()


# Factory function for creating sync-aware connections
def create_sync_aware_connection(db_path: str) -> SyncAwareConnection:
    """
    Create a sync-aware database connection.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        SyncAwareConnection instance
    """
    return SyncAwareConnection(db_path)


if __name__ == "__main__":
    # Test the sync triggers
    import tempfile
    import os
    
    print("🧪 Testing Database Sync Triggers")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        test_db_path = tmp_file.name
    
    try:
        # Create test table
        conn = sqlite3.connect(test_db_path)
        conn.execute("""
            CREATE TABLE leads (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                sync_status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT,
                airtable_synced TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        # Test sync-aware connection
        print("1. Testing sync-aware connection...")
        with create_sync_aware_connection(test_db_path) as sync_conn:
            print("   ✅ Connection created with triggers")
            
            # Test lead creation
            print("2. Testing lead creation with sync...")
            lead_id = sync_conn.create_lead_with_sync({
                'name': 'Test Lead',
                'email': 'test@example.com'
            })
            print(f"   ✅ Lead created: {lead_id}")
            
            # Test lead update
            print("3. Testing lead update with sync...")
            success = sync_conn.update_lead_with_sync(lead_id, {
                'email': 'updated@example.com'
            })
            print(f"   ✅ Lead updated: {success}")
        
        print("✅ Database sync triggers test completed")
        
    finally:
        # Clean up
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)