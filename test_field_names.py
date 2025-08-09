#!/usr/bin/env python3
"""
Test script to verify Airtable field names are working correctly
"""

import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent / "4runr-lead-scraper"))
sys.path.append(str(Path(__file__).parent / "4runr-outreach-system" / "shared"))

try:
    from config.settings import get_settings
    import requests
    from urllib.parse import quote
    
    def test_airtable_fields():
        """Test that Airtable field names are correctly recognized"""
        print("🧪 Testing Airtable Field Names")
        print("=" * 40)
        
        # Get settings
        settings = get_settings()
        api_key = settings.airtable.api_key
        base_id = settings.airtable.base_id
        table_name = settings.airtable.table_name
        
        # API setup
        encoded_table_name = quote(table_name)
        base_url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}"
        headers = {'Authorization': f'Bearer {api_key}'}
        
        print(f"📋 Testing table: {table_name}")
        print(f"🔗 Base URL: {base_url}")
        
        # Test 1: Get first record to see available fields
        print("\n🧪 Test 1: Getting first record to check available fields")
        try:
            response = requests.get(f"{base_url}?maxRecords=1", headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                records = result.get('records', [])
                
                if records:
                    fields = records[0].get('fields', {})
                    print(f"✅ Success! Found {len(fields)} fields:")
                    
                    # Check for the specific fields we updated
                    expected_fields = [
                        'Full Name',
                        'LinkedIn URL', 
                        'Job Title',
                        'Company',
                        'Email',
                        'AI Message',
                        'Response Notes',
                        'Engagement_Status',
                        'Email_Confidence_Level',
                        'Level Engaged',
                        'Website',
                        'Company Description',
                        'Website Insights',
                        'Top Services',
                        'Business_Type'
                    ]
                    
                    found_fields = []
                    missing_fields = []
                    
                    for field in expected_fields:
                        if field in fields:
                            found_fields.append(field)
                            print(f"   ✅ {field}: {fields[field]}")
                        else:
                            missing_fields.append(field)
                            print(f"   ❌ {field}: NOT FOUND")
                    
                    print(f"\n📊 Results:")
                    print(f"   Found: {len(found_fields)}/{len(expected_fields)} fields")
                    print(f"   Missing: {len(missing_fields)} fields")
                    
                    if missing_fields:
                        print(f"   Missing fields: {', '.join(missing_fields)}")
                    
                    return len(missing_fields) == 0
                else:
                    print("❌ No records found in table")
                    return False
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False
    
    if __name__ == "__main__":
        success = test_airtable_fields()
        
        if success:
            print("\n🎉 All field names are working correctly!")
        else:
            print("\n⚠️ Some field names may need attention")
            
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the correct directory with the right environment")