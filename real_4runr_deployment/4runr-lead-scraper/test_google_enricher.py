#!/usr/bin/env python3
"""
Test the Google Enricher
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from enricher.google_enricher import GoogleEnricher


def main():
    """Test the Google enricher."""
    print("🔍 Testing Google Enricher")
    print("=" * 50)
    
    try:
        enricher = GoogleEnricher()
        
        # Test leads with missing data
        test_leads = [
            {
                'id': 'test_1',
                'name': 'John Smith',
                'company': '',  # Missing
                'website': '',  # Missing
                'linkedin_url': 'https://linkedin.com/in/johnsmith'
            },
            {
                'id': 'test_2', 
                'name': 'Sarah Johnson',
                'company': 'TechCorp',  # Has company
                'website': '',  # Missing website
                'linkedin_url': 'https://linkedin.com/in/sarahjohnson'
            }
        ]
        
        print(f"📋 Testing with {len(test_leads)} sample leads:")
        for i, lead in enumerate(test_leads, 1):
            print(f"  {i}. {lead['name']} at {lead['company'] or 'Unknown'}")
        
        print(f"\n🚀 Processing leads...")
        
        # Test single lead enrichment
        for i, lead in enumerate(test_leads, 1):
            print(f"\n--- Testing Lead {i}: {lead['name']} ---")
            
            result = enricher.enrich_lead_with_google(lead)
            
            print(f"✅ Results for {lead['name']}:")
            print(f"  Success: {result['success']}")
            print(f"  Found Company: {result.get('found_company', 'None')}")
            print(f"  Found Website: {result.get('found_website', 'None')}")
            print(f"  Queries Used: {len(result.get('search_queries_used', []))}")
            
            if result.get('error'):
                print(f"  Error: {result['error']}")
        
        print(f"\n🧪 Testing batch enrichment...")
        
        # Test batch enrichment
        batch_results = enricher.batch_enrich_with_google(test_leads, max_leads=2)
        
        successful = sum(1 for r in batch_results if r.get('success'))
        print(f"\n✅ Batch Results:")
        print(f"  Total: {len(batch_results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {len(batch_results) - successful}")
        
        return successful > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    print(f"\n{'✅ Test completed successfully!' if success else '❌ Test failed!'}")