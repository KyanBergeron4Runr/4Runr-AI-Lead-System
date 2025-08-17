#!/usr/bin/env python3
"""
Pull Clean Leads from Airtable
==============================
Downloads all leads from Airtable, cleans them up, and populates the database.
Much better than trying to fix fake generated data!
"""

import sqlite3
import requests
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

class AirtableLeadPuller:
    def __init__(self, db_path='data/unified_leads.db'):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_id = 'tblbBSE2jJv9am7ZA'
        self.db_path = db_path
        
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY environment variable not set")
    
    def pull_all_airtable_records(self) -> List[Dict]:
        """Pull all records from Airtable"""
        print("📊 Pulling all records from Airtable...")
        
        url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}'
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        all_records = []
        offset = None
        
        while True:
            params = {}
            if offset:
                params['offset'] = offset
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"❌ Error fetching Airtable records: {response.status_code}")
                print(f"Response: {response.text}")
                break
                
            data = response.json()
            records = data.get('records', [])
            all_records.extend(records)
            
            print(f"   📋 Pulled {len(records)} records (total: {len(all_records)})")
            
            offset = data.get('offset')
            if not offset:
                break
        
        print(f"✅ Successfully pulled {len(all_records)} total records from Airtable")
        return all_records
    
    def clean_airtable_record(self, airtable_record: Dict) -> Optional[Dict]:
        """Clean and validate an Airtable record"""
        fields = airtable_record.get('fields', {})
        record_id = airtable_record.get('id', '')
        
        # Extract and clean fields
        full_name = str(fields.get('Full Name', '')).strip()
        linkedin_url = str(fields.get('LinkedIn URL', '')).strip()
        job_title = str(fields.get('Job Title', '')).strip()
        company = str(fields.get('Company', '')).strip()
        email = str(fields.get('Email', '')).strip()
        source = str(fields.get('Source', '')).strip()
        lead_quality = str(fields.get('Lead Quality', '')).strip()
        website = str(fields.get('Website', '')).strip()
        business_type = str(fields.get('Business_Type', '')).strip()
        company_description = str(fields.get('Company_Description', '')).strip()
        
        # Skip records without essential data
        if not full_name or full_name in ['', 'None', 'null']:
            return None
        
        # Clean LinkedIn URL
        if linkedin_url:
            # Remove fake patterns
            if re.search(r'-\d{3,}$', linkedin_url):
                print(f"   🚨 Skipping fake LinkedIn URL: {linkedin_url}")
                linkedin_url = ''
            
            # Validate LinkedIn URL format
            if linkedin_url and 'linkedin.com' not in linkedin_url:
                print(f"   ⚠️ Invalid LinkedIn URL format: {linkedin_url}")
                linkedin_url = ''
        
        # Clean email
        if email and '@' not in email:
            print(f"   ⚠️ Invalid email format: {email}")
            email = ''
        
        # Default values
        if not source:
            source = 'Airtable'
        if not lead_quality:
            lead_quality = 'Warm'
        
        # Create clean record
        clean_record = {
            'airtable_id': record_id,
            'full_name': full_name,
            'linkedin_url': linkedin_url or None,
            'job_title': job_title or None,
            'company': company or None,
            'email': email or None,
            'source': source,
            'lead_quality': lead_quality,
            'website': website or None,
            'business_type': business_type or None,
            'company_description': company_description or None,
            'date_scraped': datetime.now().strftime('%Y-%m-%d'),
            'created_at': datetime.now().isoformat(),
            'needs_enrichment': 0  # Assume Airtable data is already enriched
        }
        
        return clean_record
    
    def setup_database(self):
        """Setup database with all required fields"""
        print("🔧 Setting up database schema...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Create table with all fields
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                airtable_id TEXT UNIQUE,
                full_name TEXT,
                linkedin_url TEXT,
                job_title TEXT,
                company TEXT,
                email TEXT,
                source TEXT,
                lead_quality TEXT,
                website TEXT,
                business_type TEXT,
                company_description TEXT,
                date_scraped TEXT,
                date_enriched TEXT,
                date_messaged TEXT,
                ai_message TEXT,
                replied INTEGER DEFAULT 0,
                response_date TEXT,
                response_notes TEXT,
                extra_info TEXT,
                level_engaged TEXT,
                engagement_status TEXT,
                email_confidence_level TEXT,
                follow_up_stage TEXT,
                response_status TEXT,
                needs_enrichment INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database schema ready")
    
    def clear_existing_data(self):
        """Clear existing data from database"""
        print("🗑️ Clearing existing database data...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT COUNT(*) FROM leads')
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            conn.execute('DELETE FROM leads')
            conn.commit()
            print(f"✅ Cleared {existing_count} existing records")
        else:
            print("✅ Database was already empty")
        
        conn.close()
    
    def insert_clean_records(self, clean_records: List[Dict]) -> int:
        """Insert clean records into database"""
        print(f"💾 Inserting {len(clean_records)} clean records into database...")
        
        conn = sqlite3.connect(self.db_path)
        
        insert_sql = '''
            INSERT OR REPLACE INTO leads (
                airtable_id, full_name, linkedin_url, job_title, company, email,
                source, lead_quality, website, business_type, company_description,
                date_scraped, created_at, needs_enrichment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        inserted_count = 0
        
        for record in clean_records:
            try:
                conn.execute(insert_sql, (
                    record['airtable_id'],
                    record['full_name'],
                    record['linkedin_url'],
                    record['job_title'],
                    record['company'],
                    record['email'],
                    record['source'],
                    record['lead_quality'],
                    record['website'],
                    record['business_type'],
                    record['company_description'],
                    record['date_scraped'],
                    record['created_at'],
                    record['needs_enrichment']
                ))
                inserted_count += 1
                
            except Exception as e:
                print(f"   ❌ Error inserting record {record['full_name']}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully inserted {inserted_count}/{len(clean_records)} records")
        return inserted_count
    
    def analyze_pulled_data(self, airtable_records: List[Dict], clean_records: List[Dict]):
        """Analyze the data we pulled from Airtable"""
        print("\n📊 AIRTABLE DATA ANALYSIS")
        print("=" * 50)
        
        print(f"📋 Raw Airtable records: {len(airtable_records)}")
        print(f"✅ Clean records after filtering: {len(clean_records)}")
        print(f"🗑️ Records filtered out: {len(airtable_records) - len(clean_records)}")
        
        # Analyze clean records
        with_linkedin = len([r for r in clean_records if r.get('linkedin_url')])
        with_email = len([r for r in clean_records if r.get('email')])
        with_company = len([r for r in clean_records if r.get('company')])
        
        print(f"\n📊 Clean Data Quality:")
        print(f"   Records with LinkedIn: {with_linkedin} ({with_linkedin/len(clean_records)*100:.1f}%)")
        print(f"   Records with Email: {with_email} ({with_email/len(clean_records)*100:.1f}%)")
        print(f"   Records with Company: {with_company} ({with_company/len(clean_records)*100:.1f}%)")
        
        # Source breakdown
        sources = {}
        for record in clean_records:
            source = record.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n📋 Source Breakdown:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"   {source}: {count} records")
        
        # Show examples
        print(f"\n📝 Sample Clean Records:")
        for i, record in enumerate(clean_records[:5], 1):
            name = record['full_name']
            company = record.get('company', 'No company')
            linkedin = record.get('linkedin_url', 'No LinkedIn')
            email = record.get('email', 'No email')
            print(f"   {i}. {name} at {company}")
            print(f"      LinkedIn: {linkedin}")
            print(f"      Email: {email}")
            print()
    
    def pull_and_clean_all_data(self) -> Dict:
        """Complete process to pull and clean Airtable data"""
        print("🔄 PULLING CLEAN LEADS FROM AIRTABLE")
        print("=" * 50)
        print("Using Airtable as source of truth instead of fixing fake data")
        print("")
        
        try:
            # Step 1: Pull all Airtable records
            airtable_records = self.pull_all_airtable_records()
            
            if not airtable_records:
                print("❌ No records found in Airtable")
                return {'status': 'error', 'message': 'No records found'}
            
            # Step 2: Clean and validate records
            print("\n🧹 Cleaning and validating records...")
            clean_records = []
            
            for record in airtable_records:
                clean_record = self.clean_airtable_record(record)
                if clean_record:
                    clean_records.append(clean_record)
            
            # Step 3: Analyze the data
            self.analyze_pulled_data(airtable_records, clean_records)
            
            # Step 4: Setup database
            self.setup_database()
            
            # Step 5: Clear existing data
            self.clear_existing_data()
            
            # Step 6: Insert clean data
            inserted_count = self.insert_clean_records(clean_records)
            
            # Step 7: Final verification
            print(f"\n✅ PULL COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print(f"📊 Airtable records pulled: {len(airtable_records)}")
            print(f"✅ Clean records created: {len(clean_records)}")
            print(f"💾 Records inserted: {inserted_count}")
            print(f"🎯 Success rate: {inserted_count/len(airtable_records)*100:.1f}%")
            
            # Save report
            report = {
                'timestamp': datetime.now().isoformat(),
                'airtable_records_pulled': len(airtable_records),
                'clean_records_created': len(clean_records),
                'records_inserted': inserted_count,
                'success_rate': inserted_count/len(airtable_records)*100,
                'status': 'success'
            }
            
            report_file = f"airtable_pull_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"📊 Report saved to: {report_file}")
            
            return report
            
        except Exception as e:
            print(f"❌ Pull failed: {e}")
            return {'status': 'error', 'message': str(e)}

def main():
    """Run the Airtable lead puller"""
    try:
        puller = AirtableLeadPuller()
        result = puller.pull_and_clean_all_data()
        
        if result['status'] == 'success':
            print(f"\n🎉 SUCCESS! Database now populated with {result['records_inserted']} clean leads from Airtable!")
            print("✅ No more fake LinkedIn URLs")
            print("✅ Real data from your Airtable")
            print("✅ Ready for production use")
            return 0
        else:
            print(f"\n❌ FAILED: {result['message']}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
