#!/usr/bin/env python3
"""
Enrichment Testing Framework - Continuous Validation & Optimization
===================================================================
This framework continuously tests, validates, and optimizes all enrichment methods
to ensure we maintain the BEST performance in the industry.

FEATURES:
- Real-time validation testing
- Automated quality assurance
- Performance regression detection
- Competitive benchmarking automation
- Method effectiveness scoring
- Data quality monitoring
- Alert system for performance drops
"""

import os
import json
import sqlite3
import logging
import requests
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class EnrichmentTestingFramework:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('testing_framework')
        
        # Initialize testing database
        self.setup_testing_database()
        
        # Testing configuration
        self.test_config = {
            'min_success_rate': 0.70,  # Minimum acceptable success rate
            'max_processing_time': 5.0,  # Maximum processing time in seconds
            'test_frequency': 3600,  # Test every hour
            'alert_threshold': 0.60,  # Alert if success rate drops below 60%
            'sample_size': 20,  # Number of leads to test per method
            'regression_threshold': 0.10  # Alert if performance drops by 10%
        }
        
        # Test lead database
        self.test_leads = []
        self.verified_test_leads = []
        
        # Performance baselines
        self.performance_baselines = {}
        
        # Alert system
        self.alert_handlers = []
        
        self.logger.info("🧪 Enrichment Testing Framework initialized")
        self.logger.info("🎯 Ready for continuous validation and optimization")

    def setup_logging(self):
        """Setup comprehensive logging"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/enrichment-testing.log'),
                logging.StreamHandler()
            ]
        )

    def setup_testing_database(self):
        """Setup database for testing results and validation"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect('data/enrichment_testing.db')
        
        # Test results table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT,
                method_name TEXT,
                test_type TEXT,
                lead_name TEXT,
                lead_company TEXT,
                expected_result TEXT,
                actual_result TEXT,
                success BOOLEAN,
                processing_time REAL,
                confidence_score INTEGER,
                error_message TEXT,
                timestamp TEXT,
                test_batch TEXT
            )
        ''')
        
        # Performance baselines table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS performance_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_name TEXT UNIQUE,
                baseline_success_rate REAL,
                baseline_processing_time REAL,
                baseline_confidence REAL,
                established_date TEXT,
                sample_size INTEGER,
                last_updated TEXT
            )
        ''')
        
        # Test lead library
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_name TEXT,
                lead_company TEXT,
                linkedin_url TEXT,
                verified_email TEXT,
                verified_phone TEXT,
                job_title TEXT,
                industry TEXT,
                lead_quality TEXT,
                verification_date TEXT,
                verification_method TEXT,
                confidence_level TEXT
            )
        ''')
        
        # Quality monitoring
        conn.execute('''
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                metric_type TEXT,
                measurement_date TEXT,
                method_name TEXT,
                alert_triggered BOOLEAN DEFAULT 0
            )
        ''')
        
        # Alert history
        conn.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                alert_message TEXT,
                severity TEXT,
                method_affected TEXT,
                metric_value REAL,
                threshold_value REAL,
                timestamp TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolution_time TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("✅ Testing database initialized")

    def add_verified_test_lead(self, lead_data: Dict):
        """Add a verified test lead to our testing library"""
        try:
            conn = sqlite3.connect('data/enrichment_testing.db')
            
            conn.execute('''
                INSERT OR REPLACE INTO test_leads (
                    lead_name, lead_company, linkedin_url, verified_email,
                    verified_phone, job_title, industry, lead_quality,
                    verification_date, verification_method, confidence_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead_data.get('full_name'),
                lead_data.get('company'),
                lead_data.get('linkedin_url'),
                lead_data.get('verified_email'),
                lead_data.get('verified_phone'),
                lead_data.get('job_title'),
                lead_data.get('industry'),
                lead_data.get('lead_quality', 'verified'),
                datetime.now().isoformat(),
                lead_data.get('verification_method', 'manual'),
                lead_data.get('confidence_level', 'high')
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Added verified test lead: {lead_data.get('full_name')}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add test lead: {e}")

    def load_test_leads(self) -> List[Dict]:
        """Load verified test leads from database"""
        try:
            conn = sqlite3.connect('data/enrichment_testing.db')
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute('''
                SELECT * FROM test_leads 
                WHERE confidence_level IN ('high', 'verified')
                ORDER BY verification_date DESC
            ''')
            
            test_leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.logger.info(f"📚 Loaded {len(test_leads)} verified test leads")
            return test_leads
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load test leads: {e}")
            return []

    def run_comprehensive_test_suite(self, methods_to_test: List[str] = None) -> Dict:
        """Run comprehensive test suite on all enrichment methods"""
        try:
            test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"🧪 Starting comprehensive test suite: {test_id}")
            
            # Load test leads
            test_leads = self.load_test_leads()
            
            if len(test_leads) < 10:
                self.logger.warning("⚠️ Not enough verified test leads for comprehensive testing")
                return {}
            
            # Default methods to test
            if not methods_to_test:
                methods_to_test = [
                    'pattern_generation',
                    'domain_search',
                    'social_lookup',
                    'advanced_patterns',
                    'ml_prediction',
                    'company_website_extraction',
                    'linkedin_scraping'
                ]
            
            test_results = {}
            
            # Test each method
            for method in methods_to_test:
                self.logger.info(f"🔬 Testing method: {method}")
                
                method_results = self.test_method_performance(
                    method, 
                    test_leads[:self.test_config['sample_size']], 
                    test_id
                )
                
                test_results[method] = method_results
                
                # Check for performance issues
                self.check_performance_regression(method, method_results)
            
            # Generate overall test report
            overall_report = self.generate_test_report(test_results, test_id)
            
            # Store test results
            self.store_test_batch_results(test_id, test_results)
            
            self.logger.info(f"✅ Comprehensive test suite completed: {test_id}")
            return overall_report
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive test suite failed: {e}")
            return {}

    def test_method_performance(self, method_name: str, test_leads: List[Dict], test_id: str) -> Dict:
        """Test performance of a specific enrichment method"""
        results = {
            'method': method_name,
            'test_id': test_id,
            'total_tests': len(test_leads),
            'successful_tests': 0,
            'failed_tests': 0,
            'processing_times': [],
            'confidence_scores': [],
            'error_types': {},
            'success_rate': 0.0,
            'avg_processing_time': 0.0,
            'avg_confidence': 0.0
        }
        
        try:
            for lead in test_leads:
                test_start = time.time()
                
                # Run enrichment method
                method_result = self.run_enrichment_method(method_name, lead)
                
                processing_time = time.time() - test_start
                results['processing_times'].append(processing_time)
                
                # Validate result
                success = self.validate_enrichment_result(lead, method_result)
                
                if success:
                    results['successful_tests'] += 1
                else:
                    results['failed_tests'] += 1
                    
                    # Track error types
                    error_type = method_result.get('error_type', 'unknown_error')
                    results['error_types'][error_type] = results['error_types'].get(error_type, 0) + 1
                
                # Track confidence
                confidence = method_result.get('confidence', 0)
                results['confidence_scores'].append(confidence)
                
                # Store individual test result
                self.store_test_result(test_id, method_name, lead, method_result, success, processing_time)
            
            # Calculate summary statistics
            results['success_rate'] = results['successful_tests'] / results['total_tests']
            results['avg_processing_time'] = statistics.mean(results['processing_times']) if results['processing_times'] else 0
            results['avg_confidence'] = statistics.mean(results['confidence_scores']) if results['confidence_scores'] else 0
            
            self.logger.info(f"📊 {method_name} results: {results['success_rate']:.1%} success, {results['avg_processing_time']:.2f}s avg time")
            
        except Exception as e:
            self.logger.error(f"❌ Method testing failed for {method_name}: {e}")
            results['error'] = str(e)
        
        return results

    def run_enrichment_method(self, method_name: str, lead: Dict) -> Dict:
        """Run specific enrichment method (simulated for now)"""
        try:
            # This would integrate with actual enrichment methods
            # For now, simulate different method behaviors
            
            import random
            time.sleep(random.uniform(0.1, 2.0))  # Simulate processing time
            
            # Method-specific simulation
            method_configs = {
                'pattern_generation': {'success_rate': 0.70, 'confidence_range': (60, 85)},
                'domain_search': {'success_rate': 0.50, 'confidence_range': (40, 70)},
                'social_lookup': {'success_rate': 0.35, 'confidence_range': (30, 60)},
                'advanced_patterns': {'success_rate': 0.60, 'confidence_range': (50, 80)},
                'ml_prediction': {'success_rate': 0.80, 'confidence_range': (70, 95)},
                'company_website_extraction': {'success_rate': 0.45, 'confidence_range': (35, 65)},
                'linkedin_scraping': {'success_rate': 0.25, 'confidence_range': (20, 50)}
            }
            
            config = method_configs.get(method_name, {'success_rate': 0.50, 'confidence_range': (30, 70)})
            
            success = random.random() < config['success_rate']
            confidence = random.randint(*config['confidence_range']) if success else random.randint(10, 40)
            
            if success:
                return {
                    'email': f"{lead.get('lead_name', 'test').lower().replace(' ', '.')}@{lead.get('lead_company', 'test').lower().replace(' ', '')}.com",
                    'confidence': confidence,
                    'method': method_name,
                    'success': True
                }
            else:
                return {
                    'error_type': random.choice(['domain_not_found', 'format_invalid', 'timeout', 'rate_limit']),
                    'confidence': confidence,
                    'method': method_name,
                    'success': False
                }
                
        except Exception as e:
            return {
                'error_type': 'method_exception',
                'error_message': str(e),
                'confidence': 0,
                'method': method_name,
                'success': False
            }

    def validate_enrichment_result(self, lead: Dict, result: Dict) -> bool:
        """Validate enrichment result against known correct data"""
        try:
            if not result.get('success', False):
                return False
            
            # Check if we have verified data for this lead
            verified_email = lead.get('verified_email')
            predicted_email = result.get('email')
            
            if verified_email and predicted_email:
                # Exact match is best
                if verified_email.lower() == predicted_email.lower():
                    return True
                
                # Check if domains match (partial credit)
                verified_domain = verified_email.split('@')[1] if '@' in verified_email else ''
                predicted_domain = predicted_email.split('@')[1] if '@' in predicted_email else ''
                
                if verified_domain and predicted_domain and verified_domain == predicted_domain:
                    return True  # Domain match is still good
            
            # If no verified data, use confidence threshold
            confidence = result.get('confidence', 0)
            return confidence >= 70  # Consider high confidence as success
            
        except Exception as e:
            self.logger.debug(f"Validation error: {e}")
            return False

    def store_test_result(self, test_id: str, method_name: str, lead: Dict, result: Dict, success: bool, processing_time: float):
        """Store individual test result"""
        try:
            conn = sqlite3.connect('data/enrichment_testing.db')
            
            conn.execute('''
                INSERT INTO test_results (
                    test_id, method_name, test_type, lead_name, lead_company,
                    expected_result, actual_result, success, processing_time,
                    confidence_score, error_message, timestamp, test_batch
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_id,
                method_name,
                'performance_test',
                lead.get('lead_name'),
                lead.get('lead_company'),
                lead.get('verified_email', ''),
                json.dumps(result),
                success,
                processing_time,
                result.get('confidence', 0),
                result.get('error_message', ''),
                datetime.now().isoformat(),
                test_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store test result: {e}")

    def check_performance_regression(self, method_name: str, results: Dict):
        """Check for performance regression compared to baseline"""
        try:
            baseline = self.get_performance_baseline(method_name)
            
            if not baseline:
                # No baseline yet, establish one
                self.establish_performance_baseline(method_name, results)
                return
            
            current_success_rate = results.get('success_rate', 0)
            baseline_success_rate = baseline.get('baseline_success_rate', 0)
            
            # Check for significant regression
            regression = baseline_success_rate - current_success_rate
            
            if regression > self.test_config['regression_threshold']:
                self.trigger_alert(
                    'performance_regression',
                    f"Method {method_name} performance dropped by {regression:.1%}",
                    'high',
                    method_name,
                    current_success_rate,
                    baseline_success_rate
                )
            
            # Check for extremely low performance
            if current_success_rate < self.test_config['alert_threshold']:
                self.trigger_alert(
                    'low_performance',
                    f"Method {method_name} success rate critically low: {current_success_rate:.1%}",
                    'critical',
                    method_name,
                    current_success_rate,
                    self.test_config['alert_threshold']
                )
            
        except Exception as e:
            self.logger.error(f"❌ Regression check failed for {method_name}: {e}")

    def get_performance_baseline(self, method_name: str) -> Optional[Dict]:
        """Get performance baseline for method"""
        try:
            conn = sqlite3.connect('data/enrichment_testing.db')
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute(
                "SELECT * FROM performance_baselines WHERE method_name = ?",
                (method_name,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get baseline for {method_name}: {e}")
            return None

    def establish_performance_baseline(self, method_name: str, results: Dict):
        """Establish performance baseline for method"""
        try:
            conn = sqlite3.connect('data/enrichment_testing.db')
            
            conn.execute('''
                INSERT OR REPLACE INTO performance_baselines (
                    method_name, baseline_success_rate, baseline_processing_time,
                    baseline_confidence, established_date, sample_size, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                method_name,
                results.get('success_rate', 0),
                results.get('avg_processing_time', 0),
                results.get('avg_confidence', 0),
                datetime.now().isoformat(),
                results.get('total_tests', 0),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"📊 Established baseline for {method_name}: {results.get('success_rate', 0):.1%} success rate")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to establish baseline for {method_name}: {e}")

    def trigger_alert(self, alert_type: str, message: str, severity: str, method_affected: str, metric_value: float, threshold_value: float):
        """Trigger alert for performance issues"""
        try:
            # Store alert in database
            conn = sqlite3.connect('data/enrichment_testing.db')
            
            conn.execute('''
                INSERT INTO alert_history (
                    alert_type, alert_message, severity, method_affected,
                    metric_value, threshold_value, timestamp, resolved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_type, message, severity, method_affected,
                metric_value, threshold_value, datetime.now().isoformat(), False
            ))
            
            conn.commit()
            conn.close()
            
            # Log alert
            log_level = logging.CRITICAL if severity == 'critical' else logging.WARNING
            self.logger.log(log_level, f"🚨 ALERT: {message}")
            
            # Send notifications
            self.send_alert_notifications(alert_type, message, severity, method_affected)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to trigger alert: {e}")

    def send_alert_notifications(self, alert_type: str, message: str, severity: str, method_affected: str):
        """Send alert notifications through configured channels"""
        try:
            # For now, just log the alert
            # In production, this would send emails, Slack messages, etc.
            
            alert_data = {
                'type': alert_type,
                'message': message,
                'severity': severity,
                'method': method_affected,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save alert to file for external monitoring
            os.makedirs('alerts', exist_ok=True)
            alert_file = f"alerts/alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(alert_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
            
            self.logger.info(f"📧 Alert notification saved: {alert_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Alert notification failed: {e}")

    def generate_test_report(self, test_results: Dict, test_id: str) -> Dict:
        """Generate comprehensive test report"""
        report = {
            'test_id': test_id,
            'generated_at': datetime.now().isoformat(),
            'overall_summary': {},
            'method_details': {},
            'performance_trends': {},
            'recommendations': [],
            'quality_score': 0
        }
        
        try:
            # Calculate overall metrics
            total_methods = len(test_results)
            successful_methods = sum(1 for r in test_results.values() if r.get('success_rate', 0) >= self.test_config['min_success_rate'])
            
            all_success_rates = [r.get('success_rate', 0) for r in test_results.values()]
            overall_success_rate = statistics.mean(all_success_rates) if all_success_rates else 0
            
            report['overall_summary'] = {
                'total_methods_tested': total_methods,
                'methods_meeting_threshold': successful_methods,
                'overall_success_rate': overall_success_rate,
                'quality_grade': self.calculate_quality_grade(overall_success_rate)
            }
            
            # Method details
            for method, results in test_results.items():
                report['method_details'][method] = {
                    'success_rate': results.get('success_rate', 0),
                    'avg_processing_time': results.get('avg_processing_time', 0),
                    'avg_confidence': results.get('avg_confidence', 0),
                    'meets_threshold': results.get('success_rate', 0) >= self.test_config['min_success_rate'],
                    'performance_grade': self.calculate_method_grade(results),
                    'error_types': results.get('error_types', {})
                }
            
            # Generate recommendations
            report['recommendations'] = self.generate_test_recommendations(test_results)
            
            # Calculate overall quality score
            report['quality_score'] = self.calculate_overall_quality_score(test_results)
            
        except Exception as e:
            self.logger.error(f"❌ Test report generation failed: {e}")
            report['error'] = str(e)
        
        return report

    def calculate_quality_grade(self, success_rate: float) -> str:
        """Calculate quality grade based on success rate"""
        if success_rate >= 0.90:
            return 'A+'
        elif success_rate >= 0.80:
            return 'A'
        elif success_rate >= 0.70:
            return 'B'
        elif success_rate >= 0.60:
            return 'C'
        elif success_rate >= 0.50:
            return 'D'
        else:
            return 'F'

    def calculate_method_grade(self, results: Dict) -> str:
        """Calculate grade for individual method"""
        success_rate = results.get('success_rate', 0)
        processing_time = results.get('avg_processing_time', 0)
        confidence = results.get('avg_confidence', 0)
        
        # Weighted scoring
        score = (success_rate * 0.6) + (min(confidence/100, 1.0) * 0.3) + (max(0, 1 - processing_time/5) * 0.1)
        
        return self.calculate_quality_grade(score)

    def calculate_overall_quality_score(self, test_results: Dict) -> int:
        """Calculate overall quality score (0-100)"""
        try:
            scores = []
            
            for results in test_results.values():
                success_rate = results.get('success_rate', 0)
                processing_time = results.get('avg_processing_time', 0)
                confidence = results.get('avg_confidence', 0)
                
                # Method score calculation
                method_score = (
                    success_rate * 60 +  # 60% weight for success rate
                    (confidence / 100) * 30 +  # 30% weight for confidence
                    max(0, (5 - processing_time) / 5) * 10  # 10% weight for speed
                )
                
                scores.append(method_score)
            
            overall_score = statistics.mean(scores) if scores else 0
            return int(overall_score)
            
        except Exception as e:
            self.logger.error(f"❌ Quality score calculation failed: {e}")
            return 0

    def generate_test_recommendations(self, test_results: Dict) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        try:
            # Find underperforming methods
            poor_methods = [
                method for method, results in test_results.items()
                if results.get('success_rate', 0) < self.test_config['min_success_rate']
            ]
            
            if poor_methods:
                recommendations.append(f"Improve or disable underperforming methods: {', '.join(poor_methods)}")
            
            # Find slow methods
            slow_methods = [
                method for method, results in test_results.items()
                if results.get('avg_processing_time', 0) > self.test_config['max_processing_time']
            ]
            
            if slow_methods:
                recommendations.append(f"Optimize processing time for: {', '.join(slow_methods)}")
            
            # Find best performing method
            best_method = max(test_results.items(), key=lambda x: x[1].get('success_rate', 0))
            if best_method[1].get('success_rate', 0) > 0.80:
                recommendations.append(f"Consider prioritizing '{best_method[0]}' method - highest success rate at {best_method[1].get('success_rate', 0):.1%}")
            
            # Overall performance assessment
            overall_success = statistics.mean([r.get('success_rate', 0) for r in test_results.values()])
            if overall_success < 0.70:
                recommendations.append("Overall system performance is below target - consider comprehensive review")
            
        except Exception as e:
            self.logger.error(f"❌ Recommendation generation failed: {e}")
        
        return recommendations

    def store_test_batch_results(self, test_id: str, test_results: Dict):
        """Store test batch results summary"""
        try:
            # Store quality metrics
            conn = sqlite3.connect('data/enrichment_testing.db')
            
            for method, results in test_results.items():
                # Store success rate metric
                conn.execute('''
                    INSERT INTO quality_metrics (
                        metric_name, metric_value, metric_type, measurement_date, method_name
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    'success_rate',
                    results.get('success_rate', 0),
                    'performance',
                    datetime.now().isoformat(),
                    method
                ))
                
                # Store processing time metric
                conn.execute('''
                    INSERT INTO quality_metrics (
                        metric_name, metric_value, metric_type, measurement_date, method_name
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    'processing_time',
                    results.get('avg_processing_time', 0),
                    'performance',
                    datetime.now().isoformat(),
                    method
                ))
            
            conn.commit()
            conn.close()
            
            # Save detailed report to file
            os.makedirs('test_reports', exist_ok=True)
            report_file = f"test_reports/test_report_{test_id}.json"
            
            with open(report_file, 'w') as f:
                json.dump(test_results, f, indent=2)
            
            self.logger.info(f"📊 Test batch results stored: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store test batch results: {e}")

    def start_continuous_testing(self):
        """Start continuous testing process"""
        def testing_loop():
            while True:
                try:
                    self.logger.info("🔄 Starting continuous testing cycle")
                    
                    # Run comprehensive test suite
                    test_results = self.run_comprehensive_test_suite()
                    
                    if test_results:
                        self.logger.info(f"✅ Testing cycle complete - Quality Score: {test_results.get('quality_score', 0)}")
                    
                    # Wait for next test cycle
                    time.sleep(self.test_config['test_frequency'])
                    
                except Exception as e:
                    self.logger.error(f"❌ Continuous testing error: {e}")
                    time.sleep(300)  # Wait 5 minutes before retrying
        
        # Start testing thread
        testing_thread = threading.Thread(target=testing_loop)
        testing_thread.daemon = True
        testing_thread.start()
        
        self.logger.info("🔄 Continuous testing started")


def main():
    """Test the Enrichment Testing Framework"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrichment Testing Framework - Continuous Validation')
    parser.add_argument('--test', action='store_true', help='Run comprehensive test suite')
    parser.add_argument('--add-test-lead', action='store_true', help='Add a test lead')
    parser.add_argument('--continuous', action='store_true', help='Start continuous testing')
    parser.add_argument('--report', help='Generate report for test ID')
    
    args = parser.parse_args()
    
    framework = EnrichmentTestingFramework()
    
    if args.test:
        print("🧪 Running comprehensive test suite...")
        
        # Add some sample verified test leads first
        sample_leads = [
            {
                'full_name': 'John Smith',
                'company': 'Tech Corp',
                'linkedin_url': 'https://linkedin.com/in/johnsmith',
                'verified_email': 'john.smith@techcorp.com',
                'job_title': 'CEO',
                'verification_method': 'manual'
            },
            {
                'full_name': 'Jane Doe',
                'company': 'Marketing Inc',
                'linkedin_url': 'https://linkedin.com/in/janedoe',
                'verified_email': 'jane.doe@marketinginc.com',
                'job_title': 'Director',
                'verification_method': 'manual'
            }
        ]
        
        for lead in sample_leads:
            framework.add_verified_test_lead(lead)
        
        # Run tests
        results = framework.run_comprehensive_test_suite()
        
        if results:
            print("\n" + "="*50)
            print("TEST RESULTS SUMMARY")
            print("="*50)
            
            summary = results.get('overall_summary', {})
            print(f"Overall Success Rate: {summary.get('overall_success_rate', 0):.1%}")
            print(f"Quality Grade: {summary.get('quality_grade', 'N/A')}")
            print(f"Quality Score: {results.get('quality_score', 0)}/100")
            
            print("\nMethod Performance:")
            for method, details in results.get('method_details', {}).items():
                status = "✅" if details['meets_threshold'] else "❌"
                print(f"  {status} {method}: {details['success_rate']:.1%} (Grade: {details['performance_grade']})")
            
            print("\nRecommendations:")
            for rec in results.get('recommendations', []):
                print(f"  • {rec}")
        
    elif args.add_test_lead:
        print("➕ Adding test lead...")
        
        lead = {
            'full_name': input("Full Name: "),
            'company': input("Company: "),
            'linkedin_url': input("LinkedIn URL: "),
            'verified_email': input("Verified Email: "),
            'job_title': input("Job Title: "),
            'verification_method': 'manual'
        }
        
        framework.add_verified_test_lead(lead)
        print("✅ Test lead added successfully")
        
    elif args.continuous:
        print("🔄 Starting continuous testing...")
        framework.start_continuous_testing()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Continuous testing stopped")
    
    elif args.report:
        print(f"📊 Generating report for test: {args.report}")
        # This would load and display a specific test report
        print("Report generation not implemented yet")
    
    else:
        print("🧪 Enrichment Testing Framework Ready!")
        print("Use --test, --add-test-lead, --continuous, or --report options")

if __name__ == "__main__":
    main()
