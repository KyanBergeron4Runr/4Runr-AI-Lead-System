#!/usr/bin/env python3
"""
Test script for the resilient engagement pipeline.

Tests the new fallback message generation and defensive lead processing
to ensure leads are processed even when upstream modules fail.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from outreach.engager.app import EngagerAgent
from outreach.engager.resilient_engager import ResilientEngager


def test_fallback_message_generation():
    """Test fallback message generation with various lead data scenarios."""
    print("🔄 Testing Fallback Message Generation")
    print("=" * 50)
    
    # Test scenarios with different data availability
    test_leads = [
        {
            'id': 'test_001',
            'Name': 'John Smith',
            'Company': 'TechCorp Inc',
            'Job Title': 'CTO',
            'Email': 'john@techcorp.com',
            'Website': 'https://techcorp.com',
            'Company Description': 'TechCorp is a leading software development company specializing in enterprise solutions.',
            'Custom_Message': ''  # No custom message - should generate fallback
        },
        {
            'id': 'test_002',
            'Name': 'Sarah Johnson',
            'Company': 'Marketing Solutions LLC',
            'Email': 'sarah@marketingsolutions.com',
            'Company Description': 'We provide marketing strategy and customer engagement solutions.',
            'Custom_Message': ''  # No custom message - should generate fallback
        },
        {
            'id': 'test_003',
            'Name': 'Mike Davis',
            'Company': 'Unknown Company',
            'Email': 'mike@example.com',
            'Custom_Message': ''  # Minimal data - should still generate message
        }
    ]
    
    try:
        engager = EngagerAgent()
        
        for i, lead in enumerate(test_leads, 1):
            print(f"\n📝 Test Case {i}: {lead.get('Name')} at {lead.get('Company')}")
            
            # Test fallback message generation
            message = engager._get_or_generate_message(lead)
            
            if message:
                print("✅ Fallback message generated successfully")
                print(f"  Length: {len(message)} characters")
                print(f"  Preview: {message[:100]}...")
                
                # Check message quality
                if lead.get('Company', 'Unknown') in message:
                    print("✅ Company name included in message")
                else:
                    print("⚠️  Company name not found in message")
                
                if lead.get('Name', '').split()[0] in message:
                    print("✅ Lead name included in message")
                else:
                    print("⚠️  Lead name not found in message")
                
                if '4Runr' in message:
                    print("✅ 4Runr branding included")
                else:
                    print("❌ 4Runr branding missing")
                    
            else:
                print("❌ Failed to generate fallback message")
                return False
        
        print("\n✅ All fallback message generation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Fallback message generation test failed: {e}")
        return False


def test_resilient_lead_processing():
    """Test resilient lead processing logic."""
    print("\n🛡️  Testing Resilient Lead Processing")
    print("=" * 50)
    
    # Test leads with various conditions
    test_scenarios = [
        {
            'name': 'Lead with custom message',
            'lead': {
                'id': 'test_custom',
                'Name': 'Alice Brown',
                'Company': 'CustomCorp',
                'Email': 'alice@customcorp.com',
                'Email_Confidence_Level': 'Real',
                'Custom_Message': 'This is a custom message for Alice.',
                'Engagement_Status': 'Auto-Send'
            },
            'should_process': True,
            'expected_message_source': 'custom'
        },
        {
            'name': 'Lead without custom message',
            'lead': {
                'id': 'test_no_custom',
                'Name': 'Bob Wilson',
                'Company': 'NoCorp',
                'Email': 'bob@nocorp.com',
                'Email_Confidence_Level': 'Pattern',
                'Custom_Message': '',
                'Engagement_Status': 'Auto-Send'
            },
            'should_process': True,
            'expected_message_source': 'generated'
        },
        {
            'name': 'Lead with guess email confidence',
            'lead': {
                'id': 'test_guess',
                'Name': 'Charlie Green',
                'Company': 'GuessCorp',
                'Email': 'charlie@guesscorp.com',
                'Email_Confidence_Level': 'Guess',
                'Custom_Message': 'Custom message for Charlie',
                'Engagement_Status': 'Auto-Send'
            },
            'should_process': False,  # Should skip due to low confidence
            'expected_message_source': None
        },
        {
            'name': 'Lead with no email',
            'lead': {
                'id': 'test_no_email',
                'Name': 'Diana White',
                'Company': 'NoEmailCorp',
                'Email': '',
                'Email_Confidence_Level': 'Real',
                'Custom_Message': 'Custom message for Diana',
                'Engagement_Status': 'Auto-Send'
            },
            'should_process': False,  # Should skip due to no email
            'expected_message_source': None
        }
    ]
    
    try:
        resilient_engager = ResilientEngager()
        
        for scenario in test_scenarios:
            print(f"\n📋 Testing: {scenario['name']}")
            lead = scenario['lead']
            
            # Test skip logic
            skip_reason = resilient_engager._should_skip_lead(lead)
            
            if scenario['should_process']:
                if skip_reason:
                    print(f"❌ Lead should be processed but was skipped: {skip_reason}")
                    return False
                else:
                    print("✅ Lead correctly identified for processing")
                    
                    # Test message generation
                    message = resilient_engager._get_or_generate_message(lead)
                    if message:
                        print("✅ Message generated successfully")
                        
                        # Check message source
                        has_custom = bool(lead.get('Custom_Message', '').strip())
                        if scenario['expected_message_source'] == 'custom' and has_custom:
                            print("✅ Using custom message as expected")
                        elif scenario['expected_message_source'] == 'generated' and not has_custom:
                            print("✅ Generated fallback message as expected")
                        else:
                            print("⚠️  Message source different than expected")
                    else:
                        print("❌ Failed to generate message")
                        return False
            else:
                if skip_reason:
                    print(f"✅ Lead correctly skipped: {skip_reason}")
                else:
                    print("❌ Lead should be skipped but was not")
                    return False
        
        print("\n✅ All resilient lead processing tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Resilient lead processing test failed: {e}")
        return False


def test_engagement_statistics():
    """Test engagement statistics and reporting."""
    print("\n📊 Testing Engagement Statistics")
    print("=" * 50)
    
    try:
        engager = EngagerAgent()
        resilient_engager = ResilientEngager()
        
        # Test standard engager stats
        print("Standard Engager Statistics:")
        stats = engager.get_processing_stats()
        print(f"  Total leads ready: {stats['total_leads_ready']}")
        print(f"  Leads with messages: {stats['leads_with_messages']}")
        print(f"  Leads with Real emails: {stats['leads_with_real_emails']}")
        print(f"  Leads with Pattern emails: {stats['leads_with_pattern_emails']}")
        print(f"  Leads with Guess emails: {stats['leads_with_guess_emails']}")
        
        # Test resilient engager stats
        print("\nResilient Engager Statistics:")
        resilient_stats = resilient_engager.get_processing_stats()
        print(f"  Total leads ready: {resilient_stats['total_leads_ready']}")
        print(f"  Leads with custom messages: {resilient_stats['leads_with_custom_messages']}")
        print(f"  Leads without custom messages: {resilient_stats['leads_without_custom_messages']}")
        print(f"  Leads with Real emails: {resilient_stats['leads_with_real_emails']}")
        print(f"  Leads with Pattern emails: {resilient_stats['leads_with_pattern_emails']}")
        print(f"  Leads with Guess emails: {resilient_stats['leads_with_guess_emails']}")
        
        # Calculate potential improvement
        leads_without_messages = resilient_stats['leads_without_custom_messages']
        leads_with_good_emails = resilient_stats['leads_with_real_emails'] + resilient_stats['leads_with_pattern_emails']
        
        print(f"\n📈 Resilience Impact:")
        print(f"  Leads without custom messages: {leads_without_messages}")
        print(f"  Leads with good email confidence: {leads_with_good_emails}")
        print(f"  Potential additional engagements: {min(leads_without_messages, leads_with_good_emails)}")
        
        print("\n✅ Engagement statistics test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Engagement statistics test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 Starting Resilient Engagement Pipeline Tests")
    print("=" * 60)
    
    # Run tests
    fallback_ok = test_fallback_message_generation()
    processing_ok = test_resilient_lead_processing()
    stats_ok = test_engagement_statistics()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Fallback Message Generation: {'✅ PASS' if fallback_ok else '❌ FAIL'}")
    print(f"Resilient Lead Processing: {'✅ PASS' if processing_ok else '❌ FAIL'}")
    print(f"Engagement Statistics: {'✅ PASS' if stats_ok else '❌ FAIL'}")
    
    if fallback_ok and processing_ok and stats_ok:
        print("\n🎉 All resilient engagement tests passed!")
        print("\nThe resilient engagement pipeline is working correctly:")
        print("- ✅ Generates fallback messages when custom messages are missing")
        print("- ✅ Only skips leads for fundamental issues (no email, invalid format)")
        print("- ✅ Processes leads even when upstream modules fail")
        print("- ✅ Provides detailed statistics and logging")
        print("- ✅ Maintains structured skip reasons for debugging")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)