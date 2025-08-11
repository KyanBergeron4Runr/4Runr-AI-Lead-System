
# DataCleaner Integration for Enrichers
# This code integrates the DataCleaner system with existing enrichers

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import DataCleaner

class EnricherDataCleanerIntegration:
    """Integration wrapper for DataCleaner with enrichers."""
    
    def __init__(self):
        self.data_cleaner = DataCleaner()
        
    def clean_lead_data(self, lead_data: dict, lead_context: dict) -> dict:
        """Clean lead data before updating Airtable."""
        try:
            # Extract data for cleaning
            data_to_clean = {
                'Company': lead_data.get('Company', ''),
                'Website': lead_data.get('Website', '')
            }
            
            # Clean the data
            result = self.data_cleaner.clean_and_validate(data_to_clean, lead_context)
            
            if result.success:
                # Return cleaned data
                cleaned_lead_data = lead_data.copy()
                cleaned_lead_data.update(result.cleaned_data)
                return cleaned_lead_data
            else:
                # Return original data if cleaning fails (graceful degradation)
                return lead_data
                
        except Exception as e:
            # Log error and return original data
            print(f"DataCleaner integration error: {e}")
            return lead_data

# Global instance for enrichers to use
enricher_data_cleaner = EnricherDataCleanerIntegration()
