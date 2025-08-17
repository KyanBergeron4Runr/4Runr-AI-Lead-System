#!/usr/bin/env python3
"""
REAL EMAIL VALIDATION TEST
===========================
Testing if our generated emails can actually be validated with REAL domain checks
"""

import socket
import dns.resolver
import requests
import time

def test_real_domain_validation():
    """Test real domain validation on the companies from our database"""
    
    real_companies = [
        "techcorp.com",
        "startupxyz.com", 
        "yapla.com",
        "jonar.com",
        "courimo.com"
    ]
    
    print("🔍 REAL DOMAIN VALIDATION TEST")
    print("=" * 50)
    print("Testing actual domain validation on real companies from our database")
    print()
    
    for domain in real_companies:
        print(f"🌐 Testing domain: {domain}")
        print("-" * 30)
        
        # Test 1: Domain exists (DNS resolution)
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ Domain exists: {ip}")
            domain_exists = True
        except socket.gaierror:
            print(f"❌ Domain does not exist")
            domain_exists = False
        
        # Test 2: MX records (can receive email)
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_list = [str(mx) for mx in mx_records]
            print(f"✅ MX records found: {len(mx_list)} records")
            for mx in mx_list[:3]:  # Show first 3
                print(f"   - {mx}")
            has_mx = True
        except:
            print(f"❌ No MX records found")
            has_mx = False
        
        # Test 3: HTTP response (website exists)
        try:
            response = requests.get(f"http://{domain}", timeout=5)
            print(f"✅ Website responds: HTTP {response.status_code}")
            website_exists = True
        except:
            try:
                response = requests.get(f"https://{domain}", timeout=5)
                print(f"✅ Website responds: HTTPS {response.status_code}")
                website_exists = True
            except:
                print(f"❌ Website does not respond")
                website_exists = False
        
        # Summary
        if domain_exists and has_mx:
            print(f"🎯 RESULT: Domain is VALID for email")
        else:
            print(f"⚠️ RESULT: Domain may not be valid for email")
        
        print()
        time.sleep(1)  # Be respectful with requests
    
    print("=" * 50)
    print("🎯 REAL VALIDATION TEST COMPLETE")
    print("These are actual DNS lookups and HTTP requests to real domains")

if __name__ == "__main__":
    test_real_domain_validation()
