#!/usr/bin/env python3
"""
Comprehensive integration test for the fallback messaging system.

This test validates that the fallback messaging system works correctly
with the existing 4Runr lead processing pipeline and can handle various
lead scenarios with limited data.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from enricher.fallback_message_generator import (
        FallbackMessageGenerator, 
        generate_fallback_message, 
        should_use_fallback_messaging
    )
    FALLBACK_AVAILABLE = True
except ImportError as e:
    FALLBACK_AVAILABLE = False
    import_error = str(e)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('fallback-integration-test')

def test_fallback_decision_logic():
    """Test the decision logic for when to use fallback messaging."""
    
    logger.info("🧪 Testing fallback decision logic")
    
    if not FALLBACK_AVAILABLE:
        logger.error(f"❌ Fallback system not available: {import_error}")
        return False
    
    # Test cases for fallback decision
    test_cases = [
        {
            'name': 'Complete Lead (Should NOT use fallback)',
            'data': {
                'full_name': 'John Smith',
                'email': 'john@techcorp.com',
                'email_confidence': 'real',
                'Business_Type': 'SaaS',
                'Business_Traits': ['B2B', 'Technical Team'],
                'Pain_Points': ['Lead generation'],
                'Strategic_Insight': 'Great candidate for automation tools',
                'website': 'https://techcorp.com',
                'scraped_content': 'Company content here...'
            },
            'should_fallback': False
        },
        {
            'name': 'Missing Business Intelligence (Should use fallback)',
            'data': {
                'full_name': 'Jane Doe',
                'email': 'jane@startup.io',
                'email_confidence': 'real',
                'Business_Type': 'Unknown',
                'Business_Traits': [],
                'website': None
            },
            'should_fallback': True
        },
        {
            'name': 'Low Email Confidence (Should NOT use fallback)',
            'data': {
                'full_name': 'Mike Johnson',
                'email': 'mike@company.com',
                'email_confidence': 'low',
                'Business_Type': 'Unknown'
            },
            'should_fallback': False
        },
        {
            'name': 'Pattern Email with Missing Data (Should use fallback)',
            'data': {
                'full_name': 'Sarah Wilson',
                'email': 'sarah@business.com',
                'email_confidence': 'pattern',
                'Business_Type': 'Unknown',
                'Business_Traits': []
            },
            'should_fallback': True
        }
    ]
    
    passed_tests = 0
    
    for test_case in test_cases:
        logger.info(f"   Testing: {test_case['name']}")
        
        try:
            decision = should_use_fallback_messaging(test_case['data'])
            
            should_fallback = decision.get('should_use_fallback', False)
            expected = test_case['should_fallback']
            
            if should_fallback == expected:
                logger.info(f"   ✅ Correct decision: {should_fallback}")
                logger.info(f"      Reasons: {', '.join(decision.get('reasons', [])[:2])}...")
                passed_tests += 1
            else:
                logger.error(f"   ❌ Wrong decision: got {should_fallback}, expected {expected}")
                logger.error(f"      Reasons: {', '.join(decision.get('reasons', [])[:2])}...")
        
        except Exception as e:
            logger.error(f"   ❌ Decision test failed: {str(e)}")
    
    logger.info(f"✅ Decision logic tests: {passed_tests}/{len(test_cases)} passed")
    return passed_tests == len(test_cases)

def test_template_message_generation():
    """Test template-based message generation for various lead types."""
    
    logger.info("\\n🧪 Testing template-based message generation")
    
    if not FALLBACK_AVAILABLE:
        logger.error(f"❌ Fallback system not available: {import_error}")
        return False
    
    # Test scenarios representing different industries and data availability
    test_scenarios = [
        {
            'name': 'Tech Company with Full Context',
            'data': {
                'full_name': 'Alex Rodriguez',
                'email': 'alex@techsolutions.com',
                'company_name': 'TechSolutions Inc',
                'domain': 'techsolutions.com',
                'email_confidence': 'real',
                'Business_Type': 'Unknown',
                'Business_Traits': []
            },
            'expected_keywords': ['tech', 'automate', 'processes']
        },
        {
            'name': 'Marketing Agency',
            'data': {
                'full_name': 'Jennifer Kim',
                'email': 'jennifer@creativemarketingagency.co',
                'domain': 'creativemarketingagency.co',
                'email_confidence': 'pattern',
                'Business_Type': 'Unknown'
            },
            'expected_keywords': ['agency', 'clients', 'campaigns']
        },
        {
            'name': 'Healthcare Organization',
            'data': {
                'full_name': 'Dr. Lisa Chen',
                'email': 'lisa@healthcaresolutions.org',
                'domain': 'healthcaresolutions.org',
                'email_confidence': 'real',
                'Business_Type': 'Unknown'
            },
            'expected_keywords': ['healthcare', 'administrative', 'efficiency']
        },
        {
            'name': 'Generic Business',
            'data': {
                'full_name': 'Michael Davis',
                'email': 'michael@businesscorp.com',
                'company_name': 'Business Corp',
                'email_confidence': 'pattern',
                'Business_Type': 'Unknown'
            },
            'expected_keywords': ['business', 'automate', 'workflows']
        },
        {
            'name': 'Minimal Data Lead',
            'data': {
                'full_name': 'Robert Thompson',
                'email': 'robert@unknowndomain.biz',
                'email_confidence': 'real',
                'Business_Type': 'Unknown'
            },
            'expected_keywords': ['business', 'automation']
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\\n   Scenario {i}: {scenario['name']}")
        logger.info(f"   Email: {scenario['data']['email']}")
        
        try:
            # Generate fallback message using template-based approach
            result = generate_fallback_message(scenario['data'], use_ai=False)
            
            # Analyze results
            test_result = {
                'name': scenario['name'],
                'success': result.get('generation_success', False),
                'message': result.get('message', ''),
                'confidence': result.get('confidence', 'none'),
                'method': result.get('generation_method', ''),
                'passed': False
            }
            
            # Evaluate message quality
            if result.get('generation_success'):
                message = result.get('message', '').lower()
                
                # Check for expected keywords
                keyword_matches = sum(1 for keyword in scenario['expected_keywords'] if keyword in message)
                
                # Check basic message structure
                has_name = scenario['data']['full_name'].split()[0].lower() in message
                has_greeting = any(greeting in message for greeting in ['hi ', 'hello '])
                has_cta = any(phrase in message for phrase in ['interested', 'open to', 'would you'])
                has_signature = '4runr' in message.lower()
                
                # Calculate quality score
                structure_score = sum([has_name, has_greeting, has_cta, has_signature])
                content_score = min(keyword_matches, 2)  # Max 2 points for keywords
                
                total_score = structure_score + content_score
                
                if total_score >= 4:
                    test_result['passed'] = True
                    logger.info(f"   ✅ High-quality message generated")
                elif total_score >= 3:
                    test_result['passed'] = True
                    logger.info(f"   ✅ Acceptable message generated")
                else:
                    logger.warning(f"   ⚠️ Low-quality message (score: {total_score}/6)")
                
                # Log quality details
                logger.info(f"   📊 Quality Score: {total_score}/6")
                logger.info(f"   📊 Structure: {structure_score}/4 (name: {has_name}, greeting: {has_greeting}, cta: {has_cta}, signature: {has_signature})")
                logger.info(f"   📊 Content: {content_score}/2 (keywords: {keyword_matches}/{len(scenario['expected_keywords'])})")
                logger.info(f"   📊 Confidence: {test_result['confidence']}")
                logger.info(f"   📊 Method: {test_result['method']}")
                
                # Show message preview
                preview = result.get('message', '')[:100] + "..." if len(result.get('message', '')) > 100 else result.get('message', '')
                logger.info(f"   📝 Preview: {preview}")
            else:
                logger.error(f"   ❌ Message generation failed: {result.get('generation_error', 'Unknown error')}")
            
            results.append(test_result)
            
        except Exception as e:
            logger.error(f"   ❌ Scenario failed with exception: {str(e)}")
            results.append({
                'name': scenario['name'],
                'success': False,
                'error': str(e),
                'passed': False
            })
    
    # Summary
    passed_tests = sum(1 for r in results if r['passed'])
    total_tests = len(results)
    
    logger.info(f"\\n📊 Template Message Generation Results:")
    logger.info("=" * 50)
    logger.info(f"✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    for result in results:
        status = "✅" if result['passed'] else "❌"
        confidence = result.get('confidence', 'none')
        logger.info(f"{status} {result['name']}: {confidence} confidence")
    
    return passed_tests >= total_tests * 0.8  # 80% pass rate

def test_integration_with_existing_pipeline():
    """Test integration with existing 4Runr pipeline data structures."""
    
    logger.info("\\n🧪 Testing integration with existing pipeline")
    
    if not FALLBACK_AVAILABLE:
        logger.error(f"❌ Fallback system not available: {import_error}")
        return False
    
    # Simulate lead data as it would come from the existing pipeline
    pipeline_lead_data = {
        'full_name': 'Emma Watson',
        'email': 'emma@startupxyz.com',
        'company_name': 'StartupXYZ',
        'domain': 'startupxyz.com',
        'website': None,  # Website discovery failed
        'scraped_content': None,  # No content scraped
        'Business_Type': 'Unknown',  # Enrichment failed
        'Business_Traits': [],  # No traits extracted
        'Pain_Points': [],  # No pain points identified
        'Strategic_Insight': None,  # No insights available
        'email_confidence': 'pattern',  # Pattern-based email
        'Response_Notes': None,  # No enrichment notes
        'Enrichment_Status': 'Failed - No Website'
    }
    
    try:
        logger.info("   Testing fallback decision...")
        
        # Test decision logic
        decision = should_use_fallback_messaging(pipeline_lead_data)
        
        if decision.get('should_use_fallback'):
            logger.info("   ✅ Correctly identified need for fallback messaging")
            logger.info(f"      Reasons: {', '.join(decision.get('reasons', [])[:3])}...")
        else:
            logger.error("   ❌ Failed to identify need for fallback messaging")
            return False
        
        logger.info("   Testing message generation...")
        
        # Test message generation
        result = generate_fallback_message(pipeline_lead_data, use_ai=False)
        
        if result.get('generation_success'):
            logger.info("   ✅ Successfully generated fallback message")
            
            # Validate result structure matches expected pipeline format
            expected_fields = [
                'message', 'confidence', 'used_fallback', 'fallback_reason',
                'generation_success', 'generated_at', 'lead_name', 'company_name',
                'generation_method'
            ]
            
            missing_fields = [field for field in expected_fields if field not in result]
            
            if not missing_fields:
                logger.info("   ✅ Result structure matches pipeline expectations")
            else:
                logger.warning(f"   ⚠️ Missing fields in result: {missing_fields}")
            
            # Validate message content
            message = result.get('message', '')
            if len(message) > 50 and 'Emma' in message and '4Runr' in message:
                logger.info("   ✅ Message content is appropriate")
            else:
                logger.warning("   ⚠️ Message content may be inadequate")
            
            # Log integration details
            logger.info(f"   📊 Used Fallback: {result.get('used_fallback')}")
            logger.info(f"   📊 Confidence: {result.get('confidence')}")
            logger.info(f"   📊 Method: {result.get('generation_method')}")
            logger.info(f"   📊 Fallback Reason: {result.get('fallback_reason')}")
            
            return True
        else:
            logger.error(f"   ❌ Message generation failed: {result.get('generation_error')}")
            return False
    
    except Exception as e:
        logger.error(f"   ❌ Integration test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling for various failure scenarios."""
    
    logger.info("\\n🧪 Testing error handling")
    
    if not FALLBACK_AVAILABLE:
        logger.error(f"❌ Fallback system not available: {import_error}")
        return False
    
    error_test_cases = [
        {
            'name': 'Missing Name',
            'data': {'email': 'test@example.com', 'email_confidence': 'real'},
            'should_fail': True
        },
        {
            'name': 'Missing Email',
            'data': {'full_name': 'John Smith', 'email_confidence': 'real'},
            'should_fail': True
        },
        {
            'name': 'Invalid Email Format',
            'data': {'full_name': 'John Smith', 'email': 'invalid-email', 'email_confidence': 'real'},
            'should_fail': True
        },
        {
            'name': 'Empty Data',
            'data': {},
            'should_fail': True
        },
        {
            'name': 'Valid Minimal Data',
            'data': {'full_name': 'Jane Doe', 'email': 'jane@company.com', 'email_confidence': 'real'},
            'should_fail': False
        }
    ]
    
    passed_tests = 0
    
    for test_case in error_test_cases:
        logger.info(f"   Testing: {test_case['name']}")
        
        try:
            result = generate_fallback_message(test_case['data'], use_ai=False)
            
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
                    logger.error(f"   ❌ Should have succeeded but failed: {result.get('generation_error')}")
        
        except Exception as e:
            if test_case['should_fail']:
                logger.info(f"   ✅ Correctly failed with exception: {str(e)}")
                passed_tests += 1
            else:
                logger.error(f"   ❌ Unexpected exception: {str(e)}")
    
    logger.info(f"✅ Error handling tests: {passed_tests}/{len(error_test_cases)} passed")
    return passed_tests == len(error_test_cases)

