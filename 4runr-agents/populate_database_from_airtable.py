#!/usr/bin/env python3
"""
Populate Database from Airtable Leads

This script imports the provided Airtable leads data into the database
and sets up proper enrichment data and status tracking.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

from database.lead_database import get_lead_database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your Airtable leads data
AIRTABLE_LEADS_DATA = [
    {
        "name": "Pascal Jarry",
        "linkedin_url": "https://ca.linkedin.com/in/pascaljarry",
        "title": "Founder and CEO",
        "company": "Yapla",
        "email": "pascaljarry@membogo.com",
        "status": "Search",
        "enrichment_data": "Website: www.yapla.com | Found emails: pascaljarry@membogo.com, pascaljarry@yapla.com, dpo@yapla.com | Enriched: success | Methods: website_found, email_search",
        "date": "7/29/2025"
    },
    {
        "name": "Jon Ruby",
        "linkedin_url": "https://ca.linkedin.com/in/rubyjon",
        "title": "CEO",
        "company": "Jonar",
        "email": "jon.ruby@www.jonar.com",
        "status": "Search",
        "custom_message": "Hi Jon, Quick question for you as Professional at Jonar: Are you currently looking for ways to optimize resource allocation? We've got some interesting results to share.",
        "enrichment_data": "Website: www.jonar.com | Email patterns: jon.ruby@www.jonar.com, jon@www.jonar.com, ruby@www.jonar.com | Enriched: success | Methods: website_found, pattern_generated",
        "date": "7/29/2025"
    },
    {
        "name": "Claude Lemay",
        "linkedin_url": "https://ca.linkedin.com/in/claude-lemay-10808213",
        "title": "President and CEO",
        "company": "Claude Lemay & Partners",
        "email": "claude.lemay@lemay.com",
        "status": "Search",
        "custom_message": "Hi Claude, Quick question for you as Professional at Claude Lemay & Partners: Are you currently looking for ways to streamline workflows? We've got some interesting results to share.",
        "enrichment_data": "Website: lemay.com | Email patterns: claude.lemay@lemay.com, claude@lemay.com, lemay@lemay.com | Enriched: success | Methods: website_found, pattern_generated",
        "date": "7/29/2025"
    },
    {
        "name": "Elie Wahnoun",
        "linkedin_url": "https://www.linkedin.com/in/eliewahnoun",
        "title": "Founder and CEO",
        "company": "Courimo",
        "email": "wahnounelie@gmail.com",
        "status": "Search",
        "enrichment_data": "Website: courimo.com | Found emails: wahnounelie@gmail.com, elie@courimo.com | Enriched: success | Methods: website_found, email_search",
        "date": "7/29/2025"
    },
    {
        "name": "Randal Tucker",
        "linkedin_url": "https://ca.linkedin.com/in/randal-tucker-31bbb618",
        "title": "CEO & President",
        "company": "SFM",
        "email": "randal.tucker@www.sfm.ca",
        "status": "Search",
        "enrichment_data": "Website: www.sfm.ca | Email patterns: randal.tucker@www.sfm.ca, randal@www.sfm.ca, tucker@www.sfm.ca | Enriched: success | Methods: website_found, pattern_generated",
        "date": "7/29/2025"
    },
    {
        "name": "Renée Touzin",
        "linkedin_url": "https://ca.linkedin.com/in/ren%C3%A9e-touzin-a0b00267",
        "title": "President and CEO",
        "company": "Giro · Specialties:",
        "email": "renee.touzin@giro.ca",
        "status": "checked",
        "custom_message": "Hi Renée, Quick question for you as Professional at Giro · Specialties:: Are you currently looking for ways to optimize resource allocation? We've got some interesting results to share.",
        "enrichment_data": "🔧 Enriched via: comprehensive_serpapi_enricher🎯 Lead Quality: High (Ready for engagement)",
        "date": "7/31/2025"
    },
    {
        "name": "Yves-Gabriel Leboeuf",
        "linkedin_url": "https://ca.linkedin.com/in/ygl",
        "title": "Product Manager at Video Tutorials",
        "company": "Teck Resources Limited",
        "email": "yvesgabriel.leboeuf@teck.com",
        "status": "checked",
        "enrichment_data": "🌐 Website: teck.com🔧 Enriched via: comprehensive_serpapi_enricher🎯 Lead Quality: High (Ready for engagement)",
        "date": "7/31/2025"
    },
    {
        "name": "Stéphane Paquet",
        "linkedin_url": "https://ca.linkedin.com/in/st%C3%A9phane-paquet-621b022b",
        "title": "CEO",
        "company": "",
        "email": "",
        "status": "checked",
        "enrichment_data": "🔧 Enriched via: comprehensive_serpapi_enricher",
        "date": "7/31/2025"
    },
    {
        "name": "Stephane Rouleau",
        "linkedin_url": "https://ca.linkedin.com/in/srouleau",
        "title": "Director",
        "company": "Axxess International Inc",
        "email": "stephane.rouleau@axxessintl.com",
        "status": "checked",
        "custom_message": "Hi Stephane, Quick question for you as Professional at Axxess International Inc: Are you currently looking for ways to optimize resource allocation? We've got some interesting results to share.",
        "enrichment_data": "🌐 Website: axxessintl.com🔧 Enriched via: comprehensive_serpapi_enricher🎯 Lead Quality: High (Ready for engagement)",
        "date": "7/31/2025"
    },
    {
        "name": "Maxime Leclair",
        "linkedin_url": "https://ca.linkedin.com/in/maxime-leclair",
        "title": "Chief Executive Officer at Maximize IT",
        "company": "Maximize It. Maximize",
        "email": "",
        "status": "checked",
        "custom_message": "Hi Maxime, I noticed your work as Professional at Maximize It. Maximize. I'd love to connect and share how we're helping industry leaders streamline their operations. Would you be open to a brief conversation?",
        "enrichment_data": "🔧 Enriched via: comprehensive_serpapi_enricher",
        "date": "7/31/2025"
    }
]

def parse_enrichment_data(enrichment_text: str) -> dict:
    """Parse enrichment data text into structured data"""
    enrichment_info = {
        'website': '',
        'emails_found': [],
        'enrichment_method': '',
        'quality': '',
        'status': 'enriched'
    }
    
    if not enrichment_text:
        return enrichment_info
    
    # Extract website
    if 'Website:' in enrichment_text:
        website_part = enrichment_text.split('Website:')[1].split('|')[0].strip()
        enrichment_info['website'] = website_part
    
    # Extract found emails
    if 'Found emails:' in enrichment_text:
        emails_part = enrichment_text.split('Found emails:')[1].split('|')[0].strip()
        enrichment_info['emails_found'] = [email.strip() for email in emails_part.split(',')]
    
    # Extract enrichment method
    if 'Methods:' in enrichment_text:
        methods_part = enrichment_text.split('Methods:')[1].strip()
        enrichment_info['enrichment_method'] = methods_part
    elif 'Enriched via:' in enrichment_text:
        method_part = enrichment_text.split('Enriched via:')[1].split('🎯')[0].strip()
        enrichment_info['enrichment_method'] = method_part
    
    # Extract quality
    if 'Lead Quality:' in enrichment_text:
        quality_part = enrichment_text.split('Lead Quality:')[1].strip()
        enrichment_info['quality'] = quality_part
    
    return enrichment_info

def determine_lead_status(lead_data: dict) -> str:
    """Determine the appropriate status for the lead"""
    enrichment_data = lead_data.get('enrichment_data', '')
    
    # If it has "Ready for engagement" or good enrichment data, mark as ready
    if 'Ready for engagement' in enrichment_data:
        return 'Ready for Outreach'
    elif 'Enriched: success' in enrichment_data:
        return 'Ready for Outreach'
    elif lead_data.get('custom_message'):
        return 'Ready for Outreach'
    elif lead_data.get('email'):
        return 'Enriched'
    else:
        return 'new'

def populate_database():
    """Populate the database with Airtable leads data"""
    
    logger.info("Starting database population from Airtable leads data")
    
    try:
        # Get database connection
        db = get_lead_database()
        
        # Get current stats
        initial_stats = db.get_database_stats()
        logger.info(f"Initial database stats: {initial_stats.get('total_leads', 0)} leads")
        
        added_count = 0
        updated_count = 0
        error_count = 0
        
        for lead_data in AIRTABLE_LEADS_DATA:
            try:
                # Parse enrichment data
                enrichment_info = parse_enrichment_data(lead_data.get('enrichment_data', ''))
                
                # Determine status
                status = determine_lead_status(lead_data)
                
                # Prepare lead data for database
                db_lead_data = {
                    'full_name': lead_data['name'],
                    'linkedin_url': lead_data.get('linkedin_url'),
                    'title': lead_data.get('title', ''),
                    'company': lead_data.get('company', ''),
                    'email': lead_data.get('email', ''),
                    'status': status,
                    'enriched': bool(lead_data.get('enrichment_data')),
                    'needs_enrichment': not bool(lead_data.get('enrichment_data')),
                    'verified': bool(lead_data.get('email')),
                    'source': 'airtable_import',
                    'raw_data': {
                        'original_status': lead_data.get('status'),
                        'custom_message': lead_data.get('custom_message', ''),
                        'enrichment_data': lead_data.get('enrichment_data', ''),
                        'import_date': datetime.now().isoformat(),
                        'airtable_date': lead_data.get('date'),
                        'enrichment_info': enrichment_info,
                        'website': enrichment_info.get('website', ''),
                        'emails_found': enrichment_info.get('emails_found', []),
                        'enrichment_method': enrichment_info.get('enrichment_method', ''),
                        'quality_assessment': enrichment_info.get('quality', '')
                    }
                }
                
                # Add to database (will handle duplicates automatically)
                lead_id = db.add_lead(db_lead_data)
                
                if lead_id:
                    # Check if this was a new lead or update
                    existing_lead = db.get_lead(lead_id)
                    if existing_lead and existing_lead.get('created_at') == existing_lead.get('updated_at'):
                        added_count += 1
                        logger.info(f"✅ Added new lead: {lead_data['name']} (ID: {lead_id[:8]}...)")
                    else:
                        updated_count += 1
                        logger.info(f"🔄 Updated existing lead: {lead_data['name']} (ID: {lead_id[:8]}...)")
                else:
                    error_count += 1
                    logger.error(f"❌ Failed to add lead: {lead_data['name']}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing lead {lead_data.get('name', 'Unknown')}: {str(e)}")
        
        # Get final stats
        final_stats = db.get_database_stats()
        
        # Summary
        logger.info("=" * 50)
        logger.info("DATABASE POPULATION COMPLETE")
        logger.info("=" * 50)
        logger.info(f"📊 Initial leads: {initial_stats.get('total_leads', 0)}")
        logger.info(f"📊 Final leads: {final_stats.get('total_leads', 0)}")
        logger.info(f"✅ New leads added: {added_count}")
        logger.info(f"🔄 Existing leads updated: {updated_count}")
        logger.info(f"❌ Errors: {error_count}")
        
        # Show status breakdown
        status_counts = final_stats.get('status_counts', {})
        logger.info("\n📈 Status Breakdown:")
        for status, count in status_counts.items():
            logger.info(f"   {status}: {count}")
        
        # Show leads ready for campaign brain
        ready_leads = db.search_leads({'status': 'Ready for Outreach'})
        logger.info(f"\n🎯 Leads ready for Campaign Brain: {len(ready_leads)}")
        for lead in ready_leads:
            logger.info(f"   - {lead.get('full_name')} at {lead.get('company')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database population failed: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Populating database with Airtable leads data...")
    
    success = populate_database()
    
    if success:
        print("\n✅ Database population completed successfully!")
        print("🎯 You can now run the campaign brain to process leads")
        print("💡 Use: python serve_campaign_brain.py --batch-size 5 --dry-run")
    else:
        print("\n❌ Database population failed!")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())