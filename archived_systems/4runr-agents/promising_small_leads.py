#!/usr/bin/env python3
"""
Extract the most promising small Montreal company leads
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('promising-leads')

def extract_promising_leads():
    """Extract the best small company leads from our search"""
    
    # Manually curated promising leads from the search results
    promising_leads = [
        {
            "full_name": "Pascal Jarry",
            "title": "Founder and CEO", 
            "company": "Yapla",
            "linkedin_url": "https://ca.linkedin.com/in/pascaljarry",
            "location": "Montreal, Quebec, Canada",
            "company_size": "35 employees",
            "why_good": "Small tech company (35 people), founder-CEO, web specialists",
            "confidence": "high"
        },
        {
            "full_name": "Jon Ruby",
            "title": "CEO",
            "company": "Jonar",
            "linkedin_url": "https://ca.linkedin.com/in/rubyjon",
            "location": "Montreal, Quebec, Canada", 
            "company_size": "Small software company",
            "why_good": "Privately held software company since 1986, accessible CEO",
            "confidence": "high"
        },
        {
            "full_name": "Claude Lemay",
            "title": "President and CEO",
            "company": "Claude Lemay & Partners, Consultants",
            "linkedin_url": "https://ca.linkedin.com/in/claude-lemay-10808213",
            "location": "Montreal, Quebec, Canada",
            "company_size": "Small consulting firm",
            "why_good": "Small consulting firm, likely very responsive to AI solutions",
            "confidence": "high"
        },
        {
            "full_name": "Elie Wahnoun", 
            "title": "Founder and CEO",
            "company": "Courimo (Digital Marketing Agency)",
            "linkedin_url": "https://www.linkedin.com/in/eliewahnoun",
            "location": "Montreal, Quebec, Canada",
            "company_size": "Small agency",
            "why_good": "Digital marketing agency founder, perfect for AI tools",
            "confidence": "high"
        },
        {
            "full_name": "Afshan Nasseri",
            "title": "Founder & CEO", 
            "company": "Aam Creative",
            "linkedin_url": "Unknown",
            "location": "Montreal, Quebec, Canada",
            "company_size": "Small creative agency",
            "why_good": "Creative agency founder, minority-owned business, likely responsive",
            "confidence": "medium"
        },
        {
            "full_name": "Randal Tucker",
            "title": "Chief Executive Officer & President",
            "company": "SFM",
            "linkedin_url": "https://ca.linkedin.com/in/randal-tucker-31bbb618",
            "location": "Montreal, Quebec, Canada",
            "company_size": "Light manufacturing",
            "why_good": "25 years experience, manufacturing CEO, good AI prospect",
            "confidence": "high"
        },
        {
            "full_name": "François Rainville",
            "title": "President and CEO",
            "company": "Averna",
            "linkedin_url": "Unknown",
            "location": "Montreal, Quebec, Canada", 
            "company_size": "Medium tech company",
            "why_good": "Tech company CEO, recently appointed, may be open to new solutions",
            "confidence": "medium"
        }
    ]
    
    # Save to file
    shared_dir = Path(__file__).parent / "shared"
    output_file = shared_dir / "promising_small_leads.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(promising_leads, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved {len(promising_leads)} promising leads")
    
    # Print summary
    print("\n" + "="*70)
    print("🎯 PROMISING SMALL MONTREAL COMPANY LEADS")
    print("="*70)
    
    high_confidence = [l for l in promising_leads if l['confidence'] == 'high']
    medium_confidence = [l for l in promising_leads if l['confidence'] == 'medium']
    
    print(f"\n✅ HIGH CONFIDENCE LEADS ({len(high_confidence)}):")
    print("-" * 50)
    for lead in high_confidence:
        print(f"• {lead['full_name']} - {lead['title']}")
        print(f"  Company: {lead['company']} ({lead['company_size']})")
        print(f"  LinkedIn: {lead['linkedin_url']}")
        print(f"  Why good: {lead['why_good']}")
        print()
    
    print(f"⚠️ MEDIUM CONFIDENCE LEADS ({len(medium_confidence)}):")
    print("-" * 50)
    for lead in medium_confidence:
        print(f"• {lead['full_name']} - {lead['title']}")
        print(f"  Company: {lead['company']} ({lead['company_size']})")
        print(f"  Why good: {lead['why_good']}")
        print()
    
    print("="*70)
    print("💡 NEXT STEPS:")
    print("1. These are MUCH better targets than huge corporations")
    print("2. Small companies (20-200 employees) are more responsive")
    print("3. Founders/CEOs are decision makers, not gatekeepers")
    print("4. Focus LinkedIn outreach on the high-confidence leads first")
    print("5. These companies actually NEED AI solutions and can afford them")
    print("="*70)
    
    return promising_leads

if __name__ == "__main__":
    extract_promising_leads()