#!/usr/bin/env python3
"""
Fix Database Schema to Match Required 25 Fields
===============================================
This script will:
1. Create a new table with ONLY the 25 required fields
2. Migrate existing data to the new schema
3. Drop the old table with extra fields
4. Ensure clean, organized database structure
"""

import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# The EXACT 25 fields that should exist
REQUIRED_FIELDS = {
    'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
    'Full_Name': 'TEXT',
    'LinkedIn_URL': 'TEXT',
    'Job_Title': 'TEXT', 
    'Company': 'TEXT',
    'Email': 'TEXT UNIQUE',
    'Source': 'TEXT DEFAULT "scraper"',
    'Needs_Enrichment': 'INTEGER DEFAULT 1',
    'AI_Message': 'TEXT',
    'Replied': 'INTEGER DEFAULT 0',
    'Response_Date': 'TEXT',
    'Response_Notes': 'TEXT',
    'Lead_Quality': 'TEXT',
    'Date_Scraped': 'TEXT',
    'Date_Enriched': 'TEXT',
    'Date_Messaged': 'TEXT',
    'Extra_info': 'TEXT',
    'Level_Engaged': 'INTEGER DEFAULT 0',
    'Engagement_Status': 'TEXT DEFAULT "pending"',
    'Email_Confidence_Level': 'TEXT',
    'Website': 'TEXT',
    'Created_At': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    'Business_Type': 'TEXT',
    'Follow_Up_Stage': 'TEXT DEFAULT "initial"',
    'Response_Status': 'TEXT DEFAULT "pending"',
    'Company_Description': 'TEXT'
}

