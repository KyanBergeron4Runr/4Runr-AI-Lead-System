#!/usr/bin/env python3
"""
Test the Google Enricher Agent
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from outreach.google_enricher.app import GoogleEnricherAgent


async def main():
    """Test the Google enricher."""
    print("🔍 Testing Google Enricher Agent")
    print("=" * 50)
    
    try:
        agent = GoogleEnricherAgent()
        
        # Get stats first
        leads = agent._get_leads_needing_enrichment(10)
        print(f"📊 Found {len(leads)} leads needing enrichment")
        
        if leads:
            print("\n📋 Sample leads:")
            for i, lead in enumerate(leads[:3]):  # Show first 3
                name = lead.get('Full Name', 'Unknown')
                company = lead.get('Company', 'Missing')
                website = lead.get('Website', 'Missing')
                print(f"  {i+1}. {name}")
                print(f"     Company: {company}")
                print(f"     Website: {website}")
        
        # Test processing
        print(f"\n🚀 Processing up to 2 leads...")
        results = await agent.process_leads(limit=2)
        
        print(f"\n✅ Results:")
        print(f"  Processed: {results['processed']}")
        print(f"  Successful: {results['successful']}")
        print(f"  Errors: {results['errors']}")
        
        return results['successful'] > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    print(f"\n{'✅ Success!' if success else '❌ Failed!'}")