#!/usr/bin/env python3
"""
Enhanced Enricher Integration

Combines web content scraping with AI-powered business trait extraction
for comprehensive lead enrichment. Integrates with database and Airtable.
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
    from utils.web_content_scraper import scrape_website_content_sync
    from enricher.business_trait_extractor import extract_business_traits_from_content
    from database.models import get_lead_database, Lead
    from sync.airtable_sync import AirtableSync
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    INTEGRATION_AVAILABLE = False
    import_error = str(e)

logger = logging.getLogger('enhanced-enricher-integration')

class EnhancedEnricherIntegration:
    """
    Enhanced enricher that combines web scraping with AI-powered business trait extraction.
    Provides complete lead enrichment with database and Airtable integration.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the enhanced enricher integration.
        
        Args:
            openai_api_key: Optional OpenAI API key for trait extraction
        """
        if not INTEGRATION_AVAILABLE:
            raise ImportError(f"Integration dependencies not available: {import_error}")
        
        # Initialize components
        self.db = get_lead_database()
        self.airtable_sync = AirtableSync()
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        # Configuration
        self.max_batch_size = 20
        self.enable_ai_extraction = bool(self.openai_api_key)
        
        logger.info("🧠 Enhanced Enricher Integration initialized")
        logger.info(f"🤖 AI extraction enabled: {self.enable_ai_extraction}")
    
    def enrich_lead_comprehensive(self, lead_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive lead enrichment including web scraping and AI analysis.
        
        Args:
            lead_id: ID of the lead to enrich
            
        Returns:
            Dictionary with enrichment results
        """
        logger.info(f"🧠 Starting comprehensive enrichment for lead {lead_id}")
        
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
            
            # Check if lead has website
            if not hasattr(lead, 'website') or not lead.website:
                logger.warning(f"⚠️ Lead {lead_id} has no website for enrichment")
                return {
                    'success': False,
                    'error': 'No website available for enrichment',
                    'lead_id': lead_id,
                    'lead_name': lead.name
                }
            
            # Step 1: Scrape website content
            logger.info(f"🌐 Scraping website: {lead.website}")
            content_result = scrape_website_content_sync(lead.website)
            
            if not content_result.get('success'):
                return self._handle_scraping_failed(lead, content_result.get('error', 'Unknown scraping error'))
            
            # Step 2: Extract business traits using AI (if enabled)
            traits_result = {}
            if self.enable_ai_extraction:
                logger.info("🤖 Extracting business traits using AI")
                
                # Add lead context to content
                enhanced_content = {
                    **content_result,
                    'company_name': getattr(lead, 'company', ''),
                    'email': getattr(lead, 'email', '')
                }
                
                traits_result = extract_business_traits_from_content(enhanced_content, self.openai_api_key)
            else:
                logger.info("⚠️ AI extraction disabled - using basic analysis")
                traits_result = self._basic_trait_extraction(content_result)
            
            # Step 3: Combine results and update database
            enrichment_data = self._combine_enrichment_results(content_result, traits_result)
            
            # Step 4: Update lead in database
            update_success = self._update_lead_database(lead, enrichment_data)
            
            # Step 5: Sync to Airtable
            airtable_success = self._sync_to_airtable(lead.id)
            
            # Create result
            result = {
                'success': True,
                'lead_id': lead_id,
                'lead_name': lead.name,
                'website_url': lead.website,
                'scraping_success': True,
                'ai_extraction_success': traits_result.get('extraction_success', False),
                'database_updated': update_success,
                'airtable_updated': airtable_success,
                'enrichment_data': enrichment_data
            }
            
            logger.info(f"✅ Comprehensive enrichment completed for {lead.name}")
            logger.info(f"   Business Type: {enrichment_data.get('Business_Type', 'Unknown')}")
            logger.info(f"   Traits: {len(enrichment_data.get('Business_Traits', []))}")
            logger.info(f"   Pain Points: {len(enrichment_data.get('Pain_Points', []))}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Comprehensive enrichment failed for lead {lead_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'lead_id': lead_id
            }
    
    def enrich_leads_batch(self, limit: int = None) -> Dict[str, Any]:
        """
        Perform batch enrichment on multiple leads.
        
        Args:
            limit: Maximum number of leads to enrich
            
        Returns:
            Dictionary with batch enrichment results
        """
        logger.info(f"🧠 Starting batch enrichment (limit: {limit or 'unlimited'})")
        
        try:
            # Get leads that need enrichment (have website but not enriched)
            all_leads = self.db.search_leads({}, limit=limit or self.max_batch_size * 2)
            
            # Filter leads that need enrichment
            leads_to_enrich = []
            for lead in all_leads:
                if (hasattr(lead, 'website') and lead.website and 
                    not getattr(lead, 'enriched', False)):
                    leads_to_enrich.append(lead)
                    if len(leads_to_enrich) >= (limit or self.max_batch_size):
                        break
            
            if not leads_to_enrich:
                logger.info("✅ No leads need enrichment")
                return {
                    'success': True,
                    'leads_processed': 0,
                    'enrichment_successful': 0,
                    'enrichment_failed': 0,
                    'details': []
                }
            
            logger.info(f"📋 Processing {len(leads_to_enrich)} leads for enrichment")
            
            # Process each lead
            results = {
                'success': True,
                'leads_processed': 0,
                'enrichment_successful': 0,
                'enrichment_failed': 0,
                'details': []
            }
            
            for lead in leads_to_enrich:
                try:
                    result = self.enrich_lead_comprehensive(lead.id)
                    results['details'].append(result)
                    results['leads_processed'] += 1
                    
                    if result.get('success'):
                        results['enrichment_successful'] += 1
                    else:
                        results['enrichment_failed'] += 1
                
                except Exception as e:
                    logger.error(f"❌ Batch enrichment error for lead {lead.id}: {str(e)}")
                    results['enrichment_failed'] += 1
                    results['details'].append({
                        'success': False,
                        'error': str(e),
                        'lead_id': lead.id
                    })
            
            # Summary
            logger.info(f"✅ Batch enrichment completed:")
            logger.info(f"   📊 Processed: {results['leads_processed']} leads")
            logger.info(f"   ✅ Successful: {results['enrichment_successful']}")
            logger.info(f"   ❌ Failed: {results['enrichment_failed']}")
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Batch enrichment failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'leads_processed': 0,
                'enrichment_successful': 0,
                'enrichment_failed': 1
            }
    
    def _handle_scraping_failed(self, lead: Lead, error: str) -> Dict[str, Any]:
        """Handle failed website scraping."""
        logger.warning(f"⚠️ Website scraping failed for {lead.name}: {error}")
        
        # Update lead with scraping failure
        update_data = {
            'enrichment_attempts': getattr(lead, 'enrichment_attempts', 0) + 1,
            'enrichment_last_attempt': datetime.now().isoformat(),
            'enrichment_method': 'web_scraping_failed',
            'updated_at': datetime.now().isoformat()
        }
        
        self.db.update_lead(lead.id, update_data)
        
        return {
            'success': False,
            'error': f'Website scraping failed: {error}',
            'lead_id': lead.id,
            'lead_name': lead.name,
            'website_url': lead.website,
            'scraping_success': False
        }
    
    def _basic_trait_extraction(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Basic trait extraction without AI (fallback method)."""
        logger.info("🔍 Performing basic trait extraction (no AI)")
        
        text = content.get('text', '').lower()
        title = content.get('page_title', '').lower()
        meta = content.get('meta_description', '').lower()
        
        all_content = f"{text} {title} {meta}"
        
        # Basic business type detection
        business_type = 'Unknown'
        if any(word in all_content for word in ['saas', 'software', 'platform', 'app']):
            business_type = 'SaaS'
        elif any(word in all_content for word in ['agency', 'marketing', 'advertising']):
            business_type = 'Agency'
        elif any(word in all_content for word in ['consulting', 'consultant', 'advisory']):
            business_type = 'Consulting'
        elif any(word in all_content for word in ['law', 'legal', 'attorney', 'lawyer']):
            business_type = 'Law Firm'
        elif any(word in all_content for word in ['shop', 'store', 'ecommerce', 'retail']):
            business_type = 'E-commerce'
        
        # Basic traits detection
        traits = []
        if 'b2b' in all_content or 'business' in all_content:
            traits.append('B2B')
        if any(word in all_content for word in ['service', 'services']):
            traits.append('Service-Based')
        if any(word in all_content for word in ['local', 'area', 'city']):
            traits.append('Local')
        if any(word in all_content for word in ['enterprise', 'large', 'corporate']):
            traits.append('Enterprise-Focused')
        
        # Basic pain points detection
        pain_points = []
        if any(word in all_content for word in ['manual', 'time-consuming', 'inefficient']):
            pain_points.append('Manual processes')
        if any(word in all_content for word in ['lead', 'customer', 'client']):
            pain_points.append('Lead generation')
        if any(word in all_content for word in ['scale', 'scaling', 'growth']):
            pain_points.append('Scaling operations')
        
        return {
            'Business_Type': business_type,
            'Business_Traits': traits,
            'Pain_Points': pain_points,
            'Strategic_Insight': f'Basic analysis suggests {business_type.lower()} business model',
            'extraction_success': True,
            'extraction_method': 'basic_keyword_analysis',
            'extracted_at': datetime.now().isoformat()
        }
    
    def _combine_enrichment_results(self, content: Dict[str, Any], traits: Dict[str, Any]) -> Dict[str, Any]:
        """Combine web scraping and trait extraction results."""
        
        # Create comprehensive enrichment data
        enrichment_data = {
            # AI-extracted business intelligence
            'Business_Type': traits.get('Business_Type', 'Unknown'),
            'Business_Traits': traits.get('Business_Traits', []),
            'Pain_Points': traits.get('Pain_Points', []),
            'Strategic_Insight': traits.get('Strategic_Insight', ''),
            
            # Website content data (using Extra info field for now)
            'Extra info': self._create_combined_website_data(content, traits),
            
            # Metadata
            'enrichment_success': traits.get('extraction_success', False),
            'enrichment_method': traits.get('extraction_method', 'unknown'),
            'enriched_at': datetime.now().isoformat(),
            'content_length': content.get('content_length', 0),
            'source_url': content.get('url', '')
        }
        
        return enrichment_data
    
    def _generate_company_description(self, content: Dict[str, Any]) -> str:
        """Generate company description from content."""
        # Use meta description if available and good quality
        meta = content.get('meta_description', '').strip()
        if meta and len(meta) > 50:
            return meta
        
        # Extract first meaningful sentence from content
        text = content.get('text', '')
        if text:
            sentences = text.split('.')
            for sentence in sentences[:3]:  # Check first 3 sentences
                sentence = sentence.strip()
                if len(sentence) > 50 and any(word in sentence.lower() for word in ['we', 'our', 'company', 'business']):
                    return sentence + '.'
        
        # Fallback to title
        title = content.get('page_title', '').strip()
        return title if title else 'No description available'
    
    def _extract_top_services(self, content: Dict[str, Any]) -> str:
        """Extract top services from content."""
        text = content.get('text', '').lower()
        
        # Common service keywords
        service_keywords = [
            'consulting', 'development', 'design', 'marketing', 'sales',
            'support', 'training', 'implementation', 'integration', 'automation',
            'analytics', 'optimization', 'management', 'strategy', 'planning'
        ]
        
        found_services = []
        for keyword in service_keywords:
            if keyword in text:
                found_services.append(keyword.title())
        
        if found_services:
            return ', '.join(found_services[:5])  # Top 5 services
        else:
            return 'Services not clearly specified'
    
    def _analyze_website_tone(self, content: Dict[str, Any]) -> str:
        """Analyze website tone."""
        text = content.get('text', '').lower()
        
        # Tone indicators
        formal_indicators = ['professional', 'enterprise', 'corporate', 'established']
        friendly_indicators = ['friendly', 'welcome', 'help', 'support', 'team']
        bold_indicators = ['leading', 'best', 'top', 'premier', 'innovative']
        casual_indicators = ['easy', 'simple', 'fun', 'awesome', 'cool']
        
        scores = {
            'formal': sum(1 for word in formal_indicators if word in text),
            'friendly': sum(1 for word in friendly_indicators if word in text),
            'bold': sum(1 for word in bold_indicators if word in text),
            'casual': sum(1 for word in casual_indicators if word in text)
        }
        
        # Return tone with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get).title()
        else:
            return 'Professional'
    
    def _create_combined_website_data(self, content: Dict[str, Any], traits: Dict[str, Any]) -> str:
        """Create combined website data for Extra info field."""
        data_parts = []
        
        # Company description
        description = self._generate_company_description(content)
        if description and description != 'No description available':
            data_parts.append(f"Company: {description}")
        
        # Top services
        services = self._extract_top_services(content)
        if services and services != 'Services not specified':
            data_parts.append(f"Services: {services}")
        
        # Website tone
        tone = self._analyze_website_tone(content)
        if tone:
            data_parts.append(f"Tone: {tone}")
        
        # Website insights
        insights = self._create_website_insights(content, traits)
        if insights:
            data_parts.append(f"Insights: {insights}")
        
        return " | ".join(data_parts) if data_parts else ""
    
    def _create_website_insights(self, content: Dict[str, Any], traits: Dict[str, Any]) -> str:
        """Create structured website insights."""
        insights_parts = []
        
        # Add URL and analysis date
        if content.get('url'):
            insights_parts.append(f"URL: {content['url']}")
        
        insights_parts.append(f"Analyzed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Add content summary
        content_length = content.get('content_length', 0)
        insights_parts.append(f"Content: {content_length} characters extracted")
        
        # Add business intelligence summary
        business_type = traits.get('Business_Type', 'Unknown')
        insights_parts.append(f"Business Type: {business_type}")
        
        traits_list = traits.get('Business_Traits', [])
        if traits_list:
            insights_parts.append(f"Key Traits: {', '.join(traits_list)}")
        
        pain_points = traits.get('Pain_Points', [])
        if pain_points:
            insights_parts.append(f"Pain Points: {', '.join(pain_points)}")
        
        # Add strategic insight
        strategic_insight = traits.get('Strategic_Insight', '')
        if strategic_insight:
            insights_parts.append(f"Strategic Insight: {strategic_insight}")
        
        return ' | '.join(insights_parts)
    
    def _update_lead_database(self, lead: Lead, enrichment_data: Dict[str, Any]) -> bool:
        """Update lead in database with enrichment data."""
        try:
            update_data = {
                'enriched': True,
                'enrichment_attempts': getattr(lead, 'enrichment_attempts', 0) + 1,
                'enrichment_last_attempt': datetime.now().isoformat(),
                'enrichment_method': enrichment_data.get('enrichment_method', 'enhanced_enricher'),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add enrichment fields if they exist in the database schema
            enrichment_fields = [
                'Business_Type', 'Business_Traits', 'Pain_Points', 'Strategic_Insight',
                'Extra info'
            ]
            
            for field in enrichment_fields:
                if field in enrichment_data:
                    # Convert lists to strings for database storage
                    value = enrichment_data[field]
                    if isinstance(value, list):
                        value = ', '.join(value)
                    update_data[field.lower()] = value
            
            success = self.db.update_lead(lead.id, update_data)
            
            if success:
                logger.info(f"✅ Database updated for lead {lead.id}")
            else:
                logger.warning(f"⚠️ Database update failed for lead {lead.id}")
            
            return success
        
        except Exception as e:
            logger.error(f"❌ Database update error for lead {lead.id}: {str(e)}")
            return False
    
    def _sync_to_airtable(self, lead_id: str) -> bool:
        """Sync enriched lead to Airtable."""
        try:
            # Get updated lead
            updated_lead = self.db.get_lead(lead_id)
            if not updated_lead:
                return False
            
            # Force sync to Airtable
            sync_result = self.airtable_sync.sync_leads_to_airtable([updated_lead], force=True)
            
            if sync_result.get('success'):
                logger.info(f"✅ Airtable updated for lead {lead_id}")
                return True
            else:
                logger.warning(f"⚠️ Airtable sync failed for lead {lead_id}: {sync_result.get('error')}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Airtable sync error for lead {lead_id}: {str(e)}")
            return False


# Convenience functions
def enrich_lead_comprehensive(lead_id: str, openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform comprehensive lead enrichment.
    
    Args:
        lead_id: ID of the lead to enrich
        openai_api_key: Optional OpenAI API key
        
    Returns:
        Enrichment result dictionary
    """
    try:
        enricher = EnhancedEnricherIntegration(openai_api_key)
        return enricher.enrich_lead_comprehensive(lead_id)
    except Exception as e:
        logger.error(f"❌ Lead enrichment failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'lead_id': lead_id
        }


def enrich_leads_batch(limit: int = None, openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform batch lead enrichment.
    
    Args:
        limit: Maximum number of leads to enrich
        openai_api_key: Optional OpenAI API key
        
    Returns:
        Batch enrichment result dictionary
    """
    try:
        enricher = EnhancedEnricherIntegration(openai_api_key)
        return enricher.enrich_leads_batch(limit)
    except Exception as e:
        logger.error(f"❌ Batch enrichment failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'leads_processed': 0,
            'enrichment_successful': 0,
            'enrichment_failed': 1
        }


if __name__ == "__main__":
    # Test the enhanced enricher integration
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Enhanced Enricher Integration')
    parser.add_argument('--lead-id', help='Enrich specific lead ID')
    parser.add_argument('--batch', action='store_true', help='Enrich batch of leads')
    parser.add_argument('--limit', type=int, default=5, help='Limit for batch enrichment')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.lead_id:
        # Enrich specific lead
        print(f"🧠 Enriching lead: {args.lead_id}")
        result = enrich_lead_comprehensive(args.lead_id)
        print(f"📊 Result: {result}")
    
    elif args.batch:
        # Enrich batch of leads
        print(f"🧠 Enriching batch of leads (limit: {args.limit})")
        result = enrich_leads_batch(args.limit)
        print(f"📊 Batch Result: {result}")
    
    else:
        print("❌ Please specify --lead-id or --batch")
        print("Usage examples:")
        print("  python enhanced_enricher_integration.py --lead-id lead-123")
        print("  python enhanced_enricher_integration.py --batch --limit 10")