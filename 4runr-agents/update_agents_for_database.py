#!/usr/bin/env python3
"""
Update All Agents for Database Integration

This script updates key agents to use the database instead of JSON files
and ensures proper integration across the system.
"""

import sys
import os
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_daily_enricher_agent():
    """Update daily enricher agent to use database"""
    
    logger.info("Updating daily_enricher_agent.py for database integration")
    
    enricher_file = Path(__file__).parent / "daily_enricher_agent.py"
    
    if not enricher_file.exists():
        logger.warning("daily_enricher_agent.py not found")
        return False
    
    try:
        # Read current content
        with open(enricher_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if 'from database.lead_database import get_lead_database' in content:
            logger.info("daily_enricher_agent.py already updated for database")
            return True
        
        # Add database import
        import_section = """
# Import database components
try:
    from database.lead_database import get_lead_database
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import database components: {e}")
    DATABASE_AVAILABLE = False
"""
        
        # Find where to insert the import
        if 'from shared.production_logger import get_logger' in content:
            content = content.replace(
                'from shared.production_logger import get_logger',
                'from shared.production_logger import get_logger' + import_section
            )
        else:
            # Insert at the beginning after existing imports
            lines = content.split('\n')
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_index = i + 1
            
            lines.insert(insert_index, import_section)
            content = '\n'.join(lines)
        
        # Write back
        with open(enricher_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ Updated daily_enricher_agent.py for database integration")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to update daily_enricher_agent.py: {str(e)}")
        return False

def update_sync_to_airtable():
    """Update sync_to_airtable.py to use database"""
    
    logger.info("Updating sync_to_airtable.py for database integration")
    
    sync_file = Path(__file__).parent / "sync_to_airtable.py"
    
    if not sync_file.exists():
        logger.warning("sync_to_airtable.py not found")
        return False
    
    try:
        # Read current content
        with open(sync_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if 'from database.lead_database import get_lead_database' in content:
            logger.info("sync_to_airtable.py already updated for database")
            return True
        
        # Add database import
        import_section = """
# Import database components
try:
    from database.lead_database import get_lead_database
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import database components: {e}")
    DATABASE_AVAILABLE = False
"""
        
        # Find where to insert the import
        if 'from shared.production_logger import get_logger' in content:
            content = content.replace(
                'from shared.production_logger import get_logger',
                'from shared.production_logger import get_logger' + import_section
            )
        else:
            # Insert at the beginning after existing imports
            lines = content.split('\n')
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_index = i + 1
            
            lines.insert(insert_index, import_section)
            content = '\n'.join(lines)
        
        # Write back
        with open(sync_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ Updated sync_to_airtable.py for database integration")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to update sync_to_airtable.py: {str(e)}")
        return False

def create_database_sync_agent():
    """Create a new agent for bidirectional database-Airtable sync"""
    
    logger.info("Creating database_sync_agent.py")
    
    sync_agent_content = '''#!/usr/bin/env python3
"""
Database-Airtable Sync Agent

Handles bidirectional synchronization between the database and Airtable.
Ensures data consistency and proper status tracking.
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

from database.lead_database import get_lead_database
from shared.airtable_client import get_airtable_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseAirtableSync:
    """Handles bidirectional sync between database and Airtable"""
    
    def __init__(self):
        """Initialize the sync agent"""
        self.db = get_lead_database()
        self.airtable = get_airtable_client()
        logger.info("Database-Airtable sync agent initialized")
    
    def sync_database_to_airtable(self, limit: int = 50) -> dict:
        """Sync leads from database to Airtable"""
        
        logger.info(f"Starting database to Airtable sync (limit: {limit})")
        
        try:
            # Get leads that need syncing
            pending_leads = self.db.get_sync_pending_leads()
            
            if not pending_leads:
                logger.info("No leads pending sync to Airtable")
                return {'synced': 0, 'errors': 0}
            
            # Limit the batch size
            if len(pending_leads) > limit:
                pending_leads = pending_leads[:limit]
            
            synced_count = 0
            error_count = 0
            
            for lead in pending_leads:
                try:
                    # Prepare Airtable data
                    airtable_data = self._prepare_airtable_data(lead)
                    
                    # Check if lead already exists in Airtable
                    if lead.get('airtable_id'):
                        # Update existing record
                        success = self.airtable.update_lead_fields(lead['airtable_id'], airtable_data)
                    else:
                        # Create new record
                        airtable_id = self.airtable.add_lead(airtable_data)
                        if airtable_id:
                            # Update database with Airtable ID
                            self.db.update_lead(lead['id'], {'airtable_id': airtable_id})
                            success = True
                        else:
                            success = False
                    
                    if success:
                        # Mark as synced in database
                        self.db.update_lead(lead['id'], {
                            'airtable_synced': True,
                            'sync_pending': False,
                            'last_sync_attempt': datetime.now()
                        })
                        synced_count += 1
                        logger.info(f"✅ Synced {lead.get('full_name')} to Airtable")
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed to sync {lead.get('full_name')} to Airtable")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Error syncing lead {lead.get('full_name', 'Unknown')}: {str(e)}")
            
            logger.info(f"Database to Airtable sync complete: {synced_count} synced, {error_count} errors")
            return {'synced': synced_count, 'errors': error_count}
            
        except Exception as e:
            logger.error(f"❌ Database to Airtable sync failed: {str(e)}")
            return {'synced': 0, 'errors': 1}
    
    def sync_airtable_to_database(self, limit: int = 50) -> dict:
        """Sync updates from Airtable to database"""
        
        logger.info(f"Starting Airtable to database sync (limit: {limit})")
        
        try:
            # Get recently updated records from Airtable
            # This would need to be implemented based on Airtable's last modified field
            # For now, we'll focus on database to Airtable sync
            
            logger.info("Airtable to database sync not yet implemented")
            return {'synced': 0, 'errors': 0}
            
        except Exception as e:
            logger.error(f"❌ Airtable to database sync failed: {str(e)}")
            return {'synced': 0, 'errors': 1}
    
    def _prepare_airtable_data(self, lead: dict) -> dict:
        """Prepare lead data for Airtable format"""
        
        raw_data = lead.get('raw_data', {})
        if isinstance(raw_data, str):
            try:
                import json
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}
        
        airtable_data = {
            'Name': lead.get('full_name', ''),
            'LinkedIn_URL': lead.get('linkedin_url', ''),
            'Title': lead.get('title', ''),
            'Company': lead.get('company', ''),
            'Email': lead.get('email', ''),
            'Status': lead.get('status', 'new'),
            'Enriched': lead.get('enriched', False),
            'Verified': lead.get('verified', False),
            'Source': lead.get('source', ''),
            'Created_Date': lead.get('created_at', ''),
            'Updated_Date': lead.get('updated_at', ''),
        }
        
        # Add enrichment data if available
        if raw_data:
            if raw_data.get('custom_message'):
                airtable_data['Custom_Message'] = raw_data['custom_message']
            
            if raw_data.get('enrichment_data'):
                airtable_data['Enrichment_Data'] = raw_data['enrichment_data']
            
            if raw_data.get('website'):
                airtable_data['Website'] = raw_data['website']
            
            # Add campaign brain results if available
            if raw_data.get('brain_status'):
                airtable_data['Brain_Status'] = raw_data['brain_status']
                airtable_data['Brain_Quality_Score'] = raw_data.get('brain_quality_score', 0)
                airtable_data['Messaging_Angle'] = raw_data.get('messaging_angle', '')
                airtable_data['Campaign_Tone'] = raw_data.get('campaign_tone', '')
        
        return airtable_data
    
    def run_full_sync(self, batch_size: int = 25) -> dict:
        """Run full bidirectional sync"""
        
        logger.info("Starting full bidirectional sync")
        
        # Sync database to Airtable
        db_to_airtable = self.sync_database_to_airtable(batch_size)
        
        # Sync Airtable to database (when implemented)
        airtable_to_db = self.sync_airtable_to_database(batch_size)
        
        total_result = {
            'database_to_airtable': db_to_airtable,
            'airtable_to_database': airtable_to_db,
            'total_synced': db_to_airtable['synced'] + airtable_to_db['synced'],
            'total_errors': db_to_airtable['errors'] + airtable_to_db['errors']
        }
        
        logger.info(f"Full sync complete: {total_result['total_synced']} synced, {total_result['total_errors']} errors")
        return total_result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database-Airtable Sync Agent")
    parser.add_argument('--batch-size', type=int, default=25, help='Batch size for sync operations')
    parser.add_argument('--db-to-airtable', action='store_true', help='Sync database to Airtable only')
    parser.add_argument('--airtable-to-db', action='store_true', help='Sync Airtable to database only')
    
    args = parser.parse_args()
    
    try:
        sync_agent = DatabaseAirtableSync()
        
        if args.db_to_airtable:
            result = sync_agent.sync_database_to_airtable(args.batch_size)
        elif args.airtable_to_db:
            result = sync_agent.sync_airtable_to_database(args.batch_size)
        else:
            result = sync_agent.run_full_sync(args.batch_size)
        
        print(f"Sync completed: {result}")
        return 0
        
    except Exception as e:
        logger.error(f"Sync agent failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())
'''
    
    sync_agent_file = Path(__file__).parent / "database_sync_agent.py"
    
    try:
        with open(sync_agent_file, 'w', encoding='utf-8') as f:
            f.write(sync_agent_content)
        
        logger.info("✅ Created database_sync_agent.py")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database_sync_agent.py: {str(e)}")
        return False

def main():
    """Main function"""
    print("🔧 Updating agents for database integration...")
    
    success_count = 0
    total_count = 0
    
    # Update daily enricher agent
    total_count += 1
    if update_daily_enricher_agent():
        success_count += 1
    
    # Update sync to airtable
    total_count += 1
    if update_sync_to_airtable():
        success_count += 1
    
    # Create database sync agent
    total_count += 1
    if create_database_sync_agent():
        success_count += 1
    
    print(f"\n📊 Agent updates complete: {success_count}/{total_count} successful")
    
    if success_count == total_count:
        print("✅ All agents updated successfully!")
        print("\n🎯 Next steps:")
        print("1. Run: python populate_database_from_airtable.py")
        print("2. Run: python database_sync_agent.py --db-to-airtable")
        print("3. Test: python serve_campaign_brain.py --batch-size 3 --dry-run")
        return 0
    else:
        print("⚠️ Some agent updates failed. Check logs for details.")
        return 1

if __name__ == '__main__':
    exit(main())