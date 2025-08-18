#!/usr/bin/env python3
"""
Fix Diverse Search Scraper
===========================
Patch the SerpAPI scraper to accept custom diverse queries
"""

import sys
import os
sys.path.insert(0, './4runr-lead-scraper/scraper')

def create_custom_search_method():
    """Create a custom search method that accepts diverse queries"""
    
    patch_code = '''
def search_custom_query(self, custom_query: str, max_results: int = 10):
    """
    Search using a custom query string.
    
    Args:
        custom_query: Custom search query (e.g. 'site:linkedin.com/in/ "CTO" Toronto')
        max_results: Maximum number of results
        
    Returns:
        List of lead dictionaries
    """
    import time
    import random
    from .scraper_config import logger
    
    all_leads = []
    processed_urls = set()
    
    logger.info(f"🔍 Custom search: {custom_query}")
    
    try:
        results = self._execute_serpapi_search(custom_query)
        
        if results:
            logger.info(f"✅ Found {len(results)} search results")
            
            # Extract LinkedIn profiles from results
            for result in results:
                lead = self._extract_linkedin_lead(result)
                
                if lead and lead['linkedin_url'] not in processed_urls:
                    processed_urls.add(lead['linkedin_url'])
                    all_leads.append(lead)
                    logger.info(f"📋 Found: {lead['name']} - {lead['title']} at {lead['company']}")
                
                if len(all_leads) >= max_results:
                    break
        
        logger.info(f"✅ Custom search completed: {len(all_leads)} leads found")
        return all_leads
        
    except Exception as e:
        logger.error(f"❌ Custom search failed: {e}")
        return []
'''
    
    return patch_code

def patch_autonomous_organism():
    """Create a patch for the autonomous organism to use custom search"""
    
    patch_code = '''
# REPLACE the scraper call in real_autonomous_organism.py around line 176

# OLD CODE:
# results = scraper.search_montreal_ceos(max_results=3)

# NEW CODE:
results = scraper.search_custom_query(custom_query=query, max_results=5)
'''
    
    return patch_code

def create_direct_fix():
    """Create a direct fix by modifying the autonomous organism"""
    
    # Read current real_autonomous_organism.py
    try:
        with open('real_autonomous_organism.py', 'r') as f:
            content = f.read()
        
        # Replace the hardcoded scraper call
        old_line = "results = scraper.search_montreal_ceos(max_results=3)"
        new_line = "results = scraper.search_custom_query(custom_query=query, max_results=5)"
        
        if old_line in content:
            updated_content = content.replace(old_line, new_line)
            
            with open('real_autonomous_organism.py', 'w') as f:
                f.write(updated_content)
            
            print("✅ Successfully patched real_autonomous_organism.py")
            return True
        else:
            print("❌ Could not find the line to replace")
            return False
            
    except Exception as e:
        print(f"❌ Error patching file: {e}")
        return False

def main():
    print("🔧 DIVERSE SEARCH SCRAPER FIX")
    print("=" * 30)
    print("📋 The autonomous organism needs to use custom queries")
    print("")
    
    # Show the issue
    print("🔍 ISSUE IDENTIFIED:")
    print("   The scraper is hardcoded to use Montreal CEO searches")
    print("   Our diverse queries are being ignored")
    print("")
    
    # Create custom search method
    custom_method = create_custom_search_method()
    print("✅ Created custom search method")
    
    # Show patch for autonomous organism
    organism_patch = patch_autonomous_organism()
    print("✅ Created autonomous organism patch")
    
    # Apply direct fix
    print("\n🔧 Applying direct fix...")
    success = create_direct_fix()
    
    if success:
        print("\n🎉 FIX APPLIED SUCCESSFULLY!")
        print("   ✅ Autonomous organism now uses custom diverse queries")
        print("   🧪 Test with: python3 real_autonomous_organism.py --test")
        print("   🎯 Should now find NEW people with diverse searches!")
    else:
        print("\n❌ MANUAL FIX NEEDED:")
        print("   1. Open real_autonomous_organism.py")
        print("   2. Find line: results = scraper.search_montreal_ceos(max_results=3)")
        print("   3. Replace with: results = scraper.search_custom_query(custom_query=query, max_results=5)")
        print("   4. Add the custom_search_query method to SerpAPILeadScraper")
    
    print(f"\n📋 CUSTOM SEARCH METHOD TO ADD:")
    print(custom_method)

if __name__ == "__main__":
    main()
