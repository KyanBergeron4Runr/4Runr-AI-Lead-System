#!/usr/bin/env python3
"""
SerpAPI LinkedIn Scraper
Uses SerpAPI to search for Montreal CEOs and LinkedIn profiles
This is the working approach that integrates with your existing system
"""

import os
import json
import time
import logging
import requests
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('serpapi-linkedin-scraper')

class SerpAPILinkedInScraper:
    def __init__(self):
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        
        if not self.serpapi_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")
        
        logger.info("🔍 SerpAPI LinkedIn Scraper initialized")
        logger.info("✅ SerpAPI key found - using premium search")
        
        # Montreal-specific search queries
        self.montreal_ceo_queries = [
            "Montreal CEO LinkedIn site:linkedin.com/in",
            "Montreal Chief Executive Officer LinkedIn site:linkedin.com/in", 
            "Montreal President CEO LinkedIn site:linkedin.com/in",
            "Montreal startup founder CEO LinkedIn site:linkedin.com/in",
            "Montreal company CEO LinkedIn site:linkedin.com/in -Shopify -CGI -Lightspeed",
            "Montreal tech CEO LinkedIn site:linkedin.com/in",
            "Montreal business owner CEO LinkedIn site:linkedin.com/in"
        ]
    
    def search_montreal_ceos_with_serpapi(self, max_results=10):
        """Search for Montreal CEOs using SerpAPI"""
        all_leads = []
        processed_urls = set()
        
        # Limit queries to conserve API calls
        queries_to_use = self.montreal_ceo_queries[:3]  # Use first 3 queries
        
        for i, query in enumerate(queries_to_use, 1):
            if len(all_leads) >= max_results:
                break
                
            logger.info(f"🔍 SerpAPI Search {i}/{len(queries_to_use)}: {query}")
            
            try:
                url = "https://serpapi.com/search"
                params = {
                    'q': query,
                    'api_key': self.serpapi_key,
                    'engine': 'google',
                    'num': 5,  # 5 results per query
                    'safe': 'active',
                    'location': 'Montreal, Quebec, Canada',
                    'gl': 'ca',  # Canada
                    'hl': 'en'   # English
                }
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('organic_results', [])
                    
                    logger.info(f"✅ Found {len(results)} search results")
                    
                    # Extract LinkedIn profiles from results
                    for result in results:
                        lead = self.extract_linkedin_lead(result)
                        
                        if lead and lead['linkedin_url'] not in processed_urls:
                            processed_urls.add(lead['linkedin_url'])
                            all_leads.append(lead)
                            logger.info(f"📋 Found: {lead['name']} - {lead['title']} at {lead['company']}")
                        
                        if len(all_leads) >= max_results:
                            break
                
                elif response.status_code == 429:
                    logger.warning("⚠️ SerpAPI rate limit reached - waiting...")
                    time.sleep(60)
                    continue
                else:
                    logger.warning(f"⚠️ SerpAPI request failed: {response.status_code}")
                
                # Rate limiting between searches
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"❌ SerpAPI search error: {str(e)}")
                continue
        
        logger.info(f"✅ SerpAPI scraping completed: {len(all_leads)} Montreal CEOs found")
        return all_leads
    
    def extract_linkedin_lead(self, result):
        """Extract lead information from SerpAPI search result"""
        try:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            link = result.get('link', '')
            
            # Must be a LinkedIn profile
            if 'linkedin.com/in/' not in link:
                return None
            
            # Extract name from title (usually "Name - Title - Company | LinkedIn")
            name = ""
            job_title = ""
            company = ""
            
            if ' - ' in title:
                parts = title.split(' - ')
                if len(parts) >= 1:
                    name = parts[0].strip()
                if len(parts) >= 2:
                    job_title = parts[1].strip()
                if len(parts) >= 3:
                    company_part = parts[2].strip()
                    # Remove "| LinkedIn" if present
                    if '|' in company_part:
                        company = company_part.split('|')[0].strip()
                    else:
                        company = company_part
            
            # If name extraction failed, try alternative parsing
            if not name and title:
                # Sometimes format is "Name | LinkedIn"
                if '|' in title:
                    name = title.split('|')[0].strip()
                else:
                    name = title.strip()
            
            # Extract additional info from snippet
            if not job_title and snippet:
                # Look for job titles in snippet
                ceo_indicators = ['CEO', 'Chief Executive Officer', 'President', 'Founder', 'Owner', 'Director']
                for indicator in ceo_indicators:
                    if indicator.lower() in snippet.lower():
                        job_title = indicator
                        break
            
            # Extract company from snippet if not found in title
            if not company and snippet:
                # Look for company indicators in snippet
                lines = snippet.split('.')
                for line in lines:
                    line = line.strip()
                    # Look for patterns like "at Company Name" or "chez Company"
                    if ' at ' in line.lower():
                        parts = line.lower().split(' at ')
                        if len(parts) > 1:
                            company = parts[1].strip().title()
                            break
                    elif ' chez ' in line.lower():
                        parts = line.lower().split(' chez ')
                        if len(parts) > 1:
                            company = parts[1].strip().title()
                            break
                    elif any(word in line.lower() for word in ['company', 'inc', 'corp', 'ltd', 'llc', 'international']):
                        company = line.strip()
                        break
            
            # Validate we have minimum required info
            if not name or not link:
                return None
            
            # Check if this looks like a Montreal-based person
            montreal_indicators = ['montreal', 'québec', 'quebec', 'canada', 'qc']
            is_montreal = any(indicator in (title + ' ' + snippet).lower() for indicator in montreal_indicators)
            
            if not is_montreal:
                logger.debug(f"⚠️ Skipping non-Montreal profile: {name}")
                return None
            
            # Create lead object
            lead = {
                "name": name,
                "title": job_title or "Executive",
                "company": company or "Unknown Company",
                "linkedin_url": link,
                "location": "Montreal, Quebec, Canada",
                "email": None,
                "verified": False,
                "enriched": False,
                "engagement_method": None,
                "scraped_at": datetime.now().isoformat(),
                "source": "SerpAPI LinkedIn Search",
                "search_snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet
            }
            
            return lead
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract lead from result: {str(e)}")
            return None

