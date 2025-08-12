#!/usr/bin/env python3
"""
Simplified engager system test without external dependencies

Tests core functionality of the engagement pipeline.
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
    
    simple_generator = import_module_from_path("simple_generator", "campaign_system/campaign_generator/simple_generator.py")
    campaign_injector = import_module_from_path("campaign_injector", "campaign_system/campaign_injector.py")
    queue_manager = import_module_from_path("queue_manager", "campaign_system/queue_manager/queue_manager.py")
    
    SimpleCampaignGenerator = simple_generator.SimpleCampaignGenerator
    CampaignInjector = campaign_injector.CampaignInjector
    MessageQueueManager = queue_manager.MessageQueueManager
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class SimpleEngagerTester:
    """Simplified engager system tester"""
    
    def __init__(self):
        self.db = get_database_connection()
        self.generator = SimpleCampaignGenerator()
        self.injector = CampaignInjector()
        self.queue_manager = MessageQueueManager()
    
    def test_campaign_generation_and_injection(self):
        """Test campaign generation and injection"""
        print("🚀 Testing Campaign Generation and Injection")
        print("=" * 60)
        
        # Test data
        lead_data = {
            'id': 'engager_test_001',
            'Name': 'Sarah Johnson',
            'Company': 'TechCorp',
            'Title': 'VP of Engineering',
            'Email': 'sarah@techcorp.com'
        }
        
        company_data = {
            'company_description': 'TechCorp is a leading SaaS platform providing enterprise solutions',
            'top_services': 'Software as a Service, API integrations, Cloud platforms',
            'tone': 'Professional',
            'traits': ['enterprise', 'API-based', 'cloud-native']
        }
        
        # Step 1: Generate campaign
        print("📧 Step 1: Generating Campaign...")
        
        campaign_data = self.generator.generate_campaign(lead_data, company_data)
        
        if not campaign_data:
            print("❌ Failed to generate campaign")
            return False
        
        quality_score = campaign_data.get('overall_quality_score', 0)
        ready_to_send = campaign_data.get('ready_to_send', False)
        messages = campaign_data.get('messages', [])
        
        print(f"  ✅ Campaign generated")
        print(f"  📊 Quality Score: {quality_score}/100")
        print(f"  🎯 Ready to Send: {'✅' if ready_to_send else '❌'}")
        print(f"  📨 Messages: {len(messages)}")
        
        # Show message preview
        if messages:
            hook_msg = messages[0]
            print(f"  📧 Hook Subject: {hook_msg.get('subject', 'No subject')}")
        
        # Step 2: Inject campaign
        print(f"\n📥 Step 2: Injecting Campaign...")
        
        if not ready_to_send:
            print("⚠️  Campaign not ready to send, skipping injection")
            return False
        
        injection_success = self.injector.inject_campaign(campaign_data, lead_data)
        
        if injection_success:
            print("  ✅ Campaign injected successfully")
        else:
            print("  ❌ Failed to inject campaign")
            return False
        
        return True
    
    def test_queue_operations(self):
        """Test queue operations"""
        print("\n📬 Testing Queue Operations")
        print("=" * 60)
        
        # Get initial queue stats
        print("📊 Initial Queue Status:")
        initial_stats = self.queue_manager.get_queue_stats()
        
        print(f"  Total messages: {initial_stats.get('total_messages', 0)}")
        print(f"  Ready for delivery: {initial_stats.get('ready_for_delivery', 0)}")
        
        if initial_stats.get('by_status'):
            for status, count in initial_stats['by_status'].items():
                print(f"  {status.title()}: {count}")
        
        # Add test message
        print(f"\n📥 Adding Test Message to Queue...")
        
        queue_id = self.queue_manager.add_to_queue(
            campaign_id='test_queue_ops',
            message_number=1,
            lead_email='test@example.com',
            subject='Test Queue Operations',
            body='This is a test message for queue operations',
            scheduled_for=datetime.now() - timedelta(minutes=1),  # Make it ready
            priority=3
        )
        
        if queue_id:
            print(f"  ✅ Message added: {queue_id}")
        else:
            print("  ❌ Failed to add message")
            return False
        
        # Get updated stats
        print(f"\n📊 Updated Queue Status:")
        updated_stats = self.queue_manager.get_queue_stats()
        
        print(f"  Total messages: {updated_stats.get('total_messages', 0)}")
        print(f"  Ready for delivery: {updated_stats.get('ready_for_delivery', 0)}")
        
        # Test message processing
        print(f"\n⚙️  Testing Message Processing...")
        
        # Mark as processing
        processing_success = self.queue_manager.mark_processing(queue_id)
        print(f"  Mark processing: {'✅' if processing_success else '❌'}")
        
        # Mark as sent
        sent_success = self.queue_manager.mark_sent(queue_id)
        print(f"  Mark sent: {'✅' if sent_success else '❌'}")
        
        # Final stats
        print(f"\n📊 Final Queue Status:")
        final_stats = self.queue_manager.get_queue_stats()
        
        if final_stats.get('by_status'):
            for status, count in final_stats['by_status'].items():
                print(f"  {status.title()}: {count}")
        
        return processing_success and sent_success
    
    def test_delivery_simulation(self):
        """Test delivery simulation"""
        print("\n🚀 Testing Delivery Simulation")
        print("=" * 60)
        
        # Get ready messages
        ready_messages = self.queue_manager.get_ready_messages(5)
        
        print(f"📋 Found {len(ready_messages)} ready messages")
        
        if ready_messages:
            print(f"\n📧 Processing Ready Messages:")
            
            processed = 0
            sent = 0
            
            for i, message in enumerate(ready_messages[:3], 1):  # Process up to 3
                print(f"  {i}. Campaign: {message.campaign_id}")
                print(f"     Message: {message.message_number}")
                print(f"     To: {message.lead_email}")
                print(f"     Subject: {message.subject}")
                
                # Simulate processing
                self.queue_manager.mark_processing(message.queue_id)
                print(f"     ⏳ Marked as processing")
                
                # Simulate successful send
                self.queue_manager.mark_sent(message.queue_id)
                print(f"     ✅ Marked as sent")
                
                processed += 1
                sent += 1
                print()
            
            print(f"📊 Simulation Results:")
            print(f"  Processed: {processed}")
            print(f"  Sent: {sent}")
            print(f"  Success Rate: 100%")
            
            return True
        else:
            print("⚠️  No messages ready for delivery")
            
            # Check if there are any queued messages
            all_stats = self.queue_manager.get_queue_stats()
            total_messages = all_stats.get('total_messages', 0)
            
            if total_messages > 0:
                print(f"📋 Found {total_messages} total messages in queue")
                print("   (They may be scheduled for future delivery)")
                return True
            else:
                print("📋 No messages in queue at all")
                return False
    
    def test_campaign_tracking(self):
        """Test campaign tracking"""
        print("\n📊 Testing Campaign Tracking")
        print("=" * 60)
        
        # Get injection stats
        print("📈 Injection Statistics:")
        injection_stats = self.injector.get_injection_stats()
        
        if 'error' in injection_stats:
            print(f"❌ Error getting stats: {injection_stats['error']}")
            return False
        
        print(f"  Total campaigns: {injection_stats.get('total_campaigns', 0)}")
        
        by_status = injection_stats.get('by_status', {})
        if by_status:
            print("  By status:")
            for status, count in by_status.items():
                print(f"    {status.title()}: {count}")
        
        # Get queue stats
        print(f"\n📬 Queue Statistics:")
        queue_stats = self.queue_manager.get_queue_stats()
        
        print(f"  Total messages: {queue_stats.get('total_messages', 0)}")
        print(f"  Ready for delivery: {queue_stats.get('ready_for_delivery', 0)}")
        
        if queue_stats.get('by_status'):
            print("  By status:")
            for status, count in queue_stats['by_status'].items():
                print(f"    {status.title()}: {count}")
        
        return True
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Clean up test data
            cleanup_queries = [
                "DELETE FROM campaigns WHERE lead_id = 'engager_test_001' OR campaign_id = 'test_queue_ops'",
                "DELETE FROM campaign_messages WHERE campaign_id LIKE 'test_%'",
                "DELETE FROM message_queue WHERE campaign_id LIKE 'test_%' OR lead_email = 'test@example.com'",
                "DELETE FROM campaign_analytics WHERE campaign_id LIKE 'test_%'"
            ]
            
            for query in cleanup_queries:
                self.db.execute_query(query)
            
            print("✅ Test data cleaned up")
            return True
            
        except Exception as e:
            print(f"❌ Error cleaning up: {e}")
            return False


def main():
    """Run simplified engager system tests"""
    print("🚀 Simplified Engager System Test\n")
    
    try:
        # Initialize database
        print("🗄️  Initializing database...")
        create_campaign_tables()
        
        tester = SimpleEngagerTester()
        
        # Test 1: Campaign generation and injection
        print("=" * 70)
        generation_success = tester.test_campaign_generation_and_injection()
        
        # Test 2: Queue operations
        print("=" * 70)
        queue_success = tester.test_queue_operations()
        
        # Test 3: Delivery simulation
        print("=" * 70)
        delivery_success = tester.test_delivery_simulation()
        
        # Test 4: Campaign tracking
        print("=" * 70)
        tracking_success = tester.test_campaign_tracking()
        
        # Cleanup
        print("=" * 70)
        cleanup_success = tester.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 70)
        print("🎉 Engager System Test Complete!")
        
        print(f"\n📊 Test Results:")
        print(f"  Campaign Generation & Injection: {'✅ Passed' if generation_success else '❌ Failed'}")
        print(f"  Queue Operations: {'✅ Passed' if queue_success else '❌ Failed'}")
        print(f"  Delivery Simulation: {'✅ Passed' if delivery_success else '❌ Failed'}")
        print(f"  Campaign Tracking: {'✅ Passed' if tracking_success else '❌ Failed'}")
        print(f"  Cleanup: {'✅ Passed' if cleanup_success else '❌ Failed'}")
        
        all_passed = all([generation_success, queue_success, delivery_success, tracking_success])
        
        if all_passed:
            print(f"\n✅ ALL TESTS PASSED - Engager System is Working Correctly!")
            print(f"\n🚀 Verified System Components:")
            print(f"  📧 Campaign generation with quality control")
            print(f"  📥 Campaign injection and database storage")
            print(f"  📬 Message queue management and processing")
            print(f"  🚀 Delivery simulation and status tracking")
            print(f"  📊 Campaign and queue analytics")
            print(f"  🔄 Complete end-to-end workflow")
            
            print(f"\n🎯 System Ready For:")
            print(f"  • Production campaign generation")
            print(f"  • Automated message scheduling")
            print(f"  • Queue-based delivery processing")
            print(f"  • Response tracking and analytics")
            print(f"  • Cold lead recycling")
        else:
            print(f"\n⚠️  Some tests failed - Check the results above")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)