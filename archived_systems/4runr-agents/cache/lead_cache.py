"""
Lead Cache Manager

Provides fast local access to lead data with automatic Airtable synchronization.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from .models import DatabaseSchema

class LeadCache:
    """Main lead cache manager with fast local access and smart sync"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize lead cache with database"""
        
        # Use environment variable or default path
        self.db_path = db_path or os.getenv('LEAD_CACHE_DB_PATH', 'data/leads_cache.db')
        
        # Initialize database
        DatabaseSchema.create_tables(self.db_path)
        
        print(f"🗄️ Lead cache initialized: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return DatabaseSchema.get_connection(self.db_path)
    
    # Fast read operations (no API calls)
    
    def get_all_leads(self) -> List[Dict[str, Any]]:
        """Get all cached leads instantly"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, company, email, status, title, 
                       linkedin_url, website, location, data_json, last_updated
                FROM leads 
                ORDER BY last_updated DESC
            ''')
            
            leads = []
            for row in cursor.fetchall():
                lead = dict(row)
                # Parse JSON data if available
                if lead['data_json']:
                    try:
                        full_data = json.loads(lead['data_json'])
                        lead.update(full_data)
                    except json.JSONDecodeError:
                        pass
                leads.append(lead)
            
            return leads
        finally:
            conn.close()
    
    def get_leads_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get leads by status from cache (uses index for speed)"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, company, email, status, title, 
                       linkedin_url, website, location, data_json, last_updated
                FROM leads 
                WHERE status = ?
                ORDER BY last_updated DESC
            ''', (status,))
            
            leads = []
            for row in cursor.fetchall():
                lead = dict(row)
                if lead['data_json']:
                    try:
                        full_data = json.loads(lead['data_json'])
                        lead.update(full_data)
                    except json.JSONDecodeError:
                        pass
                leads.append(lead)
            
            return leads
        finally:
            conn.close()
    
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get specific lead from cache"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, company, email, status, title, 
                       linkedin_url, website, location, data_json, last_updated
                FROM leads 
                WHERE id = ?
            ''', (lead_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            lead = dict(row)
            if lead['data_json']:
                try:
                    full_data = json.loads(lead['data_json'])
                    lead.update(full_data)
                except json.JSONDecodeError:
                    pass
            
            return lead
        finally:
            conn.close()
    
    def search_leads(self, query: str) -> List[Dict[str, Any]]:
        """Search leads in cache (name, company, email)"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute('''
                SELECT id, name, company, email, status, title, 
                       linkedin_url, website, location, data_json, last_updated
                FROM leads 
                WHERE name LIKE ? OR company LIKE ? OR email LIKE ?
                ORDER BY 
                    CASE 
                        WHEN name LIKE ? THEN 1
                        WHEN company LIKE ? THEN 2
                        WHEN email LIKE ? THEN 3
                        ELSE 4
                    END,
                    last_updated DESC
            ''', (search_pattern, search_pattern, search_pattern,
                  search_pattern, search_pattern, search_pattern))
            
            leads = []
            for row in cursor.fetchall():
                lead = dict(row)
                if lead['data_json']:
                    try:
                        full_data = json.loads(lead['data_json'])
                        lead.update(full_data)
                    except json.JSONDecodeError:
                        pass
                leads.append(lead)
            
            return leads
        finally:
            conn.close()
    
    # Write operations (cache + mark for sync)
    
    def update_lead(self, lead_id: str, updates: Dict[str, Any], agent_name: str = "unknown") -> bool:
        """Update lead in cache and mark for sync with data validation"""
        if not lead_id or not updates:
            print(f"❌ Invalid update: lead_id={lead_id}, updates={updates}")
            return False
            
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Verify lead exists first
            cursor.execute('SELECT id, data_json, name, company FROM leads WHERE id = ?', (lead_id,))
            row = cursor.fetchone()
            if not row:
                print(f"❌ Lead {lead_id} not found in cache")
                return False
            
            # Log the update for tracking
            print(f"🔄 [{agent_name}] Updating lead {lead_id} ({row['name']} at {row['company']})")
            print(f"   Updates: {list(updates.keys())}")
            
            # Parse current data
            current_data = {}
            if row['data_json']:
                try:
                    current_data = json.loads(row['data_json'])
                except json.JSONDecodeError:
                    print(f"⚠️ Warning: Could not parse existing data for lead {lead_id}")
                    current_data = {}
            
            # Validate critical fields don't change unexpectedly
            critical_fields = ['Name', 'Company', 'LinkedIn URL']
            for field in critical_fields:
                if field in updates and field in current_data:
                    old_value = current_data.get(field, '')
                    new_value = updates.get(field, '')
                    if old_value and new_value and old_value != new_value:
                        print(f"⚠️ Warning: Changing {field} from '{old_value}' to '{new_value}' for lead {lead_id}")
            
            # Merge updates safely
            current_data.update(updates)
            
            # Update main fields for indexing (with fallbacks)
            name = current_data.get('Name') or current_data.get('Full Name', '')
            company = current_data.get('Company', '')
            email = current_data.get('Email', '')
            status = current_data.get('Status', 'new')
            title = current_data.get('Title') or current_data.get('Job Title', '')
            linkedin_url = current_data.get('LinkedIn URL', '')
            website = current_data.get('Website', '')
            location = current_data.get('Location', '')
            
            # Update lead in database with transaction
            cursor.execute('''
                UPDATE leads 
                SET name = ?, company = ?, email = ?, status = ?, title = ?,
                    linkedin_url = ?, website = ?, location = ?, data_json = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (name, company, email, status, title, linkedin_url, website, location,
                  json.dumps(current_data), lead_id))
            
            if cursor.rowcount == 0:
                print(f"❌ Failed to update lead {lead_id} in database")
                return False
            
            # Add to pending sync with metadata
            sync_data = {
                'updates': updates,
                'agent': agent_name,
                'timestamp': datetime.now().isoformat()
            }
            
            cursor.execute('''
                INSERT INTO pending_sync (lead_id, action, changes_json)
                VALUES (?, 'update', ?)
            ''', (lead_id, json.dumps(sync_data)))
            
            conn.commit()
            print(f"✅ [{agent_name}] Successfully updated lead {lead_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating lead {lead_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_lead(self, lead_data: Dict[str, Any], agent_name: str = "unknown") -> bool:
        """Add new lead to cache and mark for sync with validation"""
        if not lead_data:
            print("❌ Cannot add empty lead data")
            return False
            
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Validate required fields
            lead_id = lead_data.get('id') or lead_data.get('Id', '')
            if not lead_id:
                print("❌ Cannot add lead without ID")
                return False
            
            name = lead_data.get('Name') or lead_data.get('Full Name', '')
            company = lead_data.get('Company', '')
            
            if not name or not company:
                print(f"❌ Cannot add lead {lead_id} without name ({name}) or company ({company})")
                return False
            
            # Check if lead already exists
            cursor.execute('SELECT id, name, company FROM leads WHERE id = ?', (lead_id,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"⚠️ Lead {lead_id} already exists ({existing['name']} at {existing['company']})")
                print(f"   Use update_lead() instead of add_lead()")
                return False
            
            print(f"➕ [{agent_name}] Adding new lead: {name} at {company}")
            
            # Extract and validate main fields for indexing
            email = lead_data.get('Email', '')
            status = lead_data.get('Status', 'new')
            title = lead_data.get('Title') or lead_data.get('Job Title', '')
            linkedin_url = lead_data.get('LinkedIn URL', '')
            website = lead_data.get('Website', '')
            location = lead_data.get('Location', '')
            
            # Insert lead with validation
            cursor.execute('''
                INSERT INTO leads 
                (id, name, company, email, status, title, linkedin_url, website, location, data_json, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (lead_id, name, company, email, status, title, linkedin_url, website, location,
                  json.dumps(lead_data)))
            
            # Add to pending sync with metadata
            sync_data = {
                'lead_data': lead_data,
                'agent': agent_name,
                'timestamp': datetime.now().isoformat()
            }
            
            cursor.execute('''
                INSERT INTO pending_sync (lead_id, action, changes_json)
                VALUES (?, 'create', ?)
            ''', (lead_id, json.dumps(sync_data)))
            
            conn.commit()
            print(f"✅ [{agent_name}] Successfully added lead {lead_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding lead: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # Cache management
    
    def is_cache_fresh(self, max_age_hours: int = 2) -> bool:
        """Check if cache is still fresh"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT value FROM cache_meta WHERE key = 'last_full_sync'
            ''')
            row = cursor.fetchone()
            
            if not row:
                return False
            
            try:
                last_sync = datetime.fromisoformat(row['value'])
                age = datetime.now() - last_sync
                return age.total_seconds() < (max_age_hours * 3600)
            except (ValueError, TypeError):
                return False
                
        finally:
            conn.close()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Get total leads
            cursor.execute('SELECT COUNT(*) as total FROM leads')
            total_leads = cursor.fetchone()['total']
            
            # Get leads by status
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM leads 
                GROUP BY status
            ''')
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Get last sync time
            cursor.execute('''
                SELECT value FROM cache_meta WHERE key = 'last_full_sync'
            ''')
            last_sync_row = cursor.fetchone()
            last_sync = last_sync_row['value'] if last_sync_row else None
            
            # Get pending sync count
            cursor.execute('SELECT COUNT(*) as pending FROM pending_sync WHERE synced_at IS NULL')
            pending_sync = cursor.fetchone()['pending']
            
            return {
                'total_leads': total_leads,
                'status_counts': status_counts,
                'last_sync': last_sync,
                'pending_sync': pending_sync,
                'cache_fresh': self.is_cache_fresh()
            }
            
        finally:
            conn.close()
    
    def _update_cache_meta(self, key: str, value: str) -> None:
        """Update cache metadata"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cache_meta (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
            conn.commit()
        finally:
            conn.close()