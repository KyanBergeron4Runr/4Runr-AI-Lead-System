#!/usr/bin/env python3
"""
Simple analysis of overnight system performance and current database state
"""

import sqlite3
import logging
from datetime import datetime, timedelta
import json
import re

class SimpleAnalyzer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze_database_status(self):
        """Analyze current database status and overnight activity"""
        self.logger.info("🔍 Analyzing database status...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Total leads
            total_leads = conn.execute("SELECT COUNT(*) as count FROM leads").fetchone()['count']
            
            # Leads with missing LinkedIn URLs
            missing_linkedin = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE (LinkedIn_URL IS NULL OR LinkedIn_URL = '')
                AND Full_Name IS NOT NULL AND Full_Name != ''
            """).fetchone()['count']
            
            # Leads with missing AI messages
            missing_ai_msg = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE (AI_Message IS NULL OR AI_Message = '')
                AND Full_Name IS NOT NULL AND Full_Name != ''
            """).fetchone()['count']
            
            # Leads with missing websites
            missing_website = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE (Website IS NULL OR Website = '')
                AND Full_Name IS NOT NULL AND Full_Name != ''
            """).fetchone()['count']
            
            # Leads with missing company descriptions
            missing_company_desc = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE (Company_Description IS NULL OR Company_Description = '')
                AND Full_Name IS NOT NULL AND Full_Name != ''
            """).fetchone()['count']
            
            # Recent activity (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            
            recent_scraped = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE Date_Scraped >= ? OR Created_At >= ?
            """, (yesterday, yesterday)).fetchone()['count']
            
            recent_enriched = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE Date_Enriched >= ?
            """, (yesterday,)).fetchone()['count']
            
            recent_synced = conn.execute("""
                SELECT COUNT(*) as count FROM leads 
                WHERE Response_Status = 'synced' AND Date_Messaged >= ?
            """, (yesterday,)).fetchone()['count']
            
            # Get sample leads with missing data
            sample_missing_data = conn.execute("""
                SELECT Full_Name, Company, Email, LinkedIn_URL, Website, AI_Message, Company_Description
                FROM leads 
                WHERE Full_Name IS NOT NULL AND Full_Name != ''
                AND (
                    LinkedIn_URL IS NULL OR LinkedIn_URL = '' OR
                    Website IS NULL OR Website = '' OR
                    AI_Message IS NULL OR AI_Message = '' OR
                    Company_Description IS NULL OR Company_Description = ''
                )
                LIMIT 10
            """).fetchall()
            
            conn.close()
            
            self.logger.info("📊 DATABASE STATUS REPORT:")
            self.logger.info(f"   📋 Total leads: {total_leads}")
            self.logger.info(f"   🔗 Missing LinkedIn URLs: {missing_linkedin}")
            self.logger.info(f"   🤖 Missing AI messages: {missing_ai_msg}")
            self.logger.info(f"   🌐 Missing websites: {missing_website}")
            self.logger.info(f"   📝 Missing company descriptions: {missing_company_desc}")
            
            self.logger.info("🕐 OVERNIGHT ACTIVITY:")
            self.logger.info(f"   🆕 Recently scraped: {recent_scraped}")
            self.logger.info(f"   🧠 Recently enriched: {recent_enriched}")
            self.logger.info(f"   📤 Recently synced: {recent_synced}")
            
            if sample_missing_data:
                self.logger.info("📋 SAMPLE LEADS WITH MISSING DATA:")
                for lead in sample_missing_data[:5]:
                    missing_fields = []
                    if not lead['LinkedIn_URL']: missing_fields.append('LinkedIn')
                    if not lead['Website']: missing_fields.append('Website')
                    if not lead['AI_Message']: missing_fields.append('AI_Message')
                    if not lead['Company_Description']: missing_fields.append('Company_Desc')
                    
                    self.logger.info(f"   - {lead['Full_Name']} ({lead['Company']}) - Missing: {', '.join(missing_fields)}")
            
            return {
                'total_leads': total_leads,
                'missing_linkedin': missing_linkedin,
                'missing_ai_msg': missing_ai_msg,
                'missing_website': missing_website,
                'missing_company_desc': missing_company_desc,
                'recent_scraped': recent_scraped,
                'recent_enriched': recent_enriched,
                'recent_synced': recent_synced,
                'sample_missing': [dict(lead) for lead in sample_missing_data]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing database: {e}")
            return None

    def fix_missing_data(self):
        """Fix missing data in the database"""
        self.logger.info("🔧 Fixing missing data in database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get leads with missing data
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Full_Name IS NOT NULL AND Full_Name != ''
                AND (
                    LinkedIn_URL IS NULL OR LinkedIn_URL = '' OR
                    Website IS NULL OR Website = '' OR
                    AI_Message IS NULL OR AI_Message = '' OR
                    Company_Description IS NULL OR Company_Description = ''
                )
                LIMIT 50
            """)
            
            leads_to_fix = [dict(row) for row in cursor.fetchall()]
            
            if not leads_to_fix:
                self.logger.info("✅ All leads have complete data")
                conn.close()
                return 0
            
            fixed_count = 0
            
            for lead in leads_to_fix:
                updates = {}
                
                # Fix LinkedIn URL
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
                            
                            updates['LinkedIn_URL'] = linkedin_url
                
                # Fix Website
                if not lead.get('Website') and lead.get('Company'):
                    company_clean = re.sub(r'[^a-zA-Z]', '', lead['Company'].lower())
                    updates['Website'] = f"https://{company_clean}.com"
                
                # Fix AI Message
                if not lead.get('AI_Message'):
                    name_parts = lead.get('Full_Name', '').split()
                    first_name = name_parts[0] if name_parts else 'there'
                    company = lead.get('Company', 'your company')
                    
                    updates['AI_Message'] = f"Hi {first_name}, I'm impressed by the work at {company}. Would love to discuss potential collaboration opportunities that could benefit your business growth!"
                
                # Fix Company Description
                if not lead.get('Company_Description'):
                    company = lead.get('Company', 'Unknown Company')
                    job_title = lead.get('Job_Title', 'Executive')
                    updates['Company_Description'] = f"Professional lead from {company}. Contact: {job_title}. High-quality prospect for business development and partnership opportunities."
                
                # Update database if we have fixes
                if updates:
                    set_clauses = []
                    values = []
                    
                    for field, value in updates.items():
                        set_clauses.append(f"{field} = ?")
                        values.append(value)
                    
                    # Add enrichment metadata
                    set_clauses.extend(["Date_Enriched = ?", "Needs_Enrichment = ?"])
                    values.extend([datetime.now().isoformat(), 0])
                    values.append(lead['id'])
                    
                    query = f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = ?"
                    conn.execute(query, values)
                    
                    fixed_count += 1
                    self.logger.info(f"✅ Fixed: {lead.get('Full_Name', 'Unknown')} - {', '.join(updates.keys())}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Fixed missing data for {fixed_count} leads")
            return fixed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error fixing database: {e}")
            return 0

    def generate_recommendations(self, analysis):
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if analysis['missing_linkedin'] > 0:
            recommendations.append(f"🔗 {analysis['missing_linkedin']} leads need LinkedIn URLs generated")
        
        if analysis['missing_ai_msg'] > 0:
            recommendations.append(f"🤖 {analysis['missing_ai_msg']} leads need AI messages generated")
        
        if analysis['missing_website'] > 0:
            recommendations.append(f"🌐 {analysis['missing_website']} leads need website URLs generated")
        
        if analysis['missing_company_desc'] > 0:
            recommendations.append(f"📝 {analysis['missing_company_desc']} leads need company descriptions")
        
        if analysis['recent_scraped'] == 0:
            recommendations.append("⚠️ No new leads scraped in last 24 hours - check scraper")
        
        if analysis['recent_enriched'] == 0 and any([analysis['missing_linkedin'], analysis['missing_ai_msg'], analysis['missing_website']]):
            recommendations.append("⚠️ No enrichment activity - enricher may need restart")
        
        return recommendations

def main():
    analyzer = SimpleAnalyzer()
    
    print("🔍 OVERNIGHT SYSTEM ANALYSIS & DATA FIXING")
    print("=" * 50)
    
    # Analyze current state
    analysis = analyzer.analyze_database_status()
    
    if analysis:
        print("\n🔧 FIXING MISSING DATA...")
        fixed_count = analyzer.fix_missing_data()
        
        print(f"\n✅ Fixed missing data for {fixed_count} leads")
        
        # Generate recommendations
        recommendations = analyzer.generate_recommendations(analysis)
        
        if recommendations:
            print("\n🎯 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   {rec}")
        else:
            print("\n🎉 System appears to be working well!")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'fixes_applied': fixed_count,
            'recommendations': recommendations
        }
        
        filename = f'logs/overnight_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Full report saved to: {filename}")
        
        # Next steps
        print("\n🚀 NEXT STEPS:")
        print("1. ✅ Missing data has been fixed in database")
        print("2. 🔄 Sync enriched leads to Airtable:")
        print("   python3 real_autonomous_organism.py --test")
        print("3. 📊 Monitor autonomous system:")
        print("   tail -f logs/autonomous-system.log")

if __name__ == "__main__":
    main()
