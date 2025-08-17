#!/usr/bin/env python3
"""
REAL PATTERN ENGINE TEST - NO BS
================================
Testing our pattern engine with ACTUAL real leads from the database.
NO fake data, NO made-up results.
"""

import sqlite3
import json
from pattern_based_email_engine import PatternBasedEmailEngine

def get_real_leads_from_database():
    """Get actual real leads from our database"""
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT full_name, company, job_title, email, linkedin_url
            FROM leads 
            WHERE full_name IS NOT NULL 
            AND company IS NOT NULL
            AND full_name != ''
            AND company != ''
            LIMIT 5
        """)
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"📊 Found {len(leads)} real leads in database")
        return leads
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []

def test_pattern_engine_with_real_data():
    """Test pattern engine with real leads - NO FAKE DATA"""
    print("🔥 REAL PATTERN ENGINE TEST - NO BS")
    print("=" * 60)
    print("Testing with ACTUAL leads from our database")
    print()
    
    # Get real leads
    real_leads = get_real_leads_from_database()
    
    if not real_leads:
        print("❌ No real leads found in database to test with")
        return
    
    # Initialize engine
    engine = PatternBasedEmailEngine()
    
    print("📋 REAL LEADS TO TEST:")
    for i, lead in enumerate(real_leads, 1):
        print(f"{i}. {lead['full_name']} at {lead['company']}")
        if lead.get('email'):
            print(f"   Known email: {lead['email']}")
        print()
    
    print("🔍 TESTING PATTERN ENGINE:")
    print("=" * 40)
    
    for i, lead in enumerate(real_leads, 1):
        print(f"\n{i}. TESTING: {lead['full_name']} at {lead['company']}")
        print("-" * 50)
        
        # Test our pattern engine
        try:
            results = engine.discover_emails(lead)
            
            print(f"📧 Pattern engine found {len(results)} email candidates:")
            
            if results:
                # Show top 10 results
                for j, email_result in enumerate(results[:10], 1):
                    print(f"   {j}. {email_result.email}")
                    print(f"      Confidence: {email_result.confidence.value}")
                    print(f"      Pattern: {email_result.pattern_used}")
                    print(f"      Validation Score: {email_result.validation_score}")
                    
                    # Check if we found the known email
                    if lead.get('email') and email_result.email.lower() == lead['email'].lower():
                        print(f"      🎯 MATCH! Found the known email!")
                    print()
                
                if len(results) > 10:
                    print(f"   ... and {len(results) - 10} more candidates")
            else:
                print("   ❌ No valid email candidates found")
                
        except Exception as e:
            print(f"   ❌ Engine failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 REAL TEST COMPLETE - NO FAKE DATA USED")
    print("Results above are from actual database leads and real domain validation")

if __name__ == "__main__":
    test_pattern_engine_with_real_data()
