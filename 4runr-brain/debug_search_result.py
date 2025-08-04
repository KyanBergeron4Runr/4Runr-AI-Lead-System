#!/usr/bin/env python3
"""
Debug search result
"""

import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent / "4runr-agents"))

from database.lead_database import get_lead_database

def main():
    # Use the database from the 4runr-agents directory
    db_path = str(Path(__file__).parent.parent / "4runr-agents" / "data" / "leads.db")
    db = get_lead_database(db_path)
    
    print(f"Database path: {db_path}")
    
    # Test the search
    leads = db.search_leads({'status': 'Ready for Outreach'})
    print(f"Search returned {len(leads)} leads")
    
    for i, lead in enumerate(leads):
        print(f"Lead {i}: {type(lead)} - {lead}")
        if lead:
            print(f"  full_name: {lead.get('full_name')}")
            print(f"  status: {lead.get('status')}")
            print(f"  raw_data: {type(lead.get('raw_data'))}")

if __name__ == '__main__':
    main()