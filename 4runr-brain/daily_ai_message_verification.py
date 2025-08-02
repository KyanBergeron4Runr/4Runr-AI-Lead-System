#!/usr/bin/env python3
"""
Daily AI Message Verification Agent

This script runs daily to check for leads missing AI messages and generates them
using website data when available.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent / "4runr-outreach-system"))
sys.path.append(str(Path(__file__).parent))

from shared.airtable_client import get_airtable_client
from campaign_brain import CampaignBrainGraph, CampaignBrainConfig

class DailyVerificationAgent:
    def __init__(self):
        self.airtable_client = get_airtable_client()
        self.config = CampaignBrainConfig()
        self.brain = CampaignBrainGraph(self.config)
    
    def get_leads_needing_ai_messages(self, limit=10):
        """Get leads where AI Message field is empty"""
        try:
            # Get leads where AI Message is empty (ALL leads, not just LinkedIn)
            formula = "AND({AI Message} = '', {Full Name} != '', {Company} != '')"
            
            records = self.airtable_client.table.all(
                formula=formula,
                max_records=limit
            )
            
            leads = []
            for record in records:
                fields = record['fields']
                
                # Convert Airtable record to Campaign Brain format
                lead_data = {
                    "id": record['id'],
                    "Name": fields.get('Full Name', ''),
                    "LinkedIn_URL": fields.get('LinkedIn URL', ''),
                    "Email": fields.get('Email'),  # May be None
                    "Company": fields.get('Company', fields.get('Full Name', 'Unknown Company')),
                    "Title": fields.get('Title', 'Professional'),
                    "Website": fields.get('Website', ''),
                    
                    # Website data for personalization
                    "company_data": {
                        "description": fields.get('Company_Description', ''),
                        "services": fields.get('Top_Services', ''), 
                        "tone": fields.get('Tone', 'Professional'),
                        "website_insights": fields.get('Website_Insights', '')
                    },
                    
                    # Response notes for exclusion checking
                    "response_notes": fields.get('Response Notes', ''),
                    
                    # Current AI message status
                    "ai_message": fields.get('AI Message', '')
                }
                leads.append(lead_data)
                
            return leads
            
        except Exception as e:
            print(f"Error getting leads from Airtable: {e}")
            return []
    
    def should_generate_ai_message(self, lead):
        """Determine if lead is eligible for AI message generation"""
        # Check response notes for exclusions
        response_notes = lead.get('response_notes', '').lower()
        exclusion_patterns = [
            'no website',
            'website not available', 
            'site down',
            'under construction',
            'coming soon'
        ]
        
        if any(pattern in response_notes for pattern in exclusion_patterns):
            return False, f"Excluded due to response notes: {response_notes}"
        
        # Check if we have basic lead information
        if not lead.get('Name') or not lead.get('Company'):
            return False, "Missing basic lead information"
        
        return True, "Eligible for AI message generation"
    
    def has_website_data(self, lead):
        """Check if lead has sufficient website data for enhanced personalization"""
        company_data = lead.get('company_data', {})
        
        description = company_data.get('description', '')
        insights = company_data.get('website_insights', '')
        
        # Check for meaningful website data
        has_description = description and len(description) > 50
        has_insights = insights and len(insights) > 50
        
        # Check if it's not just generic fallback text
        if has_description:
            generic_phrases = [
                'professional services and consulting company',
                'business consulting, professional services',
                'unable to extract company information'
            ]
            if any(phrase in description.lower() for phrase in generic_phrases) and len(description) < 100:
                has_description = False
        
        return has_description or has_insights
    
    async def process_lead_for_ai_message(self, lead_data):
        """Process a single lead for AI message generation"""
        try:
            lead_id = lead_data.get('id')
            lead_name = lead_data.get('Name', 'Unknown')
            
            print(f"\n🧠 Processing: {lead_name} (ID: {lead_id})")
            print(f"   Company: {lead_data.get('Company', 'Unknown')}")
            print(f"   LinkedIn: {lead_data.get('LinkedIn_URL', 'None')}")
            print(f"   Email: {lead_data.get('Email', 'None')}")
            
            # Check if lead has website data
            has_website = self.has_website_data(lead_data)
            print(f"   Website data available: {has_website}")
            
            # Process through Campaign Brain
            result = await self.brain.execute(lead_data)
            
            print(f"   ✅ Status: {result.final_status.value}")
            print(f"   📊 Quality Score: {result.overall_quality_score:.1f}/100")
            
            if result.final_status.value == 'approved':
                if result.delivery_method == 'dual_delivery':
                    print(f"   📱 AI Message created + 📧 Email queued")
                    return {
                        'success': True,
                        'method': 'dual',
                        'campaign': result.formatted_linkedin_campaign,
                        'queue_id': result.queue_id,
                        'website_data_used': has_website
                    }
                elif result.delivery_method == 'manual_only':
                    print(f"   📱 AI Message created for manual sending")
                    return {
                        'success': True,
                        'method': 'manual',
                        'campaign': result.formatted_linkedin_campaign,
                        'website_data_used': has_website
                    }
            else:
                print(f"   ⚠️ Campaign needs manual review: {result.status_reason}")
                return {
                    'success': False,
                    'reason': result.status_reason,
                    'website_data_used': has_website
                }
                
        except Exception as e:
            print(f"   ❌ Error processing lead: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'website_data_used': False
            }
    
    async def run_daily_verification(self, limit=10):
        """Run daily verification to find and process leads needing AI messages"""
        print("🚀 Daily AI Message Verification")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get leads needing AI messages
        leads = self.get_leads_needing_ai_messages(limit=limit)
        
        if not leads:
            print("No leads found with empty AI Message fields")
            return {
                'processed': 0,
                'successful': 0,
                'excluded': 0,
                'errors': 0,
                'website_data_used': 0
            }
        
        print(f"Found {len(leads)} leads needing AI messages:")
        
        stats = {
            'processed': 0,
            'successful': 0,
            'excluded': 0,
            'errors': 0,
            'website_data_used': 0
        }
        
        # Process each lead
        for lead in leads:
            # Check if we should generate AI message
            should_generate, reason = self.should_generate_ai_message(lead)
            stats['processed'] += 1
            
            if not should_generate:
                print(f"\n⏭️  Skipping {lead.get('Name', 'Unknown')}: {reason}")
                stats['excluded'] += 1
                continue
            
            # Process the lead
            result = await self.process_lead_for_ai_message(lead)
            
            if result and result.get('success'):
                stats['successful'] += 1
                if result.get('website_data_used'):
                    stats['website_data_used'] += 1
            else:
                stats['errors'] += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DAILY VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"✅ Leads processed: {stats['processed']}")
        print(f"🤖 AI messages generated: {stats['successful']}")
        print(f"🌐 Used website data: {stats['website_data_used']}")
        print(f"⏭️  Excluded (no website/other): {stats['excluded']}")
        print(f"❌ Errors: {stats['errors']}")
        
        success_rate = (stats['successful'] / stats['processed'] * 100) if stats['processed'] > 0 else 0
        website_usage_rate = (stats['website_data_used'] / stats['successful'] * 100) if stats['successful'] > 0 else 0
        
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        print(f"🌐 Website Data Usage: {website_usage_rate:.1f}%")
        
        if stats['successful'] > 0:
            print(f"\n📱 AI Messages saved to Airtable 'AI Message' field")
            print("   Ready for manual sending via your account!")
            print(f"   Also saved as backup files in: 4runr-brain/linkedin_campaigns/")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return stats

async def main():
    """Main entry point for daily verification"""
    agent = DailyVerificationAgent()
    
    # Run verification with limit of 5 for testing
    stats = await agent.run_daily_verification(limit=5)
    
    # Return success if we processed any leads
    return stats['processed'] > 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)