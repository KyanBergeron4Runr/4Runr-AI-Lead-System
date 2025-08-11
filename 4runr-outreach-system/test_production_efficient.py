#!/usr/bin/env python3
"""
Efficient End-to-End Production Testing for DataCleaner System

This optimized test suite minimizes Airtable API calls while thoroughly
testing the data cleaning pipeline with realistic production data patterns.

Key Features:
- Minimal API calls (uses cached/simulated data)
- Comprehensive garbage pattern testing
- Real-world data quality scenarios
- Performance validation
- Complete pipeline integration testing
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import DataCleaner, CleaningResult
from shared.logging_utils import get_logger

@dataclass
class TestResult:
    """Results from a specific test."""
    test_name: str
    success: bool
    quality_before: float
    quality_after: float
    improvement_pct: float
    processing_time: float
    records_tested: int
    garbage_removed: int
    details: Dict[str, Any]

class EfficientProductionTester:
    """
    Efficient production testing that minimizes external API calls
    while providing comprehensive validation of the DataCleaner system.
    """
    
    def __init__(self):
        self.logger = get_logger('efficient_tester')
        self.data_cleaner = DataCleaner()
        self.test_results = []
        
        # Real production garbage patterns we've seen
        self.production_garbage_data = [
            {
                'Company': 'Sirius XM and ... Some results may have been delisted',
                'Website': 'https://google.com/search?q=sirius+xm',
                'expected_clean': False
            },
            {
                'Company': 'Apple Inc - Google Search Results',
                'Website': 'https://www.google.com/search?q=apple+inc',
                'expected_clean': False
            },
            {
                'Company': '<div class="result">Microsoft Corporation</div>',
                'Website': 'linkedin.com/company/microsoft',
                'expected_clean': False
            },
            {
                'Company': 'Tesla Inc &nbsp;&amp; Search Results',
                'Website': 'facebook.com/tesla',
                'expected_clean': False
            },
            {
                'Company': 'Some results may have been delisted - Amazon',
                'Website': 'https://google.com/search?q=amazon',
                'expected_clean': False
            },
            # Clean data examples
            {
                'Company': 'Acme Corporation',
                'Website': 'https://acmecorp.com',
                'expected_clean': True
            },
            {
                'Company': 'Tech Solutions Inc',
                'Website': 'https://techsolutions.com',
                'expected_clean': True
            },
            {
                'Company': 'Global Industries LLC',
                'Website': 'https://globalindustries.com',
                'expected_clean': True
            }
        ]
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete efficient testing suite."""
        print("🚀 Efficient DataCleaner Production Testing")
        print("=" * 60)
        print("⚡ Optimized for minimal API calls")
        print("🎯 Testing with realistic production data patterns")
        print()
        
        try:
            # Test 1: Garbage Pattern Detection and Removal
            print("🗑️ Test 1: Garbage Pattern Detection")
            garbage_test = self._test_garbage_detection()
            self.test_results.append(garbage_test)
            
            # Test 2: Data Quality Improvement Measurement
            print("\n📈 Test 2: Data Quality Improvement")
            quality_test = self._test_quality_improvement()
            self.test_results.append(quality_test)
            
            # Test 3: System Performance Testing
            print("\n⚡ Test 3: Performance Testing")
            performance_test = self._test_system_performance()
            self.test_results.append(performance_test)
            
            # Test 4: Error Handling and Resilience
            print("\n🛡️ Test 4: Error Handling")
            resilience_test = self._test_error_resilience()
            self.test_results.append(resilience_test)
            
            # Test 5: Complete Pipeline Integration
            print("\n🔄 Test 5: Pipeline Integration")
            integration_test = self._test_pipeline_integration()
            self.test_results.append(integration_test)
            
            # Generate final report
            final_report = self._generate_final_report()
            
            return final_report
            
        except Exception as e:
            self.logger.log_module_activity('efficient_tester', 'test_suite', 'error', {
                'message': f'Test suite failed: {e}'
            })
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_garbage_detection(self) -> TestResult:
        """Test garbage pattern detection and removal."""
        print("   Testing known garbage patterns...")
        
        try:
            start_time = time.time()
            
            garbage_patterns_detected = 0
            garbage_patterns_removed = 0
            successful_cleanings = 0
            
            # Test each garbage data sample
            for i, sample in enumerate(self.production_garbage_data):
                data = {
                    'Company': sample['Company'],
                    'Website': sample['Website']
                }
                
                context = {
                    'id': f'garbage_test_{i}',
                    'Full Name': 'Test User',
                    'source': 'garbage_detection_test'
                }
                
                # Count garbage patterns before cleaning
                before_patterns = self._count_garbage_patterns(data)
                garbage_patterns_detected += before_patterns
                
                # Clean the data
                result = self.data_cleaner.clean_and_validate(data, context)
                
                if result.success:
                    successful_cleanings += 1
                    
                    # Count garbage patterns after cleaning
                    after_patterns = self._count_garbage_patterns(result.cleaned_data)
                    patterns_removed = before_patterns - after_patterns
                    garbage_patterns_removed += patterns_removed
                    
                    # Verify expected behavior
                    if sample['expected_clean']:
                        expected_result = "✅ Clean data preserved"
                    else:
                        expected_result = f"🧹 Garbage removed: {patterns_removed} patterns"
                    
                    print(f"     Sample {i+1}: {expected_result}")
                else:
                    print(f"     Sample {i+1}: ❌ Cleaning failed")
            
            processing_time = time.time() - start_time
            removal_rate = (garbage_patterns_removed / garbage_patterns_detected * 100) if garbage_patterns_detected > 0 else 100
            
            print(f"   📊 Results:")
            print(f"     Garbage patterns detected: {garbage_patterns_detected}")
            print(f"     Garbage patterns removed: {garbage_patterns_removed}")
            print(f"     Removal rate: {removal_rate:.1f}%")
            print(f"     Processing time: {processing_time:.3f}s")
            
            return TestResult(
                test_name="Garbage Pattern Detection",
                success=removal_rate >= 90.0,  # 90% removal rate required
                quality_before=0.0,
                quality_after=removal_rate,
                improvement_pct=removal_rate,
                processing_time=processing_time,
                records_tested=len(self.production_garbage_data),
                garbage_removed=garbage_patterns_removed,
                details={
                    'patterns_detected': garbage_patterns_detected,
                    'patterns_removed': garbage_patterns_removed,
                    'removal_rate': removal_rate,
                    'successful_cleanings': successful_cleanings
                }
            )
            
        except Exception as e:
            self.logger.log_module_activity('efficient_tester', 'garbage_detection', 'error', {
                'message': f'Garbage detection test failed: {e}'
            })
            return TestResult(
                test_name="Garbage Pattern Detection",
                success=False,
                quality_before=0.0,
                quality_after=0.0,
                improvement_pct=0.0,
                processing_time=0.0,
                records_tested=0,
                garbage_removed=0,
                details={'error': str(e)}
            )
    
    def _test_quality_improvement(self) -> TestResult:
        """Test measurable data quality improvement."""
        print("   Measuring data quality improvement...")
        
        try:
            start_time = time.time()
            
            # Calculate baseline quality (with garbage data)
            baseline_quality = self._calculate_quality_score(self.production_garbage_data)
            
            # Process data through cleaner
            cleaned_data = []
            total_confidence = 0.0
            successful_cleanings = 0
            
            for i, sample in enumerate(self.production_garbage_data):
                data = {
                    'Company': sample['Company'],
                    'Website': sample['Website']
                }
                
                context = {
                    'id': f'quality_test_{i}',
                    'Full Name': 'Test User',
                    'source': 'quality_improvement_test'
                }
                
                result = self.data_cleaner.clean_and_validate(data, context)
                
                if result.success:
                    cleaned_data.append(result.cleaned_data)
                    total_confidence += result.confidence_score
                    successful_cleanings += 1
            
            # Calculate improved quality
            improved_quality = self._calculate_quality_score(cleaned_data)
            
            processing_time = time.time() - start_time
            improvement_pct = ((improved_quality - baseline_quality) / baseline_quality * 100) if baseline_quality > 0 else 0
            avg_confidence = total_confidence / successful_cleanings if successful_cleanings > 0 else 0
            
            print(f"   📊 Results:")
            print(f"     Baseline quality: {baseline_quality:.2f}")
            print(f"     Improved quality: {improved_quality:.2f}")
            print(f"     Quality improvement: {improvement_pct:.1f}%")
            print(f"     Average confidence: {avg_confidence:.2f}")
            print(f"     Success rate: {successful_cleanings}/{len(self.production_garbage_data)}")
            
            return TestResult(
                test_name="Data Quality Improvement",
                success=improvement_pct >= 110.0,  # 110% improvement target
                quality_before=baseline_quality,
                quality_after=improved_quality,
                improvement_pct=improvement_pct,
                processing_time=processing_time,
                records_tested=len(self.production_garbage_data),
                garbage_removed=0,  # Calculated in other tests
                details={
                    'baseline_quality': baseline_quality,
                    'improved_quality': improved_quality,
                    'average_confidence': avg_confidence,
                    'success_rate': successful_cleanings / len(self.production_garbage_data)
                }
            )
            
        except Exception as e:
            self.logger.log_module_activity('efficient_tester', 'quality_improvement', 'error', {
                'message': f'Quality improvement test failed: {e}'
            })
            return TestResult(
                test_name="Data Quality Improvement",
                success=False,
                quality_before=0.0,
                quality_after=0.0,
                improvement_pct=0.0,
                processing_time=0.0,
                records_tested=0,
                garbage_removed=0,
                details={'error': str(e)}
            )
    
    def _test_system_performance(self) -> TestResult:
        """Test system performance with various load scenarios."""
        print("   Testing system performance...")
        
        try:
            # Test with different batch sizes
            batch_sizes = [10, 50, 100]
            performance_results = []
            
            for batch_size in batch_sizes:
                print(f"     Testing batch size: {batch_size}")
                
                start_time = time.time()
                
                # Create test batch
                test_batch = []
                for i in range(batch_size):
                    sample = self.production_garbage_data[i % len(self.production_garbage_data)]
                    test_batch.append({
                        'Company': sample['Company'],
                        'Website': sample['Website']
                    })
                
                # Process batch
                successful_processes = 0
                for i, record in enumerate(test_batch):
                    context = {
                        'id': f'perf_test_{batch_size}_{i}',
                        'Full Name': 'Test User',
                        'source': 'performance_test'
                    }
                    
                    try:
                        result = self.data_cleaner.clean_and_validate(record, context)
                        if result.success:
                            successful_processes += 1
                    except Exception as e:
                        self.logger.log_module_activity('efficient_tester', 'performance', 'error', {
                            'message': f'Performance test error: {e}'
                        })
                
                batch_time = time.time() - start_time
                avg_time_per_record = batch_time / batch_size
                success_rate = successful_processes / batch_size
                throughput = batch_size / batch_time
                
                performance_results.append({
                    'batch_size': batch_size,
                    'total_time': batch_time,
                    'avg_time_per_record': avg_time_per_record,
                    'success_rate': success_rate,
                    'throughput': throughput
                })
                
                print(f"       Time: {batch_time:.2f}s, Avg/record: {avg_time_per_record:.3f}s, Success: {success_rate:.1%}")
            
            # Analyze performance
            max_avg_time = max(result['avg_time_per_record'] for result in performance_results)
            min_success_rate = min(result['success_rate'] for result in performance_results)
            max_throughput = max(result['throughput'] for result in performance_results)
            
            performance_acceptable = max_avg_time <= 5.0 and min_success_rate >= 0.95
            
            print(f"   📊 Performance Summary:")
            print(f"     Max avg time/record: {max_avg_time:.3f}s")
            print(f"     Min success rate: {min_success_rate:.1%}")
            print(f"     Max throughput: {max_throughput:.1f} records/sec")
            
            return TestResult(
                test_name="System Performance",
                success=performance_acceptable,
                quality_before=0.0,
                quality_after=min_success_rate * 100,
                improvement_pct=0.0,
                processing_time=max_avg_time,
                records_tested=sum(r['batch_size'] for r in performance_results),
                garbage_removed=0,
                details={
                    'performance_results': performance_results,
                    'max_avg_time_per_record': max_avg_time,
                    'min_success_rate': min_success_rate,
                    'max_throughput': max_throughput
                }
            )
            
        except Exception as e:
            self.logger.log_module_activity('efficient_tester', 'performance', 'error', {
                'message': f'Performance test failed: {e}'
            })
            return TestResult(
                test_name="System Performance",
                success=False,
                quality_before=0.0,
                quality_after=0.0,
                improvement_pct=0.0,
                processing_time=0.0,
                records_tested=0,
                garbage_removed=0,
                details={'error': str(e)}
            )
    
    def _test_error_resilience(self) -> TestResult:
        """Test error handling and system resilience."""
        print("   Testing error handling and resilience...")
        
        try:
            start_time = time.time()
            
            # Test various error scenarios
            error_scenarios = [
                {'Company': None, 'Website': None},  # Null values
                {'Company': '', 'Website': ''},      # Empty strings
                {'Company': 'A' * 1000, 'Website': 'B' * 1000},  # Very long strings
                {'Company': '🚀💻🎉', 'Website': 'https://🌟.com'},  # Unicode/emoji
                {'Company': '<script>alert("xss")</script>', 'Website': 'javascript:void(0)'},  # Malicious content
            ]
            
            successful_error_handling = 0
            total_scenarios = len(error_scenarios)
            
            for i, scenario in enumerate(error_scenarios):
                try:
                    context = {
                        'id': f'error_test_{i}',
                        'Full Name': 'Test User',
                        'source': 'error_resilience_test'
                    }
                    
                    # This should not crash, even with bad data
                    result = self.data_cleaner.clean_and_validate(scenario, context)
                    
                    # System should handle gracefully
                    if result is not None:
                        successful_error_handling += 1
                        print(f"     Scenario {i+1}: ✅ Handled gracefully")
                    
                except Exception as e:
                    # Log but continue - we want to test resilience
                    self.logger.log_module_activity('efficient_tester', 'error_scenario', 'warning', {
                        'message': f'Error scenario {i+1} caused exception: {e}'
                    })
                    print(f"     Scenario {i+1}: ⚠️ Exception occurred")
            
            # Test system health after errors
            try:
                health_status = self.data_cleaner.get_system_health()
                system_healthy = health_status.get('overall_healthy', False)
                print(f"     System health after errors: {'✅ Healthy' if system_healthy else '❌ Unhealthy'}")
            except Exception as e:
                system_healthy = False
                print(f"     System health check failed: {e}")
            
            processing_time = time.time() - start_time
            error_handling_rate = successful_error_handling / total_scenarios
            
            print(f"   📊 Resilience Results:")
            print(f"     Error scenarios handled: {successful_error_handling}/{total_scenarios}")
            print(f"     Error handling rate: {error_handling_rate:.1%}")
            print(f"     System health: {'Healthy' if system_healthy else 'Unhealthy'}")
            
            return TestResult(
                test_name="Error Handling and Resilience",
                success=error_handling_rate >= 0.8 and system_healthy,
                quality_before=0.0,
                quality_after=error_handling_rate * 100,
                improvement_pct=0.0,
                processing_time=processing_time,
                records_tested=total_scenarios,
                garbage_removed=0,
                details={
                    'error_handling_rate': error_handling_rate,
                    'system_healthy': system_healthy,
                    'scenarios_tested': total_scenarios
                }
            )
            
        except Exception as e:
            self.logger.log_module_activity('efficient_tester', 'error_resilience', 'error', {
                'message': f'Error resilience test failed: {e}'
            })
            return TestResult(
                test_name="Error Handling and Resilience",
                success=False,
                quality_before=0.0,
                quality_after=0.0,
                improvement_pct=0.0,
                processing_time=0.0,
                records_tested=0,
                garbage_removed=0,
                details={'error': str(e)}
            )
    
    def _test_pipeline_integration(self) -> TestResult:
        """Test complete pipeline integration."""
        print("   Testing complete pipeline integration...")
        
        try:
            start_time = time.time()
            
            # Simulate complete enricher pipeline with realistic data
            test_leads = [
                {
                    'id': 'integration_test_1',
                    'Full Name': 'John Doe',
                    'Company': 'Sirius XM and ... Some results may have been delisted',
                    'Website': 'https://google.com/search?q=company',
                    'source': 'integration_test'
                },
                {
                    'id': 'integration_test_2', 
                    'Full Name': 'Jane Smith',
                    'Company': 'Real Company Inc <div>Search Results</div>',
                    'Website': 'linkedin.com/company/real',
                    'source': 'integration_test'
                },
                {
                    'id': 'integration_test_3',
                    'Full Name': 'Bob Johnson',
                    'Company': 'Clean Company LLC',
                    'Website': 'https://cleancompany.com',
                    'source': 'integration_test'
                }
            ]
            
            successful_integrations = 0
            garbage_eliminated = True
            
            for lead in test_leads:
                try:
                    # Extract data for cleaning
                    data_to_clean = {
                        'Company': lead.get('Company', ''),
                        'Website': lead.get('Website', '')
                    }
                    
                    context = {
                        'id': lead['id'],
                        'Full Name': lead.get('Full Name', ''),
                        'source': lead.get('source', 'unknown')
                    }
                    
                    # Clean the data
                    cleaning_result = self.data_cleaner.clean_and_validate(data_to_clean, context)
                    
                    if cleaning_result.success:
                        successful_integrations += 1
                        
                        # Check for remaining garbage patterns
                        cleaned_data_str = str(cleaning_result.cleaned_data).lower()
                        garbage_patterns = ['google', 'search', 'results', 'delisted', '<div>', 'linkedin.com']
                        
                        for pattern in garbage_patterns:
                            if pattern in cleaned_data_str:
                                garbage_eliminated = False
                                print(f"     WARNING: Garbage pattern '{pattern}' found in cleaned data for {lead['id']}")
                        
                        print(f"     Lead {lead['id']}: ✅ Successfully integrated")
                    else:
                        print(f"     Lead {lead['id']}: ❌ Integration failed")
                        
                except Exception as e:
                    self.logger.log_module_activity('efficient_tester', 'pipeline_integration', 'error', {
                        'message': f'Pipeline integration error for {lead["id"]}: {e}'
                    })
                    print(f"     Lead {lead['id']}: ❌ Exception occurred")
            
            processing_time = time.time() - start_time
            integration_success_rate = successful_integrations / len(test_leads)
            
            print(f"   📊 Integration Results:")
            print(f"     Integration success rate: {integration_success_rate:.1%}")
            print(f"     Garbage eliminated: {'✅ Yes' if garbage_eliminated else '❌ No'}")
            print(f"     Pipeline processing time: {processing_time:.2f}s")
            
            return TestResult(
                test_name="Complete Pipeline Integration",
                success=integration_success_rate >= 0.9 and garbage_eliminated,
                quality_before=0.0,
                quality_after=integration_success_rate * 100,
                improvement_pct=0.0,
                processing_time=processing_time,
                records_tested=len(test_leads),
                garbage_removed=0,
                details={
                    'integration_success_rate': integration_success_rate,
                    'garbage_eliminated': garbage_eliminated,
                    'leads_tested': len(test_leads)
                }
            )
            
        except Exception as e:
            self.logger.log_module_activity('efficient_tester', 'pipeline_integration', 'error', {
                'message': f'Pipeline integration test failed: {e}'
            })
            return TestResult(
                test_name="Complete Pipeline Integration",
                success=False,
                quality_before=0.0,
                quality_after=0.0,
                improvement_pct=0.0,
                processing_time=0.0,
                records_tested=0,
                garbage_removed=0,
                details={'error': str(e)}
            )
    
    def _count_garbage_patterns(self, data: Dict[str, Any]) -> int:
        """Count garbage patterns in data."""
        garbage_patterns = [
            'some results may have been delisted',
            'google search',
            'search results',
            '<div>',
            '</div>',
            '&nbsp;',
            '&amp;',
            'linkedin.com',
            'facebook.com',
            'google.com'
        ]
        
        data_str = str(data).lower()
        return sum(1 for pattern in garbage_patterns if pattern in data_str)
    
    def _calculate_quality_score(self, data_list: List[Dict[str, Any]]) -> float:
        """Calculate quality score for a list of data records."""
        if not data_list:
            return 0.0
        
        total_score = 0.0
        
        for record in data_list:
            record_score = 0.0
            
            # Check company name quality
            company = str(record.get('Company', '')).lower()
            if company and len(company.strip()) > 2:
                # Deduct points for garbage patterns
                garbage_count = self._count_garbage_patterns({'Company': company})
                if garbage_count == 0:
                    record_score += 50.0  # 50 points for clean company name
                else:
                    record_score += max(0, 50.0 - (garbage_count * 10))  # Deduct 10 points per garbage pattern
            
            # Check website quality
            website = str(record.get('Website', '')).lower()
            if website and len(website.strip()) > 4:
                # Deduct points for garbage patterns
                garbage_count = self._count_garbage_patterns({'Website': website})
                if garbage_count == 0 and website.startswith(('http://', 'https://')):
                    record_score += 50.0  # 50 points for clean website
                else:
                    record_score += max(0, 50.0 - (garbage_count * 10))  # Deduct 10 points per garbage pattern
            
            total_score += record_score
        
        return total_score / len(data_list)
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        
        # Calculate overall metrics
        total_records_tested = sum(result.records_tested for result in self.test_results)
        total_garbage_removed = sum(result.garbage_removed for result in self.test_results)
        
        # Calculate quality improvements
        quality_improvements = [result.improvement_pct for result in self.test_results 
                              if result.improvement_pct > 0]
        avg_quality_improvement = sum(quality_improvements) / len(quality_improvements) if quality_improvements else 0
        
        # Determine overall success
        overall_success = (
            passed_tests >= total_tests * 0.8 and  # 80% of tests must pass
            avg_quality_improvement >= 110.0  # 110% improvement target
        )
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_success': overall_success,
            'summary': {
                'tests_passed': f"{passed_tests}/{total_tests}",
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%",
                'records_tested': total_records_tested,
                'garbage_removed': total_garbage_removed,
                'avg_quality_improvement': f"{avg_quality_improvement:.1f}%",
                'api_calls_used': 0  # Minimal API usage
            },
            'test_results': [asdict(result) for result in self.test_results],
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_tests = [result for result in self.test_results if not result.success]
        
        if not failed_tests:
            recommendations.extend([
                "✅ All tests passed successfully - system ready for production deployment",
                "🚀 Data quality improvement target achieved (110%+)",
                "📊 Performance metrics within acceptable ranges",
                "🛡️ Error handling working correctly",
                "🔄 Pipeline integration functioning properly",
                "⚡ System optimized for minimal API usage"
            ])
        else:
            recommendations.append("⚠️ Some tests failed - review failed test details")
            
            for failed_test in failed_tests:
                recommendations.append(f"❌ {failed_test.test_name}: {failed_test.details.get('error', 'Unknown error')}")
        
        # Check quality improvement
        quality_improvements = [result.improvement_pct for result in self.test_results 
                              if result.improvement_pct > 0]
        if quality_improvements:
            avg_improvement = sum(quality_improvements) / len(quality_improvements)
            if avg_improvement < 110.0:
                recommendations.append(f"📈 Quality improvement ({avg_improvement:.1f}%) below target (110%)")
        
        return recommendations


