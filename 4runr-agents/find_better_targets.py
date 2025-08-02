#!/usr/bin/env python3
"""
Find Better Target Companies - Focus on mid-size Montreal businesses
instead of huge corporations where CEOs are too busy/unreachable
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('target-finder')

def analyze_current_leads():
    """Analyze current leads and suggest better targets"""
    shared_dir = Path(__file__).parent / "shared"
    raw_leads_file = shared_dir / "raw_leads.json"
    
    if not raw_leads_file.exists():
        logger.error("❌ raw_leads.json not found")
        return
    
    with open(raw_leads_file, 'r', encoding='utf-8') as f:
        leads = json.load(f)
    
    print("\n" + "="*80)
    print("MONTREAL LEAD TARGET ANALYSIS")
    print("="*80)
    
    # Categorize companies by size/accessibility
    huge_companies = []
    good_targets = []
    unknown_companies = []
    
    # Define company categories
    huge_corp_indicators = [
        'shopify', 'bombardier', 'cgi', 'metro', 'saputo', 'dollarama',
        'hydro-québec', 'desjardins group'
    ]
    
    good_target_indicators = [
        'lightspeed', 'nuvei', 'cae', 'tfi', 'couche-tard', 'snc-lavalin'
    ]
    
    for lead in leads:
        name = lead.get('full_name', 'Unknown')
        company = lead.get('company', 'Unknown')
        company_lower = company.lower()
        
        if any(huge in company_lower for huge in huge_corp_indicators):
            huge_companies.append((name, company))
        elif any(good in company_lower for good in good_target_indicators):
            good_targets.append((name, company))
        else:
            unknown_companies.append((name, company))
    
    # Show analysis
    print(f"\n❌ AVOID - HUGE COMPANIES ({len(huge_companies)}):")
    print("   These CEOs are too big/busy and likely won't respond:")
    print("-" * 60)
    for name, company in huge_companies:
        print(f"   {name} - {company}")
        print(f"     💡 Why avoid: Massive corporation, CEO gets 1000s of emails")
    
    print(f"\n✅ GOOD TARGETS - MID-SIZE COMPANIES ({len(good_targets)}):")
    print("   These are better targets - successful but still accessible:")
    print("-" * 60)
    for name, company in good_targets:
        print(f"   {name} - {company}")
        print(f"     💡 Why good: Growing company, CEO more likely to respond")
    
    print(f"\n❓ RESEARCH NEEDED ({len(unknown_companies)}):")
    print("   Need to research these companies to determine if they're good targets:")
    print("-" * 60)
    for name, company in unknown_companies:
        print(f"   {name} - {company}")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS:")
    print("="*80)
    print("1. 🎯 FOCUS ON: Mid-size companies (50-1000 employees)")
    print("2. ❌ AVOID: Huge corporations (5000+ employees)")
    print("3. 🔍 LOOK FOR: Growing tech companies, family businesses, regional leaders")
    print("4. 💡 SWEET SPOT: Companies that need AI but aren't overwhelmed with vendors")
    print("\n📋 BETTER MONTREAL TARGETS TO FIND:")
    print("   - Local tech startups (Series A/B)")
    print("   - Regional manufacturing companies")
    print("   - Montreal-based consulting firms")
    print("   - Local retail/restaurant chains")
    print("   - Professional services firms")
    print("   - Family-owned businesses")
    print("="*80)

def suggest_new_search_terms():
    """Suggest better search terms for finding accessible Montreal business leaders"""
    print("\n🔍 BETTER SEARCH TERMS FOR MONTREAL LEADS:")
    print("="*50)
    
    better_searches = [
        "Montreal startup CEO",
        "Montreal tech founder",
        "Montreal family business owner",
        "Montreal consulting firm president",
        "Montreal manufacturing CEO",
        "Montreal professional services",
        "Montreal regional manager",
        "Montreal business owner",
        "Montreal entrepreneur",
        "Montreal small business CEO"
    ]
    
    for search_term in better_searches:
        print(f"   • {search_term}")
    
    print("\n💡 TARGET COMPANY SIZE:")
    print("   • 20-500 employees (sweet spot)")
    print("   • $5M-$100M annual revenue")
    print("   • Growing but not overwhelmed")
    print("   • Local decision makers")

if __name__ == "__main__":
    analyze_current_leads()
    suggest_new_search_terms()