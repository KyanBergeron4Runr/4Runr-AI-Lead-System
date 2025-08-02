#!/usr/bin/env python3
"""
Check Airtable Fields
Checks what fields exist in your Airtable base
"""

import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

def check_airtable_fields():
    """Check what fields exist in Airtable"""
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
    
    if not all([api_key, base_id]):
        print("❌ Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID")
        return
    
    # Get table schema
    encoded_table_name = quote(table_name)
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            tables = data.get('tables', [])
            
            # Find our table
            target_table = None
            for table in tables:
                if table['name'] == table_name:
                    target_table = table
                    break
            
            if target_table:
                print(f"✅ Found table: {table_name}")
                print(f"📋 Available fields:")
                
                for field in target_table.get('fields', []):
                    field_name = field.get('name', '')
                    field_type = field.get('type', '')
                    print(f"  - {field_name} ({field_type})")
            else:
                print(f"❌ Table '{table_name}' not found")
                print("Available tables:")
                for table in tables:
                    print(f"  - {table['name']}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_airtable_fields()