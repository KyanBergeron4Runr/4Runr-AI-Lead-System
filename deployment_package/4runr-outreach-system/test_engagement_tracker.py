#!/usr/bin/env python3
"""
Test script for the Engagement Level Tracker functionality.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.engagement_level_tracker import EngagementLevelTracker, EngagementLevelConfig


def test_engagement_tracker():
    """Test the Engagement Level Tracker functionality."""
    print("🧪 Testing Engagement Level Tracker...")
    
    # Test 1: Initialize tracker
    print("\n1. Testing tracker initialization...")
    try:
        tracker = EngagementLevelTracker()
        print("   ✅ Tracker initialized successfully")
        print(f"   📊 Available engagement levels: {list(tracker.ENGAGEMENT_LEVELS.keys())}")
    except Exception as e:
        print(f"   ❌ Failed to initialize tracker: {e}")
        return False
    
    # Test 2: Test engagement level configuration
    print("\n2. Testing engagement level configuration...")
    for level_name, config in tracker.ENGAGEMENT_LEVELS.items():
        print(f"   📋 {level_name}:")
        print(f"      - Display: {config.display_name}")
        print(f"      - Tone: {config.message_tone}")
        print(f"      - Next: {config.next_level}")
        print(f"      - Skip if reached: {config.skip_if_reached}")
    
    # Test 3: Test level progression logic
    print("\n3. Testing level progression logic...")
    progression_tests = [
        ('1st degree', '2nd degree'),
        ('2nd degree', '3rd degree'),
        ('3rd degree', 'retry'),
        ('retry', None),
        ('unknown_level', None)
    ]
    
    for current, expected_next in progression_tests:
        actual_next = tracker.get_next_engagement_level(current)
        status = "✅" if actual_next == expected_next else "❌"
        print(f"   {status} {current} → {actual_next} (expected: {expected_next})")
    
    # Test 4: Test current level detection
    print("\n4. Testing current level detection...")
    test_leads = [
        ({'Level Engaged': '1st degree'}, '1st degree'),
        ({'Level Engaged': ['2nd degree']}, '2nd degree'),  # Airtable list format
        ({'Level Engaged': ''}, '1st degree'),  # Empty defaults to 1st
        ({}, '1st degree'),  # Missing field defaults to 1st
        ({'Level Engaged': 'invalid_level'}, '1st degree')  # Invalid defaults to 1st
    ]
    
    for lead_data, expected_level in test_leads:
        actual_level = tracker.get_current_engagement_level(lead_data)
        status = "✅" if actual_level == expected_level else "❌"
        print(f"   {status} {lead_data} → {actual_level} (expected: {expected_level})")
    
    # Test 5: Test skip logic
    print("\n5. Testing skip logic...")
    skip_tests = [
        ({'Level Engaged': '1st degree'}, False),
        ({'Level Engaged': '2nd degree'}, False),
        ({'Level Engaged': '3rd degree'}, False),
        ({'Level Engaged': 'retry'}, True),  # Should skip retry level
        ({'Level Engaged': ''}, False)  # Empty defaults to 1st, should not skip
    ]
    
    for lead_data, expected_skip in skip_tests:
        actual_skip = tracker.should_skip_lead(lead_data)
        status = "✅" if actual_skip == expected_skip else "❌"
        level = tracker.get_current_engagement_level(lead_data)
        print(f"   {status} Level '{level}' → skip: {actual_skip} (expected: {expected_skip})")
    
    # Test 6: Test message tone retrieval
    print("\n6. Testing message tone retrieval...")
    for level in tracker.ENGAGEMENT_LEVELS.keys():
        tone = tracker.get_message_tone_for_level(level)
        expected_tone = tracker.ENGAGEMENT_LEVELS[level].message_tone
        status = "✅" if tone == expected_tone else "❌"
        print(f"   {status} {level} → {tone}")
    
    # Test 7: Test field validation (will fail without Airtable connection, but tests the logic)
    print("\n7. Testing field validation...")
    try:
        is_valid = tracker.validate_engagement_level_field()
        print(f"   📊 Field validation result: {is_valid}")
        print("   ℹ️  Note: May fail without proper Airtable connection")
    except Exception as e:
        print(f"   ⚠️  Field validation error (expected without Airtable): {e}")
    
    print("\n🎉 Engagement Level Tracker tests completed!")
    return True


if __name__ == '__main__':
    success = test_engagement_tracker()
    sys.exit(0 if success else 1)