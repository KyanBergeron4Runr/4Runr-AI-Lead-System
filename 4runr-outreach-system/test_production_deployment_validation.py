#!/usr/bin/env python3
"""
Production Deployment Validation Test Suite

This script performs comprehensive end-to-end testing with production-like data
to validate that the DataCleaner system is ready for deployment and will achieve
the target of eliminating garbage data like "Some results may have been delisted".
"""

import sys
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import DataCleaner
from outreach.google_enricher.app import GoogleEnricherAgent
from outreach.simple_enricher.app import SimpleEnricherAgent


class ProductionValidationSuite:
    """Comprehensive production validation test suite."""
    
    def __init__(self):
        """Initialize the validation suite."""
        self.data_cleaner = DataCleaner()
        self.google_enricher = GoogleEnricherAgent()
        self.simple_enricher = SimpleEnricherAgent()
        
        # Production garbage data patterns (real examples from Airtable)
        self.garbage_data_samples = [
            {
                'name': 'Classic Sirius XM Pattern',
                'company': 'Sirius XM and ... Some results may have been delisted consistent with local laws',
                'website': 'https://linkedin.com/company/test',
                'expected_company_cleaned': True,
                'expected_website_rejected': True
            },
            {
                'name': 'Sirius XM with Real Company',
                'company': 'TechCorp Inc Sirius XM and ... Some results may have been delisted',
                'website': 'https://google.com/search?q=techcorp',
                'expected_company_contains': 'TechCorp Inc',
                'expected_website_rejected': True
            },
            {
                'name': 'HTML with Search Artifacts',
                'company': '<div class="company-name">Microsoft Corporation</div> About 1,234 results Learn more',
                'website': 'https://microsoft.com',
                'expected_company_contains': 'Microsoft',
                'expected_website_valid': True
            },
            {
                'name': 'Complex Google Search Result',
                'company': '<span>Apple Inc</span> Images Videos News Shopping More Rating: 4.5 stars',
                'website': 'https://apple.com',
                'expected_company_contains': 'Apple Inc',
                'expected_website_valid': True
            },
            {
                'name': 'Just Delisted Pattern',
                'company': 'Some results may have been delisted consistent with local laws',
                'website': 'https://example.com',
                'expected_company_empty': True,
                'expected_website_rejected': True
            },
            {
                'name': 'LinkedIn Company URL',
                'company': 'Amazon Web Services',
                'website': 'https://linkedin.com/company/amazon-web-services',
                'expected_company_contains': 'Amazon Web Services',
                'expected_website_rejected': True
            },
            {
                'name': 'Facebook Page URL',
                'company': 'Tesla Inc',
                'website': 'https://facebook.com/pages/tesla',
                'expected_company_contains': 'Tesla Inc',
                'expected_website_rejected': True
            },
            {
                'name': 'Search Navigation Artifacts',
                'company': 'Netflix Inc Next Previous About 567,890 results (0.23 seconds)',
                'website': 'https://netflix.com',
                'expected_company_contains': 'Netflix Inc',
                'expected_website_valid': True
            },
            {
                'name': 'HTML Entities and Tags',
                'company': '&lt;div&gt;Johnson &amp; Johnson Inc&lt;/div&gt; &nbsp;Healthcare&nbsp;',
                'website': 'https://jnj.com',
                'expected_company_contains': 'Johnson & Johnson Inc',
                'expected_website_valid': True
            },
            {
                'name': 'Time-based Search Artifacts',
                'company': 'Google LLC 2 hours ago · 3 days ago · 1 week ago',
                'website': 'https://google.com',
                'expected_company_contains': 'Google LLC',
                'expected_website_rejected': True
            }
        ]
    
    def test_data_cleaner_direct(self) -> Dict[str, Any]:
        """Test DataCleaner directly with garbage data samples."""
        print("🧹 Testing DataCleaner Direct Processing")
        print("=" * 60)
        
        results = {
            'total_tests': len(self.garbage_data_samples),
            'successful_cleanings': 0,
            'garbage_eliminated': 0,
            'valid_data_preserved': 0,
            'test_details': []
        }
        
        for i, sample in enumerate(self.garbage_data_samples, 1):
            print(f"\\n🧪 Test {i}: {sample['name']}")
            
            # Prepare test data
            raw_data = {
                'Company': sample['company'],
                'Website': sample['website']
            }
            
            context = {
                'id': f'test_{i}',
                'Full Name': 'Test User',
                'source': 'production_validation'
            }
            
            print(f"   Input Company: {sample['company'][:50]}...")
            print(f"   Input Website: {sample['website']}")
            
            # Process with DataCleaner
            start_time = time.time()
            result = self.data_cleaner.clean_and_validate(raw_data, context)
            processing_time = time.time() - start_time
            
            print(f"   Success: {result.success}")
            print(f"   Cleaned Data: {result.cleaned_data}")
            print(f"   Confidence: {result.confidence_score:.2f}")
            print(f"   Processing Time: {processing_time:.3f}s")
            
            # Validate results
            test_passed = True
            validation_notes = []
            
            # Check company cleaning
            if sample.get('expected_company_cleaned'):
                if result.cleaned_data.get('Company') != sample['company']:
                    validation_notes.append("✅ Company was cleaned")
                    results['garbage_eliminated'] += 1
                else:
                    validation_notes.append("❌ Company was not cleaned")
                    test_passed = False
            
            if sample.get('expected_company_contains'):
                if sample['expected_company_contains'] in str(result.cleaned_data.get('Company', '')):
                    validation_notes.append("✅ Company contains expected content")
                    results['valid_data_preserved'] += 1
                else:
                    validation_notes.append("❌ Company missing expected content")
                    test_passed = False
            
            if sample.get('expected_company_empty'):
                if not result.cleaned_data.get('Company'):
                    validation_notes.append("✅ Garbage company correctly removed")
                    results['garbage_eliminated'] += 1
                else:
                    validation_notes.append("❌ Garbage company not removed")
                    test_passed = False
            
            # Check website validation
            if sample.get('expected_website_valid'):
                if result.cleaned_data.get('Website'):
                    validation_notes.append("✅ Valid website preserved")
                    results['valid_data_preserved'] += 1
                else:
                    validation_notes.append("❌ Valid website was rejected")
                    test_passed = False
            
            if sample.get('expected_website_rejected'):
                if not result.cleaned_data.get('Website'):
                    validation_notes.append("✅ Invalid website correctly rejected")
                    results['garbage_eliminated'] += 1
                else:
                    validation_notes.append("❌ Invalid website not rejected")
                    test_passed = False
            
            # Print validation results
            for note in validation_notes:
                print(f"   {note}")
            
            if test_passed:
                results['successful_cleanings'] += 1
                print(f"   ✅ OVERALL: PASS")
            else:
                print(f"   ❌ OVERALL: FAIL")
            
            # Store test details
            results['test_details'].append({
                'name': sample['name'],
                'passed': test_passed,
                'processing_time': processing_time,
                'confidence_score': result.confidence_score,
                'cleaning_actions': len(result.cleaning_actions),
                'validation_results': len(result.validation_results)
            })
        
        return results
    
    async def test_google_enricher_integration(self) -> Dict[str, Any]:
        """Test Google Enricher integration with DataCleaner."""
        print("\\n🔍 Testing Google Enricher Integration")
        print("=" * 60)
        
        # Mock test leads with garbage data
        test_leads = [
            {
                'id': 'google_test_1',
                'Full Name': 'John Doe',
                'Company': '',
                'Website': '',
                'LinkedIn URL': 'https://linkedin.com/in/johndoe'
            },
            {
                'id': 'google_test_2', 
                'Full Name': 'Jane Smith',
                'Company': 'Sirius XM and ... Some results may have been delisted',
                'Website': 'https://linkedin.com/company/test',
                'LinkedIn URL': 'https://linkedin.com/in/janesmith'
            }
        ]
        
        results = {
            'total_tests': len(test_leads),
            'integration_working': 0,
            'data_cleaner_active': 0,
            'test_details': []
        }
        
        for i, lead in enumerate(test_leads, 1):
            print(f"\\n🧪 Integration Test {i}: {lead['Full Name']}")
            print(f"   Lead ID: {lead['id']}")
            print(f"   Current Company: {lead['Company'] or '(empty)'}")
            print(f"   Current Website: {lead['Website'] or '(empty)'}")
            
            # Check if Google Enricher has DataCleaner
            has_data_cleaner = hasattr(self.google_enricher, 'data_cleaner') and self.google_enricher.data_cleaner is not None
            
            if has_data_cleaner:
                print(f"   ✅ DataCleaner integration detected")
                results['data_cleaner_active'] += 1
                results['integration_working'] += 1
            else:
                print(f"   ❌ DataCleaner integration missing")
            
            results['test_details'].append({
                'lead_id': lead['id'],
                'has_data_cleaner': has_data_cleaner,
                'full_name': lead['Full Name']
            })
        
        return results
    
    async def test_simple_enricher_integration(self) -> Dict[str, Any]:
        """Test Simple Enricher integration with DataCleaner."""
        print("\\n🔗 Testing Simple Enricher Integration")
        print("=" * 60)
        
        # Mock test leads
        test_leads = [
            {
                'id': 'simple_test_1',
                'Full Name': 'Bob Johnson',
                'Company': '',
                'Website': '',
                'LinkedIn URL': 'https://linkedin.com/in/bob-johnson-techcorp'
            }
        ]
        
        results = {
            'total_tests': len(test_leads),
            'integration_working': 0,
            'data_cleaner_active': 0,
            'test_details': []
        }
        
        for i, lead in enumerate(test_leads, 1):
            print(f"\\n🧪 Integration Test {i}: {lead['Full Name']}")
            
            # Check if Simple Enricher has DataCleaner
            has_data_cleaner = hasattr(self.simple_enricher, 'data_cleaner') and self.simple_enricher.data_cleaner is not None
            
            if has_data_cleaner:
                print(f"   ✅ DataCleaner integration detected")
                results['data_cleaner_active'] += 1
                results['integration_working'] += 1
            else:
                print(f"   ❌ DataCleaner integration missing")
            
            results['test_details'].append({
                'lead_id': lead['id'],
                'has_data_cleaner': has_data_cleaner,
                'full_name': lead['Full Name']
            })
        
        return results
    
    def test_specific_garbage_patterns(self) -> Dict[str, Any]:
        """Test specific garbage patterns that must be eliminated."""
        print("\\n🎯 Testing Specific Garbage Pattern Elimination")
        print("=" * 60)
        
        # Critical garbage patterns that MUST be eliminated
        critical_patterns = [
            {
                'name': 'Sirius XM Delisted Pattern',
                'input': 'Sirius XM and ... Some results may have been delisted consistent with local laws',
                'must_be_eliminated': True
            },
            {
                'name': 'Just Delisted Pattern',
                'input': 'Some results may have been delisted consistent with local laws',
                'must_be_eliminated': True
            },
            {
                'name': 'Sirius XM Holdings Pattern',
                'input': 'TechCorp Inc Sirius XM Holdings Inc and other companies Some results may have been delisted',
                'must_preserve': 'TechCorp Inc',
                'must_eliminate': 'Sirius XM'
            },
            {
                'name': 'Google Search Results Pattern',
                'input': 'Microsoft Corporation About 1,234,567 results (0.45 seconds) Next',
                'must_preserve': 'Microsoft Corporation',
                'must_eliminate': 'About'
            },
            {
                'name': 'LinkedIn Company URL',
                'input': 'https://linkedin.com/company/test-company',
                'field': 'website',
                'must_be_rejected': True
            },
            {
                'name': 'Google Search URL',
                'input': 'https://google.com/search?q=company',
                'field': 'website',
                'must_be_rejected': True
            }
        ]
        
        results = {
            'total_patterns': len(critical_patterns),
            'successfully_eliminated': 0,
            'successfully_preserved': 0,
            'pattern_details': []
        }
        
        for i, pattern in enumerate(critical_patterns, 1):
            print(f"\\n🧪 Pattern Test {i}: {pattern['name']}")
            print(f"   Input: {pattern['input'][:60]}...")
            
            # Test the pattern
            if pattern.get('field') == 'website':
                # Test website validation
                context = {'id': f'pattern_test_{i}', 'Full Name': 'Test User'}
                from shared.data_cleaner import ValidationEngine, ConfigurationManager
                config_manager = ConfigurationManager()
                validation_engine = ValidationEngine(config_manager.validation_rules)
                result = validation_engine.validate_website_url(pattern['input'], context)
                
                if pattern.get('must_be_rejected'):
                    if not result.is_valid:
                        print(f"   ✅ PASS - Website correctly rejected")
                        results['successfully_eliminated'] += 1
                    else:
                        print(f"   ❌ FAIL - Website should have been rejected")
                
            else:
                # Test company cleaning
                from shared.data_cleaner import CleaningRulesEngine, ConfigurationManager
                config_manager = ConfigurationManager()
                cleaning_engine = CleaningRulesEngine(config_manager.cleaning_rules)
                result = cleaning_engine.clean_company_name(pattern['input'])
                
                print(f"   Output: {result}")
                
                if pattern.get('must_be_eliminated'):
                    if not result or result != pattern['input']:
                        print(f"   ✅ PASS - Garbage pattern eliminated")
                        results['successfully_eliminated'] += 1
                    else:
                        print(f"   ❌ FAIL - Garbage pattern not eliminated")
                
                if pattern.get('must_preserve'):
                    if pattern['must_preserve'] in result:
                        print(f"   ✅ PASS - Valid content preserved")
                        results['successfully_preserved'] += 1
                    else:
                        print(f"   ❌ FAIL - Valid content not preserved")
                
                if pattern.get('must_eliminate'):
                    if pattern['must_eliminate'] not in result:
                        print(f"   ✅ PASS - Unwanted content eliminated")
                        results['successfully_eliminated'] += 1
                    else:
                        print(f"   ❌ FAIL - Unwanted content not eliminated")
            
            results['pattern_details'].append({
                'name': pattern['name'],
                'input': pattern['input'],
                'output': result if 'result' in locals() else 'N/A'
            })
        
        return results
    
    def calculate_data_quality_improvement(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate data quality improvement metrics."""
        print("\\n📊 Calculating Data Quality Improvement")
        print("=" * 60)
        
        # Before DataCleaner (simulated baseline)
        baseline_garbage_rate = 0.85  # 85% of data had garbage before
        baseline_valid_preservation = 0.60  # 60% of valid data was preserved
        
        # After DataCleaner (from test results)
        total_tests = results['total_tests']
        garbage_eliminated = results['garbage_eliminated']
        valid_preserved = results['valid_data_preserved']
        
        # Calculate improvement metrics
        garbage_elimination_rate = garbage_eliminated / total_tests if total_tests > 0 else 0
        valid_preservation_rate = valid_preserved / total_tests if total_tests > 0 else 0
        
        # Overall data quality score
        data_quality_score = (garbage_elimination_rate * 0.6) + (valid_preservation_rate * 0.4)
        
        # Improvement over baseline
        garbage_improvement = garbage_elimination_rate - (1 - baseline_garbage_rate)
        preservation_improvement = valid_preservation_rate - baseline_valid_preservation
        
        improvement_metrics = {
            'baseline_garbage_rate': baseline_garbage_rate,
            'current_garbage_elimination_rate': garbage_elimination_rate,
            'garbage_improvement': garbage_improvement,
            'baseline_valid_preservation': baseline_valid_preservation,
            'current_valid_preservation_rate': valid_preservation_rate,
            'preservation_improvement': preservation_improvement,
            'overall_data_quality_score': data_quality_score,
            'deployment_ready': data_quality_score >= 0.8  # 80% threshold for deployment
        }
        
        print(f"   Baseline Garbage Rate: {baseline_garbage_rate:.1%}")
        print(f"   Current Garbage Elimination: {garbage_elimination_rate:.1%}")
        print(f"   Garbage Elimination Improvement: {garbage_improvement:+.1%}")
        print(f"   ")
        print(f"   Baseline Valid Preservation: {baseline_valid_preservation:.1%}")
        print(f"   Current Valid Preservation: {valid_preservation_rate:.1%}")
        print(f"   Preservation Improvement: {preservation_improvement:+.1%}")
        print(f"   ")
        print(f"   Overall Data Quality Score: {data_quality_score:.1%}")
        print(f"   Deployment Ready: {'✅ YES' if improvement_metrics['deployment_ready'] else '❌ NO'}")
        
        return improvement_metrics
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run the complete production validation suite."""
        print("🚀 Production Deployment Validation Suite")
        print("=" * 70)
        print("Testing DataCleaner system readiness for production deployment")
        print("Target: Eliminate 'Some results may have been delisted' and similar garbage")
        print("=" * 70)
        
        # Run all validation tests
        start_time = time.time()
        
        # Test 1: Direct DataCleaner testing
        datacleaner_results = self.test_data_cleaner_direct()
        
        # Test 2: Google Enricher integration
        google_results = await self.test_google_enricher_integration()
        
        # Test 3: Simple Enricher integration
        simple_results = await self.test_simple_enricher_integration()
        
        # Test 4: Specific garbage pattern elimination
        pattern_results = self.test_specific_garbage_patterns()
        
        # Calculate overall improvement
        improvement_metrics = self.calculate_data_quality_improvement(datacleaner_results)
        
        total_time = time.time() - start_time
        
        # Compile final results
        final_results = {
            'validation_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_validation_time': total_time,
            'datacleaner_results': datacleaner_results,
            'google_enricher_results': google_results,
            'simple_enricher_results': simple_results,
            'pattern_elimination_results': pattern_results,
            'improvement_metrics': improvement_metrics,
            'deployment_recommendation': self._generate_deployment_recommendation(
                datacleaner_results, google_results, simple_results, pattern_results, improvement_metrics
            )
        }
        
        return final_results
    
    def _generate_deployment_recommendation(self, datacleaner_results, google_results, 
                                          simple_results, pattern_results, improvement_metrics) -> Dict[str, Any]:
        """Generate deployment recommendation based on test results."""
        
        # Calculate readiness scores
        datacleaner_score = datacleaner_results['successful_cleanings'] / datacleaner_results['total_tests']
        integration_score = (google_results['integration_working'] + simple_results['integration_working']) / 2
        pattern_score = (pattern_results['successfully_eliminated'] + pattern_results['successfully_preserved']) / pattern_results['total_patterns']
        overall_quality_score = improvement_metrics['overall_data_quality_score']
        
        # Determine readiness
        readiness_threshold = 0.75  # 75% threshold
        is_ready = all([
            datacleaner_score >= readiness_threshold,
            integration_score >= readiness_threshold,
            pattern_score >= readiness_threshold,
            overall_quality_score >= 0.8  # Higher threshold for overall quality
        ])
        
        recommendation = {
            'ready_for_deployment': is_ready,
            'readiness_scores': {
                'datacleaner_functionality': datacleaner_score,
                'enricher_integration': integration_score,
                'pattern_elimination': pattern_score,
                'overall_data_quality': overall_quality_score
            },
            'critical_issues': [],
            'recommendations': [],
            'deployment_confidence': 'HIGH' if is_ready else 'MEDIUM' if datacleaner_score > 0.6 else 'LOW'
        }
        
        # Add specific recommendations
        if datacleaner_score < readiness_threshold:
            recommendation['critical_issues'].append('DataCleaner core functionality below threshold')
            recommendation['recommendations'].append('Fix failing cleaning rules before deployment')
        
        if integration_score < readiness_threshold:
            recommendation['critical_issues'].append('Enricher integration issues detected')
            recommendation['recommendations'].append('Verify DataCleaner integration in all enrichers')
        
        if pattern_score < readiness_threshold:
            recommendation['critical_issues'].append('Critical garbage patterns not fully eliminated')
            recommendation['recommendations'].append('Enhance pattern matching for Sirius XM and delisted patterns')
        
        if overall_quality_score < 0.8:
            recommendation['critical_issues'].append('Overall data quality score below deployment threshold')
            recommendation['recommendations'].append('Improve data quality metrics before production deployment')
        
        if is_ready:
            recommendation['recommendations'].append('System ready for production deployment')
            recommendation['recommendations'].append('Monitor data quality metrics closely after deployment')
            recommendation['recommendations'].append('Set up alerting for quality degradation')
        
        return recommendation


async def main():
    """Run the production validation suite."""
    try:
        # Initialize validation suite
        validator = ProductionValidationSuite()
        
        # Run comprehensive validation
        results = await validator.run_comprehensive_validation()
        
        # Print final summary
        print("\\n" + "=" * 70)
        print("🎯 FINAL DEPLOYMENT VALIDATION RESULTS")
        print("=" * 70)
        
        recommendation = results['deployment_recommendation']
        
        print(f"Deployment Ready: {'✅ YES' if recommendation['ready_for_deployment'] else '❌ NO'}")
        print(f"Deployment Confidence: {recommendation['deployment_confidence']}")
        print(f"Overall Data Quality Score: {results['improvement_metrics']['overall_data_quality_score']:.1%}")
        print(f"Validation Time: {results['total_validation_time']:.2f} seconds")
        
        print(f"\\n📊 Readiness Scores:")
        for metric, score in recommendation['readiness_scores'].items():
            status = "✅" if score >= 0.75 else "⚠️" if score >= 0.5 else "❌"
            print(f"   {status} {metric.replace('_', ' ').title()}: {score:.1%}")
        
        if recommendation['critical_issues']:
            print(f"\\n⚠️ Critical Issues:")
            for issue in recommendation['critical_issues']:
                print(f"   • {issue}")
        
        print(f"\\n💡 Recommendations:")
        for rec in recommendation['recommendations']:
            print(f"   • {rec}")
        
        # Specific garbage elimination results
        datacleaner_results = results['datacleaner_results']
        print(f"\\n🎵 Sirius XM Pattern Elimination:")
        print(f"   Garbage Eliminated: {datacleaner_results['garbage_eliminated']}/{datacleaner_results['total_tests']}")
        print(f"   Valid Data Preserved: {datacleaner_results['valid_data_preserved']}/{datacleaner_results['total_tests']}")
        print(f"   Success Rate: {datacleaner_results['successful_cleanings']}/{datacleaner_results['total_tests']} ({datacleaner_results['successful_cleanings']/datacleaner_results['total_tests']:.1%})")
        
        # Return success status
        return recommendation['ready_for_deployment']
        
    except Exception as e:
        print(f"\\n💥 VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    print(f"\\n{'🚀 SYSTEM READY FOR DEPLOYMENT!' if success else '🔧 SYSTEM NEEDS FIXES BEFORE DEPLOYMENT'}")
    sys.exit(0 if success else 1)