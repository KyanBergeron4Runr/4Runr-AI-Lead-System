#!/usr/bin/env python3
"""
Main entry point for the Engager module.
Can be run with: python -m outreach.engager.main
"""

import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from outreach.engager.app import EngagerAgent


def main():
    """Main entry point for the Engager Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Engager Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - validate setup without sending emails')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - Testing engager setup")
        try:
            agent = EngagerAgent()
            stats = agent.get_processing_stats()
            print("✅ Engager initialized successfully")
            print(f"  Total leads ready: {stats['total_leads_ready']}")
            print(f"  Leads with Real emails: {stats['leads_with_real_emails']}")
            print(f"  Leads with Pattern emails: {stats['leads_with_pattern_emails']}")
            print(f"  Leads with Guess emails: {stats['leads_with_guess_emails']}")
            print(f"  Leads with messages: {stats['leads_with_messages']}")
            return True
        except Exception as e:
            print(f"❌ Engager setup failed: {e}")
            return False
    
    agent = EngagerAgent()
    
    if args.stats:
        stats = agent.get_processing_stats()
        print(f"Processing Statistics:")
        print(f"  Total leads ready: {stats['total_leads_ready']}")
        print(f"  Leads with Real emails: {stats['leads_with_real_emails']}")
        print(f"  Leads with Pattern emails: {stats['leads_with_pattern_emails']}")
        print(f"  Leads with Guess emails: {stats['leads_with_guess_emails']}")
        print(f"  Leads with messages: {stats['leads_with_messages']}")
        return True
    
    if args.lead_id:
        result = agent.process_specific_lead(args.lead_id)
        print(f"Result: {result}")
        return result == 'success'
    
    # Process leads in batch
    results = agent.process_leads(limit=args.limit)
    
    print(f"Engager Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)