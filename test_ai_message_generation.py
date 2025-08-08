#!/usr/bin/env python3
"""
Test script to pull leads from Airtable and generate AI messages using website data
"""

import sys
import os
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent / "4runr-outreach-system"))
sys.path.append(str(Path(__file__).parent / "4runr-agents"))

try:
    from shared.airtable_client import get_airtable_client
except ImportError:
    # Try alternative path
    sys.path.append(str(Path(__file__).parent / "4runr-outreach-system" / "shared"))
    from airtable_client import get_airtable_client

try:
    from shared.ai_message_generator import generate_ai_message
except ImportError:
    # Try alternative path
    sys.path.append(str(Path(__file__).parent / "4runr-agents" / "shared"))
    from ai_message_generator import generate_ai_message

def get_leads_without_ai_messages(limit=10):
    """Get leads where AI Message field is empty"""
    try:
        client = get_airtable_client()
        
        # Get leads where AI Message is empty
        formula = "AND({AI Message} = '', {Full Name} != '')"
        
        records = client.table.all(
            formula=formula,
            max_records=limit
        )
        
        leads = []
        for record in records:
            fields = record['fields']
            
            # Convert Airtable record to lead format
            lead_data = {
                "id": record['id'],
                "name": fields.get('Full Name', ''),
                "full_name": fields.get('Full Name', ''),
                "title": fields.get('Job Title', 'Professional'),
                "company": fields.get('Company', 'Unknown Company'),
                
                # Website data fields (using Extra info field for now)
                "company_description": fields.get('Extra info', ''),
                "website_insights": fields.get('Extra info', ''),
                "top_services": fields.get('Extra info', ''),
                "tone": fields.get('Tone', 'Professional'),
                
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

def should_generate_ai_message(lead):
    """Check if we should generate an AI message for this lead"""
    # Check if response notes indicate no website
    response_notes = lead.get('response_notes', '').lower()
    exclusion_patterns = ['no website', 'website not available', 'site down', 'under construction']
    
    if any(pattern in response_notes for pattern in exclusion_patterns):
        return False, f"Excluded due to response notes: {response_notes}"
    
    # Check if we have some website data
    has_description = lead.get('company_description', '') and len(lead.get('company_description', '')) > 50
    has_insights = lead.get('website_insights', '') and len(lead.get('website_insights', '')) > 50
    
    if not has_description and not has_insights:
        return False, "No sufficient website data available"
    
    return True, "Eligible for AI message generation"

def update_ai_message_in_airtable(lead_id, message, metadata):
    """Update the AI Message field in Airtable"""
    try:
        client = get_airtable_client()
        
        # Prepare the update
        update_data = {
            'AI Message': message
        }
        
        # Update the record
        client.table.update(lead_id, update_data)
        return True
        
    except Exception as e:
        print(f"Error updating Airtable for lead {lead_id}: {e}")
        return False

def main():
    """Main function to test AI message generation"""
    print("🚀 Testing AI Message Generation with Website Data")
    print("=" * 60)
    
    # Get leads without AI messages
    leads = get_leads_without_ai_messages(limit=10)
    
    if not leads:
        print("No leads found without AI messages")
        return
    
    print(f"Found {len(leads)} leads without AI messages")
    
    stats = {
        'processed': 0,
        'generated': 0,
        'excluded': 0,
        'errors': 0,
        'website_data_used': 0
    }
    
    for i, lead in enumerate(leads, 1):
        print(f"\n{i}. Processing: {lead['name']} at {lead['company']}")
        print(f"   ID: {lead['id']}")
        
        # Check if we should generate AI message
        should_generate, reason = should_generate_ai_message(lead)
        stats['processed'] += 1
        
        if not should_generate:
            print(f"   ⏭️  Skipped: {reason}")
            stats['excluded'] += 1
            continue
        
        try:
            # Generate AI message
            message_result = generate_ai_message(lead, source="Search")
            
            if message_result.get('message'):
                print(f"   ✅ Generated AI message")
                print(f"   📊 Template: {message_result.get('template_id')}")
                print(f"   🎨 Tone: {message_result.get('tone')}")
                print(f"   🌐 Website data used: {message_result.get('website_data_used', False)}")
                
                if message_result.get('website_data_sources'):
                    print(f"   📄 Data sources: {', '.join(message_result.get('website_data_sources', []))}")
                    stats['website_data_used'] += 1
                
                # Show first 100 characters of the message
                message_preview = message_result['message'][:100] + "..." if len(message_result['message']) > 100 else message_result['message']
                print(f"   💬 Message: {message_preview}")
                
                # Update Airtable
                update_success = update_ai_message_in_airtable(
                    lead['id'], 
                    message_result['message'], 
                    message_result
                )
                
                if update_success:
                    print(f"   💾 Updated Airtable successfully")
                    stats['generated'] += 1
                else:
                    print(f"   ❌ Failed to update Airtable")
                    stats['errors'] += 1
            else:
                print(f"   ❌ Failed to generate message")
                stats['errors'] += 1
                
        except Exception as e:
            print(f"   ❌ Error processing lead: {str(e)}")
            stats['errors'] += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    print(f"✅ Leads processed: {stats['processed']}")
    print(f"📝 AI messages generated: {stats['generated']}")
    print(f"🌐 Used website data: {stats['website_data_used']}")
    print(f"⏭️  Excluded (no website): {stats['excluded']}")
    print(f"❌ Errors: {stats['errors']}")
    
    if stats['generated'] > 0:
        print(f"\n🎉 Successfully generated {stats['generated']} AI messages!")
        print("   Check your Airtable 'AI Message' field for the results")

if __name__ == "__main__":
    main()