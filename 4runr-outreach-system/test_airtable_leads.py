#!/usr/bin/env python3
"""
Test script to check available leads in Airtable
"""

from shared.airtable_client import get_airtable_client

def main():
    try:
        client = get_airtable_client()
        leads = client.get_leads_for_outreach(limit=10)
        
        print("Available leads in Airtable:")
        print("-" * 50)
        
        for lead in leads:
            print(f"ID: {lead.get('id')}")
            print(f"Name: {lead.get('Name')}")
            print(f"Email: {lead.get('Email')}")
            print(f"LinkedIn: {lead.get('LinkedIn_URL')}")
            print(f"Company: {lead.get('Company')}")
            print("-" * 30)
            
        if not leads:
            print("No leads found in Airtable")
            
    except Exception as e:
        print(f"Error accessing Airtable: {e}")

if __name__ == "__main__":
    main()