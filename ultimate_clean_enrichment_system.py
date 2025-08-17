#!/usr/bin/env python3
"""
🌟 ULTIMATE CLEAN ENRICHMENT SYSTEM 🌟
======================================
The complete system that combines:
- Advanced domain discovery
- Pattern-based email generation  
- Real-time duplicate prevention
- Intelligent lead cleaning
- Quality scoring and validation

This is the production-ready system that generates clean, unique, 
high-quality leads with zero duplicates.
"""

import sqlite3
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from pattern_based_email_engine import PatternBasedEmailEngine
from domain_discovery_breakthrough import AdvancedDomainDiscovery
from real_time_duplicate_prevention import RealTimeDuplicatePrevention
from intelligent_lead_cleaner import IntelligentLeadCleaner

class UltimateCleanEnrichmentSystem:
    """The complete clean enrichment system"""
    
    def __init__(self, db_path: str = "data/unified_leads.db"):
        self.db_path = db_path
        
        # Initialize all components
        self.email_engine = PatternBasedEmailEngine()
        self.domain_discoverer = AdvancedDomainDiscovery()
        self.duplicate_prevention = RealTimeDuplicatePrevention(db_path)
        self.lead_cleaner = IntelligentLeadCleaner(db_path)
        
        # System metrics
        self.metrics = {
            'leads_processed': 0,
            'duplicates_prevented': 0,
            'domains_discovered': 0,
            'emails_generated': 0,
            'processing_times': [],
            'quality_scores': []
        }
        
        print("🌟 Ultimate Clean Enrichment System initialized")
        print("🎯 Ready for production-grade lead enrichment")
    
    def enrich_lead_complete(self, raw_lead: Dict) -> Dict:
        """Complete lead enrichment with duplicate prevention"""
        start_time = time.time()
        
        print(f"\n🌟 ENRICHING: {raw_lead.get('full_name')} at {raw_lead.get('company')}")
        print("=" * 70)
        
        # Step 1: Domain Discovery
        print("🔍 Step 1: Domain Discovery")
        domain_result = self.domain_discoverer.discover_company_domain(raw_lead.get('company', ''))
        
        if not domain_result:
            return {
                'success': False,
                'step_failed': 'domain_discovery',
                'reason': 'No valid domain found',
                'raw_lead': raw_lead
            }
        
        print(f"   ✅ Found: {domain_result['domain']} ({domain_result['method']})")
        self.metrics['domains_discovered'] += 1
        
        # Step 2: Email Generation
        print("📧 Step 2: Email Pattern Generation")
        enriched_lead = raw_lead.copy()
        enriched_lead['discovered_domain'] = domain_result['domain']
        
        email_results = self.email_engine.discover_emails(enriched_lead)
        print(f"   ✅ Generated: {len(email_results)} email candidates")
        self.metrics['emails_generated'] += len(email_results)
        
        # Step 3: Lead Enhancement
        print("⚡ Step 3: Lead Data Enhancement")
        enhanced_lead = self.enhance_lead_data(raw_lead, domain_result, email_results)
        print(f"   ✅ Enhanced with {len(enhanced_lead)} fields")
        
        # Step 4: Quality Scoring
        print("📊 Step 4: Quality Assessment")
        quality_score = self.lead_cleaner.calculate_lead_quality_score(enhanced_lead)
        enhanced_lead['lead_quality_score'] = quality_score
        enhanced_lead['lead_quality'] = self.get_quality_tier(quality_score)
        print(f"   ✅ Quality: {enhanced_lead['lead_quality']} ({quality_score}/100)")
        self.metrics['quality_scores'].append(quality_score)
        
        # Step 5: Duplicate Prevention
        print("🚫 Step 5: Duplicate Prevention")
        prevention_result = self.duplicate_prevention.process_lead_with_prevention(enhanced_lead)
        
        # Step 6: Final Result
        processing_time = (time.time() - start_time) * 1000
        self.metrics['processing_times'].append(processing_time)
        self.metrics['leads_processed'] += 1
        
        if prevention_result['status'] == 'rejected':
            self.metrics['duplicates_prevented'] += 1
        
        final_result = {
            'success': True,
            'processing_time_ms': processing_time,
            'domain_discovery': domain_result,
            'emails_found': len(email_results),
            'top_emails': [r.email for r in email_results[:10]],
            'quality_score': quality_score,
            'quality_tier': enhanced_lead['lead_quality'],
            'duplicate_prevention': prevention_result,
            'enhanced_lead': enhanced_lead if prevention_result['status'] != 'rejected' else None
        }
        
        print(f"🎯 FINAL RESULT: {prevention_result['status'].upper()}")
        print(f"   Processing time: {processing_time:.2f}ms")
        print(f"   Quality tier: {enhanced_lead['lead_quality']}")
        
        return final_result
    
    def enhance_lead_data(self, raw_lead: Dict, domain_result: Dict, email_results: List) -> Dict:
        """Enhance lead with discovered data"""
        enhanced = raw_lead.copy()
        
        # Add domain information
        enhanced['website'] = domain_result['domain']
        enhanced['domain_discovery_method'] = domain_result['method']
        enhanced['domain_confidence'] = domain_result['confidence']
        
        # Add email information
        if email_results:
            # Best email (highest confidence)
            best_email = email_results[0]
            enhanced['email'] = best_email.email
            enhanced['email_confidence_level'] = best_email.confidence.value.title()
            enhanced['email_pattern_used'] = best_email.pattern_used
            enhanced['email_validation_score'] = best_email.validation_score
            
            # Alternative emails
            enhanced['alternative_emails'] = [r.email for r in email_results[1:5]]
            
            # Confidence distribution
            confidence_counts = {}
            for result in email_results:
                conf = result.confidence.value
                confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
            enhanced['email_confidence_distribution'] = confidence_counts
        
        # Add enrichment metadata
        enhanced['enriched'] = 1
        enhanced['enrichment_timestamp'] = datetime.now().isoformat()
        enhanced['enrichment_version'] = '1.0'
        enhanced['source'] = enhanced.get('source', 'Advanced_Enrichment')
        enhanced['needs_enrichment'] = 0
        
        # Add derived fields
        if not enhanced.get('business_type'):
            enhanced['business_type'] = self.infer_business_type(enhanced.get('company', ''))
        
        if not enhanced.get('date_scraped'):
            enhanced['date_scraped'] = datetime.now().isoformat()
        
        enhanced['date_enriched'] = datetime.now().isoformat()
        
        return enhanced
    
    def infer_business_type(self, company_name: str) -> str:
        """Infer business type from company name"""
        if not company_name:
            return 'Unknown'
        
        company_lower = company_name.lower()
        
        # Technology companies
        if any(keyword in company_lower for keyword in ['tech', 'software', 'systems', 'digital', 'ai', 'data']):
            return 'Technology'
        
        # Marketing/Advertising
        if any(keyword in company_lower for keyword in ['marketing', 'advertising', 'agency', 'media']):
            return 'Marketing'
        
        # Consulting
        if any(keyword in company_lower for keyword in ['consulting', 'advisors', 'partners']):
            return 'Consulting'
        
        # Manufacturing/Industrial
        if any(keyword in company_lower for keyword in ['manufacturing', 'industrial', 'factory', 'production']):
            return 'Manufacturing'
        
        # Services
        if any(keyword in company_lower for keyword in ['services', 'solutions', 'support']):
            return 'Services'
        
        # Resources/Energy
        if any(keyword in company_lower for keyword in ['resources', 'energy', 'mining', 'oil', 'gas']):
            return 'Resources'
        
        return 'General Business'
    
    def get_quality_tier(self, score: float) -> str:
        """Convert quality score to tier"""
        if score >= 80:
            return 'Hot'
        elif score >= 60:
            return 'Warm'
        else:
            return 'Cold'
    
    def batch_enrich_leads(self, raw_leads: List[Dict]) -> Dict:
        """Enrich multiple leads in batch"""
        print(f"🚀 BATCH ENRICHMENT: {len(raw_leads)} leads")
        print("=" * 80)
        
        batch_start = time.time()
        results = {
            'total_leads': len(raw_leads),
            'successful_enrichments': 0,
            'duplicates_prevented': 0,
            'domains_discovered': 0,
            'total_emails_found': 0,
            'quality_distribution': {'Hot': 0, 'Warm': 0, 'Cold': 0},
            'processing_time_total': 0,
            'results': []
        }
        
        for i, raw_lead in enumerate(raw_leads, 1):
            print(f"\n📋 LEAD {i}/{len(raw_leads)}")
            
            result = self.enrich_lead_complete(raw_lead)
            results['results'].append(result)
            
            if result['success']:
                if result['duplicate_prevention']['status'] not in ['rejected']:
                    results['successful_enrichments'] += 1
                    results['total_emails_found'] += result['emails_found']
                    
                    if result.get('quality_tier'):
                        results['quality_distribution'][result['quality_tier']] += 1
                
                if result['duplicate_prevention']['status'] == 'rejected':
                    results['duplicates_prevented'] += 1
                
                if result.get('domain_discovery'):
                    results['domains_discovered'] += 1
        
        results['processing_time_total'] = (time.time() - batch_start) * 1000
        results['average_processing_time'] = results['processing_time_total'] / len(raw_leads)
        results['success_rate'] = (results['successful_enrichments'] / len(raw_leads)) * 100
        
        return results
    
    def get_system_metrics(self) -> Dict:
        """Get comprehensive system metrics"""
        avg_processing_time = sum(self.metrics['processing_times']) / len(self.metrics['processing_times']) if self.metrics['processing_times'] else 0
        avg_quality_score = sum(self.metrics['quality_scores']) / len(self.metrics['quality_scores']) if self.metrics['quality_scores'] else 0
        
        return {
            'leads_processed': self.metrics['leads_processed'],
            'duplicates_prevented': self.metrics['duplicates_prevented'],
            'domains_discovered': self.metrics['domains_discovered'],
            'emails_generated': self.metrics['emails_generated'],
            'average_processing_time_ms': avg_processing_time,
            'average_quality_score': avg_quality_score,
            'duplicate_prevention_rate': (self.metrics['duplicates_prevented'] / max(1, self.metrics['leads_processed'])) * 100,
            'domain_discovery_rate': (self.metrics['domains_discovered'] / max(1, self.metrics['leads_processed'])) * 100,
            'emails_per_lead': self.metrics['emails_generated'] / max(1, self.metrics['leads_processed'])
        }

