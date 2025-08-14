#!/usr/bin/env python3
"""
Airtable Synchronization

Consolidated Airtable sync system for bidirectional synchronization between
the local database and Airtable.
"""

import os
import time
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import quote

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import get_lead_database, Lead
from config.settings import get_settings

logger = logging.getLogger('airtable-sync')

class AirtableSync:
    """
    Airtable synchronization manager for bidirectional sync operations.
    """
    
    def __init__(self):
        """Initialize Airtable sync manager."""
        self.settings = get_settings()
        self.db = get_lead_database()
        
        # Airtable configuration
        self.api_key = self.settings.airtable.api_key
        self.base_id = self.settings.airtable.base_id
        self.table_name = self.settings.airtable.table_name
        
        # API endpoints
        encoded_table_name = quote(self.table_name)
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{encoded_table_name}"
        
        # Headers for API requests
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests (5 requests/second)
        
        # Initialize engagement defaults manager if enabled
        self.engagement_defaults_manager = None
        if self.settings.engagement_defaults.enabled:
            try:
                # Try relative import first, then absolute
                try:
                    from .engagement_defaults import EngagementDefaultsManager
                except ImportError:
                    from engagement_defaults import EngagementDefaultsManager
                
                self.engagement_defaults_manager = EngagementDefaultsManager()
                logger.info("🎯 Engagement defaults manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize engagement defaults manager: {e}")
        
        logger.info("📊 Airtable sync manager initialized")
        logger.info(f"📋 Target table: {self.table_name}")
    
    def sync_leads_to_airtable(self, leads: List[Lead] = None, force: bool = False) -> Dict[str, Any]:
        """
        Sync leads from database to Airtable.
        
        Args:
            leads: Optional list of specific leads to sync
            force: Force sync even if already synced
            
        Returns:
            Dictionary with sync results
        """
        logger.info("📤 Starting database to Airtable sync")
        
        try:
            # Get leads to sync
            if leads is None:
                # Get leads that need syncing
                filters = {}
                if not force:
                    filters['sync_status'] = 'pending'
                
                leads = self.db.search_leads(filters, limit=100)
            
            if not leads:
                logger.info("✅ No leads need syncing to Airtable")
                return {
                    'success': True,
                    'synced_count': 0,
                    'failed_count': 0,
                    'errors': [],
                    'defaults_applied': {'count': 0, 'fields_updated': [], 'errors': []}
                }
            
            logger.info(f"📋 Syncing {len(leads)} leads to Airtable")
            
            # Process in batches (Airtable limit is 10 records per request)
            batch_size = 10
            synced_count = 0
            failed_count = 0
            errors = []
            all_synced_records = []
            
            for i in range(0, len(leads), batch_size):
                batch = leads[i:i + batch_size]
                
                try:
                    batch_result = self._sync_batch_to_airtable(batch)
                    synced_count += batch_result['synced']
                    failed_count += batch_result['failed']
                    errors.extend(batch_result['errors'])
                    
                    # Collect synced records for defaults application
                    if 'synced_records' in batch_result:
                        all_synced_records.extend(batch_result['synced_records'])
                    
                    logger.info(f"✅ Batch {i//batch_size + 1}: {batch_result['synced']} synced, {batch_result['failed']} failed")
                    
                    # Rate limiting between batches
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Batch {i//batch_size + 1} failed: {str(e)}")
                    failed_count += len(batch)
                    errors.append(f"Batch {i//batch_size + 1}: {str(e)}")
            
            # Log sync to database
            self._log_sync_operation('to_airtable', synced_count, failed_count, errors)
            
            logger.info(f"📊 Airtable sync completed: {synced_count} synced, {failed_count} failed")
            
            # Apply engagement defaults if enabled and we have synced records
            defaults_result = {'count': 0, 'fields_updated': [], 'errors': []}
            if all_synced_records and self.engagement_defaults_manager:
                try:
                    defaults_result = self._apply_engagement_defaults_after_sync(all_synced_records)
                except Exception as e:
                    logger.error(f"❌ Failed to apply engagement defaults: {str(e)}")
                    defaults_result['errors'].append(str(e))
            
            return {
                'success': failed_count == 0,
                'synced_count': synced_count,
                'failed_count': failed_count,
                'errors': errors,
                'defaults_applied': defaults_result
            }
            
        except Exception as e:
            logger.error(f"❌ Airtable sync failed: {str(e)}")
            return {
                'success': False,
                'synced_count': 0,
                'failed_count': 0,
                'errors': [str(e)],
                'defaults_applied': {'count': 0, 'fields_updated': [], 'errors': []}
            }
    
    def sync_updates_from_airtable(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync updates from Airtable to database (DAILY ONLY - 6:00 AM).
        This provides updated user interface data from Airtable.
        
        Args:
            force: Force sync regardless of last sync time
            
        Returns:
            Dictionary with sync results
        """
        logger.info("📥 Starting DAILY Airtable to database sync (UI updates)")
        
        try:
            # Get records from Airtable that have been modified recently
            cutoff_time = self._get_sync_cutoff_time(force)
            airtable_records = self._get_airtable_records(modified_since=cutoff_time)
            
            if not airtable_records:
                logger.info("✅ No updated records in Airtable")
                return {
                    'success': True,
                    'synced_count': 0,
                    'failed_count': 0,
                    'errors': []
                }
            
            logger.info(f"📋 Processing {len(airtable_records)} updated records from Airtable")
            
            synced_count = 0
            failed_count = 0
            errors = []
            
            for record in airtable_records:
                try:
                    success = self._update_lead_from_airtable(record)
                    if success:
                        synced_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Failed to update lead from Airtable record {record.get('id')}: {str(e)}")
                    failed_count += 1
                    errors.append(f"Record {record.get('id')}: {str(e)}")
            
            # Log sync to database
            self._log_sync_operation('from_airtable', synced_count, failed_count, errors)
            
            logger.info(f"📊 Airtable to database sync completed: {synced_count} synced, {failed_count} failed")
            
            return {
                'success': failed_count == 0,
                'synced_count': synced_count,
                'failed_count': failed_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"❌ Airtable to database sync failed: {str(e)}")
            return {
                'success': False,
                'synced_count': 0,
                'failed_count': 0,
                'errors': [str(e)]
            }
    
    def _sync_batch_to_airtable(self, batch: List[Lead]) -> Dict[str, Any]:
        """
        Sync a batch of leads to Airtable.
        
        Args:
            batch: List of leads to sync
            
        Returns:
            Dictionary with batch sync results
        """
        # Apply rate limiting
        self._apply_rate_limiting()
        
        # Format records for Airtable
        records = []
        for lead in batch:
            try:
                airtable_record = self._format_lead_for_airtable(lead)
                records.append({'fields': airtable_record})
            except Exception as e:
                logger.warning(f"⚠️ Failed to format lead {lead.name}: {str(e)}")
                continue
        
        if not records:
            return {'synced': 0, 'failed': len(batch), 'errors': ['No valid records to sync'], 'synced_records': []}
        
        # Send to Airtable
        try:
            data = {'records': records}
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                created_records = result.get('records', [])
                
                # Update database with Airtable IDs
                synced_count = 0
                synced_records = []
                for i, airtable_record in enumerate(created_records):
                    if i < len(batch):
                        lead = batch[i]
                        airtable_id = airtable_record['id']
                        success = self.db.update_lead(lead.id, {
                            'airtable_id': airtable_id,
                            'airtable_synced': datetime.now().isoformat(),
                            'sync_status': 'synced'
                        })
                        
                        if success:
                            synced_count += 1
                            # Update the lead object with the Airtable ID for defaults application
                            lead.airtable_id = airtable_id
                            synced_records.append(lead)
                
                return {
                    'synced': synced_count,
                    'failed': len(batch) - synced_count,
                    'errors': [],
                    'synced_records': synced_records
                }
            
            else:
                error_msg = f"Airtable API error: {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                return {
                    'synced': 0,
                    'failed': len(batch),
                    'errors': [error_msg],
                    'synced_records': []
                }
                
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'synced': 0,
                'failed': len(batch),
                'errors': [error_msg],
                'synced_records': []
            }
    
    def _format_lead_for_airtable(self, lead: Lead) -> Dict[str, Any]:
        """
        Format lead data for Airtable.
        
        Args:
            lead: Lead instance
            
        Returns:
            Dictionary formatted for Airtable
        """
        # Map to Airtable field names (only use fields that actually exist in Airtable)
        airtable_record = {
            'Full Name': lead.name or '',
            'LinkedIn URL': lead.linkedin_url or '',
            'Job Title': getattr(lead, 'title', '') or '',
            'Company': getattr(lead, 'company', '') or '',
            'Needs Enrichment': not lead.enriched,
            'Date Scraped': self._format_date_for_airtable(lead.scraped_at),
        }
        
        # Add email if available
        if lead.email:
            airtable_record['Email'] = lead.email
        
        # Add website if available (extracted from SerpAPI)
        if hasattr(lead, 'website') and lead.website:
            airtable_record['Website'] = lead.website
            logger.debug(f"✅ Adding website to Airtable record: {lead.website}")
        
        # Remove empty/None fields
        return {k: v for k, v in airtable_record.items() if v is not None and v != ''}
    
    def _format_date_for_airtable(self, date_string: Optional[str]) -> Optional[str]:
        """Format ISO date string for Airtable (YYYY-MM-DD)."""
        if not date_string:
            return None
        
        try:
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return None
    
    def _get_airtable_records(self, modified_since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get records from Airtable.
        
        Args:
            modified_since: Only get records modified since this time
            
        Returns:
            List of Airtable records
        """
        try:
            # Apply rate limiting
            self._apply_rate_limiting()
            
            # Build query parameters
            params = {}
            if modified_since:
                # Airtable uses a different format for filtering by date
                # This is a simplified implementation
                pass
            
            response = requests.get(self.base_url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('records', [])
            else:
                logger.error(f"❌ Failed to get Airtable records: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to get Airtable records: {str(e)}")
            return []
    
    def _update_lead_from_airtable(self, airtable_record: Dict[str, Any]) -> bool:
        """
        Update a lead in the database from an Airtable record.
        
        Args:
            airtable_record: Airtable record data
            
        Returns:
            True if update successful
        """
        try:
            fields = airtable_record.get('fields', {})
            airtable_id = airtable_record.get('id')
            
            # Find existing lead by Airtable ID or email
            lead = None
            
            # First try to find by Airtable ID
            if airtable_id:
                leads = self.db.search_leads({'airtable_id': airtable_id}, limit=1)
                if leads:
                    lead = leads[0]
            
            # If not found, try by email
            if not lead and fields.get('Email'):
                leads = self.db.search_leads({'email': fields['Email']}, limit=1)
                if leads:
                    lead = leads[0]
            
            if not lead:
                # Create new lead if not found
                lead_data = self._format_airtable_for_lead(fields, airtable_id)
                lead_id = self.db.create_lead(lead_data)
                logger.info(f"✅ Created new lead from Airtable: {fields.get('Full Name', 'Unknown')}")
                return True
            else:
                # Update existing lead
                updates = self._format_airtable_for_lead(fields, airtable_id)
                success = self.db.update_lead(lead.id, updates)
                if success:
                    logger.info(f"✅ Updated lead from Airtable: {lead.name}")
                return success
                
        except Exception as e:
            logger.error(f"❌ Failed to update lead from Airtable: {str(e)}")
            return False
    
    def _format_airtable_for_lead(self, fields: Dict[str, Any], airtable_id: str) -> Dict[str, Any]:
        """
        Format Airtable fields for lead database.
        
        Args:
            fields: Airtable record fields
            airtable_id: Airtable record ID
            
        Returns:
            Dictionary formatted for lead database
        """
        lead_data = {
            'name': fields.get('Full Name', ''),
            'email': fields.get('Email', ''),
            'linkedin_url': fields.get('LinkedIn URL', ''),
            'title': fields.get('Job Title', ''),
            'company': fields.get('Company', ''),
            'enriched': not fields.get('Needs Enrichment', True),
            'scraped_at': fields.get('Date Scraped', ''),
            'airtable_id': airtable_id,
            'airtable_synced': datetime.now().isoformat(),
            'sync_status': 'synced'
        }
        
        # Add website if available
        if fields.get('Website'):
            lead_data['website'] = fields['Website']
            logger.debug(f"✅ Adding website from Airtable: {fields['Website']}")
        
        return lead_data
    
    def _get_sync_cutoff_time(self, force: bool) -> Optional[datetime]:
        """Get cutoff time for incremental sync."""
        if force:
            return None
        
        # Get last successful sync time from database
        # For now, use 24 hours ago as default
        return datetime.now() - timedelta(hours=24)
    
    def _apply_rate_limiting(self):
        """Apply rate limiting for Airtable API requests."""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _log_sync_operation(self, operation: str, synced_count: int, failed_count: int, errors: List[str]):
        """Log sync operation to database."""
        try:
            # Log to sync_log table
            query = """
                INSERT INTO sync_log (operation, status, error_message, sync_timestamp)
                VALUES (?, ?, ?, ?)
            """
            
            status = 'success' if failed_count == 0 else 'failed'
            error_message = '; '.join(errors) if errors else None
            
            self.db.db.execute_update(query, (operation, status, error_message, datetime.now().isoformat()))
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to log sync operation: {str(e)}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get synchronization status and statistics.
        
        Returns:
            Dictionary with sync status information
        """
        try:
            # Get sync statistics from database
            cursor = self.db.db.execute_query("""
                SELECT 
                    operation,
                    status,
                    COUNT(*) as count,
                    MAX(sync_timestamp) as last_sync
                FROM sync_log 
                WHERE sync_timestamp >= datetime('now', '-7 days')
                GROUP BY operation, status
                ORDER BY last_sync DESC
            """)
            
            sync_stats = {}
            for row in cursor.fetchall():
                operation = row[0]
                status = row[1]
                count = row[2]
                last_sync = row[3]
                
                if operation not in sync_stats:
                    sync_stats[operation] = {}
                
                sync_stats[operation][status] = {
                    'count': count,
                    'last_sync': last_sync
                }
            
            # Get pending sync count
            pending_leads = self.db.search_leads({'sync_status': 'pending'})
            
            return {
                'sync_statistics': sync_stats,
                'pending_sync_count': len(pending_leads),
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get sync status: {str(e)}")
            return {
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }
    
    def _apply_engagement_defaults_after_sync(self, synced_leads: List[Lead]) -> Dict[str, Any]:
        """
        Apply engagement defaults to leads after they've been synced to Airtable.
        
        Args:
            synced_leads: List of leads that were successfully synced
            
        Returns:
            Dictionary with defaults application results
        """
        if not self.engagement_defaults_manager:
            return {'count': 0, 'fields_updated': [], 'errors': ['Engagement defaults manager not available']}
        
        logger.info(f"🎯 Applying engagement defaults to {len(synced_leads)} synced leads")
        
        # Prepare lead records for defaults application
        lead_records = []
        for lead in synced_leads:
            if hasattr(lead, 'airtable_id') and lead.airtable_id:
                lead_records.append({
                    'lead_id': str(lead.id),
                    'airtable_record_id': lead.airtable_id
                })
        
        if not lead_records:
            logger.warning("⚠️ No leads have Airtable IDs for defaults application")
            return {'count': 0, 'fields_updated': [], 'errors': ['No leads with Airtable IDs']}
        
        # Apply defaults using the engagement defaults manager
        try:
            result = self.engagement_defaults_manager.apply_defaults_to_multiple_leads(lead_records)
            
            logger.info(f"🎯 Engagement defaults applied: {result['updated_count']} updated, "
                       f"{result['skipped_count']} skipped, {result['failed_count']} failed")
            
            return {
                'count': result['updated_count'],
                'fields_updated': result['fields_updated'],
                'errors': result['errors'],
                'skipped_count': result['skipped_count'],
                'failed_count': result['failed_count']
            }
            
        except Exception as e:
            logger.error(f"❌ Exception applying engagement defaults: {str(e)}")
            return {
                'count': 0,
                'fields_updated': [],
                'errors': [str(e)]
            }
    
    def sync_leads_to_airtable_with_defaults(self, leads: List[Lead] = None, force: bool = False) -> Dict[str, Any]:
        """
        Sync leads to Airtable and apply engagement defaults.
        This is a convenience method that combines sync and defaults application.
        
        Args:
            leads: Optional list of specific leads to sync
            force: Force sync even if already synced
            
        Returns:
            Dictionary with sync and defaults results
        """
        logger.info("📤 Starting database to Airtable sync with engagement defaults")
        
        # Perform the regular sync
        sync_result = self.sync_leads_to_airtable(leads, force)
        
        # The sync method already applies defaults, so we just return the result
        logger.info(f"📊 Sync with defaults completed: {sync_result['synced_count']} synced, "
                   f"{sync_result['defaults_applied']['count']} defaults applied")
        
        return sync_result


# Convenience functions
def sync_to_airtable(leads: List[Lead] = None, force: bool = False) -> Dict[str, Any]:
    """
    Sync leads to Airtable (convenience function).
    
    Args:
        leads: Optional list of specific leads to sync
        force: Force sync even if already synced
        
    Returns:
        Sync result dictionary
    """
    sync_manager = AirtableSync()
    return sync_manager.sync_leads_to_airtable(leads, force)

def sync_to_airtable_with_defaults(leads: List[Lead] = None, force: bool = False) -> Dict[str, Any]:
    """
    Sync leads to Airtable with engagement defaults application (convenience function).
    
    Args:
        leads: Optional list of specific leads to sync
        force: Force sync even if already synced
        
    Returns:
        Sync result dictionary with defaults application results
    """
    sync_manager = AirtableSync()
    return sync_manager.sync_leads_to_airtable_with_defaults(leads, force)

def sync_from_airtable(force: bool = False) -> Dict[str, Any]:
    """
    Sync updates from Airtable (convenience function).
    
    Args:
        force: Force sync regardless of last sync time
        
    Returns:
        Sync result dictionary
    """
    sync_manager = AirtableSync()
    return sync_manager.sync_updates_from_airtable(force)

def get_sync_status() -> Dict[str, Any]:
    """
    Get sync status (convenience function).
    
    Returns:
        Sync status dictionary
    """
    sync_manager = AirtableSync()
    return sync_manager.get_sync_status()


if __name__ == "__main__":
    # Test Airtable sync
    sync_manager = AirtableSync()
    
    print("🧪 Testing Airtable Sync...")
    
    # Test sync to Airtable
    result = sync_manager.sync_leads_to_airtable()
    print(f"Sync to Airtable result: {result}")
    
    # Test sync status
    status = sync_manager.get_sync_status()
    print(f"Sync status: {status}")
    
    print("✅ Airtable sync test completed")