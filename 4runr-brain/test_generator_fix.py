#!/usr/bin/env python3
"""
Test script to isolate the generator issue
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

from serve_campaign_brain import CampaignBrainService

async def test_generator_issue():
    """Test the specific generator issue"""
    
    print("DEBUG: Starting test")
    
    try:
        # Initialize service
        print("DEBUG: Initializing service")
        service = CampaignBrainService()
        print("DEBUG: Service initialized")
        
        # Test the method that's causing issues
        print("DEBUG: Testing _get_leads_from_directory")
        leads = service._get_leads_from_directory(10)
        print(f"DEBUG: Got {len(leads)} leads")
        
        # Test process_batch
        print("DEBUG: Testing process_batch")
        result = await service.process_batch(1, dry_run=True)
        print(f"DEBUG: process_batch result: {result}")
        
    except Exception as e:
        print(f"DEBUG: Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generator_issue())