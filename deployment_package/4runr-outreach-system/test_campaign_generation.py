#!/usr/bin/env python3
"""
Test script for campaign generation functionality

Tests the AI-powered campaign generator with sample lead data.
"""

import sys
import os
import json
from datetime import datetime

# Add campaign system to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from campaign_system.campaign_generator.generator import CampaignGenerator
from campaign_system.campaign_generator.quality_validator import CampaignQualityValidator


def test_campaign_generation():
    """Test campaign generation with sample data"""
    print("🧪 Testing Campaign Generation...")
    
    # Sample lead data (similar to trivago example)
    lead_data = {
        'id': 'test_lead_123',
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
    
    # Initialize generator
    generator = CampaignGenerator()
    
    # Generate campaign
    print(f"📧 Generating campaign for {lead_data['Name']} at {lead_data['Company']}...")
    campaign_data = generator.generate_campaign(lead_data, company_data)
    
    # Display results
    print(f"\n✅ Campaign generated successfully!")
    print(f"Generation method: {campaign_data.get('generation_method', 'unknown')}")
    print(f"Quality score: {campaign_data.get('quality_score', 0)}/100")
    
    if campaign_data.get('quality_issues'):
        print(f"Quality issues: {campaign_data['quality_issues']}")
    
    # Display each message
    messages = campaign_data.get('messages', [])
    for i, message in enumerate(messages, 1):
        msg_type = message.get('type', f'message_{i}').upper()
        subject = message.get('subject', 'No subject')
        body = message.get('body', 'No body')
        
        print(f"\n📨 {msg_type} MESSAGE (Day {[0, 3, 7][i-1]}):")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("-" * 60)
    
    # Test LinkedIn fallback
    linkedin_msg = generator.generate_linkedin_fallback(campaign_data)
    if linkedin_msg:
        print(f"\n💼 LinkedIn Fallback ({len(linkedin_msg)} chars):")
        print(linkedin_msg)
    
    return campaign_data


def test_quality_validation():
    """Test quality validation system"""
    print("\n🔍 Testing Quality Validation...")
    
    # Sample campaign data for validation
    sample_campaign = {
        'lead_id': 'test_123',
        'company': 'Test Company',
        'messages': [
            {
                'type': 'hook',
                'subject': 'Travel tech is evolving fast — is trivago still ahead?',
                'body': '''Hi Johannes,

Platforms like trivago changed the game by making hotel search effortless. But now, even that category is evolving — faster personalization, AI-native flows, zero-friction booking.

We're helping companies stay ahead of the curve without duct-taping new tools onto old infrastructure.

Would it make sense to connect briefly and compare notes on where things are heading?

— 4Runr Team'''
            },
            {
                'type': 'proof',
                'subject': 'What makes the fastest travel platforms win?',
                'body': '''Hi Johannes,

From what we've seen, it's not the brand or budget that wins in travel tech anymore — it's the system layer.

The teams getting ahead are building lean, modular infrastructure that:
• Cuts booking flow friction by 25–40%
• Personalizes without compromising speed
• Automates decisions, not just responses

That's exactly what we help optimize — quietly, and often invisibly.

Let me know if it's worth a quick chat on what's working best at your scale.

— 4Runr Team'''
            },
            {
                'type': 'fomo',
                'subject': 'Final note — some platforms are locking in their edge',
                'body': '''Hi Johannes,

A few of your competitors are already testing systems that streamline booking flow logic and reduce decision drop-offs. Quiet upgrades — big results.

That edge compounds fast.

If you're open to it, I'd love to share how we're helping similar platforms unlock performance without adding complexity.

No pressure — just figured I'd close the loop.

— 4Runr Team'''
            }
        ]
    }
    
    # Initialize validator
    validator = CampaignQualityValidator()
    
    # Validate campaign
    validation_result = validator.validate_campaign(sample_campaign)
    
    print(f"Overall Score: {validation_result['overall_score']:.1f}/100")
    print(f"Valid: {validation_result['valid']}")
    
    if validation_result['issues']:
        print(f"\nIssues:")
        for issue in validation_result['issues']:
            print(f"  ❌ {issue}")
    
    if validation_result['suggestions']:
        print(f"\nSuggestions:")
        for suggestion in validation_result['suggestions']:
            print(f"  💡 {suggestion}")
    
    # Show individual message scores
    print(f"\nMessage Scores:")
    for msg_type, score_data in validation_result['message_scores'].items():
        print(f"  {msg_type.upper()}: {score_data['score']}/100")
        if score_data['metrics']:
            metrics = score_data['metrics']
            print(f"    Words: {metrics.get('word_count', 0)}, Personalization: {metrics.get('personalization_score', 0)}/100")
    
    return validation_result


def test_fallback_generation():
    """Test fallback generation when AI is not available"""
    print("\n🔄 Testing Fallback Generation...")
    
    # Create generator without AI
    generator = CampaignGenerator()
    generator.client = None  # Force fallback mode
    
    lead_data = {
        'id': 'fallback_test',
        'Name': 'Jane Smith',
        'Company': 'TechCorp',
        'Title': 'CTO'
    }
    
    company_data = {
        'company_description': 'TechCorp provides enterprise software solutions',
        'top_services': 'Software development, Cloud services, IT consulting',
        'tone': 'Professional'
    }
    
    campaign_data = generator.generate_campaign(lead_data, company_data)
    
    print(f"Generation method: {campaign_data.get('generation_method', 'unknown')}")
    print(f"Quality score: {campaign_data.get('quality_score', 0)}/100")
    
    # Show first message as example
    if campaign_data.get('messages'):
        first_msg = campaign_data['messages'][0]
        print(f"\nSample {first_msg.get('type', 'message').upper()} message:")
        print(f"Subject: {first_msg.get('subject', 'No subject')}")
        print(f"Body preview: {first_msg.get('body', 'No body')[:100]}...")
    
    return campaign_data


def main():
    """Run all campaign generation tests"""
    print("🚀 Testing Campaign Generation System\n")
    
    try:
        # Test main campaign generation
        campaign_data = test_campaign_generation()
        
        # Test quality validation
        validation_result = test_quality_validation()
        
        # Test fallback generation
        fallback_data = test_fallback_generation()
        
        print("\n🎉 All campaign generation tests completed!")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"  Main campaign quality: {campaign_data.get('quality_score', 0)}/100")
        print(f"  Validation score: {validation_result.get('overall_score', 0):.1f}/100")
        print(f"  Fallback quality: {fallback_data.get('quality_score', 0)}/100")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)