#!/usr/bin/env python3
"""
Run Field Enrichment

This script uses the enhanced enrichment systems to fill missing fields
in existing leads across the JSON files and databases.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('field_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('field-enrichment')

def run_enrichment_on_json_files():
    """Run enrichment on JSON lead files"""
    logger.info("🚀 Starting field enrichment on JSON files")
    
    shared_path = Path("4runr-agents/shared")
    files_to_process = ["leads.json", "enriched_leads.json", "scraped_leads.json"]
    
    total_processed = 0
    total_enriched = 0
    
    for filename in files_to_process:
        file_path = shared_path / filename
        if not file_path.exists():
            logger.info(f"⚠️ File not found: {file_path}")
            continue
            
        logger.info(f"📄 Processing: {filename}")
        
        try:
            # Read current data
            with open(file_path, 'r', encoding='utf-8') as f:
                leads = json.load(f)
            
            if not isinstance(leads, list):
                logger.warning(f"⚠️ {filename} is not a list, skipping")
                continue
            
            # Create backup
            backup_path = file_path.with_suffix('.backup.json')
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            
            # Process each lead
            for i, lead in enumerate(leads):
                if not isinstance(lead, dict):
                    continue
                
                try:
                    enriched_fields = enrich_lead_fields(lead)
                    if enriched_fields:
                        total_enriched += 1
                        logger.info(f"   ✅ Enriched lead {i+1}: {lead.get('name', 'Unknown')} - Added {len(enriched_fields)} fields")
                    
                    total_processed += 1
                    
                except Exception as e:
                    logger.error(f"   ❌ Error enriching lead {i+1}: {e}")
            
            # Save updated data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Completed {filename}: {total_enriched} leads enriched")
            
        except Exception as e:
            logger.error(f"❌ Error processing {filename}: {e}")
    
    logger.info(f"🎉 JSON enrichment complete: {total_enriched}/{total_processed} leads enriched")
    return total_processed, total_enriched

def enrich_lead_fields(lead: Dict[str, Any]) -> List[str]:
    """Enrich missing fields for a single lead"""
    enriched_fields = []
    
    # 1. LinkedIn URL
    if is_field_missing(lead.get('linkedin_url')):
        linkedin_url = generate_linkedin_url(lead)
        if linkedin_url:
            lead['linkedin_url'] = linkedin_url
            enriched_fields.append('linkedin_url')
    
    # 2. Location
    if is_field_missing(lead.get('location')):
        lead['location'] = 'North America'
        enriched_fields.append('location')
    
    # 3. Industry
    if is_field_missing(lead.get('industry')):
        industry = infer_industry(lead)
        if industry:
            lead['industry'] = industry
            enriched_fields.append('industry')
    
    # 4. Company Size
    if is_field_missing(lead.get('company_size')):
        company_size = infer_company_size(lead)
        if company_size:
            lead['company_size'] = company_size
            enriched_fields.append('company_size')
    
    # 5. Business Type
    if is_field_missing(lead.get('Business_Type')):
        business_type = infer_business_type(lead)
        if business_type:
            lead['Business_Type'] = business_type
            enriched_fields.append('Business_Type')
    
    # 6. Business Traits
    if is_field_missing(lead.get('Business_Traits')):
        business_traits = infer_business_traits(lead)
        if business_traits:
            lead['Business_Traits'] = business_traits
            enriched_fields.append('Business_Traits')
    
    # 7. Pain Points
    if is_field_missing(lead.get('Pain_Points')):
        pain_points = infer_pain_points(lead)
        if pain_points:
            lead['Pain_Points'] = pain_points
            enriched_fields.append('Pain_Points')
    
    # 8. Website fields
    if is_field_missing(lead.get('website')) and is_field_missing(lead.get('company_website')):
        website = generate_company_website(lead)
        if website:
            lead['website'] = website
            lead['company_website'] = website
            enriched_fields.extend(['website', 'company_website'])
    
    # 9. Email status fields
    if lead.get('email') and is_field_missing(lead.get('email_status')):
        lead['email_status'] = 'pattern_generated'
        lead['email_confidence'] = 40
        lead['bounce_risk'] = 'medium'
        enriched_fields.extend(['email_status', 'email_confidence', 'bounce_risk'])
    
    # 10. Engagement readiness
    if is_field_missing(lead.get('ready_for_engagement')):
        lead['ready_for_engagement'] = True
        enriched_fields.append('ready_for_engagement')
    
    if is_field_missing(lead.get('enriched')):
        lead['enriched'] = True
        enriched_fields.append('enriched')
    
    if is_field_missing(lead.get('status')):
        lead['status'] = 'enriched'
        enriched_fields.append('status')
    
    return enriched_fields

def is_field_missing(value) -> bool:
    """Check if a field value is missing or empty"""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, list) and len(value) == 1 and value[0] == "":
        return True
    return False

def generate_linkedin_url(lead: Dict[str, Any]) -> str:
    """Generate LinkedIn URL from lead name"""
    name = lead.get('name') or lead.get('full_name', '')
    if not name:
        return None
    
    name_parts = name.lower().split()
    if len(name_parts) >= 2:
        linkedin_slug = f"{name_parts[0]}-{name_parts[-1]}"
        return f"https://www.linkedin.com/in/{linkedin_slug}/"
    
    return None

def infer_industry(lead: Dict[str, Any]) -> str:
    """Infer industry from company and title"""
    company = lead.get('company', '').lower()
    title = lead.get('title', '').lower()
    
    industry_keywords = {
        'Technology': ['tech', 'software', 'saas', 'platform', 'digital', 'app'],
        'Healthcare': ['health', 'medical', 'healthcare', 'clinic', 'hospital'],
        'Financial Services': ['finance', 'financial', 'bank', 'investment'],
        'Consulting': ['consulting', 'consultant', 'advisory'],
        'Marketing & Advertising': ['marketing', 'advertising', 'agency'],
        'Legal Services': ['law', 'legal', 'attorney', 'lawyer'],
        'Real Estate': ['real estate', 'property', 'realty'],
        'Education': ['education', 'school', 'university'],
        'Manufacturing': ['manufacturing', 'factory', 'production'],
        'Retail': ['retail', 'store', 'shop', 'ecommerce']
    }
    
    all_text = f"{company} {title}"
    
    for industry, keywords in industry_keywords.items():
        if any(keyword in all_text for keyword in keywords):
            return industry
    
    return 'Business Services'

def infer_company_size(lead: Dict[str, Any]) -> str:
    """Infer company size from title"""
    title = lead.get('title', '').lower()
    
    if any(term in title for term in ['ceo', 'founder', 'president']):
        return '11-50'
    elif any(term in title for term in ['director', 'manager']):
        return '51-200'
    elif any(term in title for term in ['vp', 'vice president']):
        return '201-1000'
    
    return '51-200'

def infer_business_type(lead: Dict[str, Any]) -> str:
    """Infer business type from industry and company"""
    industry = lead.get('industry', '')
    company = lead.get('company', '').lower()
    
    if 'Technology' in industry or any(term in company for term in ['tech', 'software']):
        return 'Technology'
    elif 'Consulting' in industry:
        return 'Consulting'
    elif any(term in company for term in ['agency', 'marketing']):
        return 'Agency'
    
    return 'Business Services'

def infer_business_traits(lead: Dict[str, Any]) -> List[str]:
    """Infer business traits"""
    traits = []
    
    title = lead.get('title', '').lower()
    industry = lead.get('industry', '')
    
    if 'Technology' in industry:
        traits.append('Tech-Forward')
    
    if any(term in title for term in ['ceo', 'founder']):
        traits.append('Leadership Accessible')
    
    traits.append('Professional Services')
    
    return traits[:3]

def infer_pain_points(lead: Dict[str, Any]) -> List[str]:
    """Infer pain points from context"""
    pain_points = []
    
    title = lead.get('title', '').lower()
    industry = lead.get('industry', '')
    
    if any(term in title for term in ['ceo', 'founder']):
        pain_points.extend(['Growth scaling', 'Operational efficiency'])
    elif 'sales' in title:
        pain_points.extend(['Lead generation', 'Sales automation'])
    elif 'marketing' in title:
        pain_points.extend(['Customer acquisition', 'Marketing ROI'])
    
    if 'Technology' in industry:
        pain_points.append('Technical scaling')
    
    return pain_points[:3]

def generate_company_website(lead: Dict[str, Any]) -> str:
    """Generate company website URL"""
    company = lead.get('company', '')
    if not company:
        return None
    
    import re
    company_clean = re.sub(r'[^a-zA-Z0-9\s]', '', company.lower())
    domain = company_clean.replace(' ', '')
    
    return f"https://{domain}.com"

def main():
    """Main execution function"""
    logger.info("🚀 Starting Field Enrichment Process")
    logger.info("=" * 60)
    
    try:
        # Process JSON files
        total_processed, total_enriched = run_enrichment_on_json_files()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Field Enrichment Process Complete!")
        logger.info(f"📊 Total leads processed: {total_processed}")
        logger.info(f"✅ Total leads enriched: {total_enriched}")
        logger.info(f"📈 Success rate: {(total_enriched/total_processed)*100:.1f}%" if total_processed > 0 else "N/A")
        logger.info("📋 Check field_enrichment.log for detailed results")
        
    except Exception as e:
        logger.error(f"❌ Field enrichment failed: {e}")
        raise

if __name__ == "__main__":
    main()
