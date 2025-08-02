#!/usr/bin/env python3
"""
Campaign Delivery Service

Processes the message queue and sends campaign messages according to schedule.
This is the main delivery script that should be run periodically (e.g., via cron).
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Add campaign system to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import campaign system components
try:
    from campaign_system.executor.executor import CampaignExecutor
    from campaign_system.queue_manager.queue_manager import MessageQueueManager
    from campaign_system.database.schema import create_campaign_tables
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the campaign system is properly set up")
    sys.exit(1)


class CampaignDeliveryService:
    """Main service for processing campaign deliveries"""
    
    def __init__(self):
        self.executor = CampaignExecutor()
        self.queue_manager = MessageQueueManager()
    
    def run_delivery_cycle(self, batch_size: int = 10, dry_run: bool = False) -> dict:
        """
        Run a single delivery cycle
        
        Args:
            batch_size: Number of messages to process
            dry_run: If True, don't actually send messages
            
        Returns:
            Dictionary with cycle results
        """
        print(f"🚀 Starting delivery cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if dry_run:
            print("🧪 DRY RUN MODE - No messages will actually be sent")
        
        try:
            # Get queue statistics
            queue_stats = self.queue_manager.get_queue_stats()
            ready_count = queue_stats.get('ready_for_delivery', 0)
            
            print(f"📊 Queue Status:")
            print(f"  Ready for delivery: {ready_count}")
            print(f"  Total messages: {queue_stats.get('total_messages', 0)}")
            
            if queue_stats.get('by_status'):
                for status, count in queue_stats['by_status'].items():
                    print(f"  {status.title()}: {count}")
            
            if ready_count == 0:
                print("✅ No messages ready for delivery")
                return {'processed': 0, 'sent': 0, 'failed': 0, 'skipped': 0}
            
            # Process deliveries
            if not dry_run:
                delivery_stats = self.executor.process_delivery_queue(batch_size)
            else:
                # Simulate processing for dry run
                ready_messages = self.queue_manager.get_ready_messages(batch_size)
                delivery_stats = {
                    'processed': len(ready_messages),
                    'sent': len(ready_messages),  # Simulate all successful
                    'failed': 0,
                    'skipped': 0
                }
                
                print(f"🧪 DRY RUN: Would process {len(ready_messages)} messages")
                for msg in ready_messages[:3]:  # Show first 3
                    print(f"  📧 Campaign {msg.campaign_id}, Message {msg.message_number} to {msg.lead_email}")
                if len(ready_messages) > 3:
                    print(f"  ... and {len(ready_messages) - 3} more messages")
            
            # Report results
            print(f"\n📈 Delivery Results:")
            print(f"  Processed: {delivery_stats['processed']}")
            print(f"  Sent: {delivery_stats['sent']}")
            print(f"  Failed: {delivery_stats['failed']}")
            print(f"  Skipped: {delivery_stats['skipped']}")
            
            return delivery_stats
        
        except Exception as e:
            print(f"❌ Error in delivery cycle: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        try:
            # Get delivery stats
            delivery_stats = self.executor.get_delivery_stats()
            
            # Get queue stats
            queue_stats = self.queue_manager.get_queue_stats()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'delivery_stats': delivery_stats,
                'queue_stats': queue_stats,
                'system_healthy': True
            }
        
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'system_healthy': False
            }
    
    def cleanup_old_data(self, days_old: int = 30) -> dict:
        """Clean up old completed messages"""
        try:
            deleted_count = self.queue_manager.cleanup_old_messages(days_old)
            
            return {
                'deleted_messages': deleted_count,
                'cleanup_date': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def requeue_failed_messages(self, campaign_id: str = None) -> dict:
        """Requeue failed messages for retry"""
        try:
            requeued_count = self.queue_manager.requeue_failed_messages(campaign_id)
            
            return {
                'requeued_messages': requeued_count,
                'campaign_id': campaign_id,
                'requeue_date': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='4Runr Campaign Delivery Service')
    parser.add_argument('--batch-size', type=int, default=10, 
                       help='Number of messages to process per cycle')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate delivery without actually sending')
    parser.add_argument('--status', action='store_true',
                       help='Show system status and exit')
    parser.add_argument('--cleanup', type=int, metavar='DAYS',
                       help='Clean up messages older than DAYS days')
    parser.add_argument('--requeue', action='store_true',
                       help='Requeue failed messages for retry')
    parser.add_argument('--campaign-id', type=str,
                       help='Limit operations to specific campaign ID')
    parser.add_argument('--init-db', action='store_true',
                       help='Initialize database tables')
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        print("🗄️  Initializing database tables...")
        try:
            create_campaign_tables()
            print("✅ Database tables initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False
    
    # Create service instance
    try:
        service = CampaignDeliveryService()
    except Exception as e:
        print(f"❌ Failed to initialize delivery service: {e}")
        return False
    
    # Handle different operations
    if args.status:
        print("📊 System Status:")
        print("=" * 50)
        
        status = service.get_system_status()
        
        if status.get('system_healthy'):
            print("✅ System is healthy")
            
            # Show delivery stats
            delivery_stats = status.get('delivery_stats', {})
            if 'today_stats' in delivery_stats:
                today = delivery_stats['today_stats']
                print(f"\n📈 Today's Activity:")
                print(f"  Messages sent: {today.get('messages_sent_today', 0)}")
                print(f"  Responses received: {today.get('responses_today', 0)}")
            
            # Show queue stats
            queue_stats = status.get('queue_stats', {})
            if 'by_status' in queue_stats:
                print(f"\n📋 Queue Status:")
                for status_name, count in queue_stats['by_status'].items():
                    print(f"  {status_name.title()}: {count}")
                print(f"  Ready for delivery: {queue_stats.get('ready_for_delivery', 0)}")
        else:
            print("❌ System has issues")
            print(f"Error: {status.get('error', 'Unknown error')}")
        
        return status.get('system_healthy', False)
    
    elif args.cleanup:
        print(f"🧹 Cleaning up messages older than {args.cleanup} days...")
        result = service.cleanup_old_data(args.cleanup)
        
        if 'error' in result:
            print(f"❌ Cleanup failed: {result['error']}")
            return False
        else:
            print(f"✅ Cleaned up {result['deleted_messages']} old messages")
            return True
    
    elif args.requeue:
        print("🔄 Requeuing failed messages...")
        result = service.requeue_failed_messages(args.campaign_id)
        
        if 'error' in result:
            print(f"❌ Requeue failed: {result['error']}")
            return False
        else:
            print(f"✅ Requeued {result['requeued_messages']} failed messages")
            return True
    
    else:
        # Run delivery cycle
        result = service.run_delivery_cycle(args.batch_size, args.dry_run)
        
        if 'error' in result:
            print(f"❌ Delivery cycle failed: {result['error']}")
            return False
        else:
            success = result.get('sent', 0) > 0 or result.get('processed', 0) == 0
            return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)