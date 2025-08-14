#!/usr/bin/env python3
"""
Clean and Populate Database with Test Data

This script cleans the local database and populates it with comprehensive test data
to thoroughly test the 4Runr system.
"""

import sys
import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lead_database import LeadDatabase
from simple_pipeline import SimplePipeline


def clear_database():
    """Clear all leads from the database."""
    print("🧹 Cleaning database...")
    
    try:
        db = LeadDatabase()
        
        # Get all leads
        all_leads = db.search_leads({})
        print(f"   Found {len(all_leads)} existing leads")
        
        # Clear database using direct SQL
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM leads")
            conn.commit()
            deleted_count = cursor.rowcount
        
        print(f"   ✅ Deleted {deleted_count} leads")
        return True
        
    except Exception as e:
        print(f"   ❌ Error clearing database: {e}")
        return False


def create_test_leads():
    """Create comprehensive test data."""
    print("\n📝 Creating comprehensive test data...")
    
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


def populate_database():
    """Populate the database with test data."""
    print("\n🚀 Populating database with test data...")
    
    try:
        # Initialize pipeline
        pipeline = SimplePipeline()
        
        # Get test data
        test_leads = create_test_leads()
        
        # Add each lead
        added_count = 0
        for i, lead_data in enumerate(test_leads, 1):
            print(f"   📝 Adding lead {i}/{len(test_leads)}: {lead_data['full_name']}")
            
            lead_id = pipeline.add_lead(lead_data)
            if lead_id:
                added_count += 1
                print(f"      ✅ Added successfully")
            else:
                print(f"      ❌ Failed to add")
        
        print(f"\n✅ Successfully added {added_count}/{len(test_leads)} leads")
        return added_count
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        return 0


def test_system():
    """Test the complete system with the new data."""
    print("\n🧪 Testing complete system...")
    
    try:
        pipeline = SimplePipeline()
        
        # Get system stats
        stats = pipeline.get_system_stats()
        print(f"📊 System Stats:")
        print(f"   Total leads: {stats.get('database', {}).get('total_leads', 0)}")
        print(f"   Pending syncs: {stats.get('sync', {}).get('pending_syncs', 0)}")
        
        # Test sync
        print(f"\n🔄 Testing sync to Airtable...")
        sync_results = pipeline.sync_to_airtable()
        print(f"   Sync results: {sync_results['successful']} successful, {sync_results['failed']} failed")
        
        # Test AI message generation
        print(f"\n🤖 Testing AI message generation...")
        leads_without_messages = pipeline.db.search_leads({'ai_generated_message': None})
        print(f"   Leads without messages: {len(leads_without_messages)}")
        
        # Generate messages for a few leads
        message_count = 0
        for lead in leads_without_messages[:3]:  # Test with 3 leads
            try:
                message = pipeline.message_generator.generate_message(lead)
                if message:
                    pipeline.db.update_lead(lead['id'], {
                        'ai_generated_message': message,
                        'message_generated_at': datetime.datetime.now().isoformat()
                    })
                    message_count += 1
                    print(f"   ✅ Generated message for {lead.get('full_name', 'Unknown')}")
            except Exception as e:
                print(f"   ❌ Failed to generate message for {lead.get('full_name', 'Unknown')}: {e}")
        
        print(f"   Generated {message_count} messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing system: {e}")
        return False


def main():
    """Main function to clean and populate the database."""
    print("🚀 4Runr Database Clean & Populate")
    print("=" * 50)
    
    # Step 1: Clear database
    if not clear_database():
        print("❌ Failed to clear database")
        return False
    
    # Step 2: Populate with test data
    added_count = populate_database()
    if added_count == 0:
        print("❌ Failed to populate database")
        return False
    
    # Step 3: Test the system
    if not test_system():
        print("❌ System test failed")
        return False
    
    print("\n🎉 Database clean and populate completed successfully!")
    print(f"   ✅ Added {added_count} test leads")
    print(f"   ✅ System tested and working")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
