#!/usr/bin/env python3
"""
Add LinkedIn messaging fields to Airtable
"""

from shared.airtable_client import get_airtable_client

def main():
    try:
        client = get_airtable_client()
        
        # Get the first record to test field updates
        records = client.table.all(max_records=1)
        
        if records:
            record_id = records[0]['id']
            print(f"Testing field update on record: {record_id}")
            
            # Try to add the LinkedIn fields
            test_data = {
                'AI Message': 'Test LinkedIn campaign content',
                'Messaging Method': 'Manual LinkedIn',
                'Manual Message Sent': False
            }
            
            print("Attempting to add LinkedIn fields...")
            success = client.update_lead_fields(record_id, test_data)
            
            if success:
                print("✅ Successfully added LinkedIn fields to Airtable!")
                
                # Verify the update
                updated_record = client.table.get(record_id)
                print("Updated fields:")
                for field, value in updated_record['fields'].items():
                    if field in test_data:
                        print(f"  {field}: {value}")
            else:
                print("❌ Failed to add LinkedIn fields")
                
        else:
            print("No records found to test with")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nThis is expected if the fields don't exist in Airtable yet.")
        print("You need to manually add these fields to your Airtable:")
        print("1. AI Message (Long text field)")
        print("2. Messaging Method (Single select: Email, Manual LinkedIn)")
        print("3. Manual Message Sent (Checkbox)")

if __name__ == "__main__":
    main()