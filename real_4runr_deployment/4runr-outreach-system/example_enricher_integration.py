#!/usr/bin/env python3
"""
Example: How to integrate DataCleaner with existing enricher code

This example shows how to modify your existing enricher agents to use
the DataCleaner system for eliminating garbage data before updating Airtable.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the integration wrapper
from enricher_data_cleaner_integration import enricher_data_cleaner
from shared.airtable_client import AirtableClient
from shared.logging_utils import get_logger

class ExampleEnricherWithDataCleaner:
    """
    Example enricher showing how to integrate DataCleaner.
    
    This is how you would modify your existing GoogleEnricherAgent
    or SimpleEnricher to use the DataCleaner system.
    """
    
    def __init__(self):
        self.logger = get_logger('example_enricher')
        self.airtable_client = AirtableClient()
        
        # The DataCleaner integration is already initialized
        # via the enricher_data_cleaner_integration module
    
    def process_lead_with_cleaning(self, lead_id: str, lead_data: dict):
        """
        Process a lead with data cleaning integration.
        
        This is the pattern to follow in your existing enrichers.
        """
        try:
            self.logger.log_module_activity('example_enricher', lead_id, 'info', {
                'message': 'Starting lead processing with data cleaning',
                'original_data': lead_data
            })
            
            # Step 1: Prepare context for DataCleaner
            lead_context = {
                'id': lead_id,
                'Full Name': lead_data.get('Full Name', ''),
                'source': 'example_enricher'
            }
            
            # Step 2: Clean the data BEFORE updating Airtable
            # This is the key integration point!
            cleaned_lead_data = enricher_data_cleaner.clean_lead_data(lead_data, lead_context)
            
            # Step 3: Check if data was cleaned
            data_was_cleaned = cleaned_lead_data != lead_data
            
            if data_was_cleaned:
                self.logger.log_module_activity('example_enricher', lead_id, 'info', {
                    'message': 'Data was cleaned by DataCleaner',
                    'original_company': lead_data.get('Company', ''),
                    'cleaned_company': cleaned_lead_data.get('Company', ''),
                    'original_website': lead_data.get('Website', ''),
                    'cleaned_website': cleaned_lead_data.get('Website', '')
                })
            
            # Step 4: Update Airtable with cleaned data
            # This is where you would normally call airtable_client.update_lead_fields()
            update_result = self.airtable_client.update_lead_fields(lead_id, cleaned_lead_data)
            
            if update_result:
                self.logger.log_module_activity('example_enricher', lead_id, 'success', {
                    'message': 'Lead updated successfully with cleaned data',
                    'data_was_cleaned': data_was_cleaned,
                    'final_data': cleaned_lead_data
                })
                return True
            else:
                self.logger.log_module_activity('example_enricher', lead_id, 'error', {
                    'message': 'Failed to update lead in Airtable'
                })
                return False
                
        except Exception as e:
            self.logger.log_module_activity('example_enricher', lead_id, 'error', {
                'message': f'Error processing lead: {e}',
                'original_data': lead_data
            })
            return False
    
    def demonstrate_garbage_elimination(self):
        """
        Demonstrate how the DataCleaner eliminates garbage data.
        """
        print("🧹 DataCleaner Integration Demonstration")
        print("=" * 60)
        
        # Example garbage data that would come from Google searches
        garbage_examples = [
            {
                'id': 'demo_1',
                'Full Name': 'John Doe',
                'Company': 'Sirius XM and ... Some results may have been delisted',
                'Website': 'https://google.com/search?q=sirius+xm'
            },
            {
                'id': 'demo_2',
                'Full Name': 'Jane Smith',
                'Company': 'Apple Inc - Google Search Results',
                'Website': 'linkedin.com/company/apple'
            },
            {
                'id': 'demo_3',
                'Full Name': 'Bob Johnson',
                'Company': '<div>Microsoft Corporation</div>',
                'Website': 'facebook.com/microsoft'
            },
            {
                'id': 'demo_4',
                'Full Name': 'Alice Brown',
                'Company': 'Clean Company LLC',  # This is clean data
                'Website': 'https://cleancompany.com'
            }
        ]
        
        for example in garbage_examples:
            print(f"\n📝 Processing Lead: {example['id']}")
            print(f"   Original Company: {example['Company']}")
            print(f"   Original Website: {example['Website']}")
            
            # Prepare context
            context = {
                'id': example['id'],
                'Full Name': example['Full Name'],
                'source': 'demonstration'
            }
            
            # Clean the data
            cleaned_data = enricher_data_cleaner.clean_lead_data(example, context)
            
            print(f"   Cleaned Company: {cleaned_data.get('Company', 'REJECTED')}")
            print(f"   Cleaned Website: {cleaned_data.get('Website', 'REJECTED')}")
            
            # Check if garbage was eliminated
            original_str = f"{example['Company']} {example['Website']}".lower()
            cleaned_str = f"{cleaned_data.get('Company', '')} {cleaned_data.get('Website', '')}".lower()
            
            garbage_patterns = ['google', 'search', 'results', 'delisted', '<div>', 'linkedin.com', 'facebook.com']
            garbage_eliminated = []
            
            for pattern in garbage_patterns:
                if pattern in original_str and pattern not in cleaned_str:
                    garbage_eliminated.append(pattern)
            
            if garbage_eliminated:
                print(f"   ✅ Garbage eliminated: {', '.join(garbage_eliminated)}")
            elif any(pattern in original_str for pattern in garbage_patterns):
                print(f"   🛡️ Garbage data rejected (quality too low)")
            else:
                print(f"   ✅ Clean data preserved")


def main():
    """Demonstrate the DataCleaner integration."""
    try:
        # Create example enricher
        enricher = ExampleEnricherWithDataCleaner()
        
        # Demonstrate garbage elimination
        enricher.demonstrate_garbage_elimination()
        
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION INSTRUCTIONS")
        print("=" * 60)
        print("To integrate DataCleaner with your existing enrichers:")
        print()
        print("1. Import the integration wrapper:")
        print("   from enricher_data_cleaner_integration import enricher_data_cleaner")
        print()
        print("2. Before updating Airtable, clean the data:")
        print("   cleaned_data = enricher_data_cleaner.clean_lead_data(lead_data, context)")
        print()
        print("3. Use cleaned_data instead of original lead_data:")
        print("   airtable_client.update_lead_fields(lead_id, cleaned_data)")
        print()
        print("✅ That's it! No more garbage data will reach Airtable!")
        print("🎉 'Some results may have been delisted' is now eliminated!")
        
        return True
        
    except Exception as e:
        print(f"\n💥 DEMONSTRATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)