#!/usr/bin/env python3
"""
Process leads with empty AI Message fields through Campaign Brain
"""

import asyncio
import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent / "4runr-outreach-system"))
sys.path.append(str(Path(__file__).parent))

from shared.airtable_client import get_airtable_client
from campaign_brain import CampaignBrainGraph, CampaignBrainConfig

def get_leads_needing_ai_messages(limit=10):
    """Get leads where AI Message field is empty"""
    try:
        client = get_airtable_client()
        
        # Get leads where AI Message is empty (ALL leads, not just LinkedIn)
        formula = "{AI Message} = ''"
        
        records = client.table.all(
            formula=formula,
            max_records=limit
        )
        
        # Convert generator to list to avoid subscriptable errors
        records_list = list(records)
        
        leads = []
        for record in records_list:
            fields = record['fields']
            
            # Convert Airtable record to Campaign Brain format
            lead_data = {
                "id": record['id'],
                "Name": fields.get('Full Name', ''),
                "LinkedIn_URL": fields.get('LinkedIn URL', ''),
                "Email": fields.get('Email'),  # May be None
                "Company": fields.get('Company', fields.get('Full Name', 'Unknown Company')),
                "Title": fields.get('Title', 'Professional'),
                "company_data": {
                    "description": fields.get('Company_Description', 'Professional services and consulting company'),
                    "services": fields.get('Services', 'Business consulting, professional services, and strategic advisory'), 
                    "tone": "Professional"
                },
                "scraped_content": {
                    "homepage_text": fields.get('Homepage_Content', f"Professional services company focused on delivering strategic value to clients through innovative solutions and expert consulting."),
                    "about_page": fields.get('About_Content', f"Established professional services firm with expertise in business strategy, operations, and growth acceleration.")
                }
            }
            leads.append(lead_data)
            
        return leads
        
    except Exception as e:
        print(f"Error getting leads from Airtable: {e}")
        return []

async def process_lead_through_campaign_brain(lead_data):
    """Process a single lead through the Campaign Brain"""
    try:
        config = CampaignBrainConfig()
        brain = CampaignBrainGraph(config)
        
        print(f"\n🧠 Processing: {lead_data['Name']} (ID: {lead_data['id']})")
        print(f"   LinkedIn: {lead_data.get('LinkedIn_URL', 'None')}")
        print(f"   Email: {lead_data.get('Email', 'None')}")
        
        result = await brain.execute(lead_data)
        
        print(f"   ✅ Status: {result.final_status.value}")
        print(f"   📊 Quality Score: {result.overall_quality_score:.1f}/100")
        
        if result.final_status.value == 'approved':
            if result.delivery_method == 'dual_delivery':
                print(f"   📱 AI Message created + 📧 Email queued")
                return {
                    'success': True,
                    'method': 'dual',
                    'campaign': result.formatted_linkedin_campaign,
                    'queue_id': result.queue_id
                }
            elif result.delivery_method == 'manual_only':
                print(f"   📱 AI Message created for manual sending")
                return {
                    'success': True,
                    'method': 'manual',
                    'campaign': result.formatted_linkedin_campaign
                }
        else:
            print(f"   ⚠️ Campaign needs manual review: {result.status_reason}")
            return {
                'success': False,
                'reason': result.status_reason
            }
            
    except Exception as e:
        print(f"   ❌ Error processing lead: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def main():
    """Main processing function"""
    print("🚀 Campaign Brain - Processing Leads with Empty AI Messages")
    print("=" * 60)
    
    # Get leads needing AI messages
    leads = get_leads_needing_ai_messages(limit=5)
    
    if not leads:
        print("No leads found with empty AI Message fields")
        return
    
    print(f"Found {len(leads)} leads needing AI messages:")
    
    # Process each lead
    results = []
    for lead in leads:
        result = await process_lead_through_campaign_brain(lead)
        results.append({
            'lead': lead,
            'result': result
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['result']['success'])
    dual_campaigns = sum(1 for r in results if r['result'].get('method') == 'dual')
    manual_campaigns = sum(1 for r in results if r['result'].get('method') == 'manual')
    
    print(f"✅ Successfully processed: {successful}/{len(results)}")
    print(f"📱📧 Dual delivery (AI Message + Email): {dual_campaigns}")
    print(f"📱 Manual only (AI Message): {manual_campaigns}")
    print(f"⚠️ Manual review needed: {len(results) - successful}")
    
    # Show AI Messages generated
    if successful > 0:
        print(f"\n📱 AI Messages saved to Airtable 'AI Message' field")
        print("   Ready for manual sending via your account!")
        print(f"   Also saved as backup files in: 4runr-brain/linkedin_campaigns/")

if __name__ == "__main__":
    asyncio.run(main())