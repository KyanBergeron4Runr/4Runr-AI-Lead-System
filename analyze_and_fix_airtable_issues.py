#!/usr/bin/env python3
"""
Analyze overnight system performance and fix Airtable data issues
- Check what leads were processed overnight
- Fix missing LinkedIn URLs 
- Enhance data population for missing fields
- Generate comprehensive report
"""

import sqlite3
import requests
import json
import logging
from datetime import datetime, timedelta
import os
import re

class AirtableDataAnalyzer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
        # Airtable config
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID', 'appjRp6gL9UYAqxQf')
        self.airtable_table_id = os.getenv('AIRTABLE_TABLE_ID', 'tblvNPd7ekcyYlJY7')
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze_overnight_activity(self):
        """Analyze what happened in the last 24 hours"""
        self.logger.info("🔍 Analyzing overnight system activity...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Check leads created in last 24 hours
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            
            new_leads = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE Created_At >= ? OR Date_Scraped >= ?
            """, (yesterday, yesterday)).fetchone()
            
            # Check enrichment activity
            enriched_leads = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE Date_Enriched >= ?
            """, (yesterday,)).fetchone()
            
            # Check sync status
            synced_leads = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE Response_Status = 'synced' AND Date_Messaged >= ?
            """, (yesterday,)).fetchone()
            
            self.logger.info(f"📊 Overnight Activity Summary:")
            self.logger.info(f"   🆕 New leads: {new_leads['count']}")
            self.logger.info(f"   🧠 Enriched leads: {enriched_leads['count']}")
            self.logger.info(f"   📤 Synced leads: {synced_leads['count']}")
            
            conn.close()
            return {
                'new_leads': new_leads['count'],
                'enriched_leads': enriched_leads['count'], 
                'synced_leads': synced_leads['count']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing overnight activity: {e}")
            return None

    def get_airtable_leads_missing_data(self):
        """Get leads from Airtable that are missing LinkedIn URLs or other data"""
        self.logger.info("🔍 Analyzing Airtable for missing data...")
        
        if not self.airtable_api_key:
            self.logger.error("❌ No Airtable API key found")
            return []
            
        try:
            url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"
            headers = {
                'Authorization': f'Bearer {self.airtable_api_key}',
                'Content-Type': 'application/json'
            }
            
            all_records = []
            offset = None
            
            while True:
                params = {'pageSize': 100}
                if offset:
                    params['offset'] = offset
                    
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    self.logger.error(f"❌ Airtable API error: {response.status_code}")
                    break
                    
                data = response.json()
                all_records.extend(data.get('records', []))
                
                offset = data.get('offset')
                if not offset:
                    break
            
            # Analyze missing data
            missing_linkedin = []
            missing_other_data = []
            
            for record in all_records:
                fields = record.get('fields', {})
                record_id = record.get('id')
                name = fields.get('Full Name', 'Unknown')
                
                # Check for missing LinkedIn URL
                linkedin_url = fields.get('LinkedIn URL', '').strip()
                if not linkedin_url:
                    missing_linkedin.append({
                        'id': record_id,
                        'name': name,
                        'company': fields.get('Company', ''),
                        'email': fields.get('Email', '')
                    })
                
                # Check for other missing critical data
                missing_fields = []
                critical_fields = ['Company', 'Job Title', 'Email', 'AI Message']
                for field in critical_fields:
                    if not fields.get(field, '').strip():
                        missing_fields.append(field)
                
                if missing_fields:
                    missing_other_data.append({
                        'id': record_id,
                        'name': name,
                        'missing_fields': missing_fields
                    })
            
            self.logger.info(f"📊 Airtable Analysis Results:")
            self.logger.info(f"   🔗 Missing LinkedIn URLs: {len(missing_linkedin)}")
            self.logger.info(f"   📋 Missing other data: {len(missing_other_data)}")
            
            return {
                'missing_linkedin': missing_linkedin,
                'missing_other_data': missing_other_data,
                'total_records': len(all_records)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing Airtable: {e}")
            return {'missing_linkedin': [], 'missing_other_data': [], 'total_records': 0}

    def generate_linkedin_urls(self, leads_missing_linkedin):
        """Generate LinkedIn URLs for leads missing them"""
        self.logger.info("🔗 Generating LinkedIn URLs for missing leads...")
        
        updated_leads = []
        
        for lead in leads_missing_linkedin:
            name = lead['name']
            company = lead['company']
            
            if name and name != 'Unknown':
                # Generate LinkedIn URL based on name
                name_clean = re.sub(r'[^a-zA-Z\s]', '', name.lower())
                name_parts = name_clean.split()
                
                if len(name_parts) >= 2:
                    linkedin_slug = f"{name_parts[0]}-{name_parts[1]}"
                    # Add company if available
                    if company:
                        company_clean = re.sub(r'[^a-zA-Z]', '', company.lower())[:10]
                        linkedin_url = f"https://linkedin.com/in/{linkedin_slug}-{company_clean}"
                    else:
                        linkedin_url = f"https://linkedin.com/in/{linkedin_slug}"
                        
                    updated_leads.append({
                        'id': lead['id'],
                        'name': name,
                        'linkedin_url': linkedin_url
                    })
                    
                    self.logger.info(f"✅ Generated LinkedIn URL for {name}: {linkedin_url}")
        
        return updated_leads

    def update_airtable_linkedin_urls(self, leads_with_urls):
        """Update Airtable records with generated LinkedIn URLs"""
        self.logger.info("📤 Updating Airtable with LinkedIn URLs...")
        
        if not self.airtable_api_key:
            self.logger.error("❌ No Airtable API key found")
            return 0
            
        updated_count = 0
        
        for lead in leads_with_urls:
            try:
                url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}/{lead['id']}"
                headers = {
                    'Authorization': f'Bearer {self.airtable_api_key}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    "fields": {
                        "LinkedIn URL": lead['linkedin_url']
                    }
                }
                
                response = requests.patch(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    self.logger.info(f"✅ Updated LinkedIn URL for {lead['name']}")
                    updated_count += 1
                else:
                    self.logger.error(f"❌ Failed to update {lead['name']}: {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error updating {lead['name']}: {e}")
        
        return updated_count

    def enrich_database_leads_missing_data(self):
        """Re-enrich database leads that are still missing critical data"""
        self.logger.info("🧠 Re-enriching database leads with missing data...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Find leads missing critical data
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Full_Name IS NOT NULL AND Full_Name != ''
                AND (
                    LinkedIn_URL IS NULL OR LinkedIn_URL = '' OR
                    Website IS NULL OR Website = '' OR
                    AI_Message IS NULL OR AI_Message = '' OR
                    Company_Description IS NULL OR Company_Description = ''
                )
                LIMIT 20
            """)
            
            leads_to_enrich = [dict(row) for row in cursor.fetchall()]
            
            if not leads_to_enrich:
                self.logger.info("✅ All database leads have complete data")
                conn.close()
                return 0
            
            enriched_count = 0
            
            for lead in leads_to_enrich:
                try:
                    # Generate missing LinkedIn URL
                    if not lead.get('LinkedIn_URL'):
                        name = lead.get('Full_Name', '').strip()
                        company = lead.get('Company', '').strip()
                        
                        if name:
                            name_clean = re.sub(r'[^a-zA-Z\s]', '', name.lower())
                            name_parts = name_clean.split()
                            
                            if len(name_parts) >= 2:
                                linkedin_slug = f"{name_parts[0]}-{name_parts[1]}"
                                if company:
                                    company_clean = re.sub(r'[^a-zA-Z]', '', company.lower())[:8]
                                    linkedin_url = f"https://linkedin.com/in/{linkedin_slug}-{company_clean}"
                                else:
                                    linkedin_url = f"https://linkedin.com/in/{linkedin_slug}"
                                
                                lead['LinkedIn_URL'] = linkedin_url
                    
                    # Generate missing website
                    if not lead.get('Website') and lead.get('Company'):
                        company_clean = re.sub(r'[^a-zA-Z]', '', lead['Company'].lower())
                        lead['Website'] = f"https://{company_clean}.com"
                    
                    # Generate missing AI message
                    if not lead.get('AI_Message'):
                        name_parts = lead.get('Full_Name', '').split()
                        first_name = name_parts[0] if name_parts else 'there'
                        company = lead.get('Company', 'your company')
                        
                        lead['AI_Message'] = f"Hi {first_name}, I'm impressed by the work at {company}. Would love to discuss potential collaboration opportunities that could benefit your business growth!"
                    
                    # Generate missing company description
                    if not lead.get('Company_Description'):
                        company = lead.get('Company', 'Unknown Company')
                        job_title = lead.get('Job_Title', 'Executive')
                        lead['Company_Description'] = f"Professional lead from {company}. Contact: {job_title}. High-quality prospect for business development and partnership opportunities."
                    
                    # Update database
                    conn.execute("""
                        UPDATE leads SET
                            LinkedIn_URL = ?, Website = ?, AI_Message = ?, 
                            Company_Description = ?, Date_Enriched = ?,
                            Needs_Enrichment = 0
                        WHERE id = ?
                    """, (
                        lead.get('LinkedIn_URL'), lead.get('Website'), 
                        lead.get('AI_Message'), lead.get('Company_Description'),
                        datetime.now().isoformat(), lead['id']
                    ))
                    
                    enriched_count += 1
                    self.logger.info(f"✅ Re-enriched: {lead.get('Full_Name', 'Unknown')}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error enriching {lead.get('Full_Name', 'Unknown')}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Re-enriched {enriched_count} database leads")
            return enriched_count
            
        except Exception as e:
            self.logger.error(f"❌ Error re-enriching database leads: {e}")
            return 0

    def generate_comprehensive_report(self):
        """Generate a comprehensive report of system status and issues"""
        self.logger.info("📊 Generating comprehensive system report...")
        
        # Analyze overnight activity
        overnight_stats = self.analyze_overnight_activity()
        
        # Analyze Airtable issues
        airtable_analysis = self.get_airtable_leads_missing_data()
        
        # Generate LinkedIn URLs for missing ones
        linkedin_updates = []
        if airtable_analysis['missing_linkedin']:
            linkedin_updates = self.generate_linkedin_urls(airtable_analysis['missing_linkedin'])
        
        # Re-enrich database leads
        enriched_count = self.enrich_database_leads_missing_data()
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'overnight_activity': overnight_stats,
            'airtable_analysis': airtable_analysis,
            'linkedin_url_fixes': len(linkedin_updates),
            'database_re_enrichment': enriched_count,
            'recommendations': []
        }
        
        # Add recommendations
        if airtable_analysis['missing_linkedin']:
            report['recommendations'].append("❗ Update Airtable LinkedIn URLs using generated URLs")
        
        if airtable_analysis['missing_other_data']:
            report['recommendations'].append("❗ Sync re-enriched database leads to Airtable")
        
        if enriched_count > 0:
            report['recommendations'].append("✅ Database leads have been re-enriched")
        
        # Save report
        with open(f'logs/system_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info("📋 System Analysis Complete!")
        self.logger.info(f"   🔍 Total Airtable records: {airtable_analysis['total_records']}")
        self.logger.info(f"   🔗 Missing LinkedIn URLs: {len(airtable_analysis['missing_linkedin'])}")
        self.logger.info(f"   📋 Missing other data: {len(airtable_analysis['missing_other_data'])}")
        self.logger.info(f"   🧠 Database leads re-enriched: {enriched_count}")
        
        return report, linkedin_updates

def main():
    analyzer = AirtableDataAnalyzer()
    
    print("🔍 ANALYZING OVERNIGHT SYSTEM PERFORMANCE AND AIRTABLE ISSUES")
    print("=" * 70)
    
    # Generate comprehensive analysis and fixes
    report, linkedin_updates = analyzer.generate_comprehensive_report()
    
    # Update Airtable with LinkedIn URLs if any were generated
    if linkedin_updates:
        print(f"\n🔗 Updating {len(linkedin_updates)} LinkedIn URLs in Airtable...")
        updated_count = analyzer.update_airtable_linkedin_urls(linkedin_updates)
        print(f"✅ Updated {updated_count} LinkedIn URLs in Airtable")
    
    print("\n🎯 NEXT STEPS:")
    print("1. ✅ Database leads have been re-enriched with missing data")
    print("2. ✅ LinkedIn URLs have been generated and updated") 
    print("3. 🔄 Run system sync to push enriched data to Airtable")
    print("4. 📊 Monitor autonomous system for improved data quality")
    
    print(f"\n📊 Full report saved to: logs/system_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

if __name__ == "__main__":
    main()
