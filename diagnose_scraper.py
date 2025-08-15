#!/usr/bin/env python3
"""
Diagnose why the scraper isn't finding leads
"""

import os
import requests
import json
from dotenv import load_dotenv

def diagnose_scraper():
    """Test SerpAPI connection and search functionality"""
    
    print("🔍 DIAGNOSING SCRAPER ISSUES")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Check environment variables
    print("\n📋 CHECKING CONFIGURATION:")
    serpapi_key = os.getenv('SERPAPI_API_KEY')
    search_location = os.getenv('SEARCH_LOCATION', 'Montreal, Quebec, Canada')
    search_queries = os.getenv('SEARCH_QUERIES', 'CEO,Founder,President')
    max_leads = int(os.getenv('MAX_LEADS_PER_RUN', '5'))
    
    print(f"✅ SerpAPI Key: {'Set' if serpapi_key else '❌ Missing'}")
    print(f"✅ Search Location: {search_location}")
    print(f"✅ Search Queries: {search_queries}")
    print(f"✅ Max Leads: {max_leads}")
    
    if not serpapi_key:
        print("❌ SERPAPI_API_KEY is missing!")
        return
    
    # Test SerpAPI connection
    print(f"\n🔗 TESTING SERPAPI CONNECTION:")
    
    try:
        # Test basic SerpAPI connectivity
        test_url = f"https://serpapi.com/account?api_key={serpapi_key}"
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            account_data = response.json()
            print(f"✅ SerpAPI Connection: SUCCESS")
            print(f"✅ Account Plan: {account_data.get('plan', 'Unknown')}")
            print(f"✅ Searches Left: {account_data.get('searches_left', 'Unknown')}")
        else:
            print(f"❌ SerpAPI Connection: FAILED ({response.status_code})")
            return
            
    except Exception as e:
        print(f"❌ SerpAPI Connection Error: {e}")
        return
    
    # Test actual search
    print(f"\n🔍 TESTING LINKEDIN SEARCH:")
    
    try:
        search_params = {
            'api_key': serpapi_key,
            'engine': 'google',
            'q': f'site:linkedin.com/in/ CEO Montreal',
            'location': search_location,
            'num': '10'
        }
        
        search_url = "https://serpapi.com/search"
        response = requests.get(search_url, params=search_params, timeout=30)
        
        if response.status_code == 200:
            results = response.json()
            organic_results = results.get('organic_results', [])
            
            print(f"✅ Search Response: SUCCESS")
            print(f"✅ Results Found: {len(organic_results)}")
            
            if organic_results:
                print(f"\n📊 SAMPLE RESULTS:")
                for i, result in enumerate(organic_results[:3], 1):
                    title = result.get('title', 'No title')
                    link = result.get('link', 'No link')
                    snippet = result.get('snippet', 'No snippet')
                    
                    print(f"{i}. {title}")
                    print(f"   Link: {link}")
                    print(f"   Snippet: {snippet[:100]}...")
                    print()
            else:
                print("⚠️ No organic results found")
                print("This might be why the scraper returned 0 leads")
                
                # Check for other result types
                if 'error' in results:
                    print(f"❌ API Error: {results['error']}")
                
                if 'search_information' in results:
                    search_info = results['search_information']
                    print(f"Search took: {search_info.get('query_displayed_time', 'Unknown')}")
                    print(f"Total results: {search_info.get('total_results', 'Unknown')}")
        else:
            print(f"❌ Search Request FAILED ({response.status_code})")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Search Error: {e}")
    
    # Test alternative search terms
    print(f"\n🎯 TESTING ALTERNATIVE SEARCHES:")
    
    test_queries = [
        'site:linkedin.com/in/ "CEO" Montreal Canada',
        'site:linkedin.com/in/ "Founder" Montreal',
        'site:linkedin.com/in/ "President" Quebec Canada',
        'LinkedIn CEO Montreal startup',
        'LinkedIn executive Montreal Quebec'
    ]
    
    for i, query in enumerate(test_queries, 1):
        try:
            search_params = {
                'api_key': serpapi_key,
                'engine': 'google',
                'q': query,
                'num': '5'
            }
            
            response = requests.get("https://serpapi.com/search", params=search_params, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                organic_count = len(results.get('organic_results', []))
                print(f"{i}. Query: '{query}' → {organic_count} results")
            else:
                print(f"{i}. Query: '{query}' → FAILED ({response.status_code})")
                
        except Exception as e:
            print(f"{i}. Query: '{query}' → ERROR: {e}")
    
    print(f"\n🎯 DIAGNOSIS COMPLETE!")
    print("If searches are returning 0 results, the issue might be:")
    print("1. Search terms are too specific")
    print("2. LinkedIn is blocking SerpAPI searches")
    print("3. Montreal market is oversearched")
    print("4. Need to try different search strategies")

if __name__ == "__main__":
    diagnose_scraper()
