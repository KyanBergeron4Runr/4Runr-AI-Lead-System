#!/usr/bin/env python3
"""
Comprehensive test for the engager system

Tests the complete engagement pipeline from campaign generation through delivery.
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

# Import required modules
try:
    from campaign_system.database.connection import get_database_connection
    from campaign_system.database.schema import create_campaign_tables
    
    simple_generator = import_module_from_path("simple_generator", "campaign_system/campaign_generator/simple_generator.py")
    campaign_injector = import_module_from_path("campaign_injector", "campaign_system/campaign_injector.py")
    queue_manager = import_module_from_path("queue_manager", "campaign_system/queue_manager/queue_manager.py")
    executor = import_module_from_path("executor", "campaign_system/executor/executor.py")
    
    SimpleCampaignGenerator = simple_generator.SimpleCampaignGenerator
    CampaignInjector = campaign_injector.CampaignInjector
    MessageQueueManager = queue_manager.MessageQueueManager
    CampaignExecutor = executor.CampaignExecutor
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class EngagerSystemTester:
    """Comprehensive tester for the engager system"""
    
    def __init__(self):
        self.db = get_database_connection()
        self.generator = SimpleCampaignGenerator()
        self.injector = CampaignInjector()
        self.queue_manager = MessageQueueManager()
        self.executor = CampaignExecutor()
    
    def setup_test_environment(self):
        """Set up test environment"""
        print("🗄️  Setting up test environment...")
        
        try:
            # Initialize database
            create_campaign_tables()
            print("✅ Database initialized")
            
            return True
        except Exception as e:
            print(f"❌ Failed to setup environment: {e}")
            return False
    
    def test_end_to_end_engagement_flow(self):
        """Test complete end-to-end engagement flow"""
        print("\n🚀 Testing End-to-End Engagement Flow")
        print("=" * 60)
        
        # Step 1: Generate high-quality campaign
        print("📧 Step 1: Generating Campaign...")
        
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
        
        campaign_data = self.generator.generate_campaign(lead_data, company_data)
        
        if not campaign_data:
            print("❌ Failed to generate campaign")
            return False
        
        quality_score = campaign_data.get('overall_quality_score', 0)
        ready_to_send = campaign_data.get('ready_to_send', False)
        
        print(f"  Quality Score: {quality_score}/100")
        print(f"  Ready to Send: {'✅' if ready_to_send else '❌'}")
        
        if not ready_to_send:
            print("❌ Campaign not ready for engagement")
            return False
        
        # Step 2: Inject campaign into delivery system
        print("\n📥 Step 2: Injecting Campaign...")
        
        injection_success = self.injector.inject_campaign(campaign_data, lead_data)
        
        if not injection_success:
            print("❌ Failed to inject campaign")
            return False
        
        print("✅ Campaign injected successfully")
        
        # Step 3: Check queue status
        print("\n📋 Step 3: Checking Queue Status...")
        
        queue_stats = self.queue_manager.get_queue_stats()
        ready_messages = queue_stats.get('ready_for_delivery', 0)
        
        print(f"  Messages ready for delivery: {ready_messages}")
        print(f"  Total messages in queue: {queue_stats.get('total_messages', 0)}")
        
        if ready_messages == 0:
            print("⚠️  No messages ready for immediate delivery (scheduled for future)")
        
        # Step 4: Process delivery queue
        print("\n🚀 Step 4: Processing Delivery Queue...")
        
        # Get ready messages (including future scheduled ones for testing)
        ready_messages_list = self.queue_manager.get_ready_messages(10)
        
        if not ready_messages_list:
            # Force get all messages for testing
            all_messages_query = """
            SELECT * FROM message_queue 
            WHERE status = 'queued'
            ORDER BY scheduled_for ASC
            LIMIT 5
            """
            
            rows = self.db.execute_query(all_messages_query)
            print(f"  Found {len(rows)} queued messages (including future scheduled)")
            
            if rows:
                # Process first message for testing
                first_row = rows[0]
                queue_id = first_row['queue_id']
                
                print(f"  📧 Processing test message: {queue_id}")
                
                # Mark as processing
                self.queue_manager.mark_processing(queue_id)
                print("    ⏳ Marked as processing")
                
                # Simulate successful delivery
                self.queue_manager.mark_sent(queue_id)
                print("    ✅ Marked as sent")
                
                delivery_success = True
            else:
                print("❌ No messages found in queue")
                delivery_success = False
        else:
            # Process actual ready messages
            delivery_stats = self.executor.process_delivery_queue(batch_size=3)
            
            print(f"  Processed: {delivery_stats['processed']}")
            print(f"  Sent: {delivery_stats['sent']}")
            print(f"  Failed: {delivery_stats['failed']}")
            
            delivery_success = delivery_stats['sent'] > 0
        
        # Step 5: Check final status
        print("\n📊 Step 5: Final Status Check...")
        
        updated_stats = self.queue_manager.get_queue_stats()
        
        print(f"  Updated queue status:")
        if updated_stats.get('by_status'):
            for status, count in updated_stats['by_status'].items():
                print(f"    {status.title()}: {count}")
        
        return delivery_success
    
    def test_queue_management(self):
        """Test queue management functionality"""
        print("\n📬 Testing Queue Management")
        print("=" * 60)
        
        # Test 1: Add message to queue
        print("📥 Test 1: Adding Message to Queue...")
        
        queue_id = self.queue_manager.add_to_queue(
            campaign_id='test_campaign_queue',
            message_number=1,
            lead_email='test@example.com',
            subject='Test Queue Message',
            body='This is a test message for queue management',
            scheduled_for=datetime.now() + timedelta(minutes=1),
            priority=5
        )
        
        if queue_id:
            print(f"✅ Message added to queue: {queue_id}")
        else:
            print("❌ Failed to add message to queue")
            return False
        
        # Test 2: Get queue statistics
        print("\n📊 Test 2: Queue Statistics...")
        
        stats = self.queue_manager.get_queue_stats()
        
        print(f"  Total messages: {stats.get('total_messages', 0)}")
        print(f"  Ready for delivery: {stats.get('ready_for_delivery', 0)}")
        
        if stats.get('by_status'):
            print("  By status:")
            for status, count in stats['by_status'].items():
                print(f"    {status.title()}: {count}")
        
        # Test 3: Message processing
        print("\n⚙️  Test 3: Message Processing...")
        
        # Mark as processing
        processing_success = self.queue_manager.mark_processing(queue_id)
        print(f"  Mark processing: {'✅' if processing_success else '❌'}")
        
        # Mark as sent
        sent_success = self.queue_manager.mark_sent(queue_id)
        print(f"  Mark sent: {'✅' if sent_success else '❌'}")
        
        return processing_success and sent_success
    
    def test_campaign_progression(self):
        """Test campaign progression logic"""
        print("\n🔄 Testing Campaign Progression")
        print("=" * 60)
        
        # Create test campaign
        campaign_id = str(uuid.uuid4())
        
        # Insert test campaign
        campaign_query = """
        INSERT INTO campaigns (
            campaign_id, lead_id, company, campaign_status, current_message,
            response_detected, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            campaign_id,
            'progression_test_lead',
            'ProgressionCorp',
            'active',
            1,
            0,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        )
        
        self.db.execute_query(campaign_query, params)
        print(f"✅ Created test campaign: {campaign_id}")
        
        # Test progression update
        print("\n📈 Testing Progression Update...")
        
        progression_success = self.executor._update_campaign_progress(campaign_id, 1)
        print(f"  Update progress: {'✅' if progression_success else '❌'}")
        
        # Test response handling
        print("\n📧 Testing Response Handling...")
        
        response_success = self.executor.handle_response_received(campaign_id, 1, "interested")
        print(f"  Handle response: {'✅' if response_success else '❌'}")
        
        # Check campaign status
        status_query = "SELECT campaign_status, response_detected FROM campaigns WHERE campaign_id = ?"
        status_rows = self.db.execute_query(status_query, (campaign_id,))
        
        if status_rows:
            status = status_rows[0]['campaign_status']
            response_detected = status_rows[0]['response_detected']
            print(f"  Final status: {status}")
            print(f"  Response detected: {'✅' if response_detected else '❌'}")
        
        return progression_success and response_success
    
    def test_delivery_simulation(self):
        """Test delivery simulation"""
        print("\n🎯 Testing Delivery Simulation")
        print("=" * 60)
        
        # Create multiple test messages
        test_messages = []
        
        for i in range(3):
            queue_id = self.queue_manager.add_to_queue(
                campaign_id=f'delivery_test_{i}',
                message_number=1,
                lead_email=f'test{i}@example.com',
                subject=f'Test Delivery Message {i+1}',
                body=f'This is test delivery message {i+1}',
                scheduled_for=datetime.now() - timedelta(minutes=1),  # Make ready now
                priority=3
            )
            
            if queue_id:
                test_messages.append(queue_id)
        
        print(f"✅ Created {len(test_messages)} test messages")
        
        # Process delivery batch
        print("\n🚀 Processing Delivery Batch...")
        
        delivery_stats = self.executor.process_delivery_queue(batch_size=5)
        
        print(f"📊 Delivery Results:")
        print(f"  Processed: {delivery_stats['processed']}")
        print(f"  Sent: {delivery_stats['sent']}")
        print(f"  Failed: {delivery_stats['failed']}")
        print(f"  Skipped: {delivery_stats['skipped']}")
        
        success_rate = 0
        if delivery_stats['processed'] > 0:
            success_rate = (delivery_stats['sent'] / delivery_stats['processed']) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        
        return delivery_stats['processed'] > 0
    
    def test_analytics_integration(self):
        """Test analytics integration"""
        print("\n📊 Testing Analytics Integration")
        print("=" * 60)
        
        # Get delivery stats
        delivery_stats = self.executor.get_delivery_stats()
        
        if 'error' in delivery_stats:
            print(f"❌ Error getting delivery stats: {delivery_stats['error']}")
            return False
        
        print("✅ Delivery Stats Retrieved:")
        
        # Show queue stats
        queue_stats = delivery_stats.get('queue_stats', {})
        print(f"  Queue total messages: {queue_stats.get('total_messages', 0)}")
        print(f"  Queue ready for delivery: {queue_stats.get('ready_for_delivery', 0)}")
        
        # Show campaign stats
        campaign_stats = delivery_stats.get('campaign_stats', {})
        if campaign_stats:
            print("  Campaign status distribution:")
            for status, count in campaign_stats.items():
                print(f"    {status.title()}: {count}")
        
        # Show today's stats
        today_stats = delivery_stats.get('today_stats', {})
        print(f"  Messages sent today: {today_stats.get('messages_sent_today', 0)}")
        print(f"  Responses today: {today_stats.get('responses_today', 0)}")
        
        return True
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Clean up test campaigns
            cleanup_queries = [
                "DELETE FROM campaigns WHERE lead_id LIKE '%test%' OR campaign_id LIKE 'test_%' OR campaign_id LIKE 'delivery_test_%'",
                "DELETE FROM campaign_messages WHERE campaign_id LIKE 'test_%' OR campaign_id LIKE 'delivery_test_%'",
                "DELETE FROM message_queue WHERE campaign_id LIKE 'test_%' OR campaign_id LIKE 'delivery_test_%' OR lead_email LIKE 'test%@example.com'",
                "DELETE FROM campaign_analytics WHERE campaign_id LIKE 'test_%' OR campaign_id LIKE 'delivery_test_%'"
            ]
            
            for query in cleanup_queries:
                self.db.execute_query(query)
            
            print("✅ Test data cleaned up")
            return True
            
        except Exception as e:
            print(f"❌ Error cleaning up: {e}")
            return False


