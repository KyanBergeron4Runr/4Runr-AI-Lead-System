#!/usr/bin/env python3
"""
Auto Lead Processor - Automatically detects, enriches, and processes leads

This system:
1. Monitors for new leads
2. Checks data completeness 
3. Enriches missing data (with time limits)
4. Marks leads as complete when ready
5. Triggers campaign generation
"""

import sys
import time
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

from database.lead_database import get_lead_database
from enrichment_config import get_enrichment_config
# from shared.airtable_client import get_airtable_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LeadDataChecker:
    """Checks lead data completeness and quality"""
    
    REQUIRED_FIELDS = ['full_name', 'company']
    PREFERRED_FIELDS = ['email', 'title', 'linkedin_url']
    ENRICHMENT_FIELDS = ['company_website', 'industry', 'company_size']
    
    def __init__(self):
        self.config = get_enrichment_config()
    
    def check_completeness(self, lead: dict) -> dict:
        """Check lead data completeness"""
        
        # Required fields check
        missing_required = []
        for field in self.REQUIRED_FIELDS:
            if not lead.get(field):
                missing_required.append(field)
        
        # Preferred fields check
        missing_preferred = []
        for field in self.PREFERRED_FIELDS:
            if not lead.get(field):
                missing_preferred.append(field)
        
        # Enrichment fields check
        missing_enrichment = []
        for field in self.ENRICHMENT_FIELDS:
            if not lead.get(field):
                missing_enrichment.append(field)
        
        # Calculate completeness score
        total_fields = len(self.REQUIRED_FIELDS) + len(self.PREFERRED_FIELDS) + len(self.ENRICHMENT_FIELDS)
        missing_total = len(missing_required) + len(missing_preferred) + len(missing_enrichment)
        completeness_score = ((total_fields - missing_total) / total_fields) * 100
        
        # Determine readiness
        is_ready_for_outreach = (
            len(missing_required) == 0 and  # Must have required fields
            'email' not in missing_preferred and  # Must have email
            completeness_score >= 60  # At least 60% complete
        )
        
        is_ready_for_enrichment = (
            len(missing_required) == 0 and  # Must have required fields
            len(missing_preferred) > 0  # Has missing preferred fields
        )
        
        return {
            'missing_required': missing_required,
            'missing_preferred': missing_preferred,
            'missing_enrichment': missing_enrichment,
            'completeness_score': completeness_score,
            'is_ready_for_outreach': is_ready_for_outreach,
            'is_ready_for_enrichment': is_ready_for_enrichment,
            'needs_enrichment': len(missing_preferred) > 0 or len(missing_enrichment) > 0
        }

