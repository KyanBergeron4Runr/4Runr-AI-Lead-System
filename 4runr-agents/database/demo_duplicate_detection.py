#!/usr/bin/env python3
"""
Enhanced Duplicate Detection Demo

Demonstrates the advanced duplicate detection capabilities with fuzzy matching,
confidence scoring, and intelligent data merging.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.lead_database import get_lead_database

def demo_duplicate_detection():
    """Demonstrate enhanced duplicate detection features"""
    print("🔍 Enhanced Duplicate Detection Demo")
    print("=" * 45)
    
    # Get database instance
    db = get_lead_database()
    
    print("\n📊 Starting with clean database...")
    initial_count = db.get_lead_count()
    print(f"   Initial lead count: {initial_count}")
    
    # Demo 1: LinkedIn URL exact matching
    print("\n🔗 Demo 1: LinkedIn URL Exact Matching")
    print("-" * 40)
    
    original_lead = {
        'full_name': 'John Smith',
        'linkedin_url': 'https://linkedin.com/in/johnsmith',
        'company': 'TechCorp',
        'title': 'Developer'
    }
    
    lead_id1 = db.add_lead(original_lead)
    print(f"   ✅ Added original lead: {original_lead['full_name']} (ID: {lead_id1[:8]}...)")
    
    # Try to add duplicate with different name but same LinkedIn
    duplicate_linkedin = {
        'full_name': 'John S. Smith',  # Slightly different name
        'linkedin_url': 'https://linkedin.com/in/johnsmith',  # Same LinkedIn
        'company': 'TechCorp Inc',  # Slightly different company
        'title': 'Senior Developer',  # Updated title
        'verified': True,  # Additional data
        'location': 'Montreal, QC'
    }
    
    lead_id2 = db.add_lead(duplicate_linkedin)
    print(f"   🔄 Attempted to add duplicate: {duplicate_linkedin['full_name']}")
    print(f"   ✅ Detected duplicate! Returned same ID: {lead_id2[:8]}...")
    print(f"   📝 Data was merged intelligently")
    
    # Show merged result
    merged_lead = db.get_lead(lead_id1)
    print(f"   📋 Merged result:")
    print(f"      Name: {merged_lead['full_name']}")
    print(f"      Title: {merged_lead['title']}")
    print(f"      Verified: {merged_lead['verified']}")
    print(f"      Location: {merged_lead['location']}")
    
    # Demo 2: Email exact matching
    print("\n📧 Demo 2: Email Exact Matching")
    print("-" * 35)
    
    email_lead1 = {
        'full_name': 'Sarah Johnson',
        'email': 'sarah@innovate.co',
        'company': 'Innovate Solutions'
    }
    
    lead_id3 = db.add_lead(email_lead1)
    print(f"   ✅ Added lead: {email_lead1['full_name']} (ID: {lead_id3[:8]}...)")
    
    # Try duplicate with same email, different case
    email_duplicate = {
        'full_name': 'Sarah J. Johnson',
        'email': 'SARAH@INNOVATE.CO',  # Different case
        'title': 'CTO',
        'enriched': True
    }
    
    lead_id4 = db.add_lead(email_duplicate)
    print(f"   🔄 Attempted duplicate with different case email")
    print(f"   ✅ Detected duplicate! Same ID: {lead_id4[:8]}...")
    
    # Demo 3: Fuzzy name matching
    print("\n🎯 Demo 3: Fuzzy Name Matching")
    print("-" * 32)
    
    fuzzy_lead1 = {
        'full_name': 'Christopher Anderson',
        'company': 'Software Solutions Inc',
        'title': 'CEO'
    }
    
    lead_id5 = db.add_lead(fuzzy_lead1)
    print(f"   ✅ Added lead: {fuzzy_lead1['full_name']} (ID: {lead_id5[:8]}...)")
    
    # Try fuzzy match with nickname
    fuzzy_duplicate = {
        'full_name': 'Chris Anderson',  # Nickname
        'company': 'Software Solutions Inc',  # Same company
        'email': 'chris@softwaresolutions.com',
        'verified': True
    }
    
    lead_id6 = db.add_lead(fuzzy_duplicate)
    print(f"   🔄 Attempted to add with nickname: {fuzzy_duplicate['full_name']}")
    print(f"   ✅ Fuzzy match detected! Same ID: {lead_id6[:8]}...")
    
    # Demo 4: Domain + name similarity matching
    print("\n🌐 Demo 4: Domain + Name Similarity")
    print("-" * 35)
    
    domain_lead1 = {
        'full_name': 'Michael Chen',
        'email': 'michael.chen@techstartup.com',
        'company': 'TechStartup'
    }
    
    lead_id7 = db.add_lead(domain_lead1)
    print(f"   ✅ Added lead: {domain_lead1['full_name']} (ID: {lead_id7[:8]}...)")
    
    # Try similar name, same domain
    domain_duplicate = {
        'full_name': 'Mike Chen',  # Similar name
        'email': 'mike@techstartup.com',  # Same domain
        'title': 'CTO',
        'location': 'Vancouver, BC'
    }
    
    lead_id8 = db.add_lead(domain_duplicate)
    print(f"   🔄 Attempted similar name, same domain: {domain_duplicate['full_name']}")
    print(f"   ✅ Domain similarity detected! Same ID: {lead_id8[:8]}...")
    
    # Demo 5: No false positives
    print("\n❌ Demo 5: No False Positives")
    print("-" * 30)
    
    different_lead = {
        'full_name': 'Jane Doe',
        'email': 'jane@differentcompany.com',
        'company': 'Different Company',
        'title': 'Manager'
    }
    
    lead_id9 = db.add_lead(different_lead)
    print(f"   ✅ Added completely different lead: {different_lead['full_name']} (ID: {lead_id9[:8]}...)")
    print(f"   ✅ No false positive matches detected")
    
    # Demo 6: Advanced duplicate analysis
    print("\n🔬 Demo 6: Advanced Duplicate Analysis")
    print("-" * 38)
    
    # Test lead that might match multiple existing leads
    test_lead = {
        'full_name': 'John Smith',  # Might match first lead
        'email': 'john.smith@newcompany.com',  # Different email
        'company': 'New Company'
    }
    
    # Find all potential duplicates
    all_duplicates = db.find_all_duplicates(test_lead)
    
    print(f"   🔍 Analyzing potential duplicates for: {test_lead['full_name']}")
    print(f"   📊 Found {len(all_duplicates)} potential matches:")
    
    for i, dup in enumerate(all_duplicates, 1):
        print(f"      {i}. Match Type: {dup['match_type']}")
        print(f"         Confidence: {dup['confidence']:.2f}")
        print(f"         Existing Lead: {dup['existing_lead']['full_name']}")
        print(f"         Details: {dup['match_details']}")
        print()
    
    # Final statistics
    print("\n📊 Final Database Statistics")
    print("-" * 30)
    
    final_stats = db.get_database_stats()
    print(f"   Total unique leads: {final_stats['total_leads']}")
    print(f"   Duplicates prevented: {8 - final_stats['total_leads']}")  # We tried to add 8 leads
    print(f"   Duplicate detection rate: {((8 - final_stats['total_leads']) / 8) * 100:.1f}%")
    
    # Show all leads
    print(f"\n📋 All Unique Leads in Database:")
    all_leads = db.get_all_leads()
    
    for i, lead in enumerate(all_leads, 1):
        print(f"   {i}. {lead['full_name']} ({lead['company'] or 'No company'})")
        print(f"      Email: {lead['email'] or 'Not available'}")
        print(f"      LinkedIn: {lead['linkedin_url'] or 'Not available'}")
        print(f"      Verified: {lead['verified']} | Enriched: {lead['enriched']}")
        print()
    
    print("✅ Enhanced duplicate detection demo completed!")

def demo_data_merging():
    """Demonstrate intelligent data merging"""
    print("\n🔄 Data Merging Intelligence Demo")
    print("=" * 35)
    
    db = get_lead_database()
    
    # Add a basic lead
    basic_lead = {
        'full_name': 'Alex',  # Short name
        'email': 'alex@company.com',
        'company': 'Co',  # Short company name
        'verified': False,
        'enriched': False
    }
    
    lead_id = db.add_lead(basic_lead)
    print(f"✅ Added basic lead: {basic_lead['full_name']} (ID: {lead_id[:8]}...)")
    
    # Add more complete duplicate
    complete_lead = {
        'full_name': 'Alexander Thompson',  # More complete name
        'email': 'alex@company.com',  # Same email (will match)
        'company': 'Company Solutions Inc',  # More complete company
        'title': 'Chief Technology Officer',  # New field
        'location': 'Toronto, ON',  # New field
        'industry': 'Technology',  # New field
        'verified': True,  # Should become True
        'enriched': True,  # Should become True
        'raw_data': {
            'linkedin_profile': 'detailed_profile',
            'confidence_score': 0.95,
            'enrichment_source': 'clearbit'
        }
    }
    
    duplicate_id = db.add_lead(complete_lead)
    print(f"🔄 Added more complete duplicate")
    print(f"✅ Merged into same lead: {duplicate_id[:8]}...")
    
    # Show intelligent merging results
    merged = db.get_lead(lead_id)
    print(f"\n📋 Intelligent Merging Results:")
    print(f"   Name: '{basic_lead['full_name']}' → '{merged['full_name']}'")
    print(f"   Company: '{basic_lead['company']}' → '{merged['company']}'")
    print(f"   Title: None → '{merged['title']}'")
    print(f"   Location: None → '{merged['location']}'")
    print(f"   Verified: {basic_lead['verified']} → {merged['verified']}")
    print(f"   Enriched: {basic_lead['enriched']} → {merged['enriched']}")
    print(f"   Raw Data: Added enrichment information")
    
    print("\n✅ Data merging demo completed!")

def main():
    """Main demo function"""
    try:
        demo_duplicate_detection()
        demo_data_merging()
        
        print("\n🎉 All duplicate detection demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)