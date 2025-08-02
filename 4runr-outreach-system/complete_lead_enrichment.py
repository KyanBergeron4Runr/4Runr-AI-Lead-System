#!/usr/bin/env python3
"""
Complete lead enrichment: Website scraping + AI message generation
"""

import sys
import os
import time
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent / "4runr-agents" / "shared"))

# Import required modules
from shared.airtable_client import get_airtable_client
from ai_message_generator import generate_ai_message
from website_scraper.scraping_engine import ScrapingEngine
from website_scraper.content_analyzer import ContentAnalyzer

def get_leads_for_complete_enrichment(limit=3):
    """Get leads that need website enrichment and AI messages"""
    try:
        client = get_airtable_client()
        
        # Get leads where AI Message is empty and we have company info
        formula = "AND({AI Message} = '', {Company} != '', {Full Name} != '')"
        
        records = client.table.all(
            formula=formula,
            max_records=limit
        )
        
        leads = []
        for record in records:
            fields = record['fields']
            
            lead_data = {
                "id": record['id'],
                "name": fields.get('Full Name', ''),
                "title": fields.get('Title', 'Professional'),
                "company": fields.get('Company', 'Unknown Company'),
                "website": fields.get('Website', ''),
                "linkedin_url": fields.get('LinkedIn URL', ''),
                
                # Current website data
                "company_description": fields.get('Company_Description', ''),
                "website_insights": fields.get('Website_Insights', ''),
                "top_services": fields.get('Top_Services', ''),
                "tone": fields.get('Tone', 'Professional'),
                
                # AI message status
                "ai_message": fields.get('AI Message', ''),
                "response_notes": fields.get('Response Notes', '')
            }
            leads.append(lead_data)
            
        return leads
        
    except Exception as e:
        print(f"Error getting leads from Airtable: {e}")
        return []

def construct_website_url(company_name):
    """Try to construct a website URL from company name"""
    if not company_name or company_name.lower() in ['unknown company', 'unknown']:
        return None
    
    # Clean company name
    clean_name = company_name.lower()
    
    # Remove common business suffixes
    suffixes_to_remove = [' inc', ' ltd', ' llc', ' corp', ' corporation', ' company', ' co', ' &', ' and']
    for suffix in suffixes_to_remove:
        clean_name = clean_name.replace(suffix, '')
    
    # Remove special characters and spaces
    clean_name = ''.join(c for c in clean_name if c.isalnum())
    
    if clean_name:
        return f"https://www.{clean_name}.com"
    
    return None

def enrich_lead_with_website_data(lead):
    """Enrich a single lead with website data"""
    website_url = lead.get('website', '')
    
    if not website_url:
        # Try to construct website from company name
        website_url = construct_website_url(lead.get('company', ''))
        if not website_url:
            return False, "No website URL available"
    
    try:
        print(f"   🌐 Scraping website: {website_url}")
        
        # Initialize scraper and analyzer
        scraper = ScrapingEngine()
        analyzer = ContentAnalyzer()
        
        # Scrape website
        scraped_data = scraper.scrape_website(website_url, lead['id'])
        
        if not scraped_data or scraped_data.get('error'):
            return False, f"Failed to scrape website: {scraped_data.get('error', 'Unknown error')}"
        
        # Check if we got meaningful content
        if not scraped_data.get('raw_content') or len(scraped_data.get('raw_content', '')) < 100:
            return False, "Website content too short or empty"
        
        print(f"   📄 Scraped {len(scraped_data.get('raw_content', ''))} characters")
        
        # Analyze content
        analysis = analyzer.analyze_content(scraped_data, lead['id'])
        
        if not analysis:
            return False, "Failed to analyze website content"
        
        # Update lead with website data
        lead['company_description'] = analysis.get('company_description', '')
        lead['website_insights'] = analysis.get('website_insights', '')
        lead['top_services'] = analysis.get('top_services', '')
        lead['tone'] = analysis.get('tone', 'Professional')
        
        print(f"   ✅ Extracted description: {len(lead['company_description'])} chars")
        print(f"   ✅ Detected tone: {lead['tone']}")
        
        return True, "Website data enriched successfully"
        
    except Exception as e:
        return False, f"Error enriching website data: {str(e)}"

def update_lead_in_airtable(lead_id, updates):
    """Update lead data in Airtable"""
    try:
        client = get_airtable_client()
        client.table.update(lead_id, updates)
        return True
    except Exception as e:
        print(f"   ❌ Error updating Airtable: {e}")
        return False