async def scrape_linkedin_leads_serpapi():
    """Main async function for SerpAPI LinkedIn scraping"""
    try:
        scraper = SerpAPILinkedInScraper()
        
        # Get max leads from environment
        max_leads = int(os.getenv('MAX_LEADS_PER_RUN', '5'))
        
        logger.info(f"🚀 Starting SerpAPI LinkedIn scraping for {max_leads} Montreal CEOs")
        
        # Search for Montreal CEOs
        leads = scraper.search_montreal_ceos_with_serpapi(max_results=max_leads)
        
        if not leads:
            logger.warning("⚠️ No Montreal CEOs found via SerpAPI")
            return []
        
        logger.info(f"✅ SerpAPI LinkedIn scraping completed: {len(leads)} leads found")
        
        # Log sample results
        for i, lead in enumerate(leads[:3], 1):
            logger.info(f"   📋 {i}. {lead['name']} - {lead['title']} at {lead['company']}")
            logger.info(f"      🔗 {lead['linkedin_url']}")
        
        return leads
        
    except Exception as e:
        logger.error(f"❌ SerpAPI LinkedIn scraping failed: {str(e)}")
        return []

def scrape_linkedin_leads_serpapi_sync():
    """Synchronous wrapper for SerpAPI scraping"""
    import asyncio
    return asyncio.run(scrape_linkedin_leads_serpapi())

if __name__ == "__main__":
    # Test the SerpAPI scraper
    leads = scrape_linkedin_leads_serpapi_sync()
    print(f"\n✅ Found {len(leads)} Montreal CEOs via SerpAPI:")
    for lead in leads:
        print(f"- {lead['name']} ({lead['title']}) at {lead['company']}")
        print(f"  LinkedIn: {lead['linkedin_url']}")
        print()