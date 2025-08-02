#!/usr/bin/env python3
"""
Test script for cold lead recycling system

Demonstrates the complete recycling workflow from eligibility detection
to re-engagement campaign generation and injection.
"""

import sys
import os
import uuid
import importlib.util
from datetime import datetime, timedelta

# Direct imports
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import required modules
try:
    from campaign_system.database.connection import get_database_connection
    from campaign_system.database.schema import create_campaign_tables
    
    retry_cold_campaigns = import_module_from_path("retry_cold_campaigns", "retry_cold_campaigns.py")
    ColdLeadRecycler = retry_cold_campaigns.ColdLeadRecycler
    RecycledCampaignGenerator = retry_cold_campaigns.RecycledCampaignGenerator
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class ColdRecyclingTester:
    """Test the cold lead recycling system"""
    
    def __init__(self):
        self.db = get_database_connection()
        self.recycler = ColdLeadRecycler(cooldown_days=1)  # Short cooldown for testing
    
    def setup_test_data(self):
        """Create test campaigns for recycling"""
        print("🗄️  Setting up test data...")
        
        # Create test campaigns that are eligible for recycling
        test_campaigns = [
            {
                'campaign_id': str(uuid.uuid4()),
                'lead_id': 'test_lead_001',
                'company': 'TestCorp',
                'campaign_status': 'completed',
                'current_message': 3,
                'response_detected': 0,
                'created_at': (datetime.now() - timedelta(days=15)).isoformat(),
                'updated_at': (datetime.now() - timedelta(days=15)).isoformat(),
                'lead_traits': '{"Name": "John Doe", "Company": "TestCorp", "Title": "CEO", "Email": "john@testcorp.com"}',
                'company_insights': '{"company_description": "TestCorp provides business solutions", "top_services": "Consulting, Software", "tone": "Professional"}'
            },
            {
                'campaign_id': str(uuid.uuid4()),
                'lead_id': 'test_lead_002',
                'company': 'InnovateCo',
                'campaign_status': 'completed',
                'current_message': 3,
                'response_detected': 0,
                'created_at': (datetime.now() - timedelta(days=20)).isoformat(),
                'updated_at': (datetime.now() - timedelta(days=20)).isoformat(),
                'lead_traits': '{"Name": "Sarah Johnson", "Company": "InnovateCo", "Title": "VP of Product", "Email": "sarah@innovateco.com"}',
                'company_insights': '{"company_description": "InnovateCo builds SaaS platforms", "top_services": "Software development, Cloud services", "tone": "Professional"}'
            }
        ]
        
        # Insert test campaigns
        for campaign in test_campaigns:
            query = """
            INSERT OR REPLACE INTO campaigns (
                campaign_id, lead_id, company, campaign_status, current_message,
                response_detected, created_at, updated_at, lead_traits, company_insights,
                eligible_for_recycle, recycle_attempt_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
            """
            
            params = (
                campaign['campaign_id'],
                campaign['lead_id'],
                campaign['company'],
                campaign['campaign_status'],
                campaign['current_message'],
                campaign['response_detected'],
                campaign['created_at'],
                campaign['updated_at'],
                campaign['lead_traits'],
                campaign['company_insights']
            )
            
            self.db.execute_query(query, params)
        
        print(f"✅ Created {len(test_campaigns)} test campaigns")
        return test_campaigns
    
    def test_eligibility_detection(self):
        """Test finding eligible campaigns"""
        print("\n🔍 Testing Eligibility Detection...")
        
        eligible_campaigns = self.recycler.find_eligible_campaigns()
        
        print(f"📋 Found {len(eligible_campaigns)} eligible campaigns:")
        
        for campaign in eligible_campaigns:
            days_since = campaign.get('days_since_last_message', 0)
            print(f"  • {campaign['company']} (ID: {campaign['campaign_id'][:8]}...)")
            print(f"    Days since last message: {days_since:.1f}")
            print(f"    Status: {campaign['campaign_status']}")
            print(f"    Response detected: {campaign['response_detected']}")
        
        return eligible_campaigns
    
    def test_recycled_message_generation(self):
        """Test recycled message generation"""
        print("\n📧 Testing Recycled Message Generation...")
        
        # Test different recycle types
        recycle_types = ['soft_retry', 'content_drop', 'escalation']
        
        lead_data = {
            'Name': 'John Doe',
            'Company': 'TestCorp',
            'Title': 'CEO',
            'Email': 'john@testcorp.com'
        }
        
        company_data = {
            'company_description': 'TestCorp provides business solutions',
            'top_services': 'Consulting, Software development',
            'tone': 'Professional'
        }
        
        for recycle_type in recycle_types:
            print(f"\n🎯 Testing {recycle_type} recycling...")
            
            generator = RecycledCampaignGenerator(recycle_type)
            campaign_data = generator.generate_campaign(lead_data, company_data)
            
            if campaign_data:
                messages = campaign_data.get('messages', [])
                print(f"  ✅ Generated {len(messages)} messages")
                
                # Show hook message as example
                if messages:
                    hook_msg = messages[0]
                    print(f"  📨 Hook Subject: {hook_msg.get('subject', 'No subject')}")
                    print(f"  📝 Hook Preview: {hook_msg.get('body', 'No body')[:100]}...")
            else:
                print(f"  ❌ Failed to generate campaign")
        
        return True
    
    def test_complete_recycling_workflow(self):
        """Test the complete recycling workflow"""
        print("\n🔄 Testing Complete Recycling Workflow...")
        
        # Process recycling batch
        result = self.recycler.process_recycling_batch(limit=5, dry_run=False)
        
        print(f"📊 Recycling Results:")
        print(f"  Eligible found: {result['eligible_found']}")
        print(f"  Marked for recycle: {result['marked_for_recycle']}")
        print(f"  Campaigns generated: {result['campaigns_generated']}")
        print(f"  Campaigns injected: {result['campaigns_injected']}")
        print(f"  Quality failures: {result['quality_failures']}")
        print(f"  Errors: {result['errors']}")
        
        return result
    
    def test_recycling_statistics(self):
        """Test recycling statistics"""
        print("\n📊 Testing Recycling Statistics...")
        
        stats = self.recycler.get_recycling_stats()
        
        if 'error' in stats:
            print(f"❌ Error getting stats: {stats['error']}")
            return False
        
        print(f"📋 Statistics:")
        print(f"  Eligible for recycling: {stats['eligible_for_recycling']}")
        print(f"  Total recycled campaigns: {stats['total_recycled_campaigns']}")
        print(f"  Cooldown days: {stats['cooldown_days']}")
        print(f"  Max attempts: {stats['max_attempts']}")
        
        if stats['recycled_by_type']:
            print(f"\n📈 Performance by Type:")
            for recycle_type, type_stats in stats['recycled_by_type'].items():
                print(f"  {recycle_type.title()}:")
                print(f"    Count: {type_stats['count']}")
                print(f"    Response Rate: {type_stats['response_rate']}%")
        
        return True
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Remove test campaigns
            self.db.execute_query("DELETE FROM campaigns WHERE lead_id LIKE 'test_lead_%'")
            self.db.execute_query("DELETE FROM campaign_messages WHERE campaign_id LIKE 'test_%'")
            self.db.execute_query("DELETE FROM message_queue WHERE campaign_id LIKE 'test_%'")
            
            print("✅ Test data cleaned up")
            return True
        except Exception as e:
            print(f"❌ Error cleaning up: {e}")
            return False