def main():
    """Main function to enrich leads and generate AI messages"""
    print("🚀 Complete Lead Enrichment: Website Scraping + AI Messages")
    print("=" * 70)
    
    # Get leads that need enrichment
    leads = get_leads_for_complete_enrichment(limit=3)
    
    if not leads:
        print("No leads found that need enrichment and AI messages")
        return
    
    print(f"Found {len(leads)} leads to process")
    
    stats = {
        'processed': 0,
        'website_enriched': 0,
        'ai_generated': 0,
        'website_data_used': 0,
        'errors': 0
    }
    
    for i, lead in enumerate(leads, 1):
        print(f"\n{'='*50}")
        print(f"{i}. Processing: {lead['name']} at {lead['company']}")
        print(f"   ID: {lead['id']}")
        print(f"{'='*50}")
        
        stats['processed'] += 1
        
        # Check if lead already has website data
        has_website_data = (
            lead.get('company_description') and len(lead.get('company_description', '')) > 50
        ) or (
            lead.get('website_insights') and len(lead.get('website_insights', '')) > 50
        )
        
        website_updates = {}
        
        if not has_website_data:
            print(f"   📋 No website data found, attempting to scrape...")
            
            # Try to enrich with website data
            enriched, message = enrich_lead_with_website_data(lead)
            
            if enriched:
                print(f"   ✅ Website data enriched successfully")
                stats['website_enriched'] += 1
                
                # Prepare website data updates
                website_updates = {
                    'Company_Description': lead.get('company_description', ''),
                    'Website_Insights': lead.get('website_insights', ''),
                    'Top_Services': lead.get('top_services', ''),
                    'Tone': lead.get('tone', 'Professional')
                }
                
            else:
                print(f"   ⚠️  Website enrichment failed: {message}")
                # Set response notes to indicate no website data
                website_updates['Response Notes'] = f"No website data available: {message}"
        else:
            print(f"   ✅ Already has website data")
        
        # Generate AI message (will use website data if available)
        print(f"   🤖 Generating AI message...")
        
        try:
            message_result = generate_ai_message(lead, source="Search")
            
            if message_result and message_result.get('message'):
                print(f"   ✅ AI message generated successfully")
                print(f"   📊 Template: {message_result.get('template_id')}")
                print(f"   🎨 Tone: {message_result.get('tone')}")
                print(f"   🌐 Website data used: {message_result.get('website_data_used', False)}")
                
                if message_result.get('website_data_used'):
                    stats['website_data_used'] += 1
                    print(f"   📄 Data sources: {', '.join(message_result.get('website_data_sources', []))}")
                
                # Show message preview
                message_preview = message_result['message'][:150] + "..." if len(message_result['message']) > 150 else message_result['message']
                print(f"   💬 Message Preview:")
                print(f"      {message_preview}")
                
                # Add AI message to updates
                website_updates['AI Message'] = message_result['message']
                stats['ai_generated'] += 1
                
            else:
                print(f"   ❌ Failed to generate AI message")
                stats['errors'] += 1
                
        except Exception as e:
            print(f"   ❌ Error generating AI message: {str(e)}")
            stats['errors'] += 1
        
        # Update Airtable with all changes
        if website_updates:
            print(f"   💾 Updating Airtable...")
            update_success = update_lead_in_airtable(lead['id'], website_updates)
            
            if update_success:
                print(f"   ✅ Airtable updated successfully")
            else:
                print(f"   ❌ Failed to update Airtable")
                stats['errors'] += 1
        
        # Small delay between leads to be respectful
        if i < len(leads):
            print(f"   ⏳ Waiting 3 seconds before next lead...")
            time.sleep(3)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 COMPLETE ENRICHMENT SUMMARY")
    print("=" * 70)
    print(f"✅ Leads processed: {stats['processed']}")
    print(f"🌐 Website data enriched: {stats['website_enriched']}")
    print(f"🤖 AI messages generated: {stats['ai_generated']}")
    print(f"📄 Messages using website data: {stats['website_data_used']}")
    print(f"❌ Errors: {stats['errors']}")
    
    success_rate = (stats['ai_generated'] / stats['processed'] * 100) if stats['processed'] > 0 else 0
    website_usage_rate = (stats['website_data_used'] / stats['ai_generated'] * 100) if stats['ai_generated'] > 0 else 0
    
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    print(f"🌐 Website Data Usage: {website_usage_rate:.1f}%")
    
    if stats['ai_generated'] > 0:
        print(f"\n🎉 Successfully processed {stats['ai_generated']} leads!")
        print("   ✅ Check your Airtable 'AI Message' field for the results")
        print("   ✅ Website data has been added to Company_Description and other fields")
        print("   ✅ Messages are ready for manual sending from your personal account")

if __name__ == "__main__":
    main()