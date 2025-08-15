#!/usr/bin/env python3
"""
Automated Real-Time Airtable Sync for EC2
- Runs continuously monitoring database changes
- Intelligent lead quality scoring 
- Error handling and retry logic
- Perfect for EC2 deployment
"""

import sqlite3
import requests
import json
import os
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/airtable_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedAirtableSync:
    """Automated real-time Airtable sync for EC2 deployment"""
    
    def __init__(self, db_path: str = "data/unified_leads.db"):
        self.db_path = db_path
        
        # Airtable credentials
        self.api_key = 'pat1EXE7KfOBTgJl6.28307c0b4f5eb80de65d01de18ecead5da6e7bc98f04ceea7e60b540e9773923'
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_name = 'Table 1'
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        self.airtable_url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_name}'
        
        # Sync state tracking
        self.last_sync_time = None
        self.sync_interval = 300  # 5 minutes
        self.retry_attempts = 3
        self.retry_delay = 60  # 1 minute
        
        # Performance metrics
        self.sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync_duration': 0,
            'avg_sync_duration': 0
        }
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        logger.info("Automated Airtable Sync initialized")
    
    def calculate_intelligent_lead_quality(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate intelligent lead quality with detailed breakdown"""
        
        score = 0
        factors = []
        
        # Email Quality (35 points)
        email_score = 0
        if lead.get('verified'):
            email_score += 30
            factors.append("Email verified")
        elif lead.get('email') and '@' in lead.get('email', ''):
            email = lead['email']
            domain = email.split('@')[1] if '@' in email else ''
            if domain and not any(provider in domain.lower() for provider in ['gmail', 'yahoo', 'hotmail', 'outlook']):
                email_score += 25
                factors.append("Corporate email")
            else:
                email_score += 15
                factors.append("Personal email")
        
        # Company Data Quality (25 points)
        company_score = 0
        if lead.get('company'):
            company_score += 5
            factors.append("Company name")
        if lead.get('industry'):
            company_score += 5
            factors.append("Industry data")
        if lead.get('company_size'):
            company_score += 5
            factors.append("Company size")
            # Enterprise bonus
            if any(size in lead.get('company_size', '').lower() for size in ['large', 'enterprise', '1000+', '500+']):
                company_score += 5
                factors.append("Enterprise company")
        if lead.get('website'):
            company_score += 5
            factors.append("Company website")
        
        # Engagement Potential (25 points)
        engagement_score = 0
        job_title = lead.get('job_title', '').lower()
        if any(role in job_title for role in ['ceo', 'cto', 'founder', 'president', 'director', 'vp']):
            engagement_score += 20
            factors.append("Decision maker title")
        elif any(role in job_title for role in ['manager', 'lead', 'senior']):
            engagement_score += 15
            factors.append("Senior role")
        elif job_title:
            engagement_score += 10
            factors.append("Professional title")
            
        if lead.get('linkedin_url'):
            engagement_score += 5
            factors.append("LinkedIn profile")
        
        # Data Completeness (15 points)
        data_score = 0
        if lead.get('ai_message') and len(lead.get('ai_message', '')) > 200:
            data_score += 10
            factors.append("Personalized AI message")
        if lead.get('company_description'):
            data_score += 5
            factors.append("Company description")
        
        total_score = email_score + company_score + engagement_score + data_score
        
        # Determine tier
        if total_score >= 80:
            tier = "Hot"
        elif total_score >= 60:
            tier = "Warm"
        else:
            tier = "Cold"
        
        return {
            'score': total_score,
            'tier': tier,
            'factors': factors,
            'breakdown': {
                'email_quality': email_score,
                'company_data': company_score,
                'engagement_potential': engagement_score,
                'data_completeness': data_score
            }
        }
    
    def sync_new_and_updated_leads(self) -> Dict[str, Any]:
        """Sync only new and updated leads since last sync"""
        
        start_time = time.time()
        logger.info("Starting incremental sync...")
        
        try:
            # Get leads that need syncing
            leads_to_sync = self._get_leads_to_sync()
            
            if not leads_to_sync:
                logger.info("No leads to sync")
                return {'processed': 0, 'updated': 0, 'created': 0, 'errors': 0}
            
            logger.info(f"Found {len(leads_to_sync)} leads to sync")
            
            # Get existing Airtable records
            existing_records = self._get_existing_airtable_records()
            email_to_record = {record.get('fields', {}).get('Email', '').lower(): record['id'] 
                              for record in existing_records if record.get('fields', {}).get('Email')}
            
            stats = {'processed': 0, 'updated': 0, 'created': 0, 'errors': 0, 'error_details': []}
            
            for lead in leads_to_sync:
                try:
                    # Calculate intelligent quality
                    quality_analysis = self.calculate_intelligent_lead_quality(lead)
                    
                    # Map to Airtable fields
                    airtable_fields = self._map_lead_to_airtable(lead, quality_analysis)
                    
                    # Update or create record
                    email = lead.get('email', '').lower()
                    if email and email in email_to_record:
                        # Update existing record
                        success = self._update_airtable_record_with_retry(email_to_record[email], airtable_fields)
                        if success:
                            stats['updated'] += 1
                            self._mark_lead_as_synced(lead['id'])
                            logger.info(f"✅ Updated: {lead.get('full_name', 'Unknown')} - Quality: {quality_analysis['tier']}")
                        else:
                            stats['errors'] += 1
                    elif email:
                        # Create new record
                        success, record_id = self._create_airtable_record_with_retry(airtable_fields)
                        if success:
                            stats['created'] += 1
                            self._mark_lead_as_synced(lead['id'], record_id)
                            logger.info(f"✅ Created: {lead.get('full_name', 'Unknown')} - Quality: {quality_analysis['tier']}")
                        else:
                            stats['errors'] += 1
                    
                    stats['processed'] += 1
                    
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"{lead.get('full_name', 'Unknown')}: {str(e)}")
                    logger.error(f"Error processing {lead.get('full_name', 'Unknown')}: {e}")
            
            # Update sync stats
            duration = time.time() - start_time
            self._update_sync_stats(duration, stats['errors'] == 0)
            self.last_sync_time = datetime.now()
            
            logger.info(f"Sync completed: {stats['updated']} updated, {stats['created']} created, {stats['errors']} errors in {duration:.2f}s")
            
            return stats
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self._update_sync_stats(time.time() - start_time, False)
            return {'processed': 0, 'updated': 0, 'created': 0, 'errors': 1, 'error_details': [str(e)]}
    
    def _get_leads_to_sync(self) -> List[Dict[str, Any]]:
        """Get leads that need to be synced"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Get leads that have been updated since last sync or never synced
        if self.last_sync_time:
            # Incremental sync
            cursor = conn.execute("""
                SELECT 
                    id, full_name, email, company, job_title, linkedin_url, website,
                    industry, location, company_size, phone, business_type, 
                    company_description, ai_message, created_at, updated_at, 
                    scraped_at, message_generated_at, verified, enriched, 
                    score, engagement_level, engagement_status, response_received,
                    contact_attempts, follow_up_count, last_engagement_date,
                    engagement_notes, source, notes, airtable_id, sync_status
                FROM leads 
                WHERE ai_message IS NOT NULL AND ai_message != ''
                AND (sync_status != 'synced' OR updated_at > ?)
            """, (self.last_sync_time.isoformat(),))
        else:
            # Full sync
            cursor = conn.execute("""
                SELECT 
                    id, full_name, email, company, job_title, linkedin_url, website,
                    industry, location, company_size, phone, business_type, 
                    company_description, ai_message, created_at, updated_at, 
                    scraped_at, message_generated_at, verified, enriched, 
                    score, engagement_level, engagement_status, response_received,
                    contact_attempts, follow_up_count, last_engagement_date,
                    engagement_notes, source, notes, airtable_id, sync_status
                FROM leads 
                WHERE ai_message IS NOT NULL AND ai_message != ''
            """)
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leads
    
    def _map_lead_to_airtable(self, lead: Dict[str, Any], quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Map lead data to Airtable fields"""
        
        fields = {
            'Full Name': lead.get('full_name', ''),
            'Email': lead.get('email', ''),
            'Company': lead.get('company', ''),
            'Job Title': lead.get('job_title', '') or 'Not specified',
            'LinkedIn URL': lead.get('linkedin_url', ''),
            'Website': lead.get('website', ''),
            'AI Message': lead.get('ai_message', ''),
            'Business_Type': lead.get('business_type', '') or 'Other',
            'Lead Quality': quality_analysis['tier'],
            'Email_Confidence_Level': 'Real' if lead.get('verified') else 'Pattern'
        }
        
        # Clean empty fields
        return {k: v for k, v in fields.items() if v not in [None, '', 'Not specified']}
    
    def _update_airtable_record_with_retry(self, record_id: str, fields: Dict[str, Any]) -> bool:
        """Update Airtable record with retry logic"""
        
        for attempt in range(self.retry_attempts):
            try:
                update_data = {"fields": fields}
                response = requests.patch(f"{self.airtable_url}/{record_id}", 
                                        headers=self.headers, json=update_data)
                
                if response.status_code == 200:
                    return True
                elif response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limited, waiting {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(f"Failed to update record {record_id}: {response.status_code} - {response.text}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return False
                    
            except Exception as e:
                logger.error(f"Error updating record {record_id} (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False
        
        return False
    
    def _create_airtable_record_with_retry(self, fields: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Create Airtable record with retry logic"""
        
        for attempt in range(self.retry_attempts):
            try:
                create_data = {"fields": fields}
                response = requests.post(self.airtable_url, headers=self.headers, json=create_data)
                
                if response.status_code == 200:
                    record_id = response.json().get('id')
                    return True, record_id
                elif response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limited, waiting {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(f"Failed to create record: {response.status_code} - {response.text}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return False, None
                    
            except Exception as e:
                logger.error(f"Error creating record (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False, None
        
        return False, None
    
    def _mark_lead_as_synced(self, lead_id: str, airtable_id: Optional[str] = None):
        """Mark lead as successfully synced"""
        
        conn = sqlite3.connect(self.db_path)
        if airtable_id:
            conn.execute("""
                UPDATE leads 
                SET sync_status = 'synced', airtable_id = ?, updated_at = ? 
                WHERE id = ?
            """, (airtable_id, datetime.now().isoformat(), lead_id))
        else:
            conn.execute("""
                UPDATE leads 
                SET sync_status = 'synced', updated_at = ? 
                WHERE id = ?
            """, (datetime.now().isoformat(), lead_id))
        conn.commit()
        conn.close()
    
    def _get_existing_airtable_records(self) -> List[Dict[str, Any]]:
        """Get existing Airtable records"""
        
        try:
            response = requests.get(self.airtable_url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get('records', [])
            else:
                logger.error(f"Failed to get Airtable records: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting Airtable records: {e}")
            return []
    
    def _update_sync_stats(self, duration: float, success: bool):
        """Update sync performance statistics"""
        
        self.sync_stats['total_syncs'] += 1
        if success:
            self.sync_stats['successful_syncs'] += 1
        else:
            self.sync_stats['failed_syncs'] += 1
        
        self.sync_stats['last_sync_duration'] = duration
        
        # Calculate average duration
        if self.sync_stats['total_syncs'] > 0:
            self.sync_stats['avg_sync_duration'] = (
                (self.sync_stats['avg_sync_duration'] * (self.sync_stats['total_syncs'] - 1) + duration) /
                self.sync_stats['total_syncs']
            )
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics"""
        
        return {
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_interval': self.sync_interval,
            'stats': self.sync_stats,
            'next_sync_in': self.sync_interval - (time.time() - (self.last_sync_time.timestamp() if self.last_sync_time else 0))
        }
    
    def run_continuous_sync(self):
        """Run continuous sync in background (for EC2)"""
        
        logger.info("Starting continuous Airtable sync...")
        
        # Schedule sync every X minutes
        schedule.every(self.sync_interval // 60).minutes.do(self.sync_new_and_updated_leads)
        
        # Run initial sync
        self.sync_new_and_updated_leads()
        
        # Keep running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Continuous sync stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous sync: {e}")
                time.sleep(60)  # Wait before retrying


def main():
    """Main function for different run modes"""
    
    import sys
    
    sync_manager = AutomatedAirtableSync()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # Continuous mode for EC2
        print("🚀 Starting continuous Airtable sync for EC2...")
        sync_manager.run_continuous_sync()
    else:
        # One-time sync
        print("🔄 Running one-time Airtable sync...")
        results = sync_manager.sync_new_and_updated_leads()
        
        print(f"\\n✅ Sync Results:")
        print(f"Processed: {results['processed']} leads")
        print(f"Updated: {results['updated']} records")
        print(f"Created: {results['created']} records")
        print(f"Errors: {results['errors']}")
        
        if results['error_details']:
            print("\\nErrors:")
            for error in results['error_details'][:5]:
                print(f"  - {error}")


if __name__ == "__main__":
    main()
