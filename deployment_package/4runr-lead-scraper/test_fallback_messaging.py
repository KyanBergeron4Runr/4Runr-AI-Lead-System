#!/usr/bin/env python3
"""
Test script for Fallback Message Generator.

This script tests the LLM-aware fallback messaging system with various
lead scenarios to ensure reliable message generation for leads with limited data.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from enricher.fallback_message_generator import FallbackMessageGenerator, generate_fallback_message, should_use_fallback_messaging
    FALLBACK_AVAILABLE = True
except ImportError as e:
    FALLBACK_AVAILABLE = False
    import_error = str(e)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('fallback-messaging-test')

def test_fallback_availability():
    """Test if fallback message generator is available and properly configured."""
    
    logger.info("🧪 Testing fallback message generator availability")
    
    if not FALLBACK_AVAILABLE:
        logger.error(f"❌ Fallback generator not available: {import_error}")
        return False
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("⚠️ OPENAI_API_KEY not found in environment")
        logger.info("💡 Set OPENAI_API_KEY to test AI message generation")
        return False
    
    try:
        generator = FallbackMessageGenerator()
        logger.info("✅ Fallback message generator initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Generator initialization failed: {str(e)}")
        return False

def test_fallback_decision_logic():
    """Test the logic for determining when to use fallback messaging."""
    
    logger.info("\n🧪 Testing fallback decision logic")
    
    if not FALLBACK_AVAILABLE:
        logger.warning("⚠️ Skipping test - fallback generator not available")
        return False
    
    test_cases = [
        {
            'name': 'High-confidence email, no enrichment data',
            'data': {
                'full_name': 'John Smith',
                'email': 'john@company.com',
                'email_confidence': 'real',
                'business_type': 'Unknown',
                'business_traits': [],
                'website': None
            },
            'should_use_fallback': True
        },
        {
            'name': 'Pattern email, failed website scraping',
            'data': {
                'full_name': 'Jane Doe',
                'email': 'jane@startup.io',
                'email_confidence': 'pattern',
                'website': 'https://startup.io',
                'website_scraping_failed': True,
                'business_type': 'Unknown'
            },
            'should_use_fallback': True
        },
        {
            'name': 'Low-confidence email',
            'data': {
                'full_name': 'Mike Johnson',
                'email': 'mike@company.com',
                'email_confidence': 'guess',
                'business_type': 'Unknown'
            },
            'should_use_fallback': False
        },
        {
            'name': 'Previously skipped lead',
            'data': {
                'full_name': 'Sarah Wilson',
                'email': 'sarah@business.com',
                'email_confidence': 'real',
                'previously_skipped': True,
                'business_type': 'Unknown'
            },
            'should_use_fallback': False
        },
        {
            'name': 'Complete enrichment data available',
            'data': {
                'full_name': 'David Chen',
                'email': 'david@techcorp.com',
                'email_confidence': 'real',
                'business_type': 'SaaS',
                'business_traits': ['B2B', 'Technical'],
                'website': 'https://techcorp.com',
                'strategic_insight': 'Great candidate for automation'
            },
            'should_use_fallback': False
        }
    ]
    
    passed_tests = 0
    
    for test_case in test_cases:
        logger.info(f"   Testing: {test_case['name']}")
        
        try:
            should_use = should_use_fallback_messaging(test_case['data'])
            expected = test_case['should_use_fallback']
            
            if should_use == expected:
                logger.info(f"   ✅ Correct decision: {should_use}")
                passed_tests += 1
            else:
                logger.error(f"   ❌ Wrong decision: got {should_use}, expected {expected}")
        
        except Exception as e:
            logger.error(f"   ❌ Test failed with exception: {str(e)}")
    
    logger.info(f"✅ Fallback decision tests: {passed_tests}/{len(test_cases)} passed")
    return passed_tests == len(test_cases)

def test_sample_message_generation():
    """Test fallback message generation with 5 sample leads."""
    
    logger.info("\n🧪 Testing 5 sample fallback message generations")
    
    if not FALLBACK_AVAILABLE:
        logger.warning("⚠️ Skipping test - fallback generator not available")
        return False
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️ Skipping test - OPENAI_API_KEY not found")
        return False
    
    # 5 sample leads with different scenarios
    sample_leads = [
        {
            'name': 'Tech Startup CEO',
            'data': {
                'full_name': 'Alex Rodriguez',
                'email': 'alex@innovatetech.com',
                'email_confidence': 'real',
                'business_type': 'Unknown',
                'business_traits': [],
                'website': None,
                'company_name': 'InnovateTech'
            },
            'expected_elements': ['alex', 'innovatetech', 'tech', 'growth']
        },
        {
            'name': 'Healthcare Professional',
            'data': {
                'full_name': 'Dr. Sarah Johnson',
                'email': 'sarah@healthcareplus.org',
                'email_confidence': 'pattern',
                'website': 'https://healthcareplus.org',
                'website_scraping_failed': True,
                'business_type': 'Unknown'
            },
            'expected_elements': ['sarah', 'healthcare', 'efficiency', 'operations']
        },
        {
            'name': 'Consulting Firm Partner',
            'data': {
                'full_name': 'Michael Chen',
                'email': 'mchen@strategyconsulting.ca',
                'email_confidence': 'real',
                'ai_analysis_failed': True,
                'business_type': 'Unknown',
                'business_traits': []
            },
            'expected_elements': ['michael', 'strategy', 'consulting', 'optimization']
        },
        {
            'name': 'Manufacturing Executive',
            'data': {
                'full_name': 'Jennifer Williams',
                'email': 'jwilliams@industrialmfg.com',
                'email_confidence': 'pattern',
                'business_type': 'Unknown',
                'website': None
            },
            'expected_elements': ['jennifer', 'industrial', 'manufacturing', 'automation']
        },
        {
            'name': 'Finance Professional',
            'data': {
                'full_name': 'Robert Taylor',
                'email': 'rtaylor@capitalinvest.com',
                'email_confidence': 'real',
                'business_type': 'Unknown',
                'business_traits': [],
                'strategic_insight': ''
            },
            'expected_elements': ['robert', 'capital', 'finance', 'growth']
        }
    ]
    
    results = []
    
    for i, sample in enumerate(sample_leads, 1):
        logger.info(f"\n🧪 Sample {i}: {sample['name']}")
        
        try:
            # Generate fallback message
            result = generate_fallback_message(sample['data'])
            
            # Analyze results
            test_result = {
                'name': sample['name'],
                'success': result.get('generation_success', False),
                'confidence': result.get('confidence', 'none'),
                'subject_line': result.get('subject_line', ''),
                'message': result.get('message', ''),
                'fallback_reason': result.get('fallback_reason', ''),
                'error': result.get('generation_error', ''),
                'passed': False
            }
            
            # Evaluate quality
            if result.get('generation_success'):
                message_lower = result.get('message', '').lower()
                subject_lower = result.get('subject_line', '').lower()
                combined_content = f"{message_lower} {subject_lower}"
                
                # Check for expected elements
                elements_found = 0
                for element in sample['expected_elements']:
                    if element.lower() in combined_content:
                        elements_found += 1
                
                # Quality checks
                has_name = sample['data']['full_name'].split()[0].lower() in message_lower
                has_reasonable_length = len(result.get('message', '')) > 100
                has_subject = len(result.get('subject_line', '')) > 5
                has_4runr_mention = '4runr' in message_lower
                
                quality_score = sum([
                    elements_found >= 2,  # At least 2 expected elements
                    has_name,             # Personalized with name
                    has_reasonable_length, # Adequate message length
                    has_subject,          # Has subject line
                    has_4runr_mention     # Mentions 4Runr
                ])
                
                if quality_score >= 4:
                    test_result['passed'] = True
                    logger.info(f"   ✅ High-quality message generated")
                elif quality_score >= 3:
                    test_result['passed'] = True
                    logger.info(f"   ✅ Good-quality message generated")
                else:
                    logger.warning(f"   ⚠️ Message quality could be improved (score: {quality_score}/5)")
            else:
                logger.error(f"   ❌ Message generation failed: {result.get('generation_error', 'Unknown error')}")
            
            # Log details
            logger.info(f"   📊 Confidence: {test_result['confidence']}")
            logger.info(f"   📊 Reason: {test_result['fallback_reason']}")
            if test_result['subject_line']:
                logger.info(f"   📋 Subject: {test_result['subject_line']}")
            if test_result['message']:
                logger.info(f"   📋 Message: {test_result['message'][:150]}...")
            
            results.append(test_result)
            
        except Exception as e:
            logger.error(f"   ❌ Sample failed with exception: {str(e)}")
            results.append({
                'name': sample['name'],
                'success': False,
                'error': str(e),
                'passed': False
            })
    
    # Summary
    passed_tests = sum(1 for r in results if r['passed'])
    total_tests = len(results)
    
    logger.info(f"\n📊 Sample Message Generation Results:")
    logger.info("=" * 50)
    logger.info(f"✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    for result in results:
        status = "✅" if result['passed'] else "❌"
        logger.info(f"{status} {result['name']}: {result.get('confidence', 'failed')}")
    
    return passed_tests >= 4  # At least 4/5 should pass

def test_error_handling():
    """Test error handling for various failure scenarios."""
    
    logger.info("\n🧪 Testing error handling")
    
    if not FALLBACK_AVAILABLE:
        logger.warning("⚠️ Skipping test - fallback generator not available")
        return False
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️ Skipping test - OPENAI_API_KEY not found")
        return False
    
    error_test_cases = [
        {
            'name': 'Missing name',
            'data': {'email': 'test@company.com', 'email_confidence': 'real'},
            'should_fail': True
        },
        {
            'name': 'Missing email',
            'data': {'full_name': 'John Smith', 'email_confidence': 'real'},
            'should_fail': True
        },
        {
            'name': 'Invalid email format',
            'data': {'full_name': 'John Smith', 'email': 'invalid-email', 'email_confidence': 'real'},
            'should_fail': True
        },
        {
            'name': 'Minimal valid data',
            'data': {'full_name': 'Jane Doe', 'email': 'jane@company.com', 'email_confidence': 'real'},
            'should_fail': False
        }
    ]
    
    passed_tests = 0
    
    for test_case in error_test_cases:
        logger.info(f"   Testing: {test_case['name']}")
        
        try:
            result = generate_fallback_message(test_case['data'])
            
            if test_case['should_fail']:
                if not result.get('generation_success'):
                    logger.info(f"   ✅ Correctly failed: {result.get('generation_error', 'No error message')}")
                    passed_tests += 1
                else:
                    logger.error(f"   ❌ Should have failed but succeeded")
            else:
                if result.get('generation_success'):
                    logger.info("   ✅ Correctly succeeded")
                    passed_tests += 1
                else:
                    logger.warning(f"   ⚠️ Failed on valid data: {result.get('generation_error')}")
        
        except Exception as e:
            if test_case['should_fail']:
                logger.info(f"   ✅ Correctly failed with exception: {str(e)}")
                passed_tests += 1
            else:
                logger.error(f"   ❌ Unexpected exception: {str(e)}")
    
    logger.info(f"✅ Error handling tests: {passed_tests}/{len(error_test_cases)} passed")
    return passed_tests == len(error_test_cases)

def test_integration_readiness():
    """Test that the fallback generator is ready for integration."""
    
    logger.info("\n🧪 Testing integration readiness")
    
    if not FALLBACK_AVAILABLE:
        logger.warning("⚠️ Skipping test - fallback generator not available")
        return False
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️ Skipping test - OPENAI_API_KEY not found")
        return False
    
    try:
        # Test that generator can be imported and used independently
        generator = FallbackMessageGenerator()
        
        # Test with sample data
        sample_data = {
            'full_name': 'Test User',
            'email': 'test@company.com',
            'email_confidence': 'real',
            'business_type': 'Unknown'
        }
        
        result = generator.generate_fallback_message(sample_data)
        
        # Check result structure
        expected_keys = [
            'message', 'subject_line', 'confidence', 'used_fallback', 
            'fallback_reason', 'generation_success', 'generated_at'
        ]
        
        for key in expected_keys:
            if key not in result:
                logger.error(f"   ❌ Missing key in result: {key}")
                return False
        
        logger.info("   ✅ Result structure correct")
        
        # Test convenience functions
        from enricher.fallback_message_generator import generate_fallback_message, should_use_fallback_messaging
        
        if callable(generate_fallback_message):
            logger.info("   ✅ generate_fallback_message available")
        else:
            logger.error("   ❌ generate_fallback_message not callable")
            return False
        
        if callable(should_use_fallback_messaging):
            logger.info("   ✅ should_use_fallback_messaging available")
        else:
            logger.error("   ❌ should_use_fallback_messaging not callable")
            return False
        
        # Test fallback decision logic
        should_use = generator.should_use_fallback(sample_data)
        if isinstance(should_use, bool):
            logger.info("   ✅ Fallback decision logic working")
        else:
            logger.error("   ❌ Fallback decision logic not working")
            return False
        
        logger.info("✅ Integration readiness test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration readiness test failed: {str(e)}")
        return False

def test_message_quality():
    """Test the quality and personalization of generated messages."""
    
    logger.info("\n🧪 Testing message quality and personalization")
    
    if not FALLBACK_AVAILABLE:
        logger.warning("⚠️ Skipping test - fallback generator not available")
        return False
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️ Skipping test - OPENAI_API_KEY not found")
        return False
    
    try:
        # Test with detailed lead data
        detailed_lead = {
            'full_name': 'Jennifer Martinez',
            'email': 'jennifer@digitalmarketing.com',
            'company_name': 'Digital Marketing Solutions',
            'email_confidence': 'real',
            'business_type': 'Unknown',
            'business_traits': [],
            'website': None
        }
        
        result = generate_fallback_message(detailed_lead)
        
        if not result.get('generation_success'):
            logger.error(f"   ❌ Message generation failed: {result.get('generation_error')}")
            return False
        
        message = result.get('message', '').lower()
        subject = result.get('subject_line', '').lower()
        
        # Quality checks
        quality_checks = [
            ('Personalized with name', 'jennifer' in message),
            ('References company', 'digital marketing' in message or 'digitalmarketing' in message),
            ('Mentions 4Runr', '4runr' in message),
            ('Has call to action', any(phrase in message for phrase in ['call', 'meeting', 'chat', 'discuss', 'connect'])),
            ('Professional tone', len(message) > 100 and len(message) < 500),
            ('Has subject line', len(subject) > 5),
            ('Strategic positioning', any(phrase in message for phrase in ['growth', 'efficiency', 'optimization', 'automation']))
        ]
        
        passed_checks = sum(1 for _, check in quality_checks if check)
        
        logger.info(f"   📊 Quality Score: {passed_checks}/{len(quality_checks)}")
        
        for check_name, passed in quality_checks:
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {check_name}")
        
        # Log sample output
        logger.info(f"   📋 Sample Subject: {result.get('subject_line', '')}")
        logger.info(f"   📋 Sample Message: {result.get('message', '')[:200]}...")
        
        # Pass if at least 5/7 quality checks pass
        return passed_checks >= 5
        
    except Exception as e:
        logger.error(f"❌ Message quality test failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Fallback Message Generator Tests")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            ("Fallback Availability", test_fallback_availability),
            ("Fallback Decision Logic", test_fallback_decision_logic),
            ("Sample Message Generation (5 cases)", test_sample_message_generation),
            ("Error Handling", test_error_handling),
            ("Integration Readiness", test_integration_readiness),
            ("Message Quality", test_message_quality),
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
            logger.info("🎉 All fallback messaging tests passed!")
            logger.info("✅ Fallback system is ready for integration")
        else:
            logger.warning("⚠️ Some tests failed - check logs above")
            
            if not FALLBACK_AVAILABLE:
                logger.info("\n💡 To enable fallback messaging:")
                logger.info("   pip install openai")
                logger.info("   export OPENAI_API_KEY=your_api_key")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)