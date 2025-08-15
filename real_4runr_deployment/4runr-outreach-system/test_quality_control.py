#!/usr/bin/env python3
"""
Test script for campaign quality control system

Tests comprehensive quality scoring, issue detection, and validation.
"""

import sys
import os
import importlib.util

# Direct import to avoid dependency issues
spec = importlib.util.spec_from_file_location("simple_generator", "campaign_system/campaign_generator/simple_generator.py")
simple_generator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple_generator_module)
SimpleCampaignGenerator = simple_generator_module.SimpleCampaignGenerator

spec2 = importlib.util.spec_from_file_location("quality_control", "campaign_system/campaign_generator/quality_control.py")
quality_control_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(quality_control_module)
MessageQualityController = quality_control_module.MessageQualityController
CampaignQualityController = quality_control_module.CampaignQualityController


def test_message_quality_scoring():
    """Test individual message quality scoring"""
    print("🔍 Testing Message Quality Scoring...")
    
    # Test data
    lead_data = {
        'Name': 'Johannes Reck',
        'Company': 'trivago',
        'Title': 'CEO'
    }
    
    company_data = {
        'company_description': 'trivago is a global hotel search platform',
        'top_services': 'Hotel price comparison, Travel booking',
        'tone': 'Professional'
    }
    
    controller = MessageQualityController()
    
    # Test high-quality message
    high_quality_message = {
        'type': 'hook',
        'subject': 'Travel tech is evolving fast — is trivago still ahead?',
        'body': '''Hello Johannes,

Platforms like trivago changed the game by making hotel search effortless. But now, even that category is evolving — faster personalization, AI-native flows, zero-friction booking.

We're helping companies stay ahead of the curve without duct-taping new tools onto old infrastructure.

Would it make sense to connect briefly and compare notes on where things are heading?

— 4Runr Team'''
    }
    
    analysis = controller.analyze_message_quality(high_quality_message, 'hook', lead_data, company_data)
    
    print(f"\n📊 High-Quality Message Analysis:")
    print(f"  Quality Score: {analysis['quality_score']}/100")
    print(f"  Quality Tier: {analysis['quality_tier']}")
    print(f"  Issues Detected: {len(analysis['issues_detected'])}")
    
    if analysis['issues_detected']:
        print(f"  Issues:")
        for issue in analysis['issues_detected']:
            print(f"    ❌ {issue}")
    
    if analysis['suggestions']:
        print(f"  Suggestions:")
        for suggestion in analysis['suggestions']:
            print(f"    💡 {suggestion}")
    
    # Show detailed metrics
    metrics = analysis['metrics']
    print(f"\n📈 Detailed Metrics:")
    print(f"  Word Count: {metrics['word_count']}")
    print(f"  Personalization Elements:")
    print(f"    Has Lead Name: {metrics['personalization_elements']['has_lead_name']}")
    print(f"    Has Company Name: {metrics['personalization_elements']['has_company_name']}")
    print(f"    Industry References: {metrics['personalization_elements']['industry_references']}")
    print(f"  Content Quality:")
    print(f"    Strategic Language: {metrics['content_quality']['strategic_language_count']}")
    print(f"    Generic Phrases: {metrics['content_quality']['generic_phrase_count']}")
    print(f"    Questions: {metrics['content_quality']['question_count']}")
    
    return analysis


def test_poor_quality_message():
    """Test detection of poor quality messages"""
    print("\n🚨 Testing Poor Quality Message Detection...")
    
    lead_data = {
        'Name': 'John Doe',
        'Company': 'TestCorp',
        'Title': 'Manager'
    }
    
    company_data = {
        'company_description': 'TestCorp provides business solutions',
        'tone': 'Professional'
    }
    
    controller = MessageQualityController()
    
    # Poor quality message with multiple issues
    poor_message = {
        'type': 'hook',
        'subject': 'Hi',  # Too short
        'body': '''Hey there,

I wanted to reach out because I came across your company and we provide solutions that could help. We offer services and I hope this email finds you well.

Let me know if you're interested. Buy now for a special deal!

Thanks'''  # Generic, salesy, missing signature
    }
    
    analysis = controller.analyze_message_quality(poor_message, 'hook', lead_data, company_data)
    
    print(f"\n📊 Poor Quality Message Analysis:")
    print(f"  Quality Score: {analysis['quality_score']}/100")
    print(f"  Quality Tier: {analysis['quality_tier']}")
    print(f"  Issues Detected: {len(analysis['issues_detected'])}")
    
    print(f"\n❌ Issues Found:")
    for issue in analysis['issues_detected']:
        print(f"    • {issue}")
    
    print(f"\n💡 Suggestions:")
    for suggestion in analysis['suggestions']:
        print(f"    • {suggestion}")
    
    return analysis


