#!/usr/bin/env python3
"""
Quick Diverse Search Fix
========================
Immediate implementation to get diverse leads instead of same 3 people
"""

import sqlite3
import random
import logging

class QuickDiverseSearchFix:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def create_diverse_searches(self):
        """Create immediately usable diverse search combinations"""
        
        locations = [
            'Toronto, Ontario, Canada',
            'Vancouver, BC, Canada', 
            'Calgary, Alberta, Canada',
            'Ottawa, Ontario, Canada',
            'Montreal, Quebec, Canada'
        ]
        
        job_titles = [
            'Chief Technology Officer', 'CTO',
            'Chief Marketing Officer', 'CMO', 
            'Chief Operating Officer', 'COO',
            'Vice President', 'VP Sales', 'VP Marketing',
            'Director', 'Managing Director',
            'Founder', 'Co-Founder',
            'Owner', 'Business Owner',
            'General Manager', 'Operations Manager',
            'Product Manager', 'Sales Manager'
        ]
        
        industries = [
            'technology', 'tech startup', 'software',
            'consulting', 'digital marketing', 
            'healthcare', 'fintech', 'e-commerce',
            'real estate', 'manufacturing',
            'education', 'legal services'
        ]
        
        # Create diverse search combinations
        diverse_searches = []
        
        # Method 1: Job Title + Location
        for location in locations:
            for title in job_titles[:8]:  # Use first 8 titles
                search = f'site:linkedin.com/in/ "{title}" {location.split(",")[0]}'
                diverse_searches.append(search)
        
        # Method 2: Industry + Job Title + Location  
        for location in locations[:3]:  # Top 3 cities
            for industry in industries[:6]:  # Top 6 industries
                for title in ['CEO', 'Founder', 'Director']:
                    search = f'site:linkedin.com/in/ {title} {industry} {location.split(",")[0]}'
                    diverse_searches.append(search)
        
        self.logger.info(f"✅ Created {len(diverse_searches)} diverse search combinations")
        return diverse_searches

    def create_test_searches(self):
        """Create a small set of test searches for immediate use"""
        test_searches = [
            'site:linkedin.com/in/ "Chief Technology Officer" Toronto',
            'site:linkedin.com/in/ "Marketing Director" Vancouver',
            'site:linkedin.com/in/ "Business Owner" Calgary', 
            'site:linkedin.com/in/ "VP Sales" Ottawa',
            'site:linkedin.com/in/ Founder startup Toronto',
            'site:linkedin.com/in/ CEO technology Vancouver',
            'site:linkedin.com/in/ Director consulting Calgary',
            'site:linkedin.com/in/ "Operations Manager" Ottawa'
        ]
        
        self.logger.info(f"✅ Created {len(test_searches)} test searches")
        return test_searches

    def modify_autonomous_organism_search(self):
        """Show how to modify the autonomous organism search logic"""
        
        modification_guide = """
        📋 MODIFY real_autonomous_organism.py:
        
        1. Find the search_queries section (around line 30-35)
        
        2. Replace this:
           search_queries = ['CEO', 'Founder', 'President']
           search_location = 'Montreal, Quebec, Canada'
        
        3. With this diverse rotation:
           diverse_searches = [
               'site:linkedin.com/in/ "Chief Technology Officer" Toronto',
               'site:linkedin.com/in/ "Marketing Director" Vancouver', 
               'site:linkedin.com/in/ "Business Owner" Calgary',
               'site:linkedin.com/in/ "VP Sales" Ottawa',
               'site:linkedin.com/in/ Founder startup Toronto',
               'site:linkedin.com/in/ CEO technology Vancouver'
           ]
           
           # Rotate searches each cycle
           import random
           current_search = random.choice(diverse_searches)
        
        4. Update the scraper call to use varied searches
        
        5. Lower quality filters:
           - Accept "Unknown Company" if LinkedIn + Job Title exist
           - Don't require email if LinkedIn URL is present
           - Accept partial company info extracted from job titles
        """
        
        self.logger.info("📋 Autonomous organism modification guide:")
        print(modification_guide)
        
        return modification_guide

    def create_immediate_patch_file(self):
        """Create a patch file to immediately fix the search diversity"""
        
        patch_code = '''
# IMMEDIATE PATCH FOR DIVERSE SEARCHES
# Add this to real_autonomous_organism.py

import random

class DiverseSearchPatch:
    @staticmethod
    def get_diverse_search():
        """Get a random diverse search query"""
        diverse_searches = [
            'site:linkedin.com/in/ "Chief Technology Officer" Toronto',
            'site:linkedin.com/in/ "Marketing Director" Vancouver',
            'site:linkedin.com/in/ "Business Owner" Calgary', 
            'site:linkedin.com/in/ "VP Sales" Ottawa',
            'site:linkedin.com/in/ Founder startup Toronto',
            'site:linkedin.com/in/ CEO technology Vancouver',
            'site:linkedin.com/in/ Director consulting Calgary',
            'site:linkedin.com/in/ "Operations Manager" Ottawa',
            'site:linkedin.com/in/ "Product Manager" Montreal',
            'site:linkedin.com/in/ "General Manager" Toronto tech'
        ]
        return random.choice(diverse_searches)
    
    @staticmethod
    def should_accept_lead(lead_data):
        """More lenient lead acceptance criteria"""
        # Accept if has LinkedIn + any job title info
        has_linkedin = bool(lead_data.get('linkedin_url'))
        has_job_info = bool(lead_data.get('job_title'))
        has_name = bool(lead_data.get('full_name'))
        
        # Lower bar - just need basic professional info
        return has_linkedin and has_job_info and has_name

# Usage in main scraping function:
# search_query = DiverseSearchPatch.get_diverse_search()
# if DiverseSearchPatch.should_accept_lead(lead_data):
#     save_lead(lead_data)
'''
        
        try:
            with open('diverse_search_patch.py', 'w') as f:
                f.write(patch_code)
            
            self.logger.info("💾 Created diverse_search_patch.py")
            return 'diverse_search_patch.py'
            
        except Exception as e:
            self.logger.error(f"❌ Error creating patch: {e}")
            return None

