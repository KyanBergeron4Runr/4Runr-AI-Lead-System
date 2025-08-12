#!/usr/bin/env python3
"""
Simple Enricher Agent for the 4Runr Autonomous Outreach System.

This agent performs basic enrichment using existing data patterns and LinkedIn URLs
without requiring Google search. It integrates with the comprehensive DataCleaner
system to ensure high-quality, professional data output.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import re

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.airtable_client import get_airtable_client
from shared.logging_utils import get_logger
from shared.config import config
from shared.data_cleaner import DataCleaner


class SimpleEnricherAgent:
    """Simple Enricher Agent for basic lead enrichment without Google search."""
    
    def __init__(self):
        """Initialize the Simple Enricher Agent."""
        self.logger = get_logger('simple_enricher')
        self.airtable_client = get_airtable_client()
        self.system_config = config.get_system_config()
        
        # Initialize DataCleaner for comprehensive data cleaning and validation
        try:
            self.data_cleaner = DataCleaner()
            self.logger.log_module_activity('simple_enricher', 'system', 'success', {
                'message': 'DataCleaner initialized successfully',
                'data_quality_enabled': True
            })
        except Exception as e:
            self.logger.log_error(e, {'action': 'initialize_data_cleaner'})
            self.data_cleaner = None
            self.logger.log_module_activity('simple_enricher', 'system', 'warning', {
                'message': 'DataCleaner initialization failed, falling back to basic validation',
                'data_quality_enabled': False
            })
    
    async def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads using simple enrichment methods.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads that need enrichment (missing company or website)
        batch_size = limit or self.system_config['batch_size']
        leads = self._get_leads_needing_enrichment(batch_size)
        
        if not leads:
            self.logger.log_module_activity('simple_enricher', 'system', 'info', 
                                           {'message': 'No leads found that need simple enrichment'})
            return {'processed': 0, 'successful': 0, 'errors': 0}
        
        self.logger.log_pipeline_start(len(leads))
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0}
        
        for i, lead in enumerate(leads):
            try:
                # Log progress
                self.logger.log_batch_progress(i + 1, len(leads))
                
                # Process individual lead
                success = await self._process_single_lead(lead)
                
                stats['processed'] += 1
                if success:
                    stats['successful'] += 1
                else:
                    stats['errors'] += 1
                
                # Rate limiting (lighter than Google enricher)
                if i < len(leads) - 1:  # Don't delay after the last lead
                    await asyncio.sleep(0.5)  # Shorter delay for simple enrichment
                    
            except Exception as e:
                self.logger.log_error(e, {
                    'action': 'process_leads',
                    'lead_id': lead.get('id', 'unknown'),
                    'lead_index': i
                })
                stats['processed'] += 1
                stats['errors'] += 1
        
        self.logger.log_pipeline_complete(stats['processed'], stats['successful'], stats['errors'])
        return stats
    
    def _get_leads_needing_enrichment(self, limit: int) -> List[Dict[str, Any]]:
        """Get leads that need simple enrichment (missing company or website info)."""
        try:
            # Get leads with names but missing company info or website
            formula = "AND(NOT({Full Name} = ''), OR({Company} = '', {Website} = ''))"
            
            records = self.airtable_client.table.all(
                formula=formula,
                max_records=limit
            )
            
            leads = []
            for record in records:
                lead_data = {
                    'id': record['id'],
                    **record['fields']
                }
                leads.append(lead_data)
            
            self.logger.log_module_activity('airtable_client', 'system', 'success', 
                                           {'message': f'Retrieved {len(leads)} records', 
                                            'formula': formula, 'max_records': limit})
            return leads
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_leads_needing_enrichment'})
            return []
    
    async def _process_single_lead(self, lead: Dict[str, Any]) -> bool:
        """
        Process a single lead using simple enrichment methods.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        full_name = lead.get('Full Name', '')
        current_company = lead.get('Company', '')
        current_website = lead.get('Website', '')
        linkedin_url = lead.get('LinkedIn URL', '')
        
        self.logger.log_module_activity('simple_enricher', lead_id, 'start', 
                                       {'message': f'Processing {full_name}', 
                                        'current_company': current_company,
                                        'current_website': current_website,
                                        'enrichment_method': 'simple_patterns'})
        
        # Validate we have a name to work with
        if not full_name or len(full_name.strip()) < 3:
            self.logger.log_module_activity('simple_enricher', lead_id, 'skip', 
                                           {'message': 'Invalid or missing full name'})
            return False
        
        try:
            enrichment_data = {}
            
            # Try LinkedIn-based enrichment
            if linkedin_url and not current_company:
                linkedin_company = self._extract_company_from_linkedin(linkedin_url, full_name)
                if linkedin_company:
                    enrichment_data['Company'] = linkedin_company
                    self.logger.log_module_activity('simple_enricher', lead_id, 'info', {
                        'message': f'Extracted company from LinkedIn: {linkedin_company}',
                        'linkedin_url': linkedin_url
                    })
            
            # Try name pattern-based website generation
            if not current_website:
                pattern_website = self._generate_website_from_name_patterns(full_name, current_company)
                if pattern_website:
                    enrichment_data['Website'] = pattern_website
                    self.logger.log_module_activity('simple_enricher', lead_id, 'info', {
                        'message': f'Generated website from patterns: {pattern_website}',
                        'full_name': full_name
                    })
            
            # Update Airtable if we found new information
            if enrichment_data:
                # Prepare raw data for cleaning and validation
                raw_data = {}
                
                # Only include fields that are currently empty and we found new data for
                if not current_company and enrichment_data.get('Company'):
                    raw_data['Company'] = enrichment_data['Company']
                
                if not current_website and enrichment_data.get('Website'):
                    raw_data['Website'] = enrichment_data['Website']
                
                if raw_data:
                    # Use DataCleaner for comprehensive cleaning and validation
                    if self.data_cleaner:
                        try:
                            # Create lead context for validation
                            lead_context = {
                                'id': lead_id,
                                'Full Name': full_name,
                                'LinkedIn URL': linkedin_url,
                                'source': 'simple_enricher'
                            }
                            
                            # Clean and validate the data using our comprehensive system
                            cleaning_result = self.data_cleaner.clean_and_validate(raw_data, lead_context)
                            
                            if cleaning_result.success:
                                # Use the cleaned data for Airtable update
                                airtable_fields = cleaning_result.cleaned_data
                                
                                # Log comprehensive cleaning results
                                self.logger.log_module_activity('simple_enricher', lead_id, 'info', {
                                    'message': f'DataCleaner processed data for {full_name}',
                                    'original_data': raw_data,
                                    'cleaned_data': airtable_fields,
                                    'cleaning_actions': len(cleaning_result.cleaning_actions),
                                    'validation_results': len(cleaning_result.validation_results),
                                    'confidence_score': cleaning_result.confidence_score
                                })
                                
                                # Update Airtable with cleaned data
                                if airtable_fields:
                                    self.logger.log_module_activity('simple_enricher', lead_id, 'info', {
                                        'message': f'UPDATING AIRTABLE for {full_name} with cleaned data',
                                        'fields_to_update': airtable_fields,
                                        'data_quality_score': cleaning_result.confidence_score,
                                        'cleaning_system': 'DataCleaner v2.0'
                                    })
                                    
                                    update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
                                    
                                    if update_success:
                                        self.logger.log_module_activity('simple_enricher', lead_id, 'success', {
                                            'message': f'✅ SUCCESSFULLY ENRICHED {full_name} with DataCleaner',
                                            'enriched_fields': list(airtable_fields.keys()),
                                            'company': airtable_fields.get('Company'),
                                            'website': airtable_fields.get('Website'),
                                            'confidence_score': cleaning_result.confidence_score,
                                            'data_quality': 'PROFESSIONAL GRADE - DataCleaner validated',
                                            'enrichment_method': 'simple_patterns'
                                        })
                                        return True
                                    else:
                                        self.logger.log_module_activity('simple_enricher', lead_id, 'error', {
                                            'message': 'Failed to update Airtable with cleaned data'
                                        })
                                        return False
                                else:
                                    self.logger.log_module_activity('simple_enricher', lead_id, 'skip', {
                                        'message': 'No data remaining after DataCleaner processing'
                                    })
                                    return False
                            else:
                                # Data was rejected by DataCleaner
                                self.logger.log_module_activity('simple_enricher', lead_id, 'warning', {
                                    'message': f'DataCleaner rejected data for {full_name}',
                                    'original_data': raw_data,
                                    'rejection_reasons': cleaning_result.rejection_reasons,
                                    'confidence_score': cleaning_result.confidence_score
                                })
                                return False
                                
                        except Exception as e:
                            self.logger.log_error(e, {
                                'action': 'data_cleaner_processing',
                                'lead_id': lead_id,
                                'raw_data': raw_data
                            })
                            
                            # Fallback to basic validation if DataCleaner fails
                            self.logger.log_module_activity('simple_enricher', lead_id, 'warning', {
                                'message': 'DataCleaner failed, falling back to basic validation'
                            })
                            return self._fallback_validation_and_update(lead_id, full_name, raw_data)
                    else:
                        # DataCleaner not available, use fallback validation
                        return self._fallback_validation_and_update(lead_id, full_name, raw_data)
                else:
                    self.logger.log_module_activity('simple_enricher', lead_id, 'skip', {
                        'message': 'No new data to process - all fields already populated'
                    })
                    return False
            else:
                self.logger.log_module_activity('simple_enricher', lead_id, 'skip', 
                                               {'message': 'No enrichment data found via simple patterns'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'full_name': full_name
            })
            return False
    
    def _extract_company_from_linkedin(self, linkedin_url: str, full_name: str) -> str:
        """
        Extract company information from LinkedIn URL.
        
        Args:
            linkedin_url: LinkedIn profile URL
            full_name: Person's full name for validation
            
        Returns:
            Company name if found, None otherwise
        """
        try:
            if not linkedin_url or 'linkedin.com' not in linkedin_url.lower():
                return None
            
            # Pattern 1: LinkedIn company URLs in profile
            # Sometimes profiles contain company URLs like /company/microsoft
            company_match = re.search(r'/company/([^/?]+)', linkedin_url)
            if company_match:
                company_slug = company_match.group(1)
                # Convert slug to company name
                company_name = company_slug.replace('-', ' ').title()
                
                # Basic validation - must look like a real company
                if len(company_name) > 2 and not company_name.lower() in ['linkedin', 'profile', 'user']:
                    return company_name
            
            # Pattern 2: Extract from profile URL structure
            # Some LinkedIn URLs contain company info in the path
            if '/in/' in linkedin_url:
                # Look for patterns like linkedin.com/in/john-doe-microsoft
                profile_part = linkedin_url.split('/in/')[-1].split('/')[0]
                parts = profile_part.split('-')
                
                # Look for company indicators in the profile slug
                name_parts = full_name.lower().split()
                company_indicators = []
                
                for part in parts:
                    part_lower = part.lower()
                    # Skip parts that are likely name components
                    if part_lower not in name_parts and len(part) > 2:
                        # Check if it looks like a company name
                        if not part_lower in ['linkedin', 'profile', 'user', 'www', 'com']:
                            company_indicators.append(part.title())
                
                if company_indicators:
                    # Take the last non-name part as potential company
                    potential_company = ' '.join(company_indicators[-1:])
                    if len(potential_company) > 2:
                        return potential_company
            
            return None
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'extract_company_from_linkedin',
                'linkedin_url': linkedin_url
            })
            return None
    
    def _generate_website_from_name_patterns(self, full_name: str, current_company: str) -> str:
        """
        Generate potential website URLs from name and company patterns.
        
        Args:
            full_name: Person's full name
            current_company: Current company name (if any)
            
        Returns:
            Generated website URL if pattern looks valid, None otherwise
        """
        try:
            name_parts = full_name.strip().split()
            if len(name_parts) < 2:
                return None
            
            first_name = name_parts[0].lower()
            last_name = name_parts[-1].lower()
            
            # Clean names for URL generation
            first_clean = re.sub(r'[^a-z]', '', first_name)
            last_clean = re.sub(r'[^a-z]', '', last_name)
            
            if len(first_clean) < 2 or len(last_clean) < 2:
                return None
            
            # Strategy 1: Use company name if it suggests a personal business
            if current_company:
                company_lower = current_company.lower()
                # Look for patterns that suggest personal businesses
                personal_indicators = [
                    '& associates', '& partners', 'consulting', 'law firm', 
                    'attorney', 'lawyer', 'cpa', 'accountant', 'financial',
                    first_name, last_name
                ]
                
                if any(indicator in company_lower for indicator in personal_indicators):
                    # Generate website based on company name
                    company_clean = re.sub(r'[^a-z\s]', '', company_lower)
                    company_words = company_clean.split()
                    
                    # Filter out common business words
                    business_words = ['inc', 'corp', 'llc', 'ltd', 'company', 'co', 'and', 'the']
                    meaningful_words = [w for w in company_words if w not in business_words and len(w) > 2]
                    
                    if meaningful_words:
                        domain_base = ''.join(meaningful_words[:2])  # Take first 2 meaningful words
                        if len(domain_base) >= 4:
                            return f"https://{domain_base}.com"
            
            # Strategy 2: Generate from name patterns
            potential_domains = [
                f"{first_clean}{last_clean}",      # johnsmith
                f"{first_clean}-{last_clean}",     # john-smith
                f"{last_clean}",                   # smith (if it's a common business name)
                f"{first_clean[0]}{last_clean}",   # jsmith
            ]
            
            # Validate domain patterns
            for domain_base in potential_domains:
                if len(domain_base) >= 4 and len(domain_base) <= 20:
                    # Prefer .com for business websites
                    website = f"https://{domain_base}.com"
                    
                    # Basic validation - avoid obviously personal patterns
                    if not self._looks_like_personal_website(domain_base, first_name, last_name):
                        return website
            
            return None
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'generate_website_from_name_patterns',
                'full_name': full_name
            })
            return None
    
    def _looks_like_personal_website(self, domain_base: str, first_name: str, last_name: str) -> bool:
        """
        Check if a domain looks too personal (not business-like).
        
        Args:
            domain_base: The domain base (without .com)
            first_name: Person's first name
            last_name: Person's last name
            
        Returns:
            True if it looks too personal, False if it could be business
        """
        try:
            domain_lower = domain_base.lower()
            
            # If it's just firstname+lastname, it might be too personal
            if domain_lower == f"{first_name}{last_name}":
                # But some professionals use this pattern for business
                # Allow it if the last name could be a business name
                business_last_names = [
                    'smith', 'johnson', 'brown', 'davis', 'miller', 'wilson',
                    'moore', 'taylor', 'anderson', 'thomas', 'jackson', 'white'
                ]
                return last_name.lower() in business_last_names
            
            # If it's just the last name, it could be a business
            if domain_lower == last_name.lower():
                return False  # Could be a business
            
            # If it has hyphens or is abbreviated, it's more likely business
            if '-' in domain_lower or len(domain_lower) <= 8:
                return False  # Likely business
            
            return True  # Probably too personal
            
        except Exception as e:
            return True  # Default to personal if we can't determine
    
    def _fallback_validation_and_update(self, lead_id: str, full_name: str, raw_data: Dict[str, str]) -> bool:
        """
        Fallback validation and update when DataCleaner is not available.
        
        Args:
            lead_id: Lead ID
            full_name: Person's full name
            raw_data: Raw data to validate and update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            airtable_fields = {}
            
            # Use basic validation for each field
            for field_name, value in raw_data.items():
                if field_name == 'Company':
                    if self._basic_company_validation(value):
                        airtable_fields['Company'] = value
                    else:
                        self.logger.log_module_activity('simple_enricher', lead_id, 'warning', {
                            'message': f'Company {value} failed basic validation for {full_name}'
                        })
                elif field_name == 'Website':
                    if self._basic_website_validation(value):
                        airtable_fields['Website'] = value
                    else:
                        self.logger.log_module_activity('simple_enricher', lead_id, 'warning', {
                            'message': f'Website {value} failed basic validation for {full_name}'
                        })
            
            if airtable_fields:
                self.logger.log_module_activity('simple_enricher', lead_id, 'info', {
                    'message': f'UPDATING AIRTABLE for {full_name} with basic validation',
                    'fields_to_update': airtable_fields,
                    'validation_method': 'FALLBACK - Basic validation only'
                })
                
                update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
                
                if update_success:
                    self.logger.log_module_activity('simple_enricher', lead_id, 'success', {
                        'message': f'✅ SUCCESSFULLY ENRICHED {full_name} with basic validation',
                        'enriched_fields': list(airtable_fields.keys()),
                        'company': airtable_fields.get('Company'),
                        'website': airtable_fields.get('Website'),
                        'data_quality': 'BASIC - Fallback validation only',
                        'enrichment_method': 'simple_patterns'
                    })
                    return True
                else:
                    self.logger.log_module_activity('simple_enricher', lead_id, 'error', {
                        'message': 'Failed to update Airtable with basic validation'
                    })
                    return False
            else:
                self.logger.log_module_activity('simple_enricher', lead_id, 'skip', {
                    'message': 'No data passed basic validation'
                })
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'fallback_validation_and_update',
                'lead_id': lead_id,
                'raw_data': raw_data
            })
            return False
    
    def _basic_company_validation(self, company: str) -> bool:
        """Basic company name validation."""
        if not company or len(company.strip()) < 3:
            return False
        
        # Check for obvious bad values
        bad_indicators = [
            'linkedin', 'facebook', 'twitter', 'google', 'search', 'results',
            'unknown', 'not found', 'error', 'none', 'null', 'undefined'
        ]
        
        company_lower = company.lower()
        if any(bad in company_lower for bad in bad_indicators):
            return False
        
        return True
    
    def _basic_website_validation(self, website: str) -> bool:
        """Basic website URL validation."""
        if not website or not website.startswith('http'):
            return False
        
        # Check for obviously wrong domains
        bad_domains = [
            'linkedin.com', 'facebook.com', 'twitter.com', 'google.com',
            'example.com', 'test.com'
        ]
        
        if any(bad_domain in website.lower() for bad_domain in bad_domains):
            return False
        
        return True


async def main():
    """Main entry point for the Simple Enricher Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Simple Enricher Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    
    args = parser.parse_args()
    
    agent = SimpleEnricherAgent()
    
    if args.stats:
        leads = agent._get_leads_needing_enrichment(1000)
        print(f"Simple Enricher Statistics:")
        print(f"  Leads needing enrichment: {len(leads)}")
        return True
    
    # Process leads in batch
    results = await agent.process_leads(limit=args.limit)
    
    print(f"Simple Enricher Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)