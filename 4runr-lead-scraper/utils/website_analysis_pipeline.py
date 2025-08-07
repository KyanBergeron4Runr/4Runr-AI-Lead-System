#!/usr/bin/env python3
"""
Website Analysis Pipeline

Complete pipeline that combines website content scraping, analysis, and Airtable integration
to extract company information and update lead records with enriched data.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from database.models import get_lead_database, Lead
from sync.airtable_sync import AirtableSync
from utils.website_content_scraper import scrape_website_content_sync
from utils.website_content_analyzer import analyze_website_content

logger = logging.getLogger('website-analysis-pipeline')

class WebsiteAnalysisPipeline:
    """
    Complete pipeline for website content analysis and lead enrichment.
    """
    
    def __init__(self):
        """Initialize the website analysis pipeline."""
        self.db = get_lead_database()
        self.airtable_sync = AirtableSync()
        
        logger.info("🔬 Website Analysis Pipeline initialized")
    
    def process_lead_website_analysis(self, lead: Lead) -> Dict[str, Any]:
        """
        Process complete website analysis for a single lead.
        
        Args:
            lead: Lead instance with website information
            
        Returns:
            Processing results dictionary
        """
        logger.info(f"🔬 Processing website analysis for: {lead.name}")
        
        result = {
            'lead_id': lead.id,
            'lead_name': lead.name,
            'website_url': getattr(lead, 'website', None),
            'scraping_success': False,
            'analysis_success': False,
            'database_updated': False,
            'airtable_updated': False,
            'company_description': '',
            'top_services': '',
            'tone': '',
            'website_insights': '',
            'errors': []
        }
        
        try:
            # Check if lead has website
            website_url = getattr(lead, 'website', None)
            if not website_url:
                error_msg = f"Lead {lead.name} has no website URL"
                logger.warning(f"⚠️ {error_msg}")
                result['errors'].append(error_msg)
                return result
            
            result['website_url'] = website_url
            
            # Step 1: Scrape website content
            logger.info(f"🌐 Scraping website content: {website_url}")
            scraped_content = scrape_website_content_sync(website_url, headless=True, timeout=30000)
            
            if scraped_content['success']:
                result['scraping_success'] = True
                logger.info(f"✅ Website scraping successful: {len(scraped_content['pages_scraped'])} pages")
            else:
                error_msg = f"Website scraping failed: {scraped_content['errors']}"
                logger.error(f"❌ {error_msg}")
                result['errors'].append(error_msg)
                return result
            
            # Step 2: Analyze content
            logger.info(f"📊 Analyzing website content")
            analysis_result = analyze_website_content(scraped_content)
            
            if analysis_result['success']:
                result['analysis_success'] = True
                result['company_description'] = analysis_result['company_description']
                result['top_services'] = analysis_result['top_services']
                result['tone'] = analysis_result['tone']
                result['website_insights'] = analysis_result['website_insights']
                
                logger.info(f"✅ Content analysis successful")
                logger.info(f"   📝 Description: {len(result['company_description'])} chars")
                logger.info(f"   🔧 Services: {result['top_services'][:50]}...")
                logger.info(f"   🎨 Tone: {result['tone']}")
            else:
                error_msg = f"Content analysis failed: {analysis_result['errors']}"
                logger.error(f"❌ {error_msg}")
                result['errors'].append(error_msg)
                return result
            
            # Step 3: Update database
            logger.info(f"💾 Updating database with analysis results")
            database_success = self._update_database_with_analysis(lead.id, analysis_result)
            result['database_updated'] = database_success
            
            if database_success:
                logger.info(f"✅ Database updated successfully")
            else:
                logger.error(f"❌ Database update failed")
                result['errors'].append("Database update failed")
            
            # Step 4: Update Airtable
            logger.info(f"📤 Updating Airtable with analysis results")
            airtable_success = self._update_airtable_with_analysis(lead.id)
            result['airtable_updated'] = airtable_success
            
            if airtable_success:
                logger.info(f"✅ Airtable updated successfully")
            else:
                logger.error(f"❌ Airtable update failed")
                result['errors'].append("Airtable update failed")
            
            return result
            
        except Exception as e:
            error_msg = f"Website analysis pipeline failed for {lead.name}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            return result
    
    def process_leads_batch_analysis(self, leads: List[Lead]) -> Dict[str, Any]:
        """
        Process website analysis for a batch of leads.
        
        Args:
            leads: List of leads to process
            
        Returns:
            Batch processing results
        """
        logger.info(f"🔬 Processing website analysis for {len(leads)} leads")
        
        batch_result = {
            'total_leads': len(leads),
            'leads_processed': 0,
            'scraping_successful': 0,
            'analysis_successful': 0,
            'database_updates': 0,
            'airtable_updates': 0,
            'errors': [],
            'lead_results': []
        }
        
        for i, lead in enumerate(leads, 1):
            logger.info(f"🔬 Processing lead {i}/{len(leads)}: {lead.name}")
            
            try:
                lead_result = self.process_lead_website_analysis(lead)
                batch_result['lead_results'].append(lead_result)
                
                # Update batch statistics
                batch_result['leads_processed'] += 1
                
                if lead_result['scraping_success']:
                    batch_result['scraping_successful'] += 1
                
                if lead_result['analysis_success']:
                    batch_result['analysis_successful'] += 1
                
                if lead_result['database_updated']:
                    batch_result['database_updates'] += 1
                
                if lead_result['airtable_updated']:
                    batch_result['airtable_updates'] += 1
                
                batch_result['errors'].extend(lead_result['errors'])
                
                # Delay between leads to be respectful
                import time
                time.sleep(2)
                
            except Exception as e:
                error_msg = f"Batch processing failed for lead {lead.name}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                batch_result['errors'].append(error_msg)
        
        logger.info(f"✅ Batch processing completed: {batch_result['analysis_successful']} successful analyses")
        return batch_result
    
    def get_leads_needing_website_analysis(self, limit: Optional[int] = None) -> List[Lead]:
        """
        Get leads that need website analysis.
        
        Args:
            limit: Optional limit on results
            
        Returns:
            List of leads needing website analysis
        """
        try:
            # Get leads with websites that haven't been analyzed
            all_leads = self.db.search_leads({}, limit=limit * 2 if limit else 100)
            
            leads_needing_analysis = []
            for lead in all_leads:
                if self._lead_needs_website_analysis(lead):
                    leads_needing_analysis.append(lead)
                    
                    if limit and len(leads_needing_analysis) >= limit:
                        break
            
            logger.info(f"📋 Found {len(leads_needing_analysis)} leads needing website analysis")
            return leads_needing_analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to get leads needing website analysis: {str(e)}")
            return []
    
    def _lead_needs_website_analysis(self, lead: Lead) -> bool:
        """
        Check if a lead needs website analysis.
        
        Args:
            lead: Lead instance
            
        Returns:
            True if lead needs website analysis
        """
        # Must have a website URL
        website = getattr(lead, 'website', None)
        if not website:
            return False
        
        # Check if already has company description (indicates analysis was done)
        company_description = getattr(lead, 'company_description', None)
        if company_description:
            logger.debug(f"Lead {lead.name} already has company description")
            return False
        
        # Check if already has top services (indicates analysis was done)
        top_services = getattr(lead, 'top_services', None)
        if top_services:
            logger.debug(f"Lead {lead.name} already has top services")
            return False
        
        return True
    
    def _update_database_with_analysis(self, lead_id: str, analysis_result: Dict[str, Any]) -> bool:
        """
        Update database with website analysis results.
        
        Args:
            lead_id: Lead ID
            analysis_result: Analysis results from content analyzer
            
        Returns:
            True if update successful
        """
        try:
            # Requirement 3.7: Update Airtable with Company_Description, Top_Services, Tone, and Website_Insights fields
            update_data = {
                'company_description': analysis_result.get('company_description', ''),
                'top_services': analysis_result.get('top_services', ''),
                'tone': analysis_result.get('tone', 'professional'),
                'website_insights': analysis_result.get('website_insights', ''),
                'website_analyzed_at': datetime.now().isoformat()
            }
            
            # Remove empty values to avoid database issues
            update_data = {k: v for k, v in update_data.items() if v}
            
            success = self.db.update_lead(lead_id, update_data)
            
            if success:
                logger.info(f"✅ Updated database for lead {lead_id}")
            else:
                logger.error(f"❌ Failed to update database for lead {lead_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Database update failed for lead {lead_id}: {str(e)}")
            return False
    
    def _update_airtable_with_analysis(self, lead_id: str) -> bool:
        """
        Update Airtable with website analysis results.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            True if update successful
        """
        try:
            # Get the updated lead from database
            updated_lead = self.db.get_lead(lead_id)
            
            if not updated_lead:
                logger.error(f"❌ Lead {lead_id} not found for Airtable update")
                return False
            
            # Sync to Airtable
            sync_result = self.airtable_sync.sync_leads_to_airtable([updated_lead], force=True)
            
            if sync_result['success']:
                logger.info(f"✅ Updated Airtable for lead {lead_id}")
                return True
            else:
                logger.error(f"❌ Airtable update failed for lead {lead_id}: {sync_result['errors']}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Airtable update failed for lead {lead_id}: {str(e)}")
            return False


# Convenience functions
def process_leads_website_analysis(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Process website analysis for leads that need it.
    
    Args:
        limit: Optional limit on number of leads to process
        
    Returns:
        Processing results dictionary
    """
    pipeline = WebsiteAnalysisPipeline()
    
    # Get leads needing website analysis
    leads = pipeline.get_leads_needing_website_analysis(limit=limit)
    
    if not leads:
        logger.info("📭 No leads need website analysis")
        return {
            'total_leads': 0,
            'leads_processed': 0,
            'scraping_successful': 0,
            'analysis_successful': 0,
            'database_updates': 0,
            'airtable_updates': 0,
            'errors': []
        }
    
    # Process leads
    return pipeline.process_leads_batch_analysis(leads)

