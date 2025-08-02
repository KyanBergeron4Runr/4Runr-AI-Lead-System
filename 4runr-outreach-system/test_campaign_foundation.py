#!/usr/bin/env python3
"""
Test script for campaign system foundation

This script tests the basic data models and database functionality.
"""

import sys
import os
from datetime import datetime, timedelta
import uuid

# Add campaign system to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from campaign_system.models.campaign import Campaign, CampaignMessage, MessageType, CampaignStatus
from campaign_system.models.queue import MessageQueue, QueueStatus
from campaign_system.models.analytics import CampaignAnalytics
from campaign_system.database.schema import create_campaign_tables
from campaign_system.config import get_config


def test_campaign_model():
    """Test the Campaign data model"""
    print("🧪 Testing Campaign model...")
    
    # Create a test campaign
    campaign = Campaign(
        campaign_id=str(uuid.uuid4()),
        lead_id="test_lead_123",
        company="Test Company",
        lead_traits={"name": "John Doe", "role": "CEO"},
        company_insights={"industry": "Tech", "size": "Startup"}
    )
    
    # Add messages
    hook_message = CampaignMessage(
        message_number=1,
        message_type=MessageType.HOOK,
        subject="Test Hook Subject",
        body="Test hook message body",
        scheduled_date=datetime.now()
    )
    
    proof_message = CampaignMessage(
        message_number=2,
        message_type=MessageType.PROOF,
        subject="Test Proof Subject", 
        body="Test proof message body",
        scheduled_date=datetime.now() + timedelta(days=3)
    )
    
    campaign.add_message(hook_message)
    campaign.add_message(proof_message)
    
    # Test serialization
    campaign_dict = campaign.to_dict()
    restored_campaign = Campaign.from_dict(campaign_dict)
    
    assert restored_campaign.campaign_id == campaign.campaign_id
    assert len(restored_campaign.messages) == 2
    assert restored_campaign.messages[0].message_type == MessageType.HOOK
    
    print("✅ Campaign model test passed")


def test_queue_model():
    """Test the MessageQueue data model"""
    print("🧪 Testing MessageQueue model...")
    
    queue_entry = MessageQueue(
        queue_id=str(uuid.uuid4()),
        campaign_id="test_campaign_123",
        message_number=1,
        lead_email="test@example.com",
        subject="Test Subject",
        body="Test body",
        scheduled_for=datetime.now() + timedelta(hours=1)
    )
    
    # Test queue operations
    assert queue_entry.is_ready_for_delivery() == False  # Not yet time
    queue_entry.scheduled_for = datetime.now() - timedelta(minutes=1)
    assert queue_entry.is_ready_for_delivery() == True
    
    # Test failure handling
    queue_entry.mark_failed("Test error")
    assert queue_entry.status == QueueStatus.FAILED
    assert queue_entry.attempts == 1
    
    # Test serialization
    queue_dict = queue_entry.to_dict()
    restored_queue = MessageQueue.from_dict(queue_dict)
    assert restored_queue.queue_id == queue_entry.queue_id
    
    print("✅ MessageQueue model test passed")


def test_analytics_model():
    """Test the CampaignAnalytics data model"""
    print("🧪 Testing CampaignAnalytics model...")
    
    analytics = CampaignAnalytics(
        analytics_id=str(uuid.uuid4()),
        campaign_id="test_campaign_123",
        date=datetime.now().date(),
        hook_opens=5,
        hook_clicks=2,
        hook_sent=True,
        proof_opens=3,
        proof_sent=True
    )
    
    # Test metric calculations
    analytics.update_metrics()
    assert analytics.get_total_opens() == 8
    assert analytics.get_total_sent() == 2
    assert analytics.engagement_rate == 4.0  # 8 opens / 2 sent
    
    # Test serialization
    analytics_dict = analytics.to_dict()
    restored_analytics = CampaignAnalytics.from_dict(analytics_dict)
    assert restored_analytics.analytics_id == analytics.analytics_id
    
    print("✅ CampaignAnalytics model test passed")


def test_database_creation():
    """Test database table creation"""
    print("🧪 Testing database creation...")
    
    try:
        create_campaign_tables()
        print("✅ Database creation test passed")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False
    
    return True


def test_configuration():
    """Test configuration loading"""
    print("🧪 Testing configuration...")
    
    config = get_config()
    
    # Test that config loads without errors
    assert config.HOOK_MESSAGE_DELAY_DAYS == 0
    assert config.PROOF_MESSAGE_DELAY_DAYS == 3
    assert config.FOMO_MESSAGE_DELAY_DAYS == 7
    
    delays = config.get_message_delays()
    assert delays['hook'] == 0
    assert delays['proof'] == 3
    assert delays['fomo'] == 7
    
    print("✅ Configuration test passed")


def main():
    """Run all foundation tests"""
    print("🚀 Testing Campaign System Foundation\n")
    
    try:
        test_campaign_model()
        test_queue_model()
        test_analytics_model()
        test_database_creation()
        test_configuration()
        
        print("\n🎉 All foundation tests passed!")
        print("✅ Campaign system foundation is working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)