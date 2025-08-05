#!/usr/bin/env python3
"""
Check Kyan Bergeron leads in Airtable and local database.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.airtable_client import get_airtable_client


def check_kyan_in_airtable():
    """Check for Kyan Bergeron records in Airtable."""
    print("🔍 CHECKING KYAN BERGERON IN AIRTABLE:")
    print("=" * 50)
    
    try:
        airtable_client = get_airtable_client()
        
        # Get all records
        all_records = list(airtable_client.table.all())
        
        print(f"📊 Total records in Airtable: {len(all_records)}")
        
        kyan_records = []
        
        for record in all_records:
            fields = record.get('fields', {})
            name = fields.get('Full Name', '') or fields.get('Name', '')
            email = fields.get('Email', '')
            
            # Check if this might be Kyan
            if 'kyan' in name.lower() or 'kyan' in email.lower():
                kyan_records.append(record)
        
        if kyan_records:
            print(f"\n✅ Found {len(kyan_records)} Kyan record(s):")
            
            for i, record in enumerate(kyan_records, 1):
                fields = record.get('fields', {})
                print(f"\n{i}. Record ID: {record['id']}")
                print(f"   📋 Available fields: {list(fields.keys())}")
                for field, value in fields.items():
                    print(f"   {field}: {value}")
        else:
            print("\n❌ No Kyan records found")
            
            # Show all records for debugging
            print(f"\n📋 ALL RECORDS IN AIRTABLE:")
            for i, record in enumerate(all_records, 1):
                fields = record.get('fields', {})
                name = fields.get('Full Name', '') or fields.get('Name', '')
                print(f"{i}. {record['id']}: {name} - {list(fields.keys())}")
        
    except Exception as e:
        print(f"❌ Error checking Airtable: {e}")


if __name__ == '__main__':
    check_kyan_in_airtable()