#!/usr/bin/env python3
"""
Lead Database API Demo

Demonstrates how to use the Lead Database API for common operations.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.lead_database import get_lead_database

def demo_basic_operations():
    """Demonstrate basic CRUD operations"""
    print("🔧 Lead Database API Demo")
    print("=" * 40)
    
    # Get database instance
    db = get_lead_database()
    
    print("\n📊 Initial database stats:")
    stats = db.get_database_stats()
    print(f"   Total leads: {stats['total_leads']}")
    print(f"   Database size: {stats['database_size_mb']} MB")
    
    # Add some sample leads
    print("\n➕ Adding sample leads...")
    
    sample_leads = [
        {
            'full_name': 'John Smith',
            'email': 'john.smith@techcorp.com',
            'company': 'TechCorp Inc',
            'title': 'CEO',
            'linkedin_url': 'https://linkedin.com/in/johnsmith',
            'location': 'Montreal, QC',
            'industry': 'Technology',
            'source': 'LinkedIn Scraper',
            'scraped_at': datetime.now()
        },
        {
            'full_name': 'Sarah Johnson',
            'email': 'sarah@innovate.co',
            'company': 'Innovate Solutions',
            'title': 'CTO',
            'linkedin_url': 'https://linkedin.com/in/sarahjohnson',
            'location': 'Toronto, ON',
            'industry': 'Software',
            'source': 'Manual Entry',
            'verified': True
        },
        {
            'full_name': 'Mike Chen',
            'company': 'StartupXYZ',
            'title': 'Founder',
            'linkedin_url': 'https://linkedin.com/in/mikechen',
            'location': 'Vancouver, BC',
            'industry': 'Fintech',
            'needs_enrichment': True
        }
    ]
    
    lead_ids = []
    for lead_data in sample_leads:
        try:
            lead_id = db.add_lead(lead_data)
            lead_ids.append(lead_id)
            print(f"   ✅ Added: {lead_data['full_name']} (ID: {lead_id[:8]}...)")
        except Exception as e:
            print(f"   ❌ Failed to add {lead_data['full_name']}: {e}")
    
    # Demonstrate duplicate detection
    print("\n🔍 Testing duplicate detection...")
    duplicate_lead = {
        'full_name': 'John Smith Updated',  # Different name
        'email': 'john.smith@techcorp.com',  # Same email
        'company': 'TechCorp Inc',
        'title': 'Chief Executive Officer',  # Updated title
        'enriched': True,
        'enriched_at': datetime.now()
    }
    
    duplicate_id = db.add_lead(duplicate_lead)
    if duplicate_id == lead_ids[0]:
        print(f"   ✅ Duplicate detected and updated (ID: {duplicate_id[:8]}...)")
    else:
        print(f"   ❌ Duplicate detection failed")
    
    # Retrieve and display leads
    print("\n📋 Current leads in database:")
    all_leads = db.get_all_leads()
    
    for lead in all_leads:
        print(f"   • {lead['full_name']} ({lead['company']})")
        print(f"     Email: {lead['email'] or 'Not available'}")
        print(f"     Status: {lead['status']} | Enriched: {lead['enriched']}")
        print(f"     Created: {lead['created_at'][:19]}")
        print()
    
    # Demonstrate search functionality
    print("🔍 Search examples:")
    
    # Search by company
    tech_leads = db.search_leads({'company': 'TechCorp Inc'})
    print(f"   TechCorp leads: {len(tech_leads)}")
    
    # Search by enrichment status
    enriched_leads = db.search_leads({'enriched': True})
    print(f"   Enriched leads: {len(enriched_leads)}")
    
    # Search by location (wildcard)
    montreal_leads = db.search_leads({'location': '%Montreal%'})
    print(f"   Montreal leads: {len(montreal_leads)}")
    
    # Demonstrate lead updates
    print("\n✏️ Updating lead data...")
    if lead_ids:
        first_lead_id = lead_ids[0]
        updates = {
            'verified': True,
            'status': 'contacted',
            'raw_data': {
                'last_contact': datetime.now().isoformat(),
                'contact_method': 'email',
                'response_received': False
            }
        }
        
        success = db.update_lead(first_lead_id, updates)
        if success:
            print(f"   ✅ Updated lead {first_lead_id[:8]}...")
            
            # Show updated lead
            updated_lead = db.get_lead(first_lead_id)
            print(f"   Status: {updated_lead['status']}")
            print(f"   Verified: {updated_lead['verified']}")
            print(f"   Raw data: {updated_lead['raw_data']}")
    
    # Demonstrate sync operations
    print("\n🔄 Sync operations:")
    
    # Mark leads for sync
    for lead_id in lead_ids[:2]:  # Mark first 2 leads
        db.mark_for_sync(lead_id)
    
    # Get pending sync leads
    pending_leads = db.get_sync_pending_leads()
    print(f"   Leads pending sync: {len(pending_leads)}")
    
    for lead in pending_leads:
        print(f"   • {lead['full_name']} (ID: {lead['id'][:8]}...)")
    
    # Final statistics
    print("\n📊 Final database statistics:")
    final_stats = db.get_database_stats()
    
    print(f"   Total leads: {final_stats['total_leads']}")
    print(f"   Status breakdown: {final_stats['status_counts']}")
    print(f"   Enriched leads: {final_stats['enriched_leads']}")
    print(f"   Pending sync: {final_stats['pending_sync']}")
    print(f"   Database size: {final_stats['database_size_mb']} MB")
    
    print("\n✅ Demo completed successfully!")

def demo_advanced_features():
    """Demonstrate advanced features"""
    print("\n🚀 Advanced Features Demo")
    print("=" * 30)
    
    db = get_lead_database()
    
    # Complex search with multiple criteria
    print("\n🔍 Complex search example:")
    complex_search = db.search_leads({
        'industry': 'Technology',
        'verified': True,
        'enriched': False
    })
    
    print(f"   Tech leads that are verified but not enriched: {len(complex_search)}")
    
    # Pagination example
    print("\n📄 Pagination example:")
    page_size = 2
    page_1 = db.get_all_leads(limit=page_size, offset=0)
    page_2 = db.get_all_leads(limit=page_size, offset=page_size)
    
    print(f"   Page 1 ({len(page_1)} leads):")
    for lead in page_1:
        print(f"     • {lead['full_name']}")
    
    print(f"   Page 2 ({len(page_2)} leads):")
    for lead in page_2:
        print(f"     • {lead['full_name']}")
    
    # Raw data handling
    print("\n📦 Raw data handling:")
    lead_with_complex_data = {
        'full_name': 'Complex Data Lead',
        'email': 'complex@example.com',
        'raw_data': {
            'enrichment_sources': ['linkedin', 'clearbit', 'hunter'],
            'confidence_scores': {
                'email': 0.95,
                'company': 0.87,
                'title': 0.92
            },
            'social_profiles': {
                'twitter': '@complexlead',
                'github': 'complexlead'
            },
            'contact_attempts': [
                {'date': '2024-01-15', 'method': 'email', 'success': False},
                {'date': '2024-01-20', 'method': 'linkedin', 'success': True}
            ]
        }
    }
    
    complex_lead_id = db.add_lead(lead_with_complex_data)
    retrieved_complex = db.get_lead(complex_lead_id)
    
    print(f"   Complex lead added: {complex_lead_id[:8]}...")
    print(f"   Enrichment sources: {retrieved_complex['raw_data']['enrichment_sources']}")
    print(f"   Email confidence: {retrieved_complex['raw_data']['confidence_scores']['email']}")

def main():
    """Main demo function"""
    try:
        demo_basic_operations()
        demo_advanced_features()
        
        print("\n🎉 All demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)