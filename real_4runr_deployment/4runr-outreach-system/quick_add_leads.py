#!/usr/bin/env python3
"""
Quick Lead Addition Script

This script quickly adds test data to the database using direct SQL to avoid
connection pool issues.
"""

import sys
import sqlite3
import datetime
import uuid
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def create_test_leads():
    """Create comprehensive test data."""
    print("📝 Creating comprehensive test data...")
    
    # Realistic test data with various industries and company types
    test_leads = [
        # Travel & Hospitality
        {
            'full_name': 'Sarah Johnson',
            'email': 'sarah.johnson@luxuryhotels.com',
            'company': 'Luxury Hotels International',
            'title': 'VP of Operations',
            'linkedin_url': 'https://linkedin.com/in/sarahjohnson-luxury',
            'website': 'luxuryhotels.com',
            'location': 'Miami, FL',
            'industry': 'Hospitality',
            'company_size': '500-1000',
            'source': 'LinkedIn',
            'status': 'new'
        },
        {
            'full_name': 'Michael Chen',
            'email': 'mchen@traveltech.co',
            'company': 'TravelTech Solutions',
            'title': 'Chief Technology Officer',
            'linkedin_url': 'https://linkedin.com/in/michaelchen-cto',
            'website': 'traveltech.co',
            'location': 'San Francisco, CA',
            'industry': 'Travel Technology',
            'company_size': '50-200',
            'source': 'Website Scraping',
            'status': 'new'
        },
        {
            'full_name': 'Emily Rodriguez',
            'email': 'emily@vacationrentals.net',
            'company': 'Vacation Rentals Network',
            'title': 'Marketing Director',
            'linkedin_url': 'https://linkedin.com/in/emilyrodriguez-marketing',
            'website': 'vacationrentals.net',
            'location': 'Austin, TX',
            'industry': 'Real Estate',
            'company_size': '100-500',
            'source': 'LinkedIn',
            'status': 'new'
        },
        
        # E-commerce & Retail
        {
            'full_name': 'David Kim',
            'email': 'david.kim@shopify.com',
            'company': 'Shopify Plus',
            'title': 'Senior Account Executive',
            'linkedin_url': 'https://linkedin.com/in/davidkim-shopify',
            'website': 'shopify.com',
            'location': 'Toronto, ON',
            'industry': 'E-commerce',
            'company_size': '1000+',
            'source': 'LinkedIn',
            'status': 'new'
        },
        {
            'full_name': 'Lisa Thompson',
            'email': 'lisa@fashionboutique.com',
            'company': 'Fashion Boutique Online',
            'title': 'Founder & CEO',
            'linkedin_url': 'https://linkedin.com/in/lisathompson-founder',
            'website': 'fashionboutique.com',
            'location': 'New York, NY',
            'industry': 'Fashion Retail',
            'company_size': '10-50',
            'source': 'Website Scraping',
            'status': 'new'
        },
        
        # Fintech & Financial Services
        {
            'full_name': 'Robert Wilson',
            'email': 'r.wilson@fintechpay.com',
            'company': 'FinTech Payments',
            'title': 'VP of Business Development',
            'linkedin_url': 'https://linkedin.com/in/robertwilson-fintech',
            'website': 'fintechpay.com',
            'location': 'Chicago, IL',
            'industry': 'Fintech',
            'company_size': '200-500',
            'source': 'LinkedIn',
            'status': 'new'
        },
        {
            'full_name': 'Jennifer Park',
            'email': 'jennifer@cryptobank.io',
            'company': 'CryptoBank Solutions',
            'title': 'Head of Marketing',
            'linkedin_url': 'https://linkedin.com/in/jenniferpark-crypto',
            'website': 'cryptobank.io',
            'location': 'Seattle, WA',
            'industry': 'Cryptocurrency',
            'company_size': '50-200',
            'source': 'Website Scraping',
            'status': 'new'
        },
        
        # Healthcare & Medical
        {
            'full_name': 'Dr. Amanda Foster',
            'email': 'amanda.foster@medtech.com',
            'company': 'MedTech Innovations',
            'title': 'Chief Medical Officer',
            'linkedin_url': 'https://linkedin.com/in/amandafoster-cmo',
            'website': 'medtech.com',
            'location': 'Boston, MA',
            'industry': 'Healthcare Technology',
            'company_size': '100-500',
            'source': 'LinkedIn',
            'status': 'new'
        },
        {
            'full_name': 'Carlos Martinez',
            'email': 'carlos@healthstartup.co',
            'company': 'HealthStartup',
            'title': 'CEO & Co-Founder',
            'linkedin_url': 'https://linkedin.com/in/carlosmartinez-ceo',
            'website': 'healthstartup.co',
            'location': 'Los Angeles, CA',
            'industry': 'Digital Health',
            'company_size': '10-50',
            'source': 'Website Scraping',
            'status': 'new'
        },
        
        # SaaS & Technology
        {
            'full_name': 'Alex Turner',
            'email': 'alex@saasplatform.com',
            'company': 'SaaS Platform Inc',
            'title': 'VP of Sales',
            'linkedin_url': 'https://linkedin.com/in/alexturner-sales',
            'website': 'saasplatform.com',
            'location': 'Denver, CO',
            'industry': 'SaaS',
            'company_size': '200-500',
            'source': 'LinkedIn',
            'status': 'new'
        },
        {
            'full_name': 'Rachel Green',
            'email': 'rachel@aiautomation.io',
            'company': 'AI Automation Labs',
            'title': 'Product Manager',
            'linkedin_url': 'https://linkedin.com/in/rachelgreen-pm',
            'website': 'aiautomation.io',
            'location': 'Palo Alto, CA',
            'industry': 'Artificial Intelligence',
            'company_size': '50-200',
            'source': 'Website Scraping',
            'status': 'new'
        },
        
        # Education & Training
        {
            'full_name': 'Dr. James Brown',
            'email': 'james.brown@edutech.edu',
            'company': 'EduTech University',
            'title': 'Dean of Technology',
            'linkedin_url': 'https://linkedin.com/in/jamesbrown-dean',
            'website': 'edutech.edu',
            'location': 'Atlanta, GA',
            'industry': 'Education Technology',
            'company_size': '500-1000',
            'source': 'LinkedIn',
            'status': 'new'
        },
        {
            'full_name': 'Maria Garcia',
            'email': 'maria@onlinelearning.com',
            'company': 'Online Learning Platform',
            'title': 'Director of Partnerships',
            'linkedin_url': 'https://linkedin.com/in/mariagarcia-partnerships',
            'website': 'onlinelearning.com',
            'location': 'Phoenix, AZ',
            'industry': 'Online Education',
            'company_size': '100-500',
            'source': 'Website Scraping',
            'status': 'new'
        },
        
        # Real Estate & Property
        {
            'full_name': 'Thomas Anderson',
            'email': 'thomas@proprealty.com',
            'company': 'PropRealty Group',
            'title': 'Managing Director',
            'linkedin_url': 'https://linkedin.com/in/thomasanderson-md',
            'website': 'proprealty.com',
            'location': 'Dallas, TX',
            'industry': 'Real Estate',
            'company_size': '200-500',
            'source': 'LinkedIn',
            'status': 'new'
        },
        {
            'full_name': 'Sophie Williams',
            'email': 'sophie@smartproperties.com',
            'company': 'Smart Properties',
            'title': 'Innovation Manager',
            'linkedin_url': 'https://linkedin.com/in/sophiewilliams-innovation',
            'website': 'smartproperties.com',
            'location': 'Portland, OR',
            'industry': 'PropTech',
            'company_size': '50-200',
            'source': 'Website Scraping',
            'status': 'new'
        },
        
        # Marketing & Advertising
        {
            'full_name': 'Kevin O\'Connor',
            'email': 'kevin@digitalmarketing.com',
            'company': 'Digital Marketing Agency',
            'title': 'Creative Director',
            'linkedin_url': 'https://linkedin.com/in/kevinoconnor-creative',
            'website': 'digitalmarketing.com',
            'location': 'Nashville, TN',
            'industry': 'Digital Marketing',
            'company_size': '100-500',
            'source': 'LinkedIn',
            'status': 'new'
        },
        {
            'full_name': 'Nina Patel',
            'email': 'nina@adtechstartup.com',
            'company': 'AdTech Startup',
            'title': 'VP of Engineering',
            'linkedin_url': 'https://linkedin.com/in/ninapatel-engineering',
            'website': 'adtechstartup.com',
            'location': 'San Diego, CA',
            'industry': 'Advertising Technology',
            'company_size': '10-50',
            'source': 'Website Scraping',
            'status': 'new'
        }
    ]
    
    return test_leads


