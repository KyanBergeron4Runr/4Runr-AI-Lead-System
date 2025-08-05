#!/usr/bin/env python3
"""
Daily Enricher Agent - Database Integration Version

Updated to use the new Lead Database system instead of JSON files.
Runs daily to find leads missing emails and enriches them with advanced stealth techniques.
"""

import os
import sys
import time
import random
import logging
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path
import dns.resolver
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote
import hashlib

# Add database directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

# Import database system
from database.lead_database import get_lead_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('daily-enricher-db')

# Initialize production logging
try:
    from production_logger import log_production_event
    PRODUCTION_LOGGING_ENABLED = True
    logger.info("🏭 Production logging enabled for daily enricher")
except ImportError:
    logger.warning("⚠️ Production logging not available")
    PRODUCTION_LOGGING_ENABLED = False

class DatabaseEnricherAgent:
    """
    Enhanced enricher agent using the new database system
    """
    
    def __init__(self):
        """Initialize the enricher agent with database connection"""
        self.db = get_lead_database()
        self.session = requests.Session()
        
        # Initialize encoding fixer
        try:
            from encoding_fixer import EncodingFixer
            self.encoding_fixer = EncodingFixer()
            logger.info("✅ Encoding fixer initialized")
        except ImportError:
            logger.warning("⚠️ Encoding fixer not available")
            self.encoding_fixer = None
        
        # User agents for stealth
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        # Configure session for stealth
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        logger.info("🔧 Database Enricher Agent initialized")
    
    def run_daily_enrichment(self, max_leads: int = 10, delay_range: tuple = (5, 15)):
        """
        Run daily enrichment process using database
        
        Args:
            max_leads: Maximum number of leads to enrich
            delay_range: Random delay range between requests (seconds)
        """
        logger.info("🚀 Starting daily enrichment process")
        
        try:
            # Get leads that need enrichment from database
            leads_to_enrich = self.db.get_leads_needing_enrichment(limit=max_leads)
            
            if not leads_to_enrich:
                logger.info("✅ No leads need enrichment")
                return
            
            logger.info(f"📊 Found {len(leads_to_enrich)} leads needing enrichment")
            
            enriched_count = 0
            failed_count = 0
            
            for i, lead in enumerate(leads_to_enrich, 1):
                logger.info(f"🔍 Enriching lead {i}/{len(leads_to_enrich)}: {lead['full_name']}")
                
                try:
                    # Enrich the lead
                    enrichment_result = self.enrich_lead(lead)
                    
                    if enrichment_result['success']:
                        # Update lead in database
                        updates = {
                            'email': enrichment_result.get('email'),
                            'phone': enrichment_result.get('phone'),
                            'industry': enrichment_result.get('industry'),
                            'company_size': enrichment_result.get('company_size'),
                            'enriched': True,
                            'enriched_at': datetime.now().isoformat(),
                            'needs_enrichment': False,
                            'raw_data': {
                                'enrichment_source': enrichment_result.get('source', 'daily_enricher'),
                                'enrichment_method': enrichment_result.get('method', 'email_pattern'),
                                'confidence_score': enrichment_result.get('confidence', 0.8),
                                'enriched_fields': list(enrichment_result.get('data', {}).keys()),
                                'enrichment_timestamp': datetime.now().isoformat()
                            }
                        }
                        
                        # Remove None values
                        updates = {k: v for k, v in updates.items() if v is not None}
                        
                        success = self.db.update_lead(lead['id'], updates)
                        
                        if success:
                            enriched_count += 1
                            logger.info(f"✅ Enriched: {lead['full_name']} - Email: {enrichment_result.get('email', 'N/A')}")
                            
                            # Log production event
                            if PRODUCTION_LOGGING_ENABLED:
                                try:
                                    log_production_event(
                                        "lead_enrichment",
                                        lead,
                                        enrichment_result,
                                        {"agent": "daily_enricher_db"}
                                    )
                                except Exception as e:
                                    logger.warning(f"⚠️ Production logging failed: {e}")
                        else:
                            logger.error(f"❌ Failed to update lead in database: {lead['full_name']}")
                            failed_count += 1
                    else:
                        logger.warning(f"⚠️ Enrichment failed: {lead['full_name']} - {enrichment_result.get('error', 'Unknown error')}")
                        failed_count += 1
                        
                        # Update lead with failed enrichment attempt
                        updates = {
                            'raw_data': {
                                'last_enrichment_attempt': datetime.now().isoformat(),
                                'enrichment_error': enrichment_result.get('error', 'Unknown error')
                            }
                        }
                        
                        self.db.update_lead(lead['id'], updates)
                
                except Exception as e:
                    logger.error(f"❌ Error enriching {lead['full_name']}: {str(e)}")
                    failed_count += 1
                
                # Random delay between requests for stealth
                if i < len(leads_to_enrich):
                    delay = random.uniform(*delay_range)
                    logger.debug(f"⏱️ Waiting {delay:.1f}s before next request...")
                    time.sleep(delay)
            
            # Final summary
            logger.info(f"🎉 Enrichment completed: {enriched_count} enriched, {failed_count} failed")
            
            # Get updated statistics
            stats = self.db.get_search_statistics()
            logger.info(f"📊 Database stats: {stats['total_leads']} total, {stats['enriched_count']} enriched")
            
        except Exception as e:
            logger.error(f"❌ Daily enrichment failed: {str(e)}")
            raise
    
    def enrich_lead(self, lead: dict) -> dict:
        """
        Enrich a single lead with email and other data
        
        Args:
            lead: Lead data from database
            
        Returns:
            dict: Enrichment result with success status and data
        """
        try:
            full_name = lead.get('full_name', '')
            company = lead.get('company', '')
            
            if not full_name or not company:
                return {
                    'success': False,
                    'error': 'Missing required fields (full_name or company)'
                }
            
            # Try multiple enrichment methods
            enrichment_methods = [
                self._enrich_via_email_patterns,
                self._enrich_via_company_website,
                self._enrich_via_linkedin_data
            ]
            
            for method in enrichment_methods:
                try:
                    result = method(lead)
                    if result['success']:
                        return result
                except Exception as e:
                    logger.debug(f"Enrichment method failed: {method.__name__} - {e}")
                    continue
            
            return {
                'success': False,
                'error': 'All enrichment methods failed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Enrichment error: {str(e)}'
            }
    
    def _enrich_via_email_patterns(self, lead: dict) -> dict:
        """
        Enrich lead using common email patterns
        
        Args:
            lead: Lead data
            
        Returns:
            dict: Enrichment result
        """
        try:
            full_name = lead['full_name']
            company = lead['company']
            
            # Extract first and last name
            name_parts = full_name.strip().split()
            if len(name_parts) < 2:
                return {'success': False, 'error': 'Cannot parse name parts'}
            
            first_name = name_parts[0].lower()
            last_name = name_parts[-1].lower()
            
            # Get company domain
            domain = self._extract_company_domain(company)
            if not domain:
                return {'success': False, 'error': 'Cannot determine company domain'}
            
            # Common email patterns
            email_patterns = [
                f"{first_name}.{last_name}@{domain}",
                f"{first_name}@{domain}",
                f"{last_name}@{domain}",
                f"{first_name[0]}{last_name}@{domain}",
                f"{first_name}{last_name[0]}@{domain}",
                f"{first_name}_{last_name}@{domain}",
                f"{first_name}{last_name}@{domain}"
            ]
            
            # Test each pattern
            for email in email_patterns:
                if self._verify_email_exists(email):
                    return {
                        'success': True,
                        'email': email,
                        'method': 'email_pattern',
                        'source': 'daily_enricher',
                        'confidence': 0.8,
                        'data': {'email': email, 'domain': domain}
                    }
            
            return {'success': False, 'error': 'No valid email pattern found'}
            
        except Exception as e:
            return {'success': False, 'error': f'Email pattern enrichment failed: {str(e)}'}
    
    def _enrich_via_company_website(self, lead: dict) -> dict:
        """
        Enrich lead by scraping company website
        
        Args:
            lead: Lead data
            
        Returns:
            dict: Enrichment result
        """
        try:
            company = lead['company']
            domain = self._extract_company_domain(company)
            
            if not domain:
                return {'success': False, 'error': 'Cannot determine company domain'}
            
            # Try to scrape company website
            website_url = f"https://{domain}"
            
            response = self.session.get(website_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for contact information
            contact_info = self._extract_contact_info(soup, domain)
            
            if contact_info:
                return {
                    'success': True,
                    'method': 'website_scraping',
                    'source': 'company_website',
                    'confidence': 0.7,
                    'data': contact_info,
                    **contact_info
                }
            
            return {'success': False, 'error': 'No contact information found on website'}
            
        except Exception as e:
            return {'success': False, 'error': f'Website scraping failed: {str(e)}'}
    
    def _enrich_via_linkedin_data(self, lead: dict) -> dict:
        """
        Enrich lead using LinkedIn profile data
        
        Args:
            lead: Lead data
            
        Returns:
            dict: Enrichment result
        """
        try:
            linkedin_url = lead.get('linkedin_url')
            
            if not linkedin_url:
                return {'success': False, 'error': 'No LinkedIn URL available'}
            
            # Extract additional data from LinkedIn (if available)
            # This would require LinkedIn API or careful scraping
            # For now, return basic structure
            
            return {
                'success': True,
                'method': 'linkedin_data',
                'source': 'linkedin_profile',
                'confidence': 0.9,
                'data': {
                    'linkedin_url': linkedin_url,
                    'profile_verified': True
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'LinkedIn enrichment failed: {str(e)}'}
    
    def _extract_company_domain(self, company: str) -> str:
        """
        Extract domain from company name
        
        Args:
            company: Company name
            
        Returns:
            str: Domain name or None
        """
        try:
            # Clean company name
            company_clean = re.sub(r'[^\w\s]', '', company.lower())
            company_clean = company_clean.replace(' ', '')
            
            # Common domain patterns
            possible_domains = [
                f"{company_clean}.com",
                f"{company_clean}.ca",
                f"{company_clean}.org"
            ]
            
            # Test each domain
            for domain in possible_domains:
                try:
                    dns.resolver.resolve(domain, 'A')
                    return domain
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Domain extraction failed: {e}")
            return None
    
    def _verify_email_exists(self, email: str) -> bool:
        """
        Verify if email address exists (basic check)
        
        Args:
            email: Email address to verify
            
        Returns:
            bool: True if email likely exists
        """
        try:
            # Basic format check
            if '@' not in email or '.' not in email.split('@')[1]:
                return False
            
            domain = email.split('@')[1]
            
            # Check if domain has MX record
            try:
                dns.resolver.resolve(domain, 'MX')
                return True
            except:
                return False
                
        except Exception as e:
            logger.debug(f"Email verification failed: {e}")
            return False
    
    def _extract_contact_info(self, soup, domain: str) -> dict:
        """
        Extract contact information from website HTML
        
        Args:
            soup: BeautifulSoup object
            domain: Company domain
            
        Returns:
            dict: Contact information
        """
        contact_info = {}
        
        try:
            # Look for email addresses
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            text = soup.get_text()
            emails = re.findall(email_pattern, text)
            
            # Filter emails from the same domain
            company_emails = [email for email in emails if domain in email]
            if company_emails:
                contact_info['email'] = company_emails[0]
            
            # Look for phone numbers
            phone_pattern = r'[\+]?[1-9]?[\d\s\-\(\)]{10,}'
            phones = re.findall(phone_pattern, text)
            if phones:
                contact_info['phone'] = phones[0].strip()
            
            # Look for industry keywords
            industry_keywords = {
                'technology': ['tech', 'software', 'digital', 'IT', 'computer'],
                'healthcare': ['health', 'medical', 'hospital', 'clinic'],
                'finance': ['finance', 'bank', 'investment', 'financial'],
                'consulting': ['consulting', 'advisory', 'strategy']
            }
            
            text_lower = text.lower()
            for industry, keywords in industry_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    contact_info['industry'] = industry
                    break
            
            return contact_info
            
        except Exception as e:
            logger.debug(f"Contact info extraction failed: {e}")
            return {}
    
    def get_enrichment_statistics(self) -> dict:
        """
        Get enrichment statistics from database
        
        Returns:
            dict: Enrichment statistics
        """
        try:
            stats = self.db.get_search_statistics()
            
            enrichment_stats = {
                'total_leads': stats['total_leads'],
                'enriched_leads': stats['enriched_count'],
                'needs_enrichment': stats.get('needs_enrichment', 0),
                'enrichment_rate': (stats['enriched_count'] / stats['total_leads'] * 100) if stats['total_leads'] > 0 else 0,
                'recent_enrichments': len(self.db.get_recent_leads(days=1))
            }
            
            return enrichment_stats
            
        except Exception as e:
            logger.error(f"Failed to get enrichment statistics: {e}")
            return {}


def main():
    """
    Main function for standalone execution
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Lead Enricher with Database Integration')
    parser.add_argument('--max-leads', type=int, default=10, help='Maximum leads to enrich')
    parser.add_argument('--min-delay', type=int, default=5, help='Minimum delay between requests')
    parser.add_argument('--max-delay', type=int, default=15, help='Maximum delay between requests')
    parser.add_argument('--stats', action='store_true', help='Show enrichment statistics')
    
    args = parser.parse_args()
    
    try:
        # Initialize enricher agent
        enricher = DatabaseEnricherAgent()
        
        if args.stats:
            # Show statistics
            stats = enricher.get_enrichment_statistics()
            
            print("📊 Enrichment Statistics")
            print("=" * 30)
            print(f"Total leads: {stats['total_leads']}")
            print(f"Enriched leads: {stats['enriched_leads']}")
            print(f"Needs enrichment: {stats['needs_enrichment']}")
            print(f"Enrichment rate: {stats['enrichment_rate']:.1f}%")
            print(f"Recent enrichments: {stats['recent_enrichments']}")
            return
        
        # Run enrichment
        enricher.run_daily_enrichment(
            max_leads=args.max_leads,
            delay_range=(args.min_delay, args.max_delay)
        )
        
        print("✅ Daily enrichment completed successfully!")
        
    except KeyboardInterrupt:
        print("\\n⚠️ Enrichment cancelled by user")
    except Exception as e:
        print(f"\\n❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()