def main():
    fixer = QuickDiverseSearchFix()
    
    print("🚀 QUICK DIVERSE SEARCH FIX")
    print("=" * 30)
    print("📋 Immediate solution to get NEW leads (not same 3 people)")
    print("")
    
    # Create diverse searches
    diverse_searches = fixer.create_diverse_searches()
    test_searches = fixer.create_test_searches()
    
    print(f"✅ DIVERSE SEARCH READY:")
    print(f"   📊 Generated {len(diverse_searches)} search combinations")
    print(f"   🧪 Created {len(test_searches)} test searches")
    
    print(f"\n🎯 TEST SEARCHES (try these immediately):")
    for i, search in enumerate(test_searches, 1):
        print(f"   {i}. {search}")
    
    # Show modification guide
    print(f"\n📋 MODIFICATION GUIDE:")
    fixer.modify_autonomous_organism_search()
    
    # Create patch file
    patch_file = fixer.create_immediate_patch_file()
    if patch_file:
        print(f"💾 Created patch file: {patch_file}")
    
    print(f"\n🔧 IMMEDIATE ACTIONS:")
    print(f"   1. ✅ Use test searches above in SerpAPI manually")
    print(f"   2. 🔧 Modify autonomous organism with diverse rotation")
    print(f"   3. 📉 Lower quality filters (accept LinkedIn + partial info)")
    print(f"   4. 🧪 Test with: python3 real_autonomous_organism.py --test")
    
    print(f"\n🎉 EXPECTED RESULTS:")
    print(f"   📍 NEW people from Toronto, Vancouver, Calgary")
    print(f"   💼 CTOs, CMOs, VPs, Directors, Managers")
    print(f"   🏢 Tech, consulting, healthcare, fintech professionals")
    print(f"   📊 10-20 new leads instead of same 3 people!")

if __name__ == "__main__":
    main()
