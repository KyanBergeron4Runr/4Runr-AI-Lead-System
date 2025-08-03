#!/usr/bin/env python3
"""
Database Initialization Script

Standalone script to initialize the lead database with proper schema.
Can be run independently or imported as a module.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_database_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_database(db_path: str = None) -> bool:
    """
    Initialize the lead database with proper schema
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        logger.info("🔧 Initializing lead database...")
        
        # Get database connection (this will initialize schema)
        db_conn = get_database_connection(db_path)
        
        # Perform health check
        health = db_conn.health_check()
        
        if health['status'] != 'healthy':
            logger.error(f"❌ Database health check failed: {health.get('error', 'Unknown error')}")
            return False
        
        # Get database info
        info = db_conn.get_database_info()
        
        logger.info("✅ Database initialization completed successfully!")
        logger.info(f"📍 Database location: {info['database_path']}")
        logger.info(f"📊 Database size: {info['database_size_mb']} MB")
        logger.info(f"📋 Tables created: leads, sync_status, migration_log")
        logger.info(f"🔍 Indexes created for performance optimization")
        
        # Log table counts
        logger.info(f"📈 Current data:")
        logger.info(f"   - Leads: {info['leads_count']}")
        logger.info(f"   - Sync status records: {info['sync_status_count']}")
        logger.info(f"   - Migration log entries: {info['migration_log_count']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def verify_database_schema(db_path: str = None) -> bool:
    """
    Verify that the database schema is correct
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        bool: True if schema is valid, False otherwise
    """
    try:
        logger.info("🔍 Verifying database schema...")
        
        db_conn = get_database_connection(db_path)
        
        with db_conn.get_connection() as conn:
            # Check that all required tables exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('leads', 'sync_status', 'migration_log')
                ORDER BY name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = ['leads', 'migration_log', 'sync_status']
            
            if tables != expected_tables:
                logger.error(f"❌ Missing tables. Expected: {expected_tables}, Found: {tables}")
                return False
            
            # Check leads table structure
            cursor = conn.execute("PRAGMA table_info(leads)")
            leads_columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            required_columns = {
                'id': 'TEXT',
                'uuid': 'TEXT',
                'full_name': 'TEXT',
                'linkedin_url': 'TEXT',
                'email': 'TEXT',
                'company': 'TEXT',
                'title': 'TEXT',
                'verified': 'BOOLEAN',
                'enriched': 'BOOLEAN',
                'needs_enrichment': 'BOOLEAN',
                'status': 'TEXT',
                'airtable_synced': 'BOOLEAN',
                'sync_pending': 'BOOLEAN'
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in leads_columns:
                    logger.error(f"❌ Missing column in leads table: {col_name}")
                    return False
            
            # Check indexes exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """)
            
            indexes = [row[0] for row in cursor.fetchall()]
            
            if len(indexes) < 5:  # We expect several indexes
                logger.warning(f"⚠️ Only {len(indexes)} indexes found, expected more")
            
            logger.info("✅ Database schema verification passed!")
            logger.info(f"📋 Tables: {', '.join(tables)}")
            logger.info(f"🔍 Indexes: {len(indexes)} performance indexes")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False

def create_backup(db_path: str = None, backup_dir: str = None) -> str:
    """
    Create a backup of the database
    
    Args:
        db_path: Optional custom database path
        backup_dir: Optional backup directory
        
    Returns:
        str: Path to backup file
    """
    try:
        db_conn = get_database_connection(db_path)
        
        if backup_dir is None:
            backup_dir = Path(db_conn.db_path).parent / 'backups'
        
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'leads_backup_{timestamp}.db'
        
        # Copy database file
        import shutil
        shutil.copy2(db_conn.db_path, backup_path)
        
        logger.info(f"✅ Database backup created: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"❌ Backup creation failed: {e}")
        raise

def main():
    """
    Main function for standalone execution
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize 4Runr Lead Database')
    parser.add_argument('--db-path', help='Custom database path')
    parser.add_argument('--verify', action='store_true', help='Verify schema only')
    parser.add_argument('--backup', action='store_true', help='Create backup')
    parser.add_argument('--info', action='store_true', help='Show database info')
    
    args = parser.parse_args()
    
    try:
        if args.backup:
            backup_path = create_backup(args.db_path)
            print(f"Backup created: {backup_path}")
            return
        
        if args.info:
            db_conn = get_database_connection(args.db_path)
            info = db_conn.get_database_info()
            
            print("\n📊 Database Information:")
            print(f"   Path: {info['database_path']}")
            print(f"   Size: {info['database_size_mb']} MB")
            print(f"   Leads: {info['leads_count']}")
            print(f"   Sync records: {info['sync_status_count']}")
            print(f"   Migration logs: {info['migration_log_count']}")
            return
        
        if args.verify:
            success = verify_database_schema(args.db_path)
        else:
            success = initialize_database(args.db_path)
        
        if success:
            print("✅ Database operation completed successfully!")
            sys.exit(0)
        else:
            print("❌ Database operation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()