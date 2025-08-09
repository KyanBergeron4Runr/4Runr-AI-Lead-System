#!/usr/bin/env python3
"""
EC2 Airtable Debug Script

This script helps diagnose 404 errors specifically on EC2 instances.
Run this on your EC2 instance to identify the issue.
"""

import os
import sys
import requests
import json
from pathlib import Path

def check_environment_loading():
    """Check how environment variables are being loaded on EC2."""
    
    print("🔍 EC2 ENVIRONMENT VARIABLE DEBUG")
    print("=" * 50)
    
    # Check current working directory
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📁 Script location: {Path(__file__).parent.absolute()}")
    print()
    
    # Check for .env files
    env_files_to_check = [
        '.env',
        '4runr-outreach-system/.env',
        '4runr-lead-scraper/.env',
        '4runr-brain/.env',
        '../.env',
        '../4runr-outreach-system/.env',
        '../4runr-lead-scraper/.env'
    ]
    
    print("📋 Checking for .env files:")
    found_files = []
    for env_file in env_files_to_check:
        if os.path.exists(env_file):
            size = os.path.getsize(env_file)
            print(f"✅ Found: {env_file} ({size} bytes)")
            found_files.append(env_file)
        else:
            print(f"❌ Missing: {env_file}")
    
    print()
    
    if not found_files:
        print("❌ NO .env FILES FOUND!")
        print("💡 This is likely why you're getting 404 errors on EC2")
        return False
    
    # Load and check environment variables
    print("🔑 Environment Variables:")
    env_vars = {}
    
    # Try loading from the first found file
    env_file = found_files[0]
    print(f"📁 Loading from: {env_file}")
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            print(f"📊 File size: {len(content)} characters")
            
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    env_vars[key] = value
                    
                    # Show key info (masked)
                    if 'API_KEY' in key:
                        masked_value = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***"
                        print(f"   {key}: {masked_value}")
                    elif key in ['AIRTABLE_BASE_ID', 'AIRTABLE_TABLE_NAME']:
                        print(f"   {key}: {value}")
    
    except Exception as e:
        print(f"❌ Error reading {env_file}: {str(e)}")
        return False
    
    print()
    
    # Check required variables
    required_vars = ['AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID', 'AIRTABLE_TABLE_NAME']
    missing_vars = []
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables found")
    return env_vars

def test_airtable_from_ec2(env_vars):
    """Test Airtable connection with EC2-specific considerations."""
    
    print("\n🌐 EC2 AIRTABLE CONNECTION TEST")
    print("=" * 50)
    
    api_key = env_vars['AIRTABLE_API_KEY']
    base_id = env_vars['AIRTABLE_BASE_ID']
    table_name = env_vars['AIRTABLE_TABLE_NAME']
    
    print(f"🔑 API Key: {api_key[:15]}...{api_key[-10:]}")
    print(f"🗄️ Base ID: {base_id}")
    print(f"📋 Table Name: '{table_name}'")
    print()
    
    # Test with different table name encodings
    table_variations = [
        table_name,                    # Original
        table_name.replace(' ', '%20'), # URL encoded
        'Table%201',                   # Direct encoding
        'Table+1'                      # Plus encoding
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'EC2-Debug-Script/1.0'
    }
    
    for i, table_var in enumerate(table_variations, 1):
        print(f"🧪 Test {i}: Table name = '{table_var}'")
        
        url = f"https://api.airtable.com/v0/{base_id}/{table_var}"
        
        try:
            response = requests.get(
                url, 
                headers=headers, 
                params={'maxRecords': 1},
                timeout=15  # Longer timeout for EC2
            )
            
            print(f"   📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                data = response.json()
                records = data.get('records', [])
                print(f"   📊 Records found: {len(records)}")
                return True
            elif response.status_code == 404:
                print("   ❌ 404 - Not Found")
                print(f"   📄 Response: {response.text[:200]}...")
            elif response.status_code == 401:
                print("   ❌ 401 - Unauthorized (API key issue)")
                print(f"   📄 Response: {response.text}")
                return False
            elif response.status_code == 403:
                print("   ❌ 403 - Forbidden (permissions issue)")
                print(f"   📄 Response: {response.text}")
                return False
            else:
                print(f"   ⚠️ Unexpected status: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
        
        except requests.exceptions.Timeout:
            print("   ❌ Request timeout (network issue)")
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection error (network/DNS issue)")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        print()
    
    return False

def provide_ec2_solutions():
    """Provide specific solutions for EC2 issues."""
    
    print("🔧 EC2 TROUBLESHOOTING SOLUTIONS")
    print("=" * 50)
    
    print("If you're still getting 404 errors on EC2, try these solutions:")
    print()
    
    print("1. 📁 ENVIRONMENT FILE LOCATION:")
    print("   - Ensure .env file is in the correct directory")
    print("   - Check file permissions: chmod 644 .env")
    print("   - Verify file ownership: chown user:user .env")
    print()
    
    print("2. 🔄 RESTART SERVICES:")
    print("   - Restart your application after updating .env")
    print("   - Clear any cached environment variables")
    print("   - sudo systemctl restart your-service")
    print()
    
    print("3. 🌐 NETWORK ISSUES:")
    print("   - Check EC2 security groups allow outbound HTTPS (port 443)")
    print("   - Verify DNS resolution: nslookup api.airtable.com")
    print("   - Test connectivity: curl -I https://api.airtable.com")
    print()
    
    print("4. 📋 TABLE NAME ENCODING:")
    print("   - Try using 'Table%201' instead of 'Table 1'")
    print("   - Or use the table ID: tblbBSE2jJv9am7ZA")
    print()
    
    print("5. 🔑 API KEY ISSUES:")
    print("   - Regenerate your Airtable Personal Access Token")
    print("   - Ensure the token has access to the specific base")
    print("   - Check token permissions in Airtable settings")
    print()
    
    print("6. 📝 QUICK FIX - Update your .env file:")
    print("   AIRTABLE_TABLE_NAME=Table%201")
    print("   # OR use table ID:")
    print("   AIRTABLE_TABLE_NAME=tblbBSE2jJv9am7ZA")

def main():
    """Main diagnostic function."""
    
    print("🚀 EC2 AIRTABLE 404 ERROR DIAGNOSTIC")
    print("=" * 60)
    print("Run this script on your EC2 instance to diagnose the issue.")
    print()
    
    # Step 1: Check environment loading
    env_vars = check_environment_loading()
    
    if not env_vars:
        print("\n❌ ENVIRONMENT SETUP ISSUE DETECTED")
        print("The problem is with environment variable loading on EC2.")
        provide_ec2_solutions()
        return
    
    # Step 2: Test Airtable connection
    success = test_airtable_from_ec2(env_vars)
    
    if success:
        print("🎉 CONNECTION SUCCESSFUL!")
        print("The issue might be intermittent or resolved.")
    else:
        print("❌ CONNECTION FAILED")
        provide_ec2_solutions()

if __name__ == "__main__":
    main()