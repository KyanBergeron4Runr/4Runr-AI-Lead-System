#!/usr/bin/env python3
"""
Test database integration
"""

import sys
import asyncio
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "4runr-agents"))

from serve_campaign_brain import CampaignBrainService

async def test():
    service = CampaignBrainService()
    
    if service.lead_db:
        print("✅ Database connection established")
        
        # Test the method directly
        leads = service._get_leads_from_database(5)
        print(f"Database method returned {len(leads)} leads")
        
        for lead in leads:
            print(f"  - {lead.get('full_name')} (status: {lead.get('status')})")
    else:
        print("❌ No database connection")

if __name__ == '__main__':
    asyncio.run(test())