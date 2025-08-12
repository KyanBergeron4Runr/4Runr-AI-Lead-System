#!/usr/bin/env python3
"""
Main entry point for the Email Validator module.
Can be run with: python -m outreach.email_validator.main
"""

import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from outreach.email_validator.app import EmailValidatorAgent


def main():
    """Main entry point for the Email Validator Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Email Validator Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - validate setup without processing')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - Testing email validator setup")
        try:
            agent = EmailValidatorAgent()
            print("✅ Email validator initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Email validator setup failed: {e}")
            return False
    
    agent = EmailValidatorAgent()
    
    if args.stats:
        print("Email Validator Statistics:")
        print("  Module ready for processing")
        return True
    
    # Process leads in batch
    results = agent.process_leads(limit=args.limit)
    
    print(f"Email Validator Results:")
    print(f"  Processed: {results.get('processed', 0)}")
    print(f"  Successful: {results.get('successful', 0)}")
    print(f"  Errors: {results.get('errors', 0)}")
    
    return results.get('successful', 0) > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)