#!/usr/bin/env python3
"""
Updated Sync Leads to Airtable Agent
Syncs scraped and enriched leads to Airtable using the new database API
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
from urllib.parse import quote
from typing import List, Dict, Any, Optional

# Import new database components
from lead_database import LeadDatabase
from airtable_sync_manager import AirtableSyncManager, SyncSummary
from database_logger import database_logger, log_database_event

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('airtable-sync-updated')


class DatabaseAirtableSync:
    """Updated Airtable sync agent using the new database API."""
    
    def __init__(self):
        """Initialize the sync agent with database and Airtable connections."""
        try:
            # Initialize database connection
            self.db = LeadDatabase()
            logger.info("✅ Database connection established")
            
            # Initialize Airtable sync manager
            self.airtable_sync = AirtableSyncManager()
            logger.info("✅ Airtable sync manager initialized")
            
            # Airtable API configuration
            self.api_key = os.getenv('AIRTABLE_API_KEY')
            self.base_id = os.getenv('AIRTABLE_BASE_ID')
            self.table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
            
            if not all([self.api_key, self.base_id]):
                raise ValueError("Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID")
            
            logger.info(f"📊 Airtable sync initialized for table: {self.table_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize sync agent: {e}")
            raise
    
    def get_leads_to_sync(self) -> List[Dict[str, Any]]:
        """
        Get leads from database that need to be synced to Airtable.
        
        Returns:
            List of lead dictionaries that need syncing
        """
        try:
            # Get leads pending sync from database
            pending_leads = self.db.get_sync_pending_leads()
            
            logger.info(f"📋 Found {len(pending_leads)} leads pending sync to Airtable")
            
            # Log the sync operation start
            log_database_event("sync_operation", {}, {
                "sync_type": "to_airtable_preparation",
                "leads_to_sync": len(pending_leads),
                "success": True
            }, {
                "sync_type": "to_airtable",
                "sync_details": {"preparation": True},
                "leads_processed": [{"id": lead.get("id", ""), "name": lead.get("full_name", "")} 
                                  for lead in pending_leads[:5]]  # Log first 5 for reference
            })
            
            return pending_leads
            
        except Exception as e:
            logger.error(f"❌ Error getting leads to sync: {e}")
            
            # Log error
            log_database_event("sync_operation", {}, {
                "sync_type": "to_airtable_preparation",
                "success": False,
                "error": str(e)
            }, {
                "sync_type": "to_airtable",
                "sync_details": {"preparation": True}
            })
            
            return []
    
    def format_lead_for_airtable(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format lead data for Airtable using correct field names.
        
        Args:
            lead: Lead data from database
            
        Returns:
            Formatted data for Airtable
        """
        # Map lead fields to exact Airtable field names
        airtable_record = {
            'Full Name': lead.get('full_name') or lead.get('name', ''),
            'Company': lead.get('company', ''),
            'Job Title': lead.get('title', ''),
            'Email': lead.get('email', ''),
            'LinkedIn URL': lead.get('linkedin_url', ''),
            'Location': lead.get('location', ''),
            'Industry': lead.get('industry', ''),
            'Company Size': lead.get('company_size', ''),
            'Verified': lead.get('verified', False),
            'Enriched': lead.get('enriched', False),
            'Needs Enrichment': lead.get('needs_enrichment', True),
            'Status': lead.get('status', 'new'),
            'Source': lead.get('source', 'Database'),
            'Date Scraped': self.format_date_for_airtable(lead.get('scraped_at')),
            'Date Enriched': self.format_date_for_airtable(lead.get('enriched_at')) if lead.get('enriched') else None
        }
        
        # Remove empty/None fields
        return {k: v for k, v in airtable_record.items() if v is not None and v != ''}
    
    def format_date_for_airtable(self, date_value: Any) -> Optional[str]:
        """
        Format date value to YYYY-MM-DD for Airtable.
        
        Args:
            date_value: Date value (string, datetime, or None)
            
        Returns:
            Formatted date string or None
        """
        if not date_value:
            return None
        
        try:
            if isinstance(date_value, str):
                # Parse ISO format and return just the date part
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            elif hasattr(date_value, 'strftime'):
                # datetime object
                return date_value.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"⚠️ Could not format date {date_value}: {e}")
        
        return None
    
    def sync_leads_to_airtable_direct(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync leads directly to Airtable API (fallback method).
        
        Args:
            leads: List of leads to sync
            
        Returns:
            Sync results dictionary
        """
        if not leads:
            return {"success": True, "synced_count": 0, "failed_count": 0, "errors": []}
        
        # Airtable API endpoint
        encoded_table_name = quote(self.table_name)
        url = f"https://api.airtable.com/v0/{self.base_id}/{encoded_table_name}"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Process in batches of 10 (Airtable limit)
        batch_size = 10
        synced_count = 0
        failed_count = 0
        errors = []
        
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            
            try:
                # Format records for Airtable
                records = []
                for lead in batch:
                    formatted_lead = self.format_lead_for_airtable(lead)
                    records.append({'fields': formatted_lead})
                
                # Send to Airtable
                data = {'records': records}
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    created_records = result.get('records', [])
                    synced_count += len(created_records)
                    
                    logger.info(f"✅ Synced batch {i//batch_size + 1}: {len(created_records)} records")
                    
                    # Update database with Airtable IDs
                    for j, lead in enumerate(batch):
                        if j < len(created_records):
                            airtable_id = created_records[j]['id']
                            self.db.update_lead(lead['id'], {
                                'airtable_id': airtable_id,
                                'airtable_synced': True,
                                'sync_pending': False,
                                'last_sync_attempt': datetime.now().isoformat()
                            })
                
                else:
                    error_msg = f"Airtable API error: {response.status_code} - {response.text}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    failed_count += len(batch)
                
            except Exception as e:
                error_msg = f"Batch sync error: {str(e)}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
                failed_count += len(batch)
            
            # Rate limiting
            time.sleep(1)
        
        return {
            "success": failed_count == 0,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "errors": errors
        }
    
    def sync_leads_using_manager(self, leads: List[Dict[str, Any]]) -> SyncSummary:
        """
        Sync leads using the AirtableSyncManager.
        
        Args:
            leads: List of leads to sync
            
        Returns:
            SyncSummary object with results
        """
        try:
            # Extract lead IDs for the sync manager
            lead_ids = [lead['id'] for lead in leads if lead.get('id')]
            
            if not lead_ids:
                logger.warning("⚠️ No valid lead IDs found for sync")
                return SyncSummary()
            
            # Use the sync manager to sync leads
            summary = self.airtable_sync.sync_to_airtable(lead_ids)
            
            logger.info(f"✅ Sync manager completed: {summary.successful_syncs} successful, {summary.failed_syncs} failed")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error using sync manager: {e}")
            # Return empty summary on error
            summary = SyncSummary()
            summary.errors.append(f"Sync manager error: {str(e)}")
            return summary
    
    def run_sync_process(self, use_sync_manager: bool = True) -> Dict[str, Any]:
        """
        Run the complete sync process.
        
        Args:
            use_sync_manager: Whether to use AirtableSyncManager (True) or direct API (False)
            
        Returns:
            Sync results dictionary
        """
        start_time = time.time()
        
        try:
            logger.info("🚀 Starting Airtable sync process...")
            
            # Get leads to sync
            leads = self.get_leads_to_sync()
            
            if not leads:
                logger.info("✅ No leads to sync - all up to date")
                return {
                    "success": True,
                    "total_leads": 0,
                    "synced_count": 0,
                    "failed_count": 0,
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "method": "none_needed"
                }
            
            # Choose sync method
            if use_sync_manager:
                logger.info("📊 Using AirtableSyncManager for sync...")
                summary = self.sync_leads_using_manager(leads)
                
                results = {
                    "success": summary.failed_syncs == 0,
                    "total_leads": summary.total_leads,
                    "synced_count": summary.successful_syncs,
                    "failed_count": summary.failed_syncs,
                    "created_records": summary.created_records,
                    "updated_records": summary.updated_records,
                    "errors": summary.errors,
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "method": "sync_manager"
                }
            else:
                logger.info("🔗 Using direct Airtable API for sync...")
                direct_results = self.sync_leads_to_airtable_direct(leads)
                
                results = {
                    "success": direct_results["success"],
                    "total_leads": len(leads),
                    "synced_count": direct_results["synced_count"],
                    "failed_count": direct_results["failed_count"],
                    "errors": direct_results["errors"],
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "method": "direct_api"
                }
            
            # Log final results
            if results["success"]:
                logger.info(f"✅ Sync completed successfully: {results['synced_count']}/{results['total_leads']} leads synced")
            else:
                logger.error(f"❌ Sync completed with errors: {results['synced_count']}/{results['total_leads']} leads synced")
                for error in results.get("errors", []):
                    logger.error(f"   - {error}")
            
            return results
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Sync process failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "total_leads": 0,
                "synced_count": 0,
                "failed_count": 0,
                "errors": [error_msg],
                "execution_time_ms": execution_time_ms,
                "method": "error"
            }
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Get sync statistics from the database.
        
        Returns:
            Dictionary with sync statistics
        """
        try:
            # Get database statistics
            db_stats = self.db.get_database_stats()
            
            # Get sync manager statistics
            sync_stats = self.airtable_sync.get_sync_statistics()
            
            return {
                "database_stats": db_stats,
                "sync_stats": sync_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting sync statistics: {e}")
            return {"error": str(e)}


def sync_leads_to_airtable(use_sync_manager: bool = True) -> bool:
    """
    Main function to sync leads to Airtable using the new database API.
    
    Args:
        use_sync_manager: Whether to use AirtableSyncManager or direct API
        
    Returns:
        True if sync successful, False otherwise
    """
    try:
        logger.info("📊 Starting database-powered Airtable sync...")
        
        # Initialize sync agent
        sync_agent = DatabaseAirtableSync()
        
        # Run sync process
        results = sync_agent.run_sync_process(use_sync_manager)
        
        # Print summary
        logger.info("=" * 50)
        logger.info("📊 SYNC SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Method: {results.get('method', 'unknown')}")
        logger.info(f"Total leads: {results.get('total_leads', 0)}")
        logger.info(f"Successfully synced: {results.get('synced_count', 0)}")
        logger.info(f"Failed: {results.get('failed_count', 0)}")
        logger.info(f"Execution time: {results.get('execution_time_ms', 0):.1f}ms")
        logger.info(f"Success rate: {(results.get('synced_count', 0) / max(results.get('total_leads', 1), 1) * 100):.1f}%")
        
        if results.get("errors"):
            logger.info("Errors:")
            for error in results["errors"]:
                logger.info(f"  - {error}")
        
        logger.info("=" * 50)
        
        return results.get("success", False)
        
    except Exception as e:
        logger.error(f"❌ Sync process failed: {str(e)}")
        return False


def main():
    """Main function with command line options."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync leads to Airtable using database API')
    parser.add_argument('--method', choices=['manager', 'direct'], default='manager',
                       help='Sync method: manager (use AirtableSyncManager) or direct (direct API)')
    parser.add_argument('--stats', action='store_true',
                       help='Show sync statistics only')
    
    args = parser.parse_args()
    
    if args.stats:
        # Show statistics only
        try:
            sync_agent = DatabaseAirtableSync()
            stats = sync_agent.get_sync_statistics()
            print(json.dumps(stats, indent=2))
            return 0
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return 1
    
    # Run sync
    use_sync_manager = args.method == 'manager'
    success = sync_leads_to_airtable(use_sync_manager)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())