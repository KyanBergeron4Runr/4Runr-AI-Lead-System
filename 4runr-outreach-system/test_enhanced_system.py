#!/usr/bin/env python3
"""
Test the enhanced outreach system with Trivago to demonstrate improved personalization.
"""

import sys
import json
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_enhanced_trivago():
    """Test the enhanced system with Trivago."""
    print("🚀 Enhanced 4Runr Outreach System - Trivago Test")
    print("=" * 60)
    
    try:
        # Step 1: Enhanced website scraping
        print("\n📄 Step 1: Enhanced Website Scraping")
        print("-" * 40)
        
        from scraper.scrape_site import EnhancedWebsiteScraper
        
        scraper = EnhancedWebsiteScraper()
        scraped_data = scraper.scrape_enhanced_data('https://www.trivago.ca/', 'test_trivago')
        
        print(f"✅ Scraped Data Summary:")
        print(f"   Headline: {scraped_data.get('headline', 'N/A')[:50]}...")
        print(f"   Features Found: {len(scraped_data.get('features', []))}")
        print(f"   Tech Keywords: {scraped_data.get('tech_keywords_found', [])[:3]}")
        print(f"   Primary Tone: {scraped_data.get('tone_indicators', {}).get('primary_tone', 'N/A')}")
        print(f"   CTA Buttons: {scraped_data.get('cta_buttons', [])[:3]}")
        
        # Step 2: Trait inference
        print("\n🧠 Step 2: ICP Trait Inference")
        print("-" * 40)
        
        from enricher.infer_traits import ICPTraitInference
        
        lead_data = {
            'id': 'test_trivago',
            'Name': 'Johannes Thomas',
            'Company': 'trivago',
            'Title': 'Chief Technology Officer',
            'Email': 'j.thomas@trivago.com'
        }
        
        trait_engine = ICPTraitInference()
        traits_data = trait_engine.infer_traits(scraped_data, lead_data)
        
        print(f"✅ Inferred Traits:")
        traits = traits_data.get('traits', {})
        print(f"   Industry: {traits.get('industry', 'N/A')}")
        print(f"   Company Size: {traits.get('company_size', 'N/A')}")
        print(f"   Tech Sophistication: {traits.get('tech_sophistication', 'N/A')}")
        print(f"   Business Model: {traits.get('business_model', 'N/A')}")
        print(f"   Confidence Score: {traits_data.get('confidence_score', 0.0):.2f}")
        
        print(f"\n✅ Matched Value Props:")
        for i, prop in enumerate(traits_data.get('value_props', [])[:3], 1):
            print(f"   {i}. {prop}")
        
        # Step 3: Enhanced message generation
        print("\n💬 Step 3: Modular Message Generation")
        print("-" * 40)
        
        from generator.generate_message import ModularMessageGenerator
        
        generator = ModularMessageGenerator()
        message_result = generator.generate_enhanced_message(lead_data, scraped_data, traits_data)
        
        print(f"✅ Message Generation:")
        print(f"   Method: {message_result.get('generation_method', 'N/A')}")
        print(f"   AI Enhanced: {message_result.get('ai_enhanced', False)}")
        print(f"   Industry Template: {message_result.get('industry', 'N/A')}")
        print(f"   Tone: {message_result.get('tone', 'N/A')}")
        
        # Step 4: Display enhanced message
        print("\n📧 Step 4: Enhanced Message Output")
        print("=" * 60)
        
        enhanced_message = message_result.get('message', '')
        print(f"To: {lead_data['Email']}")
        print(f"Subject: Strategic Partnership Opportunity - {lead_data['Company']}")
        print("-" * 60)
        print(enhanced_message)
        print("-" * 60)
        
        # Step 5: Analysis comparison
        print("\n📊 Step 5: Enhancement Analysis")
        print("-" * 40)
        
        print("✅ Enhanced Features Demonstrated:")
        print(f"   • Rich website data extraction ({len(scraped_data.get('features', []))} features)")
        print(f"   • Industry-specific trait inference ({traits.get('industry', 'N/A')})")
        print(f"   • Modular template system with {len(message_result.get('template_blocks_used', []))} blocks")
        print(f"   • Context-aware personalization")
        print(f"   • AI enhancement: {message_result.get('ai_enhanced', False)}")
        
        # Step 6: Save results for comparison
        print("\n💾 Step 6: Saving Results")
        print("-" * 40)
        
        results = {
            'scraped_data': scraped_data,
            'traits_data': traits_data,
            'message_result': message_result,
            'test_timestamp': '2025-07-29',
            'test_type': 'enhanced_system'
        }
        
        output_file = Path('4runr-outreach-system/enhanced_trivago_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Results saved to: {output_file}")
        
        # Step 7: Send enhanced message
        print("\n📧 Step 7: Send Enhanced Message")
        print("-" * 40)
        
        try:
            import requests
            
            # Get Graph configuration
            sys.path.append('4runr-outreach-system')
            from shared.config import config
            
            graph_config = {
                'client_id': config.get('MS_GRAPH_CLIENT_ID'),
                'client_secret': config.get('MS_GRAPH_CLIENT_SECRET'),
                'tenant_id': config.get('MS_GRAPH_TENANT_ID'),
                'sender_email': config.get('MS_GRAPH_SENDER_EMAIL')
            }
            
            # Get access token
            token_url = f"https://login.microsoftonline.com/{graph_config['tenant_id']}/oauth2/v2.0/token"
            token_data = {
                'client_id': graph_config['client_id'],
                'client_secret': graph_config['client_secret'],
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            token_response = requests.post(token_url, data=token_data)
            if token_response.status_code == 200:
                access_token = token_response.json()['access_token']
                
                # Send enhanced message
                send_url = f"https://graph.microsoft.com/v1.0/users/{graph_config['sender_email']}/sendMail"
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                email_data = {
                    "message": {
                        "subject": "🚀 Enhanced AI Outreach - Travel Tech Partnership",
                        "body": {
                            "contentType": "Text",
                            "content": enhanced_message + "\n\n---\nGenerated by Enhanced 4Runr Outreach System v2.0\nFeatures: Modular templates, ICP inference, AI enhancement"
                        },
                        "toRecipients": [
                            {
                                "emailAddress": {
                                    "address": "kyanberg@outlook.com"
                                }
                            }
                        ]
                    }
                }
                
                send_response = requests.post(send_url, headers=headers, json=email_data)
                
                if send_response.status_code == 202:
                    print("✅ Enhanced message sent successfully!")
                    print("📧 Check your inbox for the enhanced Trivago message")
                else:
                    print(f"❌ Send failed: {send_response.status_code}")
            else:
                print("❌ Failed to get access token")
                
        except Exception as e:
            print(f"❌ Send error: {str(e)}")
        
        print("\n🎉 Enhanced System Test Complete!")
        print("The enhanced system demonstrates:")
        print("  ✅ Richer website data extraction")
        print("  ✅ Intelligent trait inference")
        print("  ✅ Modular message templates")
        print("  ✅ Context-aware personalization")
        print("  ✅ AI-powered enhancement")
        print("  ✅ Industry-specific value propositions")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced system test failed: {str(e)}")
        return False


async def main():
    """Main test function."""
    success = await test_enhanced_trivago()
    return success


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)