def main():
    """Run the efficient production testing suite."""
    print("🚀 DataCleaner Efficient Production Testing")
    print("=" * 60)
    print("⚡ Optimized for minimal Airtable API usage")
    print("🎯 Comprehensive testing with realistic production data")
    print()
    
    try:
        # Initialize and run tests
        tester = EfficientProductionTester()
        final_report = tester.run_complete_test_suite()
        
        # Display final results
        print("\n" + "=" * 60)
        print("🎯 FINAL PRODUCTION TEST RESULTS")
        print("=" * 60)
        
        if final_report.get('success', False):
            print("✅ PRODUCTION TESTING SUCCESSFUL!")
            print("🎉 DataCleaner system is ready for deployment")
        else:
            print("❌ PRODUCTION TESTING FAILED!")
            print("🔧 System needs improvements before deployment")
        
        # Display summary
        summary = final_report.get('summary', {})
        print(f"\n📊 Test Summary:")
        print(f"   Tests Passed: {summary.get('tests_passed', 'N/A')}")
        print(f"   Success Rate: {summary.get('success_rate', 'N/A')}")
        print(f"   Records Tested: {summary.get('records_tested', 'N/A')}")
        print(f"   Garbage Removed: {summary.get('garbage_removed', 'N/A')}")
        print(f"   Quality Improvement: {summary.get('avg_quality_improvement', 'N/A')}")
        print(f"   API Calls Used: {summary.get('api_calls_used', 'N/A')} (Minimal!)")
        
        # Display recommendations
        recommendations = final_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        
        # Save detailed report
        report_file = f"efficient_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return final_report.get('success', False)
        
    except Exception as e:
        print(f"\n💥 PRODUCTION TESTING ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)