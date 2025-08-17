#!/usr/bin/env python3
"""
🌟 PRODUCTION CLEAN ORGANISM 🌟
==============================
Production-ready organism that uses the ultimate clean enrichment system.
Zero duplicates guaranteed!
"""

import time
import sqlite3
from datetime import datetime
from ultimate_clean_enrichment_system import UltimateCleanEnrichmentSystem

class ProductionCleanOrganism:
    """Production organism with clean enrichment system"""
    
    def __init__(self):
        self.enrichment_system = UltimateCleanEnrichmentSystem()
        self.running = True
        
        print("🌟 Production Clean Organism initialized")
        print("🚫 Zero duplicates guaranteed!")
    
    def get_leads_needing_enrichment(self):
        """Get leads that need enrichment"""
        try:
            conn = sqlite3.connect('data/unified_leads.db')
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE (enriched = 0 OR enriched IS NULL)
                AND full_name IS NOT NULL 
                AND company IS NOT NULL
                LIMIT 5
            """)
            
            leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return leads
            
        except Exception as e:
            print(f"❌ Error getting leads: {e}")
            return []
    
    def process_leads_batch(self):
        """Process a batch of leads with clean enrichment"""
        leads = self.get_leads_needing_enrichment()
        
        if not leads:
            print("📊 No leads need enrichment")
            return
        
        print(f"🌟 Processing {len(leads)} leads with clean enrichment...")
        
        # Use our ultimate clean system
        batch_results = self.enrichment_system.batch_enrich_leads(leads)
        
        print(f"✅ Batch completed:")
        print(f"   Success rate: {batch_results['success_rate']:.1f}%")
        print(f"   Duplicates prevented: {batch_results['duplicates_prevented']}")
        print(f"   Emails found: {batch_results['total_emails_found']}")
        print(f"   Quality distribution: {batch_results['quality_distribution']}")
    
    def run_continuous(self, cycles=100, interval=60):
        """Run continuous enrichment with duplicate prevention"""
        print(f"🔄 Starting continuous enrichment...")
        print(f"   Cycles: {cycles}")
        print(f"   Interval: {interval} seconds")
        
        for cycle in range(1, cycles + 1):
            if not self.running:
                break
            
            print(f"\n🔄 CYCLE {cycle}/{cycles}")
            print("=" * 50)
            
            try:
                self.process_leads_batch()
                
                # Show system metrics
                metrics = self.enrichment_system.get_system_metrics()
                print(f"📊 System metrics:")
                print(f"   Leads processed: {metrics['leads_processed']}")
                print(f"   Duplicate prevention rate: {metrics['duplicate_prevention_rate']:.1f}%")
                print(f"   Average quality: {metrics['average_quality_score']:.1f}/100")
                
            except Exception as e:
                print(f"❌ Cycle {cycle} failed: {e}")
            
            if cycle < cycles:
                print(f"😴 Sleeping {interval} seconds...")
                time.sleep(interval)
        
        print(f"🏁 Continuous enrichment completed!")
    
    def stop(self):
        """Stop the organism"""
        self.running = False
        print("🛑 Production organism stopped")

def main():
    """Run production organism"""
    organism = ProductionCleanOrganism()
    
    try:
        # Run for 10 cycles as demo
        organism.run_continuous(cycles=10, interval=30)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    finally:
        organism.stop()

if __name__ == "__main__":
    main()