def test_campaign_quality_analysis():
    """Test complete campaign quality analysis"""
    print("\n🎯 Testing Complete Campaign Quality Analysis...")
    
    # Generate a campaign first
    generator = SimpleCampaignGenerator()
    
    lead_data = {
        'id': 'quality_test',
        'Name': 'Sarah Johnson',
        'Company': 'CloudTech',
        'Title': 'VP of Product'
    }
    
    company_data = {
        'company_description': 'CloudTech provides SaaS solutions for enterprise workflow management',
        'top_services': 'Software as a Service, API integrations, Cloud platforms',
        'tone': 'Professional',
        'traits': ['enterprise', 'API-based', 'cloud-native']
    }
    
    campaign_data = generator.generate_campaign(lead_data, company_data)
    
    print(f"\n📧 Campaign Generated:")
    print(f"  Overall Quality Score: {campaign_data.get('overall_quality_score', 0):.1f}/100")
    print(f"  Quality Tier: {campaign_data.get('quality_tier', 'Unknown')}")
    print(f"  Ready to Send: {campaign_data.get('ready_to_send', False)}")
    
    # Show individual message scores
    messages = campaign_data.get('messages', [])
    print(f"\n📨 Individual Message Scores:")
    
    for i, message in enumerate(messages, 1):
        msg_type = message.get('type', f'message_{i}').upper()
        quality_score = message.get('quality_score', 0)
        quality_tier = message.get('quality_tier', 'Unknown')
        issues_count = len(message.get('issues_detected', []))
        
        print(f"  {msg_type}: {quality_score}/100 ({quality_tier}) - {issues_count} issues")
        
        # Show first few issues if any
        issues = message.get('issues_detected', [])
        if issues:
            for issue in issues[:2]:  # Show first 2 issues
                print(f"    ❌ {issue}")
            if len(issues) > 2:
                print(f"    ... and {len(issues) - 2} more issues")
    
    # Show campaign-level analysis
    quality_analysis = campaign_data.get('quality_analysis', {})
    
    if quality_analysis.get('campaign_issues'):
        print(f"\n🚨 Campaign Issues:")
        for issue in quality_analysis['campaign_issues']:
            print(f"  ❌ {issue}")
    
    if quality_analysis.get('campaign_suggestions'):
        print(f"\n💡 Campaign Suggestions:")
        for suggestion in quality_analysis['campaign_suggestions']:
            print(f"  • {suggestion}")
    
    # Show progression analysis
    progression = quality_analysis.get('progression_analysis', {})
    if progression:
        print(f"\n🔄 Progression Analysis:")
        print(f"  Score: {progression.get('score', 0)}/100")
        if progression.get('issues'):
            for issue in progression['issues']:
                print(f"    ❌ {issue}")
    
    return campaign_data


def test_quality_control_integration():
    """Test quality control integration with campaign generation"""
    print("\n🔧 Testing Quality Control Integration...")
    
    # Test multiple campaigns with different quality levels
    test_cases = [
        {
            'name': 'High-Quality Lead (CEO)',
            'lead_data': {
                'id': 'ceo_test',
                'Name': 'Michael Chen',
                'Company': 'InnovateTech',
                'Title': 'CEO'
            },
            'company_data': {
                'company_description': 'InnovateTech is a leading fintech platform providing payment solutions',
                'top_services': 'Payment processing, Financial APIs, Fraud detection',
                'tone': 'Professional',
                'traits': ['enterprise', 'fintech', 'API-based']
            }
        },
        {
            'name': 'Standard Lead (Manager)',
            'lead_data': {
                'id': 'manager_test',
                'Name': 'Lisa',
                'Company': 'SmallCorp',
                'Title': 'Marketing Manager'
            },
            'company_data': {
                'company_description': 'SmallCorp provides marketing services',
                'top_services': 'Digital marketing, SEO',
                'tone': 'Casual'
            }
        }
    ]
    
    generator = SimpleCampaignGenerator()
    results = []
    
    for test_case in test_cases:
        print(f"\n🎯 Testing {test_case['name']}...")
        
        campaign_data = generator.generate_campaign(
            test_case['lead_data'], 
            test_case['company_data']
        )
        
        overall_score = campaign_data.get('overall_quality_score', 0)
        quality_tier = campaign_data.get('quality_tier', 'Unknown')
        ready_to_send = campaign_data.get('ready_to_send', False)
        
        print(f"  Overall Score: {overall_score:.1f}/100")
        print(f"  Quality Tier: {quality_tier}")
        print(f"  Ready to Send: {'✅' if ready_to_send else '❌'}")
        
        # Count total issues across all messages
        total_issues = 0
        for message in campaign_data.get('messages', []):
            total_issues += len(message.get('issues_detected', []))
        
        print(f"  Total Issues: {total_issues}")
        
        results.append({
            'name': test_case['name'],
            'score': overall_score,
            'tier': quality_tier,
            'ready': ready_to_send,
            'issues': total_issues
        })
    
    return results


def main():
    """Run all quality control tests"""
    print("🚀 Testing Campaign Quality Control System\n")
    
    try:
        # Test individual message quality
        high_quality_analysis = test_message_quality_scoring()
        
        # Test poor quality detection
        poor_quality_analysis = test_poor_quality_message()
        
        # Test complete campaign analysis
        campaign_analysis = test_campaign_quality_analysis()
        
        # Test integration
        integration_results = test_quality_control_integration()
        
        print("\n🎉 All quality control tests completed!")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"  High-Quality Message Score: {high_quality_analysis['quality_score']}/100")
        print(f"  Poor-Quality Message Score: {poor_quality_analysis['quality_score']}/100")
        print(f"  Campaign Overall Score: {campaign_analysis.get('overall_quality_score', 0):.1f}/100")
        
        print(f"\n🔧 Integration Test Results:")
        for result in integration_results:
            status = "✅ Ready" if result['ready'] else "❌ Needs Work"
            print(f"  {result['name']}: {result['score']:.1f}/100 ({result['tier']}) - {status}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)