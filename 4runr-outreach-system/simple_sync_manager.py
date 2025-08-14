"""
Simple Airtable Sync Manager - Working version

This is a simplified, working version of the sync manager to replace the broken one.
"""

import time
import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from lead_database import LeadDatabase
from shared.airtable_client import AirtableClient


class SyncStatus(Enum):
    """Status of sync operations."""
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    lead_id: str
    airtable_id: Optional[str] = None
    status: SyncStatus = SyncStatus.FAILED
    error_message: Optional[str] = None


class SimpleSyncManager:
    """
    Simple, working Airtable sync manager.
    """
    
    def __init__(self, db_path: str = "data/leads_cache.db"):
        """Initialize the sync manager."""
        self.db = LeadDatabase(db_path)
        self.airtable = AirtableClient()
        
        # Field mappings - based on actual Airtable fields
        self.field_mapping = {
            'full_name': 'Full Name',
            'email': 'Email',
            'company': 'Company',
            'linkedin_url': 'LinkedIn URL',
            'website': 'Website',
            'status': 'Engagement_Status',
            'source': 'Business_Type'
        }
    
    def sync_to_airtable(self, lead_ids: Optional[List[str]] = None) -> List[SyncResult]:
        """
        Sync leads from database to Airtable.
        
        Args:
            lead_ids: Specific lead IDs to sync (if None, sync all pending)
            
        Returns:
            List of sync results
        """
        results = []
        
        try:
            # Get leads to sync
            if lead_ids:
                leads_to_sync = []
                for lead_id in lead_ids:
                    lead = self.db.get_lead(lead_id)
                    if lead:
                        leads_to_sync.append(lead)
            else:
                leads_to_sync = self.db.get_sync_pending_leads()
            
            print(f"Syncing {len(leads_to_sync)} leads to Airtable...")
            
            for lead in leads_to_sync:
                result = self._sync_single_lead(lead)
                results.append(result)
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            
            return results
            
        except Exception as e:
            print(f"Sync failed: {e}")
            return results
    
    def _sync_single_lead(self, lead: Dict[str, Any]) -> SyncResult:
        """Sync a single lead to Airtable."""
        result = SyncResult(lead_id=lead.get('id', ''))
        
        try:
            # Map database fields to Airtable fields
            airtable_fields = self._map_to_airtable_fields(lead)
            
            # Create record in Airtable
            airtable_id = self.airtable.create_lead(airtable_fields)
            
            if airtable_id:
                result.status = SyncStatus.SUCCESS
                result.airtable_id = airtable_id
                
                # Update database with Airtable ID
                self.db.update_lead(lead['id'], {
                    'airtable_id': airtable_id,
                    'airtable_synced': True,
                    'sync_pending': False,
                    'last_sync_attempt': datetime.datetime.now().isoformat()
                })
                
                print(f"✅ Synced lead {lead.get('full_name', 'Unknown')} to Airtable")
            else:
                result.error_message = "Failed to create record in Airtable"
                print(f"❌ Failed to sync lead {lead.get('full_name', 'Unknown')}")
                
        except Exception as e:
            result.error_message = str(e)
            print(f"❌ Error syncing lead {lead.get('full_name', 'Unknown')}: {e}")
        
        return result
    
    def _map_to_airtable_fields(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Map database fields to Airtable field names."""
        airtable_fields = {}
        
        for db_field, airtable_field in self.field_mapping.items():
            if db_field in lead and lead[db_field] is not None:
                value = lead[db_field]
                
                # Handle boolean fields
                if isinstance(value, bool):
                    value = 'Yes' if value else 'No'
                
                # Handle status field - use valid Airtable status
                if db_field == 'status':
                    if value == 'new':
                        value = 'Needs Review'  # Use a valid Airtable status
                    elif value not in ['Needs Review', 'Sent']:
                        value = 'Needs Review'  # Default to valid status
                
                airtable_fields[airtable_field] = value
        
        # Add sync tracking
        airtable_fields['Date Scraped'] = datetime.datetime.now().strftime('%Y-%m-%d')
        
        return airtable_fields
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get sync statistics."""
        try:
            db_stats = self.db.get_database_stats()
            sync_pending = self.db.get_sync_pending_leads()
            
            return {
                'total_leads': db_stats.get('total_leads', 0),
                'pending_syncs': len(sync_pending),
                'synced_leads': db_stats.get('total_leads', 0) - len(sync_pending),
                'last_check': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
