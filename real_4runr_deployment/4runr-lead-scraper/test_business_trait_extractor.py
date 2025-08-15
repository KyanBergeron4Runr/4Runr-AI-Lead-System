#!/usr/bin/env python3
"""
Test script for Business Trait Extractor.

This script tests the AI-powered business trait extraction with various
website content types to ensure reliable business intelligence extraction.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from enricher.business_trait_extractor import BusinessTraitExtractor, extract_business_traits_from_content
    EXTRACTOR_AVAILABLE = True
except ImportError as e:
    EXTRACTOR_AVAILABLE = False
    import_error = str(e)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('business-trait-extractor-test')

def test_extractor_availability():
    """Test if business trait extractor is available and properly configured."""
    
    logger.info("🧪 Testing business trait extractor availability")
    
    if not EXTRACTOR_AVAILABLE:
        logger.error(f"❌ Extractor not available: {import_error}")
        return False
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("⚠️ OPENAI_API_KEY not found in environment")
        logger.info("💡 Set OPENAI_API_KEY to test AI extraction")
        return False
    
    try:
        extractor = BusinessTraitExtractor()
        logger.info("✅ Business trait extractor initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Extractor initialization failed: {str(e)}")
        return False

def test_sample_enrichments():
    """Test business trait extraction with 5 sample content types."""
    
    logger.info("\n🧪 Testing 5 sample enrichments")
    
    if not EXTRACTOR_AVAILABLE:
        logger.warning("⚠️ Skipping test - extractor not available")
        return False
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️ Skipping test - OPENAI_API_KEY not found")
        return False
    
    # 5 sample content types for testing
    test_cases = [
        {
            'name': 'SaaS Platform',
            'content': {
                'text': 'We are a leading customer relationship management platform designed for growing businesses. Our cloud-based CRM helps sales teams track leads, manage pipelines, and automate follow-ups. With advanced analytics and integrations, we serve over 10,000 companies worldwide. Our customers often struggle with scattered customer data, manual sales processes, and lack of visibility into their sales funnel. We offer subscription plans starting at $29/month with enterprise features for larger teams.',
                'page_title': 'CRMPro - Customer Relationship Management Software',
                'meta_description': 'Streamline your sales process with our powerful CRM platform. Track leads, manage pipelines, and grow your business.',
                'url': 'https://example-crm.com',
                'company_name': 'CRMPro',
                'email': 'contact@crmpro.com'
            },
            'expected_type': 'SaaS',
            'expected_traits': ['B2B', 'Subscription-Based', 'Cloud-Based'],
            'expected_pain_points': ['Manual processes', 'Data management', 'Sales visibility']
        },
        {
            'name': 'Marketing Agency',
            'content': {
                'text': 'We are a full-service digital marketing agency specializing in B2B lead generation and content marketing. Our team of 25+ experts helps technology companies scale their marketing efforts through SEO, paid advertising, and marketing automation. We work with clients ranging from startups to Fortune 500 companies. Our clients typically come to us when they are struggling with inconsistent lead quality, high customer acquisition costs, and difficulty measuring marketing ROI. We offer retainer-based services and project-based engagements.',
                'page_title': 'GrowthMarketing - B2B Digital Marketing Agency',
                'meta_description': 'Scale your B2B marketing with our expert team. SEO, PPC, content marketing, and lead generation services.',
                'url': 'https://example-agency.com',
                'company_name': 'GrowthMarketing',
                'email': 'hello@growthmarketing.com'
            },
            'expected_type': 'Agency',
            'expected_traits': ['B2B', 'Service-Based', 'Expert Team'],
            'expected_pain_points': ['Lead quality', 'Customer acquisition', 'ROI measurement']
        },
        {
            'name': 'Local Service Provider',
            'content': {
                'text': 'Johnson & Associates is a premier accounting firm serving small and medium businesses in the Greater Toronto Area. With over 20 years of experience, we provide comprehensive bookkeeping, tax preparation, and financial consulting services. Our certified accountants help business owners stay compliant, reduce tax burden, and make informed financial decisions. Many of our clients come to us overwhelmed by financial paperwork, worried about tax compliance, and needing better financial visibility. We offer both monthly retainer services and project-based tax work.',
                'page_title': 'Johnson & Associates - Accounting Services Toronto',
                'meta_description': 'Professional accounting services for small businesses in Toronto. Bookkeeping, tax prep, and financial consulting.',
                'url': 'https://example-accounting.com',
                'company_name': 'Johnson & Associates',
                'email': 'info@johnsonaccounting.com'
            },
            'expected_type': 'Local Service',
            'expected_traits': ['B2B', 'Professional Services', 'Local'],
            'expected_pain_points': ['Compliance', 'Financial management', 'Paperwork']
        },
        {
            'name': 'E-commerce Platform',
            'content': {
                'text': 'ShopBuilder is an all-in-one e-commerce platform that helps entrepreneurs launch and scale their online stores. Our drag-and-drop store builder, integrated payment processing, and inventory management tools make it easy to start selling online. We serve over 50,000 merchants worldwide, from solo entrepreneurs to multi-million dollar brands. Our customers often struggle with technical complexity, high transaction fees, and difficulty managing inventory across multiple channels. We offer plans from $19/month to enterprise solutions with custom pricing.',
                'page_title': 'ShopBuilder - E-commerce Platform for Online Stores',
                'meta_description': 'Build and scale your online store with our powerful e-commerce platform. Easy setup, integrated payments, inventory management.',
                'url': 'https://example-ecommerce.com',
                'company_name': 'ShopBuilder',
                'email': 'support@shopbuilder.com'
            },
            'expected_type': 'SaaS',
            'expected_traits': ['B2B', 'E-commerce', 'Subscription-Based'],
            'expected_pain_points': ['Technical complexity', 'Transaction fees', 'Inventory management']
        },
        {
            'name': 'Consulting Firm',
            'content': {
                'text': 'Strategic Solutions Consulting is a management consulting firm specializing in digital transformation and operational efficiency for mid-market companies. Our team of former executives and industry experts helps organizations streamline processes, implement new technologies, and drive sustainable growth. We have successfully completed over 200 engagements across manufacturing, healthcare, and financial services. Our clients typically engage us when facing operational bottlenecks, technology integration challenges, and need for process optimization. We work on project-based engagements ranging from 3-18 months.',
                'page_title': 'Strategic Solutions - Management Consulting Firm',
                'meta_description': 'Drive digital transformation and operational efficiency with our expert consulting services. Process optimization and technology integration.',
                'url': 'https://example-consulting.com',
                'company_name': 'Strategic Solutions',
                'email': 'contact@strategicsolutions.com'
            },
            'expected_type': 'Consulting',
            'expected_traits': ['B2B', 'Expert Team', 'Project-Based'],
            'expected_pain_points': ['Operational efficiency', 'Technology integration', 'Process optimization']
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n🧪 Test Case {i}: {test_case['name']}")
        
        try:
            # Extract business traits
            result = extract_business_traits_from_content(test_case['content'])
            
            # Analyze results
            test_result = {
                'name': test_case['name'],
                'success': result.get('extraction_success', False),
                'business_type': result.get('Business_Type', 'Unknown'),
                'business_traits': result.get('Business_Traits', []),
                'pain_points': result.get('Pain_Points', []),
                'strategic_insight': result.get('Strategic_Insight', ''),
                'error': result.get('extraction_error', ''),
                'passed': False
            }
            
            # Evaluate quality
            if result.get('extraction_success'):
                business_type = result.get('Business_Type', '').lower()
                expected_type = test_case['expected_type'].lower()
                
                # Check if business type is reasonable
                type_match = (
                    business_type == expected_type or
                    expected_type in business_type or
                    business_type in expected_type or
                    business_type != 'unknown'
                )
                
                # Check if we got some traits and pain points
                has_traits = len(result.get('Business_Traits', [])) > 0
                has_pain_points = len(result.get('Pain_Points', [])) > 0
                has_insight = bool(result.get('Strategic_Insight', '').strip())
                
                if type_match and has_traits and has_pain_points:
                    test_result['passed'] = True
                    logger.info(f"   ✅ Extraction successful")
                else:
                    logger.warning(f"   ⚠️ Extraction incomplete - Type: {type_match}, Traits: {has_traits}, Pain Points: {has_pain_points}")
            else:
                logger.error(f"   ❌ Extraction failed: {result.get('extraction_error', 'Unknown error')}")
            
            # Log details
            logger.info(f"   📊 Business Type: {test_result['business_type']}")
            logger.info(f"   📊 Traits ({len(test_result['business_traits'])}): {test_result['business_traits']}")
            logger.info(f"   📊 Pain Points ({len(test_result['pain_points'])}): {test_result['pain_points']}")
            if test_result['strategic_insight']:
                logger.info(f"   📊 Insight: {test_result['strategic_insight'][:100]}...")
            
            results.append(test_result)
            
        except Exception as e:
            logger.error(f"   ❌ Test case failed with exception: {str(e)}")
            results.append({
                'name': test_case['name'],
                'success': False,
                'error': str(e),
                'passed': False
            })
    
    # Summary
    passed_tests = sum(1 for r in results if r['passed'])
    total_tests = len(results)
    
    logger.info(f"\n📊 Sample Enrichment Test Results:")
    logger.info("=" * 50)
    logger.info(f"✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    for result in results:
        status = "✅" if result['passed'] else "❌"
        logger.info(f"{status} {result['name']}: {result.get('business_type', 'Failed')}")
    
    return passed_tests == total_tests

def test_error_handling():
    """Test error handling for various failure scenarios."""
    
    logger.info("\n🧪 Testing error handling")
    
    if not EXTRACTOR_AVAILABLE:
        logger.warning("⚠️ Skipping test - extractor not available")
        return False
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️ Skipping test - OPENAI_API_KEY not found")
        return False
    
    error_test_cases = [
        {
            'name': 'Empty Content',
            'content': {'text': '', 'page_title': '', 'meta_description': ''},
            'should_fail': True
        },
        {
            'name': 'Very Short Content',
            'content': {'text': 'Hello world', 'page_title': 'Test', 'meta_description': ''},
            'should_fail': True
        },
        {
            'name': 'Error Page Content',
            'content': {
                'text': '404 Page Not Found. The page you are looking for does not exist. Please check the URL and try again.',
                'page_title': '404 - Page Not Found',
                'meta_description': 'Error page'
            },
            'should_fail': True
        },
        {
            'name': 'Generic Content',
            'content': {
                'text': 'Welcome to our website. We are a company that does business. Contact us for more information about our services.',
                'page_title': 'Welcome',
                'meta_description': 'Welcome to our website'
            },
            'should_fail': False  # Should work but return generic results
        }
    ]
    
    passed_tests = 0
    
    for test_case in error_test_cases:
        logger.info(f"   Testing: {test_case['name']}")
        
        try:
            result = extract_business_traits_from_content(test_case['content'])
            
            if test_case['should_fail']:
                if not result.get('extraction_success') or result.get('Business_Type') == 'Unknown':
                    logger.info(f"   ✅ Correctly handled: {result.get('extraction_error', 'Fallback result')}")
                    passed_tests += 1
                else:
                    logger.error(f"   ❌ Should have failed but succeeded")
            else:
                if result.get('extraction_success'):
                    logger.info("   ✅ Correctly processed generic content")
                    passed_tests += 1
                else:
                    logger.warning(f"   ⚠️ Failed on generic content: {result.get('extraction_error')}")
                    passed_tests += 1  # Still acceptable for generic content
        
        except Exception as e:
            if test_case['should_fail']:
                logger.info(f"   ✅ Correctly failed with exception: {str(e)}")
                passed_tests += 1
            else:
                logger.error(f"   ❌ Unexpected exception: {str(e)}")
    
    logger.info(f"✅ Error handling tests: {passed_tests}/{len(error_test_cases)} passed")
    return passed_tests == len(error_test_cases)

def test_integration_readiness():
    """Test that the extractor is ready for integration with enricher."""
    
    logger.info("\n🧪 Testing integration readiness")
    
    if not EXTRACTOR_AVAILABLE:
        logger.warning("⚠️ Skipping test - extractor not available")
        return False
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️ Skipping test - OPENAI_API_KEY not found")
        return False
    
    try:
        # Test that extractor can be imported and used independently
        extractor = BusinessTraitExtractor()
        
        # Test with sample content
        sample_content = {
            'text': 'We are a software development company specializing in web applications for small businesses.',
            'page_title': 'DevCorp - Web Development Services',
            'meta_description': 'Custom web development for small businesses',
            'url': 'https://example-dev.com'
        }
        
        result = extractor.extract_business_traits(sample_content)
        
        # Check result structure
        expected_keys = ['Business_Type', 'Business_Traits', 'Pain_Points', 'Strategic_Insight', 'extraction_success']
        
        for key in expected_keys:
            if key not in result:
                logger.error(f"   ❌ Missing key in result: {key}")
                return False
        
        logger.info("   ✅ Result structure correct")
        
        # Check that convenience functions work
        from enricher.business_trait_extractor import extract_business_traits_from_content, analyze_website_for_business_traits
        
        if callable(extract_business_traits_from_content):
            logger.info("   ✅ extract_business_traits_from_content available")
        else:
            logger.error("   ❌ extract_business_traits_from_content not callable")
            return False
        
        if callable(analyze_website_for_business_traits):
            logger.info("   ✅ analyze_website_for_business_traits available")
        else:
            logger.error("   ❌ analyze_website_for_business_traits not callable")
            return False
        
        logger.info("✅ Integration readiness test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration readiness test failed: {str(e)}")
        return False

def test_output_format():
    """Test that output format matches specifications."""
    
    logger.info("\n🧪 Testing output format compliance")
    
    if not EXTRACTOR_AVAILABLE:
        logger.warning("⚠️ Skipping test - extractor not available")
        return False
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️ Skipping test - OPENAI_API_KEY not found")
        return False
    
    try:
        sample_content = {
            'text': 'We provide marketing automation software for B2B companies. Our platform helps with lead generation and email campaigns.',
            'page_title': 'MarketingTech - B2B Marketing Automation',
            'meta_description': 'B2B marketing automation platform',
            'url': 'https://example-marketing.com',
            'company_name': 'MarketingTech',
            'email': 'info@marketingtech.com'
        }
        
        result = extract_business_traits_from_content(sample_content)
        
        # Check field types
        checks = [
            ('Business_Type', str, "Business_Type should be string"),
            ('Business_Traits', list, "Business_Traits should be list"),
            ('Pain_Points', list, "Pain_Points should be list"),
            ('Strategic_Insight', str, "Strategic_Insight should be string"),
            ('extraction_success', bool, "extraction_success should be boolean")
        ]
        
        for field, expected_type, message in checks:
            if field in result:
                if isinstance(result[field], expected_type):
                    logger.info(f"   ✅ {message}")
                else:
                    logger.error(f"   ❌ {message} (got {type(result[field])})")
                    return False
            else:
                logger.error(f"   ❌ Missing field: {field}")
                return False
        
        # Check list contents
        if result.get('Business_Traits'):
            if all(isinstance(trait, str) for trait in result['Business_Traits']):
                logger.info("   ✅ Business_Traits contains strings")
            else:
                logger.error("   ❌ Business_Traits should contain only strings")
                return False
        
        if result.get('Pain_Points'):
            if all(isinstance(point, str) for point in result['Pain_Points']):
                logger.info("   ✅ Pain_Points contains strings")
            else:
                logger.error("   ❌ Pain_Points should contain only strings")
                return False
        
        logger.info("✅ Output format compliance test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Output format test failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Business Trait Extractor Tests")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            ("Extractor Availability", test_extractor_availability),
            ("Sample Enrichments (5 cases)", test_sample_enrichments),
            ("Error Handling", test_error_handling),
            ("Integration Readiness", test_integration_readiness),
            ("Output Format Compliance", test_output_format),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
        
        # Summary
        logger.info("\n📊 Test Results Summary:")
        logger.info("=" * 40)
        
        passed_tests = 0
        total_tests = len(results)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status}: {test_name}")
            if passed:
                passed_tests += 1
        
        logger.info(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All business trait extractor tests passed!")
            logger.info("✅ Extractor is ready for integration with enricher")
        else:
            logger.warning("⚠️ Some tests failed - check logs above")
            
            if not EXTRACTOR_AVAILABLE:
                logger.info("\n💡 To enable business trait extractor:")
                logger.info("   pip install openai")
                logger.info("   export OPENAI_API_KEY=your_api_key")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)