def run_comprehensive_test():
    """Run all fallback messaging integration tests."""
    
    logger.info("🚀 Starting Comprehensive Fallback Messaging Integration Tests")
    logger.info("=" * 80)
    
    # Run all tests
    tests = [
        ("Fallback Decision Logic", test_fallback_decision_logic),
        ("Template Message Generation", test_template_message_generation),
        ("Pipeline Integration", test_integration_with_existing_pipeline),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    logger.info("\\n📊 Integration Test Results Summary:")
    logger.info("=" * 60)
    
    passed_tests = 0
    total_tests = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if passed:
            passed_tests += 1
    
    logger.info(f"\\n📈 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All fallback messaging integration tests passed!")
        logger.info("✅ Fallback system is ready for production integration")
        
        logger.info("\\n📋 Integration Summary:")
        logger.info("   • Template-based messaging works without AI dependency")
        logger.info("   • Decision logic correctly identifies fallback scenarios")
        logger.info("   • Message generation handles various industry types")
        logger.info("   • Error handling is robust and graceful")
        logger.info("   • Integration with existing pipeline data structures is seamless")
        
        return True
    else:
        logger.warning("⚠️ Some integration tests failed - check logs above")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        
        if success:
            logger.info("\\n🎯 Next Steps:")
            logger.info("   1. Integrate fallback messaging into the main pipeline")
            logger.info("   2. Update message generator to use fallback when needed")
            logger.info("   3. Add fallback tracking to Airtable fields")
            logger.info("   4. Test with real lead data")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"❌ Integration test execution failed: {str(e)}")
        sys.exit(1)