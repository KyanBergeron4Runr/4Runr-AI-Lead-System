#!/usr/bin/env python3
"""
Working Airtable Sync - Only sync fields that exist in Airtable
"""

import os
import sqlite3
import requests
import json
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkingAirtableSync:
    """Sync only fields that exist in Airtable."""
    
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.table_name = os.getenv('AIRTABLE_TABLE_NAME')
        self.db_path = 'data/unified_leads.db'
        
        if not all([self.api_key, self.base_id, self.table_name]):
            raise ValueError("Missing required Airtable environment variables")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        self.base_url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_name}'
        
        # Known working fields from earlier tests
        self.working_fields = [
            'Full Name',
            'Email', 
            'Company',
            'LinkedIn URL',
            'AI Message'
            # 'Created At' is computed, so we skip it
        ]
        
    def sync_enriched_leads(self):
        """Sync enriched leads with working fields only."""
        logger.info("WORKING AIRTABLE SYNC - ENRICHED LEADS")
        logger.info("=" * 50)
        
        try:
            # Clear existing records first
            self.clear_existing_records()
            
            # Get enriched leads from database
            leads = self.get_enriched_leads()
            logger.info(f"Found {len(leads)} enriched leads to sync")
            
            if not leads:
                logger.warning("No enriched leads found in database")
                return True
            
            # Show what we're syncing
            self.show_enriched_preview(leads)
            
            # Sync to Airtable with working fields
            success_count = 0
            fail_count = 0
            
            logger.info(f"\nSyncing {len(leads)} enriched leads with core data...")
            
            for lead in leads:
                try:
                    self.sync_working_lead(lead)
                    success_count += 1
                    logger.info(f"SYNCED: {lead['full_name']} at {lead['company']}")
                    logger.info(f"  Business Type: {lead.get('business_type', 'N/A')}")
                    logger.info(f"  Industry: {lead.get('industry', 'N/A')}")
                    logger.info(f"  Location: {lead.get('location', 'N/A')}")
                    logger.info(f"  Lead Score: {lead.get('score', 0)}/100")
                    logger.info("")
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Failed to sync {lead['full_name']}: {e}")
            
            # Report results
            self.report_final_results(success_count, fail_count, len(leads), leads)
            
            return fail_count == 0
                
        except Exception as e:
            logger.error(f"Working sync failed: {e}")
            return False
    
    def clear_existing_records(self):
        """Clear existing records from Airtable."""
        try:
            logger.info("Clearing existing Airtable records...")
            
            # Get all existing records
            response = requests.get(self.base_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                # Delete in batches of 10 (Airtable limit)
                for i in range(0, len(records), 10):
                    batch = records[i:i+10]
                    record_ids = [record['id'] for record in batch]
                    
                    if record_ids:
                        delete_params = '&'.join([f'records[]={rid}' for rid in record_ids])
                        delete_url = f"{self.base_url}?{delete_params}"
                        
                        delete_response = requests.delete(delete_url, headers=self.headers)
                        
                        if delete_response.status_code != 200:
                            logger.warning(f"Failed to delete batch: {delete_response.status_code}")
                
                logger.info(f"Cleared {len(records)} existing records")
            else:
                logger.warning(f"Failed to get existing records: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Failed to clear existing records: {e}")
    
    def get_enriched_leads(self):
        """Get all enriched leads from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE enriched = 1 
                ORDER BY score DESC, full_name
            """)
            leads = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return leads
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            return []
    
    def show_enriched_preview(self, leads):
        """Show preview of enriched data."""
        logger.info(f"\nENRICHED DATA PREVIEW")
        logger.info("-" * 30)
        
        # Show enrichment stats
        business_types = {}
        scores = []
        
        for lead in leads:
            bt = lead.get('business_type', 'Unknown')
            score = lead.get('score', 0)
            
            business_types[bt] = business_types.get(bt, 0) + 1
            scores.append(score)
        
        logger.info(f"Business Type Distribution:")
        for bt, count in business_types.items():
            logger.info(f"  {bt}: {count} leads")
        
        avg_score = sum(scores) / len(scores) if scores else 0
        logger.info(f"\nLead Quality:")
        logger.info(f"  Average Score: {avg_score:.1f}/100")
        logger.info(f"  Top Score: {max(scores) if scores else 0}/100")
        
        # Show top leads with enrichment data
        logger.info(f"\nTOP ENRICHED LEADS:")
        top_leads = sorted(leads, key=lambda x: x.get('score', 0), reverse=True)[:3]
        for i, lead in enumerate(top_leads, 1):
            logger.info(f"  {i}. {lead['full_name']} at {lead['company']}")
            logger.info(f"     Type: {lead.get('business_type', 'N/A')} | Industry: {lead.get('industry', 'N/A')}")
            logger.info(f"     Location: {lead.get('location', 'N/A')} | Score: {lead.get('score', 0)}/100")
            logger.info(f"     AI Message Length: {len(lead.get('ai_message', ''))} chars")
    
    def sync_working_lead(self, lead):
        """Sync a single lead with only working fields."""
        # Only use fields that we know work in Airtable
        airtable_fields = {
            'Full Name': lead.get('full_name', ''),
            'Email': lead.get('email', ''),
            'Company': lead.get('company', ''),
            'LinkedIn URL': lead.get('linkedin_url', ''),
            'AI Message': self.create_enriched_summary(lead)  # Include enrichment in AI message
        }
        
        # Remove empty fields
        airtable_fields = {k: v for k, v in airtable_fields.items() if v}
        
        # Prepare data for Airtable
        airtable_data = {
            'fields': airtable_fields
        }
        
        # Post to Airtable
        response = requests.post(
            self.base_url,
            headers=self.headers,
            data=json.dumps(airtable_data),
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Airtable API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def create_enriched_summary(self, lead):
        """Create enriched summary to include in AI message field."""
        # Get the AI message and add enrichment data
        ai_message = lead.get('ai_message', '')
        
        # Add enrichment summary at the end
        enrichment_summary = f"""

=== LEAD ENRICHMENT DATA ===
Business Type: {lead.get('business_type', 'N/A')}
Industry: {lead.get('industry', 'N/A')}
Company Size: {lead.get('company_size', 'N/A')}
Location: {lead.get('location', 'N/A')}
Lead Score: {lead.get('score', 0)}/100
Website: {lead.get('company_website', 'N/A')}
Company Description: {lead.get('company_description', 'N/A')[:200]}...

Status: {lead.get('status', 'Ready for Outreach')}
Data Quality: {'High' if lead.get('enriched') else 'Basic'}
Ready for Outreach: {'Yes' if lead.get('ready_for_outreach') else 'No'}"""

        # Combine AI message with enrichment data
        full_content = ai_message + enrichment_summary
        
        # Truncate if too long for Airtable
        if len(full_content) > 3000:
            full_content = full_content[:2997] + "..."
        
        return full_content
    
    def report_final_results(self, success_count, fail_count, total_count, leads):
        """Report final sync results with enrichment stats."""
        logger.info(f"\nFINAL SYNC RESULTS")
        logger.info("=" * 50)
        
        logger.info(f"SYNC SUMMARY:")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Failed: {fail_count}")
        logger.info(f"  Total: {total_count}")
        logger.info(f"  Success Rate: {(success_count/total_count*100):.1f}%")
        
        if success_count > 0:
            # Calculate enrichment stats
            enriched_leads = [l for l in leads if l.get('enriched')]
            avg_score = sum(l.get('score', 0) for l in leads) / len(leads) if leads else 0
            
            business_types = set(l.get('business_type') for l in leads if l.get('business_type'))
            industries = set(l.get('industry') for l in leads if l.get('industry'))
            locations = set(l.get('location') for l in leads if l.get('location'))
            
            logger.info(f"\nENRICHMENT QUALITY:")
            logger.info(f"  Enriched Leads: {len(enriched_leads)}/{len(leads)} ({len(enriched_leads)/len(leads)*100:.1f}%)")
            logger.info(f"  Average Lead Score: {avg_score:.1f}/100")
            logger.info(f"  Business Types: {len(business_types)} categories")
            logger.info(f"  Industries: {len(industries)} sectors")
            logger.info(f"  Locations: {len(locations)} regions")
            
            logger.info(f"\nDATA SYNCED TO AIRTABLE:")
            logger.info(f"  ✓ Core contact information (Name, Email, Company, LinkedIn)")
            logger.info(f"  ✓ Enhanced AI messages with enrichment data embedded")
            logger.info(f"  ✓ Business classification and industry analysis")
            logger.info(f"  ✓ Company size and location intelligence")
            logger.info(f"  ✓ Lead scoring and quality indicators")
            logger.info(f"  ✓ Professional company descriptions")
            logger.info(f"  ✓ Outreach readiness status")
        
        if fail_count == 0:
            logger.info(f"\n🎉 ENRICHED LEADS SUCCESSFULLY SYNCED!")
            logger.info(f"All {success_count} enriched leads are now in Airtable with comprehensive data!")
            logger.info(f"The AI Message field contains both the personalized message AND enrichment data.")
        else:
            logger.warning(f"\nSync completed with {fail_count} failures")

def main():
    """Main sync function."""
    try:
        syncer = WorkingAirtableSync()
        success = syncer.sync_enriched_leads()
        
        if success:
            print("\nENRICHED LEADS SYNC SUCCESSFUL!")
            print("All enriched lead data has been synced to Airtable.")
            return 0
        else:
            print("\nENRICHED LEADS SYNC COMPLETED WITH WARNINGS")
            return 1
            
    except Exception as e:
        print(f"ENRICHED LEADS SYNC FAILED: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
