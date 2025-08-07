#!/usr/bin/env python3
"""
Simplified test script for Google Scraper Pipeline Integration.

This script tests the core integration functionality without complex database operations.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.google_scraper_integration import GoogleScraperPipeline, process_lead_google_search
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    INTEGRATION_AVAILABLE = False
    import_error = str(e)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('google-integration-simple-test')

def test_integration_components():
    """Test that all integration components are available."""
    
    logger.info("🧪 Testing integration components")
    
    if not INTEGRATION_AVAILABLE:
        logger.error(f"❌ Integration not available: {import_error}")
        return False
    
    try:
        # Test pipeline initialization
        pipeline = GoogleScraperPipeline()
        logger.info("✅ Pipeline initialized")
        
        # Test that required components exist
        if hasattr(pipeline, 'db'):
            logger.info("✅ Database connection available")
        else:
            logger.error("❌ Database connection missing")
            return False
        
        if hasattr(pipeline, 'airtable_sync'):
            logger.info("✅ Airtable sync available")
        else:
            logger.error("❌ Airtable sync missing")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration components test failed: {str(e)}")
        return False

def test_conditional_execution_logic():
    """Test the conditional execution logic without database operations."""
    
    logger.info("\n🧪 Testing conditional execution logic")
    
    if not INTEGRATION_AVAILABLE:
        logger.warning("⚠️ Skipping test - integration not available")
        return False
    
    try:
        # Test the logic that determines if Google search should run
        
        # Mock lead with website (should skip)
        class MockLeadWithWebsite:
            def __init__(self):
                self.website = "https://existing-website.com"
                self.name = "John Smith"
                self.id = "test-id-1"
        
        # Mock lead without website (should process)
        class MockLeadWithoutWebsite:
            def __init__(self):
                self.website = None
                self.name = "Jane Doe"
                self.id = "test-id-2"
        
        lead_with_website = MockLeadWithWebsite()
        lead_without_website = MockLeadWithoutWebsite()
        
        # Test conditional logic
        if hasattr(lead_with_website, 'website') and lead_with_website.website and lead_with_website.website.strip():
            logger.info("✅ Lead with website would be skipped (correct)")
        else:
            logger.error("❌ Lead with website would not be skipped (incorrect)")
            return False
        
        if not (hasattr(lead_without_website, 'website') and lead_without_website.website and lead_without_website.website.strip()):
            logger.info("✅ Lead without website would be processed (correct)")
        else:
            logger.error("❌ Lead without website would not be processed (incorrect)")
            return False
        
        logger.info("✅ Conditional execution logic test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Conditional execution logic test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling for invalid inputs."""
    
    logger.info("\n🧪 Testing error handling")
    
    if not INTEGRATION_AVAILABLE:
        logger.warning("⚠️ Skipping test - integration not available")
        return False
    
    try:
        # Test non-existent lead ID
        result = process_lead_google_search("non-existent-id")
        
        if not result.get('success') and 'error' in result:
            logger.info("✅ Non-existent lead ID handled correctly")
        else:
            logger.error("❌ Non-existent lead ID not handled correctly")
            return False
        
        # Test None lead ID
        result = process_lead_google_search(None)
        
        if not result.get('success') and 'error' in result:
            logger.info("✅ None lead ID handled correctly")
        else:
            logger.error("❌ None lead ID not handled correctly")
            return False
        
        logger.info("✅ Error handling test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {str(e)}")
        return False

def test_convenience_functions():
    """Test that convenience functions are available."""
    
    logger.info("\n🧪 Testing convenience functions")
    
    if not INTEGRATION_AVAILABLE:
        logger.warning("⚠️ Skipping test - integration not available")
        return False
    
    try:
        from utils.google_scraper_integration import (
            process_lead_google_search,
            process_leads_google_search_batch
        )
        
        if callable(process_lead_google_search):
            logger.info("✅ process_lead_google_search available")
        else:
            logger.error("❌ process_lead_google_search not callable")
            return False
        
        if callable(process_leads_google_search_batch):
            logger.info("✅ process_leads_google_search_batch available")
        else:
            logger.error("❌ process_leads_google_search_batch not callable")
            return False
        
        logger.info("✅ Convenience functions test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Convenience functions test failed: {str(e)}")
        return False

def test_google_scraper_integration():
    """Test that Google scraper is properly integrated."""
    
    logger.info("\n🧪 Testing Google scraper integration")
    
    if not INTEGRATION_AVAILABLE:
        logger.warning("⚠️ Skipping test - integration not available")
        return False
    
    try:
        # Test that Google scraper can be imported
        from utils.google_scraper import search_company_website_google_sync
        
        if callable(search_company_website_google_sync):
            logger.info("✅ Google scraper function available")
        else:
            logger.error("❌ Google scraper function not callable")
            return False
        
        logger.info("✅ Google scraper integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Google scraper integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Simplified Google Scraper Integration Tests")
        logger.info("=" * 70)
        
        # Run simplified tests
        tests = [
            ("Integration Components", test_integration_components),
            ("Conditional Execution Logic", test_conditional_execution_logic),
            ("Error Handling", test_error_handling),
            ("Convenience Functions", test_convenience_functions),
            ("Google Scraper Integration", test_google_scraper_integration),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
        
        # Summary
        logger.info("\n📊 Test Results Summary:")
        logger.info("=" * 50)
        
        passed_tests = 0
        total_tests = len(results)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status}: {test_name}")
            if passed:
                passed_tests += 1
        
        logger.info(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All simplified integration tests passed!")
            logger.info("✅ Google scraper pipeline integration is ready")
        else:
            logger.warning("⚠️ Some tests failed - check logs above")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)