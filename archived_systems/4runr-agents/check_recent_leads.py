#!/usr/bin/env python3
import json

with open('/shared/leads.json', 'r') as f:
    leads = json.load(f)

print(f'Total leads: {len(leads)}')
print('\nLast 10 leads added:')
for lead in leads[-10:]:
    linkedin_status = "✅ REAL" if lead.get("linkedin_url") and "tobi" in lead.get("linkedin_url", "") or "daxdasilva" in lead.get("linkedin_url", "") else ("❌ BLANK" if not lead.get("linkedin_url") else "❓ UNKNOWN")
    
    print(f'- {lead["name"]} ({lead["title"]}) at {lead["company"]}')
    print(f'  LinkedIn: {lead.get("linkedin_url", "BLANK")} {linkedin_status}')
    print(f'  Location: {lead.get("location", "N/A")}')
    print(f'  Verified: {lead.get("verified", "N/A")}')
    print()