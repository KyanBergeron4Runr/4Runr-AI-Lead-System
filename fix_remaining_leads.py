#!/usr/bin/env python3
"""
Fix all remaining leads to meet production standards
"""

import sqlite3
import logging
from final_lead_enhancement import FinalLeadEnhancer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LeadFixer:
    def __init__(self):
        self.db_path = 'data/unified_leads.db'
        
    def fix_all_leads(self):
        """Fix all leads to production standards."""
        logger.info("FIXING ALL LEADS TO PRODUCTION STANDARDS")
        logger.info("=" * 50)
        
        # Get current stats
        self.show_current_stats()
        
        # Fix all leads
        enhancer = FinalLeadEnhancer()
        enhancer.enhance_all_leads()
        
        # Show final stats
        self.show_final_stats()
        
    def show_current_stats(self):
        """Show current lead statistics."""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute('SELECT COUNT(*) FROM leads')
        total = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT COUNT(*) FROM leads WHERE business_type IS NOT NULL AND business_type != ""')
        with_business_type = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT COUNT(*) FROM leads WHERE ai_message IS NOT NULL AND LENGTH(ai_message) > 500')
        with_quality_messages = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"CURRENT STATUS:")
        logger.info(f"  Total leads: {total}")
        logger.info(f"  With business type: {with_business_type} ({with_business_type/total*100:.1f}%)")
        logger.info(f"  With quality AI messages: {with_quality_messages} ({with_quality_messages/total*100:.1f}%)")
        
    def show_final_stats(self):
        """Show final lead statistics."""
        logger.info("\nFINAL STATUS AFTER ENHANCEMENT:")
        self.show_current_stats()

if __name__ == "__main__":
    fixer = LeadFixer()
    fixer.fix_all_leads()
