#!/usr/bin/env python3
"""
LinkedIn Lookup Agent - Safe Google-based LinkedIn Profile Discovery

This agent uses Google Search to find LinkedIn profile URLs without accessing LinkedIn directly.
It's safe, legal, and avoids LinkedIn's anti-bot protection.
"""

import os
import json
import time
import logging
import requests
import re
from datetime import datetime
from urllib.parse import quote_plus, urlparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('linkedin-lookup-agent')

class LinkedInLookupAgent:
    def __init__(self):
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Output files
        self.shared_dir = Path(__file__).parent / "shared"
        self.shared_dir.mkdir(exist_ok=True)
        
        self.resolved_urls_file = self.shared_dir / "resolved_linkedin_urls.json"
        self.lookup_log_file = self.shared_dir / "linkedin_lookup_log.json"
        
        # Initialize log
        self.lookup_log = []
        
        logger.info("🔍 LinkedIn Lookup Agent initialized")
        if self.serpapi_key:
            logger.info("✅ SerpAPI key found - using premium search")
        elif self.google_api_key and self.google_cse_id:
            logger.info("✅ Google Custom Search API configured")
        else:
            logger.info("⚠️ No API keys found - will use fallback search")
    
    def construct_google_query(self, full_name, company, location=None):
        """Construct a highly targeted Google search query for LinkedIn profiles"""
        # Normalize the name first to fix encoding issues
        name_clean = self.normalize_name(full_name).strip().replace('"', '')
        company_clean = company.strip().replace('"', '') if company else ""
        
        # Extract first and last name for more targeted search
        name_parts = name_clean.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            # Use exact full name for maximum precision
            name_query = f'"{name_clean}"'
        else:
            name_query = f'"{name_clean}"'
        
        # Base query with site restriction
        query_parts = [name_query]
        
        # Add company name with high precision
        if company_clean:
            # Clean company name but keep key identifiers
            company_words = company_clean.lower()
            
            # Map common company variations to exact names
            company_mappings = {
                'shopify': 'Shopify',
                'desjardins': 'Desjardins',
                'couche-tard': 'Couche-Tard',
                'snc-lavalin': 'SNC-Lavalin',
                'cae inc': 'CAE',
                'national bank': 'National Bank',
                'dollarama': 'Dollarama',
                'nuvei': 'Nuvei',
                'tfi international': 'TFI',
                'bombardier': 'Bombardier',
                'hydro-québec': 'Hydro-Québec',
                'metro inc': 'Metro',
                'saputo': 'Saputo',
                'lightspeed': 'Lightspeed',
                'cgi': 'CGI'
            }
            
            # Find the best company match
            company_key = None
            for key, value in company_mappings.items():
                if key in company_words:
                    company_key = value
                    break
            
            if company_key:
                query_parts.append(f'"{company_key}"')
            else:
                # Fallback to cleaned company name
                company_words = company_clean.replace(' Inc', '').replace(' Corp', '').replace(' Ltd', '')
                company_words = company_words.replace(' Corporation', '').replace(' Company', '')
                if company_words.strip():
                    query_parts.append(f'"{company_words.strip()}"')
        
        # Add executive terms for precision
        query_parts.append('(CEO OR "Chief Executive Officer" OR President)')
        
        # Add Montreal for local context
        if location and "montreal" in location.lower():
            query_parts.append("Montreal")
        
        query_parts.append("site:linkedin.com/in")
        
        query = " ".join(query_parts)
        
        logger.info(f"🔍 High-precision query: {query}")
        return query
    
    def search_with_serpapi(self, query, max_results=3):
        """Search using SerpAPI (premium option)"""
        if not self.serpapi_key:
            return None
        
        try:
            url = "https://serpapi.com/search"
            params = {
                'q': query,
                'api_key': self.serpapi_key,
                'engine': 'google',
                'num': max_results,
                'safe': 'active'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for result in data.get('organic_results', [])[:max_results]:
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('link', ''),
                        'snippet': result.get('snippet', '')
                    })
                
                logger.info(f"✅ SerpAPI returned {len(results)} results")
                return results
            else:
                logger.warning(f"⚠️ SerpAPI error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ SerpAPI search failed: {str(e)}")
            return None
    
    def search_with_google_cse(self, query, max_results=3):
        """Search using Google Custom Search API"""
        if not self.google_api_key or not self.google_cse_id:
            return None
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cse_id,
                'q': query,
                'num': max_results,
                'safe': 'active'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('items', [])[:max_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', '')
                    })
                
                logger.info(f"✅ Google CSE returned {len(results)} results")
                return results
            else:
                logger.warning(f"⚠️ Google CSE error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Google CSE search failed: {str(e)}")
            return None
    
    def search_with_fallback(self, query, max_results=3):
        """Fallback search using requests (basic web scraping)"""
        try:
            # Use DuckDuckGo as a fallback (more permissive than Google)
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Simple regex to extract LinkedIn URLs
                linkedin_pattern = r'https://www\.linkedin\.com/in/[a-zA-Z0-9\-_]+'
                urls = re.findall(linkedin_pattern, response.text)
                
                results = []
                for url in urls[:max_results]:
                    results.append({
                        'title': 'LinkedIn Profile',
                        'url': url,
                        'snippet': 'Found via fallback search'
                    })
                
                logger.info(f"✅ Fallback search returned {len(results)} results")
                return results
            else:
                logger.warning(f"⚠️ Fallback search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Fallback search failed: {str(e)}")
            return []
    
    def extract_linkedin_urls(self, search_results):
        """Extract and validate LinkedIn URLs from search results"""
        linkedin_urls = []
        
        for result in search_results:
            url = result.get('url', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Validate LinkedIn URL format
            if 'linkedin.com/in/' in url:
                # Clean the URL
                clean_url = url.split('?')[0]  # Remove query parameters
                clean_url = clean_url.rstrip('/')  # Remove trailing slash
                
                linkedin_urls.append({
                    'url': clean_url,
                    'title': title,
                    'snippet': snippet
                })
        
        return linkedin_urls
    
    def score_linkedin_match(self, linkedin_result, full_name, company):
        """Score how well a LinkedIn result matches the input criteria - VERY STRICT"""
        score = 0.0
        title = linkedin_result.get('title', '').lower()
        snippet = linkedin_result.get('snippet', '').lower()
        url = linkedin_result.get('url', '').lower()
        
        # Clean and normalize the name for better matching
        name_clean = self.normalize_name(full_name)
        name_parts = name_clean.lower().split()
        company_clean = company.lower() if company else ""
        
        # Extract first and last name for more precise matching
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        full_name_lower = name_clean.lower()
        
        # STRICT Name matching - require exact name match in title
        name_score = 0.0
        if first_name and last_name:
            # Check for exact full name in title (highest confidence)
            if full_name_lower in title:
                name_score = 0.9
            # Check for both first and last name in title
            elif first_name in title and last_name in title:
                name_score = 0.7
            # Check for both names in snippet (lower confidence)
            elif first_name in snippet and last_name in snippet:
                name_score = 0.4
            else:
                # If names don't match well, this is likely wrong
                return 0.0
        
        score += name_score
        
        # STRICT Company matching - require strong company presence
        company_score = 0.0
        if company_clean:
            # Define exact company matches for Montreal CEOs
            company_indicators = {
                'shopify': ['shopify'],
                'desjardins': ['desjardins'],
                'couche-tard': ['couche-tard', 'couche tard'],
                'snc-lavalin': ['snc-lavalin', 'snc lavalin'],
                'cae': ['cae'],
                'national bank': ['national bank', 'nbc'],
                'dollarama': ['dollarama'],
                'nuvei': ['nuvei'],
                'tfi': ['tfi'],
                'bombardier': ['bombardier'],
                'hydro-québec': ['hydro-québec', 'hydro quebec'],
                'metro': ['metro'],
                'saputo': ['saputo'],
                'lightspeed': ['lightspeed'],
                'cgi': ['cgi']
            }
            
            # Find matching company indicators
            for company_key, indicators in company_indicators.items():
                if company_key in company_clean:
                    for indicator in indicators:
                        if indicator in title or indicator in snippet:
                            company_score = 0.3
                            break
                    if company_score > 0:
                        break
        
        score += company_score
        
        # Executive role verification - MUST be a senior executive
        executive_score = 0.0
        executive_terms = ['ceo', 'chief executive', 'president', 'founder', 'chairman']
        for term in executive_terms:
            if term in title:
                executive_score = 0.2
                break
        
        # If no executive role found, heavily penalize
        if executive_score == 0.0:
            score *= 0.3  # Heavily reduce score for non-executives
        else:
            score += executive_score
        
        # URL quality check - prefer clean, professional URLs
        if '/in/' in url:
            profile_slug = url.split('/in/')[-1].replace('/', '')
            # Prefer URLs that contain the person's name
            if any(name_part in profile_slug for name_part in name_parts if len(name_part) > 2):
                score += 0.1
        
        # STRICT penalties for obviously wrong matches
        wrong_indicators = [
            'student', 'intern', 'assistant', 'junior', 'coordinator', 
            'manager', 'director', 'analyst', 'specialist', 'associate'
        ]
        for indicator in wrong_indicators:
            if indicator in title and 'senior' not in title and 'chief' not in title:
                return 0.0  # Immediately disqualify non-executive roles
        
        # Montreal location bonus (small)
        if 'montreal' in snippet or 'quebec' in snippet:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def normalize_name(self, name):
        """Normalize name to handle encoding issues"""
        if not name:
            return ""
        
        # Use the comprehensive encoding fixer if available
        try:
            from shared.encoding_fixer import EncodingFixer
            fixer = EncodingFixer()
            name = fixer.fix_text(name)
        except ImportError:
            # Fallback to basic fixes if encoding fixer not available
            name = name.replace('Ã©', 'é')
            name = name.replace('Ã¨', 'è')
            name = name.replace('Ã¡', 'á')
            name = name.replace('Ã ', 'à')
            name = name.replace('Ã´', 'ô')
            name = name.replace('Ã¢', 'â')
            name = name.replace('Ã§', 'ç')
            name = name.replace('Ã¼', 'ü')
            name = name.replace('Ã‰', 'É')
            name = name.replace('LÃ¼tke', 'Lütke')
            name = name.replace('BÃ©dard', 'Bédard')
            name = name.replace('FlÃ¨che', 'Flèche')
        
        return name.strip()
    
    def lookup_linkedin_profile(self, full_name, company, location=None, max_retries=2):
        """Main function to lookup a LinkedIn profile"""
        # Normalize the name first to fix any encoding issues
        normalized_name = self.normalize_name(full_name)
        logger.info(f"🔍 Looking up LinkedIn profile for: {normalized_name} at {company}")
        
        # Construct search query
        query = self.construct_google_query(normalized_name, company, location)
        
        # Try different search methods with retries
        search_results = None
        search_method = "none"
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"🔄 Retry attempt {attempt}/{max_retries}")
                time.sleep(2)  # Wait between retries
            
            # Try SerpAPI first (premium)
            if not search_results:
                search_results = self.search_with_serpapi(query)
                if search_results:
                    search_method = "serpapi"
            
            # Try Google Custom Search API
            if not search_results:
                search_results = self.search_with_google_cse(query)
                if search_results:
                    search_method = "google_cse"
            
            # Try fallback search
            if not search_results:
                search_results = self.search_with_fallback(query)
                if search_results:
                    search_method = "fallback"
            
            if search_results:
                break
        
        # Process results
        if not search_results:
            result = {
                "input_name": normalized_name,  # Use normalized name
                "input_company": company,
                "linkedin_url": None,
                "match_score": 0.0,
                "status": "not_found",
                "search_method": search_method,
                "query_used": query,
                "timestamp": datetime.now().isoformat()
            }
            logger.warning(f"❌ No LinkedIn profile found for {normalized_name}")
        else:
            # Extract LinkedIn URLs
            linkedin_urls = self.extract_linkedin_urls(search_results)
            
            if not linkedin_urls:
                result = {
                    "input_name": normalized_name,  # Use normalized name
                    "input_company": company,
                    "linkedin_url": None,
                    "match_score": 0.0,
                    "status": "no_linkedin_urls",
                    "search_method": search_method,
                    "query_used": query,
                    "timestamp": datetime.now().isoformat()
                }
                logger.warning(f"❌ No LinkedIn URLs found in search results for {normalized_name}")
            else:
                # Score and select best match
                best_match = None
                best_score = 0.0
                
                for linkedin_result in linkedin_urls:
                    score = self.score_linkedin_match(linkedin_result, normalized_name, company)
                    if score > best_score:
                        best_score = score
                        best_match = linkedin_result
                
                if best_match and best_score > 0.85:  # Very high confidence threshold to conserve API calls
                    result = {
                        "input_name": normalized_name,  # Use normalized name
                        "input_company": company,
                        "linkedin_url": best_match['url'],
                        "match_score": round(best_score, 3),
                        "status": "verified",
                        "search_method": search_method,
                        "query_used": query,
                        "result_title": best_match.get('title', ''),
                        "timestamp": datetime.now().isoformat()
                    }
                    logger.info(f"✅ Found LinkedIn profile for {normalized_name}: {best_match['url']} (score: {best_score:.3f})")
                else:
                    result = {
                        "input_name": normalized_name,  # Use normalized name
                        "input_company": company,
                        "linkedin_url": None,
                        "match_score": round(best_score, 3) if best_match else 0.0,
                        "status": "low_confidence",
                        "search_method": search_method,
                        "query_used": query,
                        "timestamp": datetime.now().isoformat()
                    }
                    logger.warning(f"⚠️ Low confidence match for {normalized_name} (score: {best_score:.3f})")
        
        # Log the lookup
        self.lookup_log.append(result)
        
        return result
    
    def prioritize_leads(self, leads):
        """Prioritize leads based on likelihood of finding accurate LinkedIn profiles"""
        # Define AVOID these huge companies - CEOs are too big/busy
        avoid_companies = [
            'shopify', 'bombardier', 'cgi', 'metro', 'saputo', 'dollarama'
        ]
        
        # Focus on mid-size Montreal companies and emerging leaders
        target_companies = [
            'lightspeed', 'nuvei', 'cae', 'tfi', 'desjardins'
        ]
        
        target_leads = []
        avoid_leads = []
        other_leads = []
        
        for lead in leads:
            company = lead.get('company', '').lower()
            full_name = lead.get('full_name', lead.get('name', ''))
            
            # Skip if no name
            if not full_name:
                continue
            
            # AVOID huge company CEOs - they're too big/busy
            is_avoid_company = any(avoid_company in company for avoid_company in avoid_companies)
            
            # Target mid-size companies
            is_target_company = any(target_company in company for target_company in target_companies)
            
            # Check name complexity (simpler names are easier to match)
            name_parts = full_name.split()
            is_simple_name = len(name_parts) == 2 and all(len(part) > 2 for part in name_parts)
            
            if is_avoid_company:
                avoid_leads.append(lead)
            elif is_target_company and is_simple_name:
                target_leads.append(lead)
            elif is_target_company or is_simple_name:
                other_leads.append(lead)
        
        # Return prioritized list - target companies first, avoid huge companies
        prioritized = target_leads + other_leads
        
        logger.info(f"📊 Lead prioritization:")
        logger.info(f"   🎯 Target companies (mid-size): {len(target_leads)} leads")
        logger.info(f"   📋 Other leads: {len(other_leads)} leads")
        logger.info(f"   ❌ Avoiding huge companies: {len(avoid_leads)} leads (too big/busy)")
        
        if avoid_leads:
            logger.info("   Skipping these huge company CEOs:")
            for lead in avoid_leads:
                name = lead.get('full_name', lead.get('name', ''))
                company = lead.get('company', '')
                logger.info(f"     - {name} ({company}) - Too big, likely unresponsive")
        
        return prioritized
    
    def process_leads_batch(self, leads, max_searches=None):
        """Process a batch of leads for LinkedIn lookup with API conservation"""
        # Prioritize leads to use API calls wisely
        prioritized_leads = self.prioritize_leads(leads)
        
        # Limit searches if specified
        if max_searches:
            prioritized_leads = prioritized_leads[:max_searches]
            logger.info(f"🎯 Limited to {max_searches} searches to conserve API calls")
        
        logger.info(f"🚀 Processing {len(prioritized_leads)} leads for LinkedIn lookup")
        
        resolved_results = []
        api_calls_used = 0
        
        for i, lead in enumerate(prioritized_leads, 1):
            full_name = lead.get('full_name', lead.get('name', ''))
            company = lead.get('company', '')
            location = lead.get('location', '')
            
            if not full_name:
                logger.warning(f"⚠️ Skipping lead {i}: No name provided")
                continue
            
            logger.info(f"📋 Processing lead {i}/{len(prioritized_leads)}: {full_name} ({company})")
            
            # Perform lookup
            result = self.lookup_linkedin_profile(full_name, company, location)
            resolved_results.append(result)
            api_calls_used += 1
            
            # Rate limiting and API conservation
            time.sleep(2)  # Be more respectful to conserve quota
        
        logger.info(f"📊 API Usage Summary:")
        logger.info(f"   API calls used: {api_calls_used}")
        logger.info(f"   Successful matches: {len([r for r in resolved_results if r.get('status') == 'verified'])}")
        
        return resolved_results
    
    def save_results(self, resolved_results):
        """Save resolved LinkedIn URLs and lookup log"""
        # Save resolved URLs
        with open(self.resolved_urls_file, 'w', encoding='utf-8') as f:
            json.dump(resolved_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(resolved_results)} resolved LinkedIn URLs to {self.resolved_urls_file}")
        
        # Save lookup log
        with open(self.lookup_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.lookup_log, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 Saved lookup log to {self.lookup_log_file}")
    
    def update_verified_leads(self, resolved_results):
        """Update verified_leads.json with resolved LinkedIn URLs"""
        verified_leads_file = self.shared_dir / "verified_leads.json"
        
        if not verified_leads_file.exists():
            logger.warning("⚠️ verified_leads.json not found - creating new file")
            verified_leads = []
        else:
            with open(verified_leads_file, 'r', encoding='utf-8') as f:
                verified_leads = json.load(f)
        
        # Create a mapping of resolved URLs
        url_mapping = {}
        for result in resolved_results:
            if result['status'] == 'verified' and result['linkedin_url']:
                key = (result['input_name'], result['input_company'])
                url_mapping[key] = result['linkedin_url']
        
        # Update verified leads
        updated_count = 0
        for lead in verified_leads:
            full_name = lead.get('full_name', lead.get('name', ''))
            company = lead.get('company', '')
            key = (full_name, company)
            
            if key in url_mapping:
                old_url = lead.get('linkedin_url', '')
                new_url = url_mapping[key]
                
                if old_url != new_url:
                    lead['linkedin_url'] = new_url
                    lead['linkedin_lookup_updated'] = datetime.now().isoformat()
                    updated_count += 1
                    logger.info(f"🔄 Updated LinkedIn URL for {full_name}: {new_url}")
        
        # Save updated verified leads
        with open(verified_leads_file, 'w', encoding='utf-8') as f:
            json.dump(verified_leads, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Updated {updated_count} LinkedIn URLs in verified_leads.json")

def load_leads_from_file(file_path):
    """Load leads from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        logger.info(f"📥 Loaded {len(leads)} leads from {file_path}")
        return leads
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"❌ Invalid JSON in file: {file_path}")
        return []

def main():
    """Main function to run LinkedIn lookup on leads"""
    logger.info("🚀 Starting LinkedIn Lookup Agent")
    
    # Initialize agent
    agent = LinkedInLookupAgent()
    
    # Load leads (try multiple sources)
    leads = []
    
    # Try to load from raw_leads.json first
    shared_dir = Path(__file__).parent / "shared"
    raw_leads_file = shared_dir / "raw_leads.json"
    
    if raw_leads_file.exists():
        leads = load_leads_from_file(raw_leads_file)
    
    # If no raw leads, try verified leads
    if not leads:
        verified_leads_file = shared_dir / "verified_leads.json"
        if verified_leads_file.exists():
            leads = load_leads_from_file(verified_leads_file)
    
    # If still no leads, create sample data
    if not leads:
        logger.warning("⚠️ No leads found, creating sample data for testing")
        leads = [
            {
                "full_name": "Tobias Lütke",
                "company": "Shopify",
                "location": "Montreal, Quebec, Canada"
            },
            {
                "full_name": "Dax Dasilva",
                "company": "Lightspeed Commerce",
                "location": "Montreal, Quebec, Canada"
            },
            {
                "full_name": "Philip Fayer",
                "company": "Nuvei Corporation",
                "location": "Montreal, Quebec, Canada"
            }
        ]
    
    if not leads:
        logger.error("❌ No leads to process")
        return
    
    # Process leads
    resolved_results = agent.process_leads_batch(leads)
    
    # Save results
    agent.save_results(resolved_results)
    
    # Update verified leads if they exist
    agent.update_verified_leads(resolved_results)
    
    # Summary
    successful_lookups = len([r for r in resolved_results if r['status'] == 'verified'])
    total_lookups = len(resolved_results)
    
    logger.info("🎯 LinkedIn Lookup Summary:")
    logger.info(f"   Total lookups: {total_lookups}")
    logger.info(f"   Successful: {successful_lookups}")
    logger.info(f"   Success rate: {successful_lookups/total_lookups*100:.1f}%")
    
    logger.info("✅ LinkedIn Lookup Agent completed successfully")

if __name__ == "__main__":
    main()