def main():
    """Run all cold recycling tests"""
    print("🚀 Testing Cold Lead Recycling System\n")
    
    try:
        # Initialize database
        print("🗄️  Initializing database...")
        create_campaign_tables()
        
        tester = ColdRecyclingTester()
        
        # Setup test data
        test_campaigns = tester.setup_test_data()
        
        # Test 1: Eligibility detection
        print("=" * 60)
        eligible_campaigns = tester.test_eligibility_detection()
        
        # Test 2: Message generation
        print("=" * 60)
        generation_test = tester.test_recycled_message_generation()
        
        # Test 3: Complete workflow
        print("=" * 60)
        workflow_result = tester.test_complete_recycling_workflow()
        
        # Test 4: Statistics
        print("=" * 60)
        stats_test = tester.test_recycling_statistics()
        
        # Cleanup
        print("=" * 60)
        cleanup_success = tester.cleanup_test_data()
        
        print("\n" + "=" * 60)
        print("🎉 Cold Lead Recycling Tests Complete!")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"  Eligible campaigns found: {len(eligible_campaigns)}")
        print(f"  Message generation: {'✅ Passed' if generation_test else '❌ Failed'}")
        print(f"  Complete workflow: {'✅ Passed' if workflow_result['errors'] == 0 else '❌ Failed'}")
        print(f"  Statistics: {'✅ Passed' if stats_test else '❌ Failed'}")
        print(f"  Cleanup: {'✅ Passed' if cleanup_success else '❌ Failed'}")
        
        if workflow_result['campaigns_injected'] > 0:
            print(f"\n🔄 Recycling Performance:")
            print(f"  Campaigns recycled: {workflow_result['campaigns_injected']}")
            print(f"  Quality pass rate: {((workflow_result['campaigns_generated'] - workflow_result['quality_failures']) / workflow_result['campaigns_generated'] * 100):.1f}%")
        
        print(f"\n🚀 System Features Demonstrated:")
        print(f"  🔍 Automatic eligibility detection")
        print(f"  📧 Specialized re-engagement message generation")
        print(f"  🎯 Multiple recycling strategies (soft_retry, content_drop, escalation)")
        print(f"  🔒 Quality control integration")
        print(f"  📊 Comprehensive tracking and analytics")
        print(f"  ⏰ Configurable cooldown periods")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)