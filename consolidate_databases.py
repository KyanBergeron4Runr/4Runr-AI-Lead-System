#!/usr/bin/env python3
import sqlite3
import os
import shutil
from datetime import datetime

def consolidate_databases():
    print("🔧 DATABASE CONSOLIDATION SCRIPT")
    print("=" * 60)
    
    # Define the primary database (largest one)
    primary_db = 'data/unified_leads.db'
    
    # Define source databases to merge
    source_databases = [
        '4runr-lead-scraper/data/leads.db',
        'data/leads.db',
        '4runr-outreach-system/data/leads_cache.db'
    ]
    
    # Backup the primary database first
    backup_path = f'backup_primary_db_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copy2(primary_db, backup_path)
    print(f"✅ Backed up primary database to: {backup_path}")
    
    # Connect to primary database
    primary_conn = sqlite3.connect(primary_db)
    primary_conn.row_factory = sqlite3.Row
    
    # Get existing leads in primary database
    cursor = primary_conn.execute("SELECT full_name, email, linkedin_url FROM leads")
    existing_leads = {(row['full_name'], row['email'], row['linkedin_url']) for row in cursor.fetchall()}
    print(f"📊 Primary database has {len(existing_leads)} existing leads")
    
    total_imported = 0
    duplicates_skipped = 0
    
    for source_db in source_databases:
        if not os.path.exists(source_db):
            print(f"❌ Source database not found: {source_db}")
            continue
            
        print(f"\n🔍 Processing: {source_db}")
        
        try:
            source_conn = sqlite3.connect(source_db)
            source_conn.row_factory = sqlite3.Row
            
            # Check if leads table exists
            cursor = source_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            if not cursor.fetchone():
                print(f"   ❌ No 'leads' table found")
                source_conn.close()
                continue
            
            # Get all leads from source
            cursor = source_conn.execute("SELECT * FROM leads")
            source_leads = cursor.fetchall()
            print(f"   📊 Found {len(source_leads)} leads")
            
            imported_count = 0
            for lead in source_leads:
                # Convert to dict for easier handling
                lead_dict = dict(lead)
                
                # Standardize key fields for duplicate detection
                full_name = lead_dict.get('full_name') or lead_dict.get('name', '')
                email = lead_dict.get('email', '')
                linkedin_url = lead_dict.get('linkedin_url', '')
                
                # Check for duplicates
                lead_key = (full_name, email, linkedin_url)
                if lead_key in existing_leads:
                    duplicates_skipped += 1
                    continue
                
                # Map source fields to primary database schema
                mapped_lead = {
                    'full_name': full_name,
                    'email': email,
                    'linkedin_url': linkedin_url,
                    'company': lead_dict.get('company', ''),
                    'job_title': lead_dict.get('job_title') or lead_dict.get('title', ''),
                    'website': lead_dict.get('website') or lead_dict.get('company_website', ''),
                    'ai_message': lead_dict.get('ai_message', ''),
                    'company_description': lead_dict.get('company_description', ''),
                    'response_status': lead_dict.get('response_status') or 'pending',
                    'created_at': lead_dict.get('created_at') or datetime.now().isoformat(),
                    'source': f'imported_from_{os.path.basename(source_db)}'
                }
                
                # Insert into primary database
                try:
                    primary_conn.execute("""
                        INSERT INTO leads (
                            full_name, email, linkedin_url, company, job_title, 
                            website, ai_message, company_description, response_status, 
                            created_at, source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        mapped_lead['full_name'],
                        mapped_lead['email'], 
                        mapped_lead['linkedin_url'],
                        mapped_lead['company'],
                        mapped_lead['job_title'],
                        mapped_lead['website'],
                        mapped_lead['ai_message'],
                        mapped_lead['company_description'],
                        mapped_lead['response_status'],
                        mapped_lead['created_at'],
                        mapped_lead['source']
                    ))
                    
                    imported_count += 1
                    total_imported += 1
                    existing_leads.add(lead_key)
                    
                except Exception as e:
                    print(f"   ⚠️ Error importing lead {full_name}: {e}")
            
            print(f"   ✅ Imported {imported_count} new leads")
            source_conn.close()
            
        except Exception as e:
            print(f"   ❌ Error processing database: {e}")
    
    # Commit all changes
    primary_conn.commit()
    
    # Get final count
    cursor = primary_conn.execute("SELECT COUNT(*) FROM leads")
    final_count = cursor.fetchone()[0]
    
    primary_conn.close()
    
    print(f"\n🎉 CONSOLIDATION COMPLETE!")
    print(f"   📊 Total leads imported: {total_imported}")
    print(f"   🔄 Duplicates skipped: {duplicates_skipped}")
    print(f"   📈 Final database size: {final_count} leads")
    print(f"   💾 Backup created: {backup_path}")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Update all system components to use: {primary_db}")
    print(f"   2. Test autonomous system with consolidated database")
    print(f"   3. Force sync ALL {final_count} leads to Airtable")
    
    return final_count

if __name__ == "__main__":
    consolidate_databases()
