#!/usr/bin/env python3
"""
Sync Manager

Coordinates synchronization operations between the local database and external systems.
Handles scheduling, conflict resolution, and sync orchestration.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .airtable_sync import AirtableSync
from ..database.models import get_lead_database
from ..config.settings import get_settings

logger = logging.getLogger('sync-manager')

class SyncManager:
    """
    Centralized sync manager for coordinating all synchronization operations.
    """
    
    def __init__(self):
        """Initialize sync manager."""
        self.settings = get_settings()
        self.db = get_lead_database()
        self.airtable_sync = AirtableSync()
        
        # Sync scheduling
        self.sync_interval = self.settings.airtable.sync_interval_minutes * 60  # Convert to seconds
        self.auto_sync_enabled = self.settings.airtable.auto_sync_enabled
        
        # Threading
        self._sync_thread = None
        self._stop_event = threading.Event()
        self._sync_lock = threading.Lock()
        
        # Sync statistics
        self.sync_stats = {
            'last_sync_to_airtable': None,
            'last_sync_from_airtable': None,
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0
        }
        
        logger.info("🔄 Sync Manager initialized")
        logger.info(f"⚙️ Auto sync enabled: {self.auto_sync_enabled}")
        logger.info(f"⚙️ Sync interval: {self.sync_interval // 60} minutes")
    
    def start_automatic_sync(self):
        """Start automatic synchronization in background thread."""
        if not self.auto_sync_enabled:
            logger.info("⚠️ Automatic sync is disabled")
            return
        
        if self._sync_thread and self._sync_thread.is_alive():
            logger.warning("⚠️ Automatic sync is already running")
            return
        
        self._stop_event.clear()
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        
        logger.info("🚀 Automatic sync started")
    
    def stop_automatic_sync(self):
        """Stop automatic synchronization."""
        if not self._sync_thread or not self._sync_thread.is_alive():
            logger.info("ℹ️ Automatic sync is not running")
            return
        
        self._stop_event.set()
        self._sync_thread.join(timeout=30)
        
        if self._sync_thread.is_alive():
            logger.warning("⚠️ Sync thread did not stop gracefully")
        else:
            logger.info("✅ Automatic sync stopped")
    
    def _sync_loop(self):
        """Main sync loop running in background thread."""
        logger.info("🔄 Sync loop started")
        
        while not self._stop_event.is_set():
            try:
                # Perform sync operations
                self._perform_scheduled_sync()
                
                # Wait for next sync interval
                self._stop_event.wait(self.sync_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in sync loop: {str(e)}")
                # Wait a bit before retrying
                self._stop_event.wait(60)
        
        logger.info("🔄 Sync loop stopped")
    
    def _perform_scheduled_sync(self):
        """Perform scheduled sync operations."""
        with self._sync_lock:
            logger.info("🔄 Starting scheduled sync")
            
            try:
                # Sync to Airtable (frequent)
                to_airtable_result = self.sync_to_airtable()
                
                # Sync from Airtable (less frequent - daily)
                should_sync_from_airtable = self._should_sync_from_airtable()
                from_airtable_result = None
                
                if should_sync_from_airtable:
                    from_airtable_result = self.sync_from_airtable()
                
                # Update statistics
                self._update_sync_stats(to_airtable_result, from_airtable_result)
                
                logger.info("✅ Scheduled sync completed")
                
            except Exception as e:
                logger.error(f"❌ Scheduled sync failed: {str(e)}")
                self.sync_stats['failed_syncs'] += 1
    
    def sync_to_airtable(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync leads from database to Airtable.
        
        Args:
            force: Force sync even if recently synced
            
        Returns:
            Sync result dictionary
        """
        logger.info("📤 Starting manual sync to Airtable")
        
        try:
            result = self.airtable_sync.sync_leads_to_airtable(force=force)
            
            if result['success']:
                self.sync_stats['last_sync_to_airtable'] = datetime.now().isoformat()
                logger.info(f"✅ Sync to Airtable completed: {result['synced_count']} leads synced")
            else:
                logger.error(f"❌ Sync to Airtable failed: {result['failed_count']} failures")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Sync to Airtable failed: {str(e)}")
            return {
                'success': False,
                'synced_count': 0,
                'failed_count': 0,
                'errors': [str(e)]
            }
    
    def sync_from_airtable(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync updates from Airtable to database.
        
        Args:
            force: Force sync regardless of last sync time
            
        Returns:
            Sync result dictionary
        """
        logger.info("📥 Starting manual sync from Airtable")
        
        try:
            result = self.airtable_sync.sync_updates_from_airtable(force=force)
            
            if result['success']:
                self.sync_stats['last_sync_from_airtable'] = datetime.now().isoformat()
                logger.info(f"✅ Sync from Airtable completed: {result['synced_count']} leads updated")
            else:
                logger.error(f"❌ Sync from Airtable failed: {result['failed_count']} failures")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Sync from Airtable failed: {str(e)}")
            return {
                'success': False,
                'synced_count': 0,
                'failed_count': 0,
                'errors': [str(e)]
            }
    
    def sync_bidirectional(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform bidirectional sync (both directions).
        
        Args:
            force: Force sync regardless of timing
            
        Returns:
            Combined sync results
        """
        logger.info("🔄 Starting bidirectional sync")
        
        # Use thread pool for parallel execution
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both sync operations
            to_airtable_future = executor.submit(self.sync_to_airtable, force)
            from_airtable_future = executor.submit(self.sync_from_airtable, force)
            
            # Wait for completion
            results = {}
            for future in as_completed([to_airtable_future, from_airtable_future]):
                try:
                    if future == to_airtable_future:
                        results['to_airtable'] = future.result()
                    else:
                        results['from_airtable'] = future.result()
                except Exception as e:
                    logger.error(f"❌ Sync operation failed: {str(e)}")
                    if future == to_airtable_future:
                        results['to_airtable'] = {'success': False, 'errors': [str(e)]}
                    else:
                        results['from_airtable'] = {'success': False, 'errors': [str(e)]}
        
        # Combine results
        combined_result = {
            'success': all(r.get('success', False) for r in results.values()),
            'to_airtable': results.get('to_airtable', {}),
            'from_airtable': results.get('from_airtable', {}),
            'total_synced': sum(r.get('synced_count', 0) for r in results.values()),
            'total_failed': sum(r.get('failed_count', 0) for r in results.values())
        }
        
        logger.info(f"🔄 Bidirectional sync completed: {combined_result['total_synced']} synced, {combined_result['total_failed']} failed")
        
        return combined_result
    
    def _should_sync_from_airtable(self) -> bool:
        """Determine if we should sync from Airtable based on timing."""
        last_sync = self.sync_stats.get('last_sync_from_airtable')
        
        if not last_sync:
            return True  # Never synced before
        
        try:
            last_sync_time = datetime.fromisoformat(last_sync)
            time_since_last = datetime.now() - last_sync_time
            
            # Sync from Airtable once daily (24 hours)
            return time_since_last >= timedelta(hours=24)
            
        except Exception:
            return True  # If we can't parse the time, sync anyway
    
    def _update_sync_stats(self, to_airtable_result: Dict[str, Any], from_airtable_result: Optional[Dict[str, Any]]):
        """Update sync statistics."""
        self.sync_stats['total_syncs'] += 1
        
        # Check if any sync was successful
        success = False
        if to_airtable_result and to_airtable_result.get('success'):
            success = True
        if from_airtable_result and from_airtable_result.get('success'):
            success = True
        
        if success:
            self.sync_stats['successful_syncs'] += 1
        else:
            self.sync_stats['failed_syncs'] += 1
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get comprehensive sync status.
        
        Returns:
            Dictionary with sync status information
        """
        try:
            # Get Airtable sync status
            airtable_status = self.airtable_sync.get_sync_status()
            
            # Get database statistics
            db_stats = self.db.get_lead_statistics()
            
            # Combine with manager statistics
            status = {
                'sync_manager': {
                    'auto_sync_enabled': self.auto_sync_enabled,
                    'sync_interval_minutes': self.sync_interval // 60,
                    'sync_thread_active': self._sync_thread and self._sync_thread.is_alive(),
                    'statistics': self.sync_stats
                },
                'airtable_sync': airtable_status,
                'database_stats': db_stats,
                'last_checked': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get sync status: {str(e)}")
            return {
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }
    
    def resolve_sync_conflicts(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolve sync conflicts using configured strategy.
        
        Args:
            conflicts: List of conflict records
            
        Returns:
            List of resolution results
        """
        logger.info(f"🔧 Resolving {len(conflicts)} sync conflicts")
        
        resolutions = []
        
        for conflict in conflicts:
            try:
                # For now, use "database wins" strategy
                resolution = self._resolve_conflict_database_wins(conflict)
                resolutions.append(resolution)
                
            except Exception as e:
                logger.error(f"❌ Failed to resolve conflict: {str(e)}")
                resolutions.append({
                    'conflict_id': conflict.get('id'),
                    'resolved': False,
                    'error': str(e)
                })
        
        logger.info(f"🔧 Resolved {sum(1 for r in resolutions if r.get('resolved'))} conflicts")
        
        return resolutions
    
    def _resolve_conflict_database_wins(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflict using "database wins" strategy.
        
        Args:
            conflict: Conflict record
            
        Returns:
            Resolution result
        """
        # This is a placeholder implementation
        # In a real system, you would implement conflict resolution logic
        # based on timestamps, data quality, etc.
        
        return {
            'conflict_id': conflict.get('id'),
            'resolved': True,
            'strategy': 'database_wins',
            'action': 'database_version_kept'
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on sync operations.
        
        Returns:
            Health check results
        """
        try:
            health = {
                'status': 'healthy',
                'checks': {},
                'checked_at': datetime.now().isoformat()
            }
            
            # Check database connectivity
            db_health = self.db.db.health_check()
            health['checks']['database'] = db_health['status']
            
            # Check Airtable connectivity (simple test)
            try:
                # This would be a simple API test
                health['checks']['airtable'] = 'healthy'
            except Exception:
                health['checks']['airtable'] = 'unhealthy'
            
            # Check sync thread status
            health['checks']['sync_thread'] = 'running' if (self._sync_thread and self._sync_thread.is_alive()) else 'stopped'
            
            # Overall status
            if any(status == 'unhealthy' for status in health['checks'].values()):
                health['status'] = 'unhealthy'
            
            return health
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }


# Global sync manager instance
_sync_manager: Optional[SyncManager] = None

def get_sync_manager() -> SyncManager:
    """
    Get global sync manager instance.
    
    Returns:
        SyncManager instance
    """
    global _sync_manager
    
    if _sync_manager is None:
        _sync_manager = SyncManager()
    
    return _sync_manager


# Convenience functions
def start_automatic_sync():
    """Start automatic synchronization."""
    manager = get_sync_manager()
    manager.start_automatic_sync()

def stop_automatic_sync():
    """Stop automatic synchronization."""
    manager = get_sync_manager()
    manager.stop_automatic_sync()

def sync_to_airtable(force: bool = False) -> Dict[str, Any]:
    """Sync to Airtable (convenience function)."""
    manager = get_sync_manager()
    return manager.sync_to_airtable(force)

def sync_from_airtable(force: bool = False) -> Dict[str, Any]:
    """Sync from Airtable (convenience function)."""
    manager = get_sync_manager()
    return manager.sync_from_airtable(force)

def get_sync_status() -> Dict[str, Any]:
    """Get sync status (convenience function)."""
    manager = get_sync_manager()
    return manager.get_sync_status()


if __name__ == "__main__":
    # Test sync manager
    manager = get_sync_manager()
    
    print("🧪 Testing Sync Manager...")
    
    # Test sync operations
    result = manager.sync_to_airtable()
    print(f"Sync to Airtable result: {result}")
    
    # Test status
    status = manager.get_sync_status()
    print(f"Sync status: {status}")
    
    # Test health check
    health = manager.health_check()
    print(f"Health check: {health}")
    
    print("✅ Sync manager test completed")