class AutoLeadEnricher:
    """Automatically enriches leads with missing data"""
    
    def __init__(self):
        self.config = get_enrichment_config()
        self.checker = LeadDataChecker()
    
    async def enrich_lead(self, lead: dict) -> dict:
        """Enrich a single lead with missing data"""
        
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('full_name', 'Unknown')
        
        logger.info(f"🔍 Starting enrichment for {lead_name}")
        
        # Check what's missing
        completeness = self.checker.check_completeness(lead)
        
        if not completeness['needs_enrichment']:
            logger.info(f"✅ {lead_name} already complete")
            return {'status': 'complete', 'changes': {}}
        
        enrichment_results = {}
        changes_made = {}
        
        # Enrich missing email
        if 'email' in completeness['missing_preferred']:
            if self.config.should_search_email(lead):
                logger.info(f"📧 Searching for email for {lead_name}")
                self.config.start_timer('email', lead_id)
                
                email_result = await self._find_email(lead)
                if email_result:
                    changes_made['email'] = email_result
                    enrichment_results['email'] = email_result
                    enrichment_results['email_method'] = 'search'
                elif self.config.should_use_fallback('email', lead):
                    # Generate pattern email
                    pattern_email = self._generate_pattern_email(lead)
                    if pattern_email:
                        changes_made['email'] = pattern_email
                        enrichment_results['email'] = pattern_email
                        enrichment_results['email_method'] = 'pattern'
                
                self.config.increment_attempts('email', lead_id)
        
        # Enrich missing website (store in raw_data since company_website column doesn't exist)
        raw_data = lead.get('raw_data', {})
        if isinstance(raw_data, str):
            import json
            try:
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}
        elif raw_data is None:
            raw_data = {}
        
        if not raw_data.get('website') and self.config.should_search_website(lead):
            logger.info(f"🌐 Searching for website for {lead_name}")
            self.config.start_timer('website', lead_id)
            
            website_result = await self._find_website(lead)
            if website_result:
                raw_data['website'] = website_result
                enrichment_results['website'] = website_result
                enrichment_results['website_method'] = 'search'
            
            self.config.increment_attempts('website', lead_id)
        
        # Enrich company information
        if self.config.should_enrich_company(lead):
            logger.info(f"🏢 Enriching company info for {lead_name}")
            self.config.start_timer('company', lead_id)
            
            company_info = await self._enrich_company_info(lead)
            if company_info:
                # Store company info in raw_data
                raw_data.update(company_info)
                enrichment_results['company_info'] = company_info
        
        # Generate enrichment summary
        enrichment_summary = self.config.get_enrichment_summary(lead, enrichment_results)
        
        # Update raw_data with enrichment info
        raw_data.update({
            'last_enrichment_attempt': datetime.now().isoformat(),
            'enrichment_summary': enrichment_summary,
            'enrichment_results': enrichment_results
        })
        
        changes_made['raw_data'] = raw_data
        changes_made['enriched'] = True
        changes_made['needs_enrichment'] = False
        
        # Determine new status
        updated_lead = {**lead, **changes_made}
        new_completeness = self.checker.check_completeness(updated_lead)
        new_status = self.config.determine_final_status(updated_lead, enrichment_results)
        
        changes_made['status'] = new_status
        
        logger.info(f"✅ Enrichment complete for {lead_name}: {new_status} (score: {new_completeness['completeness_score']:.1f}%)")
        
        return {
            'status': 'enriched',
            'changes': changes_made,
            'completeness_score': new_completeness['completeness_score'],
            'new_status': new_status
        }
    
    async def _find_email(self, lead: dict) -> Optional[str]:
        """Find email for lead (with timeout)"""
        # Simulate email search with timeout
        await asyncio.sleep(1)  # Simulate search time
        
        # Check if time exceeded
        if self.config.is_time_exceeded('email', lead.get('id', 'unknown')):
            logger.warning(f"⏰ Email search timeout for {lead.get('full_name')}")
            return None
        
        # Mock email finding logic
        company = lead.get('company', '').lower().replace(' ', '').replace('.', '')
        if company and len(company) > 3:
            name_parts = lead.get('full_name', '').lower().split()
            if len(name_parts) >= 2:
                return f"{name_parts[0]}.{name_parts[-1]}@{company}.com"
        
        return None
    
    async def _find_website(self, lead: dict) -> Optional[str]:
        """Find website for lead (with timeout)"""
        # Simulate website search with timeout
        await asyncio.sleep(0.5)  # Simulate search time
        
        # Check if time exceeded
        if self.config.is_time_exceeded('website', lead.get('id', 'unknown')):
            logger.warning(f"⏰ Website search timeout for {lead.get('full_name')}")
            return None
        
        # Mock website finding logic
        company = lead.get('company', '').lower().replace(' ', '').replace('.', '')
        if company and len(company) > 3:
            return f"www.{company}.com"
        
        return None
    
    async def _enrich_company_info(self, lead: dict) -> dict:
        """Enrich company information (with timeout)"""
        # Simulate company enrichment with timeout
        await asyncio.sleep(0.3)  # Simulate search time
        
        # Check if time exceeded
        if self.config.is_time_exceeded('company', lead.get('id', 'unknown')):
            logger.warning(f"⏰ Company enrichment timeout for {lead.get('full_name')}")
            return {}
        
        # Mock company enrichment
        company_info = {}
        
        if not lead.get('industry'):
            # Mock industry detection
            company_name = lead.get('company', '').lower()
            if 'tech' in company_name or 'software' in company_name:
                company_info['industry'] = 'Technology'
            elif 'health' in company_name or 'medical' in company_name:
                company_info['industry'] = 'Healthcare'
            else:
                company_info['industry'] = 'Business Services'
        
        if not lead.get('company_size'):
            company_info['company_size'] = 'Small (1-50 employees)'
        
        return company_info
    
    def _generate_pattern_email(self, lead: dict) -> Optional[str]:
        """Generate pattern-based email"""
        company = lead.get('company', '').lower().replace(' ', '').replace('.', '')
        full_name = lead.get('full_name', '')
        
        if not company or not full_name:
            return None
        
        name_parts = full_name.lower().split()
        if len(name_parts) < 2:
            return None
        
        # Common email patterns
        patterns = [
            f"{name_parts[0]}.{name_parts[-1]}@{company}.com",
            f"{name_parts[0][0]}{name_parts[-1]}@{company}.com",
            f"{name_parts[0]}@{company}.com"
        ]
        
        return patterns[0]  # Return first pattern

