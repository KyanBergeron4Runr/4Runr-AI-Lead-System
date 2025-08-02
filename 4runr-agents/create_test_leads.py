#!/usr/bin/env python3
"""
Create Test Leads

Create some fresh test leads to demonstrate the full production pipeline
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

# Create fresh test leads that won't be duplicates
test_leads = [
    {
        "uuid": str(uuid.uuid4()),
        "name": "Marie-Claire Dubois",
        "full_name": "Marie-Claire Dubois", 
        "title": "CEO & Founder",
        "company": "TechNova Solutions",
        "location": "Montreal, Quebec, Canada",
        "linkedin_url": "https://www.linkedin.com/in/marie-claire-dubois-technova/",
        "email": None,
        "verified": True,
        "enriched": False,
        "scraped_at": datetime.now().isoformat(),
        "source": "Test Montreal CEOs",
        "needs_enrichment": True,
        "status": "scraped"
    },
    {
        "uuid": str(uuid.uuid4()),
        "name": "Jean-François Tremblay",
        "full_name": "Jean-François Tremblay",
        "title": "President & Co-Founder", 
        "company": "InnovateMTL Inc.",
        "location": "Montreal, Quebec, Canada",
        "linkedin_url": "https://www.linkedin.com/in/jf-tremblay-innovatemtl/",
        "email": None,
        "verified": True,
        "enriched": False,
        "scraped_at": datetime.now().isoformat(),
        "source": "Test Montreal CEOs",
        "needs_enrichment": True,
        "status": "scraped"
    },
    {
        "uuid": str(uuid.uuid4()),
        "name": "Sophie Bergeron",
        "full_name": "Sophie Bergeron",
        "title": "Managing Director",
        "company": "Montreal Digital Ventures",
        "location": "Montreal, Quebec, Canada", 
        "linkedin_url": "https://www.linkedin.com/in/sophie-bergeron-mdv/",
        "email": None,
        "verified": True,
        "enriched": False,
        "scraped_at": datetime.now().isoformat(),
        "source": "Test Montreal CEOs",
        "needs_enrichment": True,
        "status": "scraped"
    }
]

# Save test leads
shared_dir = Path(__file__).parent / 'shared'
test_leads_file = shared_dir / 'test_leads.json'

with open(test_leads_file, 'w', encoding='utf-8') as f:
    json.dump(test_leads, f, indent=2, ensure_ascii=False)

print(f"✅ Created {len(test_leads)} test leads:")
for i, lead in enumerate(test_leads, 1):
    print(f"   {i}. {lead['name']} - {lead['title']} at {lead['company']}")

print(f"\n💾 Saved to: {test_leads_file}")