#!/usr/bin/env python3
"""
Test the LinkedIn Enricher Agent
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from outreach.linkedin_enricher.app import LinkedInEnricherAgent


async def main():
    """Test the LinkedIn enricher."""
    print("🔗 Testing LinkedIn Enricher Agent")
    print("=" * 50)
    
    try:
        agent = LinkedInEnricherAgent()
        
        # Get stats first
        leads = agent._get_leads_needing_website_extraction(10)
        print(f"📊 Found {len(leads)} leads needing website extraction")
        
        if leads:
            print("\n📋 Sample leads:")
            for i, lead in enumerate(leads[:3]):  # Show first 3
                print(f"  {i+1}. {lead.get('Company', 'Unknown')} - {lead.get('LinkedIn URL', 'No URL')}")
        
        # Test processing
        print(f"\n🚀 Processing up to 3 leads...")
        results = await agent.process_leads(limit=3)
        
        print(f"\n✅ Results:")
        print(f"  Processed: {results['processed']}")
        print(f"  Successful: {results['successful']}")
        print(f"  Errors: {results['errors']}")
        
        return results['successful'] > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    print(f"\n{'✅ Success!' if success else '❌ Failed!'}")