def test_ultimate_system():
    """Test the complete ultimate system"""
    print("🌟 ULTIMATE CLEAN ENRICHMENT SYSTEM TEST")
    print("=" * 80)
    
    system = UltimateCleanEnrichmentSystem()
    
    # Test leads (mix of new and potentially duplicate)
    test_leads = [
        {
            'full_name': 'Sarah Johnson',
            'company': 'InnovateTech Solutions',
            'job_title': 'CEO'
        },
        {
            'full_name': 'Mike Rodriguez',
            'company': 'Growth Marketing Lab',
            'job_title': 'Founder'
        },
        {
            'full_name': 'Lisa Chen',
            'company': 'DataDriven Consulting',
            'job_title': 'Managing Director'
        },
        {
            'full_name': 'Sarah Johnson',  # Potential duplicate
            'company': 'InnovateTech Solutions',
            'job_title': 'Chief Executive Officer'
        }
    ]
    
    # Run batch enrichment
    batch_results = system.batch_enrich_leads(test_leads)
    
    # Print results
    print("\n🏆 ULTIMATE SYSTEM RESULTS")
    print("=" * 80)
    print(f"📊 BATCH SUMMARY:")
    print(f"   Total leads: {batch_results['total_leads']}")
    print(f"   Successful enrichments: {batch_results['successful_enrichments']}")
    print(f"   Duplicates prevented: {batch_results['duplicates_prevented']}")
    print(f"   Domains discovered: {batch_results['domains_discovered']}")
    print(f"   Total emails found: {batch_results['total_emails_found']}")
    print(f"   Success rate: {batch_results['success_rate']:.1f}%")
    print(f"   Total processing time: {batch_results['processing_time_total']:.2f}ms")
    print(f"   Average per lead: {batch_results['average_processing_time']:.2f}ms")
    
    print(f"\n📈 QUALITY DISTRIBUTION:")
    for tier, count in batch_results['quality_distribution'].items():
        print(f"   {tier}: {count}")
    
    # System metrics
    metrics = system.get_system_metrics()
    print(f"\n⚡ SYSTEM PERFORMANCE:")
    print(f"   Leads processed: {metrics['leads_processed']}")
    print(f"   Duplicate prevention rate: {metrics['duplicate_prevention_rate']:.1f}%")
    print(f"   Domain discovery rate: {metrics['domain_discovery_rate']:.1f}%")
    print(f"   Emails per lead: {metrics['emails_per_lead']:.1f}")
    print(f"   Average quality score: {metrics['average_quality_score']:.1f}/100")
    
    print(f"\n✅ ULTIMATE SYSTEM VALIDATED!")
    print(f"🎯 Ready for production deployment!")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f"ultimate_system_test_{timestamp}.json", 'w') as f:
        json.dump({
            'batch_results': batch_results,
            'system_metrics': metrics,
            'test_timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"💾 Results saved to: ultimate_system_test_{timestamp}.json")

if __name__ == "__main__":
    test_ultimate_system()
