"""
Sync Manager for Airtable Integration

Handles pulling leads from Airtable and pushing changes back.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from .models import DatabaseSchema

class SyncManager:
    """Manages synchronization between local cache and Airtable"""
    
    def __init__(self, airtable_client, cache_manager):
        """Initialize with Airtable client and cache manager"""
        self.airtable = airtable_client
        self.cache = cache_manager
        
    def pull_from_airtable(self, force: bool = False) -> Dict[str, Any]:
        """Pull all leads from Airtable to cache"""
        
        print("🔄 Pulling leads from Airtable...")
        start_time = time.time()
        
        try:
            # Get all records from Airtable
            all_records = self.airtable.table.all()
            
            conn = self.cache._get_connection()
            cursor = conn.cursor()
            
            leads_processed = 0
            leads_updated = 0
            leads_created = 0
            
            try:
                for record in all_records:
                    record_id = record['id']
                    fields = record.get('fields', {})
                    
                    # Extract main fields for indexing
                    name = fields.get('Name') or fields.get('Full Name', '')
                    company = fields.get('Company', '')
                    email = fields.get('Email', '')
                    status = fields.get('Status', 'new')
                    title = fields.get('Title') or fields.get('Job Title', '')
                    linkedin_url = fields.get('LinkedIn URL', '')
                    website = fields.get('Website', '')
                    location = fields.get('Location', '')
                    
                    # Check if lead exists
                    cursor.execute('SELECT id FROM leads WHERE id = ?', (record_id,))
                    exists = cursor.fetchone()
                    
                    # Insert or update lead
                    cursor.execute('''
                        INSERT OR REPLACE INTO leads 
                        (id, name, company, email, status, title, linkedin_url, website, location, data_json, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (record_id, name, company, email, status, title, linkedin_url, website, location,
                          json.dumps(fields)))
                    
                    if exists:
                        leads_updated += 1
                    else:
                        leads_created += 1
                    
                    leads_processed += 1
                
                # Update sync metadata
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_meta (key, value, updated_at)
                    VALUES ('last_full_sync', ?, CURRENT_TIMESTAMP)
                ''', (datetime.now().isoformat(),))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_meta (key, value, updated_at)
                    VALUES ('total_leads', ?, CURRENT_TIMESTAMP)
                ''', (str(leads_processed),))
                
                conn.commit()
                
                duration = time.time() - start_time
                
                result = {
                    'success': True,
                    'leads_processed': leads_processed,
                    'leads_created': leads_created,
                    'leads_updated': leads_updated,
                    'duration_seconds': round(duration, 2),
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"✅ Sync complete: {leads_processed} leads in {duration:.1f}s")
                print(f"   Created: {leads_created}, Updated: {leads_updated}")
                
                return result
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            duration = time.time() - start_time
            error_result = {
                'success': False,
                'error': str(e),
                'duration_seconds': round(duration, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"❌ Sync failed after {duration:.1f}s: {e}")
            return error_result
    
    def push_to_airtable(self, max_records: int = 50) -> Dict[str, Any]:
        """Push pending changes to Airtable"""
        
        print("📤 Pushing changes to Airtable...")
        start_time = time.time()
        
        conn = self.cache._get_connection()
        
        try:
            cursor = conn.cursor()
            
            # Get pending sync records
            cursor.execute('''
                SELECT id, lead_id, action, changes_json, created_at
                FROM pending_sync 
                WHERE synced_at IS NULL
                ORDER BY created_at ASC
                LIMIT ?
            ''', (max_records,))
            
            pending_records = cursor.fetchall()
            
            if not pending_records:
                print("✅ No pending changes to sync")
                return {
                    'success': True,
                    'records_processed': 0,
                    'records_synced': 0,
                    'records_failed': 0,
                    'duration_seconds': 0
                }
            
            records_synced = 0
            records_failed = 0
            failed_records = []
            
            for record in pending_records:
                sync_id = record['id']
                lead_id = record['lead_id']
                action = record['action']
                
                try:
                    changes = json.loads(record['changes_json'])
                    
                    if action == 'update':
                        # Update existing record in Airtable
                        self.airtable.table.update(lead_id, changes)
                        
                    elif action == 'create':
                        # Create new record in Airtable
                        # Note: For creates, we might need to handle the ID differently
                        # depending on how your Airtable is set up
                        self.airtable.table.create(changes)
                    
                    # Mark as synced
                    cursor.execute('''
                        UPDATE pending_sync 
                        SET synced_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (sync_id,))
                    
                    records_synced += 1
                    
                except Exception as e:
                    print(f"❌ Failed to sync record {lead_id}: {e}")
                    records_failed += 1
                    failed_records.append({
                        'lead_id': lead_id,
                        'action': action,
                        'error': str(e)
                    })
            
            conn.commit()
            
            duration = time.time() - start_time
            
            result = {
                'success': records_failed == 0,
                'records_processed': len(pending_records),
                'records_synced': records_synced,
                'records_failed': records_failed,
                'failed_records': failed_records,
                'duration_seconds': round(duration, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            if records_failed == 0:
                print(f"✅ Push complete: {records_synced} records synced in {duration:.1f}s")
            else:
                print(f"⚠️ Push partial: {records_synced} synced, {records_failed} failed in {duration:.1f}s")
            
            return result
            
        except Exception as e:
            conn.rollback()
            duration = time.time() - start_time
            
            error_result = {
                'success': False,
                'error': str(e),
                'duration_seconds': round(duration, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"❌ Push failed after {duration:.1f}s: {e}")
            return error_result
            
        finally:
            conn.close()
    
    def sync_bidirectional(self, push_first: bool = True) -> Dict[str, Any]:
        """Perform two-way sync with Airtable"""
        
        print("🔄 Starting bidirectional sync...")
        start_time = time.time()
        
        results = {
            'pull_result': None,
            'push_result': None,
            'overall_success': False,
            'duration_seconds': 0
        }
        
        try:
            if push_first:
                # Push local changes first
                results['push_result'] = self.push_to_airtable()
                
                # Then pull updates from Airtable
                results['pull_result'] = self.pull_from_airtable()
            else:
                # Pull from Airtable first
                results['pull_result'] = self.pull_from_airtable()
                
                # Then push local changes
                results['push_result'] = self.push_to_airtable()
            
            results['overall_success'] = (
                results['pull_result']['success'] and 
                results['push_result']['success']
            )
            
            results['duration_seconds'] = round(time.time() - start_time, 2)
            
            if results['overall_success']:
                print(f"✅ Bidirectional sync complete in {results['duration_seconds']:.1f}s")
            else:
                print(f"⚠️ Bidirectional sync had issues in {results['duration_seconds']:.1f}s")
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            results['duration_seconds'] = round(time.time() - start_time, 2)
            print(f"❌ Bidirectional sync failed: {e}")
            return results
    
    def get_pending_sync_count(self) -> int:
        """Get count of pending sync records"""
        conn = self.cache._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM pending_sync WHERE synced_at IS NULL')
            return cursor.fetchone()['count']
        finally:
            conn.close()
    
    def clear_synced_records(self, older_than_days: int = 7) -> int:
        """Clear old synced records to keep database clean"""
        conn = self.cache._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM pending_sync 
                WHERE synced_at IS NOT NULL 
                AND synced_at < datetime('now', '-{} days')
            '''.format(older_than_days))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old sync records")
            
            return deleted_count
            
        finally:
            conn.close()