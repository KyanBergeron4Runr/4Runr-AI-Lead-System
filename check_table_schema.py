#!/usr/bin/env python3
"""
Check Airtable table schema to see all fields
"""

import requests
import sys
from pathlib import Path
sys.path.append('4runr-lead-scraper')
from config.settings import get_settings

def check_table_schema():
    settings = get_settings()
    api_key = settings.airtable.api_key
    base_id = settings.airtable.base_id
    table_name = settings.airtable.table_name

    print(f'🔍 Checking Airtable table schema...')
    print(f'Base ID: {base_id}')
    print(f'Table: {table_name}')

    # Try to get table schema using the meta API
    url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
    headers = {'Authorization': f'Bearer {api_key}'}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            tables = data.get('tables', [])
            
            for table in tables:
                if table['name'] == table_name:
                    print(f'📋 Found table: {table["name"]}')
                    print(f'📊 All fields in this table:')
                    
                    engagement_fields = []
                    for i, field in enumerate(table.get('fields', []), 1):
                        field_name = field.get('name', 'Unknown')
                        field_type = field.get('type', 'Unknown')
                        print(f'  {i:2d}. {field_name} ({field_type})')
                        
                        # Check for engagement-related fields
                        if any(keyword in field_name.lower() for keyword in ['engagement', 'confidence', 'level', 'engaged']):
                            engagement_fields.append(field_name)
                    
                    print(f'\n🎯 Engagement-related fields found:')
                    if engagement_fields:
                        for field in engagement_fields:
                            print(f'  ✅ {field}')
                    else:
                        print('  ❌ No engagement-related fields found')
                    
                    # Check for the specific fields we need
                    needed_fields = ['Engagement_Status', 'Email_Confidence_Level', 'Level Engaged']
                    print(f'\n🔍 Checking for required fields:')
                    for needed_field in needed_fields:
                        found = any(field['name'] == needed_field for field in table.get('fields', []))
                        status = '✅' if found else '❌'
                        print(f'  {status} {needed_field}')
                    
                    return
            
            print(f'❌ Table "{table_name}" not found')
            print(f'Available tables:')
            for table in tables:
                print(f'  - {table["name"]}')
        else:
            print(f'❌ API Error: {response.status_code} - {response.text}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    check_table_schema()