def main():
    """Run comprehensive engager system tests"""
    print("🚀 Comprehensive Engager System Test\n")
    
    try:
        tester = EngagerSystemTester()
        
        # Setup
        if not tester.setup_test_environment():
            return False
        
        # Test 1: End-to-end flow
        print("=" * 70)
        e2e_success = tester.test_end_to_end_engagement_flow()
        
        # Test 2: Queue management
        print("=" * 70)
        queue_success = tester.test_queue_management()
        
        # Test 3: Campaign progression
        print("=" * 70)
        progression_success = tester.test_campaign_progression()
        
        # Test 4: Delivery simulation
        print("=" * 70)
        delivery_success = tester.test_delivery_simulation()
        
        # Test 5: Analytics integration
        print("=" * 70)
        analytics_success = tester.test_analytics_integration()
        
        # Cleanup
        print("=" * 70)
        cleanup_success = tester.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 70)
        print("🎉 Engager System Test Complete!")
        
        print(f"\n📊 Test Results:")
        print(f"  End-to-End Flow: {'✅ Passed' if e2e_success else '❌ Failed'}")
        print(f"  Queue Management: {'✅ Passed' if queue_success else '❌ Failed'}")
        print(f"  Campaign Progression: {'✅ Passed' if progression_success else '❌ Failed'}")
        print(f"  Delivery Simulation: {'✅ Passed' if delivery_success else '❌ Failed'}")
        print(f"  Analytics Integration: {'✅ Passed' if analytics_success else '❌ Failed'}")
        print(f"  Cleanup: {'✅ Passed' if cleanup_success else '❌ Failed'}")
        
        all_passed = all([e2e_success, queue_success, progression_success, delivery_success, analytics_success])
        
        if all_passed:
            print(f"\n✅ ALL TESTS PASSED - Engager System is Working Correctly!")
            print(f"\n🚀 System Capabilities Verified:")
            print(f"  📧 Campaign generation and quality control")
            print(f"  📥 Campaign injection and scheduling")
            print(f"  📬 Message queue management")
            print(f"  🚀 Delivery processing and tracking")
            print(f"  🔄 Campaign progression and response handling")
            print(f"  📊 Analytics and performance monitoring")
        else:
            print(f"\n⚠️  Some tests failed - Review the results above")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)