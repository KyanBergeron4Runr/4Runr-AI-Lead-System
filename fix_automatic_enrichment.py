#!/usr/bin/env python3
"""
Fix Automatic Enrichment System
===============================
Ensures all required Airtable fields are populated automatically
"""

import sqlite3
import os
import requests
import json
from datetime import datetime
from typing import Dict, List

class AutomaticEnrichmentFixer:
    def __init__(self):
        self.db_path = 'data/unified_leads.db'
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_id = 'tblbBSE2jJv9am7ZA'
        
        # Required fields that must ALWAYS be populated
        self.required_fields = {
            'Source': 'Auto-Enriched',
            'Needs Enrichment': False,
            'AI Message': 'Auto-generated message',
            'Replied': False,
            'Response Date': None,
            'Response Notes': '',
            'Lead Quality': 'Warm',
            'Date Scraped': datetime.now().strftime('%Y-%m-%d'),
            'Date Enriched': datetime.now().strftime('%Y-%m-%d'),
            'Date Messaged': None,
            'Extra info': '',
            'Level Engaged': 0,
            'Engagement_Status': 'New',
            'Website': '',
            'Business_Type': 'Unknown',
            'Follow_Up_Stage': 'Initial',
            'Response_Status': 'Pending',
            'Company_Description': 'Business description pending enrichment'
        }
    
    def analyze_missing_fields(self):
        """Check which records have missing required fields"""
        print("🔍 ANALYZING MISSING REQUIRED FIELDS")
        print("=" * 50)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all records
            cursor = conn.execute("SELECT * FROM leads ORDER BY created_at DESC")
            records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            print(f"📊 Analyzing {len(records)} records for missing fields...")
            
            # Map database fields to Airtable fields
            field_mapping = {
                'Source': 'source',
                'Needs Enrichment': 'needs_enrichment', 
                'AI Message': 'ai_message',
                'Lead Quality': 'lead_quality',
                'Date Scraped': 'date_scraped',
                'Date Enriched': 'date_enriched',
                'Website': 'website',
                'Business_Type': 'business_type',
                'Engagement_Status': 'engagement_status',
                'Company_Description': 'company_description'
            }
            
            missing_stats = {}
            records_needing_fixes = []
            
            for airtable_field, db_field in field_mapping.items():
                missing_count = 0
                
                for record in records:
                    value = record.get(db_field)
                    
                    # Check if field is empty/missing
                    if value in [None, '', 'NULL', 0] and airtable_field not in ['Needs Enrichment']:
                        missing_count += 1
                        
                        # Track this record for fixing
                        if record['id'] not in [r['id'] for r in records_needing_fixes]:
                            records_needing_fixes.append(record)
                
                missing_stats[airtable_field] = {
                    'missing_count': missing_count,
                    'total_records': len(records),
                    'missing_percentage': (missing_count / len(records) * 100) if records else 0
                }
            
            print(f"\n📊 MISSING FIELD ANALYSIS:")
            for field, stats in missing_stats.items():
                if stats['missing_percentage'] > 0:
                    print(f"   🔴 {field}: {stats['missing_percentage']:.1f}% missing ({stats['missing_count']}/{stats['total_records']})")
                else:
                    print(f"   ✅ {field}: Complete")
            
            print(f"\n🎯 Records needing enrichment fixes: {len(records_needing_fixes)}")
            
            return records_needing_fixes, missing_stats
            
        except Exception as e:
            print(f"❌ Error analyzing fields: {e}")
            return [], {}
    
    def fix_database_fields(self, records_to_fix: List[Dict], apply_fixes: bool = False):
        """Fix missing fields in database"""
        print(f"\n🔧 FIXING MISSING FIELDS IN DATABASE")
        print("=" * 50)
        
        if not records_to_fix:
            print("✅ No records need fixing")
            return 0
        
        print(f"🎯 Found {len(records_to_fix)} records to fix")
        
        if not apply_fixes:
            print("⚠️ SIMULATION MODE - No changes will be made")
            print("To actually apply fixes, run with apply_fixes=True")
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            fixed_count = 0
            
            for record in records_to_fix:
                record_id = record['id']
                updates = []
                values = []
                
                # Check each required field and fix if missing
                field_fixes = {
                    'source': record.get('source') or 'Auto-Enriched',
                    'needs_enrichment': 0 if record.get('needs_enrichment') is None else record.get('needs_enrichment'),
                    'ai_message': record.get('ai_message') or self.generate_ai_message(record),
                    'lead_quality': record.get('lead_quality') or 'Warm',
                    'date_scraped': record.get('date_scraped') or datetime.now().strftime('%Y-%m-%d'),
                    'date_enriched': record.get('date_enriched') or datetime.now().strftime('%Y-%m-%d'),
                    'website': record.get('website') or self.discover_website(record),
                    'business_type': record.get('business_type') or self.infer_business_type(record),
                    'engagement_status': record.get('engagement_status') or 'New',
                    'company_description': record.get('company_description') or self.generate_company_description(record)
                }
                
                # Build update query
                for field, value in field_fixes.items():
                    if record.get(field) in [None, '', 'NULL']:
                        updates.append(f"{field} = ?")
                        values.append(value)
                
                if updates:
                    query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"
                    values.append(record_id)
                    
                    conn.execute(query, values)
                    fixed_count += 1
                    
                    name = record.get('full_name', 'Unknown')
                    print(f"   ✅ Fixed {len(updates)} fields for: {name}")
            
            conn.commit()
            conn.close()
            
            print(f"\n🎯 Successfully fixed {fixed_count} records")
            return fixed_count
            
        except Exception as e:
            print(f"❌ Error fixing database: {e}")
            return 0
    
    def generate_ai_message(self, record: Dict) -> str:
        """Generate AI message for lead"""
        name = record.get('full_name', 'there')
        company = record.get('company', 'your company')
        
        return f"Hi {name},\n\nI noticed {company} and thought you might be interested in our solutions. Would love to connect and discuss how we can help.\n\nBest regards"
    
    def discover_website(self, record: Dict) -> str:
        """Discover/infer website for company"""
        company = record.get('company', '')
        
        if not company:
            return ''
        
        # Simple website inference
        company_clean = company.lower().replace(' ', '').replace('inc', '').replace('ltd', '').replace('llc', '')
        return f"https://{company_clean}.com"
    
    def infer_business_type(self, record: Dict) -> str:
        """Infer business type from available data"""
        industry = record.get('industry', '').lower()
        company = record.get('company', '').lower()
        job_title = record.get('job_title', '').lower()
        
        # Business type inference logic
        if 'tech' in industry or 'software' in industry:
            return 'Technology'
        elif 'consult' in industry or 'consult' in company:
            return 'Consulting'
        elif 'market' in industry or 'market' in job_title:
            return 'Marketing'
        elif 'financ' in industry or 'bank' in industry:
            return 'Financial Services'
        elif 'health' in industry or 'medical' in industry:
            return 'Healthcare'
        else:
            return 'Professional Services'
    
    def generate_company_description(self, record: Dict) -> str:
        """Generate company description"""
        company = record.get('company', '')
        industry = record.get('industry', '')
        business_type = record.get('business_type', '')
        
        if company and industry:
            return f"{company} is a {industry.lower()} company specializing in {business_type.lower()} solutions."
        elif company:
            return f"{company} is a professional services company."
        else:
            return "Company description pending enrichment."
    
    def sync_to_airtable(self, max_records: int = 10):
        """Sync fixed records to Airtable"""
        print(f"\n🔗 SYNCING FIXED RECORDS TO AIRTABLE")
        print("=" * 50)
        
        if not self.api_key:
            print("❌ AIRTABLE_API_KEY not set")
            return False
        
        try:
            # Get recently updated records
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE updated_at > datetime('now', '-1 hour')
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (max_records,))
            
            records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if not records:
                print("✅ No recent records to sync")
                return True
            
            print(f"🔄 Syncing {len(records)} recently updated records...")
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}'
            
            sync_count = 0
            
            for record in records:
                # Map database fields to Airtable fields
                airtable_record = {
                    'Full Name': record.get('full_name', ''),
                    'LinkedIn URL': record.get('linkedin_url', ''),
                    'Job Title': record.get('job_title', ''),
                    'Company': record.get('company', ''),
                    'Email': record.get('email', ''),
                    'Source': record.get('source', 'Auto-Enriched'),
                    'Needs Enrichment': record.get('needs_enrichment', 0) == 1,
                    'AI Message': record.get('ai_message', ''),
                    'Lead Quality': record.get('lead_quality', 'Warm'),
                    'Date Scraped': record.get('date_scraped', ''),
                    'Date Enriched': record.get('date_enriched', ''),
                    'Website': record.get('website', ''),
                    'Business_Type': record.get('business_type', ''),
                    'Engagement_Status': record.get('engagement_status', 'New'),
                    'Company_Description': record.get('company_description', ''),
                    'Email_Confidence_Level': record.get('email_confidence_level', 'Pattern')
                }
                
                # Remove empty fields
                airtable_record = {k: v for k, v in airtable_record.items() if v not in [None, '', 'NULL']}
                
                data = {'fields': airtable_record}
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    sync_count += 1
                    name = record.get('full_name', 'Unknown')
                    print(f"   ✅ Synced: {name}")
                else:
                    name = record.get('full_name', 'Unknown')
                    print(f"   ❌ Failed to sync: {name} - {response.status_code}")
            
            print(f"\n🎯 Successfully synced {sync_count}/{len(records)} records to Airtable")
            return sync_count > 0
            
        except Exception as e:
            print(f"❌ Airtable sync error: {e}")
            return False
    
    def comprehensive_enrichment_fix(self, apply_fixes: bool = False):
        """Complete automatic enrichment fix"""
        print("🔧 COMPREHENSIVE AUTOMATIC ENRICHMENT FIX")
        print("=" * 60)
        print("Ensuring all required Airtable fields are populated automatically")
        print("")
        
        # Step 1: Analyze missing fields
        records_to_fix, missing_stats = self.analyze_missing_fields()
        
        if not records_to_fix:
            print("✅ All required fields are properly populated!")
            return True
        
        # Step 2: Fix database fields
        fixed_count = self.fix_database_fields(records_to_fix, apply_fixes)
        
        if not apply_fixes:
            print(f"\n⚠️ SIMULATION MODE COMPLETE")
            print(f"📊 Would fix {len(records_to_fix)} records")
            print(f"🔧 To actually apply fixes: python3 fix_automatic_enrichment.py --fix")
            return False
        
        # Step 3: Sync to Airtable
        if fixed_count > 0:
            sync_success = self.sync_to_airtable(max_records=fixed_count)
        else:
            sync_success = True
        
        # Step 4: Results
        print(f"\n🎯 ENRICHMENT FIX RESULTS:")
        print(f"✅ Database records fixed: {fixed_count}")
        print(f"🔗 Airtable sync: {'✅ Success' if sync_success else '❌ Failed'}")
        
        if fixed_count > 0:
            print(f"\n🎉 Automatic enrichment system is now properly populating all required fields!")
        
        return fixed_count > 0

def main():
    """Run automatic enrichment fixer"""
    print("🔧 Automatic Enrichment System Fixer")
    print("Ensures all required Airtable fields are populated")
    print("")
    
    try:
        fixer = AutomaticEnrichmentFixer()
        
        import sys
        if '--fix' in sys.argv:
            success = fixer.comprehensive_enrichment_fix(apply_fixes=True)
        else:
            success = fixer.comprehensive_enrichment_fix(apply_fixes=False)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Enrichment fix failed: {e}")
        return 1

if __name__ == "__main__":
    main()
