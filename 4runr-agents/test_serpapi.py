#!/usr/bin/env python3
"""
Simple test script to verify SerpAPI key functionality
"""
import os
import requests
from dotenv import load_dotenv

def test_serpapi_key():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('SERPAPI_KEY')
    
    if not api_key:
        print("❌ SERPAPI_KEY not found in environment variables")
        return False
    
    print(f"🔑 Testing SerpAPI key: {api_key[:10]}...")
    
    # Test with a simple Google search
    url = "https://serpapi.com/search"
    params = {
        'engine': 'google',
        'q': 'test search',
        'api_key': api_key,
        'num': 1  # Only get 1 result for testing
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got valid results
            if 'organic_results' in data:
                print("✅ SerpAPI key is working! Got search results.")
                print(f"📊 Credits left: {data.get('search_metadata', {}).get('credits_left', 'Unknown')}")
                return True
            elif 'error' in data:
                print(f"❌ SerpAPI error: {data['error']}")
                return False
            else:
                print("⚠️  Unexpected response format")
                print(f"Response keys: {list(data.keys())}")
                return False
                
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid API key")
            return False
        elif response.status_code == 429:
            print("❌ Rate limit exceeded")
            return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing SerpAPI Key...")
    print("=" * 40)
    
    success = test_serpapi_key()
    
    print("=" * 40)
    if success:
        print("🎉 SerpAPI test completed successfully!")
    else:
        print("💥 SerpAPI test failed!")