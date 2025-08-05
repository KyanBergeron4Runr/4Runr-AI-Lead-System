#!/usr/bin/env python3
import json

with open('/shared/leads.json', 'r') as f:
    leads = json.load(f)

print('Sample lead status check:')
if leads:
    lead = leads[-1]
    print(f'Name: {lead["name"]}')
    print(f'Status: {lead.get("status", "NOT SET")}')
    print(f'needs_enrichment: {lead.get("needs_enrichment", "NOT SET")}')
    print(f'All fields: {list(lead.keys())}')
    print()
    print('Full lead data:')
    for key, value in lead.items():
        print(f'  {key}: {value}')