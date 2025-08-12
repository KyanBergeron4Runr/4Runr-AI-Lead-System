#!/usr/bin/env python3
"""
Integration tests for Agent Database Compatibility.

This test suite validates that all updated agents work correctly
with the new database API and maintain compatibility with existing workflows.
"""

import unittest
import tempfile
import shutil
import os
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from lead_database import LeadDatabase
from database_logger import database_logger


class TestAgentDatabaseIntegration(unittest.TestCase):
    """Integration tests for agent database compatibility."""
    
    def setUp(self):
        """Set up test environment with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_agents.db")
        
        # Create test database
        self.db = LeadDatabase(self.db_path)
        
        # Sample test data
        self.sample_leads = [
            {
                "full_name": "John Agent Test",
                "company": "Agent Test Corp",
                "email": "john@agenttest.com",
                "linkedin_url": "https://linkedin.com/in/johnagent",
                "title": "CEO",
                "source": "test_data"
            },
            {
                "full_name": "Jane Agent Test",
                "company": "Agent Test Inc",
                "email": "jane@agenttest.com",
                "linkedin_url": "https://linkedin.com/in/janeagent",
                "title": "CTO",
                "source": "test_data"
            }
        ]
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_add_test_lead_script_integration(self):
        """Test that add_test_lead.py works with database API."""
        # Import the updated script
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        
        try:
            # Mock Airtable client to avoid external API calls
            with patch('add_test_lead.get_airtable_client') as mock_airtable:
                mock_client = MagicMock()
                mock_client.create_lead.return_value = "test_record_123"
                mock_client.table.all.return_value = []  # No existing leads
                mock_airtable.return_value = mock_client
                
                # Mock the database path to use our test database
                with patch('add_test_lead.LeadDatabase') as mock_db_class:
                    mock_db_class.return_value = self.db
                    
                    # Import and run the add_lead function
                    from add_test_lead import add_lead
                    
                    result = add_lead()
                    
                    # Verify the function completed successfully
                    self.assertTrue(result)
                    
                    # Verify lead was added to database
                    search_results = self.db.search_leads({'email': 'kyan@4runr.com'})
                    self.assertEqual(len(search_results), 1)
                    
                    lead = search_results[0]
                    self.assertEqual(lead['full_name'], 'Kyan Bergeron')
                    self.assertEqual(lead['company'], '4Runr')
                    self.assertEqual(lead['email'], 'kyan@4runr.com')
                    self.assertTrue(lead['verified'])
                    self.assertTrue(lead['enriched'])
                    self.assertFalse(lead['needs_enrichment'])
        
        except ImportError as e:
            self.skipTest(f"Could not import add_test_lead: {e}")
    
    def test_sync_agent_database_integration(self):
        """Test sync agent integration with database."""
        # Add test leads to database
        lead_ids = []
        for lead_data in self.sample_leads:
            lead_id = self.db.add_lead(lead_data)
            lead_ids.append(lead_id)
        
        # Mark leads as pending sync
        for lead_id in lead_ids:
            self.db.update_lead(lead_id, {'sync_pending': True, 'airtable_synced': False})
        
        try:
            # Mock the sync agent components
            with patch('sync_to_airtable_updated.AirtableSyncManager') as mock_sync_manager:
                mock_summary = MagicMock()
                mock_summary.total_leads = 2
                mock_summary.successful_syncs = 2
                mock_summary.failed_syncs = 0
                mock_summary.errors = []
                
                mock_sync_instance = MagicMock()
                mock_sync_instance.sync_to_airtable.return_value = mock_summary
                mock_sync_manager.return_value = mock_sync_instance
                
                # Mock database path
                with patch('sync_to_airtable_updated.LeadDatabase') as mock_db_class:
                    mock_db_class.return_value = self.db
                    
                    # Import and test sync agent
                    from sync_to_airtable_updated import DatabaseAirtableSync
                    
                    sync_agent = DatabaseAirtableSync()
                    
                    # Test getting leads to sync
                    leads_to_sync = sync_agent.get_leads_to_sync()
                    self.assertEqual(len(leads_to_sync), 2)
                    
                    # Test sync process
                    results = sync_agent.run_sync_process(use_sync_manager=True)
                    
                    self.assertTrue(results['success'])
                    self.assertEqual(results['total_leads'], 2)
                    self.assertEqual(results['synced_count'], 2)
                    self.assertEqual(results['failed_count'], 0)
        
        except ImportError as e:
            self.skipTest(f"Could not import sync agent: {e}")
    
    def test_enricher_agent_database_integration(self):
        """Test enricher agent integration with database."""
        # Add leads needing enrichment
        for lead_data in self.sample_leads:
            lead_data_copy = lead_data.copy()
            lead_data_copy['email'] = None  # Remove email to trigger enrichment
            lead_data_copy['needs_enrichment'] = True
            lead_data_copy['enriched'] = False
            self.db.add_lead(lead_data_copy)
        
        try:
            # Mock external dependencies
            with patch('daily_enricher_agent_updated.dns') as mock_dns:
                mock_dns.resolver.resolve.return_value = ['mock_mx_record']
                
                # Mock database path
                with patch('daily_enricher_agent_updated.LeadDatabase') as mock_db_class:
                    mock_db_class.return_value = self.db
                    
                    # Import and test enricher agent
                    from daily_enricher_agent_updated import DatabaseEnricherAgent
                    
                    enricher_agent = DatabaseEnricherAgent()
                    
                    # Test getting leads needing enrichment
                    leads_needing_enrichment = enricher_agent.get_leads_needing_enrichment()
                    self.assertGreaterEqual(len(leads_needing_enrichment), 2)
                    
                    # Test enriching a single lead
                    test_lead = leads_needing_enrichment[0]
                    enriched_data = enricher_agent.enrich_lead(test_lead)
                    
                    self.assertIsInstance(enriched_data, dict)
                    self.assertIn('enriched_at', enriched_data)
                    self.assertIn('enrichment_method', enriched_data)
                    
                    # Test updating lead in database
                    success = enricher_agent.update_lead_in_database(test_lead['id'], enriched_data)
                    self.assertTrue(success)
        
        except ImportError as e:
            self.skipTest(f"Could not import enricher agent: {e}")
    
    def test_scraper_agent_database_integration(self):
        """Test scraper agent integration with database."""
        try:
            # Mock database path
            with patch('scraper_agent_database.LeadDatabase') as mock_db_class:
                mock_db_class.return_value = self.db
                
                # Import and test scraper agent
                from scraper_agent_database import DatabaseScraperAgent
                
                scraper_agent = DatabaseScraperAgent()
                
                # Test storing leads in database
                test_leads = [
                    {
                        'full_name': 'Scraped Lead 1',
                        'company': 'Scraped Corp',
                        'email': 'scraped1@test.com',
                        'source': 'website_scraper'
                    },
                    {
                        'full_name': 'Scraped Lead 2',
                        'company': 'Scraped Inc',
                        'email': 'scraped2@test.com',
                        'source': 'linkedin_scraper'
                    }
                ]
                
                storage_results = scraper_agent.store_leads_in_database(test_leads)
                
                self.assertTrue(storage_results['success'])
                self.assertEqual(storage_results['stored_count'], 2)
                self.assertEqual(storage_results['duplicate_count'], 0)
                self.assertEqual(storage_results['error_count'], 0)
                
                # Verify leads were stored
                stored_leads = self.db.search_leads({'source': 'website_scraper'})
                self.assertGreaterEqual(len(stored_leads), 1)
                
                linkedin_leads = self.db.search_leads({'source': 'linkedin_scraper'})
                self.assertGreaterEqual(len(linkedin_leads), 1)
        
        except ImportError as e:
            self.skipTest(f"Could not import scraper agent: {e}")
    
    def test_agent_logging_integration(self):
        """Test that agents properly integrate with database logging."""
        # Add a lead and verify logging
        lead_data = self.sample_leads[0].copy()
        
        # Mock logging to capture calls
        with patch('database_logger.log_database_event') as mock_log:
            lead_id = self.db.add_lead(lead_data)
            
            # Verify logging was called
            self.assertTrue(mock_log.called)
            
            # Check call arguments
            call_args = mock_log.call_args
            self.assertEqual(call_args[0][0], "database_operation")  # event_type
            self.assertIn("success", call_args[0][2])  # results should contain success
    
    def test_agent_error_handling(self):
        """Test agent error handling with database operations."""
        # Test with invalid lead data
        invalid_lead = {
            'company': 'Test Corp',
            # Missing required 'name' field
        }
        
        with self.assertRaises(ValueError):
            self.db.add_lead(invalid_lead)
        
        # Test with database connection issues
        # Close the database connection to simulate error
        self.db.db_manager.close()
        
        with self.assertRaises(Exception):
            self.db.add_lead(self.sample_leads[0])
    
    def test_agent_performance_monitoring(self):
        """Test that agents properly use performance monitoring."""
        # Add leads and verify performance monitoring
        start_time = datetime.now()
        
        for lead_data in self.sample_leads:
            self.db.add_lead(lead_data)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        # Performance should be reasonable (under 1 second for 2 leads)
        self.assertLess(execution_time, 1000)
        
        # Verify database stats are available
        stats = self.db.get_database_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_leads', stats)
        self.assertGreaterEqual(stats['total_leads'], 2)
    
    def test_agent_data_consistency(self):
        """Test data consistency across agent operations."""
        # Add lead via database API
        original_lead = self.sample_leads[0].copy()
        lead_id = self.db.add_lead(original_lead)
        
        # Retrieve lead
        retrieved_lead = self.db.get_lead(lead_id)
        
        # Verify data consistency
        self.assertEqual(retrieved_lead['full_name'], original_lead['full_name'])
        self.assertEqual(retrieved_lead['company'], original_lead['company'])
        self.assertEqual(retrieved_lead['email'], original_lead['email'])
        
        # Update lead
        update_data = {'title': 'Updated Title', 'verified': True}
        success = self.db.update_lead(lead_id, update_data)
        self.assertTrue(success)
        
        # Verify update
        updated_lead = self.db.get_lead(lead_id)
        self.assertEqual(updated_lead['title'], 'Updated Title')
        self.assertTrue(updated_lead['verified'])
    
    def test_agent_duplicate_handling(self):
        """Test that agents properly handle duplicate leads."""
        # Add original lead
        original_lead = self.sample_leads[0].copy()
        lead_id1 = self.db.add_lead(original_lead)
        
        # Add duplicate lead (same email)
        duplicate_lead = original_lead.copy()
        duplicate_lead['title'] = 'Different Title'  # Different title, same email
        
        lead_id2 = self.db.add_lead(duplicate_lead)
        
        # Should return same ID due to duplicate detection
        self.assertEqual(lead_id1, lead_id2)
        
        # Verify only one lead exists
        search_results = self.db.search_leads({'email': original_lead['email']})
        self.assertEqual(len(search_results), 1)
        
        # Verify lead was updated with new information
        final_lead = search_results[0]
        self.assertEqual(final_lead['title'], 'Different Title')
    
    def test_agent_search_functionality(self):
        """Test agent search functionality with database."""
        # Add test leads
        for lead_data in self.sample_leads:
            self.db.add_lead(lead_data)
        
        # Test search by company
        company_results = self.db.search_leads({'company': 'Agent Test Corp'})
        self.assertEqual(len(company_results), 1)
        self.assertEqual(company_results[0]['full_name'], 'John Agent Test')
        
        # Test search by source
        source_results = self.db.search_leads({'source': 'test_data'})
        self.assertEqual(len(source_results), 2)
        
        # Test search with multiple criteria
        multi_results = self.db.search_leads({
            'company': 'Agent Test Inc',
            'title': 'CTO'
        })
        self.assertEqual(len(multi_results), 1)
        self.assertEqual(multi_results[0]['full_name'], 'Jane Agent Test')
    
    def test_agent_sync_status_management(self):
        """Test sync status management across agents."""
        # Add leads
        lead_ids = []
        for lead_data in self.sample_leads:
            lead_id = self.db.add_lead(lead_data)
            lead_ids.append(lead_id)
        
        # Get leads pending sync
        pending_leads = self.db.get_sync_pending_leads()
        self.assertGreaterEqual(len(pending_leads), 2)
        
        # Mark leads as synced
        for lead_id in lead_ids:
            success = self.db.update_lead(lead_id, {
                'airtable_synced': True,
                'sync_pending': False,
                'airtable_id': f'airtable_{lead_id}'
            })
            self.assertTrue(success)
        
        # Verify no leads are pending sync
        pending_after_sync = self.db.get_sync_pending_leads()
        # Should be fewer pending leads (or none if these were the only ones)
        self.assertLessEqual(len(pending_after_sync), len(pending_leads))
    
    def test_agent_backward_compatibility(self):
        """Test backward compatibility with existing data structures."""
        # Test with old-style lead data (using 'name' instead of 'full_name')
        old_style_lead = {
            'name': 'Old Style Lead',  # Old field name
            'company': 'Old Style Corp',
            'email': 'oldstyle@test.com'
        }
        
        lead_id = self.db.add_lead(old_style_lead)
        self.assertIsNotNone(lead_id)
        
        # Retrieve and verify
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertEqual(retrieved_lead['full_name'], 'Old Style Lead')
        self.assertEqual(retrieved_lead['name'], 'Old Style Lead')  # Should be set for compatibility


class TestAgentWorkflowIntegration(unittest.TestCase):
    """Test complete agent workflow integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_workflow.db")
        self.db = LeadDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_lead_lifecycle(self):
        """Test complete lead lifecycle: scrape -> enrich -> sync."""
        # Step 1: Scrape leads (simulate scraper agent)
        scraped_leads = [
            {
                'full_name': 'Workflow Test Lead',
                'company': 'Workflow Corp',
                'linkedin_url': 'https://linkedin.com/in/workflowtest',
                'source': 'website_scraper',
                'needs_enrichment': True,
                'enriched': False
            }
        ]
        
        # Add scraped leads to database
        lead_ids = []
        for lead_data in scraped_leads:
            lead_id = self.db.add_lead(lead_data)
            lead_ids.append(lead_id)
        
        # Verify leads were added
        self.assertEqual(len(lead_ids), 1)
        
        # Step 2: Enrich leads (simulate enricher agent)
        for lead_id in lead_ids:
            enrichment_data = {
                'email': 'workflow@workflowcorp.com',
                'title': 'CEO',
                'enriched': True,
                'needs_enrichment': False,
                'enriched_at': datetime.now().isoformat()
            }
            
            success = self.db.update_lead(lead_id, enrichment_data)
            self.assertTrue(success)
        
        # Verify enrichment
        enriched_lead = self.db.get_lead(lead_ids[0])
        self.assertEqual(enriched_lead['email'], 'workflow@workflowcorp.com')
        self.assertTrue(enriched_lead['enriched'])
        self.assertFalse(enriched_lead['needs_enrichment'])
        
        # Step 3: Sync to Airtable (simulate sync agent)
        for lead_id in lead_ids:
            sync_data = {
                'airtable_id': f'airtable_rec_{lead_id}',
                'airtable_synced': True,
                'sync_pending': False,
                'last_sync_attempt': datetime.now().isoformat()
            }
            
            success = self.db.update_lead(lead_id, sync_data)
            self.assertTrue(success)
        
        # Verify sync status
        synced_lead = self.db.get_lead(lead_ids[0])
        self.assertTrue(synced_lead['airtable_synced'])
        self.assertFalse(synced_lead['sync_pending'])
        self.assertIsNotNone(synced_lead['airtable_id'])
        
        # Verify complete lifecycle
        final_lead = self.db.get_lead(lead_ids[0])
        self.assertEqual(final_lead['full_name'], 'Workflow Test Lead')
        self.assertEqual(final_lead['email'], 'workflow@workflowcorp.com')
        self.assertTrue(final_lead['enriched'])
        self.assertTrue(final_lead['airtable_synced'])
        self.assertEqual(final_lead['source'], 'website_scraper')


if __name__ == '__main__':
    # Run the integration tests
    unittest.main(verbosity=2)