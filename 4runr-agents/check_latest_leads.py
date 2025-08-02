#!/usr/bin/env python3
import json
import os

# Check all possible lead files
files_to_check = ['/shared/leads.json', 'shared/leads.json', 'shared/scraped_leads.json']

for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f'Found: {file_path}')
        with open(file_path, 'r') as f:
            leads = json.load(f)
        print(f'  Total leads: {len(leads)}')
        if leads:
            last_lead = leads[-1]
            print(f'  Last lead: {last_lead["name"]} at {last_lead["company"]}')
            print(f'  LinkedIn URL: {last_lead.get("linkedin_url", "N/A")}')
            print(f'  Location: {last_lead.get("location", "N/A")}')
            print(f'  Note: {last_lead.get("note", "N/A")}')
            print(f'  Verified: {last_lead.get("verified", "N/A")}')
        print()