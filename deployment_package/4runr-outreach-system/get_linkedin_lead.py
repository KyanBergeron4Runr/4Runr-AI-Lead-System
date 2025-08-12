#!/usr/bin/env python3
"""
Get a lead with LinkedIn URL for testing
"""

from shared.airtable_client import get_airtable_client

def main():
    try:
        client = get_airtable_client()
        
        # Get records with LinkedIn URL
        records = client.table.all(max_records=10)
        
        # Convert generator to list to avoid subscriptable errors
        records_list = list(records)
        
        print("Looking for leads with LinkedIn URLs:")
        print("-" * 50)
        
        for record in records_list:
            fields = record['fields']
            linkedin_url = fields.get('LinkedIn URL')
            email = fields.get('Email')
            full_name = fields.get('Full Name')
            
            if linkedin_url and not email:
                print(f"✅ Found LinkedIn-only lead:")
                print(f"ID: {record['id']}")
                print(f"Name: {full_name}")
                print(f"LinkedIn: {linkedin_url}")
                print(f"Email: {email}")
                print(f"All fields: {list(fields.keys())}")
                
                # Create a test lead file for the campaign brain
                lead_data = {
                    "id": record['id'],
                    "Name": full_name,
                    "LinkedIn_URL": linkedin_url,
                    "Company": "Unknown Company",  # We'll need to add this
                    "company_data": {
                        "description": "Professional services company",
                        "services": "Business consulting and professional services",
                        "tone": "Professional"
                    },
                    "scraped_content": {
                        "homepage_text": "Professional services and business consulting",
                        "about_page": "Established professional services firm"
                    }
                }
                
                import json
                with open('../4runr-brain/real_linkedin_lead.json', 'w') as f:
                    json.dump(lead_data, f, indent=2)
                
                print(f"\n✅ Created test file: real_linkedin_lead.json")
                return record['id']
                
        print("No leads found with LinkedIn URL but no email")
        return None
            
    except Exception as e:
        print(f"Error accessing Airtable: {e}")
        return None

if __name__ == "__main__":
    main()