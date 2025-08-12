#!/usr/bin/env python3
"""
Sync Service Startup Script

Starts the automatic sync service that provides:
- Immediate sync to Airtable when leads are created/updated
- Daily sync from Airtable to get external updates
"""

import os
import sys
import signal
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.sync_scheduler import get_sync_scheduler, start_sync_scheduler, stop_sync_scheduler
from utils.logging import get_logger
from config.settings import get_settings

class SyncService:
    """
    Sync service manager for automatic Airtable synchronization.
    """
    
    def __init__(self):
        """Initialize the sync service."""
        self.logger = get_logger('sync-service')
        self.settings = get_settings()
        self.scheduler = get_sync_scheduler()
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🔄 Sync Service initialized")
    
    def start(self):
        """Start the sync service."""
        try:
            self.logger.info("🚀 Starting 4Runr Lead Sync Service")
            self.logger.info(f"📅 Daily sync time: {self.settings.sync.get('daily_sync_time', '06:00')}")
            self.logger.info(f"⚡ Immediate sync: {'Enabled' if self.settings.sync.get('immediate_sync_enabled', True) else 'Disabled'}")
            
            # Start the sync scheduler
            start_sync_scheduler()
            self.running = True
            
            self.logger.info("✅ Sync Service started successfully")
            self.logger.info("📊 Service Status:")
            
            # Display initial status
            status = self.scheduler.get_sync_status()
            self.logger.info(f"   📋 Pending leads: {status.get('scheduler', {}).get('pending_leads_count', 0)}")
            self.logger.info(f"   📤 Last sync to Airtable: {status.get('scheduler', {}).get('last_sync_to_airtable', 'Never')}")
            self.logger.info(f"   📥 Last sync from Airtable: {status.get('scheduler', {}).get('last_sync_from_airtable', 'Never')}")
            
            # Run initial sync of pending leads
            self.logger.info("🔄 Running initial sync of pending leads...")
            result = self.scheduler.sync_all_pending_to_airtable()
            if result['success'] and result['synced_count'] > 0:
                self.logger.info(f"✅ Initial sync completed: {result['synced_count']} leads synced")
            elif result['synced_count'] == 0:
                self.logger.info("✅ No pending leads to sync")
            else:
                self.logger.warning(f"⚠️ Initial sync had issues: {result.get('errors', [])}")
            
            # Keep the service running
            self._run_service_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start sync service: {str(e)}")
            raise
    
    def stop(self):
        """Stop the sync service."""
        if not self.running:
            return
        
        self.logger.info("🛑 Stopping Sync Service...")
        self.running = False
        
        try:
            # Stop the sync scheduler
            stop_sync_scheduler()
            self.logger.info("✅ Sync Service stopped successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping sync service: {str(e)}")
    
    def status(self):
        """Display sync service status."""
        try:
            status = self.scheduler.get_sync_status()
            
            print("📊 4Runr Lead Sync Service Status")
            print("=" * 40)
            
            # Scheduler status
            scheduler_info = status.get('scheduler', {})
            print(f"🔄 Scheduler Running: {'✅ Yes' if scheduler_info.get('scheduler_running') else '❌ No'}")
            print(f"⚡ Immediate Sync: {'✅ Enabled' if scheduler_info.get('immediate_sync_enabled') else '❌ Disabled'}")
            print(f"📅 Daily Sync Time: {scheduler_info.get('daily_sync_time', 'Not set')}")
            print(f"📋 Pending Leads: {scheduler_info.get('pending_leads_count', 0)}")
            
            # Last sync times
            last_to_airtable = scheduler_info.get('last_sync_to_airtable')
            last_from_airtable = scheduler_info.get('last_sync_from_airtable')
            
            print(f"📤 Last Sync to Airtable: {self._format_timestamp(last_to_airtable)}")
            print(f"📥 Last Sync from Airtable: {self._format_timestamp(last_from_airtable)}")
            
            # Next scheduled sync
            next_sync = scheduler_info.get('next_daily_sync')
            if next_sync:
                print(f"⏰ Next Daily Sync: {self._format_timestamp(next_sync)}")
            
            # Sync statistics
            sync_stats = status.get('sync_statistics', {})
            if sync_stats:
                print("\n📈 Recent Sync Statistics (Last 7 days):")
                for operation, stats in sync_stats.items():
                    for status_type, info in stats.items():
                        print(f"   {operation} ({status_type}): {info['count']} times")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to get sync status: {str(e)}")
            return False
    
    def test_sync(self):
        """Test sync operations."""
        print("🧪 Testing Sync Operations")
        print("=" * 30)
        
        try:
            # Test sync to Airtable
            print("1. Testing sync to Airtable...")
            result = self.scheduler.sync_all_pending_to_airtable()
            if result['success']:
                print(f"   ✅ Success: {result['synced_count']} leads synced")
            else:
                print(f"   ❌ Failed: {result.get('errors', [])}")
            
            # Test sync from Airtable
            print("2. Testing sync from Airtable...")
            result = self.scheduler.sync_from_airtable_now()
            if result['success']:
                print(f"   ✅ Success: {result['synced_count']} updates received")
            else:
                print(f"   ❌ Failed: {result.get('errors', [])}")
            
            print("✅ Sync tests completed")
            return True
            
        except Exception as e:
            print(f"❌ Sync test failed: {str(e)}")
            return False
    
    def _run_service_loop(self):
        """Run the main service loop."""
        self.logger.info("🔄 Sync Service is running. Press Ctrl+C to stop.")
        
        # Status reporting interval (every 10 minutes)
        last_status_report = 0
        status_interval = 600  # 10 minutes
        
        try:
            while self.running:
                current_time = time.time()
                
                # Periodic status reporting
                if current_time - last_status_report > status_interval:
                    self._report_status()
                    last_status_report = current_time
                
                # Sleep for a short interval
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.logger.info("⚠️ Received interrupt signal")
        except Exception as e:
            self.logger.error(f"❌ Service loop error: {str(e)}")
        
        finally:
            self.stop()
    
    def _report_status(self):
        """Report periodic status."""
        try:
            status = self.scheduler.get_sync_status()
            scheduler_info = status.get('scheduler', {})
            
            pending_count = scheduler_info.get('pending_leads_count', 0)
            if pending_count > 0:
                self.logger.info(f"📋 Status: {pending_count} leads pending sync")
            else:
                self.logger.info("✅ Status: All leads synced")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Status report failed: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"📡 Received signal {signum}")
        self.running = False
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp for display."""
        if not timestamp_str:
            return "Never"
        
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return timestamp_str


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(description="4Runr Lead Sync Service")
    parser.add_argument('command', choices=['start', 'stop', 'status', 'test'], 
                       help='Service command')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run as daemon (background process)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize service
    service = SyncService()
    
    try:
        if args.command == 'start':
            if args.daemon:
                print("🔄 Starting sync service as daemon...")
                # In a real implementation, you'd use proper daemon libraries
                # For now, just run normally
                service.start()
            else:
                service.start()
        
        elif args.command == 'stop':
            print("🛑 Stopping sync service...")
            service.stop()
        
        elif args.command == 'status':
            success = service.status()
            return 0 if success else 1
        
        elif args.command == 'test':
            success = service.test_sync()
            return 0 if success else 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Service interrupted by user")
        service.stop()
        return 1
    except Exception as e:
        print(f"❌ Service failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())