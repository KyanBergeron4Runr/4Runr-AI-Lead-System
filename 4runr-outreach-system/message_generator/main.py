#!/usr/bin/env python3
"""
Main entry point for the Message Generator module.
Can be run with: python -m outreach.message_generator.main
"""

import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from outreach.message_generator.app import MessageGeneratorAgent


def main():
    """Main entry point for the Message Generator Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Message Generator Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - validate setup without processing')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - Testing message generator setup")
        try:
            agent = MessageGeneratorAgent()
            stats = agent.get_processing_stats()
            print("✅ Message generator initialized successfully")
            print(f"  Total leads ready: {stats['total_leads_ready']}")
            print(f"  Leads with company data: {stats['leads_with_company_data']}")
            print(f"  Leads without company data: {stats['leads_without_company_data']}")
            return True
        except Exception as e:
            print(f"❌ Message generator setup failed: {e}")
            return False
    
    agent = MessageGeneratorAgent()
    
    if args.stats:
        stats = agent.get_processing_stats()
        print(f"Processing Statistics:")
        print(f"  Total leads ready: {stats['total_leads_ready']}")
        print(f"  Leads with company data: {stats['leads_with_company_data']}")
        print(f"  Leads without company data: {stats['leads_without_company_data']}")
        return True
    
    if args.lead_id:
        success = agent.process_specific_lead(args.lead_id)
        return success
    
    # Process leads in batch
    results = agent.process_leads(limit=args.limit)
    
    print(f"Message Generator Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)