#!/usr/bin/env python3
"""
Test script to demonstrate fallback mode with low-quality data leads
"""

import asyncio
import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent / "4runr-outreach-system"))
sys.path.append(str(Path(__file__).parent))

from campaign_brain import CampaignBrainGraph, CampaignBrainConfig

async def test_fallback_mode():
    """Test fallback mode with different data quality scenarios"""
    
    print("🧪 Testing Fallback Mode with Low-Quality Data")
    print("=" * 60)
    
    config = CampaignBrainConfig()
    brain = CampaignBrainGraph(config)
    
    # Test scenarios with different data quality levels
    test_scenarios = [
        {
            "name": "No Website Data",
            "lead_data": {
                "id": "test_no_website_001",
                "Name": "John Smith",
                "Company": "Generic Corp",
                "Title": "CEO",
                "LinkedIn_URL": "https://linkedin.com/in/johnsmith",
                "Email": "john@genericcorp.com"
            },
            "company_data": {
                "description": "",
                "services": "",
                "tone": "Professional",
                "website_insights": ""
            },
            "scraped_content": {
                "homepage_text": "",
                "about_page": ""
            }
        },
        {
            "name": "Low Signal Website",
            "lead_data": {
                "id": "test_low_signal_002",
                "Name": "Sarah Johnson",
                "Company": "Modern Solutions Inc",
                "Title": "VP Operations",
                "LinkedIn_URL": "https://linkedin.com/in/sarahjohnson",
                "Email": "sarah@modernsolutions.com"
            },
            "company_data": {
                "description": "Modern ERP for Growing Businesses. We are the leading provider of innovative solutions.",
                "services": "Business solutions, comprehensive platform, trusted partner",
                "tone": "Professional",
                "website_insights": "Modern solutions for today's challenges. Industry expertise."
            },
            "scraped_content": {
                "homepage_text": "We provide cutting-edge solutions for modern businesses.",
                "about_page": "Leading provider of innovative business solutions."
            }
        },
        {
            "name": "Insufficient Enrichment",
            "lead_data": {
                "id": "test_insufficient_003",
                "Name": "Mike Davis",
                "Company": "TechCorp",
                "Title": "Manager",
                "LinkedIn_URL": "",
                "Email": ""
            },
            "company_data": {
                "description": "TechCorp provides technology services to businesses.",
                "services": "Technology consulting",
                "tone": "Professional",
                "website_insights": ""
            },
            "scraped_content": {
                "homepage_text": "Technology services for business growth.",
                "about_page": ""
            }
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print(f"   Lead: {scenario['lead_data']['Name']} at {scenario['lead_data']['Company']}")
        
        try:
            # Execute campaign brain
            result = await brain.execute(scenario['lead_data'])
            
            print(f"   ✅ Status: {result.final_status.value}")
            print(f"   📊 Quality Score: {result.overall_quality_score:.1f}/100")
            print(f"   🔄 Fallback Mode: {getattr(result, 'fallback_mode', 'Not set')}")
            
            if hasattr(result, 'data_quality'):
                data_quality = result.data_quality
                print(f"   📈 Data Quality Score: {data_quality.get('quality_score', 'N/A')}/10")
                print(f"   🎯 Fallback Reason: {data_quality.get('fallback_reason', 'None')}")
            
            # Show generated message
            if result.messages:
                message = result.messages[0]
                print(f"   📝 Message Type: {message.message_type}")
                print(f"   📧 Subject: {message.subject}")
                print(f"   💬 Body Preview: {message.body[:100]}...")
            
            results.append({
                'scenario': scenario['name'],
                'success': True,
                'fallback_mode': getattr(result, 'fallback_mode', False),
                'quality_score': result.overall_quality_score,
                'data_quality_score': getattr(result, 'data_quality', {}).get('quality_score', 0)
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'scenario': scenario['name'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FALLBACK MODE TEST SUMMARY")
    print("=" * 60)
    
    for result in results:
        if result['success']:
            fallback_status = "✅ Used Fallback" if result.get('fallback_mode') else "❌ No Fallback"
            print(f"{result['scenario']}: {fallback_status}")
            print(f"   Quality: {result['quality_score']:.1f}/100, Data: {result['data_quality_score']}/10")
        else:
            print(f"{result['scenario']}: ❌ Failed - {result.get('error', 'Unknown error')}")
    
    fallback_count = sum(1 for r in results if r.get('success') and r.get('fallback_mode'))
    print(f"\n🎯 Fallback Mode Triggered: {fallback_count}/{len(results)} scenarios")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_fallback_mode())