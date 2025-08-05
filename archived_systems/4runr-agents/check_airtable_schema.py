#!/usr/bin/env python3
"""
Check Airtable Schema Details

Get detailed schema information including select field options
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Get Airtable configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

print("🔍 Checking Airtable Schema Details")
print("=" * 50)

headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

# Get detailed schema
schema_url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"

try:
    response = requests.get(schema_url, headers=headers)
    
    if response.status_code == 200:
        schema_data = response.json()
        
        # Find our table
        target_table = None
        for table in schema_data.get('tables', []):
            if table['name'] == AIRTABLE_TABLE_NAME:
                target_table = table
                break
        
        if target_table:
            print(f"✅ Found table: {target_table['name']}")
            print("\nDetailed field information:")
            
            for field in target_table.get('fields', []):
                field_name = field['name']
                field_type = field['type']
                
                print(f"\n📋 {field_name}")
                print(f"   Type: {field_type}")
                
                # Check for select field options
                if field_type == 'singleSelect':
                    options = field.get('options', {}).get('choices', [])
                    if options:
                        print(f"   Valid options:")
                        for option in options:
                            print(f"     - {option['name']}")
                    else:
                        print(f"   No predefined options")
                
                elif field_type == 'multipleSelects':
                    options = field.get('options', {}).get('choices', [])
                    if options:
                        print(f"   Valid options:")
                        for option in options:
                            print(f"     - {option['name']}")
                    else:
                        print(f"   No predefined options")
                
                # Check if field is required
                if field.get('required'):
                    print(f"   ⚠️ Required field")
        
        else:
            print(f"❌ Table '{AIRTABLE_TABLE_NAME}' not found")
    
    else:
        print(f"❌ Schema request failed: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {e}")