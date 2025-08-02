#!/usr/bin/env python3
"""
LinkedIn URL Validator - Test and fix LinkedIn URLs in the database
"""

import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('linkedin-validator')

def test_linkedin_url(url, timeout=10):
    """Test if a LinkedIn URL is accessible"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            return True, "Working"
        elif response.status_code == 404:
            return False, "404 Not Found"
        elif response.status_code == 999:
            return False, "999 Anti-bot protection"
        else:
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"

def main():
    print("🔍 LINKEDIN URL VALIDATOR")
    print("=" * 60)
    
    # Current database URLs to test
    test_urls = [
        ("Marc Parent", "CAE Inc", "https://www.linkedin.com/in/marc-parent-cae/"),
        ("Philip Fayer", "Nuvei Corporation", "https://www.linkedin.com/in/philip-fayer"),
        ("Tobias Lütke", "Shopify", "https://www.linkedin.com/in/tobi/"),
        ("Dax Dasilva", "Lightspeed Commerce", "https://www.linkedin.com/in/daxdasilva/"),
        ("George Schindler", "CGI Group", "https://www.linkedin.com/in/george-schindler-cgi/"),
        ("Éric Martel", "Bombardier", "https://www.linkedin.com/in/eric-martel-bombardier/"),
        ("Ian Edwards", "SNC-Lavalin", "https://www.linkedin.com/in/ian-l-edwards/"),
        ("Neil Rossy", "Dollarama", "https://www.linkedin.com/in/neil-rossy/"),
        ("Eric La Flèche", "Metro Inc", "https://www.linkedin.com/in/eric-la-fleche/"),
        ("Sophie Brochu", "Hydro-Québec", "https://www.linkedin.com/in/sophie-brochu/"),
    ]
    
    print(f"\n🧪 Testing {len(test_urls)} LinkedIn URLs...")
    
    working_urls = []
    broken_urls = []
    
    for i, (name, company, url) in enumerate(test_urls, 1):
        print(f"\n{i:2d}. Testing {name} ({company})")
        print(f"    URL: {url}")
        
        is_working, status = test_linkedin_url(url)
        
        if is_working:
            print(f"    ✅ {status}")
            working_urls.append((name, company, url))
        else:
            print(f"    ❌ {status}")
            broken_urls.append((name, company, url, status))
        
        # Rate limiting
        time.sleep(2)
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   ✅ Working URLs: {len(working_urls)}")
    print(f"   ❌ Broken URLs: {len(broken_urls)}")
    print(f"   📈 Success Rate: {len(working_urls)/len(test_urls)*100:.1f}%")
    
    if working_urls:
        print(f"\n✅ WORKING LINKEDIN URLS:")
        for name, company, url in working_urls:
            print(f"   • {name} ({company}): {url}")
    
    if broken_urls:
        print(f"\n❌ BROKEN LINKEDIN URLS:")
        for name, company, url, status in broken_urls:
            print(f"   • {name} ({company}): {url} - {status}")
    
    print(f"\n🔧 RECOMMENDED FIXES:")
    
    # Suggest alternative URLs for broken ones
    suggested_fixes = {
        "Philip Fayer": [
            "https://www.linkedin.com/in/philip-fayer-nuvei/",
            "https://www.linkedin.com/in/philipfayer/",
            "https://www.linkedin.com/in/philip-fayer-ceo/"
        ],
        "Neil Rossy": [
            "https://www.linkedin.com/in/neil-rossy-dollarama/",
            "https://www.linkedin.com/in/neilrossy/"
        ],
        "Eric La Flèche": [
            "https://www.linkedin.com/in/eric-lafleche/",
            "https://www.linkedin.com/in/eric-la-fleche-metro/"
        ]
    }
    
    for name, company, url, status in broken_urls:
        print(f"\n   🔧 {name} ({company}) - {status}")
        if name in suggested_fixes:
            print(f"      Try these alternatives:")
            for alt_url in suggested_fixes[name]:
                print(f"      • {alt_url}")
        else:
            # Generate some common alternatives
            first_name = name.split()[0].lower()
            last_name = name.split()[-1].lower().replace('é', 'e').replace('ü', 'u')
            company_short = company.split()[0].lower()
            
            alternatives = [
                f"https://www.linkedin.com/in/{first_name}-{last_name}/",
                f"https://www.linkedin.com/in/{first_name}{last_name}/",
                f"https://www.linkedin.com/in/{first_name}-{last_name}-{company_short}/",
                f"https://www.linkedin.com/in/{first_name}.{last_name}/"
            ]
            
            print(f"      Try these pattern-based alternatives:")
            for alt_url in alternatives:
                print(f"      • {alt_url}")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Manually verify the suggested alternative URLs")
    print(f"   2. Update the database with working URLs only")
    print(f"   3. Remove or replace broken URLs")
    print(f"   4. Re-run the pipeline with corrected URLs")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 URL validation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()