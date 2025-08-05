#!/usr/bin/env python3
"""
Database Connection Test

Simple test script to verify database operations work correctly.
"""

import sys
import uuid
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_database_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_operations():
    """
    Test basic database operations
    """
    try:
        logger.info("🧪 Testing database operations...")
        
        # Get database connection
        db_conn = get_database_connection()
        
        # Test 1: Insert a test lead
        test_lead_id = str(uuid.uuid4())
        test_uuid = str(uuid.uuid4())
        
        insert_query = """
            INSERT INTO leads (id, uuid, full_name, linkedin_url, email, company, title, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            test_lead_id,
            test_uuid,
            "Test Lead",
            "https://linkedin.com/in/testlead",
            "test@example.com",
            "Test Company",
            "CEO",
            "test"
        )
        
        rows_affected = db_conn.execute_update(insert_query, params)
        
        if rows_affected != 1:
            raise RuntimeError(f"Expected 1 row affected, got {rows_affected}")
        
        logger.info("✅ Test 1 passed: Lead insertion")
        
        # Test 2: Query the lead back
        select_query = "SELECT * FROM leads WHERE id = ?"
        cursor = db_conn.execute_query(select_query, (test_lead_id,))
        
        row = cursor.fetchone()
        
        if not row:
            raise RuntimeError("Lead not found after insertion")
        
        if row['full_name'] != "Test Lead":
            raise RuntimeError(f"Expected 'Test Lead', got '{row['full_name']}'")
        
        logger.info("✅ Test 2 passed: Lead retrieval")
        
        # Test 3: Update the lead
        update_query = "UPDATE leads SET enriched = ?, enriched_at = ? WHERE id = ?"
        update_params = (True, datetime.now().isoformat(), test_lead_id)
        
        rows_affected = db_conn.execute_update(update_query, update_params)
        
        if rows_affected != 1:
            raise RuntimeError(f"Expected 1 row affected in update, got {rows_affected}")
        
        logger.info("✅ Test 3 passed: Lead update")
        
        # Test 4: Test sync status table
        sync_insert_query = """
            INSERT INTO sync_status (lead_id, operation, status)
            VALUES (?, ?, ?)
        """
        
        sync_params = (test_lead_id, "create", "pending")
        rows_affected = db_conn.execute_update(sync_insert_query, sync_params)
        
        if rows_affected != 1:
            raise RuntimeError(f"Expected 1 row affected in sync insert, got {rows_affected}")
        
        logger.info("✅ Test 4 passed: Sync status insertion")
        
        # Test 5: Test foreign key constraint
        sync_select_query = """
            SELECT s.*, l.full_name 
            FROM sync_status s 
            JOIN leads l ON s.lead_id = l.id 
            WHERE s.lead_id = ?
        """
        
        cursor = db_conn.execute_query(sync_select_query, (test_lead_id,))
        row = cursor.fetchone()
        
        if not row or row['full_name'] != "Test Lead":
            raise RuntimeError("Foreign key join failed")
        
        logger.info("✅ Test 5 passed: Foreign key relationships")
        
        # Test 6: Clean up test data
        delete_sync_query = "DELETE FROM sync_status WHERE lead_id = ?"
        db_conn.execute_update(delete_sync_query, (test_lead_id,))
        
        delete_lead_query = "DELETE FROM leads WHERE id = ?"
        rows_affected = db_conn.execute_update(delete_lead_query, (test_lead_id,))
        
        if rows_affected != 1:
            raise RuntimeError(f"Expected 1 row affected in delete, got {rows_affected}")
        
        logger.info("✅ Test 6 passed: Data cleanup")
        
        # Test 7: Health check
        health = db_conn.health_check()
        
        if health['status'] != 'healthy':
            raise RuntimeError(f"Health check failed: {health}")
        
        logger.info("✅ Test 7 passed: Health check")
        
        logger.info("🎉 All database tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Main function
    """
    success = test_database_operations()
    
    if success:
        print("✅ Database connection tests passed!")
        sys.exit(0)
    else:
        print("❌ Database connection tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()