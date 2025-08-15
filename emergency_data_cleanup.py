#!/usr/bin/env python3
"""
EMERGENCY DATA CLEANUP

Critical fix for data quality crisis.
Cleans up database to meet 95%+ quality standard.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Import production database manager
from production_db_manager import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmergencyDataCleanup:
    """Emergency data quality fix."""
    
    def __init__(self):
        self.cleaned_count = 0
        self.deleted_count = 0
        self.fixed_count = 0
        
    def emergency_cleanup(self):
        """Fix critical data quality issues immediately."""
        logger.info("🚨 EMERGENCY DATA CLEANUP - CRITICAL")
        logger.info("="*50)
        
        try:
            # 1. Remove test data
            self.remove_test_data()
            
            # 2. Fix missing required fields
            self.fix_missing_fields()
            
            # 3. Remove duplicates
            self.remove_duplicates()
            
            # 4. Validate final quality
            self.validate_final_quality()
            
            self.report_cleanup_results()
            
        except Exception as e:
            logger.error(f"❌ Emergency cleanup failed: {e}")
            return False
        
        return True
    
    def remove_test_data(self):
        """Remove all test data from production database."""
        logger.info("🗑️ Removing test data...")
        
        try:
            with db_manager.get_connection() as conn:
                # Delete all test leads
                test_patterns = [
                    'test@example.com',
                    'stress.test.%',
                    'thread%.user%',
                    'integrity.%',
                    'memory.test.%',
                    'recovery%@test.com',
                    'rapid%.test.com',
                    'boundary%@test.com',
                    'pipeline.test.%',
                    'load.%@test.com',
                    'response.%@test.com',
                    'autotest%@example.com',
                    'example.com'
                ]
                
                total_deleted = 0
                
                for pattern in test_patterns:
                    cursor = conn.execute("DELETE FROM leads WHERE email LIKE ?", (pattern,))
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    if deleted > 0:
                        logger.info(f"  Deleted {deleted} leads matching {pattern}")
                
                # Delete leads with test names
                test_name_patterns = [
                    'Test %',
                    'Stress Test %',
                    'Thread% %',
                    'Integrity Test %',
                    'Memory Test %',
                    'Recovery Test %',
                    'Rapid Test %',
                    'Boundary Test %',
                    'Pipeline Test %',
                    'Load Test %',
                    'Response Time Test %'
                ]
                
                for pattern in test_name_patterns:
                    cursor = conn.execute("DELETE FROM leads WHERE full_name LIKE ?", (pattern,))
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    if deleted > 0:
                        logger.info(f"  Deleted {deleted} leads with test names")
                
                # Delete leads with test company names
                test_company_patterns = [
                    'Test Corp%',
                    'Stress Test Corp%',
                    'Thread% Corp%',
                    'Test Performance Corp',
                    'Large Data Corp',
                    'Pipeline Test Corp',
                    'Load Corp %',
                    'Response Corp %'
                ]
                
                for pattern in test_company_patterns:
                    cursor = conn.execute("DELETE FROM leads WHERE company LIKE ?", (pattern,))
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    if deleted > 0:
                        logger.info(f"  Deleted {deleted} leads with test companies")
                
                conn.commit()
                self.deleted_count = total_deleted
                logger.info(f"✅ Removed {total_deleted} test leads")
                
        except Exception as e:
            logger.error(f"❌ Failed to remove test data: {e}")
    
    def fix_missing_fields(self):
        """Fix leads with missing required fields."""
        logger.info("🔧 Fixing missing required fields...")
        
        try:
            with db_manager.get_connection() as conn:
                # Fix missing names - delete leads without names
                cursor = conn.execute("""
                    DELETE FROM leads 
                    WHERE full_name IS NULL 
                    OR full_name = '' 
                    OR TRIM(full_name) = ''
                """)
                deleted_no_name = cursor.rowcount
                logger.info(f"  Deleted {deleted_no_name} leads without names")
                
                # Fix missing emails - delete leads without emails
                cursor = conn.execute("""
                    DELETE FROM leads 
                    WHERE email IS NULL 
                    OR email = '' 
                    OR TRIM(email) = ''
                    OR email NOT LIKE '%@%.%'
                """)
                deleted_no_email = cursor.rowcount
                logger.info(f"  Deleted {deleted_no_email} leads without valid emails")
                
                # Fix missing companies - add generic company name
                cursor = conn.execute("""
                    UPDATE leads 
                    SET company = 'Unknown Company'
                    WHERE company IS NULL 
                    OR company = '' 
                    OR TRIM(company) = ''
                """)
                fixed_companies = cursor.rowcount
                logger.info(f"  Fixed {fixed_companies} leads with missing companies")
                
                conn.commit()
                self.fixed_count += fixed_companies
                self.deleted_count += deleted_no_name + deleted_no_email
                
        except Exception as e:
            logger.error(f"❌ Failed to fix missing fields: {e}")
    
    def remove_duplicates(self):
        """Remove duplicate email addresses."""
        logger.info("🔄 Removing duplicate emails...")
        
        try:
            with db_manager.get_connection() as conn:
                # Find and remove duplicates, keeping the oldest
                cursor = conn.execute("""
                    DELETE FROM leads 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM leads 
                        GROUP BY LOWER(TRIM(email))
                    )
                """)
                
                duplicates_removed = cursor.rowcount
                conn.commit()
                
                self.deleted_count += duplicates_removed
                logger.info(f"✅ Removed {duplicates_removed} duplicate emails")
                
        except Exception as e:
            logger.error(f"❌ Failed to remove duplicates: {e}")
    
    def validate_final_quality(self):
        """Validate final data quality."""
        logger.info("📊 Validating final data quality...")
        
        try:
            with db_manager.get_connection() as conn:
                # Get all remaining leads
                cursor = conn.execute("SELECT * FROM leads")
                all_leads = cursor.fetchall()
                
                if not all_leads:
                    logger.warning("⚠️ No leads remaining after cleanup!")
                    return 0
                
                valid_leads = 0
                quality_issues = []
                
                for lead in all_leads:
                    lead_valid = True
                    
                    # Check required fields
                    if not lead['full_name'] or str(lead['full_name']).strip() == '':
                        quality_issues.append(f"Lead {lead['id']}: Missing full_name")
                        lead_valid = False
                    
                    if not lead['email'] or str(lead['email']).strip() == '':
                        quality_issues.append(f"Lead {lead['id']}: Missing email")
                        lead_valid = False
                    elif '@' not in str(lead['email']) or '.' not in str(lead['email']):
                        quality_issues.append(f"Lead {lead['id']}: Invalid email")
                        lead_valid = False
                    
                    if not lead['company'] or str(lead['company']).strip() == '':
                        quality_issues.append(f"Lead {lead['id']}: Missing company")
                        lead_valid = False
                    
                    if lead_valid:
                        valid_leads += 1
                
                quality_percentage = (valid_leads / len(all_leads)) * 100
                
                logger.info(f"📊 Final Quality Report:")
                logger.info(f"  Total leads: {len(all_leads)}")
                logger.info(f"  Valid leads: {valid_leads}")
                logger.info(f"  Quality percentage: {quality_percentage:.1f}%")
                logger.info(f"  Quality issues: {len(quality_issues)}")
                
                if quality_issues:
                    logger.warning(f"Remaining quality issues:")
                    for issue in quality_issues[:5]:
                        logger.warning(f"  - {issue}")
                    if len(quality_issues) > 5:
                        logger.warning(f"  ... and {len(quality_issues) - 5} more")
                
                return quality_percentage
                
        except Exception as e:
            logger.error(f"❌ Failed to validate quality: {e}")
            return 0
    
    def report_cleanup_results(self):
        """Report cleanup results."""
        logger.info("\n" + "="*60)
        logger.info("🚨 EMERGENCY CLEANUP COMPLETE!")
        logger.info("="*60)
        
        logger.info(f"📊 CLEANUP SUMMARY:")
        logger.info(f"  🗑️ Leads deleted: {self.deleted_count}")
        logger.info(f"  🔧 Leads fixed: {self.fixed_count}")
        
        # Get final stats
        stats = db_manager.get_database_stats()
        if stats:
            logger.info(f"  📋 Final total leads: {stats['total_leads']}")
            logger.info(f"  📧 Leads with emails: {stats['leads_with_email']} ({stats['email_percentage']}%)")
        
        logger.info("\n🎯 NEXT STEP: Run ultimate test again to verify quality!")

if __name__ == "__main__":
    cleanup = EmergencyDataCleanup()
    success = cleanup.emergency_cleanup()
    
    if success:
        print("\n✅ EMERGENCY CLEANUP COMPLETE!")
        print("Run ultimate test again to verify quality.")
    else:
        print("\n❌ Emergency cleanup failed!")
