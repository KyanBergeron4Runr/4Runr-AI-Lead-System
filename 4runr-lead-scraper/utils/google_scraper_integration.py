#!/usr/bin/env python3
"""
Google Scraper Pipeline Integration

Integration module for the Google Website Scraper that handles conditional execution,
Airtable updates, and enrichment status tracking within the lead processing pipeline.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.google_scraper import search_company_website_google_sync
    from sync.airtable_sync import AirtableSync
    from database.models import get_lead_database, Lead
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    INTEGRATION_AVAILABLE = False
    import_error = str(e)

logger = logging.getLogger('google-scraper-integration')

class GoogleScraperPipeline:
    """
    Pipeline integration for Google Website Scraper with conditional execution
    and Airtable synchronization.
    """
    
    def __init__(self):
        """Initialize the Google scraper pipeline integration."""
        if not INTEGRATION_AVAILABLE:
            raise ImportError(f"Integration dependencies not available: {import_error}")
        
        # Initialize components
        self.db = get_lead_database()
        self.airtable_sync = AirtableSync()
        
        # Configuration
        self.max_batch_size = 50
        self.search_timeout = 30  # seconds
        
        logger.info("🔍 Google Scraper Pipeline Integration initialized")
    
    def process_lead_website_search(self, lead_id: str) -> Dict[str, Any]:
        """
        Process a single lead for Google website search with conditional execution.
        
        Args:
            lead_id: ID of the lead to process
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"🔍 Processing lead {lead_id} for Google website search")
        
        try:
            # Get lead from database
            lead = self.db.get_lead(lead_id)
            if not lead:
                logger.error(f"❌ Lead {lead_id} not found in database")
                return {
                    'success': False,
                    'error': 'Lead not found',
                    'lead_id': lead_id
                }
            
            # Check conditional execution: only run if Website is None or empty
            if hasattr(lead, 'website') and lead.website and lead.website.strip():
                logger.info(f"✅ Lead {lead_id} already has website: {lead.website}")
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'Website already exists',
                    'lead_id': lead_id,
                    'existing_website': lead.website
                }
            
            # Perform Google search
            logger.info(f"🔍 Performing Google search for: {lead.name}" + 
                       (f" at {lead.company}" if lead.company else ""))
            
            website_url = search_company_website_google_sync(
                full_name=lead.name,
                company_name=lead.company
            )
            
            # Process results
            if website_url:
                return self._handle_website_found(lead, website_url)
            else:
                return self._handle_website_not_found(lead)
        
        except Exception as e:
            logger.error(f"❌ Google search processing failed for lead {lead_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'lead_id': lead_id
            }
    
    def process_leads_batch_website_search(self, limit: int = None) -> Dict[str, Any]:
        """
        Process multiple leads for Google website search in batch.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with batch processing results
        """
        logger.info(f"🔍 Starting batch Google website search (limit: {limit or 'unlimited'})")
        
        try:
            # Get leads that need Google search (no website)
            # Note: We'll filter manually since the database search may not handle None properly
            all_leads = self.db.search_leads({}, limit=limit or self.max_batch_size * 2)
            
            # Filter leads that need Google search
            leads = []
            for lead in all_leads:
                if (not lead.website or lead.website.strip() == "") and not getattr(lead, 'website_search_attempted', False):
                    leads.append(lead)
                    if len(leads) >= (limit or self.max_batch_size):
                        break
            
            leads = self.db.search_leads(filters, limit=limit or self.max_batch_size)
            
            if not leads:
                logger.info("✅ No leads need Google website search")
                return {
                    'success': True,
                    'leads_processed': 0,
                    'websites_found': 0,
                    'websites_not_found': 0,
                    'errors': 0,
                    'skipped': 0
                }
            
            logger.info(f"📋 Processing {len(leads)} leads for Google website search")
            
            # Process each lead
            results = {
                'success': True,
                'leads_processed': 0,
                'websites_found': 0,
                'websites_not_found': 0,
                'errors': 0,
                'skipped': 0,
                'details': []
            }
            
            for lead in leads:
                try:
                    result = self.process_lead_website_search(lead.id)
                    results['details'].append(result)
                    results['leads_processed'] += 1
                    
                    if result.get('success'):
                        if result.get('skipped'):
                            results['skipped'] += 1
                        elif result.get('website_found'):
                            results['websites_found'] += 1
                        else:
                            results['websites_not_found'] += 1
                    else:
                        results['errors'] += 1
                
                except Exception as e:
                    logger.error(f"❌ Batch processing error for lead {lead.id}: {str(e)}")
                    results['errors'] += 1
                    results['details'].append({
                        'success': False,
                        'error': str(e),
                        'lead_id': lead.id
                    })
            
            # Summary
            logger.info(f"✅ Batch Google search completed:")
            logger.info(f"   📊 Processed: {results['leads_processed']} leads")
            logger.info(f"   🌐 Websites found: {results['websites_found']}")
            logger.info(f"   ⚠️ Websites not found: {results['websites_not_found']}")
            logger.info(f"   ⏭️ Skipped: {results['skipped']}")
            logger.info(f"   ❌ Errors: {results['errors']}")
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Batch Google search processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'leads_processed': 0,
                'websites_found': 0,
                'websites_not_found': 0,
                'errors': 1,
                'skipped': 0
            }
    
    def _handle_website_found(self, lead: Lead, website_url: str) -> Dict[str, Any]:
        """
        Handle successful website discovery.
        
        Args:
            lead: Lead instance
            website_url: Discovered website URL
            
        Returns:
            Processing result dictionary
        """
        logger.info(f"✅ Website found for {lead.name}: {website_url}")
        
        try:
            # Update lead in database
            update_data = {
                'website': website_url,
                'website_search_attempted': True,
                'website_search_timestamp': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.db.update_lead(lead.id, update_data)
            logger.info(f"✅ Database updated for lead {lead.id}")
            
            # Update Airtable
            try:
                # Get updated lead for Airtable sync
                updated_lead = self.db.get_lead(lead.id)
                sync_result = self.airtable_sync.sync_leads_to_airtable([updated_lead], force=True)
                
                if sync_result.get('success'):
                    logger.info(f"✅ Airtable updated for lead {lead.id}")
                else:
                    logger.warning(f"⚠️ Airtable sync failed for lead {lead.id}: {sync_result.get('error')}")
            
            except Exception as e:
                logger.warning(f"⚠️ Airtable update failed for lead {lead.id}: {str(e)}")
            
            return {
                'success': True,
                'website_found': True,
                'lead_id': lead.id,
                'lead_name': lead.name,
                'website_url': website_url,
                'database_updated': True,
                'airtable_updated': True
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to handle website found for lead {lead.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'lead_id': lead.id,
                'website_url': website_url
            }
    
    def _handle_website_not_found(self, lead: Lead) -> Dict[str, Any]:
        """
        Handle case when no website is found.
        
        Args:
            lead: Lead instance
            
        Returns:
            Processing result dictionary
        """
        logger.info(f"⚠️ No website found for {lead.name}")
        
        try:
            # Update lead in database with search attempt and failed status
            update_data = {
                'website_search_attempted': True,
                'website_search_timestamp': datetime.now().isoformat(),
                'enrichment_status': 'Failed - No Website',
                'updated_at': datetime.now().isoformat()
            }
            
            self.db.update_lead(lead.id, update_data)
            logger.info(f"✅ Database updated for lead {lead.id} (no website found)")
            
            # Update Airtable with enrichment status
            try:
                # Get updated lead for Airtable sync
                updated_lead = self.db.get_lead(lead.id)
                sync_result = self.airtable_sync.sync_leads_to_airtable([updated_lead], force=True)
                
                if sync_result.get('success'):
                    logger.info(f"✅ Airtable updated for lead {lead.id} (enrichment status set)")
                else:
                    logger.warning(f"⚠️ Airtable sync failed for lead {lead.id}: {sync_result.get('error')}")
            
            except Exception as e:
                logger.warning(f"⚠️ Airtable update failed for lead {lead.id}: {str(e)}")
            
            return {
                'success': True,
                'website_found': False,
                'lead_id': lead.id,
                'lead_name': lead.name,
                'enrichment_status': 'Failed - No Website',
                'database_updated': True,
                'airtable_updated': True
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to handle website not found for lead {lead.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'lead_id': lead.id
            }


# Convenience functions for pipeline integration
def process_lead_google_search(lead_id: str) -> Dict[str, Any]:
    """
    Process a single lead for Google website search.
    
    Args:
        lead_id: ID of the lead to process
        
    Returns:
        Processing result dictionary
    """
    try:
        pipeline = GoogleScraperPipeline()
        return pipeline.process_lead_website_search(lead_id)
    except Exception as e:
        logger.error(f"❌ Google search processing failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'lead_id': lead_id
        }


def process_leads_google_search_batch(limit: int = None) -> Dict[str, Any]:
    """
    Process multiple leads for Google website search in batch.
    
    Args:
        limit: Maximum number of leads to process
        
    Returns:
        Batch processing result dictionary
    """
    try:
        pipeline = GoogleScraperPipeline()
        return pipeline.process_leads_batch_website_search(limit)
    except Exception as e:
        logger.error(f"❌ Batch Google search processing failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'leads_processed': 0,
            'websites_found': 0,
            'websites_not_found': 0,
            'errors': 1,
            'skipped': 0
        }


if __name__ == "__main__":
    # Test the Google scraper pipeline integration
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Google Scraper Pipeline Integration')
    parser.add_argument('--lead-id', help='Process specific lead ID')
    parser.add_argument('--batch', action='store_true', help='Process batch of leads')
    parser.add_argument('--limit', type=int, default=5, help='Limit for batch processing')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.lead_id:
        # Process specific lead
        print(f"🔍 Processing lead: {args.lead_id}")
        result = process_lead_google_search(args.lead_id)
        print(f"📊 Result: {result}")
    
    elif args.batch:
        # Process batch of leads
        print(f"🔍 Processing batch of leads (limit: {args.limit})")
        result = process_leads_google_search_batch(args.limit)
        print(f"📊 Batch Result: {result}")
    
    else:
        print("❌ Please specify --lead-id or --batch")
        print("Usage examples:")
        print("  python google_scraper_integration.py --lead-id lead-123")
        print("  python google_scraper_integration.py --batch --limit 10")