class AutoLeadProcessor:
    """Main auto lead processor"""
    
    def __init__(self):
        self.db = get_lead_database()
        self.enricher = AutoLeadEnricher()
        self.checker = LeadDataChecker()
        self.running = False
    
    async def process_new_leads(self) -> dict:
        """Process new leads that need attention"""
        
        logger.info("🔍 Scanning for leads that need processing...")
        
        # Get leads that need enrichment
        leads_needing_enrichment = self.db.search_leads({
            'needs_enrichment': True,
            'status': 'new'
        })
        
        # Get leads that might be ready for outreach but not marked
        potentially_ready = self.db.search_leads({
            'enriched': True,
            'status': 'Enriched'
        })
        
        logger.info(f"📊 Found {len(leads_needing_enrichment)} leads needing enrichment")
        logger.info(f"📊 Found {len(potentially_ready)} leads to check for readiness")
        
        processed_count = 0
        promoted_count = 0
        error_count = 0
        
        # Process leads needing enrichment
        for lead in leads_needing_enrichment[:5]:  # Limit batch size
            try:
                result = await self.enricher.enrich_lead(lead)
                
                if result['status'] == 'enriched' and result['changes']:
                    # Update database
                    success = self.db.update_lead(lead['id'], result['changes'])
                    if success:
                        processed_count += 1
                        logger.info(f"✅ Updated {lead.get('full_name')} -> {result['new_status']}")
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed to update {lead.get('full_name')}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing {lead.get('full_name', 'Unknown')}: {str(e)}")
        
        # Check potentially ready leads
        for lead in potentially_ready[:5]:  # Limit batch size
            try:
                completeness = self.checker.check_completeness(lead)
                
                if completeness['is_ready_for_outreach']:
                    # Promote to Ready for Outreach
                    success = self.db.update_lead(lead['id'], {
                        'status': 'Ready for Outreach',
                        'updated_at': datetime.now()
                    })
                    
                    if success:
                        promoted_count += 1
                        logger.info(f"🎯 Promoted {lead.get('full_name')} to Ready for Outreach")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error checking {lead.get('full_name', 'Unknown')}: {str(e)}")
        
        return {
            'processed': processed_count,
            'promoted': promoted_count,
            'errors': error_count,
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_continuous_processing(self, interval_minutes: int = 10):
        """Run continuous lead processing"""
        
        logger.info(f"🚀 Starting continuous lead processing (every {interval_minutes} minutes)")
        self.running = True
        
        while self.running:
            try:
                result = await self.process_new_leads()
                
                logger.info(f"📊 Processing cycle complete: "
                           f"{result['processed']} enriched, "
                           f"{result['promoted']} promoted, "
                           f"{result['errors']} errors")
                
                # Wait for next cycle
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("👋 Stopping continuous processing...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Error in processing cycle: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop(self):
        """Stop continuous processing"""
        self.running = False

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto Lead Processor")
    parser.add_argument('--continuous', action='store_true', help='Run continuous processing')
    parser.add_argument('--interval', type=int, default=10, help='Processing interval in minutes')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    
    args = parser.parse_args()
    
    processor = AutoLeadProcessor()
    
    try:
        if args.continuous:
            await processor.run_continuous_processing(args.interval)
        else:
            # Run once
            result = await processor.process_new_leads()
            print(f"✅ Processing complete: {result}")
    
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(asyncio.run(main()))