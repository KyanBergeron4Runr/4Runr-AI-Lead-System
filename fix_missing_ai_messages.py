#!/usr/bin/env python3
"""
Fix Missing AI Messages - Direct database update
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def generate_ai_message(lead_data):
    """Generate a simple AI message for a lead"""
    name = lead_data.get('full_name', 'there')
    company = lead_data.get('company', 'your company')
    
    message = f"""Hi {name},

I noticed {company} and thought you might be interested in how we're helping businesses like yours optimize their operations.

Would you be open to a quick 15-minute call to discuss how we could potentially help {company}?

Best regards,
The 4Runr Team"""
    
    return message

def fix_missing_ai_messages():
    """Fix missing AI messages in the database"""
    print("🔧 Fixing Missing AI Messages")
    print("=" * 50)
    
    try:
        # Connect to unified database
        db_path = Path("data/unified_leads.db")
        if not db_path.exists():
            print("❌ Unified database not found")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get leads without AI messages
        cursor.execute("""
            SELECT id, full_name, company, email, linkedin_url
            FROM leads 
            WHERE (ai_message IS NULL OR ai_message = '') 
            AND company IS NOT NULL 
            AND company != ''
        """)
        
        leads_without_messages = cursor.fetchall()
        
        if not leads_without_messages:
            print("✅ All leads already have AI messages")
            conn.close()
            return True
        
        print(f"Found {len(leads_without_messages)} leads without AI messages")
        
        # Generate and update AI messages
        updated_count = 0
        for lead in leads_without_messages:
            lead_id, full_name, company, email, linkedin_url = lead
            
            # Create lead data for message generation
            lead_data = {
                'full_name': full_name,
                'company': company,
                'email': email,
                'linkedin_url': linkedin_url
            }
            
            # Generate AI message
            ai_message = generate_ai_message(lead_data)
            
            # Update database
            cursor.execute("""
                UPDATE leads 
                SET ai_message = ?, updated_at = ?
                WHERE id = ?
            """, (ai_message, datetime.now().isoformat(), lead_id))
            
            updated_count += 1
            print(f"✅ Updated lead {lead_id}: {full_name} at {company}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Successfully updated {updated_count} leads with AI messages")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing AI messages: {e}")
        return False

def check_results():
    """Check the results after fixing"""
    print("\n📊 Checking Results")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("data/unified_leads.db")
        cursor = conn.cursor()
        
        # Get updated stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN ai_message IS NOT NULL AND ai_message != '' THEN 1 END) as with_ai_messages,
                COUNT(CASE WHEN enriched = 1 THEN 1 END) as enriched_leads
            FROM leads
        """)
        
        result = cursor.fetchone()
        total_leads, with_ai_messages, enriched_leads = result
        
        print(f"Total leads: {total_leads}")
        print(f"Leads with AI messages: {with_ai_messages} ({with_ai_messages/total_leads*100:.1f}%)")
        print(f"Enriched leads: {enriched_leads} ({enriched_leads/total_leads*100:.1f}%)")
        
        conn.close()
        
        if with_ai_messages == total_leads:
            print("\n🎉 All leads now have AI messages!")
            return True
        else:
            print(f"\n⚠️ Still missing AI messages for {total_leads - with_ai_messages} leads")
            return False
            
    except Exception as e:
        print(f"❌ Error checking results: {e}")
        return False

def main():
    """Main function"""
    print("🔧 4Runr AI Lead System - Fix Missing AI Messages")
    print("=" * 60)
    
    # Fix missing AI messages
    success = fix_missing_ai_messages()
    
    if success:
        # Check results
        check_results()
        
        print("\n✅ AI messages fix completed!")
        print("\nNext steps:")
        print("1. Run enrichment: python fix_enrichment.py")
        print("2. Set up automation: python fix_automation_issues.py")
    else:
        print("\n❌ Failed to fix AI messages")

if __name__ == "__main__":
    main()
