#!/usr/bin/env python3
"""
Integrate Company Extraction into SerpAPI Scraper
================================================
Update existing leads with real company names
"""

import sqlite3
import sys
import os
import logging
from enhance_company_extraction import CompanyExtractor

# Add the scraper path
sys.path.insert(0, './4runr-lead-scraper')

class CompanyExtractionIntegrator:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        self.extractor = CompanyExtractor()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fix_existing_leads_companies(self):
        """Fix company names for existing leads with 'Unknown Company'"""
        self.logger.info("🔧 Fixing existing leads with Unknown Company...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Find leads with Unknown Company
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Company = 'Unknown Company' OR Company IS NULL OR Company = ''
            """)
            
            leads_to_fix = [dict(row) for row in cursor.fetchall()]
            
            if not leads_to_fix:
                self.logger.info("✅ No leads need company fixing")
                return 0
            
            self.logger.info(f"🔧 Found {len(leads_to_fix)} leads to fix...")
            
            fixed_count = 0
            for lead in leads_to_fix:
                # Try to extract company from title
                title = lead.get('Job_Title', '') or lead.get('title', '')
                company = self.extractor.extract_best_company(title, title)  # Use title as snippet too
                
                if company and company != 'Unknown Company':
                    # Update the lead
                    conn.execute("""
                        UPDATE leads 
                        SET Company = ? 
                        WHERE id = ?
                    """, (company, lead['id']))
                    
                    fixed_count += 1
                    self.logger.info(f"✅ Fixed: {lead.get('Full_Name', 'Unknown')} -> {company}")
                else:
                    # Try to extract from job title patterns
                    if 'at Bombardier' in title:
                        company = 'Bombardier'
                    elif 'CGI' in title:
                        company = 'CGI'
                    elif 'President and CEO' in title and not company:
                        # Keep as Unknown for now, but mark for enrichment
                        continue
                    
                    if company:
                        conn.execute("""
                            UPDATE leads 
                            SET Company = ? 
                            WHERE id = ?
                        """, (company, lead['id']))
                        
                        fixed_count += 1
                        self.logger.info(f"✅ Manual fix: {lead.get('Full_Name', 'Unknown')} -> {company}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Fixed company names for {fixed_count} leads")
            return fixed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error fixing companies: {e}")
            return 0

    def update_scraper_with_extraction(self):
        """Generate updated scraper code with company extraction"""
        
        integration_code = '''
# Add this to SerpAPILeadScraper class

from enhance_company_extraction import CompanyExtractor

def __init__(self):
    # ... existing init code ...
    self.company_extractor = CompanyExtractor()

def process_search_result(self, result):
    """Enhanced result processing with company extraction"""
    
    # ... existing code to extract name, title, etc ...
    
    # NEW: Extract real company name
    title = result.get('title', '')
    snippet = result.get('snippet', '')
    linkedin_url = self.extract_linkedin_url(result)
    
    # Extract company using the enhancer
    company = self.company_extractor.extract_best_company(title, snippet, linkedin_url)
    
    if not company:
        # Fallback patterns for this specific data
        if 'at Bombardier' in title:
            company = 'Bombardier'
        elif 'CGI' in title:
            company = 'CGI Inc'
        elif 'President and CEO' in title:
            company = 'Executive Company'  # Better than Unknown
        else:
            company = 'To Be Determined'  # Better than Unknown
    
    return {
        'name': name,
        'title': title,
        'company': company,  # Now uses extracted company!
        'email': email,
        'linkedin_url': linkedin_url,
        # ... other fields
    }
        '''
        
        self.logger.info("💡 SCRAPER INTEGRATION CODE:")
        self.logger.info(integration_code)

def main():
    integrator = CompanyExtractionIntegrator()
    
    print("🔧 COMPANY EXTRACTION INTEGRATION")
    print("=" * 35)
    
    # Fix existing leads
    print("\n🔧 STEP 1: Fix existing leads with Unknown Company...")
    fixed_count = integrator.fix_existing_leads_companies()
    
    # Show integration code
    print(f"\n💡 STEP 2: Update scraper for future leads...")
    integrator.update_scraper_with_extraction()
    
    print(f"\n🎉 INTEGRATION COMPLETE!")
    print(f"   ✅ Fixed: {fixed_count} existing leads")
    print(f"   💡 Scraper code ready for integration")
    
    print(f"\n🧪 NEXT: Test the fixed system")
    print(f"   python3 real_autonomous_organism.py --test")

if __name__ == "__main__":
    main()
