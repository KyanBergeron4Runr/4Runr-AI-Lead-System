#!/usr/bin/env python3
"""
Search Engine Tests

Comprehensive test suite for the advanced search and query functionality.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.search_engine import (
    LeadSearchEngine, SearchQuery, SearchFilter, SortCriteria,
    ComparisonOperator, SortOrder
)
from database.lead_database import LeadDatabase
from database.connection import get_database_connection

class TestSearchEngine(unittest.TestCase):
    """Test cases for Search Engine"""
    
    def setUp(self):
        """Set up test database for each test"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database and search engine
        self.db_conn = get_database_connection(self.temp_db.name)
        self.search_engine = LeadSearchEngine(self.db_conn)
        self.lead_db = LeadDatabase(self.temp_db.name)
        
        # Add sample data
        self._add_sample_data()
        
    def tearDown(self):
        """Clean up after each test"""
        # Close database connections
        if hasattr(self.db_conn, 'close_connections'):
            self.db_conn.close_connections()
        
        # Remove temporary database file
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    def _add_sample_data(self):
        """Add sample leads for testing"""
        sample_leads = [
            {
                'full_name': 'John Smith',
                'email': 'john.smith@techcorp.com',
                'company': 'TechCorp Inc',
                'title': 'CEO',
                'location': 'Montreal, QC',
                'industry': 'Technology',
                'status': 'new',
                'verified': True,
                'enriched': False
            },
            {
                'full_name': 'Sarah Johnson',
                'email': 'sarah.johnson@innovate.co',
                'company': 'Innovate Solutions',
                'title': 'CTO',
                'location': 'Toronto, ON',
                'industry': 'Software',
                'status': 'contacted',
                'verified': False,
                'enriched': True
            },
            {
                'full_name': 'Mike Chen',
                'email': 'mike.chen@startup.com',
                'company': 'StartupXYZ',
                'title': 'Founder',
                'location': 'Vancouver, BC',
                'industry': 'Fintech',
                'status': 'new',
                'verified': True,
                'enriched': True
            },
            {
                'full_name': 'Alice Brown',
                'email': 'alice.brown@consulting.com',
                'company': 'Brown Consulting',
                'title': 'Principal',
                'location': 'Calgary, AB',
                'industry': 'Consulting',
                'status': 'qualified',
                'verified': False,
                'enriched': False
            },
            {
                'full_name': 'David Wilson',
                'email': 'david.wilson@techcorp.com',
                'company': 'TechCorp Inc',
                'title': 'VP Engineering',
                'location': 'Montreal, QC',
                'industry': 'Technology',
                'status': 'new',
                'verified': True,
                'enriched': False
            }
        ]
        
        for lead_data in sample_leads:
            self.lead_db.add_lead(lead_data)
    
    def test_basic_search_query(self):
        """Test basic search functionality"""
        # Search for TechCorp employees
        filter_obj = SearchFilter('company', ComparisonOperator.EQUALS, 'TechCorp Inc')
        query = SearchQuery(filters=[filter_obj])
        
        result = self.search_engine.search(query)
        
        self.assertEqual(len(result.leads), 2)
        self.assertEqual(result.total_count, 2)
        self.assertGreater(result.query_time_ms, 0)
        
        # Verify all results are from TechCorp
        for lead in result.leads:
            self.assertEqual(lead['company'], 'TechCorp Inc')
    
    def test_like_search(self):
        """Test LIKE operator for partial matching"""
        filter_obj = SearchFilter('full_name', ComparisonOperator.LIKE, '%John%')
        query = SearchQuery(filters=[filter_obj])
        
        result = self.search_engine.search(query)
        
        self.assertEqual(len(result.leads), 2)  # John Smith and Sarah Johnson
        
        # Verify all results contain 'John'
        for lead in result.leads:
            self.assertIn('John', lead['full_name'])
    
    def test_multiple_filters(self):
        """Test multiple filters with AND logic"""
        filters = [
            SearchFilter('industry', ComparisonOperator.EQUALS, 'Technology'),
            SearchFilter('verified', ComparisonOperator.EQUALS, True)
        ]
        query = SearchQuery(filters=filters)
        
        result = self.search_engine.search(query)
        
        self.assertEqual(len(result.leads), 2)  # John Smith and David Wilson
        
        # Verify all results match both criteria
        for lead in result.leads:
            self.assertEqual(lead['industry'], 'Technology')
            self.assertTrue(lead['verified'])
    
    def test_sorting(self):
        """Test sorting functionality"""
        # Sort by full_name ascending
        sort_criteria = [SortCriteria('full_name', SortOrder.ASC)]
        query = SearchQuery(sort_by=sort_criteria)
        
        result = self.search_engine.search(query)
        
        self.assertEqual(len(result.leads), 5)
        
        # Verify sorting
        names = [lead['full_name'] for lead in result.leads]
        self.assertEqual(names, sorted(names))
    
    def test_pagination(self):
        """Test pagination functionality"""
        # Get first 2 results
        query = SearchQuery(limit=2, offset=0)
        result1 = self.search_engine.search(query)
        
        self.assertEqual(len(result1.leads), 2)
        self.assertEqual(result1.page_info['current_page'], 1)
        self.assertTrue(result1.page_info['has_next_page'])
        self.assertFalse(result1.page_info['has_previous_page'])
        
        # Get next 2 results
        query = SearchQuery(limit=2, offset=2)
        result2 = self.search_engine.search(query)
        
        self.assertEqual(len(result2.leads), 2)
        self.assertEqual(result2.page_info['current_page'], 2)
        self.assertTrue(result2.page_info['has_next_page'])
        self.assertTrue(result2.page_info['has_previous_page'])
        
        # Verify no overlap
        ids1 = {lead['id'] for lead in result1.leads}
        ids2 = {lead['id'] for lead in result2.leads}
        self.assertEqual(len(ids1.intersection(ids2)), 0)
    
    def test_in_operator(self):
        """Test IN operator for multiple values"""
        filter_obj = SearchFilter('status', ComparisonOperator.IN, ['new', 'contacted'])
        query = SearchQuery(filters=[filter_obj])
        
        result = self.search_engine.search(query)
        
        self.assertEqual(len(result.leads), 4)  # All except 'qualified'
        
        # Verify all results have correct status
        for lead in result.leads:
            self.assertIn(lead['status'], ['new', 'contacted'])
    
    def test_between_operator(self):
        """Test BETWEEN operator for date ranges"""
        # Add leads with specific dates
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # This test would need actual date data, so we'll test the structure
        filter_obj = SearchFilter('created_at', ComparisonOperator.BETWEEN, 
                                 [yesterday.isoformat(), now.isoformat()])
        query = SearchQuery(filters=[filter_obj])
        
        # Should not raise an error
        result = self.search_engine.search(query)
        self.assertIsInstance(result.leads, list)
    
    def test_is_null_operator(self):
        """Test IS NULL operator"""
        # Add a lead without email
        lead_without_email = {
            'full_name': 'No Email Lead',
            'company': 'Test Company'
        }
        self.lead_db.add_lead(lead_without_email)
        
        filter_obj = SearchFilter('email', ComparisonOperator.IS_NULL)
        query = SearchQuery(filters=[filter_obj])
        
        result = self.search_engine.search(query)
        
        self.assertGreater(len(result.leads), 0)
        
        # Verify all results have null email
        for lead in result.leads:
            self.assertIsNone(lead['email'])
    
    def test_quick_search(self):
        """Test quick search across multiple fields"""
        # Search for 'John' - should match John Smith
        results = self.search_engine.quick_search('John')
        
        self.assertGreater(len(results), 0)
        
        # Verify results contain 'John' in some field
        for lead in results:
            found_match = any([
                'John' in str(lead.get('full_name', '')),
                'John' in str(lead.get('company', '')),
                'John' in str(lead.get('title', '')),
                'John' in str(lead.get('industry', '')),
                'John' in str(lead.get('location', '')),
                'John' in str(lead.get('email', ''))
            ])
            self.assertTrue(found_match, f"No 'John' found in lead: {lead}")
    
    def test_search_by_company(self):
        """Test company-specific search"""
        # Exact match
        results = self.search_engine.search_by_company('TechCorp Inc', exact_match=True)
        self.assertEqual(len(results), 2)
        
        # Partial match
        results = self.search_engine.search_by_company('Tech', exact_match=False)
        self.assertGreaterEqual(len(results), 2)
    
    def test_search_by_location(self):
        """Test location-based search"""
        results = self.search_engine.search_by_location('Montreal')
        
        self.assertEqual(len(results), 2)  # John Smith and David Wilson
        
        # Verify all results are in Montreal
        for lead in results:
            self.assertIn('Montreal', lead['location'])
    
    def test_search_by_industry(self):
        """Test industry-based search"""
        results = self.search_engine.search_by_industry('Technology')
        
        self.assertEqual(len(results), 2)  # TechCorp employees
        
        # Verify all results are in Technology industry
        for lead in results:
            self.assertEqual(lead['industry'], 'Technology')
    
    def test_get_recent_leads(self):
        """Test recent leads functionality"""
        results = self.search_engine.get_recent_leads(days=1)
        
        # All our test leads should be recent
        self.assertEqual(len(results), 5)
        
        # Test with longer period
        results = self.search_engine.get_recent_leads(days=30, limit=3)
        self.assertEqual(len(results), 3)
    
    def test_get_enriched_leads(self):
        """Test enriched leads search"""
        results = self.search_engine.get_enriched_leads()
        
        self.assertEqual(len(results), 2)  # Sarah Johnson and Mike Chen
        
        # Verify all results are enriched
        for lead in results:
            self.assertTrue(lead['enriched'])
    
    def test_get_unverified_leads(self):
        """Test unverified leads search"""
        results = self.search_engine.get_unverified_leads()
        
        self.assertEqual(len(results), 2)  # Sarah Johnson and Alice Brown
        
        # Verify all results are unverified
        for lead in results:
            self.assertFalse(lead['verified'])
    
    def test_get_leads_by_status(self):
        """Test status-based search"""
        results = self.search_engine.get_leads_by_status('new')
        
        self.assertEqual(len(results), 3)  # John Smith, Mike Chen, David Wilson
        
        # Verify all results have 'new' status
        for lead in results:
            self.assertEqual(lead['status'], 'new')
    
    def test_get_statistics(self):
        """Test statistics functionality"""
        stats = self.search_engine.get_statistics()
        
        # Verify basic statistics
        self.assertEqual(stats['total_leads'], 5)
        self.assertIn('status_breakdown', stats)
        self.assertIn('top_companies', stats)
        self.assertIn('top_industries', stats)
        self.assertIn('top_locations', stats)
        self.assertIn('verified_count', stats)
        self.assertIn('enriched_count', stats)
        
        # Verify specific counts
        self.assertEqual(stats['verified_count'], 3)
        self.assertEqual(stats['enriched_count'], 2)
        
        # Verify status breakdown
        self.assertEqual(stats['status_breakdown']['new'], 3)
        self.assertEqual(stats['status_breakdown']['contacted'], 1)
        self.assertEqual(stats['status_breakdown']['qualified'], 1)
    
    def test_case_sensitivity(self):
        """Test case-sensitive and case-insensitive searches"""
        # Case-insensitive search (default) - should match 'TechCorp Inc'
        filter_obj = SearchFilter('company', ComparisonOperator.LIKE, '%techcorp%', case_sensitive=False)
        query = SearchQuery(filters=[filter_obj])
        
        result = self.search_engine.search(query)
        self.assertEqual(len(result.leads), 2)
        
        # Case-sensitive search with correct case - should match
        filter_obj = SearchFilter('company', ComparisonOperator.LIKE, '%TechCorp%', case_sensitive=True)
        query = SearchQuery(filters=[filter_obj])
        
        result = self.search_engine.search(query)
        self.assertEqual(len(result.leads), 2)  # Should match 'TechCorp Inc'
    
    def test_distinct_results(self):
        """Test distinct results functionality"""
        # Add duplicate company data
        duplicate_lead = {
            'full_name': 'Another TechCorp Employee',
            'company': 'TechCorp Inc',
            'title': 'Developer'
        }
        self.lead_db.add_lead(duplicate_lead)
        
        # Regular search
        filter_obj = SearchFilter('company', ComparisonOperator.EQUALS, 'TechCorp Inc')
        query = SearchQuery(filters=[filter_obj], distinct=False)
        
        result = self.search_engine.search(query)
        self.assertEqual(len(result.leads), 3)  # All TechCorp employees
        
        # Distinct search (note: DISTINCT * still returns all records since they have different IDs)
        query = SearchQuery(filters=[filter_obj], distinct=True)
        result = self.search_engine.search(query)
        self.assertEqual(len(result.leads), 3)  # Still 3 because each lead is unique
    
    def test_error_handling(self):
        """Test error handling for invalid queries"""
        # Invalid field
        with self.assertRaises(ValueError):
            filter_obj = SearchFilter('invalid_field', ComparisonOperator.EQUALS, 'value')
            query = SearchQuery(filters=[filter_obj])
            self.search_engine.search(query)
        
        # Invalid IN operator value
        with self.assertRaises(ValueError):
            filter_obj = SearchFilter('status', ComparisonOperator.IN, 'not_a_list')
            query = SearchQuery(filters=[filter_obj])
            self.search_engine.search(query)
        
        # Invalid BETWEEN operator value
        with self.assertRaises(ValueError):
            filter_obj = SearchFilter('created_at', ComparisonOperator.BETWEEN, ['single_value'])
            query = SearchQuery(filters=[filter_obj])
            self.search_engine.search(query)


