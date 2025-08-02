#!/usr/bin/env python3
import json

# Try different possible file locations
import os
possible_files = ['shared/leads.json', 'shared/scraped_leads.json', '/shared/leads.json']
leads_file = None

for file_path in possible_files:
    if os.path.exists(file_path):
        leads_file = file_path
        break

if not leads_file:
    print("No leads file found. Available files in shared/:")
    for f in os.listdir('shared/'):
        print(f"  {f}")
    exit(1)

print(f"Reading from: {leads_file}")
with open(leads_file, 'r') as f:
    leads = json.load(f)

print(f'Total leads: {len(leads)}')
print('\nLast 5 leads added:')
for lead in leads[-5:]:
    print(f'- {lead["name"]} ({lead["title"]}) at {lead["company"]}')
    print(f'  LinkedIn: {lead["linkedin_url"]}')
    print(f'  Location: {lead.get("location", "N/A")}')
    print(f'  Verified: {lead.get("Verified", "N/A")}')
    print(f'  Source: {lead.get("Source", "N/A")}')
    print()