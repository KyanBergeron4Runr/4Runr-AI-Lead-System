#!/usr/bin/env python3
"""
Check what fields are available in Airtable
"""

from shared.airtable_client import get_airtable_client

def main():
    try:
        client = get_airtable_client()
        
        # Get all records without filtering to see what fields exist
        records = client.table.all(max_records=3)
        
        # Convert generator to list to avoid subscriptable errors
        records_list = list(records)
        
        if records_list:
            print("Available fields in Airtable:")
            print("-" * 50)
            
            # Show fields from first record
            first_record = records_list[0]
            print(f"Record ID: {first_record['id']}")
            print("Fields:")
            for field_name, value in first_record['fields'].items():
                print(f"  {field_name}: {value}")
                
            print(f"\nTotal records found: {len(records)}")
        else:
            print("No records found in Airtable")
            
    except Exception as e:
        print(f"Error accessing Airtable: {e}")

if __name__ == "__main__":
    main()