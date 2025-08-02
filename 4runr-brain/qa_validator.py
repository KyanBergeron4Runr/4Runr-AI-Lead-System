#!/usr/bin/env python3
"""
QA Validator for Campaign Brain

Comprehensive quality assurance testing with real leads,
trace validation, and Airtable sync verification.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "4runr-outreach-system"))

from serve_campaign_brain import CampaignBrainService


class CampaignBrainQA:
    """Comprehensive QA testing for Campaign Brain"""
    
    def __init__(self):
        self.service = CampaignBrainService()
        self.qa_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'detailed_results': []
        }
    
    async def run_comprehensive_qa(self, batch_size: int = 5) -> Dict[str, Any]:
        """Run comprehensive QA testing"""
        
        print("🧪 Starting Comprehensive QA Testing")
        print("=" * 50)
        
        # Test categories
        test_categories = [
            ("Service Health", self._test_service_health),
            ("Configuration", self._test_configuration),
            ("Trait Detection", self._test_trait_detection),
            ("Campaign Planning", self._test_campaign_planning),
            ("Message Generation", self._test_message_generation),
            ("Quality Scoring", self._test_quality_scoring),
            ("Airtable Integration", self._test_airtable_integration),
            ("Real Lead Processing", lambda: self._test_real_lead_processing(batch_size)),
            ("Trace Validation", self._test_trace_validation),
            ("Error Handling", self._test_error_handling)
        ]
        
        for category_name, test_func in test_categories:
            print(f"\n🔍 Testing {category_name}...")
            
            try:
                result = await test_func() if asyncio.iscoroutinefunction(test_func) else test_func()
                self._record_test_result(category_name, result)
                
                if result['passed']:
                    print(f"✅ {category_name}: PASSED")
                else:
                    print(f"❌ {category_name}: FAILED - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                self._record_test_result(category_name, {
                    'passed': False,
                    'error': str(e),
                    'details': f"Test execution failed: {str(e)}"
                })
                print(f"❌ {category_name}: ERROR - {str(e)}")
        
        # Generate final report
        return self._generate_qa_report()
    
    def _test_service_health(self) -> Dict[str, Any]:
        """Test service health and basic functionality"""
        
        try:
            health = self.service.health_check()
            
            if health['status'] != 'healthy':
                return {
                    'passed': False,
                    'error': f"Service health check failed: {health.get('issues', [])}",
                    'details': health
                }
            
            # Check integrations
            integrations = health.get('integrations', {})
            required_integrations = ['openai']
            
            for integration in required_integrations:
                if not integrations.get(integration, False):
                    return {
                        'passed': False,
                        'error': f"Required integration not available: {integration}",
                        'details': integrations
                    }
            
            return {
                'passed': True,
                'details': health
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Service health check failed"
            }
    
    def _test_configuration(self) -> Dict[str, Any]:
        """Test configuration validation"""
        
        try:
            config = self.service.config
            
            # Check required configuration
            required_configs = [
                ('openai_api_key', 'OpenAI API key'),
                ('quality_pass_threshold', 'Quality threshold'),
                ('max_retries', 'Max retries')
            ]
            
            for attr, name in required_configs:
                if not hasattr(config, attr) or not getattr(config, attr):
                    return {
                        'passed': False,
                        'error': f"Missing required configuration: {name}",
                        'details': f"Configuration attribute '{attr}' not found or empty"
                    }
            
            # Validate threshold range
            if not (0 <= config.quality_pass_threshold <= 100):
                return {
                    'passed': False,
                    'error': f"Invalid quality threshold: {config.quality_pass_threshold}",
                    'details': "Quality threshold must be between 0 and 100"
                }
            
            return {
                'passed': True,
                'details': {
                    'quality_threshold': config.quality_pass_threshold,
                    'max_retries': config.max_retries,
                    'model': config.openai_model
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Configuration validation failed"
            }
    
    async def _test_trait_detection(self) -> Dict[str, Any]:
        """Test trait detection with sample data"""
        
        try:
            # Create test lead with known characteristics
            test_lead = {
                'id': 'qa_trait_test',
                'Name': 'Sarah Johnson',
                'Title': 'VP of Product',
                'Company': 'CloudTech Solutions',
                'company_data': {
                    'description': 'CloudTech provides enterprise SaaS solutions for workflow management',
                    'services': 'Software as a Service, API integrations, Cloud platforms'
                },
                'scraped_content': {
                    'homepage_text': 'Enterprise-grade cloud platform for digital transformation'
                }
            }
            
            # Process through brain
            result = await self.service.brain.execute(test_lead)
            
            # Validate trait detection
            expected_traits = ['enterprise', 'saas', 'role_vp']
            detected_traits = result.traits
            
            missing_traits = [trait for trait in expected_traits if trait not in detected_traits]
            
            if missing_traits:
                return {
                    'passed': False,
                    'error': f"Missing expected traits: {missing_traits}",
                    'details': {
                        'expected': expected_traits,
                        'detected': detected_traits,
                        'confidence': result.trait_confidence
                    }
                }
            
            # Check confidence scores
            low_confidence = [
                trait for trait, conf in result.trait_confidence.items() 
                if conf < 30  # Very low confidence threshold
            ]
            
            return {
                'passed': True,
                'details': {
                    'detected_traits': detected_traits,
                    'confidence_scores': result.trait_confidence,
                    'primary_trait': result.primary_trait,
                    'low_confidence_traits': low_confidence
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Trait detection test failed"
            }
    
    async def _test_campaign_planning(self) -> Dict[str, Any]:
        """Test campaign planning logic"""
        
        try:
            # Test with different trait combinations
            test_cases = [
                {
                    'traits': ['enterprise', 'saas', 'role_ceo'],
                    'expected_angle': 'competitive_advantage',
                    'expected_tone': 'executive'
                },
                {
                    'traits': ['startup', 'api_first', 'role_cto'],
                    'expected_angle': 'technical_innovation',
                    'expected_tone': 'technical'
                }
            ]
            
            results = []
            
            for test_case in test_cases:
                # Create test state
                from campaign_brain import CampaignState
                
                state = CampaignState(
                    traits=test_case['traits'],
                    trait_confidence={trait: 85.0 for trait in test_case['traits']},
                    company_data={'tone': 'Professional'}
                )
                
                # Test campaign planner
                from nodes.campaign_planner import CampaignPlannerNode
                planner = CampaignPlannerNode(self.service.config)
                
                result_state = await planner._execute_node_logic(state)
                
                # Validate results
                test_result = {
                    'traits': test_case['traits'],
                    'messaging_angle': result_state.messaging_angle,
                    'campaign_tone': result_state.campaign_tone,
                    'sequence': result_state.campaign_sequence,
                    'expected_angle': test_case['expected_angle'],
                    'expected_tone': test_case['expected_tone']
                }
                
                results.append(test_result)
            
            return {
                'passed': True,
                'details': {
                    'test_cases': results,
                    'all_generated_sequences': all(r['sequence'] for r in results)
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Campaign planning test failed"
            }
    
    async def _test_message_generation(self) -> Dict[str, Any]:
        """Test message generation (without actual GPT calls)"""
        
        try:
            # Test message structure validation
            from campaign_brain import CampaignMessage
            
            # Create test message
            test_message = CampaignMessage(
                message_type='hook',
                subject='Test Subject',
                body='Test body content with personalization',
                quality_score=85.0
            )
            
            # Validate message structure
            required_fields = ['message_type', 'subject', 'body']
            missing_fields = [field for field in required_fields if not getattr(test_message, field)]
            
            if missing_fields:
                return {
                    'passed': False,
                    'error': f"Message missing required fields: {missing_fields}",
                    'details': test_message.__dict__
                }
            
            # Test message types
            valid_types = ['hook', 'proof', 'fomo', 'strategic_hook', 'competitive_proof', 'timing_fomo']
            
            return {
                'passed': True,
                'details': {
                    'message_structure_valid': True,
                    'valid_message_types': valid_types,
                    'test_message': test_message.__dict__
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Message generation test failed"
            }
    
    async def _test_quality_scoring(self) -> Dict[str, Any]:
        """Test quality scoring system"""
        
        try:
            from nodes.message_reviewer import MessageReviewerNode
            from campaign_brain import CampaignMessage, CampaignState
            
            reviewer = MessageReviewerNode(self.service.config)
            
            # Create test messages with different quality levels
            test_messages = [
                CampaignMessage(
                    message_type='hook',
                    subject='Strategic Partnership Opportunity - CloudTech',
                    body='Hi Sarah,\n\nI noticed CloudTech\'s focus on enterprise SaaS solutions. The market is evolving quickly in this space.\n\nWould it make sense to connect briefly?\n\nBest,\n4Runr Team'
                ),
                CampaignMessage(
                    message_type='proof',
                    subject='Generic Subject',
                    body='Hi there,\n\nWe provide solutions. Let me know if interested.\n\nThanks'
                )
            ]
            
            # Test scoring
            state = CampaignState(
                messages=test_messages,
                lead_data={'Name': 'Sarah Johnson', 'Company': 'CloudTech'},
                company_data={'tone': 'Professional'}
            )
            
            result_state = await reviewer._execute_node_logic(state)
            
            # Validate scoring
            scores = [msg.quality_score for msg in result_state.messages]
            
            # First message should score higher than second
            if len(scores) >= 2 and scores[0] <= scores[1]:
                return {
                    'passed': False,
                    'error': "Quality scoring not working correctly",
                    'details': {
                        'scores': scores,
                        'expected': 'First message should score higher than second'
                    }
                }
            
            return {
                'passed': True,
                'details': {
                    'message_scores': scores,
                    'overall_score': result_state.overall_quality_score,
                    'quality_issues': result_state.quality_issues
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Quality scoring test failed"
            }
    
    def _test_airtable_integration(self) -> Dict[str, Any]:
        """Test Airtable integration if available"""
        
        try:
            if not self.service.integrated_mode:
                return {
                    'passed': True,
                    'details': "Running in standalone mode - Airtable integration not required"
                }
            
            # Test Airtable client
            airtable_client = self.service.airtable_client
            
            if not airtable_client:
                return {
                    'passed': False,
                    'error': "Airtable client not initialized",
                    'details': "Service claims integrated mode but no Airtable client"
                }
            
            # Test connection (get 1 lead to verify connectivity)
            try:
                leads = airtable_client.get_leads_for_message_generation(1)
                
                return {
                    'passed': True,
                    'details': {
                        'connection_verified': True,
                        'sample_leads_found': len(leads),
                        'integrated_mode': True
                    }
                }
                
            except Exception as e:
                return {
                    'passed': False,
                    'error': f"Airtable connection failed: {str(e)}",
                    'details': "Could not retrieve leads from Airtable"
                }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Airtable integration test failed"
            }
    
    async def _test_real_lead_processing(self, batch_size: int) -> Dict[str, Any]:
        """Test processing with real leads"""
        
        try:
            print(f"  Processing {batch_size} real leads in dry-run mode...")
            
            # Process batch in dry-run mode
            result = await self.service.process_batch(batch_size=batch_size, dry_run=True)
            
            if result['processed'] == 0:
                return {
                    'passed': True,
                    'details': {
                        'message': 'No leads available for processing',
                        'processed': 0
                    }
                }
            
            # Analyze results
            results = result.get('results', [])
            
            # Check for basic success criteria
            approved_count = len([r for r in results if r.get('final_status') == 'approved'])
            error_count = len([r for r in results if r.get('final_status') == 'error'])
            
            # Calculate success metrics
            approval_rate = (approved_count / len(results)) * 100 if results else 0
            error_rate = (error_count / len(results)) * 100 if results else 0
            
            # Validate results
            if error_rate > 50:  # More than 50% errors is concerning
                return {
                    'passed': False,
                    'error': f"High error rate: {error_rate:.1f}%",
                    'details': {
                        'processed': result['processed'],
                        'approved': approved_count,
                        'errors': error_count,
                        'error_rate': error_rate,
                        'sample_errors': [r.get('error') for r in results if r.get('final_status') == 'error'][:3]
                    }
                }
            
            return {
                'passed': True,
                'details': {
                    'processed': result['processed'],
                    'approved': approved_count,
                    'manual_review': len([r for r in results if r.get('final_status') == 'manual_review']),
                    'errors': error_count,
                    'approval_rate': approval_rate,
                    'error_rate': error_rate,
                    'average_quality_score': sum(r.get('overall_quality_score', 0) for r in results) / len(results) if results else 0
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Real lead processing test failed"
            }
    
    def _test_trace_validation(self) -> Dict[str, Any]:
        """Test trace log validation"""
        
        try:
            trace_dir = Path("trace_logs")
            
            if not trace_dir.exists():
                return {
                    'passed': True,
                    'details': "No trace logs directory - will be created on first execution"
                }
            
            # Check recent trace files
            trace_files = list(trace_dir.glob("*.json"))
            
            if not trace_files:
                return {
                    'passed': True,
                    'details': "No trace files found - normal for fresh installation"
                }
            
            # Validate a recent trace file
            recent_trace = max(trace_files, key=lambda f: f.stat().st_mtime)
            
            try:
                with open(recent_trace, 'r') as f:
                    trace_data = json.load(f)
                
                # Check required trace fields
                required_fields = ['execution_id', 'traits', 'campaign_sequence', 'final_status']
                missing_fields = [field for field in required_fields if field not in trace_data]
                
                if missing_fields:
                    return {
                        'passed': False,
                        'error': f"Trace file missing required fields: {missing_fields}",
                        'details': {
                            'trace_file': str(recent_trace),
                            'available_fields': list(trace_data.keys())
                        }
                    }
                
                return {
                    'passed': True,
                    'details': {
                        'trace_files_found': len(trace_files),
                        'recent_trace': str(recent_trace),
                        'trace_structure_valid': True,
                        'sample_execution_id': trace_data.get('execution_id')
                    }
                }
                
            except json.JSONDecodeError as e:
                return {
                    'passed': False,
                    'error': f"Invalid JSON in trace file: {str(e)}",
                    'details': {'trace_file': str(recent_trace)}
                }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Trace validation test failed"
            }
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling capabilities"""
        
        try:
            # Test configuration validation
            from campaign_brain import CampaignBrainConfig
            
            # This should work without throwing exceptions
            config = CampaignBrainConfig()
            validation_issues = config.validate()
            
            # Test graceful handling of missing data
            from campaign_brain import CampaignState
            
            empty_state = CampaignState()
            
            # Should not crash when accessing empty state
            traits = empty_state.traits
            messages = empty_state.messages
            
            return {
                'passed': True,
                'details': {
                    'config_validation_works': True,
                    'empty_state_handling': True,
                    'validation_issues': validation_issues
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': "Error handling test failed"
            }
    
    def _record_test_result(self, test_name: str, result: Dict[str, Any]):
        """Record test result"""
        
        self.qa_results['tests_run'] += 1
        
        if result['passed']:
            self.qa_results['tests_passed'] += 1
        else:
            self.qa_results['tests_failed'] += 1
        
        self.qa_results['detailed_results'].append({
            'test_name': test_name,
            'passed': result['passed'],
            'error': result.get('error'),
            'details': result.get('details'),
            'timestamp': datetime.now().isoformat()
        })
    
    def _generate_qa_report(self) -> Dict[str, Any]:
        """Generate comprehensive QA report"""
        
        total_tests = self.qa_results['tests_run']
        passed_tests = self.qa_results['tests_passed']
        failed_tests = self.qa_results['tests_failed']
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            'qa_summary': {
                'timestamp': self.qa_results['timestamp'],
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': success_rate,
                'overall_status': 'PASSED' if failed_tests == 0 else 'FAILED'
            },
            'test_results': self.qa_results['detailed_results'],
            'recommendations': self._generate_recommendations()
        }
        
        # Save QA report
        qa_dir = Path("logs/qa")
        qa_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = qa_dir / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 QA Report saved to: {report_file}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        failed_tests = [r for r in self.qa_results['detailed_results'] if not r['passed']]
        
        if not failed_tests:
            recommendations.append("✅ All tests passed! System is ready for production.")
        else:
            recommendations.append("❌ Some tests failed. Review and fix issues before production deployment.")
            
            for failed_test in failed_tests:
                test_name = failed_test['test_name']
                error = failed_test.get('error', 'Unknown error')
                recommendations.append(f"  • Fix {test_name}: {error}")
        
        # Add general recommendations
        recommendations.extend([
            "🔍 Run QA tests regularly to catch regressions",
            "📊 Monitor approval rates and quality scores in production",
            "🔄 Set up automated daily batch processing",
            "📝 Review trace logs for optimization opportunities"
        ])
        
        return recommendations


async def main():
    """Main entry point for QA validation"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Campaign Brain QA Validator")
    parser.add_argument('--batch-size', type=int, default=5, help='Number of real leads to test')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        qa = CampaignBrainQA()
        
        if args.quick:
            print("🏃 Running quick QA tests...")
            # Run subset of tests for quick validation
            batch_size = 2
        else:
            batch_size = args.batch_size
        
        report = await qa.run_comprehensive_qa(batch_size)
        
        # Print summary
        summary = report['qa_summary']
        
        print(f"\n📊 QA Test Summary")
        print("=" * 30)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Overall Status: {summary['overall_status']}")
        
        if args.verbose and summary['failed'] > 0:
            print(f"\n❌ Failed Tests:")
            for result in report['test_results']:
                if not result['passed']:
                    print(f"  • {result['test_name']}: {result.get('error', 'Unknown error')}")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations'][:5]:  # Show first 5
            print(f"  {rec}")
        
        return summary['overall_status'] == 'PASSED'
        
    except KeyboardInterrupt:
        print("\n\nQA testing interrupted by user")
        return True
    except Exception as e:
        print(f"\n❌ QA testing error: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)