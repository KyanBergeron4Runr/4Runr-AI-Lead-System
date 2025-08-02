#!/usr/bin/env python3
"""
Check Airtable tables and find the correct table name
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def check_airtable_tables():
    """Check what tables exist in Airtable"""
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    print(f"🔍 Checking Airtable Base: {base_id}")
    
    # Try different common table names
    table_names = ['Table 1', 'tblTable1', 'Leads', 'Table1', 'Main']
    
    for table_name in table_names:
        try:
            url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            print(f"\n📋 Testing table: '{table_name}'")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                print(f"   ✅ SUCCESS! Found {len(records)} records")
                
                if records:
                    # Show first record structure
                    first_record = records[0]
                    fields = first_record.get('fields', {})
                    print(f"   📝 Sample fields: {list(fields.keys())}")
                    
                    # Show names of leads
                    names = []
                    for record in records:
                        record_fields = record.get('fields', {})
                        name = record_fields.get('Name', record_fields.get('Full Name', 'Unknown'))
                        names.append(name)
                    
                    print(f"   👥 Lead names: {names}")
                
                return table_name, records
            
            elif response.status_code == 404:
                print(f"   ❌ Table not found")
            else:
                print(f"   ⚠️ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    return None, []

if __name__ == "__main__":
    print("🔍 CHECKING AIRTABLE CONFIGURATION")
    print("="*50)
    
    table_name, records = check_airtable_tables()
    
    if table_name:
        print(f"\n✅ FOUND WORKING TABLE: '{table_name}'")
        print(f"📊 Records found: {len(records)}")
    else:
        print("\n❌ NO WORKING TABLE FOUND")
        print("💡 Check your Airtable Base ID and API key")