#!/usr/bin/env python3
"""
Test a simpler enricher that works without Google search
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.airtable_client import get_airtable_client
from shared.logging_utils import get_logger


class SimpleEnricher:
    """Simple enricher that works with existing data"""
    
    def __init__(self):
        self.logger = get_logger('simple_enricher')
        self.airtable_client = get_airtable_client()
    
    def enrich_from_linkedin(self, lead):
        """Extract company info from LinkedIn URL if available"""
        linkedin_url = lead.get('LinkedIn URL', '')
        if not linkedin_url:
            return {}
        
        # Extract company from LinkedIn URL patterns
        # LinkedIn URLs often contain company info
        if '/company/' in linkedin_url:
            # Extract company name from LinkedIn company URL
            company_part = linkedin_url.split('/company/')[-1].split('/')[0]
            company_name = company_part.replace('-', ' ').title()
            return {'company': company_name}
        
        return {}
    
    def enrich_from_name_patterns(self, lead):
        """Use name patterns to infer company info"""
        full_name = lead.get('Full Name', '')
        current_company = lead.get('Company', '')
        
        # If company already exists and looks like "FirstName LastName & Partners"
        if current_company and '&' in current_company:
            # Try to extract website pattern
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0].lower()
                last_name = name_parts[-1].lower()
                
                # Generate potential website URLs
                potential_websites = [
                    f"https://{first_name}{last_name}.com",
                    f"https://{first_name}-{last_name}.com",
                    f"https://{last_name}.com",
                    f"https://{first_name}{last_name}.ca",
                ]
                
                return {'website': potential_websites[0]}  # Return first guess
        
        return {}
    
    async def process_leads(self, limit=10):
        """Process leads with simple enrichment"""
        # Get leads that need enrichment
        formula = "AND(NOT({Full Name} = ''), OR({Company} = '', {Website} = ''))"
        
        try:
            records = self.airtable_client.table.all(
                formula=formula,
                max_records=limit
            )
            
            leads = []
            for record in records:
                lead_data = {
                    'id': record['id'],
                    **record['fields']
                }
                leads.append(lead_data)
            
            print(f"📊 Found {len(leads)} leads needing enrichment")
            
            stats = {'processed': 0, 'successful': 0, 'errors': 0}
            
            for lead in leads:
                try:
                    full_name = lead.get('Full Name', '')
                    print(f"\n🔍 Processing: {full_name}")
                    
                    enrichment_data = {}
                    
                    # Try LinkedIn enrichment
                    linkedin_data = self.enrich_from_linkedin(lead)
                    if linkedin_data:
                        enrichment_data.update(linkedin_data)
                        print(f"  ✅ LinkedIn enrichment: {linkedin_data}")
                    
                    # Try name pattern enrichment
                    name_data = self.enrich_from_name_patterns(lead)
                    if name_data:
                        enrichment_data.update(name_data)
                        print(f"  ✅ Name pattern enrichment: {name_data}")
                    
                    # Update Airtable if we found something
                    if enrichment_data:
                        airtable_fields = {}
                        
                        if not lead.get('Company') and enrichment_data.get('company'):
                            airtable_fields['Company'] = enrichment_data['company']
                        
                        if not lead.get('Website') and enrichment_data.get('website'):
                            airtable_fields['Website'] = enrichment_data['website']
                        
                        if airtable_fields:
                            success = self.airtable_client.update_lead_fields(lead['id'], airtable_fields)
                            if success:
                                print(f"  ✅ Updated Airtable: {airtable_fields}")
                                stats['successful'] += 1
                            else:
                                print(f"  ❌ Failed to update Airtable")
                                stats['errors'] += 1
                        else:
                            print(f"  ⚠️  No new fields to update")
                    else:
                        print(f"  ⚠️  No enrichment data found")
                        stats['errors'] += 1
                    
                    stats['processed'] += 1
                    
                except Exception as e:
                    print(f"  ❌ Error processing {full_name}: {e}")
                    stats['errors'] += 1
                    stats['processed'] += 1
            
            return stats
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'processed': 0, 'successful': 0, 'errors': 1}


async def main():
    """Test the simple enricher"""
    print("🔍 Testing Simple Enricher (No Google Search)")
    print("=" * 50)
    
    enricher = SimpleEnricher()
    results = await enricher.process_leads(limit=5)
    
    print(f"\n📊 Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    success_rate = (results['successful'] / results['processed'] * 100) if results['processed'] > 0 else 0
    print(f"  Success Rate: {success_rate:.1f}%")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    print(f"\n{'✅ Success!' if success else '❌ Failed!'}")