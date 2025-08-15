#!/usr/bin/env python3
"""
Fix Organism Validation
======================
Add proper validation to prevent bad leads from being saved
"""

import sqlite3
import re
from typing import Dict, Any, Optional

def validate_prospect_data(prospect: Dict[str, Any]) -> tuple[bool, str]:
    """Validate prospect data before saving to database"""
    
    # Check full name
    full_name = prospect.get('name', '').strip()
    if not full_name:
        return False, "Missing full name"
    
    if len(full_name) < 3:
        return False, "Full name too short"
    
    # Must have both first and last name (contains space)
    if ' ' not in full_name:
        return False, "Must have both first and last name"
    
    # Check for weird characters or numbers in name
    if re.search(r'[0-9@#$%^&*()+={}[\]\\|;:"<>?,./]', full_name):
        return False, "Invalid characters in name"
    
    # Check email format
    email = prospect.get('email', '').strip()
    if not email or '@' not in email or '.' not in email:
        return False, "Invalid email format"
    
    # Check company
    company = prospect.get('company', '').strip()
    if not company or len(company) < 2:
        return False, "Missing or invalid company"
    
    # Check job title
    job_title = prospect.get('job_title', '').strip()
    if not job_title:
        return False, "Missing job title"
    
    return True, "Valid"

def create_enhanced_organism_save_method():
    """Create the enhanced save method with validation"""
    
    enhanced_save_code = '''
def save_prospects_to_database(self, prospects: List[Dict]) -> int:
    """Save prospects to database with enhanced validation"""
    
    self.logger.info(f"💾 Saving {len(prospects)} prospects to database")
    
    conn = sqlite3.connect(self.db_path)
    saved_count = 0
    
    for prospect in prospects:
        try:
            # ENHANCED VALIDATION - Prevent bad data entry
            full_name = prospect.get('name', '').strip()
            
            # Validate name format
            if not full_name or len(full_name) < 3:
                self.logger.error(f"❌ Invalid name (too short): '{full_name}'")
                continue
                
            if ' ' not in full_name:
                self.logger.error(f"❌ Invalid name (missing last name): '{full_name}'")
                continue
                
            # Check for invalid characters
            import re
            if re.search(r'[0-9@#$%^&*()+={}[\\]\\\\|;:"<>?,./]', full_name):
                self.logger.error(f"❌ Invalid name (bad characters): '{full_name}'")
                continue
            
            # Validate email
            email = prospect.get('email', '').strip()
            if not email or '@' not in email:
                self.logger.error(f"❌ Invalid email for {full_name}: '{email}'")
                continue
            
            # Validate company
            company = prospect.get('company', '').strip()
            if not company or len(company) < 2:
                self.logger.error(f"❌ Invalid company for {full_name}: '{company}'")
                continue
            
            # Check for duplicates
            cursor = conn.execute(
                "SELECT id FROM leads WHERE full_name = ? OR email = ?",
                (full_name, email)
            )
            
            if cursor.fetchone():
                self.logger.warning(f"⚠️ Duplicate prospect: {full_name}")
                continue
            
            # All validation passed - save the prospect
            conn.execute("""
                INSERT INTO leads (
                    full_name, email, company, job_title, linkedin_url,
                    industry, business_type, source, date_scraped, date_enriched,
                    created_at, enriched, ready_for_outreach, score, lead_quality,
                    website, email_confidence_level, ai_message, needs_enrichment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                full_name, email, company,
                prospect['job_title'], prospect['linkedin_url'], prospect['industry'],
                prospect['business_type'], prospect['source'], prospect['date_scraped'],
                prospect['date_enriched'], prospect['generated_at'], 1, 1,
                prospect['quality_score'], prospect['lead_quality'], prospect['website'],
                prospect['email_confidence_level'], prospect['ai_message'], 0
            ))
            
            saved_count += 1
            self.logger.info(f"✅ Saved: {full_name} (validated)")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving {prospect.get('name', 'Unknown')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    self.logger.info(f"📊 Saved {saved_count} prospects to database")
    return saved_count
'''
    
    return enhanced_save_code

if __name__ == "__main__":
    print("🔧 Enhanced Organism Validation")
    print("=" * 40)
    print()
    print("This script provides enhanced validation logic")
    print("to prevent invalid leads from being saved.")
    print()
    print("The validation checks:")
    print("✅ Full name must exist and be 3+ characters")
    print("✅ Must have both first and last name (space required)")
    print("✅ No invalid characters or numbers in names")
    print("✅ Valid email format (@, . required)")
    print("✅ Company name must exist and be meaningful")
    print("✅ Job title must exist")
    print()
    print("To implement this, copy the enhanced save method")
    print("into the autonomous_4runr_organism.py file.")
