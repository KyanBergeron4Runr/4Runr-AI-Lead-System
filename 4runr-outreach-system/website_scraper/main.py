#!/usr/bin/env python3
"""
Main entry point for the Website Scraper module.
Can be run with: python -m outreach.website_scraper.main
"""

import asyncio
import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from outreach.website_scraper.app import WebsiteScraperAgent


async def main():
    """Main entry point for the Website Scraper Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Website Scraper Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - validate setup without processing')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - Testing website scraper setup")
        try:
            agent = WebsiteScraperAgent()
            stats = agent.get_processing_stats()
            print("✅ Website scraper initialized successfully")
            print(f"  Total leads ready: {stats['total_leads_ready']}")
            print(f"  Leads with websites: {stats['leads_with_websites']}")
            print(f"  Leads without websites: {stats['leads_without_websites']}")
            return True
        except Exception as e:
            print(f"❌ Website scraper setup failed: {e}")
            return False
    
    agent = WebsiteScraperAgent()
    
    if args.stats:
        stats = agent.get_processing_stats()
        print(f"Processing Statistics:")
        print(f"  Total leads ready: {stats['total_leads_ready']}")
        print(f"  Leads with websites: {stats['leads_with_websites']}")
        print(f"  Leads without websites: {stats['leads_without_websites']}")
        return True
    
    if args.lead_id:
        success = await agent.process_specific_lead(args.lead_id)
        return success
    
    # Process leads in batch
    results = await agent.process_leads(limit=args.limit)
    
    print(f"Website Scraper Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)