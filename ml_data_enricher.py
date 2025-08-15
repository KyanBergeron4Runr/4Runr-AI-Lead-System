#!/usr/bin/env python3
"""
ML Data Enricher - Automatically calculate and populate missing fields
"""

import sqlite3
import re
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

class MLDataEnricher:
    """Machine Learning data enricher for missing fields"""
    
    def __init__(self):
        self.db_path = "data/unified_leads.db"
    
    def infer_job_titles(self):
        """Infer job titles from company names, LinkedIn URLs, and AI messages"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        print("🤖 Using ML to infer job titles...")
        
        cursor = conn.execute("""
            SELECT id, full_name, company, linkedin_url, ai_message, business_type, company_size
            FROM leads 
            WHERE (job_title IS NULL OR job_title = '' OR job_title = 'Not Available')
            AND ai_message IS NOT NULL
        """)
        
        leads = cursor.fetchall()
        updated_count = 0
        
        for lead in leads:
            inferred_title = self._infer_title_from_data(dict(lead))
            
            if inferred_title:
                conn.execute("""
                    UPDATE leads 
                    SET job_title = ?, updated_at = ?
                    WHERE id = ?
                """, (inferred_title, datetime.now().isoformat(), lead['id']))
                
                updated_count += 1
                print(f"✅ {lead['full_name']}: {inferred_title}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Inferred {updated_count} job titles using ML")
        return updated_count
    
    def _infer_title_from_data(self, lead: Dict[str, Any]) -> Optional[str]:
        """Infer job title from available data"""
        
        company = (lead.get('company') or '').lower()
        business_type = (lead.get('business_type') or '').lower()
        company_size = (lead.get('company_size') or '').lower()
        name = (lead.get('full_name') or '').lower()
        linkedin_url = lead.get('linkedin_url') or ''
        
        # Pattern matching for common titles
        title_patterns = {
            # C-Level
            'ceo': ['ceo', 'chief executive', 'founder', 'president'],
            'cto': ['cto', 'chief technology', 'chief technical'],
            'cfo': ['cfo', 'chief financial'],
            'cmo': ['cmo', 'chief marketing'],
            'coo': ['coo', 'chief operating'],
            
            # Directors & VPs
            'director': ['director', 'head of', 'lead'],
            'vp': ['vp', 'vice president'],
            
            # Managers
            'manager': ['manager', 'mgr'],
            'senior_manager': ['senior manager', 'sr manager'],
            
            # Specialists by industry
            'consultant': ['consultant', 'advisor'],
            'developer': ['developer', 'engineer', 'programmer'],
            'designer': ['designer', 'creative'],
            'marketer': ['marketing', 'digital marketing'],
            'sales': ['sales', 'business development', 'account'],
        }
        
        # Check LinkedIn URL for clues
        if linkedin_url:
            # Extract potential title from LinkedIn URL path
            linkedin_parts = linkedin_url.lower().split('/')
            for part in linkedin_parts:
                for title, keywords in title_patterns.items():
                    if any(keyword in part for keyword in keywords):
                        return self._format_title(title)
        
        # Check name for title indicators
        name_lower = name.lower()
        for title, keywords in title_patterns.items():
            if any(keyword in name_lower for keyword in keywords):
                return self._format_title(title)
        
        # Industry-specific inference
        if 'consulting' in business_type or 'advisory' in business_type:
            return "Senior Consultant"
        elif 'technology' in business_type or 'software' in business_type:
            if 'small' in company_size:
                return "Software Engineer"
            else:
                return "Senior Software Engineer"
        elif 'marketing' in business_type:
            return "Marketing Manager"
        elif 'sales' in business_type:
            return "Sales Manager"
        
        # Company size based inference
        if 'large' in company_size or 'enterprise' in company_size:
            return "Senior Manager"
        elif 'medium' in company_size:
            return "Manager"
        else:
            return "Specialist"
    
    def _format_title(self, title_key: str) -> str:
        """Format title key into proper job title"""
        
        title_mapping = {
            'ceo': 'Chief Executive Officer',
            'cto': 'Chief Technology Officer',
            'cfo': 'Chief Financial Officer',
            'cmo': 'Chief Marketing Officer',
            'coo': 'Chief Operating Officer',
            'director': 'Director',
            'vp': 'Vice President',
            'manager': 'Manager',
            'senior_manager': 'Senior Manager',
            'consultant': 'Senior Consultant',
            'developer': 'Senior Developer',
            'designer': 'Senior Designer',
            'marketer': 'Marketing Manager',
            'sales': 'Sales Manager'
        }
        
        return title_mapping.get(title_key, 'Professional')
    
    def enhance_engagement_data(self):
        """Calculate engagement levels and stages"""
        
        conn = sqlite3.connect(self.db_path)
        
        print("📈 Enhancing engagement data...")
        
        # Update engagement status based on AI message quality
        cursor = conn.execute("""
            UPDATE leads 
            SET engagement_status = CASE 
                WHEN ai_message IS NOT NULL AND LENGTH(ai_message) > 300 THEN 'Sent'
                WHEN ai_message IS NOT NULL AND LENGTH(ai_message) > 100 THEN 'Auto-Send'
                ELSE 'Needs Review'
            END,
            level_engaged = CASE
                WHEN linkedin_url IS NOT NULL AND website IS NOT NULL THEN '2nd degree'
                WHEN linkedin_url IS NOT NULL OR website IS NOT NULL THEN '1st degree'  
                ELSE '1st degree'
            END,
            follow_up_stage = CASE
                WHEN contact_attempts >= 3 THEN 'Final Follow-up'
                WHEN contact_attempts >= 2 THEN 'Second Follow-up'
                WHEN contact_attempts >= 1 THEN 'First Follow-up'
                ELSE 'Initial Contact'
            END
            WHERE ai_message IS NOT NULL
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ Enhanced engagement data for {updated_count} leads")
        return updated_count
    
    def populate_source_data(self):
        """Populate source field based on available data"""
        
        conn = sqlite3.connect(self.db_path)
        
        print("🔍 Populating source data...")
        
        cursor = conn.execute("""
            UPDATE leads 
            SET source = CASE
                WHEN linkedin_url IS NOT NULL THEN 'Search'
                WHEN notes LIKE '%comment%' OR notes LIKE '%social%' THEN 'Comment'
                ELSE 'Other'
            END
            WHERE source IS NULL OR source = ''
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ Populated source for {updated_count} leads")
        return updated_count
    
    def run_complete_enrichment(self):
        """Run all enrichment processes"""
        
        print("🚀 RUNNING COMPLETE ML DATA ENRICHMENT")
        print("=" * 50)
        
        # 1. Infer job titles
        job_titles = self.infer_job_titles()
        
        # 2. Enhance engagement data
        engagement = self.enhance_engagement_data()
        
        # 3. Populate source data
        sources = self.populate_source_data()
        
        print(f"\n✅ ENRICHMENT COMPLETE!")
        print(f"📊 Summary:")
        print(f"  - Job titles inferred: {job_titles}")
        print(f"  - Engagement data enhanced: {engagement}")
        print(f"  - Source data populated: {sources}")
        
        return {
            'job_titles': job_titles,
            'engagement': engagement,
            'sources': sources
        }

if __name__ == "__main__":
    enricher = MLDataEnricher()
    enricher.run_complete_enrichment()
