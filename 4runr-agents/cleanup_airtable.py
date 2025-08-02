#!/usr/bin/env python3
"""
Clean up duplicate entries in Airtable
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
TABLE_NAME = "Table 1"

headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

def get_all_records():
    """Get all records from Airtable"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
    
    all_records = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
            
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            all_records.extend(data.get('records', []))
            
            offset = data.get('offset')
            if not offset:
                break
        else:
            print(f"Error getting records: {response.text}")
            break
    
    return all_records

def delete_record(record_id):
    """Delete a record from Airtable"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}/{record_id}"
    
    response = requests.delete(url, headers=headers)
    return response.status_code == 200

def main():
    print("🧹 Cleaning up Airtable duplicates...")
    
    # Get all records
    records = get_all_records()
    print(f"Found {len(records)} total records")
    
    # Group by name to find duplicates
    name_groups = {}
    for record in records:
        name = record['fields'].get('Full Name', 'Unknown')
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append(record)
    
    # Show what we found
    print("\n📊 Current records:")
    for name, group in name_groups.items():
        print(f"  {name}: {len(group)} entries")
    
    # Find duplicates and keep only the most recent
    to_delete = []
    to_keep = []
    
    for name, group in name_groups.items():
        if len(group) > 1:
            # Sort by creation time (most recent first)
            sorted_group = sorted(group, key=lambda x: x['createdTime'], reverse=True)
            
            # Keep the first (most recent), delete the rest
            to_keep.append(sorted_group[0])
            to_delete.extend(sorted_group[1:])
        else:
            to_keep.append(group[0])
    
    print(f"\n🎯 Plan:")
    print(f"  Keep: {len(to_keep)} records")
    print(f"  Delete: {len(to_delete)} duplicates")
    
    if to_delete:
        print("\n🗑️ Deleting duplicates...")
        deleted_count = 0
        
        for record in to_delete:
            name = record['fields'].get('Full Name', 'Unknown')
            record_id = record['id']
            
            if delete_record(record_id):
                print(f"  ✅ Deleted duplicate: {name}")
                deleted_count += 1
            else:
                print(f"  ❌ Failed to delete: {name}")
        
        print(f"\n🎉 Cleanup complete! Deleted {deleted_count} duplicates")
    else:
        print("\n✅ No duplicates found!")
    
    # Show final state
    final_records = get_all_records()
    print(f"\n📋 Final state: {len(final_records)} records remaining")
    
    for record in final_records:
        name = record['fields'].get('Full Name', 'Unknown')
        linkedin = record['fields'].get('LinkedIn URL', 'No URL')
        print(f"  👤 {name} - {linkedin}")

if __name__ == "__main__":
    main()