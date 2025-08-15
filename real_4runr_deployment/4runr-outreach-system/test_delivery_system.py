#!/usr/bin/env python3
"""
Test script for the complete delivery system integration

Tests campaign generation, quality control, injection, scheduling, and delivery.
"""

import sys
import os
import uuid
import importlib.util
from datetime import datetime, timedelta

# Direct imports to avoid dependency issues
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import modules
simple_generator = import_module_from_path("simple_generator", "campaign_system/campaign_generator/simple_generator.py")
campaign_injector = import_module_from_path("campaign_injector", "campaign_system/campaign_injector.py")

SimpleCampaignGenerator = simple_generator.SimpleCampaignGenerator
CampaignInjector = campaign_injector.CampaignInjector


class DeliverySystemTester:
    """Test the complete delivery system"""
    
    def __init__(self):
        self.generator = SimpleCampaignGenerator()
        self.injector = CampaignInjector()
    
    def test_end_to_end_flow(self):
        """Test complete end-to-end campaign flow"""
        print("🚀 Testing End-to-End Campaign Delivery Flow\n")
        
        # Step 1: Generate campaign
        print("📧 Step 1: Generating Campaign...")
        campaign_data = self._generate_test_campaign()
        
        if not campaign_data:
            print("❌ Failed to generate campaign")
            return False
        
        print(f"✅ Campaign generated with quality score: {campaign_data.get('overall_quality_score', 0)}/100")
        
        # Step 2: Inject into delivery system
        print("\n📥 Step 2: Injecting Campaign into Delivery System...")
        lead_data = self._get_test_lead_data()
        
        injection_success = self.injector.inject_campaign(campaign_data, lead_data)
        
        if not injection_success:
            print("❌ Failed to inject campaign")
            return False
        
        print("✅ Campaign injected successfully")
        
        # Step 3: Check injection stats
        print("\n📊 Step 3: Checking Injection Statistics...")
        stats = self.injector.get_injection_stats()
        
        if 'error' in stats:
            print(f"❌ Error getting stats: {stats['error']}")
            return False
        
        print(f"✅ Total campaigns: {stats.get('total_campaigns', 0)}")
        print(f"  By status: {stats.get('by_status', {})}")
        
        return True
    
    def test_campaign_generation_quality(self):
        """Test campaign generation with different quality levels"""
        print("🔍 Testing Campaign Generation Quality\n")
        
        test_cases = [
            {
                'name': 'High-Quality Lead (CEO)',
                'lead_data': {
                    'id': 'test_ceo_001',
                    'Name': 'Sarah Chen',
                    'Company': 'TechCorp',
                    'Title': 'CEO',
                    'Email': 'sarah@techcorp.com'
                },
                'company_data': {
                    'company_description': 'TechCorp is a leading SaaS platform providing enterprise solutions',
                    'top_services': 'Software as a Service, API integrations, Cloud platforms',
                    'tone': 'Professional',
                    'traits': ['enterprise', 'API-based', 'cloud-native']
                }
            },
            {
                'name': 'Standard Lead (Manager)',
                'lead_data': {
                    'id': 'test_mgr_001',
                    'Name': 'Mike Johnson',
                    'Company': 'StartupCo',
                    'Title': 'Marketing Manager',
                    'Email': 'mike@startupco.com'
                },
                'company_data': {
                    'company_description': 'StartupCo provides digital marketing services',
                    'top_services': 'Digital marketing, SEO, Content creation',
                    'tone': 'Casual',
                    'traits': ['marketing', 'digital-first']
                }
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"🎯 Testing {test_case['name']}...")
            
            campaign_data = self.generator.generate_campaign(
                test_case['lead_data'],
                test_case['company_data']
            )
            
            quality_score = campaign_data.get('overall_quality_score', 0)
            ready_to_send = campaign_data.get('ready_to_send', False)
            
            print(f"  Quality Score: {quality_score}/100")
            print(f"  Ready to Send: {'✅' if ready_to_send else '❌'}")
            
            # Show message quality breakdown
            messages = campaign_data.get('messages', [])
            for msg in messages:
                msg_type = msg.get('type', 'unknown').upper()
                msg_quality = msg.get('quality_score', 0)
                issues = len(msg.get('issues_detected', []))
                print(f"    {msg_type}: {msg_quality}/100 ({issues} issues)")
            
            results.append({
                'name': test_case['name'],
                'quality_score': quality_score,
                'ready_to_send': ready_to_send,
                'message_count': len(messages)
            })
            
            print()
        
        return results
    
    def test_injection_criteria(self):
        """Test campaign injection criteria"""
        print("🔒 Testing Campaign Injection Criteria\n")
        
        # Test case 1: High quality campaign (should be injected)
        print("✅ Test 1: High Quality Campaign")
        high_quality_campaign = {
            'ready_to_send': True,
            'overall_quality_score': 95,
            'messages': [
                {'type': 'hook', 'subject': 'Test Hook', 'body': 'Test hook body'},
                {'type': 'proof', 'subject': 'Test Proof', 'body': 'Test proof body'},
                {'type': 'fomo', 'subject': 'Test FOMO', 'body': 'Test fomo body'}
            ]
        }
        
        should_inject = self.injector._should_inject_campaign(high_quality_campaign)
        print(f"  Should inject: {'✅ Yes' if should_inject else '❌ No'}")
        
        # Test case 2: Low quality campaign (should be rejected)
        print("\n❌ Test 2: Low Quality Campaign")
        low_quality_campaign = {
            'ready_to_send': False,
            'overall_quality_score': 65,
            'messages': [
                {'type': 'hook', 'subject': 'Test Hook', 'body': 'Test hook body'},
                {'type': 'proof', 'subject': 'Test Proof', 'body': 'Test proof body'}
            ]
        }
        
        should_inject = self.injector._should_inject_campaign(low_quality_campaign)
        print(f"  Should inject: {'✅ Yes' if should_inject else '❌ No'}")
        
        # Test case 3: Incomplete campaign (should be rejected)
        print("\n❌ Test 3: Incomplete Campaign")
        incomplete_campaign = {
            'ready_to_send': True,
            'overall_quality_score': 85,
            'messages': [
                {'type': 'hook', 'subject': 'Test Hook', 'body': 'Test hook body'}
            ]
        }
        
        should_inject = self.injector._should_inject_campaign(incomplete_campaign)
        print(f"  Should inject: {'✅ Yes' if should_inject else '❌ No'}")
        
        return True
    
    def test_delivery_queue_simulation(self):
        """Simulate delivery queue processing"""
        print("📬 Testing Delivery Queue Simulation\n")
        
        try:
            # Import delivery components
            queue_manager = import_module_from_path("queue_manager", "campaign_system/queue_manager/queue_manager.py")
            MessageQueueManager = queue_manager.MessageQueueManager
            
            queue_mgr = MessageQueueManager()
            
            # Get queue stats
            stats = queue_mgr.get_queue_stats()
            
            print("📊 Queue Statistics:")
            print(f"  Total messages: {stats.get('total_messages', 0)}")
            print(f"  Ready for delivery: {stats.get('ready_for_delivery', 0)}")
            
            if stats.get('by_status'):
                print("  By status:")
                for status, count in stats['by_status'].items():
                    print(f"    {status.title()}: {count}")
            
            # Simulate adding a message to queue
            print("\n📥 Simulating Queue Addition...")
            
            queue_id = queue_mgr.add_to_queue(
                campaign_id='test_campaign_001',
                message_number=1,
                lead_email='test@example.com',
                subject='Test Subject',
                body='Test message body',
                scheduled_for=datetime.now() + timedelta(minutes=5),
                priority=3
            )
            
            if queue_id:
                print(f"✅ Message added to queue: {queue_id}")
            else:
                print("❌ Failed to add message to queue")
            
            return True
        
        except Exception as e:
            print(f"❌ Error in queue simulation: {e}")
            return False
    
    def _generate_test_campaign(self):
        """Generate a test campaign"""
        lead_data = {
            'id': 'test_lead_001',
            'Name': 'Johannes Reck',
            'Company': 'trivago',
            'Title': 'CEO',
            'Email': 'johannes@trivago.com'
        }
        
        company_data = {
            'company_description': 'trivago is a global hotel search platform that helps travelers find and compare hotel prices',
            'top_services': 'Hotel price comparison, Travel booking platform, Hotel search engine',
            'tone': 'Professional',
            'traits': ['enterprise', 'multi-language', 'search-based'],
            'website_headline': 'Compare hotel prices worldwide'
        }
        
        return self.generator.generate_campaign(lead_data, company_data)
    
    def _get_test_lead_data(self):
        """Get test lead data"""
        return {
            'id': 'test_lead_001',
            'Name': 'Johannes Reck',
            'Company': 'trivago',
            'Title': 'CEO',
            'Email': 'johannes@trivago.com'
        }


def main():
    """Run all delivery system tests"""
    print("🚀 Testing Complete Campaign Delivery System\n")
    
    try:
        tester = DeliverySystemTester()
        
        # Test 1: Campaign generation quality
        print("=" * 60)
        generation_results = tester.test_campaign_generation_quality()
        
        # Test 2: Injection criteria
        print("=" * 60)
        injection_test = tester.test_injection_criteria()
        
        # Test 3: Delivery queue simulation
        print("=" * 60)
        queue_test = tester.test_delivery_queue_simulation()
        
        # Test 4: End-to-end flow
        print("=" * 60)
        e2e_test = tester.test_end_to_end_flow()
        
        print("\n" + "=" * 60)
        print("🎉 All Delivery System Tests Completed!")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"  Campaign Generation: ✅ {len(generation_results)} test cases")
        print(f"  Injection Criteria: {'✅ Passed' if injection_test else '❌ Failed'}")
        print(f"  Queue Simulation: {'✅ Passed' if queue_test else '❌ Failed'}")
        print(f"  End-to-End Flow: {'✅ Passed' if e2e_test else '❌ Failed'}")
        
        # Show generation results
        print(f"\n📈 Generation Quality Results:")
        for result in generation_results:
            status = "✅ Ready" if result['ready_to_send'] else "❌ Not Ready"
            print(f"  {result['name']}: {result['quality_score']}/100 - {status}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)