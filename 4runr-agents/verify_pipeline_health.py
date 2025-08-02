#!/usr/bin/env python3
"""
Pipeline Health Validator

This script validates the health and integrity of the validation-first pipeline:
- Scans all pipeline files (raw, verified, enriched, engaged)
- Checks required fields and data quality
- Flags stale or duplicate UUIDs
- Ensures consistent progression through pipeline
- Validates JSON schema compliance
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline-health')

class PipelineHealthValidator:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / 'shared'
        self.logs_dir = Path(__file__).parent / 'logs'
        
        # Pipeline files
        self.pipeline_files = {
            'raw_leads': self.shared_dir / 'raw_leads.json',
            'verified_leads': self.shared_dir / 'verified_leads.json',
            'enriched_leads': self.shared_dir / 'enriched_leads.json',
            'engaged_leads': self.shared_dir / 'engaged_leads.json',
            'dropped_leads': self.shared_dir / 'dropped_leads.json'
        }
        
        # Required fields for each stage
        self.required_fields = {
            'raw_leads': ['lead_id', 'name', 'linkedin_url', 'scraped_at'],
            'verified_leads': ['lead_id', 'name', 'linkedin_url', 'verified', 'verified_at'],
            'enriched_leads': ['lead_id', 'name', 'linkedin_url', 'verified', 'enriched', 'enriched_at'],
            'engaged_leads': ['lead_id', 'name', 'linkedin_url', 'verified', 'enriched', 'contacted_at'],
            'dropped_leads': ['lead_id', 'name', 'dropped_reason', 'dropped_at']
        }
        
        # Validation results
        self.health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'unknown',
            'files': {},
            'data_quality': {},
            'pipeline_flow': {},
            'issues': [],
            'recommendations': []
        }
    
    def load_pipeline_file(self, file_path: Path) -> List[Dict]:
        """Load and validate JSON file"""
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in {file_path.name}: {str(e)}")
            self.health_report['issues'].append(f"Invalid JSON in {file_path.name}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"❌ Error loading {file_path.name}: {str(e)}")
            self.health_report['issues'].append(f"Error loading {file_path.name}: {str(e)}")
            return []
    
    def validate_required_fields(self, stage: str, leads: List[Dict]) -> Dict:
        """Validate required fields for a pipeline stage"""
        required = self.required_fields.get(stage, [])
        validation_result = {
            'total_leads': len(leads),
            'valid_leads': 0,
            'missing_fields': defaultdict(int),
            'field_coverage': {}
        }
        
        for lead in leads:
            valid = True
            for field in required:
                if field not in lead or not lead[field]:
                    validation_result['missing_fields'][field] += 1
                    valid = False
            
            if valid:
                validation_result['valid_leads'] += 1
        
        # Calculate field coverage
        for field in required:
            missing_count = validation_result['missing_fields'][field]
            coverage = ((len(leads) - missing_count) / len(leads) * 100) if leads else 100
            validation_result['field_coverage'][field] = round(coverage, 1)
        
        return validation_result
    
    def validate_data_quality(self, leads: List[Dict], stage: str) -> Dict:
        """Validate data quality and detect fake data"""
        quality_result = {
            'fake_data_detected': False,
            'fake_indicators': [],
            'email_quality': {},
            'url_quality': {},
            'name_quality': {}
        }
        
        # Fake data indicators
        fake_indicators = [
            'fake', 'mock', 'test@example.com', 'placeholder', 
            'generated', 'random', 'sample', 'dummy'
        ]
        
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        linkedin_pattern = re.compile(r'^https://www\.linkedin\.com/in/[a-zA-Z0-9-]+/?$')
        
        valid_emails = 0
        valid_urls = 0
        valid_names = 0
        
        for lead in leads:
            # Check for fake data indicators
            for key, value in lead.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    for indicator in fake_indicators:
                        if indicator in value_lower:
                            quality_result['fake_data_detected'] = True
                            quality_result['fake_indicators'].append(f"{key}: {value}")
            
            # Validate email format
            email = lead.get('email', '')
            if email:
                if email_pattern.match(email):
                    valid_emails += 1
            
            # Validate LinkedIn URL format
            linkedin_url = lead.get('linkedin_url', '')
            if linkedin_url:
                if linkedin_pattern.match(linkedin_url):
                    valid_urls += 1
            
            # Validate name format (basic check)
            name = lead.get('name', '')
            if name and len(name.split()) >= 2 and name.replace(' ', '').isalpha():
                valid_names += 1
        
        # Calculate quality percentages
        total_leads = len(leads)
        if total_leads > 0:
            quality_result['email_quality'] = {
                'valid_count': valid_emails,
                'total_with_email': len([l for l in leads if l.get('email')]),
                'validity_rate': round((valid_emails / len([l for l in leads if l.get('email')]) * 100) if [l for l in leads if l.get('email')] else 0, 1)
            }
            
            quality_result['url_quality'] = {
                'valid_count': valid_urls,
                'total_count': total_leads,
                'validity_rate': round((valid_urls / total_leads * 100), 1)
            }
            
            quality_result['name_quality'] = {
                'valid_count': valid_names,
                'total_count': total_leads,
                'validity_rate': round((valid_names / total_leads * 100), 1)
            }
        
        return quality_result
    
    def check_uuid_integrity(self, all_leads: Dict[str, List[Dict]]) -> Dict:
        """Check for duplicate or missing UUIDs across pipeline"""
        uuid_analysis = {
            'total_unique_uuids': 0,
            'duplicates': [],
            'missing_uuids': [],
            'uuid_progression': {}
        }
        
        all_uuids = set()
        uuid_to_stages = defaultdict(list)
        
        # Collect all UUIDs
        for stage, leads in all_leads.items():
            if stage == 'dropped_leads':
                continue  # Dropped leads are separate
                
            for lead in leads:
                lead_id = lead.get('lead_id')
                if not lead_id:
                    uuid_analysis['missing_uuids'].append(f"{stage}: {lead.get('name', 'Unknown')}")
                else:
                    all_uuids.add(lead_id)
                    uuid_to_stages[lead_id].append(stage)
        
        uuid_analysis['total_unique_uuids'] = len(all_uuids)
        
        # Check for duplicates within stages
        for stage, leads in all_leads.items():
            if stage == 'dropped_leads':
                continue
                
            stage_uuids = [lead.get('lead_id') for lead in leads if lead.get('lead_id')]
            duplicates_in_stage = [uuid for uuid in set(stage_uuids) if stage_uuids.count(uuid) > 1]
            
            if duplicates_in_stage:
                uuid_analysis['duplicates'].extend([f"{stage}: {uuid}" for uuid in duplicates_in_stage])
        
        # Analyze UUID progression through pipeline
        for uuid, stages in uuid_to_stages.items():
            uuid_analysis['uuid_progression'][uuid] = stages
        
        return uuid_analysis
    
    def check_pipeline_progression(self, all_leads: Dict[str, List[Dict]]) -> Dict:
        """Check logical progression through pipeline stages"""
        progression_analysis = {
            'stage_counts': {},
            'progression_issues': [],
            'conversion_rates': {},
            'stale_leads': []
        }
        
        # Count leads at each stage
        for stage, leads in all_leads.items():
            progression_analysis['stage_counts'][stage] = len(leads)
        
        # Check for logical progression issues
        raw_count = progression_analysis['stage_counts'].get('raw_leads', 0)
        verified_count = progression_analysis['stage_counts'].get('verified_leads', 0)
        enriched_count = progression_analysis['stage_counts'].get('enriched_leads', 0)
        engaged_count = progression_analysis['stage_counts'].get('engaged_leads', 0)
        
        # Verify counts make sense
        if verified_count > raw_count:
            progression_analysis['progression_issues'].append("More verified leads than raw leads")
        
        if enriched_count > verified_count:
            progression_analysis['progression_issues'].append("More enriched leads than verified leads")
        
        if engaged_count > enriched_count:
            progression_analysis['progression_issues'].append("More engaged leads than enriched leads")
        
        # Calculate conversion rates
        if raw_count > 0:
            progression_analysis['conversion_rates']['verification_rate'] = round((verified_count / raw_count * 100), 1)
        
        if verified_count > 0:
            progression_analysis['conversion_rates']['enrichment_rate'] = round((enriched_count / verified_count * 100), 1)
        
        if enriched_count > 0:
            progression_analysis['conversion_rates']['engagement_rate'] = round((engaged_count / enriched_count * 100), 1)
        
        # Check for stale leads (older than 24 hours without progression)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for stage, leads in all_leads.items():
            if stage == 'dropped_leads':
                continue
                
            for lead in leads:
                # Check various timestamp fields
                timestamps = []
                for field in ['scraped_at', 'verified_at', 'enriched_at', 'contacted_at']:
                    if field in lead and lead[field]:
                        try:
                            timestamps.append(datetime.fromisoformat(lead[field].replace('Z', '+00:00')))
                        except:
                            pass
                
                if timestamps:
                    latest_timestamp = max(timestamps)
                    if latest_timestamp < cutoff_time:
                        progression_analysis['stale_leads'].append({
                            'stage': stage,
                            'lead_id': lead.get('lead_id'),
                            'name': lead.get('name'),
                            'last_updated': latest_timestamp.isoformat()
                        })
        
        return progression_analysis
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health analysis"""
        recommendations = []
        
        # Check overall pipeline health
        total_issues = len(self.health_report['issues'])
        
        if total_issues == 0:
            recommendations.append("✅ Pipeline is healthy - no critical issues detected")
        else:
            recommendations.append(f"⚠️ {total_issues} issues detected - review and fix")
        
        # Check for fake data
        for stage, quality in self.health_report['data_quality'].items():
            if quality.get('fake_data_detected'):
                recommendations.append(f"🚨 CRITICAL: Fake data detected in {stage} - investigate immediately")
        
        # Check conversion rates
        progression = self.health_report['pipeline_flow']
        conversion_rates = progression.get('conversion_rates', {})
        
        verification_rate = conversion_rates.get('verification_rate', 0)
        if verification_rate < 50:
            recommendations.append(f"📉 Low verification rate ({verification_rate}%) - check LinkedIn URL quality")
        
        enrichment_rate = conversion_rates.get('enrichment_rate', 0)
        if enrichment_rate < 30:
            recommendations.append(f"📉 Low enrichment rate ({enrichment_rate}%) - improve email discovery methods")
        
        # Check for stale leads
        stale_count = len(progression.get('stale_leads', []))
        if stale_count > 0:
            recommendations.append(f"⏰ {stale_count} stale leads detected - consider pipeline optimization")
        
        # Check for missing files
        for stage, file_info in self.health_report['files'].items():
            if not file_info['exists'] and stage in ['raw_leads', 'verified_leads']:
                recommendations.append(f"📁 Missing {stage}.json - run corresponding agent")
        
        return recommendations
    
    def run_health_check(self) -> Dict:
        """Run complete pipeline health check"""
        logger.info("🔍 Starting Pipeline Health Validation")
        
        # Load all pipeline files
        all_leads = {}
        for stage, file_path in self.pipeline_files.items():
            leads = self.load_pipeline_file(file_path)
            all_leads[stage] = leads
            
            # File existence and basic info
            self.health_report['files'][stage] = {
                'exists': file_path.exists(),
                'path': str(file_path),
                'lead_count': len(leads),
                'file_size': file_path.stat().st_size if file_path.exists() else 0
            }
            
            if leads:
                # Validate required fields
                field_validation = self.validate_required_fields(stage, leads)
                self.health_report['files'][stage]['field_validation'] = field_validation
                
                # Validate data quality
                quality_validation = self.validate_data_quality(leads, stage)
                self.health_report['data_quality'][stage] = quality_validation
                
                logger.info(f"📊 {stage}: {len(leads)} leads, {field_validation['valid_leads']} valid")
                
                if quality_validation['fake_data_detected']:
                    logger.error(f"🚨 FAKE DATA DETECTED in {stage}!")
                    for indicator in quality_validation['fake_indicators']:
                        logger.error(f"   - {indicator}")
        
        # Check UUID integrity
        uuid_analysis = self.check_uuid_integrity(all_leads)
        self.health_report['uuid_integrity'] = uuid_analysis
        
        # Check pipeline progression
        progression_analysis = self.check_pipeline_progression(all_leads)
        self.health_report['pipeline_flow'] = progression_analysis
        
        # Generate recommendations
        self.health_report['recommendations'] = self.generate_recommendations()
        
        # Determine overall health
        critical_issues = len([issue for issue in self.health_report['issues'] if 'CRITICAL' in issue])
        fake_data_detected = any(
            quality.get('fake_data_detected', False) 
            for quality in self.health_report['data_quality'].values()
        )
        
        if critical_issues > 0 or fake_data_detected:
            self.health_report['overall_health'] = 'critical'
        elif len(self.health_report['issues']) > 0:
            self.health_report['overall_health'] = 'warning'
        else:
            self.health_report['overall_health'] = 'healthy'
        
        return self.health_report
    
    def print_health_report(self):
        """Print formatted health report"""
        report = self.health_report
        
        print("\n" + "="*80)
        print("🏥 PIPELINE HEALTH REPORT")
        print("="*80)
        
        # Overall health
        health_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '🚨'
        }
        
        overall_health = report['overall_health']
        print(f"\n{health_emoji.get(overall_health, '❓')} OVERALL HEALTH: {overall_health.upper()}")
        
        # File status
        print(f"\n📁 PIPELINE FILES:")
        for stage, file_info in report['files'].items():
            status = "✅" if file_info['exists'] else "❌"
            print(f"   {status} {stage}: {file_info['lead_count']} leads")
            
            if file_info.get('field_validation'):
                fv = file_info['field_validation']
                coverage = min(fv['field_coverage'].values()) if fv['field_coverage'] else 0
                print(f"      Field coverage: {coverage}% ({fv['valid_leads']}/{fv['total_leads']} valid)")
        
        # Data quality
        print(f"\n🔍 DATA QUALITY:")
        for stage, quality in report['data_quality'].items():
            fake_status = "🚨 FAKE DATA" if quality['fake_data_detected'] else "✅ Clean"
            print(f"   {stage}: {fake_status}")
            
            if quality.get('email_quality'):
                eq = quality['email_quality']
                print(f"      Email validity: {eq['validity_rate']}% ({eq['valid_count']}/{eq['total_with_email']})")
            
            if quality.get('url_quality'):
                uq = quality['url_quality']
                print(f"      URL validity: {uq['validity_rate']}% ({uq['valid_count']}/{uq['total_count']})")
        
        # Pipeline flow
        print(f"\n🔄 PIPELINE FLOW:")
        flow = report['pipeline_flow']
        for stage, count in flow['stage_counts'].items():
            print(f"   {stage}: {count} leads")
        
        if flow.get('conversion_rates'):
            print(f"\n📊 CONVERSION RATES:")
            for rate_name, rate_value in flow['conversion_rates'].items():
                print(f"   {rate_name}: {rate_value}%")
        
        # Issues
        if report['issues']:
            print(f"\n❌ ISSUES DETECTED:")
            for issue in report['issues']:
                print(f"   - {issue}")
        
        # Recommendations
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   - {rec}")
        
        print("\n" + "="*80)
        print(f"Report generated: {report['timestamp']}")
        print("="*80)
    
    def save_health_report(self):
        """Save health report to file"""
        self.logs_dir.mkdir(exist_ok=True)
        report_file = self.logs_dir / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.health_report, f, indent=2)
        
        logger.info(f"💾 Health report saved to {report_file}")

def main():
    """Main entry point"""
    validator = PipelineHealthValidator()
    
    # Run health check
    health_report = validator.run_health_check()
    
    # Print report
    validator.print_health_report()
    
    # Save report
    validator.save_health_report()
    
    # Return appropriate exit code
    overall_health = health_report['overall_health']
    if overall_health == 'critical':
        return False
    elif overall_health == 'warning':
        logger.warning("⚠️ Pipeline has warnings but is functional")
        return True
    else:
        logger.info("✅ Pipeline is healthy")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)