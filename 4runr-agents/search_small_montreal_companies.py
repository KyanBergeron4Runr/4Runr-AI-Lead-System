#!/usr/bin/env python3
"""
Search for Small-Medium Montreal Companies
Target: 20-200 employees, local decision makers, more accessible CEOs
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('small-company-search')

class SmallCompanySearcher:
    def __init__(self):
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.shared_dir = Path(__file__).parent / "shared"
        self.shared_dir.mkdir(exist_ok=True)
        
        logger.info("🔍 Small Montreal Company Searcher initialized")
        if self.serpapi_key:
            logger.info("✅ SerpAPI key found")
        else:
            logger.error("❌ No SerpAPI key found")
    
    def search_small_montreal_companies(self):
        """Search for small-medium Montreal companies with accessible CEOs"""
        
        # Target searches for smaller, more accessible companies
        search_queries = [
            # Focus on just 5 high-potential searches to conserve API calls
            "Montreal software company CEO -Shopify -CGI -Lightspeed",
            "Montreal consulting firm CEO president",
            "Montreal marketing agency CEO founder", 
            "Montreal manufacturing company CEO president",
            "Montreal family business CEO owner",
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            logger.info(f"🔍 Search {i}/{len(search_queries)}: {query}")
            
            try:
                url = "https://serpapi.com/search"
                params = {
                    'q': query,
                    'api_key': self.serpapi_key,
                    'engine': 'google',
                    'num': 3,  # Only 3 results per search to conserve API
                    'safe': 'active',
                    'location': 'Montreal, Quebec, Canada'
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('organic_results', [])
                    
                    logger.info(f"✅ Found {len(results)} results")
                    
                    # Extract company info from results
                    for result in results:
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        link = result.get('link', '')
                        
                        # Try to extract company and person info
                        company_info = self.extract_company_info(title, snippet, link)
                        if company_info:
                            company_info['search_query'] = query
                            company_info['found_at'] = datetime.now().isoformat()
                            all_results.append(company_info)
                
                else:
                    logger.warning(f"⚠️ Search failed: {response.status_code}")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Search error: {str(e)}")
                continue
        
        return all_results
    
    def extract_company_info(self, title, snippet, link):
        """Extract company and CEO info from search results"""
        # Look for CEO/President/Founder indicators
        ceo_indicators = ['ceo', 'president', 'founder', 'owner', 'managing partner', 'director']
        
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        # Check if this looks like a CEO/business leader
        has_ceo_indicator = any(indicator in title_lower or indicator in snippet_lower 
                               for indicator in ceo_indicators)
        
        if not has_ceo_indicator:
            return None
        
        # Try to extract name and company
        # This is basic extraction - could be improved
        potential_name = None
        potential_company = None
        
        # Look for patterns like "John Smith, CEO of ABC Company"
        if 'ceo' in title_lower:
            parts = title.split(',')
            if len(parts) >= 2:
                potential_name = parts[0].strip()
                company_part = parts[1].strip()
                if 'of' in company_part:
                    potential_company = company_part.split('of')[-1].strip()
        
        # Look for LinkedIn profiles (good sign)
        is_linkedin = 'linkedin.com' in link
        
        return {
            'potential_name': potential_name,
            'potential_company': potential_company,
            'title': title,
            'snippet': snippet,
            'link': link,
            'is_linkedin': is_linkedin,
            'confidence': 'medium' if potential_name and potential_company else 'low'
        }
    
    def save_results(self, results):
        """Save search results for manual review"""
        output_file = self.shared_dir / "small_montreal_companies.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(results)} potential leads to {output_file}")
        
        # Also create a readable report
        report_file = self.shared_dir / "small_companies_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("SMALL MONTREAL COMPANIES - MANUAL REVIEW NEEDED\n")
            f.write("=" * 60 + "\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"{i}. {result.get('title', 'No title')}\n")
                f.write(f"   Name: {result.get('potential_name', 'Unknown')}\n")
                f.write(f"   Company: {result.get('potential_company', 'Unknown')}\n")
                f.write(f"   Link: {result.get('link', '')}\n")
                f.write(f"   LinkedIn: {'Yes' if result.get('is_linkedin') else 'No'}\n")
                f.write(f"   Snippet: {result.get('snippet', '')[:100]}...\n")
                f.write(f"   Search: {result.get('search_query', '')}\n")
                f.write("-" * 60 + "\n\n")
        
        logger.info(f"📋 Created readable report: {report_file}")

def main():
    """Search for small Montreal companies"""
    logger.info("🚀 Starting search for small Montreal companies...")
    
    searcher = SmallCompanySearcher()
    
    if not searcher.serpapi_key:
        logger.error("❌ No SerpAPI key found. Please check your .env file.")
        return
    
    # Perform searches
    results = searcher.search_small_montreal_companies()
    
    # Save results
    searcher.save_results(results)
    
    # Summary
    logger.info("🎯 Search Summary:")
    logger.info(f"   Total potential leads found: {len(results)}")
    logger.info(f"   LinkedIn profiles: {len([r for r in results if r.get('is_linkedin')])}")
    logger.info(f"   High confidence: {len([r for r in results if r.get('confidence') == 'high'])}")
    logger.info(f"   Medium confidence: {len([r for r in results if r.get('confidence') == 'medium'])}")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Review the generated report: shared/small_companies_report.txt")
    print("2. Manually verify the most promising leads")
    print("3. Add verified leads to your system")
    print("4. Focus on companies with 20-200 employees")
    print("="*60)

if __name__ == "__main__":
    main()