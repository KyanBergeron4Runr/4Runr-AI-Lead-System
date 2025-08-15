#!/usr/bin/env python3
"""
Check Airtable Field Names

This script connects to Airtable and lists all the actual field names
to help identify the correct field names for the filterByFormula.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from shared.airtable_client import get_airtable_client
from shared.config import config

def main():
    """Check the actual field names in Airtable."""
    print("🔍 Checking Airtable Field Names")
    print("=" * 35)
    
    try:
        # Get Airtable client
        airtable_client = get_airtable_client()
        
        print(f"Connected to Airtable base: {config.get_airtable_config()['base_id']}")
        print(f"Table: {config.get_airtable_config()['table_name']}")
        print()
        
        # Get a few records to see the field names
        print("📋 Fetching sample records to identify field names...")
        records = list(airtable_client.table.all(max_records=10))
        
        if not records:
            print("❌ No records found in the table")
            return False
        
        # Extract all field names from the records
        all_fields = set()
        for record in records:
            all_fields.update(record['fields'].keys())
        
        print(f"\n📊 Found {len(all_fields)} unique field names:")
        print("-" * 50)
        
        # Sort and display field names
        sorted_fields = sorted(all_fields)
        for i, field_name in enumerate(sorted_fields, 1):
            print(f"{i:2d}. {field_name}")
        
        print("\n🔍 Looking for engagement-related fields:")
        print("-" * 50)
        
        # Look for fields that might be related to our query
        engagement_fields = []
        search_terms = ['engagement', 'email', 'confidence', 'level', 'engaged', 'status']
        
        for field in sorted_fields:
            field_lower = field.lower()
            if any(term in field_lower for term in search_terms):
                engagement_fields.append(field)
        
        if engagement_fields:
            for field in engagement_fields:
                print(f"  ✅ {field}")
        else:
            print("  ⚠️  No engagement-related fields found")
        
        print(f"\n🎯 Fields we're looking for in our query:")
        expected_fields = ['Engagement_Status', 'Email_Confidence_Level', 'Level Engaged']
        
        for expected in expected_fields:
            if expected in all_fields:
                print(f"  ✅ {expected} - FOUND")
            else:
                print(f"  ❌ {expected} - NOT FOUND")
                
                # Look for similar field names
                similar = [f for f in all_fields if expected.lower().replace('_', '').replace(' ', '') in f.lower().replace('_', '').replace(' ', '')]
                if similar:
                    print(f"     Similar fields: {', '.join(similar)}")
        
        print(f"\n💡 Suggested fixes:")
        print("If any expected fields are missing, you may need to:")
        print("1. Create the missing fields in Airtable")
        print("2. Update the field names in the code to match Airtable")
        print("3. Check field name spelling and capitalization")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Airtable fields: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)