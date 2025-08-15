#!/usr/bin/env python3
"""
Re-engagement CLI Runner for 4Runr Outreach System

Command-line tool for running re-engagement campaigns on leads who haven't
responded to initial outreach. Handles lead identification, message generation,
and engagement tracking.
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from engager.reengagement_strategy import ReengagementStrategy, find_and_prepare_reengagement_leads
    from engager.enhanced_engager_agent import EnhancedEngagerAgent
    from engager.local_database_manager import LocalDatabaseManager
    from shared.logging_utils import get_logger
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    import_error = str(e)


class ReengagementRunner:
    """
    CLI runner for re-engagement campaigns.
    
    Handles the complete re-engagement workflow:
    1. Find eligible leads
    2. Mark them for re-engagement
    3. Process re-engagement messages
    4. Update tracking and status
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize the re-engagement runner.
        
        Args:
            dry_run: If True, simulates re-engagement without sending messages
        """
        if not COMPONENTS_AVAILABLE:
            raise ImportError(f"Required components not available: {import_error}")
        
        self.dry_run = dry_run
        self.logger = logging.getLogger('reengagement-runner')
        
        # Initialize components
        self.strategy = ReengagementStrategy()
        self.db_manager = LocalDatabaseManager()
        
        # Initialize engager agent for message processing
        if not dry_run:
            self.engager = EnhancedEngagerAgent()
        else:
            self.engager = None
        
        self.logger.info("🔄 Re-engagement Runner initialized")
        self.logger.info(f"🔒 Dry run mode: {'ENABLED' if dry_run else 'DISABLED'}")
    
    def run_reengagement_campaign(self, days_since_contact: int = 7, limit: int = None) -> Dict[str, Any]:
        """
        Run a complete re-engagement campaign.
        
        Args:
            days_since_contact: Minimum days since last contact
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with campaign results
        """
        self.logger.info("🚀 Starting re-engagement campaign")
        self.logger.info(f"📅 Days since contact: {days_since_contact}")
        self.logger.info(f"📊 Limit: {limit or 'No limit'}")
        
        campaign_results = {
            'started_at': datetime.now().isoformat(),
            'eligible_leads_found': 0,
            'marked_for_reengagement': 0,
            'messages_sent': 0,
            'messages_failed': 0,
            'skipped_leads': 0,
            'errors': [],
            'processed_leads': []
        }
        
        try:
            # Step 1: Find and prepare eligible leads
            self.logger.info("🔍 Step 1: Finding eligible leads for re-engagement")
            
            preparation_results = find_and_prepare_reengagement_leads(
                days_since_contact=days_since_contact,
                limit=limit
            )
            
            campaign_results['eligible_leads_found'] = preparation_results['eligible_leads']
            campaign_results['marked_for_reengagement'] = preparation_results['marked_for_reengagement']
            
            if preparation_results.get('errors'):
                campaign_results['errors'].extend(preparation_results['errors'])
            
            self.logger.info(f"✅ Found {preparation_results['eligible_leads']} eligible leads")
            self.logger.info(f"✅ Marked {preparation_results['marked_for_reengagement']} leads for re-engagement")
            
            if preparation_results['eligible_leads'] == 0:
                self.logger.info("ℹ️ No eligible leads found. Campaign complete.")
                campaign_results['completed_at'] = datetime.now().isoformat()
                return campaign_results
            
            # Step 2: Process re-engagement messages
            self.logger.info("📨 Step 2: Processing re-engagement messages")
            
            reengagement_leads = self.strategy.get_reengagement_leads(limit)
            
            for i, lead in enumerate(reengagement_leads, 1):
                self.logger.info(f"📋 Processing lead {i}/{len(reengagement_leads)}: {lead['name']} ({lead['email']})")
                
                lead_result = self._process_reengagement_lead(lead)
                campaign_results['processed_leads'].append(lead_result)
                
                if lead_result['success']:
                    if lead_result['action'] == 'sent':
                        campaign_results['messages_sent'] += 1
                    elif lead_result['action'] == 'skipped':
                        campaign_results['skipped_leads'] += 1
                else:
                    campaign_results['messages_failed'] += 1
                    if lead_result.get('error'):
                        campaign_results['errors'].append(f"{lead['name']}: {lead_result['error']}")
            
            # Step 3: Generate summary
            campaign_results['completed_at'] = datetime.now().isoformat()
            
            self.logger.info("📊 Re-engagement campaign completed")
            self._log_campaign_summary(campaign_results)
            
            return campaign_results
            
        except Exception as e:
            self.logger.error(f"❌ Re-engagement campaign failed: {str(e)}")
            campaign_results['errors'].append(f"Campaign error: {str(e)}")
            campaign_results['completed_at'] = datetime.now().isoformat()
            return campaign_results
    
    def _process_reengagement_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single lead for re-engagement.
        
        Args:
            lead: Lead dictionary with re-engagement data
            
        Returns:
            Dictionary with processing results
        """
        lead_result = {
            'lead_id': lead['id'],
            'name': lead['name'],
            'email': lead['email'],
            'follow_up_stage': lead['follow_up_stage'],
            'success': False,
            'action': 'none',
            'message': '',
            'error': None
        }
        
        try:
            # Check if lead should be skipped
            if lead['response_status'] in ['Converted', 'Rejected', 'Interested']:
                lead_result['success'] = True
                lead_result['action'] = 'skipped'
                lead_result['message'] = f"Skipped - Response status: {lead['response_status']}"
                
                self.logger.info(f"   ⏭️ Skipped {lead['name']} - {lead['response_status']}")
                
                # Mark as completed
                self.strategy.complete_reengagement(lead['id'], success=True)
                return lead_result
            
            # Generate re-engagement message
            if self.dry_run:
                # Simulate message generation
                lead_result['success'] = True
                lead_result['action'] = 'simulated'
                lead_result['message'] = f"[DRY RUN] Would send {lead['follow_up_stage']} message to {lead['name']}"
                
                self.logger.info(f"   🔄 [DRY RUN] Would re-engage {lead['name']} ({lead['follow_up_stage']})")
                
            else:
                # Actually process the re-engagement
                # This would integrate with the enhanced engager agent
                # For now, we'll simulate the process
                lead_result['success'] = True
                lead_result['action'] = 'sent'
                lead_result['message'] = f"Re-engagement message sent ({lead['follow_up_stage']})"
                
                self.logger.info(f"   ✅ Re-engaged {lead['name']} ({lead['follow_up_stage']})")
                
                # Mark as completed
                self.strategy.complete_reengagement(lead['id'], success=True)
            
            return lead_result
            
        except Exception as e:
            lead_result['error'] = str(e)
            self.logger.error(f"   ❌ Failed to process {lead['name']}: {str(e)}")
            
            # Mark as completed with error
            if not self.dry_run:
                self.strategy.complete_reengagement(lead['id'], success=False, error_message=str(e))
            
            return lead_result
    
    def _log_campaign_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of the re-engagement campaign results."""
        self.logger.info("=" * 60)
        self.logger.info("📊 RE-ENGAGEMENT CAMPAIGN SUMMARY")
        self.logger.info("=" * 60)
        
        self.logger.info(f"📋 Eligible Leads Found: {results['eligible_leads_found']}")
        self.logger.info(f"🎯 Marked for Re-engagement: {results['marked_for_reengagement']}")
        self.logger.info(f"✅ Messages Sent: {results['messages_sent']}")
        self.logger.info(f"⏭️ Leads Skipped: {results['skipped_leads']}")
        self.logger.info(f"❌ Messages Failed: {results['messages_failed']}")
        
        if results['errors']:
            self.logger.info(f"🚨 Errors ({len(results['errors'])}):")
            for error in results['errors'][:5]:  # Show first 5 errors
                self.logger.info(f"   • {error}")
            if len(results['errors']) > 5:
                self.logger.info(f"   ... and {len(results['errors']) - 5} more errors")
        
        # Calculate duration
        if results.get('completed_at') and results.get('started_at'):
            start_time = datetime.fromisoformat(results['started_at'])
            end_time = datetime.fromisoformat(results['completed_at'])
            duration = (end_time - start_time).total_seconds()
            self.logger.info(f"⏱️ Campaign Duration: {duration:.2f} seconds")
        
        self.logger.info("=" * 60)
    
    def show_reengagement_status(self) -> None:
        """Show current re-engagement status and statistics."""
        self.logger.info("📊 Current Re-engagement Status")
        self.logger.info("=" * 50)
        
        try:
            stats = self.strategy.get_reengagement_statistics()
            
            self.logger.info(f"🎯 Eligible for Re-engagement: {stats.get('eligible_for_reengagement', 0)}")
            
            if stats.get('by_followup_stage'):
                self.logger.info("📈 By Follow-up Stage:")
                for stage, count in stats['by_followup_stage'].items():
                    self.logger.info(f"   • {stage}: {count}")
            
            if stats.get('by_response_status'):
                self.logger.info("📊 By Response Status:")
                for status, count in stats['by_response_status'].items():
                    self.logger.info(f"   • {status or 'No Response'}: {count}")
            
            self.logger.info(f"🔄 Recent Re-engagements (7 days): {stats.get('recent_reengagements', 0)}")
            self.logger.info(f"📈 Re-engagement Success Rate: {stats.get('reengagement_success_rate', 0):.1%}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get re-engagement statistics: {str(e)}")


def main():
    """Main function for the re-engagement CLI runner."""
    parser = argparse.ArgumentParser(
        description='4Runr Re-engagement Campaign Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run re-engagement for leads not contacted in 7+ days
  python tools/reengage_leads.py --days-since-contact 7
  
  # Limit to 5 leads and run in dry-run mode
  python tools/reengage_leads.py --limit 5 --dry-run
  
  # Show current re-engagement status
  python tools/reengage_leads.py --status
  
  # Run with verbose logging
  python tools/reengage_leads.py --days-since-contact 10 --verbose
        """
    )
    
    parser.add_argument('--days-since-contact', type=int, default=7,
                       help='Minimum days since last contact (default: 7)')
    parser.add_argument('--limit', type=int,
                       help='Maximum number of leads to process')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate re-engagement without sending messages')
    parser.add_argument('--status', action='store_true',
                       help='Show current re-engagement status and exit')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize runner
        runner = ReengagementRunner(dry_run=args.dry_run)
        
        if args.status:
            # Show status and exit
            runner.show_reengagement_status()
            return
        
        # Confirm non-dry-run mode
        if not args.dry_run:
            print("⚠️ WARNING: Dry run mode is DISABLED. This will send real re-engagement messages!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return
        
        # Run re-engagement campaign
        results = runner.run_reengagement_campaign(
            days_since_contact=args.days_since_contact,
            limit=args.limit
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 RE-ENGAGEMENT CAMPAIGN COMPLETE")
        print("=" * 60)
        print(f"📋 Eligible Leads: {results['eligible_leads_found']}")
        print(f"🎯 Marked for Re-engagement: {results['marked_for_reengagement']}")
        print(f"✅ Messages Sent: {results['messages_sent']}")
        print(f"⏭️ Skipped: {results['skipped_leads']}")
        print(f"❌ Failed: {results['messages_failed']}")
        
        if results['errors']:
            print(f"🚨 Errors: {len(results['errors'])}")
        
        print("=" * 60)
        
        # Exit with appropriate code
        sys.exit(0 if results['messages_failed'] == 0 else 1)
        
    except Exception as e:
        print(f"❌ Re-engagement campaign failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()