def analyze_lead_website(lead_id: str) -> Dict[str, Any]:
    """
    Analyze website for a specific lead.
    
    Args:
        lead_id: Lead ID
        
    Returns:
        Analysis results dictionary
    """
    try:
        pipeline = WebsiteAnalysisPipeline()
        
        # Get lead
        lead = pipeline.db.get_lead(lead_id)
        if not lead:
            return {'error': f'Lead {lead_id} not found'}
        
        # Process analysis
        return pipeline.process_lead_website_analysis(lead)
        
    except Exception as e:
        logger.error(f"❌ Failed to analyze website for lead {lead_id}: {str(e)}")
        return {'error': str(e)}


if __name__ == "__main__":
    # Test the website analysis pipeline
    import argparse
    
    def test_pipeline():
        """Test the website analysis pipeline."""
        print("🧪 Testing Website Analysis Pipeline")
        print("=" * 40)
        
        try:
            # Test processing leads with website analysis
            results = process_leads_website_analysis(limit=2)
            
            print(f"📊 Pipeline Results:")
            print(f"   Total leads: {results['total_leads']}")
            print(f"   Leads processed: {results['leads_processed']}")
            print(f"   Scraping successful: {results['scraping_successful']}")
            print(f"   Analysis successful: {results['analysis_successful']}")
            print(f"   Database updates: {results['database_updates']}")
            print(f"   Airtable updates: {results['airtable_updates']}")
            
            if results['errors']:
                print(f"   Errors: {len(results['errors'])}")
                for error in results['errors'][:3]:
                    print(f"      - {error}")
            
            print("✅ Website analysis pipeline test completed")
            return True
            
        except Exception as e:
            print(f"❌ Pipeline test failed: {str(e)}")
            return False
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Website Analysis Pipeline")
    parser.add_argument('--test', action='store_true', help='Run pipeline test')
    parser.add_argument('--analyze-lead', type=str, help='Analyze website for specific lead ID')
    
    args = parser.parse_args()
    
    if args.test:
        success = test_pipeline()
        sys.exit(0 if success else 1)
    elif args.analyze_lead:
        result = analyze_lead_website(args.analyze_lead)
        print(f"Website analysis result for lead {args.analyze_lead}:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        print("Use --test to run pipeline test or --analyze-lead <id> to analyze specific lead")