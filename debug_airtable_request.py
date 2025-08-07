#!/usr/bin/env python3
"""
Debug the Airtable API request to see what's going wrong
"""

import requests
import sys
from pathlib import Path
sys.path.append('4runr-lead-scraper')
from config.settings import get_settings

def debug_airtable_request():
    settings = get_settings()
    api_key = settings.airtable.api_key
    base_id = settings.airtable.base_id
    table_name = settings.airtable.table_name

    print(f'🔍 Debugging Airtable API request...')
    print(f'Base ID: {base_id}')
    print(f'Table: {table_name}')

    # Test record ID from the error logs
    test_record_id = 'recjOd4zlwDwJ8X8b'
    
    # Build the URL like the engagement defaults manager does
    from urllib.parse import quote
    encoded_table_name = quote(table_name)
    base_url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}"
    
    print(f'🌐 Base URL: {base_url}')
    
    # Headers
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Get record without field filtering
    print(f'\n🧪 Test 1: Get record without field filtering')
    url = f"{base_url}/{test_record_id}"
    print(f'URL: {url}')
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            fields = data.get('fields', {})
            print(f'✅ Success! Fields returned: {list(fields.keys())}')
            
            # Check if engagement fields exist
            engagement_fields = ['Engagement_Status', 'Email_Confidence_Level', 'Level Engaged']
            for field in engagement_fields:
                value = fields.get(field)
                print(f'  {field}: {value}')
        else:
            print(f'❌ Error: {response.text}')
    except Exception as e:
        print(f'❌ Exception: {e}')
    
    # Test 2: Get record with field filtering (like the engagement defaults manager does)
    print(f'\n🧪 Test 2: Get record with field filtering')
    fields_to_get = ['Engagement_Status', 'Email_Confidence_Level', 'Level Engaged']
    params = {'fields[]': fields_to_get}
    
    print(f'URL: {url}')
    print(f'Params: {params}')
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            fields = data.get('fields', {})
            print(f'✅ Success! Fields returned: {list(fields.keys())}')
            for field in fields_to_get:
                value = fields.get(field)
                print(f'  {field}: {value}')
        else:
            print(f'❌ Error: {response.text}')
    except Exception as e:
        print(f'❌ Exception: {e}')

if __name__ == "__main__":
    debug_airtable_request()