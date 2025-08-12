#!/usr/bin/env python3
"""
Comprehensive integration tests for Google Enricher with DataCleaner.

This script tests the integration between the Google Enricher and the DataCleaner
system to ensure data is properly cleaned and validated before Airtable updates.
"""

import sys
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from outreach.google_enricher.app import GoogleEnricherAgent
from shared.data_cleaner import DataCleaner, CleaningResult


def test_google_enricher_initialization():
    """Test that Google Enricher initializes with DataCleaner successfully."""
    print("🔧 Testing Google Enricher Initialization with DataCleaner")
    print("=" * 60)
    
    try:
        # Mock the dependencies to avoid external calls
        with patch('outreach.google_enricher.app.get_airtable_client'), \
             patch('outreach.google_enricher.app.config.get_system_config') as mock_config:
            
            mock_config.return_value = {
                'batch_size': 10,
                'rate_limit_delay': 1
            }
            
            # Initialize Google Enricher
            enricher = GoogleEnricherAgent()
            
            # Check that DataCleaner was initialized
            has_data_cleaner = hasattr(enricher, 'data_cleaner')
            data_cleaner_initialized = enricher.data_cleaner is not None
            
            print(f"✅ Google Enricher initialized: True")
            print(f"✅ Has DataCleaner attribute: {has_data_cleaner}")
            print(f"✅ DataCleaner initialized: {data_cleaner_initialized}")
            
            if has_data_cleaner and data_cleaner_initialized:
                print(f"✅ Google Enricher + DataCleaner integration successful")
                return True
            else:
                print(f"❌ Google Enricher + DataCleaner integration failed")
                return False
                
    except Exception as e:
        print(f"❌ Error testing initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_cleaning_integration():
    """Test that enriched data goes through DataCleaner before Airtable update."""
    print("\\n🧹 Testing Data Cleaning Integration")
    print("=" * 60)
    
    try:
        # Mock dependencies
        with patch('outreach.google_enricher.app.get_airtable_client') as mock_airtable, \
             patch('outreach.google_enricher.app.config.get_system_config') as mock_config:
            
            mock_config.return_value = {
                'batch_size': 10,
                'rate_limit_delay': 1
            }
            
            # Mock Airtable client
            mock_airtable_instance = Mock()
            mock_airtable_instance.update_lead_fields.return_value = True
            mock_airtable.return_value = mock_airtable_instance
            
            # Initialize enricher
            enricher = GoogleEnricherAgent()
            
            # Test data with garbage that should be cleaned
            test_cases = [
                {
                    'name': 'Company with Google Search Artifacts',
                    'raw_data': {
                        'Company': 'Google Search Results TechCorp Inc Some results may have been delisted'
                    },
                    'expected_cleaned': {
                        'Company': 'TechCorp Inc'
                    }
                },
                {
                    'name': 'Website with LinkedIn URL',
                    'raw_data': {
             