#!/usr/bin/env python3
"""
Validate LinkedIn URL matches and show which ones need manual review
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('linkedin-validator')

def load_resolved_urls():
    """Load the resolved LinkedIn URLs"""
    shared_dir = Path(__file__).parent / "shared"
    resolved_file = shared_dir / "resolved_linkedin_urls.json"
    
    if not resolved_file.exists():
        logger.error("❌ resolved_linkedin_urls.json not found")
        return []
    
    with open(resolved_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_matches():
    """Validate and display LinkedIn matches for manual review"""
    logger.info("🔍 Validating LinkedIn URL matches...")
    
    resolved_urls = load_resolved_urls()
    
    print("\n" + "="*80)
    print("LINKEDIN URL VALIDATION REPORT")
    print("="*80)
    
    verified_matches = []
    questionable_matches = []
    failed_matches = []
    
    for result in resolved_urls:
        name = result.get('input_name', 'Unknown')
        company = result.get('input_company', 'Unknown')
        linkedin_url = result.get('linkedin_url')
        score = result.get('match_score', 0)
        status = result.get('status', 'unknown')
        
        if status == 'verified' and linkedin_url:
            if score >= 0.8:
                verified_matches.append(result)
            else:
                questionable_matches.append(result)
        else:
            failed_matches.append(result)
    
    # Show high-confidence matches
    print(f"\n✅ HIGH CONFIDENCE MATCHES ({len(verified_matches)}):")
    print("-" * 50)
    for result in verified_matches:
        name = result['input_name']
        company = result['input_company']
        url = result['linkedin_url']
        score = result['match_score']
        print(f"  {name} ({company})")
        print(f"    URL: {url}")
        print(f"    Score: {score}")
        print()
    
    # Show questionable matches that need review
    print(f"\n⚠️  QUESTIONABLE MATCHES - NEED MANUAL REVIEW ({len(questionable_matches)}):")
    print("-" * 50)
    for result in questionable_matches:
        name = result['input_name']
        company = result['input_company']
        url = result['linkedin_url']
        score = result['match_score']
        title = result.get('result_title', 'No title')
        print(f"  {name} ({company})")
        print(f"    URL: {url}")
        print(f"    Score: {score}")
        print(f"    Title: {title}")
        print(f"    ❓ REVIEW: Does this LinkedIn profile match {name} from {company}?")
        print()
    
    # Show failed matches
    print(f"\n❌ FAILED MATCHES ({len(failed_matches)}):")
    print("-" * 50)
    for result in failed_matches:
        name = result['input_name']
        company = result['input_company']
        status = result['status']
        score = result.get('match_score', 0)
        print(f"  {name} ({company}) - Status: {status} (Score: {score})")
    
    print("\n" + "="*80)
    print("SUMMARY:")
    print(f"  ✅ High confidence: {len(verified_matches)}")
    print(f"  ⚠️  Need review: {len(questionable_matches)}")
    print(f"  ❌ Failed: {len(failed_matches)}")
    print(f"  📊 Overall accuracy: {len(verified_matches)}/{len(resolved_urls)} ({len(verified_matches)/len(resolved_urls)*100:.1f}%)")
    print("="*80)
    
    if questionable_matches:
        print("\n💡 RECOMMENDATION:")
        print("   Review the questionable matches manually by visiting the LinkedIn URLs")
        print("   If a match is incorrect, you can manually update the LinkedIn URL")
        print("   or increase the confidence threshold to be more selective.")

if __name__ == "__main__":
    validate_matches()