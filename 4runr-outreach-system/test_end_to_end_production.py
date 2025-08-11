#!/usr/bin/env python3
"""
End-to-End Production Testing for DataCleaner System

This comprehensive test suite validates the complete data cleaning pipeline
using real production data from Airtable, ensuring the system eliminates
garbage data and achieves 110% data quality improvement.

Key Testing Areas:
1. Real production data cleaning
2. Complete pipeline integration
3. Data quality measurement
4. Performance validation
5. Error handling verification
"""

import sys
import os
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import DataCleaner, CleaningResult
from shared.airtable_client import AirtableClient
from shared.logging_utils import get_logger

@dataclass
class ProductionTestResult:
    """Results from production testing."""
    test_name: str
    success: bool
    data_quality_before: float
    data_quality_after: float
    improvement_percentage: float
    processing_time: float
    records_processed: int
    garbage_removed: int
    errors_encountered: int
    details: Dict[str, Any]

@dataclass
class DataQualityMetrics:
    """Comprehensive data quality metrics."""
    total_records: int
    valid_company_names: int
    valid_websites: int
    garbage_company_names: int
    garbage_websites: int
    search_artifacts_found: int
    html_fragments_found: int
    overall_quality_score: float
    confidence_scores: List[float]

class ProductionDataTester:
    """
    Comprehensive production data testing system.
    
    Tests the complete DataCleaner pipeline with real Airtable data,
    measuring quality improvements and validating system performance.
    """
    
    def __init__(self):
        self.logger = get_logger('production_tester')
        self.data_cleaner = DataCleaner()
        self.airtable_client = AirtableClient()
        self.test_results = []
        
        # Quality thresholds
        self.quality_thresholds = {
            'minimum_improvement': 110.0,  # 110% improvement required
            'max_processing_time': 5.0,    # 5 seconds per record max
            'min_confidence_score': 0.7,   # 70% minimum confidence
            'max_error_rate': 0.01         # 1% maximum error rate
        }
        
        # Known garbage patterns to test for
        self.garbage_patterns = [
            'Some results may have been delisted',
            'Sirius XM and',
            'Google Search',
            'Search results',
            '<div>',
            '</div>',
            '&nbsp;',
            '&amp;',
            'linkedin.com',
            'facebook.com',
            'google.com'
        ]
    
    async def run_complete_production_test(self) -> Dict[str, Any]:
        """
        Run the complete production testing suite.
        
        Returns:
            Comprehensive test results and quality metrics
        """
        self.logger.log_module_activity('production_tester', 'system', 'info', {
            'message': '🚀 Starting Complete Production Test Suite'
        })
        print("🚀 DataCleaner Production Testing Suite")
        print("=" * 60)
        
        try:
            # Test 1: Sample Production Data Test
            print("\n📊 Test 1: Sample Production Data Analysis")
            sample_test = await self._test_sample_production_data()
            self.test_results.append(sample_test)
            
            # Test 2: Garbage Pattern Detection Test
            print("\n🗑️ Test 2: Garbage Pattern Detection")
            garbage_test = await self._test_garbage_pattern_detection()
            self.test_results.append(garbage_test)
            
            # Test 3: Data Quality Improvement Test
            print("\n📈 Test 3: Data Quality Improvement Measurement")
            quality_test = await self._test_data_quality_improvement()
            self.test_results.append(quality_test)
            
            # Test 4: Performance and Scale Test
            print("\n⚡ Test 4: Performance and Scale Testing")
            performance_test = await self._test_performance_and_scale()
            self.test_results.append(performance_test)
            
            # Test 5: Error Handling and Resilience Test
            print("\n🛡️ Test 5: Error Handling and Resilience")
            resilience_test = await self._test_error_handling_resilience()
            self.test_results.append(resilience_test)
            
            # Test 6: Complete Pipeline Integration Test
            print("\n🔄 Test 6: Complete Pipeline Integration")
            integration_test = await self._test_complete_pipeline_integration()
            self.test_results.append(integration_test)
            
            # Generate comprehensive report
            final_report = self._generate_final_report()
            
            return final_report
            
        except Exception as e:
            self.logger.log_module_activity('production_tester', 'system', 'error', {
                'message': f'Production test suite failed: {e}'
            })
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _test_sample_production_data(self) -> ProductionTestResult:
        """Test with real sample data from production."""
        print("   Fetching sample production data...")
        
        try:
            start_time = time.time()
            
            # Get sample records from Airtable
            sample_records = await self._fetch_sample_records(limit=50)
            
            if not sample_records:
                return ProductionTestResult(
                    test_name="Sample Production Data",
                    success=False,
                    data_quality_before=0.0,
                    data_quality_after=0.0,
                    improvement_percentage=0.0,
                    processing_time=0.0,
                    records_processed=0,
                    garbage_removed=0,
                    errors_encountered=1,
                    details={'error': 'No sample records found'}
                )
            
            print(f"   Analyzing {len(sample_records)} production records...")
            
            # Analyze data quality before cleaning
            quality_before = self._calculate_data_quality(sample_records)
            
            # Clean the data
            cleaned_records = []
            garbage_removed = 0
            errors = 0
            
            for record in sample_records:
                try:
                    # Extract relevant fields
                    data = {
                        'Company': record.get('Company', ''),
                        'Website': record.get('Website', '')
                    }
                    
                    context = {
                        'id': record.get('id', 'unknown'),
                        'Full Name': record.get('Full Name', ''),
                        'source': 'production_test'
                    }
                    
                    # Clean the data
                    result = self.data_cleaner.clean_and_validate(data, context)
                    
                    if result.success:
                        cleaned_records.append(result.cleaned_data)
                        garbage_removed += len(result.cleaning_actions)
                    else:
                        errors += 1
                        
                except Exception as e:
                    self.logger.log_module_activity('production_tester', 'record_processing', 'error', {
                        'message': f'Error processing record: {e}'
                    })
                    errors += 1
            
            # Analyze data quality after cleaning
            quality_after = self._calculate_data_quality(cleaned_records)
            
            processing_time = time.time() - start_time
            improvement = ((quality_after.overall_quality_score - quality_before.overall_quality_score) / quality_before.overall_quality_score) * 100
            
            print(f"   ✅ Quality Before: {quality_before.overall_quality_score:.2f}")
            print(f"   ✅ Quality After: {quality_after.overall_quality_score:.2f}")
            print(f"   ✅ Improvement: {improvement:.1f}%")
            print(f"   ✅ Processing Time: {processing_time:.2f}s")
            print(f"   ✅ Garbage Removed: {garbage_removed} actions")
            
            return ProductionTestResult(
                test_name="Sample Production Data",
                success=improvement >= self.quality_thresholds['minimum_improvement'],
                data_quality_before=quality_before.overall_quality_score,
                data_quality_after=quality_after.overall_quality_score,
                improvement_percentage=improvement,
                processing_time=processing_time,
                records_processed=len(sample_records),
                garbage_removed=garbage_removed,
                errors_encountered=errors,
                details={
                    'quality_before': asdict(quality_before),
                    'quality_after': asdict(quality_after),
                    'sample_size': len(sample_records)
                }
            )
            
        except Exception as e:
            self.logger.log_module_activity('production_tester', 'sample_test', 'error', {
                'message': f'Sample production data test failed: {e}'
            })
            return ProductionTestResult(
                test_name="Sample Production Data",
                success=False,
                data_quality_before=0.0,
                data_quality_after=0.0,
                improvement_percentage=0.0,
                processing_time=0.0,
                records_processed=0,
                garbage_removed=0,
                errors_encountered=1,
                details={'error': str(e)}
            )
    
    async def _test_garbage_pattern_detection(self) -> ProductionTestResult:
        """Test detection and removal of specific garbage patterns."""
        print("   Testing garbage pattern detection...")
        
        try:
            start_time = time.time()
            
            # Create test data with known garbage patterns
            test_data = [
                {
                    'Company': 'Sirius XM and ... Some results may have been delisted',
                    'Website': 'https://google.com/search?q=company'
                },
                {
                    'Company': 'Test Company <div>Google Search Results</div>',
                    'Website': 'linkedin.com/company/test'
                },
                {
                    'Company': 'Real Company Inc &nbsp;&amp; Associates',
                    'Website': 'https://realcompany.com'
                },
                {
                    'Company': 'Some results may have been delisted - Company Name',
                    'Website': 'facebook.com/company'
                }
            ]
            
            garbage_detected = 0
            garbage_removed = 0
            successful_cleanings = 0
            
            for i, data in enumerate(test_data):
                context = {
                    'id': f'garbage_test_{i}',
                    'Full Name': 'Test User',
                    'source': 'garbage_pattern_test'
                }
                
                # Check for garbage patterns before cleaning
                before_garbage = sum(1 for pattern in self.garbage_patterns 
                                   if pattern.lower() in str(data).lower())
                garbage_detected += before_garbage
                
                # Clean the data
                result = self.data_cleaner.clean_and_validate(data, context)
                
                if result.success:
                    successful_cleanings += 1
                    
                    # Check for garbage patterns after cleaning
                    after_garbage = sum(1 for pattern in self.garbage_patterns 
                                      if pattern.lower() in str(result.cleaned_data).lower())
                    
                    garbage_removed += (before_garbage - after_garbage)
                    
                    print(f"   📝 Test {i+1}: {before_garbage} → {after_garbage} garbage patterns")
            
            processing_time = time.time() - start_time
            removal_rate = (garbage_removed / garbage_detected * 100) if garbage_detected > 0 else 100
            
            print(f"   ✅ Garbage Patterns Detected: {garbage_detected}")
            print(f"   ✅ Garbage Patterns Removed: {garbage_removed}")
            print(f"   ✅ Removal Rate: {removal_rate:.1f}%")
            print(f"   ✅ Successful Cleanings: {successful_cleanings}/{len(test_data)}")
            
            return ProductionTestResult(
                test_name="Garbage Pattern Detection",
                success=removal_rate >= 90.0,  # 90% removal rate required
                data_quality_before=0.0,
                data_quality_after=removal_rate,
                improvement_percentage=removal_rate,
                processing_time=processing_time,
                records_processed=len(test_data),
                garbage_removed=garbage_removed,
                errors_encountered=len(test_data) - successful_cleanings,
                details={
                    'garbage_detected': garbage_detected,
                    'garbage_removed': garbage_removed,
                    'removal_rate': removal_rate,
                    'patterns_tested': len(self.garbage_patterns)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Garbage pattern detection test failed: {e}")
            return ProductionTestResult(
                test_name="Garbage Pattern Detection",
                success=False,
                data_quality_before=0.0,
                data_quality_after=0.0,
                improvement_percentage=0.0,
                processing_time=0.0,
                records_processed=0,
                garbage_removed=0,
                errors_encountered=1,
                details={'error': str(e)}
            )
    
    async def _test_data_quality_improvement(self) -> ProductionTestResult:
        """Test measurable data quality improvement."""
        print("   Measuring data quality improvement...")
        
        try:
            start_time = time.time()
            
            # Get a larger sample for quality measurement
            sample_records = await self._fetch_sample_records(limit=100)
            
            if not sample_records:
                raise Exception("No records available for quality testing")
            
            # Calculate baseline quality
            baseline_quality = self._calculate_data_quality(sample_records)
            
            # Process records through cleaner
            processed_records = []
            total_confidence = 0.0
            successful_cleanings = 0
            
            for record in sample_records:
                try:
                    data = {
                        'Company': record.get('Company', ''),
                        'Website': record.get('Website', '')
                    }
                    
                    context = {
                        'id': record.get('id', 'unknown'),
                        'Full Name': record.get('Full Name', ''),
                        'source': 'quality_test'
                    }
                    
                    result = self.data_cleaner.clean_and_validate(data, context)
                    
                    if result.success:
                        processed_records.append(result.cleaned_data)
                        total_confidence += result.confidence_score
                        successful_cleanings += 1
                        
                except Exception as e:
                    self.logger.error(f"Error in quality test: {e}")
            
            # Calculate improved quality
            improved_quality = self._calculate_data_quality(processed_records)
            
            processing_time = time.time() - start_time
            improvement = ((improved_quality.overall_quality_score - baseline_quality.overall_quality_score) / baseline_quality.overall_quality_score) * 100
            avg_confidence = total_confidence / successful_cleanings if successful_cleanings > 0 else 0.0
            
            print(f"   ✅ Baseline Quality: {baseline_quality.overall_quality_score:.2f}")
            print(f"   ✅ Improved Quality: {improved_quality.overall_quality_score:.2f}")
            print(f"   ✅ Quality Improvement: {improvement:.1f}%")
            print(f"   ✅ Average Confidence: {avg_confidence:.2f}")
            print(f"   ✅ Success Rate: {successful_cleanings}/{len(sample_records)}")
            
            return ProductionTestResult(
                test_name="Data Quality Improvement",
                success=improvement >= self.quality_thresholds['minimum_improvement'],
                data_quality_before=baseline_quality.overall_quality_score,
                data_quality_after=improved_quality.overall_quality_score,
                improvement_percentage=improvement,
                processing_time=processing_time,
                records_processed=len(sample_records),
                garbage_removed=0,  # Calculated separately
                errors_encountered=len(sample_records) - successful_cleanings,
                details={
                    'baseline_quality': asdict(baseline_quality),
                    'improved_quality': asdict(improved_quality),
                    'average_confidence': avg_confidence,
                    'success_rate': successful_cleanings / len(sample_records)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Data quality improvement test failed: {e}")
            return ProductionTestResult(
                test_name="Data Quality Improvement",
                success=False,
                data_quality_before=0.0,
                data_quality_after=0.0,
                improvement_percentage=0.0,
                processing_time=0.0,
                records_processed=0,
                garbage_removed=0,
                errors_encountered=1,
                details={'error': str(e)}
            )
    
    async def _test_performance_and_scale(self) -> ProductionTestResult:
        """Test system performance and scalability."""
        print("   Testing performance and scalability...")
        
        try:
            # Test with increasing batch sizes
            batch_sizes = [10, 50, 100, 200]
            performance_results = []
            
            for batch_size in batch_sizes:
                print(f"     Testing batch size: {batch_size}")
                
                start_time = time.time()
                
                # Create test data
                test_records = []
                for i in range(batch_size):
                    test_records.append({
                        'Company': f'Test Company {i} Inc',
                        'Website': f'https://testcompany{i}.com'
                    })
                
                # Process batch
                successful_processes = 0
                total_processing_time = 0.0
                
                for i, record in enumerate(test_records):
                    record_start = time.time()
                    
                    context = {
                        'id': f'perf_test_{i}',
                        'Full Name': 'Test User',
                        'source': 'performance_test'
                    }
                    
                    try:
                        result = self.data_cleaner.clean_and_validate(record, context)
                        if result.success:
                            successful_processes += 1
                    except Exception as e:
                        self.logger.error(f"Performance test error: {e}")
                    
                    total_processing_time += (time.time() - record_start)
                
                batch_time = time.time() - start_time
                avg_time_per_record = total_processing_time / batch_size
                
                performance_results.append({
                    'batch_size': batch_size,
                    'total_time': batch_time,
                    'avg_time_per_record': avg_time_per_record,
                    'success_rate': successful_processes / batch_size,
                    'throughput': batch_size / batch_time
                })
                
                print(f"       Time: {batch_time:.2f}s, Avg/record: {avg_time_per_record:.3f}s")
            
            # Analyze performance
            max_avg_time = max(result['avg_time_per_record'] for result in performance_results)
            min_success_rate = min(result['success_rate'] for result in performance_results)
            max_throughput = max(result['throughput'] for result in performance_results)
            
            performance_acceptable = (
                max_avg_time <= self.quality_thresholds['max_processing_time'] and
                min_success_rate >= 0.95  # 95% success rate required
            )
            
            print(f"   ✅ Max Avg Time/Record: {max_avg_time:.3f}s")
            print(f"   ✅ Min Success Rate: {min_success_rate:.2%}")
            print(f"   ✅ Max Throughput: {max_throughput:.1f} records/sec")
            
            return ProductionTestResult(
                test_name="Performance and Scale",
                success=performance_acceptable,
                data_quality_before=0.0,
                data_quality_after=min_success_rate * 100,
                improvement_percentage=0.0,
                processing_time=max_avg_time,
                records_processed=sum(r['batch_size'] for r in performance_results),
                garbage_removed=0,
                errors_encountered=0,
                details={
                    'performance_results': performance_results,
                    'max_avg_time_per_record': max_avg_time,
                    'min_success_rate': min_success_rate,
                    'max_throughput': max_throughput
                }
            )
            
        except Exception as e:
            self.logger.error(f"Performance test failed: {e}")
            return ProductionTestResult(
                test_name="Performance and Scale",
                success=False,
                data_quality_before=0.0,
                data_quality_after=0.0,
                improvement_percentage=0.0,
                processing_time=0.0,
                records_processed=0,
                garbage_removed=0,
                errors_encountered=1,
                details={'error': str(e)}
            )
    
    async def _test_error_handling_resilience(self) -> ProductionTestResult:
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
                        'source': 'error_handling_test'
                    }
                    
                    # This should not crash, even with bad data
                    result = self.data_cleaner.clean_and_validate(scenario, context)
                    
                    # System should handle gracefully (success or controlled failure)
                    if result is not None:
                        successful_error_handling += 1
                        print(f"     Scenario {i+1}: Handled gracefully")
                    
                except Exception as e:
                    # Log but don't fail - we want to test resilience
                    self.logger.warning(f"Error scenario {i+1} caused exception: {e}")
                    print(f"     Scenario {i+1}: Exception occurred (not ideal)")
            
            # Test system health after errors
            try:
                health_status = self.data_cleaner.get_system_health()
                system_healthy = health_status.get('overall_healthy', False)
                print(f"     System health after errors: {system_healthy}")
            except Exception as e:
                system_healthy = False
                print(f"     System health check failed: {e}")
            
            processing_time = time.time() - start_time
            error_handling_rate = successful_error_handling / total_scenarios
            
            print(f"   ✅ Error Scenarios Handled: {successful_error_handling}/{total_scenarios}")
            print(f"   ✅ Error Handling Rate: {error_handling_rate:.1%}")
            print(f"   ✅ System Health: {system_healthy}")
            
            return ProductionTestResult(
                test_name="Error Handling and Resilience",
                success=error_handling_rate >= 0.8 and system_healthy,  # 80% handling + healthy system
                data_quality_before=0.0,
                data_quality_after=error_handling_rate * 100,
                improvement_percentage=0.0,
                processing_time=processing_time,
                records_processed=total_scenarios,
                garbage_removed=0,
                errors_encountered=total_scenarios - successful_error_handling,
                details={
                    'error_handling_rate': error_handling_rate,
                    'system_healthy': system_healthy,
                    'scenarios_tested': total_scenarios
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error handling test failed: {e}")
            return ProductionTestResult(
                test_name="Error Handling and Resilience",
                success=False,
                data_quality_before=0.0,
                data_quality_after=0.0,
                improvement_percentage=0.0,
                processing_time=0.0,
                records_processed=0,
                garbage_removed=0,
                errors_encountered=1,
                details={'error': str(e)}
            )
    
    async def _test_complete_pipeline_integration(self) -> ProductionTestResult:
        """Test complete pipeline integration end-to-end."""
        print("   Testing complete pipeline integration...")
        
        try:
            start_time = time.time()
            
            # Simulate complete enricher pipeline
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
                }
            ]
            
            pipeline_results = []
            successful_integrations = 0
            
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
                        # Simulate updating the lead with cleaned data
                        updated_lead = lead.copy()
                        updated_lead.update(cleaning_result.cleaned_data)
                        
                        pipeline_results.append({
                            'original': lead,
                            'cleaned': updated_lead,
                            'cleaning_result': cleaning_result,
                            'success': True
                        })
                        successful_integrations += 1
                        
                        print(f"     Lead {lead['id']}: Successfully integrated")
                    else:
                        pipeline_results.append({
                            'original': lead,
                            'cleaned': None,
                            'cleaning_result': cleaning_result,
                            'success': False
                        })
                        print(f"     Lead {lead['id']}: Integration failed")
                        
                except Exception as e:
                    self.logger.error(f"Pipeline integration error for {lead['id']}: {e}")
                    pipeline_results.append({
                        'original': lead,
                        'cleaned': None,
                        'cleaning_result': None,
                        'success': False,
                        'error': str(e)
                    })
            
            processing_time = time.time() - start_time
            integration_success_rate = successful_integrations / len(test_leads)
            
            # Verify no garbage patterns remain
            garbage_eliminated = True
            for result in pipeline_results:
                if result['success'] and result['cleaned']:
                    cleaned_data_str = str(result['cleaned']).lower()
                    for pattern in self.garbage_patterns:
                        if pattern.lower() in cleaned_data_str:
                            garbage_eliminated = False
                            print(f"     WARNING: Garbage pattern '{pattern}' found in cleaned data")
            
            print(f"   ✅ Integration Success Rate: {integration_success_rate:.1%}")
            print(f"   ✅ Garbage Eliminated: {garbage_eliminated}")
            print(f"   ✅ Pipeline Processing Time: {processing_time:.2f}s")
            
            return ProductionTestResult(
                test_name="Complete Pipeline Integration",
                success=integration_success_rate >= 0.9 and garbage_eliminated,
                data_quality_before=0.0,
                data_quality_after=integration_success_rate * 100,
                improvement_percentage=0.0,
                processing_time=processing_time,
                records_processed=len(test_leads),
                garbage_removed=0,
                errors_encountered=len(test_leads) - successful_integrations,
                details={
                    'integration_success_rate': integration_success_rate,
                    'garbage_eliminated': garbage_eliminated,
                    'pipeline_results': pipeline_results
                }
            )
            
        except Exception as e:
            self.logger.error(f"Pipeline integration test failed: {e}")
            return ProductionTestResult(
                test_name="Complete Pipeline Integration",
                success=False,
                data_quality_before=0.0,
                data_quality_after=0.0,
                improvement_percentage=0.0,
                processing_time=0.0,
                records_processed=0,
                garbage_removed=0,
                errors_encountered=1,
                details={'error': str(e)}
            )
    
    async def _fetch_sample_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch sample records from Airtable for testing."""
        try:
            # Try to get real records from Airtable
            records = self.airtable_client.get_leads(limit=limit)
            
            if records:
                return records
            else:
                # Fallback to simulated production-like data
                return self._generate_simulated_production_data(limit)
                
        except Exception as e:
            self.logger.warning(f"Could not fetch real records, using simulated data: {e}")
            return self._generate_simulated_production_data(limit)
    
    def _generate_simulated_production_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate simulated production data with known garbage patterns."""
        simulated_data = []
        
        garbage_companies = [
            'Sirius XM and ... Some results may have been delisted',
            'Test Company <div>Google Search Results</div>',
            'Real Company Inc &nbsp;&amp; Associates',
            'Some results may have been delisted - Company Name',
            'Company Name - Google Search',
            '<span>Business Name</span> Search Results'
        ]
        
        garbage_websites = [
            'https://google.com/search?q=company',
            'linkedin.com/company/test',
            'facebook.com/company',
            'https://www.google.com/search?q=business',
            'linkedin.com/in/person'
        ]
        
        clean_companies = [
            'Acme Corporation',
            'Tech Solutions Inc',
            'Global Industries LLC',
            'Innovation Partners',
            'Digital Dynamics Corp'
        ]
        
        clean_websites = [
            'https://acmecorp.com',
            'https://techsolutions.com',
            'https://globalindustries.com',
            'https://innovationpartners.com',
            'https://digitaldynamics.com'
        ]
        
        for i in range(count):
            # Mix of garbage and clean data (70% garbage, 30% clean to simulate real production)
            if i % 10 < 7:  # 70% garbage
                company = garbage_companies[i % len(garbage_companies)]
                website = garbage_websites[i % len(garbage_websites)]
            else:  # 30% clean
                company = clean_companies[i % len(clean_companies)]
                website = clean_websites[i % len(clean_websites)]
            
            simulated_data.append({
                'id': f'simulated_{i}',
                'Full Name': f'Test User {i}',
                'Company': company,
                'Website': website,
                'source': 'simulated_production'
            })
        
        return simulated_data
    
    def _calculate_data_quality(self, records: List[Dict[str, Any]]) -> DataQualityMetrics:
        """Calculate comprehensive data quality metrics."""
        if not records:
            return DataQualityMetrics(
                total_records=0,
                valid_company_names=0,
                valid_websites=0,
                garbage_company_names=0,
                garbage_websites=0,
                search_artifacts_found=0,
                html_fragments_found=0,
                overall_quality_score=0.0,
                confidence_scores=[]
            )
        
        total_records = len(records)
        valid_company_names = 0
        valid_websites = 0
        garbage_company_names = 0
        garbage_websites = 0
        search_artifacts_found = 0
        html_fragments_found = 0
        
        for record in records:
            company = str(record.get('Company', '')).lower()
            website = str(record.get('Website', '')).lower()
            
            # Check company name quality
            if company and len(company.strip()) > 2:
                has_garbage = any(pattern.lower() in company for pattern in self.garbage_patterns)
                if not has_garbage:
                    valid_company_names += 1
                else:
                    garbage_company_names += 1
                    
                    # Count specific garbage types
                    if 'search' in company or 'results' in company or 'delisted' in company:
                        search_artifacts_found += 1
                    if '<' in company or '&' in company:
                        html_fragments_found += 1
            
            # Check website quality
            if website and len(website.strip()) > 4:
                has_garbage = any(pattern.lower() in website for pattern in self.garbage_patterns)
                if not has_garbage and website.startswith(('http://', 'https://')):
                    valid_websites += 1
                else:
                    garbage_websites += 1
        
        # Calculate overall quality score
        company_quality = valid_company_names / total_records if total_records > 0 else 0
        website_quality = valid_websites / total_records if total_records > 0 else 0
        overall_quality_score = (company_quality + website_quality) / 2 * 100
        
        return DataQualityMetrics(
            total_records=total_records,
            valid_company_names=valid_company_names,
            valid_websites=valid_websites,
            garbage_company_names=garbage_company_names,
            garbage_websites=garbage_websites,
            search_artifacts_found=search_artifacts_found,
            html_fragments_found=html_fragments_found,
            overall_quality_score=overall_quality_score,
            confidence_scores=[]  # Would be populated with actual confidence scores
        )
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        
        # Calculate overall metrics
        total_records_processed = sum(result.records_processed for result in self.test_results)
        total_garbage_removed = sum(result.garbage_removed for result in self.test_results)
        total_errors = sum(result.errors_encountered for result in self.test_results)
        
        # Calculate quality improvements
        quality_improvements = [result.improvement_percentage for result in self.test_results 
                              if result.improvement_percentage > 0]
        avg_quality_improvement = sum(quality_improvements) / len(quality_improvements) if quality_improvements else 0
        
        # Determine overall success
        overall_success = (
            passed_tests >= total_tests * 0.8 and  # 80% of tests must pass
            avg_quality_improvement >= self.quality_thresholds['minimum_improvement']
        )
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_success': overall_success,
            'summary': {
                'tests_passed': f"{passed_tests}/{total_tests}",
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%",
                'records_processed': total_records_processed,
                'garbage_removed': total_garbage_removed,
                'errors_encountered': total_errors,
                'avg_quality_improvement': f"{avg_quality_improvement:.1f}%"
            },
            'test_results': [asdict(result) for result in self.test_results],
            'quality_thresholds': self.quality_thresholds,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Analyze test results for recommendations
        failed_tests = [result for result in self.test_results if not result.success]
        
        if failed_tests:
            recommendations.append("⚠️ Some tests failed - review failed test details for specific issues")
        
        # Check quality improvement
        quality_improvements = [result.improvement_percentage for result in self.test_results 
                              if result.improvement_percentage > 0]
        if quality_improvements:
            avg_improvement = sum(quality_improvements) / len(quality_improvements)
            if avg_improvement < self.quality_thresholds['minimum_improvement']:
                recommendations.append(f"📈 Quality improvement ({avg_improvement:.1f}%) below target ({self.quality_thresholds['minimum_improvement']:.1f}%)")
        
        # Check performance
        slow_tests = [result for result in self.test_results 
                     if result.processing_time > self.quality_thresholds['max_processing_time']]
        if slow_tests:
            recommendations.append("⚡ Some operations are slower than target - consider performance optimization")
        
        # Check error rates
        high_error_tests = [result for result in self.test_results 
                           if result.records_processed > 0 and 
                           (result.errors_encountered / result.records_processed) > self.quality_thresholds['max_error_rate']]
        if high_error_tests:
            recommendations.append("🛡️ Error rates higher than acceptable - improve error handling")
        
        if not recommendations:
            recommendations.append("✅ All tests passed successfully - system ready for production deployment")
            recommendations.append("🚀 Data quality improvement target achieved")
            recommendations.append("📊 Performance metrics within acceptable ranges")
            recommendations.append("🛡️ Error handling working correctly")
        
        return recommendations


async def main():
    """Run the complete production testing suite."""
    print("🚀 DataCleaner Production Testing Suite")
    print("=" * 60)
    print("Testing complete pipeline with production data...")
    print("Validating 110% data quality improvement target...")
    print()
    
    try:
        # Initialize and run tests
        tester = ProductionDataTester()
        final_report = await tester.run_complete_production_test()
        
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
        print(f"   Records Processed: {summary.get('records_processed', 'N/A')}")
        print(f"   Garbage Removed: {summary.get('garbage_removed', 'N/A')}")
        print(f"   Quality Improvement: {summary.get('avg_quality_improvement', 'N/A')}")
        
        # Display recommendations
        recommendations = final_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        
        # Save detailed report
        report_file = f"production_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    success = asyncio.run(main())
    sys.exit(0 if success else 1)