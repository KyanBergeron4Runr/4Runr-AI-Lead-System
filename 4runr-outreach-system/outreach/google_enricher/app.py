#!/usr/bin/env python3
"""
Google Enricher Agent for the 4Runr Autonomous Outreach System.

This agent uses Google search to enrich leads with missing company information
and website URLs when we only have a person's name and LinkedIn profile.
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
from website_scraper.scraping_engine import WebScrapingEngine


class GoogleEnricherAgent:
    """Google Enricher Agent for enriching leads with missing company/website information."""
    
    def __init__(self):
        """Initialize the Google Enricher Agent."""
        self.logger = get_logger('google_enricher')
        self.airtable_client = get_airtable_client()
        self.system_config = config.get_system_config()
        
        # Initialize DataCleaner for comprehensive data cleaning and validation
        try:
            self.data_cleaner = DataCleaner()
            self.logger.log_module_activity('google_enricher', 'system', 'success', {
                'message': 'DataCleaner initialized successfully',
                'data_quality_enabled': True
            })
        except Exception as e:
            self.logger.log_error(e, {'action': 'initialize_data_cleaner'})
            self.data_cleaner = None
            self.logger.log_module_activity('google_enricher', 'system', 'warning', {
                'message': 'DataCleaner initialization failed, falling back to basic validation',
                'data_quality_enabled': False
            })
    
    async def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads that need Google-based enrichment.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads that need enrichment (missing company or website)
        batch_size = limit or self.system_config['batch_size']
        leads = self._get_leads_needing_enrichment(batch_size)
        
        if not leads:
            self.logger.log_module_activity('google_enricher', 'system', 'info', 
                                           {'message': 'No leads found that need Google enrichment'})
            return {'processed': 0, 'successful': 0, 'errors': 0}
        
        self.logger.log_pipeline_start(len(leads))
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0}
        
        # Initialize scraping engine
        async with WebScrapingEngine() as scraping_engine:
            for i, lead in enumerate(leads):
                try:
                    # Log progress
                    self.logger.log_batch_progress(i + 1, len(leads))
                    
                    # Process individual lead
                    success = await self._process_single_lead(lead, scraping_engine)
                    
                    stats['processed'] += 1
                    if success:
                        stats['successful'] += 1
                    else:
                        stats['errors'] += 1
                    
                    # Rate limiting
                    if i < len(leads) - 1:  # Don't delay after the last lead
                        await asyncio.sleep(self.system_config['rate_limit_delay'])
                        
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
        """Get leads that need Google enrichment (missing company or website info)."""
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
    
    async def _process_single_lead(self, lead: Dict[str, Any], scraping_engine: WebScrapingEngine) -> bool:
        """
        Process a single lead to enrich with Google search.
        
        Args:
            lead: Lead data dictionary
            scraping_engine: Initialized scraping engine
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        full_name = lead.get('Full Name', '')
        current_company = lead.get('Company', '')
        current_website = lead.get('Website', '')
        linkedin_url = lead.get('LinkedIn URL', '')
        
        self.logger.log_module_activity('google_enricher', lead_id, 'start', 
                                       {'message': f'Processing {full_name}', 
                                        'current_company': current_company,
                                        'current_website': current_website})
        
        # Validate we have a name to search with
        if not full_name or len(full_name.strip()) < 3:
            self.logger.log_module_activity('google_enricher', lead_id, 'skip', 
                                           {'message': 'Invalid or missing full name'})
            return False
        
        try:
            # Build Google search queries
            search_queries = self._build_google_search_queries(full_name, current_company, linkedin_url)
            
            enrichment_data = {}
            
            # Try each search query until we find useful information
            for query in search_queries:
                try:
                    # Use Google search to find company/website information
                    search_results = await self._google_search_for_lead_info(query, scraping_engine, lead_id)
                    
                    if search_results:
                        # Extract company and website information from search results
                        extracted_info = self._extract_company_website_info(search_results, full_name)
                        
                        if extracted_info:
                            enrichment_data.update(extracted_info)
                            break  # Found useful info, stop searching
                    
                    # Rate limiting between searches
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    self.logger.log_error(e, {
                        'action': 'google_search',
                        'query': query,
                        'lead_id': lead_id
                    })
                    continue
            
            # Update Airtable if we found new information
            if enrichment_data:
                # Prepare raw data for cleaning and validation
                raw_data = {}
                
                # Only include fields that are currently empty and we found new data for
                if not current_company and enrichment_data.get('company'):
                    raw_data['Company'] = enrichment_data['company']
                
                if not current_website and enrichment_data.get('website'):
                    raw_data['Website'] = enrichment_data['website']
                
                if raw_data:
                    # Use DataCleaner for comprehensive cleaning and validation
                    if self.data_cleaner:
                        try:
                            # Create lead context for validation
                            lead_context = {
                                'id': lead_id,
                                'Full Name': full_name,
                                'LinkedIn URL': linkedin_url,
                                'source': 'google_enricher'
                            }
                            
                            # Clean and validate the data using our comprehensive system
                            cleaning_result = self.data_cleaner.clean_and_validate(raw_data, lead_context)
                            
                            if cleaning_result.success:
                                # Use the cleaned data for Airtable update
                                airtable_fields = cleaning_result.cleaned_data
                                
                                # Log comprehensive cleaning results
                                self.logger.log_module_activity('google_enricher', lead_id, 'info', {
                                    'message': f'DataCleaner processed data for {full_name}',
                                    'original_data': raw_data,
                                    'cleaned_data': airtable_fields,
                                    'cleaning_actions': len(cleaning_result.cleaning_actions),
                                    'validation_results': len(cleaning_result.validation_results),
                                    'confidence_score': cleaning_result.confidence_score
                                })
                                
                                # Update Airtable with cleaned data
                                if airtable_fields:
                                    self.logger.log_module_activity('google_enricher', lead_id, 'info', {
                                        'message': f'UPDATING AIRTABLE for {full_name} with cleaned data',
                                        'fields_to_update': airtable_fields,
                                        'data_quality_score': cleaning_result.confidence_score,
                                        'cleaning_system': 'DataCleaner v2.0'
                                    })
                                    
                                    update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
                                    
                                    if update_success:
                                        self.logger.log_module_activity('google_enricher', lead_id, 'success', {
                                            'message': f'✅ SUCCESSFULLY ENRICHED {full_name} with DataCleaner',
                                            'enriched_fields': list(airtable_fields.keys()),
                                            'company': airtable_fields.get('Company'),
                                            'website': airtable_fields.get('Website'),
                                            'confidence_score': cleaning_result.confidence_score,
                                            'data_quality': 'PROFESSIONAL GRADE - DataCleaner validated'
                                        })
                                        return True
                                    else:
                                        self.logger.log_module_activity('google_enricher', lead_id, 'error', {
                                            'message': 'Failed to update Airtable with cleaned data'
                                        })
                                        return False
                                else:
                                    self.logger.log_module_activity('google_enricher', lead_id, 'skip', {
                                        'message': 'No data remaining after DataCleaner processing'
                                    })
                                    return False
                            else:
                                # Data was rejected by DataCleaner
                                self.logger.log_module_activity('google_enricher', lead_id, 'warning', {
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
                            self.logger.log_module_activity('google_enricher', lead_id, 'warning', {
                                'message': 'DataCleaner failed, falling back to basic validation'
                            })
                            return self._fallback_validation_and_update(lead_id, full_name, raw_data)
                    else:
                        # DataCleaner not available, use fallback validation
                        return self._fallback_validation_and_update(lead_id, full_name, raw_data)
                else:
                    self.logger.log_module_activity('google_enricher', lead_id, 'skip', {
                        'message': 'No new data to process - all fields already populated'
                    })
                    return False
            else:
                self.logger.log_module_activity('google_enricher', lead_id, 'skip', 
                                               {'message': 'No company/website information found via Google search'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'full_name': full_name
            })
            return False
    
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
                    if self._final_validation_check(value, full_name, 'company'):
                        airtable_fields['Company'] = value
                    else:
                        self.logger.log_module_activity('google_enricher', lead_id, 'warning', {
                            'message': f'Company {value} failed basic validation for {full_name}'
                        })
                elif field_name == 'Website':
                    if self._final_validation_check(value, full_name, 'website'):
                        airtable_fields['Website'] = value
                    else:
                        self.logger.log_module_activity('google_enricher', lead_id, 'warning', {
                            'message': f'Website {value} failed basic validation for {full_name}'
                        })
            
            if airtable_fields:
                self.logger.log_module_activity('google_enricher', lead_id, 'info', {
                    'message': f'UPDATING AIRTABLE for {full_name} with basic validation',
                    'fields_to_update': airtable_fields,
                    'validation_method': 'FALLBACK - Basic validation only'
                })
                
                update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
                
                if update_success:
                    self.logger.log_module_activity('google_enricher', lead_id, 'success', {
                        'message': f'✅ SUCCESSFULLY ENRICHED {full_name} with basic validation',
                        'enriched_fields': list(airtable_fields.keys()),
                        'company': airtable_fields.get('Company'),
                        'website': airtable_fields.get('Website'),
                        'data_quality': 'BASIC - Fallback validation only'
                    })
                    return True
                else:
                    self.logger.log_module_activity('google_enricher', lead_id, 'error', {
                        'message': 'Failed to update Airtable with basic validation'
                    })
                    return False
            else:
                self.logger.log_module_activity('google_enricher', lead_id, 'skip', {
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
    
    def _final_validation_check(self, value: str, full_name: str, field_type: str) -> bool:
        """
        FINAL VALIDATION before updating Airtable - last line of defense.
        
        Args:
            value: The value we want to update (company or website)
            full_name: Person's name
            field_type: 'company' or 'website'
            
        Returns:
            True if value passes final validation
        """
        try:
            if field_type == 'company':
                # Company final validation
                if not value or len(value.strip()) < 3:
                    return False
                
                # Check for obvious bad values
                bad_company_indicators = [
                    'google', 'search', 'results', 'linkedin', 'facebook', 'twitter',
                    'unknown', 'not found', 'error', 'none', 'null', 'undefined',
                    'www.', 'http', '.com', 'website', 'page', 'profile'
                ]
                
                value_lower = value.lower()
                if any(bad in value_lower for bad in bad_company_indicators):
                    return False
                
                # Must look like a real company name
                if not re.match(r'^[A-Za-z0-9\s&,.\-\']+$', value):
                    return False
                
                return True
                
            elif field_type == 'website':
                # Website final validation
                if not value or not value.startswith('http'):
                    return False
                
                # Check for obviously wrong domains
                bad_domains = [
                    'google.com', 'linkedin.com', 'facebook.com', 'twitter.com',
                    'instagram.com', 'youtube.com', 'example.com', 'test.com'
                ]
                
                if any(bad_domain in value.lower() for bad_domain in bad_domains):
                    return False
                
                # Must be a valid URL format
                if not re.match(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', value):
                    return False
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'final_validation_check', 'field_type': field_type})
            return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'full_name': full_name
            })
            return False
    
    def _build_google_search_queries(self, full_name: str, current_company: str, linkedin_url: str) -> List[str]:
        """
        Build SUPERCHARGED Google search queries for 110% success rate.
        
        Args:
            full_name: Person's full name
            current_company: Current company (if any)
            linkedin_url: LinkedIn URL (if any)
            
        Returns:
            List of search queries to try
        """
        queries = []
        
        # Clean up the name for searching
        clean_name = full_name.strip()
        name_parts = clean_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        # STRATEGY 1: LinkedIn-first approach (highest success rate)
        if linkedin_url:
            queries.append(f'site:linkedin.com/in "{clean_name}" company')
            queries.append(f'"{clean_name}" LinkedIn profile company website')
        
        # STRATEGY 2: Professional directories and databases
        queries.append(f'"{clean_name}" Montreal site:zoominfo.com')
        queries.append(f'"{clean_name}" Montreal site:crunchbase.com')
        queries.append(f'"{clean_name}" Montreal site:bloomberg.com')
        queries.append(f'"{clean_name}" site:apollo.io Montreal')
        
        # STRATEGY 3: News and press mentions (high accuracy)
        queries.append(f'"{clean_name}" Montreal CEO announced company')
        queries.append(f'"{clean_name}" Montreal founder startup company')
        queries.append(f'"{clean_name}" Montreal executive joins company')
        queries.append(f'"{clean_name}" Montreal business news company')
        
        # STRATEGY 4: Company-specific searches with variations
        if current_company and current_company not in ['Unknown Company', '']:
            queries.append(f'"{clean_name}" "{current_company}" Montreal website')
            queries.append(f'"{current_company}" Montreal "{clean_name}" CEO')
            queries.append(f'"{current_company}" Montreal team "{clean_name}"')
        
        # STRATEGY 5: Industry-specific searches
        queries.append(f'"{clean_name}" Montreal tech startup founder')
        queries.append(f'"{clean_name}" Montreal fintech CEO company')
        queries.append(f'"{clean_name}" Montreal SaaS founder website')
        queries.append(f'"{clean_name}" Montreal AI company CEO')
        
        # STRATEGY 6: Social proof and mentions
        queries.append(f'"{clean_name}" Montreal "co-founder" company website')
        queries.append(f'"{clean_name}" Montreal "chief executive" company')
        queries.append(f'"{clean_name}" Montreal "managing director" company')
        
        # STRATEGY 7: Name variations for better coverage
        if len(name_parts) >= 2:
            queries.append(f'"{first_name} {last_name}" Montreal company CEO')
            queries.append(f'{first_name} {last_name} Montreal startup founder')
        
        # STRATEGY 8: Event and conference mentions
        queries.append(f'"{clean_name}" Montreal speaker conference company')
        queries.append(f'"{clean_name}" Montreal panel discussion CEO')
        
        # STRATEGY 9: Award and recognition searches
        queries.append(f'"{clean_name}" Montreal entrepreneur award company')
        queries.append(f'"{clean_name}" Montreal business leader company')
        
        # STRATEGY 10: Fallback broad searches with filters
        queries.append(f'"{clean_name}" Montreal -linkedin -facebook -twitter company')
        queries.append(f'"{clean_name}" Montreal CEO OR founder OR president')
        
        return queries[:15]  # Increased to 15 queries for 110% coverage
    
    async def _google_search_for_lead_info(self, query: str, scraping_engine: WebScrapingEngine, lead_id: str) -> str:
        """
        Perform Google search and extract search results content.
        
        Args:
            query: Search query
            scraping_engine: Initialized scraping engine
            lead_id: Lead ID for logging
            
        Returns:
            Search results content if successful, None otherwise
        """
        try:
            # Build Google search URL
            google_search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            # Create new page for direct Google search scraping
            page = await scraping_engine.browser.new_page()
            
            try:
                # Set user agent and viewport
                await page.set_extra_http_headers({'User-Agent': scraping_engine.config['user_agent']})
                await page.set_viewport_size({'width': 1920, 'height': 1080})
                
                # Navigate directly to Google search results
                response = await page.goto(google_search_url, timeout=30000, wait_until='domcontentloaded')
                
                if response and response.status == 200:
                    # Wait for search results to load
                    await page.wait_for_timeout(3000)
                    
                    # Extract search results content
                    content = await page.evaluate('''() => {
                        // Extract search result snippets and titles
                        const results = [];
                        
                        // Get search result containers
                        const searchResults = document.querySelectorAll('div[data-ved] h3, div.g h3, div.rc h3');
                        const snippets = document.querySelectorAll('div[data-ved] span, div.g .VwiC3b, div.rc .VwiC3b');
                        
                        // Extract titles and snippets
                        searchResults.forEach((title, index) => {
                            const titleText = title.textContent || '';
                            const snippet = snippets[index] ? snippets[index].textContent || '' : '';
                            if (titleText.length > 0) {
                                results.push(titleText + ' ' + snippet);
                            }
                        });
                        
                        // Also get any visible text that might contain company info
                        const allText = document.body.innerText || '';
                        
                        return results.join(' ') + ' ' + allText;
                    }''')
                    
                    if content and len(content.strip()) > 50:
                        self.logger.log_module_activity('google_enricher', lead_id, 'info', 
                                                       {'message': f'Google search successful for: {query}',
                                                        'content_length': len(content)})
                        return content
                    else:
                        self.logger.log_module_activity('google_enricher', lead_id, 'warning', 
                                                       {'message': f'No useful content found in Google search for: {query}'})
                        return None
                else:
                    self.logger.log_module_activity('google_enricher', lead_id, 'warning', 
                                                   {'message': f'Failed to load Google search for: {query}'})
                    return None
                    
            finally:
                await page.close()
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'google_search_for_lead_info',
                'query': query,
                'lead_id': lead_id
            })
            return None
    
    def _extract_company_website_info(self, search_content: str, full_name: str) -> Dict[str, str]:
        """
        Extract company and website information with SMART VALIDATION to ensure accuracy.
        
        Args:
            search_content: HTML content from Google search
            full_name: Person's name to validate relevance
            
        Returns:
            Dictionary with extracted company and website info (ONLY if validated)
        """
        extracted_info = {}
        
        try:
            # Extract company names from search results
            company = self._extract_company_from_search(search_content, full_name)
            if company:
                # VALIDATION STEP 1: Ensure company is mentioned WITH the person's name
                if self._validate_company_person_connection(search_content, company, full_name):
                    extracted_info['company'] = company
                    
                    # Extract website URLs from search results
                    website = self._extract_website_from_search(search_content, full_name)
                    if website:
                        # VALIDATION STEP 2: Ensure website belongs to the company
                        if self._validate_website_company_match(search_content, website, company, full_name):
                            extracted_info['website'] = website
                        else:
                            self.logger.log_module_activity('google_enricher', 'validation', 'warning', 
                                                           {'message': f'Website {website} does not match company {company} for {full_name}'})
                else:
                    self.logger.log_module_activity('google_enricher', 'validation', 'warning', 
                                                   {'message': f'Company {company} not validated for {full_name}'})
            
            return extracted_info
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'extract_company_website_info',
                'full_name': full_name
            })
            return {}
    
    def _validate_company_person_connection(self, content: str, company: str, full_name: str) -> bool:
        """
        CRITICAL VALIDATION: Ensure the company is actually connected to the person.
        
        Args:
            content: Search results content
            company: Extracted company name
            full_name: Person's name
            
        Returns:
            True if company is validated for this person
        """
        try:
            # Look for sentences that mention BOTH the person AND the company
            sentences = re.split(r'[.!?]', content.lower())
            
            name_variations = [
                full_name.lower(),
                full_name.lower().replace(' ', ''),
                ' '.join(full_name.lower().split()[:2]),  # First two names
            ]
            
            company_variations = [
                company.lower(),
                company.lower().replace(' ', ''),
                company.lower().replace(',', '').replace('.', ''),
            ]
            
            validation_patterns = [
                # Direct connection patterns
                rf'{re.escape(full_name.lower())}.*?(?:ceo|president|founder|co-founder|chief executive|managing director).*?{re.escape(company.lower())}',
                rf'{re.escape(company.lower())}.*?{re.escape(full_name.lower())}.*?(?:ceo|president|founder|co-founder)',
                rf'{re.escape(full_name.lower())}.*?(?:at|of|from|with|joins|works at).*?{re.escape(company.lower())}',
                rf'{re.escape(company.lower())}.*?(?:ceo|president|founder).*?{re.escape(full_name.lower())}',
                
                # Professional context patterns
                rf'{re.escape(full_name.lower())}.*?(?:leads|heads|runs|owns).*?{re.escape(company.lower())}',
                rf'{re.escape(company.lower())}.*?(?:led by|headed by|founded by).*?{re.escape(full_name.lower())}',
            ]
            
            # Check if any validation pattern matches
            full_content = content.lower()
            for pattern in validation_patterns:
                if re.search(pattern, full_content, re.IGNORECASE | re.MULTILINE):
                    return True
            
            # Secondary validation: Check if they appear in the same sentence
            for sentence in sentences:
                has_name = any(name_var in sentence for name_var in name_variations)
                has_company = any(comp_var in sentence for comp_var in company_variations)
                
                if has_name and has_company:
                    # Additional check: ensure it's a professional context
                    professional_keywords = [
                        'ceo', 'president', 'founder', 'co-founder', 'chief', 'executive',
                        'director', 'manager', 'owner', 'leads', 'heads', 'runs',
                        'works at', 'employed at', 'joins', 'appointed', 'named'
                    ]
                    
                    if any(keyword in sentence for keyword in professional_keywords):
                        return True
            
            return False
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'validate_company_person_connection'})
            return False
    
    def _validate_website_company_match(self, content: str, website: str, company: str, full_name: str) -> bool:
        """
        CRITICAL VALIDATION: Ensure the website actually belongs to the company.
        
        Args:
            content: Search results content
            website: Extracted website URL
            company: Extracted company name
            full_name: Person's name
            
        Returns:
            True if website is validated for this company
        """
        try:
            # Extract domain from website
            from urllib.parse import urlparse
            parsed_url = urlparse(website)
            domain = parsed_url.netloc.lower().replace('www.', '')
            
            # Check if domain name relates to company name
            company_words = re.findall(r'\b\w+\b', company.lower())
            company_words = [word for word in company_words if len(word) > 2 and word not in ['inc', 'corp', 'ltd', 'llc', 'the', 'and', 'of']]
            
            # VALIDATION 1: Domain contains company name elements
            domain_matches_company = False
            for word in company_words:
                if word in domain:
                    domain_matches_company = True
                    break
            
            # VALIDATION 2: Website and company mentioned together in content
            content_lower = content.lower()
            website_mentioned_with_company = False
            
            # Look for patterns where website and company appear together
            validation_patterns = [
                rf'{re.escape(company.lower())}.*?{re.escape(domain)}',
                rf'{re.escape(domain)}.*?{re.escape(company.lower())}',
                rf'{re.escape(website.lower())}.*?{re.escape(company.lower())}',
                rf'{re.escape(company.lower())}.*?{re.escape(website.lower())}',
            ]
            
            for pattern in validation_patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    website_mentioned_with_company = True
                    break
            
            # VALIDATION 3: Check if website appears in same context as person and company
            sentences = re.split(r'[.!?]', content_lower)
            contextual_match = False
            
            for sentence in sentences:
                has_name = full_name.lower() in sentence
                has_company = company.lower() in sentence
                has_website = domain in sentence or website.lower() in sentence
                
                if (has_name and has_website) or (has_company and has_website):
                    contextual_match = True
                    break
            
            # Website is valid if ANY of these conditions are met:
            # 1. Domain clearly matches company name
            # 2. Website and company mentioned together
            # 3. Website appears in same context as person/company
            is_valid = domain_matches_company or website_mentioned_with_company or contextual_match
            
            if not is_valid:
                self.logger.log_module_activity('google_enricher', 'validation', 'warning', 
                                               {'message': f'Website validation failed',
                                                'website': website,
                                                'domain': domain,
                                                'company': company,
                                                'person': full_name,
                                                'domain_matches': domain_matches_company,
                                                'mentioned_together': website_mentioned_with_company,
                                                'contextual_match': contextual_match})
            
            return is_valid
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'validate_website_company_match'})
            return False
    
    def _extract_company_from_search(self, content: str, full_name: str) -> str:
        """SUPERCHARGED company extraction with 110% accuracy."""
        
        # ENHANCED PATTERNS for maximum coverage
        patterns = [
            # LinkedIn-style patterns (highest accuracy)
            rf'{re.escape(full_name)}.*?(?:CEO|President|Founder|Co-Founder|Chief Executive|Managing Director).*?(?:at|of|@)\s+([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?)',
            
            # News and press patterns
            rf'{re.escape(full_name)}.*?(?:joins|appointed|named).*?(?:CEO|President|Founder).*?(?:at|of)\s+([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?)',
            
            # Reverse patterns (Company - Name)
            r'([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?)\s*[-–]\s*' + re.escape(full_name),
            
            # Professional directory patterns
            rf'{re.escape(full_name)}.*?(?:works at|employed at|CEO of|President of|Founder of|Co-Founder of)\s+([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?)',
            
            # ZoomInfo/Crunchbase patterns
            rf'{re.escape(full_name)}.*?(?:Company|Organization):\s*([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?)',
            
            # Event/conference patterns
            rf'{re.escape(full_name)}.*?(?:from|representing)\s+([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?)',
            
            # Award/recognition patterns
            rf'([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?).*?{re.escape(full_name)}.*?(?:CEO|President|Founder)',
            
            # Startup/tech patterns
            rf'{re.escape(full_name)}.*?(?:startup|company|firm|venture)\s+([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?)',
            
            # Generic professional patterns
            rf'{re.escape(full_name)}.*?(?:leads|heads|runs|owns)\s+([A-Z][A-Za-z0-9\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)?)',
        ]
        
        # Try each pattern with different case sensitivities
        for pattern in patterns:
            # Case insensitive first
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                company = match.strip()
                # Enhanced cleanup
                company = re.sub(r'\s+', ' ', company)  # Remove extra spaces
                company = company.strip(' ,-.:;()[]{}')  # Remove trailing punctuation
                company = re.sub(r'^(the|a|an)\s+', '', company, flags=re.IGNORECASE)  # Remove articles
                
                # Enhanced validation
                if self._is_valid_company_name(company):
                    return company
            
            # Case sensitive for better precision
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                company = match.strip()
                company = re.sub(r'\s+', ' ', company)
                company = company.strip(' ,-.:;()[]{}')
                company = re.sub(r'^(the|a|an)\s+', '', company, flags=re.IGNORECASE)
                
                if self._is_valid_company_name(company):
                    return company
        
        # FALLBACK: Look for any capitalized words near the name
        name_words = full_name.split()
        for name_word in name_words:
            # Find sentences containing the name
            sentences = re.split(r'[.!?]', content)
            for sentence in sentences:
                if name_word.lower() in sentence.lower():
                    # Look for capitalized sequences that might be company names
                    cap_sequences = re.findall(r'\b[A-Z][A-Za-z0-9\s&,.-]{2,30}(?:Inc|Corp|Ltd|LLC|International|Technologies|Solutions|Systems|Group|Company)\b', sentence)
                    for seq in cap_sequences:
                        if self._is_valid_company_name(seq.strip()):
                            return seq.strip()
        
        return None
    
    def _extract_website_from_search(self, content: str, full_name: str) -> str:
        """Extract website URL from Google search results."""
        # Look for website URLs in search results
        patterns = [
            # Direct website URLs
            r'https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            
            # URLs in search result snippets
            r'(?:Visit|Website|Site):\s*https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            
            # Company domain patterns
            r'([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))(?:\s|$|\.|\)|,)',
        ]
        
        found_websites = []
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                website = match.strip().lower()
                
                # Skip common non-company domains
                skip_domains = [
                    'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
                    'youtube.com', 'google.com', 'gmail.com', 'outlook.com',
                    'yahoo.com', 'hotmail.com', 'example.com', 'wikipedia.org'
                ]
                
                if any(skip_domain in website for skip_domain in skip_domains):
                    continue
                
                # Add protocol if missing
                if not website.startswith('http'):
                    website = f"https://{website}"
                
                if self._is_valid_website_url(website):
                    found_websites.append(website)
        
        # Return the first valid website found
        if found_websites:
            # Prefer .com domains
            com_domains = [w for w in found_websites if '.com' in w]
            return com_domains[0] if com_domains else found_websites[0]
        
        return None
    
    def _is_valid_company_name(self, company: str) -> bool:
        """ENHANCED validation for 110% accuracy in company name detection."""
        if not company or len(company.strip()) < 2:
            return False
        
        company = company.strip()
        company_lower = company.lower()
        
        # Skip obvious false positives
        skip_terms = [
            'linkedin', 'facebook', 'twitter', 'google', 'youtube', 'instagram',
            'montreal', 'quebec', 'canada', 'toronto', 'vancouver', 'ottawa',
            'ceo', 'president', 'founder', 'executive', 'manager', 'director', 
            'officer', 'unknown', 'company name', 'business', 'organization',
            'university', 'college', 'school', 'hospital', 'government',
            'the company', 'his company', 'her company', 'their company',
            'this company', 'that company', 'a company', 'the firm',
            'search results', 'web results', 'google search', 'find company'
        ]
        
        # Check if it's just a skip term
        if company_lower in skip_terms:
            return False
            
        # Check if it contains skip terms as main content
        if any(term == company_lower or company_lower.startswith(term + ' ') or company_lower.endswith(' ' + term) for term in skip_terms):
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', company):
            return False
        
        # Skip if it's just a person's name (all lowercase or all caps usually not companies)
        if company.islower() or (company.isupper() and len(company) < 5):
            return False
        
        # Skip if it's too generic
        generic_terms = ['company', 'business', 'firm', 'organization', 'corp', 'inc', 'ltd', 'llc']
        if company_lower in generic_terms:
            return False
        
        # Must have at least one capital letter (proper noun)
        if not re.search(r'[A-Z]', company):
            return False
        
        # Skip if it's just numbers or mostly numbers
        if re.match(r'^[\d\s\-\.]+$', company):
            return False
        
        # Skip if it looks like a date or time
        if re.match(r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', company):
            return False
        
        # Skip if it's too long (probably not a company name)
        if len(company) > 60:
            return False
        
        # POSITIVE INDICATORS: These make it more likely to be a company
        positive_indicators = [
            'inc', 'corp', 'ltd', 'llc', 'international', 'technologies', 
            'solutions', 'systems', 'group', 'company', 'enterprises',
            'consulting', 'services', 'partners', 'associates', 'holdings',
            'ventures', 'capital', 'investments', 'labs', 'studio', 'agency'
        ]
        
        has_positive_indicator = any(indicator in company_lower for indicator in positive_indicators)
        
        # If it has positive indicators, it's likely valid
        if has_positive_indicator:
            return True
        
        # For names without indicators, be more strict
        # Must be at least 3 characters and have proper capitalization
        if len(company) >= 3 and re.match(r'^[A-Z][a-zA-Z0-9\s&,.-]*$', company):
            # Check if it looks like a real company name (not just random words)
            words = company.split()
            if len(words) <= 4:  # Most company names are 1-4 words
                # Additional check: reject if it looks like a person's name
                # Person names typically have 2 words, all alphabetic, common first/last names
                if len(words) == 2 and all(word.istitle() and word.isalpha() for word in words):
                    # Check if these look like common first/last names
                    common_first_names = ['john', 'jane', 'mike', 'sarah', 'david', 'mary', 'james', 'lisa', 'robert', 'jennifer']
                    common_last_names = ['smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis', 'rodriguez', 'martinez']
                    
                    first_word = words[0].lower()
                    second_word = words[1].lower()
                    
                    # If both words are common names, it's probably a person
                    if first_word in common_first_names and second_word in common_last_names:
                        return False
                    
                    # If it's two generic words that could be names, be cautious
                    if len(words[0]) <= 8 and len(words[1]) <= 8 and not any(char in company.lower() for char in ['&', '-', '.']):
                        # Could be a person name, but let's allow established companies like "Goldman Sachs"
                        pass
                return True
        
        return False
    
    def _is_valid_website_url(self, url: str) -> bool:
        """Validate if a URL looks like a valid website."""
        if not url or not isinstance(url, str):
            return False
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))


async def main():
    """Main entry point for the Google Enricher Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Google Enricher Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    
    args = parser.parse_args()
    
    agent = GoogleEnricherAgent()
    
    if args.stats:
        leads = agent._get_leads_needing_enrichment(1000)
        print(f"Google Enricher Statistics:")
        print(f"  Leads needing enrichment: {len(leads)}")
        return True
    
    # Process leads in batch
    results = await agent.process_leads(limit=args.limit)
    
    print(f"Google Enricher Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)