def add_leads_directly():
    """Add leads directly to the database using SQL."""
    print("🚀 Adding leads directly to database...")
    
    try:
        # Connect directly to database
        db_path = "4runr-outreach-system/data/leads_cache.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get test data
        test_leads = create_test_leads()
        
        # Add each lead
        added_count = 0
        for i, lead_data in enumerate(test_leads, 1):
            print(f"   📝 Adding lead {i}/{len(test_leads)}: {lead_data['full_name']}")
            
            # Generate UUID
            lead_uuid = str(uuid.uuid4())
            
            # Prepare data for insertion
            now = datetime.datetime.now().isoformat()
            
            # Insert lead
            cursor.execute("""
                INSERT INTO leads (
                    uuid, full_name, email, company, title, linkedin_url, company_website,
                    location, industry, company_size, source, status, verified,
                    enriched, needs_enrichment, created_at, updated_at, scraped_at,
                    enriched_at, airtable_id, airtable_synced, sync_pending,
                    last_sync_attempt, sync_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_uuid,
                lead_data.get('full_name', ''),
                lead_data.get('email', ''),
                lead_data.get('company', ''),
                lead_data.get('title', ''),
                lead_data.get('linkedin_url', ''),
                lead_data.get('website', ''),
                lead_data.get('location', ''),
                lead_data.get('industry', ''),
                lead_data.get('company_size', ''),
                lead_data.get('source', ''),
                lead_data.get('status', 'new'),
                False,  # verified
                False,  # enriched
                True,   # needs_enrichment
                now,    # created_at
                now,    # updated_at
                None,   # scraped_at
                None,   # enriched_at
                None,   # airtable_id
                False,  # airtable_synced
                True,   # sync_pending
                None,   # last_sync_attempt
                None    # sync_error
            ))
            
            added_count += 1
            print(f"      ✅ Added successfully (UUID: {lead_uuid})")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n✅ Successfully added {added_count}/{len(test_leads)} leads")
        return added_count
        
    except Exception as e:
        print(f"❌ Error adding leads: {e}")
        import traceback
        traceback.print_exc()
        return 0


def test_sync():
    """Test the sync functionality."""
    print("\n🔄 Testing sync functionality...")
    
    try:
        from simple_sync_manager import SimpleSyncManager
        
        sync_manager = SimpleSyncManager()
        
        # Get sync stats
        stats = sync_manager.get_sync_stats()
        print(f"📊 Sync Stats:")
        print(f"   Total leads: {stats.get('total_leads', 0)}")
        print(f"   Pending syncs: {stats.get('pending_syncs', 0)}")
        
        # Test sync with just a few leads first
        print(f"\n🔄 Syncing first 5 leads to Airtable...")
        
        # Get first 5 leads
        from lead_database import LeadDatabase
        db = LeadDatabase()
        leads = db.search_leads({})
        first_5_leads = leads[:5]
        
        if first_5_leads:
            lead_ids = [lead['id'] for lead in first_5_leads]
            results = sync_manager.sync_to_airtable(lead_ids)
            
            successful = sum(1 for r in results if r.status.value == 'success')
            failed = sum(1 for r in results if r.status.value == 'failed')
            
            print(f"   Sync results: {successful} successful, {failed} failed")
            
            return successful > 0
        else:
            print("   No leads found to sync")
            return False
        
    except Exception as e:
        print(f"❌ Error testing sync: {e}")
        return False


def main():
    """Main function."""
    print("🚀 4Runr Quick Lead Addition")
    print("=" * 50)
    
    # Step 1: Add leads
    added_count = add_leads_directly()
    if added_count == 0:
        print("❌ Failed to add leads")
        return False
    
    # Step 2: Test sync
    if not test_sync():
        print("❌ Sync test failed")
        return False
    
    print("\n🎉 Quick lead addition and sync test completed successfully!")
    print(f"   ✅ Added {added_count} test leads")
    print(f"   ✅ Sync functionality working")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
