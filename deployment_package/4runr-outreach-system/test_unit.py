#!/usr/bin/env python3
"""
Unit tests for 4Runr Outreach System components.

Tests individual components and functions to ensure they work correctly
in isolation.
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestImportSystem(unittest.TestCase):
    """Test the import system fixes."""
    
    def test_absolute_imports(self):
        """Test that absolute imports work correctly."""
        # Test core shared modules
        from outreach.shared.config import config
        from outreach.shared.logging_utils import get_logger
        
        self.assertIsNotNone(config)
        self.assertIsNotNone(get_logger)
    
    def test_module_entry_points(self):
        """Test that module entry points can be imported."""
        modules = [
            'outreach.website_scraper.main',
            'outreach.message_generator.main',
            'outreach.engager.main',
            'outreach.email_validator.main'
        ]
        
        for module_name in modules:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")


class TestOpenAIIntegration(unittest.TestCase):
    """Test OpenAI SDK integration."""
    
    def test_modern_openai_import(self):
        """Test that modern OpenAI SDK can be imported."""
        from openai import OpenAI
        import httpx
        
        self.assertTrue(hasattr(OpenAI, '__init__'))
        self.assertTrue(hasattr(httpx, 'Client'))
    
    def test_openai_client_initialization(self):
        """Test OpenAI client initialization."""
        from openai import OpenAI
        
        # Test basic initialization
        client = OpenAI(api_key="test_key")
        self.assertIsNotNone(client)
    
    def test_openai_proxy_support(self):
        """Test OpenAI client with proxy support."""
        import httpx
        from openai import OpenAI
        
        # Test proxy client initialization
        http_client = httpx.Client(proxies="http://test:8080", timeout=60)
        client = OpenAI(api_key="test_key", http_client=http_client)
        
        self.assertIsNotNone(client)
        self.assertIsNotNone(client._client)


class TestAirtableIntegration(unittest.TestCase):
    """Test configurable Airtable integration."""
    
    def test_configurable_client_initialization(self):
        """Test that configurable Airtable client initializes."""
        from outreach.shared.configurable_airtable_client import get_configurable_airtable_client
        
        client = get_configurable_airtable_client()
        self.assertIsNotNone(client)
    
    def test_field_mapping_configuration(self):
        """Test field mapping configuration."""
        from outreach.shared.configurable_airtable_client import get_configurable_airtable_client
        
        client = get_configurable_airtable_client()
        field_mapping = client.get_field_mapping()
        
        # Should have at least the basic fields
        required_fields = ['website', 'company_description', 'email', 'company_name']
        for field in required_fields:
            self.assertIn(field, field_mapping)
    
    @patch.dict(os.environ, {
        'AIRTABLE_FIELD_WEBSITE': 'Custom_Website',
        'AIRTABLE_FIELD_EMAIL': 'Custom_Email'
    })
    def test_custom_field_mapping(self):
        """Test that custom field mapping works."""
        # Need to reimport to pick up new env vars
        import importlib
        import outreach.shared.configurable_airtable_client
        importlib.reload(outreach.shared.configurable_airtable_client)
        
        from outreach.shared.configurable_airtable_client import ConfigurableAirtableClient
        
        client = ConfigurableAirtableClient()
        self.assertEqual(client.field_website, 'Custom_Website')
        self.assertEqual(client.field_email, 'Custom_Email')


class TestHealthCheckSystem(unittest.TestCase):
    """Test health check system."""
    
    def test_fastapi_app_creation(self):
        """Test that FastAPI app can be created."""
        from api import app
        
        self.assertIsNotNone(app)
        self.assertEqual(app.title, "4Runr Outreach System")
    
    def test_health_endpoints_exist(self):
        """Test that required health endpoints exist."""
        from api import app
        
        routes = [route.path for route in app.routes]
        required_endpoints = ['/health', '/pipeline/status', '/system/info']
        
        for endpoint in required_endpoints:
            self.assertIn(endpoint, routes, f"Endpoint {endpoint} not found")
    
    def test_health_endpoint_response(self):
        """Test health endpoint response format."""
        from fastapi.testclient import TestClient
        from api import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "outreach-system")


class TestResilientEngagement(unittest.TestCase):
    """Test resilient engagement pipeline."""
    
    def test_engager_fallback_message_generation(self):
        """Test fallback message generation."""
        from outreach.engager.app import EngagerAgent
        
        engager = EngagerAgent()
        
        test_lead = {
            'id': 'test_001',
            'Name': 'John Smith',
            'Company': 'TechCorp Inc',
            'Job Title': 'CTO',
            'Email': 'john@techcorp.com',
            'Custom_Message': ''  # No custom message
        }
        
        message = engager._get_or_generate_message(test_lead)
        
        self.assertIsNotNone(message)
        self.assertGreater(len(message), 50)
        self.assertIn('John', message)
        self.assertIn('TechCorp', message)
        self.assertIn('4Runr', message)
    
    def test_resilient_engager_skip_logic(self):
        """Test resilient engager skip logic."""
        from outreach.engager.resilient_engager import ResilientEngager
        
        engager = ResilientEngager()
        
        # Test valid lead (should not skip)
        valid_lead = {
            'id': 'test_valid',
            'Name': 'Valid User',
            'Company': 'ValidCorp',
            'Email': 'valid@validcorp.com',
            'Email_Confidence_Level': 'Real'
        }
        
        skip_reason = engager._should_skip_lead(valid_lead)
        self.assertIsNone(skip_reason)
        
        # Test invalid lead (should skip)
        invalid_lead = {
            'id': 'test_invalid',
            'Name': 'Invalid User',
            'Company': 'InvalidCorp',
            'Email': '',  # No email
            'Email_Confidence_Level': 'Real'
        }
        
        skip_reason = engager._should_skip_lead(invalid_lead)
        self.assertIsNotNone(skip_reason)
        self.assertEqual(skip_reason, 'no_email_address')
    
    def test_fallback_message_personalization(self):
        """Test that fallback messages are personalized."""
        from outreach.engager.resilient_engager import ResilientEngager
        
        engager = ResilientEngager()
        
        # Test with different company types
        tech_lead = {
            'id': 'test_tech',
            'Name': 'Tech User',
            'Company': 'TechCorp',
            'Company Description': 'Software development and technology solutions'
        }
        
        marketing_lead = {
            'id': 'test_marketing',
            'Name': 'Marketing User', 
            'Company': 'MarketingCorp',
            'Company Description': 'Marketing strategy and customer engagement'
        }
        
        tech_message = engager._generate_fallback_message(tech_lead)
        marketing_message = engager._generate_fallback_message(marketing_lead)
        
        # Messages should be different and personalized
        self.assertNotEqual(tech_message, marketing_message)
        self.assertIn('technology', tech_message.lower())
        self.assertIn('marketing', marketing_message.lower())


class TestConfiguration(unittest.TestCase):
    """Test system configuration."""
    
    def test_config_loading(self):
        """Test that configuration loads correctly."""
        from outreach.shared.config import config
        
        airtable_config = config.get_airtable_config()
        ai_config = config.get_ai_config()
        system_config = config.get_system_config()
        
        self.assertIsInstance(airtable_config, dict)
        self.assertIsInstance(ai_config, dict)
        self.assertIsInstance(system_config, dict)
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        from outreach.shared.config import config
        
        system_config = config.get_system_config()
        
        # Test that defaults are set
        self.assertIn('batch_size', system_config)
        self.assertIn('rate_limit_delay', system_config)
        
        # Test default values
        self.assertIsInstance(system_config['batch_size'], int)
        self.assertIsInstance(system_config['rate_limit_delay'], int)


class TestAgentInitialization(unittest.TestCase):
    """Test that all agents can be initialized."""
    
    def test_website_scraper_agent(self):
        """Test WebsiteScraperAgent initialization."""
        from outreach.website_scraper.app import WebsiteScraperAgent
        
        agent = WebsiteScraperAgent()
        self.assertIsNotNone(agent)
        self.assertIsNotNone(agent.logger)
        self.assertIsNotNone(agent.airtable_client)
    
    def test_message_generator_agent(self):
        """Test MessageGeneratorAgent initialization."""
        from outreach.message_generator.app import MessageGeneratorAgent
        
        agent = MessageGeneratorAgent()
        self.assertIsNotNone(agent)
        self.assertIsNotNone(agent.logger)
        self.assertIsNotNone(agent.airtable_client)
    
    def test_engager_agent(self):
        """Test EngagerAgent initialization."""
        from outreach.engager.app import EngagerAgent
        
        agent = EngagerAgent()
        self.assertIsNotNone(agent)
        self.assertIsNotNone(agent.logger)
        self.assertIsNotNone(agent.airtable_client)
    
    def test_email_validator_agent(self):
        """Test EmailValidatorAgent initialization."""
        from outreach.email_validator.app import EmailValidatorAgent
        
        agent = EmailValidatorAgent()
        self.assertIsNotNone(agent)
        self.assertIsNotNone(agent.logger)
        self.assertIsNotNone(agent.airtable_client)


def run_tests():
    """Run all unit tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestImportSystem,
        TestOpenAIIntegration,
        TestAirtableIntegration,
        TestHealthCheckSystem,
        TestResilientEngagement,
        TestConfiguration,
        TestAgentInitialization
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 Running Unit Tests for 4Runr Outreach System")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n✅ All unit tests passed!")
    else:
        print("\n❌ Some unit tests failed!")
    
    sys.exit(0 if success else 1)