#!/usr/bin/env python3
"""
Fresh Start with Enhanced System
===============================
Clear contaminated leads and start fresh with enhanced scraper + validation
"""

import sqlite3
import json
import logging
import os
from datetime import datetime

class FreshStartManager:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def backup_contaminated_data(self):
        """Backup the contaminated data before cleaning"""
        self.logger.info("💾 Backing up contaminated data...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all current leads
            cursor = conn.execute("SELECT * FROM leads")
            contaminated_leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # Save backup
            backup_file = f"backups/contaminated_leads_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("backups", exist_ok=True)
            
            with open(backup_file, 'w') as f:
                json.dump(contaminated_leads, f, indent=2, default=str)
            
            self.logger.info(f"💾 Backed up {len(contaminated_leads)} contaminated leads to: {backup_file}")
            return len(contaminated_leads)
            
        except Exception as e:
            self.logger.error(f"❌ Error backing up data: {e}")
            return 0

    def clear_contaminated_leads(self):
        """Clear all contaminated leads from database"""
        self.logger.info("🧹 Clearing contaminated leads from database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get count before deletion
            count_before = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            
            # Clear all leads
            conn.execute("DELETE FROM leads")
            
            # Reset auto-increment
            conn.execute("DELETE FROM sqlite_sequence WHERE name='leads'")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🧹 Cleared {count_before} contaminated leads from database")
            self.logger.info("✅ Database is now clean and ready for fresh leads")
            
            return count_before
            
        except Exception as e:
            self.logger.error(f"❌ Error clearing leads: {e}")
            return 0

    def test_enhanced_scraper(self):
        """Test the enhanced scraper to get fresh, clean leads"""
        self.logger.info("🚀 Testing enhanced scraper for fresh leads...")
        
        try:
            # Import the enhanced scraper
            import sys
            sys.path.insert(0, './4runr-lead-scraper')
            from scraper.serpapi_scraper import SerpAPILeadScraper
            
            # Initialize enhanced scraper
            scraper = SerpAPILeadScraper()
            
            # Get fresh leads with enhanced data extraction
            fresh_leads = scraper.search_montreal_ceos(max_results=5)
            
            self.logger.info(f"🎯 Enhanced scraper found {len(fresh_leads)} fresh leads:")
            
            for i, lead in enumerate(fresh_leads, 1):
                self.logger.info(f"   {i}. {lead.get('name', 'Unknown')} - {lead.get('title', 'Unknown')}")
                self.logger.info(f"      Company: {lead.get('company', 'Unknown')}")
                self.logger.info(f"      Email: {lead.get('email', 'Not extracted')}")
                self.logger.info(f"      Phone: {lead.get('phone', 'Not extracted')}")
                self.logger.info(f"      LinkedIn: {lead.get('linkedin_url', 'Unknown')}")
                self.logger.info(f"      Data Quality: {lead.get('data_quality', 'Unknown')}")
                self.logger.info("")
            
            return fresh_leads
            
        except Exception as e:
            self.logger.error(f"❌ Error testing enhanced scraper: {e}")
            return []

    def save_fresh_leads_to_database(self, fresh_leads):
        """Save fresh leads to the clean database"""
        if not fresh_leads:
            self.logger.info("📋 No fresh leads to save")
            return 0
        
        self.logger.info(f"💾 Saving {len(fresh_leads)} fresh leads to database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            saved_count = 0
            for lead in fresh_leads:
                # Map enhanced scraper data to database schema
                conn.execute('''
                    INSERT INTO leads (
                        Full_Name, Job_Title, Company, LinkedIn_URL, Email, 
                        Website, Business_Type, Location, Source, 
                        Date_Scraped, Created_At, scraped_at, scraping_source,
                        data_quality, search_context, Response_Status,
                        Needs_Enrichment, Phone
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lead.get('name', ''),
                    lead.get('title', ''),
                    lead.get('company', ''),
                    lead.get('linkedin_url', ''),
                    lead.get('email', ''),
                    lead.get('website', ''),
                    'Small Business',  # Default, will be enriched
                    lead.get('location', 'Montreal, Quebec, Canada'),
                    'Enhanced SerpAPI',
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    lead.get('scraped_at', datetime.now().isoformat()),
                    lead.get('scraping_source', 'serpapi_enhanced'),
                    lead.get('data_quality', 'serpapi_sourced'),
                    lead.get('search_context', ''),
                    'pending',  # Ready for enrichment
                    1,  # Needs enrichment
                    lead.get('phone', '')
                ))
                
                saved_count += 1
                self.logger.info(f"✅ Saved: {lead.get('name', 'Unknown')} - {lead.get('company', 'Unknown')}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Successfully saved {saved_count} fresh leads to database")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"❌ Error saving fresh leads: {e}")
            return 0

    def verify_fresh_system(self):
        """Verify the fresh system is working correctly"""
        self.logger.info("✅ Verifying fresh system...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Check total leads
            total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            
            # Check leads with emails
            leads_with_email = conn.execute("SELECT COUNT(*) FROM leads WHERE Email IS NOT NULL AND Email != ''").fetchone()[0]
            
            # Check leads ready for enrichment
            needs_enrichment = conn.execute("SELECT COUNT(*) FROM leads WHERE Needs_Enrichment = 1").fetchone()[0]
            
            # Get sample lead
            sample_lead = conn.execute("SELECT * FROM leads LIMIT 1").fetchone()
            
            conn.close()
            
            self.logger.info("📊 FRESH SYSTEM STATUS:")
            self.logger.info(f"   📋 Total fresh leads: {total_leads}")
            self.logger.info(f"   📧 Leads with emails: {leads_with_email}")
            self.logger.info(f"   🔧 Needs enrichment: {needs_enrichment}")
            
            if sample_lead:
                sample = dict(sample_lead)
                self.logger.info("📋 SAMPLE FRESH LEAD:")
                self.logger.info(f"   Name: {sample.get('Full_Name', 'Unknown')}")
                self.logger.info(f"   Company: {sample.get('Company', 'Unknown')}")
                self.logger.info(f"   Email: {sample.get('Email', 'None')}")
                self.logger.info(f"   Data Quality: {sample.get('data_quality', 'Unknown')}")
                self.logger.info(f"   Source: {sample.get('scraping_source', 'Unknown')}")
            
            return {
                'total_leads': total_leads,
                'leads_with_email': leads_with_email,
                'needs_enrichment': needs_enrichment,
                'sample_lead': dict(sample_lead) if sample_lead else None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error verifying system: {e}")
            return None

def main():
    manager = FreshStartManager()
    
    print("🔄 FRESH START WITH ENHANCED SYSTEM")
    print("=" * 40)
    
    # Step 1: Backup contaminated data
    print("\n💾 STEP 1: Backing up contaminated data...")
    backup_count = manager.backup_contaminated_data()
    
    # Step 2: Clear contaminated leads
    print("\n🧹 STEP 2: Clearing contaminated leads...")
    cleared_count = manager.clear_contaminated_leads()
    
    # Step 3: Test enhanced scraper
    print("\n🚀 STEP 3: Testing enhanced scraper...")
    fresh_leads = manager.test_enhanced_scraper()
    
    # Step 4: Save fresh leads
    print("\n💾 STEP 4: Saving fresh leads...")
    saved_count = manager.save_fresh_leads_to_database(fresh_leads)
    
    # Step 5: Verify fresh system
    print("\n✅ STEP 5: Verifying fresh system...")
    verification = manager.verify_fresh_system()
    
    # Summary
    print(f"\n🎉 FRESH START COMPLETE!")
    print(f"   💾 Backed up: {backup_count} contaminated leads")
    print(f"   🧹 Cleared: {cleared_count} contaminated leads")
    print(f"   🚀 Scraped: {len(fresh_leads)} fresh leads")
    print(f"   💾 Saved: {saved_count} fresh leads")
    
    if verification:
        print(f"   ✅ System verified: {verification['total_leads']} leads ready")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Test autonomous system: python3 real_autonomous_organism.py --test")
    print(f"   2. Should now find leads needing enrichment")
    print(f"   3. Enhanced data quality with no contamination")
    print(f"   4. Start autonomous mode when ready")

if __name__ == "__main__":
    main()
