#!/usr/bin/env python3
"""
Duplicate Detection Engine Tests

Comprehensive test suite for the enhanced duplicate detection functionality.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.duplicate_detector import DuplicateDetector, DuplicateMatch
from database.connection import get_database_connection
from database.lead_database import LeadDatabase

class TestDuplicateDetector(unittest.TestCase):
    """Test cases for Duplicate Detection Engine"""
    
    def setUp(self):
        """Set up test database for each test"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database
        self.db_conn = get_database_connection(self.temp_db.name)
        self.detector = DuplicateDetector(self.db_conn)
        self.lead_db = LeadDatabase(self.temp_db.name)
        
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
    
    def test_linkedin_url_exact_match(self):
        """Test LinkedIn URL exact matching"""
        # Add a lead with LinkedIn URL
        existing_lead = {
            'full_name': 'John Smith',
            'linkedin_url': 'https://linkedin.com/in/johnsmith',
            'company': 'TechCorp'
        }
        
        lead_id = self.lead_db.add_lead(existing_lead)
        
        # Test exact match
        new_lead = {
            'full_name': 'John S.',  # Different name
            'linkedin_url': 'https://linkedin.com/in/johnsmith',  # Same LinkedIn
            'company': 'Different Corp'  # Different company
        }
        
        matches = self.detector.find_duplicates(new_lead)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].lead_id, lead_id)
        self.assertEqual(matches[0].confidence, 1.0)
        self.assertEqual(matches[0].match_type, 'linkedin_url')
    
    def test_linkedin_url_normalization(self):
        """Test LinkedIn URL normalization"""
        # Add lead with normalized URL
        existing_lead = {
            'full_name': 'Jane Doe',
            'linkedin_url': 'https://linkedin.com/in/janedoe'
        }
        
        lead_id = self.lead_db.add_lead(existing_lead)
        
        # Test various URL formats
        url_variations = [
            'https://linkedin.com/in/janedoe/',  # Trailing slash
            'https://www.linkedin.com/in/janedoe',  # www prefix
            'https://linkedin.com/in/janedoe?trk=profile',  # Query parameters
        ]
        
        for url in url_variations:
            new_lead = {
                'full_name': 'Jane D.',
                'linkedin_url': url
            }
            
            matches = self.detector.find_duplicates(new_lead)
            self.assertEqual(len(matches), 1, f"Failed for URL: {url}")
            self.assertEqual(matches[0].lead_id, lead_id)
    
    def test_email_exact_match(self):
        """Test email exact matching"""
        # Add lead with email
        existing_lead = {
            'full_name': 'Bob Johnson',
            'email': 'bob@example.com',
            'company': 'Example Corp'
        }
        
        lead_id = self.lead_db.add_lead(existing_lead)
        
        # Test case-insensitive match
        new_lead = {
            'full_name': 'Robert Johnson',
            'email': 'BOB@EXAMPLE.COM',  # Different case
            'company': 'Different Corp'
        }
        
        matches = self.detector.find_duplicates(new_lead)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].lead_id, lead_id)
        self.assertEqual(matches[0].confidence, 1.0)
        self.assertEqual(matches[0].match_type, 'email')
    
    def test_name_company_exact_match(self):
        """Test exact name + company matching"""
        # Add lead
        existing_lead = {
            'full_name': 'Alice Smith',
            'company': 'Innovation Labs'
        }
        
        lead_id = self.lead_db.add_lead(existing_lead)
        
        # Test exact match (case insensitive)
        new_lead = {
            'full_name': 'ALICE SMITH',  # Different case
            'company': 'innovation labs',  # Different case
            'email': 'alice@innovationlabs.com'  # Additional data
        }
        
        matches = self.detector.find_duplicates(new_lead)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].lead_id, lead_id)
        self.assertEqual(matches[0].confidence, 0.95)
        self.assertEqual(matches[0].match_type, 'name_company')
    
    def test_domain_name_match(self):
        """Test domain + name similarity matching"""
        # Add lead with company email
        existing_lead = {
            'full_name': 'Michael Chen',
            'email': 'michael.chen@techstartup.com',
            'company': 'TechStartup Inc'  # Different company name
        }
        
        lead_id = self.lead_db.add_lead(existing_lead)
        
        # Test similar name, same domain
        new_lead = {
            'full_name': 'Mike Chen',  # Similar name
            'email': 'mike@techstartup.com',  # Same domain
            'company': 'Different Company',  # Different company
            'title': 'CTO'
        }
        
        matches = self.detector.find_duplicates(new_lead)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].lead_id, lead_id)
        self.assertEqual(matches[0].match_type, 'domain_name')
        self.assertGreater(matches[0].confidence, 0.6)
    
    def test_fuzzy_name_matching(self):
        """Test fuzzy name matching"""
        # Add lead
        existing_lead = {
            'full_name': 'Christopher Johnson',
            'company': 'Software Solutions Inc'
        }
        
        lead_id = self.lead_db.add_lead(existing_lead)
        
        # Test fuzzy name match
        new_lead = {
            'full_name': 'Chris Johnson',  # Shortened first name
            'company': 'Software Solutions Inc',  # Same company
            'title': 'Developer'
        }
        
        matches = self.detector.find_duplicates(new_lead)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].lead_id, lead_id)
        self.assertEqual(matches[0].match_type, 'fuzzy_name')
        self.assertGreater(matches[0].confidence, 0.85)
    
    def test_no_false_positives(self):
        """Test that different people don't match"""
        # Add lead
        existing_lead = {
            'full_name': 'John Smith',
            'email': 'john@company1.com',
            'company': 'Company One'
        }
        
        self.lead_db.add_lead(existing_lead)
        
        # Test completely different person
        different_lead = {
            'full_name': 'Jane Doe',
            'email': 'jane@company2.com',
            'company': 'Company Two'
        }
        
        matches = self.detector.find_duplicates(different_lead)
        
        # Should find no matches
        self.assertEqual(len(matches), 0)
    
    def test_confidence_thresholds(self):
        """Test confidence threshold filtering"""
        # Add lead
        existing_lead = {
            'full_name': 'Alexander Thompson',
            'company': 'Big Corp'
        }
        
        lead_id = self.lead_db.add_lead(existing_lead)
        
        # Test low similarity name (should not match)
        low_similarity_lead = {
            'full_name': 'Alex T',  # Very short, low similarity
            'company': 'Different Company'
        }
        
        matches = self.detector.find_duplicates(low_similarity_lead)
        
        # Should not match due to low confidence
        self.assertEqual(len(matches), 0)
    
    def test_data_merging_basic(self):
        """Test basic data merging functionality"""
        existing_lead = {
            'id': 'test-id',
            'full_name': 'John Smith',
            'email': 'john@example.com',
            'company': 'TechCorp',
            'verified': False,
            'enriched': False,
            'created_at': '2024-01-01T10:00:00',
            'updated_at': '2024-01-01T10:00:00'
        }
        
        new_lead_data = {
            'full_name': 'John Smith',
            'email': 'john@example.com',
            'title': 'CEO',  # New field
            'location': 'Montreal, QC',  # New field
            'verified': True,  # Should become True
            'enriched': True,  # Should become True
            'created_at': '2024-01-02T10:00:00'  # Later date, should keep earlier
        }
        
        merged = self.detector.merge_lead_data(existing_lead, new_lead_data)
        
        # Check that new fields were added
        self.assertEqual(merged['title'], 'CEO')
        self.assertEqual(merged['location'], 'Montreal, QC')
        
        # Check boolean OR fields
        self.assertTrue(merged['verified'])
        self.assertTrue(merged['enriched'])
        
        # Check that earlier created_at was preserved
        self.assertEqual(merged['created_at'], '2024-01-01T10:00:00')
        
        # Check that updated_at was updated
        self.assertNotEqual(merged['updated_at'], existing_lead['updated_at'])
    
    def test_data_merging_better_values(self):
        """Test merging with better values"""
        existing_lead = {
            'full_name': 'John',  # Short name
            'company': 'Tech',    # Short company
            'title': '',          # Empty title
            'email': 'john@example.com'
        }
        
        new_lead_data = {
            'full_name': 'John Smith',      # More complete name
            'company': 'TechCorp Inc',      # More complete company
            'title': 'Chief Executive Officer',  # New title
            'email': 'john@example.com'
        }
        
        merged = self.detector.merge_lead_data(existing_lead, new_lead_data)
        
        # Should use more complete values
        self.assertEqual(merged['full_name'], 'John Smith')
        self.assertEqual(merged['company'], 'TechCorp Inc')
        self.assertEqual(merged['title'], 'Chief Executive Officer')
    
    def test_raw_data_merging(self):
        """Test raw_data dictionary merging"""
        existing_lead = {
            'raw_data': {
                'source': 'linkedin',
                'confidence': 0.8,
                'social_profiles': {'linkedin': 'profile1'}
            }
        }
        
        new_lead_data = {
            'raw_data': {
                'source': 'clearbit',  # Different source
                'confidence': 0.9,     # Higher confidence
                'phone': '+1234567890',  # New field
                'social_profiles': {'twitter': '@john'}  # Additional profile
            }
        }
        
        merged = self.detector.merge_lead_data(existing_lead, new_lead_data)
        
        # Check merged raw_data
        raw_data = merged['raw_data']
        self.assertEqual(raw_data['confidence'], 0.9)  # Better value
        self.assertEqual(raw_data['phone'], '+1234567890')  # New field
        self.assertIn('linkedin', raw_data['social_profiles'])  # Preserved
        self.assertIn('twitter', raw_data['social_profiles'])   # Added
    
    def test_priority_matching(self):
        """Test that higher priority matches are returned first"""
        # Add lead with multiple matchable fields
        existing_lead = {
            'full_name': 'Sarah Wilson',
            'email': 'sarah@example.com',
            'linkedin_url': 'https://linkedin.com/in/sarahwilson',
            'company': 'Example Corp'
        }
        
        lead_id = self.lead_db.add_lead(existing_lead)
        
        # Test lead that matches on multiple criteria
        test_lead = {
            'full_name': 'Sarah Wilson',  # Name match
            'email': 'sarah@example.com',  # Email match (higher priority)
            'linkedin_url': 'https://linkedin.com/in/sarahwilson',  # LinkedIn match (highest priority)
            'company': 'Example Corp'
        }
        
        matches = self.detector.find_duplicates(test_lead)
        
        # Should return LinkedIn match first (highest confidence)
        self.assertEqual(len(matches), 1)  # Should deduplicate to one match
        self.assertEqual(matches[0].match_type, 'linkedin_url')
        self.assertEqual(matches[0].confidence, 1.0)
    
    def test_name_similarity_calculation(self):
        """Test name similarity calculation methods"""
        # Test exact match
        similarity = self.detector._calculate_name_similarity('John Smith', 'John Smith')
        self.assertEqual(similarity, 1.0)
        
        # Test partial match
        similarity = self.detector._calculate_name_similarity('John Smith', 'John S.')
        self.assertGreater(similarity, 0.7)
        
        # Test nickname match
        similarity = self.detector._calculate_name_similarity('Christopher Johnson', 'Chris Johnson')
        self.assertGreater(similarity, 0.75)  # Adjusted threshold
        
        # Test initials match
        similarity = self.detector._calculate_name_similarity('John Smith', 'J. Smith')
        self.assertGreater(similarity, 0.6)
        
        # Test no match
        similarity = self.detector._calculate_name_similarity('John Smith', 'Jane Doe')
        self.assertLess(similarity, 0.3)
    
    def test_phone_normalization(self):
        """Test phone number normalization"""
        # Test various phone formats
        test_cases = [
            ('(555) 123-4567', '+15551234567'),
            ('555-123-4567', '+15551234567'),
            ('555.123.4567', '+15551234567'),
            ('5551234567', '+15551234567'),
            ('1-555-123-4567', '+15551234567'),
            ('+1 555 123 4567', '+15551234567'),
        ]
        
        for input_phone, expected in test_cases:
            normalized = self.detector._normalize_phone(input_phone)
            self.assertEqual(normalized, expected, f"Failed for {input_phone}")
        
        # Test invalid phones
        invalid_phones = ['123', '555-123', 'not-a-phone']
        for phone in invalid_phones:
            normalized = self.detector._normalize_phone(phone)
            self.assertIsNone(normalized, f"Should be None for {phone}")
    
    def test_integration_with_lead_database(self):
        """Test integration with LeadDatabase API"""
        # Add initial lead
        lead1_data = {
            'full_name': 'Integration Test Lead',
            'email': 'integration@test.com',
            'company': 'Test Corp'
        }
        
        lead1_id = self.lead_db.add_lead(lead1_data)
        
        # Add duplicate lead (should merge)
        lead2_data = {
            'full_name': 'Integration Test Lead',
            'email': 'integration@test.com',  # Same email
            'title': 'CEO',  # Additional data
            'verified': True
        }
        
        lead2_id = self.lead_db.add_lead(lead2_data)
        
        # Should return same ID (merged)
        self.assertEqual(lead1_id, lead2_id)
        
        # Verify merged data
        merged_lead = self.lead_db.get_lead(lead1_id)
        self.assertEqual(merged_lead['title'], 'CEO')
        self.assertTrue(merged_lead['verified'])
        
        # Test find_all_duplicates API
        duplicates = self.lead_db.find_all_duplicates(lead2_data)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]['lead_id'], lead1_id)


def run_tests():
    """Run all duplicate detection tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDuplicateDetector)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)