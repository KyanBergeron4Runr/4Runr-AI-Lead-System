#!/usr/bin/env python3
"""
Check what Source options are available in Airtable
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

def check_table_schema():
    """Check the table schema to see Source field options"""
    
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Find Table 1
        for table in data.get('tables', []):
            if table['name'] == 'Table 1':
                print(f"📋 Found Table 1 with {len(table['fields'])} fields:")
                
                for field in table['fields']:
                    field_name = field['name']
                    field_type = field['type']
                    
                    print(f"  - {field_name} ({field_type})")
                    
                    # If it's a single select, show options
                    if field_type == 'singleSelect' and field_name == 'Source':
                        options = field.get('options', {}).get('choices', [])
                        print(f"    Available options:")
                        for option in options:
                            print(f"      • {option['name']}")
                        
                        if not options:
                            print("    No options defined - you can add any value")
                
                return True
        
        print("❌ Table 1 not found")
        return False
    else:
        print(f"❌ Error getting schema: {response.text}")
        return False

def test_without_source():
    """Test adding a record without the Source field"""
    
    print("\n🧪 Testing without Source field...")
    
    test_record = {
        'fields': {
            'Full Name': 'Test Without Source',
            'LinkedIn URL': 'https://linkedin.com/in/test',
            'Job Title': 'CEO',
            'Company': 'Test Company',
            'Email': 'test@company.com'
        }
    }
    
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Table 1"
    response = requests.post(url, headers=headers, json=test_record)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! Record added without Source")
        record_id = response.json().get('id')
        
        # Clean up
        delete_response = requests.delete(f"{url}/{record_id}", headers=headers)
        print(f"Cleanup: {delete_response.status_code}")
        
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

if __name__ == "__main__":
    print("🔍 Checking Airtable Source field options...")
    
    schema_success = check_table_schema()
    
    if schema_success:
        test_without_source()
    
    print("\n💡 Solution:")
    print("1. Either add 'LinkedIn' as an option to your Source field in Airtable")
    print("2. Or we'll skip the Source field for now and focus on the core business data")