#!/usr/bin/env python3
"""
Automatic Sync Scheduler

Provides automatic bidirectional synchronization between the local database and Airtable:
- Immediate sync to Airtable when changes are made to the database
- Daily sync from Airtable to get updates from external sources
"""

import os
import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.airtable_sync import AirtableSync
from database.models import get_lead_database
from config.settings import get_settings
from utils.logging import get_logger

class SyncScheduler:
    """
    Automatic synchronization scheduler for bidirectional Airtable sync.
    """
    
    def __init__(self):
        """Initialize the sync scheduler."""
        self.settings = get_settings()
        self.db = get_lead_database()
        self.airtable_sync = AirtableSync()
        self.logger = get_logger('sync-scheduler')
        
        # Scheduler state
        self.running = False
        self.scheduler_thread = None
        self.last_sync_to_airtable = None
        self.last_sync_from_airtable = None
        
        # Configuration
        self.immediate_sync_enabled = self.settings.sync.immediate_sync_enabled
        self.daily_sync_time = self.settings.sync.daily_sync_time
        self.sync_batch_size = self.settings.sync.batch_size
        
        self.logger.info("🔄 Sync Scheduler initialized")
        self.logger.info(f"⚙️ Immediate sync: {'Enabled' if self.immediate_sync_enabled else 'Disabled'}")
        self.logger.info(f"⚙️ Daily sync time: {self.daily_sync_time}")
    
    def start(self):
        """Start the sync scheduler."""
        if self.running:
            self.logger.warning("⚠️ Sync scheduler is already running")
            return
        
        self.logger.info("🚀 Starting sync scheduler")
        self.running = True
        
        # Schedule daily sync from Airtable
        schedule.every().day.at(self.daily_sync_time).do(self._run_daily_sync_from_airtable)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("✅ Sync scheduler started successfully")
    
    def stop(self):
        """Stop the sync scheduler."""
        if not self.running:
            self.logger.warning("⚠️ Sync scheduler is not running")
            return
        
        self.logger.info("🛑 Stopping sync scheduler")
        self.running = False
        
        # Clear scheduled jobs
        schedule.clear()
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("✅ Sync scheduler stopped")
    
    def sync_lead_to_airtable_immediately(self, lead_id: str) -> Dict[str, Any]:
        """
        Immediately sync a specific lead to Airtable.
        
        Args:
            lead_id: ID of the lead to sync
            
        Returns:
            Sync result dictionary
        """
        if not self.immediate_sync_enabled:
            self.logger.debug(f"⏭️ Immediate sync disabled, skipping lead {lead_id}")
            return {'success': True, 'skipped': True}
        
        try:
            self.logger.info(f"📤 Immediately syncing lead {lead_id} to Airtable")
            
            # Get the specific lead
            lead = self.db.get_lead(lead_id)
            if not lead:
                self.logger.error(f"❌ Lead {lead_id} not found")
                return {'success': False, 'error': 'Lead not found'}
            
            # Sync to Airtable
            result = self.airtable_sync.sync_leads_to_airtable([lead], force=True)
            
            if result['success']:
                self.logger.info(f"✅ Lead {lead.name} synced to Airtable immediately")
                self.last_sync_to_airtable = datetime.now()
            else:
                self.logger.error(f"❌ Failed to sync lead {lead.name}: {result.get('errors', [])}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Immediate sync failed for lead {lead_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def sync_all_pending_to_airtable(self) -> Dict[str, Any]:
        """
        Sync all pending leads to Airtable.
        
        Returns:
            Sync result dictionary
        """
        try:
            self.logger.info("📤 Syncing all pending leads to Airtable")
            
            # Get pending leads
            pending_leads = self.db.search_leads({'sync_status': 'pending'}, limit=self.sync_batch_size)
            
            if not pending_leads:
                self.logger.info("✅ No pending leads to sync")
                return {'success': True, 'synced_count': 0}
            
            self.logger.info(f"📋 Found {len(pending_leads)} pending leads")
            
            # Sync to Airtable
            result = self.airtable_sync.sync_leads_to_airtable(pending_leads)
            
            if result['success']:
                self.logger.info(f"✅ {result['synced_count']} leads synced to Airtable")
                self.last_sync_to_airtable = datetime.now()
            else:
                self.logger.error(f"❌ Sync failed: {result['failed_count']} failures")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Batch sync to Airtable failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def sync_from_airtable_now(self, force: bool = False) -> Dict[str, Any]:
        """
        Immediately sync updates from Airtable.
        
        Args:
            force: Force sync regardless of last sync time
            
        Returns:
            Sync result dictionary
        """
        try:
            self.logger.info("📥 Syncing updates from Airtable")
            
            # Sync from Airtable
            result = self.airtable_sync.sync_updates_from_airtable(force=force)
            
            if result['success']:
                self.logger.info(f"✅ {result['synced_count']} updates synced from Airtable")
                self.last_sync_from_airtable = datetime.now()
            else:
                self.logger.error(f"❌ Sync from Airtable failed: {result.get('errors', [])}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Sync from Airtable failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status and statistics.
        
        Returns:
            Sync status dictionary
        """
        try:
            # Get base sync status from AirtableSync
            base_status = self.airtable_sync.get_sync_status()
            
            # Add scheduler-specific information
            scheduler_status = {
                'scheduler_running': self.running,
                'immediate_sync_enabled': self.immediate_sync_enabled,
                'daily_sync_time': self.daily_sync_time,
                'last_sync_to_airtable': self.last_sync_to_airtable.isoformat() if self.last_sync_to_airtable else None,
                'last_sync_from_airtable': self.last_sync_from_airtable.isoformat() if self.last_sync_from_airtable else None,
                'next_daily_sync': self._get_next_daily_sync_time(),
                'pending_leads_count': len(self.db.search_leads({'sync_status': 'pending'}))
            }
            
            return {
                **base_status,
                'scheduler': scheduler_status
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get sync status: {str(e)}")
            return {'error': str(e)}
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        self.logger.info("🔄 Scheduler loop started")
        
        while self.running:
            try:
                # Run pending scheduled jobs
                schedule.run_pending()
                
                # Check for immediate sync opportunities
                if self.immediate_sync_enabled:
                    self._check_for_immediate_sync()
                
                # Sleep for a short interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Scheduler loop error: {str(e)}")
                time.sleep(60)  # Wait longer on error
        
        self.logger.info("🔄 Scheduler loop stopped")
    
    def _run_daily_sync_from_airtable(self):
        """Run the daily sync from Airtable (scheduled job)."""
        self.logger.info("📅 Running daily sync from Airtable")
        
        try:
            result = self.sync_from_airtable_now(force=True)
            
            if result['success']:
                self.logger.info(f"✅ Daily sync completed: {result['synced_count']} updates from Airtable")
            else:
                self.logger.error(f"❌ Daily sync failed: {result.get('errors', [])}")
            
            # Also sync any pending leads to Airtable
            pending_result = self.sync_all_pending_to_airtable()
            if pending_result['success'] and pending_result['synced_count'] > 0:
                self.logger.info(f"✅ Also synced {pending_result['synced_count']} pending leads to Airtable")
            
        except Exception as e:
            self.logger.error(f"❌ Daily sync job failed: {str(e)}")
    
    def _check_for_immediate_sync(self):
        """Check for leads that need immediate sync."""
        try:
            # Get recently modified leads that haven't been synced
            cutoff_time = datetime.now() - timedelta(minutes=5)  # Last 5 minutes
            
            # This is a simplified check - in a real implementation, you might want
            # to track database changes more precisely
            pending_leads = self.db.search_leads({
                'sync_status': 'pending',
                'updated_at_after': cutoff_time.isoformat()
            }, limit=10)
            
            if pending_leads:
                self.logger.debug(f"🔄 Found {len(pending_leads)} leads for immediate sync")
                result = self.airtable_sync.sync_leads_to_airtable(pending_leads)
                
                if result['success'] and result['synced_count'] > 0:
                    self.logger.info(f"✅ Immediately synced {result['synced_count']} leads")
                    self.last_sync_to_airtable = datetime.now()
            
        except Exception as e:
            self.logger.debug(f"⚠️ Immediate sync check failed: {str(e)}")
    
    def _get_next_daily_sync_time(self) -> Optional[str]:
        """Get the next scheduled daily sync time."""
        try:
            jobs = schedule.get_jobs()
            if jobs:
                next_run = min(job.next_run for job in jobs)
                return next_run.isoformat()
            return None
        except Exception:
            return None


# Global sync scheduler instance
_sync_scheduler = None

def get_sync_scheduler() -> SyncScheduler:
    """Get the global sync scheduler instance."""
    global _sync_scheduler
    if _sync_scheduler is None:
        _sync_scheduler = SyncScheduler()
    return _sync_scheduler

def start_sync_scheduler():
    """Start the global sync scheduler."""
    scheduler = get_sync_scheduler()
    scheduler.start()

def stop_sync_scheduler():
    """Stop the global sync scheduler."""
    scheduler = get_sync_scheduler()
    scheduler.stop()

def sync_lead_immediately(lead_id: str) -> Dict[str, Any]:
    """
    Immediately sync a lead to Airtable (convenience function).
    
    Args:
        lead_id: ID of the lead to sync
        
    Returns:
        Sync result dictionary
    """
    scheduler = get_sync_scheduler()
    return scheduler.sync_lead_to_airtable_immediately(lead_id)

def sync_all_pending() -> Dict[str, Any]:
    """
    Sync all pending leads to Airtable (convenience function).
    
    Returns:
        Sync result dictionary
    """
    scheduler = get_sync_scheduler()
    return scheduler.sync_all_pending_to_airtable()

def sync_from_airtable() -> Dict[str, Any]:
    """
    Sync updates from Airtable (convenience function).
    
    Returns:
        Sync result dictionary
    """
    scheduler = get_sync_scheduler()
    return scheduler.sync_from_airtable_now()


if __name__ == "__main__":
    # Test the sync scheduler
    import argparse
    
    parser = argparse.ArgumentParser(description="4Runr Sync Scheduler")
    parser.add_argument('--start', action='store_true', help='Start the sync scheduler')
    parser.add_argument('--status', action='store_true', help='Show sync status')
    parser.add_argument('--sync-pending', action='store_true', help='Sync all pending leads')
    parser.add_argument('--sync-from-airtable', action='store_true', help='Sync from Airtable')
    parser.add_argument('--test', action='store_true', help='Run test sync operations')
    
    args = parser.parse_args()
    
    scheduler = get_sync_scheduler()
    
    if args.start:
        print("🚀 Starting sync scheduler...")
        scheduler.start()
        print("✅ Sync scheduler started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping sync scheduler...")
            scheduler.stop()
            print("✅ Sync scheduler stopped.")
    
    elif args.status:
        print("📊 Sync Status:")
        status = scheduler.get_sync_status()
        import json
        print(json.dumps(status, indent=2))
    
    elif args.sync_pending:
        print("📤 Syncing pending leads...")
        result = scheduler.sync_all_pending_to_airtable()
        print(f"Result: {result}")
    
    elif args.sync_from_airtable:
        print("📥 Syncing from Airtable...")
        result = scheduler.sync_from_airtable_now(force=True)
        print(f"Result: {result}")
    
    elif args.test:
        print("🧪 Running sync tests...")
        
        # Test sync status
        print("1. Testing sync status...")
        status = scheduler.get_sync_status()
        print(f"   Status: {'✅' if not status.get('error') else '❌'}")
        
        # Test sync from Airtable
        print("2. Testing sync from Airtable...")
        result = scheduler.sync_from_airtable_now()
        print(f"   Result: {'✅' if result['success'] else '❌'} ({result.get('synced_count', 0)} synced)")
        
        # Test sync to Airtable
        print("3. Testing sync to Airtable...")
        result = scheduler.sync_all_pending_to_airtable()
        print(f"   Result: {'✅' if result['success'] else '❌'} ({result.get('synced_count', 0)} synced)")
        
        print("✅ Sync tests completed")
    
    else:
        parser.print_help()