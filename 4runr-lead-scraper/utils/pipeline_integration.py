#!/usr/bin/env python3
"""
Pipeline Integration Module

Handles the integration of Google Website Scraper with the existing lead processing pipeline.
Implements conditional execution logic and Airtable field updates.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from database.models import get_lead_database, Lead
from sync.airtable_sync import AirtableSync
from utils.google_scraper_integration import GoogleScraperPipeline

logger = logging.getLogger('pipeline-integration')

class LeadPipelineManager:
    """
    Manages the complete lead processing pipeline with Google scraper integration.
    """
    
    def __init__(self, enable_google_scraper: bool = True):
        """
        Initialize pipeline manager.
        
        Args:
            enable_google_scraper: Enable Google website scraper fallback
        """
        self.db = get_lead_database()
        self.airtable_sync = AirtableSync()
        self.enable_google_scraper = enable_google_scraper
        
        if self.enable_google_scraper:
            self.google_scraper = GoogleScraperPipeline()
        
        logger.info("🔧 Lead Pipeline Manager initialized")
        logger.info(f"⚙️ Google scraper: {'Enabled' if enable_google_scraper else 'Disabled'}")
    
    def process_lead_with_website_fallback(self, lead: Lead) -> Dict[str, Any]:
        """
        Process a single lead with Google website scraper fallback.
        
        Args:
            lead: Lead instance to process
            
        Returns:
            Processing results dictionary
        """
        logger.info(f"🔧 Processing lead: {lead.name}")
        
        result = {
            'lead_id': lead.id,
            'lead_name': lead.name,
            'original_website': getattr(lead, 'website', None),
            'website_discovered': False,
            'google_search_performed': False,
            'airtable_updated': False,
            'enrichment_status': None,
            'errors': []
        }
        
        try:
            # Check if lead needs website discovery
            if self._lead_needs_website_discovery(lead):
                logger.info(f"🔍 Lead {lead.name} needs website discovery")
                
                if self.enable_google_scraper:
                    # Perform Google search
                    website = self.google_scraper._search_single_lead_website(lead.name, lead.company)
                    result['google_search_performed'] = True
                    
                    if website:
                        logger.info(f"✅ Found website for {lead.name}: {website}")
                        result['website_discovered'] = True
                        
                        # Update database
                        update_success = self._update_lead_with_website(lead.id, website)
                        
                        if update_success:
                            # Update Airtable
                            airtable_success = self._update_airtable_with_website(lead.id, website)
                            result['airtable_updated'] = airtable_success
                            
                            result['enrichment_status'] = 'Website Found'
                        else:
                            result['errors'].append('Failed to update database')
                    else:
                        logger.info(f"❌ No website found for {lead.name}")
                        
                        # Set enrichment status to indicate failure
                        self._set_enrichment_status_failed(lead.id)
                        result['enrichment_status'] = 'Failed - No Website'
                else:
                    logger.info(f"⏭️ Google scraper disabled for {lead.name}")
                    result['enrichment_status'] = 'Skipped - Google Scraper Disabled'
            else:
                logger.info(f"✅ Lead {lead.name} already has website or was already processed")
                result['enrichment_status'] = 'Already Processed'
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to process lead {lead.name}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            return result
    
    def process_leads_batch_with_fallback(self, leads: List[Lead]) -> Dict[str, Any]:
        """
        Process a batch of leads with Google website scraper fallback.
        
        Args:
            leads: List of leads to process
            
        Returns:
            Batch processing results
        """
        logger.info(f"🔧 Processing batch of {len(leads)} leads")
        
        batch_result = {
            'total_leads': len(leads),
            'leads_processed': 0,
            'websites_discovered': 0,
            'google_searches_performed': 0,
            'airtable_updates': 0,
            'failed_no_website': 0,
            'already_processed': 0,
            'errors': [],
            'lead_results': []
        }
        
        for i, lead in enumerate(leads, 1):
            logger.info(f"🔧 Processing lead {i}/{len(leads)}: {lead.name}")
            
            try:
                lead_result = self.process_lead_with_website_fallback(lead)
                batch_result['lead_results'].append(lead_result)
                
                # Update batch statistics
                batch_result['leads_processed'] += 1
                
                if lead_result['website_discovered']:
                    batch_result['websites_discovered'] += 1
                
                if lead_result['google_search_performed']:
                    batch_result['google_searches_performed'] += 1
                
                if lead_result['airtable_updated']:
                    batch_result['airtable_updates'] += 1
                
                if lead_result['enrichment_status'] == 'Failed - No Website':
                    batch_result['failed_no_website'] += 1
                elif lead_result['enrichment_status'] == 'Already Processed':
                    batch_result['already_processed'] += 1
                
                batch_result['errors'].extend(lead_result['errors'])
                
            except Exception as e:
                error_msg = f"Batch processing failed for lead {lead.name}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                batch_result['errors'].append(error_msg)
        
        logger.info(f"✅ Batch processing completed: {batch_result['websites_discovered']} websites discovered")
        return batch_result
    
    def get_leads_needing_website_discovery(self, limit: Optional[int] = None) -> List[Lead]:
        """
        Get leads that need website discovery.
        
        Args:
            limit: Optional limit on results
            
        Returns:
            List of leads needing website discovery
        """
        try:
            # Get all leads and filter those needing website discovery
            all_leads = self.db.search_leads({}, limit=limit * 2 if limit else 100)
            
            leads_needing_discovery = []
            for lead in all_leads:
                if self._lead_needs_website_discovery(lead):
                    leads_needing_discovery.append(lead)
                    
                    if limit and len(leads_needing_discovery) >= limit:
                        break
            
            logger.info(f"📋 Found {len(leads_needing_discovery)} leads needing website discovery")
            return leads_needing_discovery
            
        except Exception as e:
            logger.error(f"❌ Failed to get leads needing website discovery: {str(e)}")
            return []
    
    def _lead_needs_website_discovery(self, lead: Lead) -> bool:
        """
        Check if a lead needs website discovery using conditional execution logic.
        
        Args:
            lead: Lead instance
            
        Returns:
            True if lead needs website discovery
        """
        # Requirement 2.5: Only run if lead.get("Website") is None or empty
        website = getattr(lead, 'website', None)
        
        if website:
            logger.debug(f"Lead {lead.name} already has website: {website}")
            return False
        
        # Check if we've already attempted website discovery
        website_search_attempted = getattr(lead, 'website_search_attempted', False)
        
        if website_search_attempted:
            logger.debug(f"Lead {lead.name} already had website search attempted")
            return False
        
        # Must have name for search
        if not lead.name:
            logger.debug(f"Lead {lead.id} missing name, cannot search")
            return False
        
        return True
    
    def _update_lead_with_website(self, lead_id: str, website: str) -> bool:
        """
        Update lead in database with discovered website.
        
        Args:
            lead_id: Lead ID
            website: Discovered website URL
            
        Returns:
            True if update successful
        """
        try:
            # Try with full update data first
            update_data = {
                'website': website,
                'website_search_attempted': True,
                'website_search_timestamp': datetime.now().isoformat()
            }
            
            success = self.db.update_lead(lead_id, update_data)
            
            if success:
                logger.info(f"✅ Updated database for lead {lead_id} with website: {website}")
                return True
            else:
                # Fallback: try with just website field
                logger.warning(f"⚠️ Full update failed, trying website-only update for lead {lead_id}")
                fallback_data = {'website': website}
                fallback_success = self.db.update_lead(lead_id, fallback_data)
                
                if fallback_success:
                    logger.info(f"✅ Updated database (fallback) for lead {lead_id} with website: {website}")
                    return True
                else:
                    logger.error(f"❌ Both full and fallback updates failed for lead {lead_id}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Database update failed for lead {lead_id}: {str(e)}")
            
            # Try fallback update with just website
            try:
                logger.warning(f"⚠️ Attempting fallback website-only update for lead {lead_id}")
                fallback_data = {'website': website}
                fallback_success = self.db.update_lead(lead_id, fallback_data)
                
                if fallback_success:
                    logger.info(f"✅ Fallback update successful for lead {lead_id}")
                    return True
                else:
                    logger.error(f"❌ Fallback update also failed for lead {lead_id}")
                    return False
                    
            except Exception as fallback_e:
                logger.error(f"❌ Fallback update exception for lead {lead_id}: {str(fallback_e)}")
                return False
    
    def _update_airtable_with_website(self, lead_id: str, website: str) -> bool:
        """
        Update Airtable with discovered website.
        
        Args:
            lead_id: Lead ID
            website: Discovered website URL
            
        Returns:
            True if update successful
        """
        try:
            # Requirement 2.6: Update Airtable Website field with discovered URL
            
            # Get the updated lead from database
            updated_lead = self.db.get_lead(lead_id)
            
            if not updated_lead:
                logger.error(f"❌ Lead {lead_id} not found for Airtable update")
                return False
            
            # Sync to Airtable
            sync_result = self.airtable_sync.sync_leads_to_airtable([updated_lead], force=True)
            
            if sync_result['success']:
                logger.info(f"✅ Updated Airtable for lead {lead_id} with website: {website}")
                return True
            else:
                logger.error(f"❌ Airtable update failed for lead {lead_id}: {sync_result['errors']}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Airtable update failed for lead {lead_id}: {str(e)}")
            return False
    
    def _set_enrichment_status_failed(self, lead_id: str) -> bool:
        """
        Set enrichment status to 'Failed - No Website' when no results found.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            True if update successful
        """
        try:
            # Requirement 2.7: Set Enrichment Status = "Failed - No Website" when no results found
            
            # Try full update first
            update_data = {
                'website_search_attempted': True,
                'website_search_timestamp': datetime.now().isoformat(),
                'status': 'Failed - No Website'
            }
            
            success = self.db.update_lead(lead_id, update_data)
            
            if success:
                logger.info(f"✅ Set enrichment status to 'Failed - No Website' for lead {lead_id}")
            else:
                # Fallback: try with just status field
                logger.warning(f"⚠️ Full status update failed, trying status-only update for lead {lead_id}")
                fallback_data = {'status': 'Failed - No Website'}
                success = self.db.update_lead(lead_id, fallback_data)
                
                if success:
                    logger.info(f"✅ Set enrichment status (fallback) to 'Failed - No Website' for lead {lead_id}")
                else:
                    logger.error(f"❌ Both full and fallback status updates failed for lead {lead_id}")
                    return False
            
            # Try to update Airtable with the failed status
            try:
                updated_lead = self.db.get_lead(lead_id)
                if updated_lead:
                    self.airtable_sync.sync_leads_to_airtable([updated_lead], force=True)
            except Exception as e:
                logger.warning(f"⚠️ Failed to sync failed status to Airtable for lead {lead_id}: {str(e)}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to set enrichment status for lead {lead_id}: {str(e)}")
            
            # Try minimal fallback
            try:
                logger.warning(f"⚠️ Attempting minimal status update for lead {lead_id}")
                minimal_data = {'status': 'Failed - No Website'}
                minimal_success = self.db.update_lead(lead_id, minimal_data)
                
                if minimal_success:
                    logger.info(f"✅ Minimal status update successful for lead {lead_id}")
                    return True
                else:
                    logger.error(f"❌ Minimal status update also failed for lead {lead_id}")
                    return False
                    
            except Exception as minimal_e:
                logger.error(f"❌ Minimal status update exception for lead {lead_id}: {str(minimal_e)}")
                return False


# Convenience functions for pipeline integration
def process_leads_with_website_fallback(limit: Optional[int] = None, 
                                      enable_google_scraper: bool = True) -> Dict[str, Any]:
    """
    Process leads with Google website scraper fallback.
    
    Args:
        limit: Optional limit on number of leads to process
        enable_google_scraper: Enable Google scraper fallback
        
    Returns:
        Processing results dictionary
    """
    pipeline = LeadPipelineManager(enable_google_scraper=enable_google_scraper)
    
    # Get leads needing website discovery
    leads = pipeline.get_leads_needing_website_discovery(limit=limit)
    
    if not leads:
        logger.info("📭 No leads need website discovery")
        return {
            'total_leads': 0,
            'leads_processed': 0,
            'websites_discovered': 0,
            'google_searches_performed': 0,
            'airtable_updates': 0,
            'failed_no_website': 0,
            'already_processed': 0,
            'errors': []
        }
    
    # Process leads with fallback
    return pipeline.process_leads_batch_with_fallback(leads)

def check_lead_website_status(lead_id: str) -> Dict[str, Any]:
    """
    Check website status for a specific lead.
    
    Args:
        lead_id: Lead ID
        
    Returns:
        Website status information
    """
    try:
        db = get_lead_database()
        lead = db.get_lead(lead_id)
        
        if not lead:
            return {'error': f'Lead {lead_id} not found'}
        
        return {
            'lead_id': lead.id,
            'lead_name': lead.name,
            'website': getattr(lead, 'website', None),
            'website_search_attempted': getattr(lead, 'website_search_attempted', False),
            'website_search_timestamp': getattr(lead, 'website_search_timestamp', None),
            'needs_website_discovery': LeadPipelineManager()._lead_needs_website_discovery(lead)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to check website status for lead {lead_id}: {str(e)}")
        return {'error': str(e)}


if __name__ == "__main__":
    # Test the pipeline integration
    import argparse
    
    def test_pipeline_integration():
        """Test pipeline integration functionality."""
        print("🧪 Testing Pipeline Integration")
        print("=" * 40)
        
        try:
            # Test processing leads with website fallback
            results = process_leads_with_website_fallback(limit=3, enable_google_scraper=True)
            
            print(f"📊 Pipeline Integration Results:")
            print(f"   Total leads: {results['total_leads']}")
            print(f"   Leads processed: {results['leads_processed']}")
            print(f"   Websites discovered: {results['websites_discovered']}")
            print(f"   Google searches: {results['google_searches_performed']}")
            print(f"   Airtable updates: {results['airtable_updates']}")
            print(f"   Failed (no website): {results['failed_no_website']}")
            print(f"   Already processed: {results['already_processed']}")
            
            if results['errors']:
                print(f"   Errors: {len(results['errors'])}")
                for error in results['errors'][:3]:
                    print(f"      - {error}")
            
            print("✅ Pipeline integration test completed")
            return True
            
        except Exception as e:
            print(f"❌ Pipeline integration test failed: {str(e)}")
            return False
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Pipeline Integration")
    parser.add_argument('--test', action='store_true', help='Run integration test')
    parser.add_argument('--check-lead', type=str, help='Check website status for specific lead ID')
    
    args = parser.parse_args()
    
    if args.test:
        success = test_pipeline_integration()
        sys.exit(0 if success else 1)
    elif args.check_lead:
        status = check_lead_website_status(args.check_lead)
        print(f"Website status for lead {args.check_lead}:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        print("Use --test to run integration test or --check-lead <id> to check lead status")