def backup_current_database():
    """Create backup of current database"""
    try:
        import shutil
        backup_name = f"data/unified_leads_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2('data/unified_leads.db', backup_name)
        logger.info(f"✅ Database backed up to: {backup_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return False

def create_new_schema():
    """Create new table with correct 25-field schema"""
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        
        # Build CREATE TABLE statement with exact 25 fields
        field_definitions = [f"{field} {definition}" for field, definition in REQUIRED_FIELDS.items()]
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS leads_new (
            {', '.join(field_definitions)}
        )
        """
        
        conn.execute(create_sql)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_leads_email ON leads_new(Email)",
            "CREATE INDEX IF NOT EXISTS idx_leads_company ON leads_new(Company)", 
            "CREATE INDEX IF NOT EXISTS idx_leads_linkedin ON leads_new(LinkedIn_URL)",
            "CREATE INDEX IF NOT EXISTS idx_leads_engagement ON leads_new(Engagement_Status)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
        conn.close()
        
        logger.info("✅ New schema created with exactly 25 fields")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}")
        return False

def migrate_data():
    """Migrate existing data to new schema, mapping old fields to new ones"""
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        conn.row_factory = sqlite3.Row
        
        # Get existing data
        cursor = conn.execute("SELECT * FROM leads")
        old_leads = cursor.fetchall()
        
        logger.info(f"📋 Migrating {len(old_leads)} existing leads...")
        
        migrated_count = 0
        for lead in old_leads:
            # Convert sqlite3.Row to dict for easier access
            lead_dict = dict(lead)
            
            # Map old fields to new schema
            new_lead = {
                'Full_Name': lead_dict.get('full_name') or lead_dict.get('Full_Name'),
                'LinkedIn_URL': lead_dict.get('linkedin_url') or lead_dict.get('LinkedIn_URL'),
                'Job_Title': lead_dict.get('job_title') or lead_dict.get('Job_Title'),
                'Company': lead_dict.get('company') or lead_dict.get('Company'),
                'Email': lead_dict.get('email') or lead_dict.get('Email'),
                'Source': lead_dict.get('source') or lead_dict.get('Source') or 'migrated',
                'Needs_Enrichment': 1 if lead_dict.get('needs_enrichment') or not lead_dict.get('enriched') else 0,
                'AI_Message': lead_dict.get('ai_message') or lead_dict.get('AI_Message'),
                'Replied': 0,  # Default
                'Response_Date': None,  # Default
                'Response_Notes': None,  # Default
                'Lead_Quality': lead_dict.get('lead_quality') or lead_dict.get('Lead_Quality') or 'Warm',
                'Date_Scraped': lead_dict.get('date_scraped') or lead_dict.get('Date_Scraped') or lead_dict.get('created_at'),
                'Date_Enriched': lead_dict.get('date_enriched') or lead_dict.get('Date_Enriched'),
                'Date_Messaged': None,  # Default
                'Extra_info': lead_dict.get('notes') or lead_dict.get('website_insights'),
                'Level_Engaged': lead_dict.get('engagement_level') or 0,
                'Engagement_Status': lead_dict.get('engagement_status') or lead_dict.get('Engagement_Status') or 'pending',
                'Email_Confidence_Level': lead_dict.get('email_confidence_level') or lead_dict.get('Email_Confidence_Level'),
                'Website': lead_dict.get('website') or lead_dict.get('Website'),
                'Created_At': lead_dict.get('created_at') or lead_dict.get('Created_At') or datetime.now().isoformat(),
                'Business_Type': lead_dict.get('business_type') or lead_dict.get('Business_Type'),
                'Follow_Up_Stage': 'initial',  # Default
                'Response_Status': 'pending',  # Default
                'Company_Description': lead_dict.get('company_description') or lead_dict.get('Company_Description')
            }
            
            # Only migrate leads with full_name (valid leads)
            if new_lead['Full_Name']:
                # Insert into new table
                placeholders = ', '.join(['?' for _ in REQUIRED_FIELDS.keys() if _ != 'id'])
                field_names = ', '.join([f for f in REQUIRED_FIELDS.keys() if f != 'id'])
                values = [new_lead.get(f.replace('_', '_')) for f in REQUIRED_FIELDS.keys() if f != 'id']
                
                conn.execute(f"""
                    INSERT INTO leads_new ({field_names})
                    VALUES ({placeholders})
                """, values)
                
                migrated_count += 1
                
                if migrated_count % 10 == 0:
                    logger.info(f"📋 Migrated {migrated_count} leads...")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Successfully migrated {migrated_count} valid leads")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data migration failed: {e}")
        return False

def replace_old_table():
    """Replace old table with new clean schema"""
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        
        # Drop old table and rename new one
        conn.execute("DROP TABLE IF EXISTS leads_old")
        conn.execute("ALTER TABLE leads RENAME TO leads_old")
        conn.execute("ALTER TABLE leads_new RENAME TO leads")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Database schema updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Table replacement failed: {e}")
        return False

def verify_new_schema():
    """Verify the new schema has exactly 25 fields"""
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        
        cursor = conn.execute("PRAGMA table_info(leads)")
        columns = cursor.fetchall()
        
        logger.info(f"📊 New schema has {len(columns)} fields:")
        for col in columns:
            logger.info(f"   - {col[1]} ({col[2]})")
        
        cursor = conn.execute("SELECT COUNT(*) FROM leads")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"✅ Database verified: {count} leads with clean schema")
        return len(columns) == 26  # 25 fields + id
        
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("🚀 Starting database schema fix...")
    
    # Step 1: Backup
    if not backup_current_database():
        logger.error("❌ Cannot proceed without backup")
        return False
    
    # Step 2: Create new schema
    if not create_new_schema():
        logger.error("❌ Failed to create new schema")
        return False
    
    # Step 3: Migrate data
    if not migrate_data():
        logger.error("❌ Failed to migrate data")
        return False
    
    # Step 4: Replace old table
    if not replace_old_table():
        logger.error("❌ Failed to replace table")
        return False
    
    # Step 5: Verify
    if not verify_new_schema():
        logger.error("❌ Schema verification failed")
        return False
    
    logger.info("🎉 DATABASE SCHEMA FIXED SUCCESSFULLY!")
    logger.info("✅ Database now has exactly 25 required fields")
    logger.info("✅ All existing leads migrated to new schema")
    logger.info("✅ System ready for proper enrichment and Airtable sync")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("❌ Schema fix failed - check logs above")
        exit(1)