class TestLeadDatabaseSearchIntegration(unittest.TestCase):
    """Test integration of search engine with Lead Database API"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.lead_db = LeadDatabase(self.temp_db.name)
        
        # Add sample data with unique identifiers to avoid duplicate detection
        sample_leads = [
            {'full_name': 'Alpha Lead', 'email': 'alpha@companya.com', 'company': 'Company A', 'status': 'new'},
            {'full_name': 'Beta Lead', 'email': 'beta@companyb.com', 'company': 'Company B', 'status': 'contacted'},
            {'full_name': 'Gamma Lead', 'email': 'gamma@companya.com', 'company': 'Company A', 'status': 'qualified'}
        ]
        
        for lead_data in sample_leads:
            self.lead_db.add_lead(lead_data)
    
    def tearDown(self):
        """Clean up"""
        if hasattr(self.lead_db, 'db_conn'):
            self.lead_db.db_conn.close_connections()
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    def test_advanced_search_integration(self):
        """Test advanced search through Lead Database API"""
        filter_obj = SearchFilter('company', ComparisonOperator.EQUALS, 'Company A')
        query = SearchQuery(filters=[filter_obj])
        
        result = self.lead_db.advanced_search(query)
        
        self.assertEqual(len(result['leads']), 2)
        self.assertEqual(result['total_count'], 2)
        self.assertIn('page_info', result)
        self.assertIn('query_time_ms', result)
    
    def test_quick_search_integration(self):
        """Test quick search through Lead Database API"""
        results = self.lead_db.quick_search('Company')
        
        self.assertEqual(len(results), 3)  # All leads have 'Company' in company field
    
    def test_search_by_company_integration(self):
        """Test company search through Lead Database API"""
        results = self.lead_db.search_by_company('Company A')
        
        self.assertEqual(len(results), 2)
        for lead in results:
            self.assertEqual(lead['company'], 'Company A')
    
    def test_get_leads_by_status_integration(self):
        """Test status search through Lead Database API"""
        results = self.lead_db.get_leads_by_status('new')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'new')
    
    def test_get_search_statistics_integration(self):
        """Test statistics through Lead Database API"""
        stats = self.lead_db.get_search_statistics()
        
        self.assertEqual(stats['total_leads'], 3)
        self.assertIn('status_breakdown', stats)
        self.assertEqual(stats['status_breakdown']['new'], 1)
        self.assertEqual(stats['status_breakdown']['contacted'], 1)
        self.assertEqual(stats['status_breakdown']['qualified'], 1)


def run_tests():
    """Run all search engine tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSearchEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestLeadDatabaseSearchIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)