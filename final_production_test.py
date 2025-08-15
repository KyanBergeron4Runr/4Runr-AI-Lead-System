#!/usr/bin/env python3
"""
FINAL PRODUCTION TEST

A CLEAN test that doesn't pollute the database.
Tests the ACTUAL production system without adding test data.
"""

import os
import sys
import time
import json
import logging
import traceback
from datetime import datetime

# Import production components
from production_db_manager import db_manager
from improved_email_finder import email_finder
from company_size_validator import company_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinalProductionTest:
    """Clean production test without polluting database."""
    
    def __init__(self):
        self.test_results = {}
        self.critical_failures = []
        
    def run_production_test(self):
        """Run clean production tests."""
        logger.info("🎯 FINAL PRODUCTION TEST - CLEAN & REAL")
        logger.info("="*60)
        logger.info("Testing ACTUAL production system capabilities")
        logger.info("NO test data pollution - read-only where possible")
        logger.info("="*60)
        
        try:
            # 1. Database Status Test
            self.test_database_status()
            
            # 2. Data Quality Test (read-only)
            self.test_data_quality()
            
            # 3. Component Integration Test
            self.test_component_integration()
            
            # 4. Performance Test (minimal)
            self.test_performance()
            
            # 5. Final Assessment
            self.final_assessment()
            
        except Exception as e:
            logger.error(f"❌ Production test failed: {e}")
            logger.error(traceback.format_exc())
            return False
        
        return len(self.critical_failures) == 0
    
    def test_database_status(self):
        """Test database status and connectivity."""
        logger.info("\n🗄️ TEST 1: DATABASE STATUS")
        logger.info("-" * 40)
        
        try:
            # Get database stats
            stats = db_manager.get_database_stats()
            
            if not stats:
                self.critical_failures.append("Cannot get database statistics")
                return
            
            logger.info(f"✅ Database connection: Working")
            logger.info(f"📊 Total leads: {stats['total_leads']}")
            logger.info(f"📧 Leads with emails: {stats['leads_with_email']} ({stats['email_percentage']}%)")
            
            if stats['total_leads'] == 0:
                self.critical_failures.append("Database is empty - no leads to work with")
            
            self.test_results['database_status'] = {
                'status': 'PASS' if stats['total_leads'] > 0 else 'FAIL',
                'total_leads': stats['total_leads'],
                'email_percentage': stats['email_percentage']
            }
            
        except Exception as e:
            self.critical_failures.append(f"Database status test failed: {e}")
            logger.error(f"❌ Database status test failed: {e}")
    
    def test_data_quality(self):
        """Test actual data quality in production database."""
        logger.info("\n📊 TEST 2: DATA QUALITY VALIDATION")
        logger.info("-" * 40)
        
        try:
            # Get ALL leads from database (read-only)
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM leads")
                all_leads = cursor.fetchall()
            
            if not all_leads:
                self.critical_failures.append("No leads in database for quality validation")
                return
            
            logger.info(f"📋 Analyzing {len(all_leads)} leads...")
            
            quality_issues = []
            valid_leads = 0
            test_data_count = 0
            
            for lead in all_leads:
                lead_issues = []
                is_test_data = False
                
                # Check for test data patterns
                email_str = str(lead['email']).lower() if lead['email'] else ''
                name_str = str(lead['full_name']).lower() if lead['full_name'] else ''
                company_str = str(lead['company']).lower() if lead['company'] else ''
                
                test_patterns = [
                    'example.com', 'test.com', 'test@', 'stress.test', 'thread',
                    'integrity.', 'memory.test', 'recovery', 'boundary', 'pipeline.test',
                    'load.', 'response.', 'rapid', 'autotest'
                ]
                
                for pattern in test_patterns:
                    if pattern in email_str or pattern in name_str or pattern in company_str:
                        is_test_data = True
                        test_data_count += 1
                        break
                
                if is_test_data:
                    lead_issues.append("Test data in production database")
                
                # Check required fields
                if not lead['full_name'] or str(lead['full_name']).strip() == '':
                    lead_issues.append("Missing or empty full_name")
                
                if not lead['email'] or str(lead['email']).strip() == '':
                    lead_issues.append("Missing or empty email")
                elif '@' not in str(lead['email']) or '.' not in str(lead['email']):
                    lead_issues.append("Invalid email format")
                
                if not lead['company'] or str(lead['company']).strip() == '':
                    lead_issues.append("Missing or empty company")
                
                if lead_issues:
                    quality_issues.extend([f"Lead {lead['id']}: {issue}" for issue in lead_issues])
                else:
                    valid_leads += 1
            
            quality_percentage = (valid_leads / len(all_leads)) * 100
            
            logger.info(f"📊 Data Quality Results:")
            logger.info(f"  Total leads: {len(all_leads)}")
            logger.info(f"  Valid leads: {valid_leads}")
            logger.info(f"  Quality percentage: {quality_percentage:.1f}%")
            logger.info(f"  Test data found: {test_data_count}")
            logger.info(f"  Quality issues: {len(quality_issues)}")
            
            if test_data_count > 0:
                logger.warning(f"⚠️ Found {test_data_count} test data entries in production!")
            
            if quality_percentage < 95:
                self.critical_failures.append(f"Data quality below 95%: {quality_percentage:.1f}%")
            
            if test_data_count > 50:  # Allow some test data but not excessive
                self.critical_failures.append(f"Too much test data: {test_data_count} entries")
            
            self.test_results['data_quality'] = {
                'status': 'PASS' if quality_percentage >= 95 and test_data_count <= 50 else 'FAIL',
                'quality_percentage': quality_percentage,
                'valid_leads': valid_leads,
                'total_leads': len(all_leads),
                'test_data_count': test_data_count
            }
            
        except Exception as e:
            self.critical_failures.append(f"Data quality test failed: {e}")
            logger.error(f"❌ Data quality test failed: {e}")
    
    def test_component_integration(self):
        """Test component integration without database pollution."""
        logger.info("\n🔧 TEST 3: COMPONENT INTEGRATION")
        logger.info("-" * 40)
        
        try:
            components_working = 0
            total_components = 3
            
            # Test company validator
            logger.info("Testing company size validator...")
            try:
                result = company_validator.is_company_too_large("Microsoft")
                if result:  # Should detect Microsoft as too large
                    components_working += 1
                    logger.info("✅ Company validator: Working")
                else:
                    logger.warning("⚠️ Company validator: Unexpected result")
            except Exception as e:
                logger.error(f"❌ Company validator failed: {e}")
            
            # Test email finder
            logger.info("Testing email finder...")
            try:
                # Test with a safe, public domain
                emails = email_finder.find_business_emails("https://example.com", "Example Corp")
                components_working += 1
                logger.info(f"✅ Email finder: Working (found {len(emails)} emails)")
            except Exception as e:
                logger.error(f"❌ Email finder failed: {e}")
            
            # Test database operations (minimal)
            logger.info("Testing database operations...")
            try:
                stats = db_manager.get_database_stats()
                if stats and 'total_leads' in stats:
                    components_working += 1
                    logger.info("✅ Database operations: Working")
                else:
                    logger.error("❌ Database operations: Failed")
            except Exception as e:
                logger.error(f"❌ Database operations failed: {e}")
            
            success_rate = (components_working / total_components) * 100
            logger.info(f"🔧 Component integration: {success_rate:.1f}% ({components_working}/{total_components})")
            
            if success_rate < 100:
                self.critical_failures.append(f"Component integration incomplete: {success_rate:.1f}%")
            
            self.test_results['component_integration'] = {
                'status': 'PASS' if success_rate == 100 else 'FAIL',
                'success_rate': success_rate,
                'components_working': components_working,
                'total_components': total_components
            }
            
        except Exception as e:
            self.critical_failures.append(f"Component integration test failed: {e}")
            logger.error(f"❌ Component integration test failed: {e}")
    
    def test_performance(self):
        """Test basic performance without adding excessive data."""
        logger.info("\n⚡ TEST 4: PERFORMANCE")
        logger.info("-" * 40)
        
        try:
            # Test single operation speed
            start_time = time.time()
            stats = db_manager.get_database_stats()
            stats_time = time.time() - start_time
            
            logger.info(f"📊 Database stats query: {stats_time*1000:.2f}ms")
            
            # Test email finder speed  
            start_time = time.time()
            emails = email_finder.find_business_emails("https://example.com", "Test")
            email_time = time.time() - start_time
            
            logger.info(f"🔍 Email finder query: {email_time*1000:.2f}ms")
            
            # Test company validator speed
            start_time = time.time()
            result = company_validator.is_company_too_large("Test Company")
            validator_time = time.time() - start_time
            
            logger.info(f"🏢 Company validator: {validator_time*1000:.2f}ms")
            
            # Check if performance is acceptable
            performance_issues = []
            
            if stats_time > 1.0:  # 1 second threshold
                performance_issues.append(f"Database stats too slow: {stats_time:.2f}s")
            
            if email_time > 5.0:  # 5 second threshold for network operation
                performance_issues.append(f"Email finder too slow: {email_time:.2f}s")
            
            if validator_time > 1.0:  # 1 second threshold
                performance_issues.append(f"Company validator too slow: {validator_time:.2f}s")
            
            if performance_issues:
                self.critical_failures.extend(performance_issues)
            
            self.test_results['performance'] = {
                'status': 'PASS' if len(performance_issues) == 0 else 'FAIL',
                'stats_time_ms': stats_time * 1000,
                'email_time_ms': email_time * 1000,
                'validator_time_ms': validator_time * 1000,
                'issues': performance_issues
            }
            
        except Exception as e:
            self.critical_failures.append(f"Performance test failed: {e}")
            logger.error(f"❌ Performance test failed: {e}")
    
    def final_assessment(self):
        """Generate final assessment."""
        logger.info("\n" + "="*60)
        logger.info("🎯 FINAL PRODUCTION ASSESSMENT")
        logger.info("="*60)
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'PASS')
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        if len(self.critical_failures) == 0 and success_rate >= 90:
            overall_status = "🟢 PRODUCTION READY"
            recommendation = "DEPLOY WITH CONFIDENCE"
        elif len(self.critical_failures) <= 2 and success_rate >= 75:
            overall_status = "🟡 MINOR ISSUES"
            recommendation = "FIX MINOR ISSUES THEN DEPLOY"
        else:
            overall_status = "🔴 NOT READY"
            recommendation = "FIX CRITICAL ISSUES BEFORE DEPLOYMENT"
        
        logger.info(f"\n📊 OVERALL STATUS: {overall_status}")
        logger.info(f"🎯 RECOMMENDATION: {recommendation}")
        logger.info(f"📈 SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        # Test results summary
        logger.info(f"\n📋 TEST RESULTS:")
        for test_name, result in self.test_results.items():
            status_icon = {"PASS": "✅", "FAIL": "❌"}.get(result.get('status'), "❓")
            logger.info(f"  {status_icon} {test_name.replace('_', ' ').title()}: {result.get('status')}")
        
        # Critical failures
        if self.critical_failures:
            logger.info(f"\n🚨 CRITICAL ISSUES ({len(self.critical_failures)}):")
            for i, failure in enumerate(self.critical_failures, 1):
                logger.info(f"  {i}. ❌ {failure}")
        else:
            logger.info(f"\n🎉 NO CRITICAL ISSUES FOUND!")
        
        # Final verdict
        logger.info(f"\n" + "="*60)
        if len(self.critical_failures) == 0:
            logger.info("🎉 VERDICT: SYSTEM IS PRODUCTION READY!")
            logger.info("💪 Deploy with confidence!")
        else:
            logger.info("🛑 VERDICT: SYSTEM NEEDS FIXES!")
            logger.info("🔧 Address critical issues and re-test!")
        
        logger.info("="*60)
        
        # Save report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'recommendation': recommendation,
            'success_rate': success_rate,
            'test_results': self.test_results,
            'critical_failures': self.critical_failures
        }
        
        report_file = f"production_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\n💾 Report saved to: {report_file}")

if __name__ == "__main__":
    tester = FinalProductionTest()
    ready = tester.run_production_test()
    
    if ready:
        print(f"\n🎉 SYSTEM IS PRODUCTION READY!")
        sys.exit(0)
    else:
        print(f"\n🛑 SYSTEM NEEDS FIXES!")
        sys.exit(1)
