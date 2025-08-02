#!/usr/bin/env python3
"""
Campaign Brain Batch Processor

Processes multiple leads through the Campaign Brain system for testing
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent / "4runr-outreach-system"))
sys.path.append(str(Path(__file__).parent))

from campaign_brain import CampaignBrainGraph, CampaignBrainConfig

async def process_batch_leads(batch_file: str, verbose: bool = False):
    """Process a batch of leads through Campaign Brain"""
    
    print("🚀 Campaign Brain - Batch Processing")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load leads from file
    try:
        with open(batch_file, 'r') as f:
            leads = json.load(f)
        print(f"📁 Loaded {len(leads)} leads from {batch_file}")
    except Exception as e:
        print(f"❌ Error loading leads file: {e}")
        return []
    
    # Initialize Campaign Brain
    config = CampaignBrainConfig()
    brain = CampaignBrainGraph(config)
    
    results = []
    
    for i, lead in enumerate(leads, 1):
        print(f"\n{'='*50}")
        print(f"{i}. Processing: {lead['name']} at {lead['company']}")
        print(f"{'='*50}")
        
        try:
            # Convert to Campaign Brain format
            lead_data = {
                "id": f"test_batch_{i:03d}",
                "Name": lead['name'],
                "Company": lead['company'],
                "Title": lead['title'],
                "Email": lead['email'],
                "LinkedIn_URL": lead.get('linkedin_url', ''),
                "Website": lead.get('website', ''),
                
                # Company data (intentionally minimal to trigger fallback)
                "company_data": {
                    "description": lead.get('company_description', ''),
                    "services": lead.get('services', ''),
                    "tone": "Professional",
                    "website_insights": ""
                },
                
                # Scraped content (minimal to trigger fallback)
                "scraped_content": {
                    "homepage_text": "",
                    "about_page": ""
                }
            }
            
            if verbose:
                print(f"   📋 Lead ID: {lead_data['id']}")
                print(f"   📧 Email: {lead_data['Email']}")
                print(f"   🌐 Website: {lead_data.get('Website', 'None')}")
            
            # Process through Campaign Brain
            result = await brain.execute(lead_data)
            
            # Extract results
            success = result.final_status.value == 'approved'
            quality_score = result.overall_quality_score
            fallback_used = getattr(result, 'fallback_mode', False)
            data_quality_score = getattr(result, 'data_quality', {}).get('quality_score', 0)
            fallback_reason = getattr(result, 'data_quality', {}).get('fallback_reason', '')
            
            print(f"   ✅ Status: {result.final_status.value}")
            print(f"   📊 Quality Score: {quality_score:.1f}/100")
            print(f"   🔄 Fallback Mode: {fallback_used}")
            print(f"   📈 Data Quality: {data_quality_score}/10")
            
            if fallback_used:
                print(f"   🎯 Fallback Reason: {fallback_reason}")
            
            # Show generated message
            if result.messages:
                message = result.messages[0]
                print(f"   📝 Message Type: {message.message_type}")
                print(f"   📧 Subject: {message.subject}")
                print(f"   💬 Body Preview: {message.body[:100]}...")
                
                if verbose:
                    print(f"   📄 Full Message:")
                    print(f"      Subject: {message.subject}")
                    print(f"      Body: {message.body}")
            
            # Check if AI message was saved
            ai_message_saved = bool(result.formatted_linkedin_campaign)
            print(f"   💾 AI Message Saved: {ai_message_saved}")
            
            if ai_message_saved and verbose:
                print(f"   📱 AI Message: {result.formatted_linkedin_campaign[:150]}...")
            
            results.append({
                'lead': lead,
                'lead_id': lead_data['id'],
                'success': success,
                'quality_score': quality_score,
                'fallback_used': fallback_used,
                'data_quality_score': data_quality_score,
                'fallback_reason': fallback_reason,
                'ai_message_saved': ai_message_saved,
                'message_type': message.message_type if result.messages else 'none',
                'subject': message.subject if result.messages else '',
                'delivery_method': result.delivery_method,
                'queue_id': result.queue_id
            })
            
        except Exception as e:
            print(f"   ❌ Error processing lead: {str(e)}")
            results.append({
                'lead': lead,
                'lead_id': f"test_batch_{i:03d}",
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 BATCH PROCESSING SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r.get('success'))
    fallback_used_count = sum(1 for r in results if r.get('fallback_used'))
    ai_messages_saved = sum(1 for r in results if r.get('ai_message_saved'))
    
    print(f"✅ Leads processed: {len(results)}")
    print(f"🎯 Successfully approved: {successful}")
    print(f"🔄 Used fallback mode: {fallback_used_count}")
    print(f"💾 AI messages saved: {ai_messages_saved}")
    
    # Detailed results table
    print(f"\n📋 DETAILED RESULTS:")
    print(f"{'Lead':<15} {'Message Type':<12} {'Fallback':<8} {'Quality':<8} {'AI Saved':<9} {'Queue ID':<12}")
    print("-" * 80)
    
    for result in results:
        if result.get('success'):
            lead_name = result['lead']['name']
            message_type = result.get('message_type', 'none')
            fallback = '✅' if result.get('fallback_used') else '❌'
            quality = f"{result.get('quality_score', 0):.1f}"
            ai_saved = '✅' if result.get('ai_message_saved') else '❌'
            queue_id = result.get('queue_id', 'none')[:12] if result.get('queue_id') else 'none'
            
            print(f"{lead_name:<15} {message_type:<12} {fallback:<8} {quality:<8} {ai_saved:<9} {queue_id:<12}")
        else:
            lead_name = result['lead']['name']
            print(f"{lead_name:<15} {'ERROR':<12} {'❌':<8} {'0.0':<8} {'❌':<9} {'none':<12}")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Campaign Brain Batch Processor')
    parser.add_argument('--batch-file', required=True, help='JSON file containing leads to process')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Run batch processing
    results = asyncio.run(process_batch_leads(args.batch_file, args.verbose))
    
    # Return success if all leads were processed successfully
    success_count = sum(1 for r in results if r.get('success'))
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)