#!/usr/bin/env python3
"""
Database Schema Upgrade - Add ALL missing fields to match Airtable
"""

import sqlite3
from datetime import datetime

def upgrade_database_schema():
    """Add all missing fields to the leads table"""
    
    conn = sqlite3.connect('data/unified_leads.db')
    cursor = conn.cursor()
    
    print("🔧 Upgrading database schema to match Airtable fields...")
    
    # Get current columns
    cursor.execute("PRAGMA table_info(leads)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Define all required fields to match your Airtable
    required_fields = {
        # Basic fields (already exist)
        'id': 'TEXT PRIMARY KEY',
        'full_name': 'TEXT',
        'email': 'TEXT',
        'company': 'TEXT',
        'linkedin_url': 'TEXT',
        'website': 'TEXT',
        'ai_message': 'TEXT',
        'business_type': 'TEXT',
        'company_description': 'TEXT',
        'created_at': 'DATETIME',
        'updated_at': 'DATETIME',
        
        # Missing fields that need to be added
        'job_title': 'TEXT',
        'source': 'TEXT DEFAULT "Search"',
        'needs_enrichment': 'BOOLEAN DEFAULT 1',
        'replied': 'BOOLEAN DEFAULT 0',
        'response_date': 'DATE',
        'response_notes': 'TEXT',
        'lead_quality': 'TEXT DEFAULT "Cold"',
        'date_scraped': 'DATE',
        'date_enriched': 'DATE',
        'date_messaged': 'DATE',
        'extra_info': 'TEXT',
        'level_engaged': 'TEXT DEFAULT "1st degree"',
        'engagement_status': 'TEXT DEFAULT "Needs Review"',
        'email_confidence_level': 'TEXT DEFAULT "Pattern"',
        'follow_up_stage': 'TEXT DEFAULT "Initial Contact"',
        'response_status': 'TEXT DEFAULT "Pending"',
        
        # Additional enrichment fields
        'phone': 'TEXT',
        'industry': 'TEXT',
        'location': 'TEXT',
        'company_size': 'TEXT',
        'revenue': 'TEXT',
        'verified': 'BOOLEAN DEFAULT 0',
        'enriched': 'BOOLEAN DEFAULT 0',
        'score': 'INTEGER DEFAULT 0',
        'engagement_level': 'INTEGER DEFAULT 1',
        'contact_attempts': 'INTEGER DEFAULT 0',
        'follow_up_count': 'INTEGER DEFAULT 0',
        'follow_up_date': 'DATE',
        'last_engagement_date': 'DATETIME',
        'engagement_notes': 'TEXT',
        'notes': 'TEXT',
        'tags': 'TEXT',
        'scraped_at': 'DATETIME',
        'message_generated_at': 'DATETIME',
        'airtable_id': 'TEXT',
        'sync_status': 'TEXT DEFAULT "pending"'
    }
    
    # Add missing columns
    added_fields = []
    for field_name, field_type in required_fields.items():
        if field_name not in existing_columns:
            try:
                alter_sql = f"ALTER TABLE leads ADD COLUMN {field_name} {field_type}"
                cursor.execute(alter_sql)
                added_fields.append(field_name)
                print(f"✅ Added field: {field_name}")
            except sqlite3.Error as e:
                print(f"❌ Failed to add {field_name}: {e}")
    
    if not added_fields:
        print("✅ All fields already exist in database")
    else:
        print(f"✅ Added {len(added_fields)} new fields to database")
    
    conn.commit()
    conn.close()
    
    return added_fields

def populate_missing_dates():
    """Populate missing dates based on existing data"""
    
    conn = sqlite3.connect('data/unified_leads.db')
    
    print("\n📅 Populating missing dates...")
    
    # Update date_scraped = created_at if missing
    cursor = conn.execute("""
        UPDATE leads 
        SET date_scraped = DATE(created_at)
        WHERE date_scraped IS NULL AND created_at IS NOT NULL
    """)
    scraped_count = cursor.rowcount
    
    # Update date_enriched = updated_at if enriched
    cursor = conn.execute("""
        UPDATE leads 
        SET date_enriched = DATE(updated_at)
        WHERE date_enriched IS NULL AND updated_at IS NOT NULL AND enriched = 1
    """)
    enriched_count = cursor.rowcount
    
    # Update date_messaged = updated_at if AI message exists
    cursor = conn.execute("""
        UPDATE leads 
        SET date_messaged = DATE(updated_at)
        WHERE date_messaged IS NULL AND ai_message IS NOT NULL AND ai_message != ''
    """)
    messaged_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {scraped_count} date_scraped fields")
    print(f"✅ Updated {enriched_count} date_enriched fields") 
    print(f"✅ Updated {messaged_count} date_messaged fields")

def calculate_lead_quality_scores():
    """Calculate and update lead quality scores for all leads"""
    
    conn = sqlite3.connect('data/unified_leads.db')
    conn.row_factory = sqlite3.Row
    
    print("\n🎯 Calculating lead quality scores...")
    
    cursor = conn.execute("SELECT * FROM leads WHERE ai_message IS NOT NULL")
    leads = cursor.fetchall()
    
    updated_count = 0
    
    for lead in leads:
        score = 0
        factors = []
        
        # Email Quality (35 points)
        if lead['verified']:
            score += 30
            factors.append("Verified email")
        elif lead['email'] and '@' in lead['email']:
            domain = lead['email'].split('@')[1] if '@' in lead['email'] else ''
            if domain and not any(provider in domain.lower() for provider in ['gmail', 'yahoo', 'hotmail']):
                score += 25
                factors.append("Corporate email")
            else:
                score += 15
                factors.append("Personal email")
        
        # Company Data (25 points)
        if lead['company']: 
            score += 5
            factors.append("Company name")
        if lead['industry']: 
            score += 5
            factors.append("Industry data")
        if lead['company_size']: 
            score += 5
            factors.append("Company size")
        if lead['website']: 
            score += 5
            factors.append("Website")
        if lead['company_description']: 
            score += 5
            factors.append("Description")
        
        # Engagement Potential (25 points)
        if lead['linkedin_url']: 
            score += 10
            factors.append("LinkedIn profile")
        if lead['ai_message'] and len(lead['ai_message']) > 200: 
            score += 15
            factors.append("Quality AI message")
        
        # Data Completeness (15 points)
        if lead['enriched']: 
            score += 10
            factors.append("Enriched data")
        if lead['business_type']: 
            score += 5
            factors.append("Business type")
        
        # Determine quality tier
        if score >= 80:
            quality = "Hot"
        elif score >= 60:
            quality = "Warm"
        else:
            quality = "Cold"
        
        # Update confidence level
        confidence = "Real" if lead['verified'] else "Pattern"
        
        # Create extra info
        extra_info = f"Quality Score: {score}\\nFactors: {', '.join(factors[:3])}\\nIndustry: {lead['industry'] or 'N/A'}\\nLocation: {lead['location'] or 'N/A'}\\nCompany Size: {lead['company_size'] or 'N/A'}"
        
        # Update the record
        conn.execute("""
            UPDATE leads 
            SET score = ?, lead_quality = ?, email_confidence_level = ?, extra_info = ?,
                needs_enrichment = ?, response_status = ?
            WHERE id = ?
        """, (score, quality, confidence, extra_info, 
              0 if lead['enriched'] else 1,
              "Received" if lead['response_received'] else "Pending",
              lead['id']))
        
        updated_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated quality scores for {updated_count} leads")

if __name__ == "__main__":
    print("🚀 DATABASE SCHEMA UPGRADE & DATA POPULATION")
    print("=" * 50)
    
    # 1. Upgrade schema
    added_fields = upgrade_database_schema()
    
    # 2. Populate dates
    populate_missing_dates()
    
    # 3. Calculate quality scores
    calculate_lead_quality_scores()
    
    print("\n✅ DATABASE UPGRADE COMPLETE!")
    print("Now your database has ALL fields needed for Airtable sync")
    print("Run the sync again to see all fields populated!")
