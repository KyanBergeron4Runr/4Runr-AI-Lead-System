#!/usr/bin/env python3
"""
Simple test script for campaign generation functionality

Tests the campaign generator with sample lead data using simplified dependencies.
"""

import sys
import os
import json

# Add campaign system to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Direct import to avoid dependency issues
import importlib.util
spec = importlib.util.spec_from_file_location("simple_generator", "campaign_system/campaign_generator/simple_generator.py")
simple_generator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple_generator_module)
SimpleCampaignGenerator = simple_generator_module.SimpleCampaignGenerator


def test_trivago_campaign():
    """Test campaign generation with trivago example"""
    print("🧪 Testing Campaign Generation with Trivago Example...")
    
    # Sample lead data (from your example)
    lead_data = {
        'id': 'trivago_test_123',
        'Name': 'Johannes Reck',
        'Company': 'trivago',
        'Title': 'CEO',
        'Email': 'johannes@trivago.com'
    }
    
    # Sample company data
    company_data = {
        'company_description': 'trivago is a global hotel search platform that helps travelers find and compare hotel prices from hundreds of booking sites.',
        'top_services': 'Hotel price comparison, Travel booking platform, Hotel search engine',
        'tone': 'Professional',
        'traits': ['enterprise', 'multi-language', 'search-based'],
        'website_headline': 'Compare hotel prices worldwide'
    }
    
    # Initialize generator (without OpenAI key for testing)
    generator = SimpleCampaignGenerator()
    
    # Generate campaign
    campaign_data = generator.generate_campaign(lead_data, company_data)
    
    # Display results
    print(f"\n✅ Campaign generated successfully!")
    print(f"Generation method: {campaign_data.get('generation_method', 'unknown')}")
    print(f"Quality score: {campaign_data.get('quality_score', 0)}/100")
    
    # Display each message
    messages = campaign_data.get('messages', [])
    for i, message in enumerate(messages, 1):
        msg_type = message.get('type', f'message_{i}').upper()
        subject = message.get('subject', 'No subject')
        body = message.get('body', 'No body')
        
        day = [0, 3, 7][i-1] if i <= 3 else i-1
        
        print(f"\n📨 {msg_type} MESSAGE (Day {day}):")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("-" * 60)
    
    # Test LinkedIn fallback
    linkedin_msg = generator.generate_linkedin_fallback(campaign_data)
    print(f"\n💼 LinkedIn Fallback ({len(linkedin_msg)} chars):")
    print(linkedin_msg)
    
    return campaign_data


def test_different_industries():
    """Test campaign generation for different industries"""
    print("\n🏭 Testing Different Industries...")
    
    industries = [
        {
            'name': 'SaaS Company',
            'lead_data': {
                'id': 'saas_test',
                'Name': 'Sarah Johnson',
                'Company': 'CloudTech',
                'Title': 'VP of Product'
            },
            'company_data': {
                'company_description': 'CloudTech provides SaaS solutions for enterprise workflow management',
                'top_services': 'Software as a Service, API integrations, Cloud platforms',
                'tone': 'Professional',
                'traits': ['enterprise', 'API-based', 'cloud-native']
            }
        },
        {
            'name': 'E-commerce Platform',
            'lead_data': {
                'id': 'ecom_test',
                'Name': 'Mike Chen',
                'Company': 'ShopFast',
                'Title': 'CTO'
            },
            'company_data': {
                'company_description': 'ShopFast is an e-commerce platform helping retailers sell online',
                'top_services': 'Online store builder, Payment processing, Inventory management',
                'tone': 'Casual',
                'traits': ['retail', 'mobile-first', 'payment-focused']
            }
        }
    ]
    
    generator = SimpleCampaignGenerator()
    
    for industry in industries:
        print(f"\n🎯 Testing {industry['name']}...")
        
        campaign_data = generator.generate_campaign(
            industry['lead_data'], 
            industry['company_data']
        )
        
        # Show just the hook message as example
        if campaign_data.get('messages'):
            hook_msg = campaign_data['messages'][0]
            print(f"Hook Subject: {hook_msg.get('subject', 'No subject')}")
            print(f"Quality Score: {campaign_data.get('quality_score', 0)}/100")
    
    return True


def test_output_format():
    """Test that output matches the required JSON structure"""
    print("\n📋 Testing Output Format...")
    
    lead_data = {
        'id': 'format_test',
        'Name': 'Test User',
        'Company': 'Test Company',
        'Title': 'Test Role'
    }
    
    company_data = {
        'company_description': 'Test company description',
        'top_services': 'Test services',
        'tone': 'Professional'
    }
    
    generator = SimpleCampaignGenerator()
    campaign_data = generator.generate_campaign(lead_data, company_data)
    
    # Check required structure
    required_fields = ['lead_id', 'company', 'messages', 'generated_at', 'generation_method']
    missing_fields = [field for field in required_fields if field not in campaign_data]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    # Check messages structure
    messages = campaign_data.get('messages', [])
    if len(messages) != 3:
        print(f"❌ Expected 3 messages, got {len(messages)}")
        return False
    
    expected_types = ['hook', 'proof', 'fomo']
    for i, message in enumerate(messages):
        expected_type = expected_types[i]
        if message.get('type') != expected_type:
            print(f"❌ Message {i+1} should be {expected_type}, got {message.get('type')}")
            return False
        
        if not message.get('subject') or not message.get('body'):
            print(f"❌ Message {i+1} missing subject or body")
            return False
    
    print("✅ Output format is correct!")
    
    # Show the structure
    print(f"\nStructure preview:")
    print(f"  lead_id: {campaign_data['lead_id']}")
    print(f"  company: {campaign_data['company']}")
    print(f"  messages: {len(campaign_data['messages'])} messages")
    print(f"  generation_method: {campaign_data['generation_method']}")
    
    return True


def main():
    """Run all campaign generation tests"""
    print("🚀 Testing Simple Campaign Generation System\n")
    
    try:
        # Test main trivago example
        trivago_campaign = test_trivago_campaign()
        
        # Test different industries
        test_different_industries()
        
        # Test output format
        format_test = test_output_format()
        
        print("\n🎉 All campaign generation tests completed!")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"  Trivago campaign quality: {trivago_campaign.get('quality_score', 0)}/100")
        print(f"  Output format test: {'✅ Passed' if format_test else '❌ Failed'}")
        print(f"  Generation method: {trivago_campaign.get('generation_method', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)