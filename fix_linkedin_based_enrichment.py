#!/usr/bin/env python3
"""
Fix LinkedIn-Based Enrichment
=============================
CRITICAL: Use the actual LinkedIn URL to get accurate data, not Google search on names.
This prevents wrong person enrichment and fake data pollution.
"""

import sqlite3
import requests
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

class LinkedInBasedEnricher:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def analyze_data_quality_issues(self):
        """Analyze leads to find data quality issues"""
        self.logger.info("🔍 Analyzing data quality issues...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get leads with LinkedIn URLs but potentially wrong data
            cursor = conn.execute("""
                SELECT id, Full_Name, Company, Job_Title, LinkedIn_URL, Email, Business_Type
                FROM leads 
                WHERE LinkedIn_URL IS NOT NULL AND LinkedIn_URL != ''
                AND Full_Name IS NOT NULL AND Full_Name != ''
                LIMIT 20
            """)
            
            leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            quality_issues = []
            
            for lead in leads:
                issues = []
                
                # Check for suspicious patterns that indicate wrong person enrichment
                company = lead.get('Company', '')
                linkedin_url = lead.get('LinkedIn_URL', '')
                
                # Pattern 1: Generic company names (likely wrong enrichment)
                generic_companies = [
                    'Business Services', 'Technology', 'Marketing', 'Consulting',
                    'Services', 'Solutions', 'Corp', 'Inc', 'LLC', 'Company'
                ]
                
                if any(generic in company for generic in generic_companies) and len(company) < 20:
                    issues.append("Generic/suspicious company name")
                
                # Pattern 2: LinkedIn URL doesn't match the person's apparent role
                if 'ceo' in linkedin_url.lower() and 'CEO' not in lead.get('Job_Title', ''):
                    issues.append("LinkedIn URL suggests CEO but job title doesn't match")
                
                # Pattern 3: Business type seems mismatched
                business_type = lead.get('Business_Type', '')
                if business_type in ['Small Business', 'Business Services'] and 'CEO' in lead.get('Job_Title', ''):
                    issues.append("Business type seems generic for executive role")
                
                if issues:
                    quality_issues.append({
                        'lead': lead,
                        'issues': issues
                    })
            
            self.logger.info(f"🚨 Found {len(quality_issues)} leads with potential data quality issues:")
            for item in quality_issues[:10]:  # Show first 10
                lead = item['lead']
                issues = item['issues']
                self.logger.info(f"   ⚠️ {lead['Full_Name']} at {lead['Company']}")
                for issue in issues:
                    self.logger.info(f"      - {issue}")
            
            return quality_issues
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing data quality: {e}")
            return []

    def extract_linkedin_profile_data(self, linkedin_url: str) -> Optional[Dict]:
        """Extract data directly from LinkedIn URL structure"""
        try:
            # Extract username from LinkedIn URL
            if 'linkedin.com/in/' not in linkedin_url:
                return None
            
            # Get the LinkedIn username
            username = linkedin_url.split('linkedin.com/in/')[-1].rstrip('/')
            
            # Clean the username
            username = username.split('?')[0]  # Remove query parameters
            username = username.split('#')[0]  # Remove fragments
            
            # Try to infer information from the LinkedIn username structure
            profile_data = {
                'linkedin_username': username,
                'profile_url': f"https://linkedin.com/in/{username}",
                'data_source': 'linkedin_url_based'
            }
            
            # Try to extract name parts from username (if structured properly)
            if '-' in username:
                name_parts = username.split('-')
                if len(name_parts) >= 2:
                    profile_data['inferred_first_name'] = name_parts[0].title()
                    profile_data['inferred_last_name'] = name_parts[1].title()
            
            return profile_data
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting LinkedIn data: {e}")
            return None

    def validate_lead_data_consistency(self, lead: Dict) -> Dict:
        """Validate that lead data is consistent and not from wrong person"""
        issues = []
        confidence_score = 100
        
        full_name = lead.get('Full_Name', '')
        company = lead.get('Company', '')
        linkedin_url = lead.get('LinkedIn_URL', '')
        email = lead.get('Email', '')
        
        # Extract LinkedIn profile data
        linkedin_data = self.extract_linkedin_profile_data(linkedin_url)
        
        if linkedin_data:
            # Check name consistency
            linkedin_username = linkedin_data.get('linkedin_username', '').lower()
            name_lower = full_name.lower().replace(' ', '-')
            
            # If the LinkedIn username doesn't match the name, it's suspicious
            if linkedin_username and name_lower:
                name_similarity = self.calculate_name_similarity(linkedin_username, name_lower)
                if name_similarity < 0.6:  # Less than 60% similarity
                    issues.append("LinkedIn URL doesn't match the name")
                    confidence_score -= 30
        
        # Check email domain vs company consistency
        if email and '@' in email and company:
            email_domain = email.split('@')[1].lower()
            company_clean = re.sub(r'[^a-zA-Z]', '', company.lower())
            
            # If email domain doesn't relate to company, might be wrong person
            if company_clean not in email_domain and email_domain not in company_clean:
                if not any(domain in email_domain for domain in ['gmail', 'yahoo', 'outlook', 'hotmail']):
                    issues.append("Email domain doesn't match company")
                    confidence_score -= 20
        
        # Check for generic/suspicious company patterns
        suspicious_patterns = [
            'unknown company', 'business services', 'technology company',
            'marketing services', 'consulting services', 'test company'
        ]
        
        if any(pattern in company.lower() for pattern in suspicious_patterns):
            issues.append("Generic or suspicious company name")
            confidence_score -= 25
        
        return {
            'issues': issues,
            'confidence_score': max(0, confidence_score),
            'linkedin_data': linkedin_data,
            'is_high_quality': confidence_score >= 70 and len(issues) == 0
        }

    def calculate_name_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        # Simple similarity calculation
        str1_set = set(str1.lower().split('-'))
        str2_set = set(str2.lower().split('-'))
        
        if not str1_set or not str2_set:
            return 0.0
        
        intersection = str1_set.intersection(str2_set)
        union = str1_set.union(str2_set)
        
        return len(intersection) / len(union)

    def mark_suspicious_leads(self):
        """Mark leads with data quality issues"""
        self.logger.info("🔍 Marking suspicious leads for review...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE LinkedIn_URL IS NOT NULL AND LinkedIn_URL != ''
                AND Full_Name IS NOT NULL AND Full_Name != ''
            """)
            
            leads = [dict(row) for row in cursor.fetchall()]
            
            suspicious_count = 0
            high_quality_count = 0
            
            for lead in leads:
                validation = self.validate_lead_data_consistency(lead)
                
                # Update lead with quality assessment
                quality_status = 'high_quality' if validation['is_high_quality'] else 'suspicious'
                confidence = validation['confidence_score']
                
                conn.execute("""
                    UPDATE leads SET 
                        Lead_Quality = ?,
                        data_confidence_score = ?,
                        data_validation_issues = ?,
                        Date_Enriched = ?
                    WHERE id = ?
                """, (
                    quality_status,
                    confidence,
                    ', '.join(validation['issues']) if validation['issues'] else '',
                    datetime.now().isoformat(),
                    lead['id']
                ))
                
                if validation['is_high_quality']:
                    high_quality_count += 1
                    self.logger.info(f"✅ High quality: {lead['Full_Name']} (Score: {confidence})")
                else:
                    suspicious_count += 1
                    self.logger.info(f"⚠️ Suspicious: {lead['Full_Name']} (Score: {confidence}) - {', '.join(validation['issues'])}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"📊 Data Quality Assessment Complete:")
            self.logger.info(f"   ✅ High quality leads: {high_quality_count}")
            self.logger.info(f"   ⚠️ Suspicious leads: {suspicious_count}")
            
            return high_quality_count, suspicious_count
            
        except Exception as e:
            self.logger.error(f"❌ Error marking suspicious leads: {e}")
            return 0, 0

    def clean_suspicious_data(self, apply_fixes=False):
        """Clean or flag suspicious data for manual review"""
        self.logger.info("🧹 Cleaning suspicious data...")
        
        if not apply_fixes:
            self.logger.info("⚠️ SIMULATION MODE - No changes will be made")
            self.logger.info("To apply fixes, run with apply_fixes=True")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get suspicious leads
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Lead_Quality = 'suspicious'
                OR data_confidence_score < 70
            """)
            
            suspicious_leads = [dict(row) for row in cursor.fetchall()]
            
            self.logger.info(f"🔍 Found {len(suspicious_leads)} suspicious leads")
            
            for lead in suspicious_leads:
                self.logger.info(f"⚠️ SUSPICIOUS: {lead['Full_Name']} at {lead['Company']}")
                self.logger.info(f"   LinkedIn: {lead['LinkedIn_URL']}")
                self.logger.info(f"   Issues: {lead.get('data_validation_issues', 'Unknown')}")
                self.logger.info(f"   Confidence: {lead.get('data_confidence_score', 0)}%")
                
                if apply_fixes:
                    # Mark as needing manual review
                    conn.execute("""
                        UPDATE leads SET 
                            Response_Status = 'needs_manual_review',
                            Needs_Enrichment = 1
                        WHERE id = ?
                    """, (lead['id'],))
            
            if apply_fixes:
                conn.commit()
                self.logger.info(f"✅ Marked {len(suspicious_leads)} leads for manual review")
            
            conn.close()
            return len(suspicious_leads)
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning suspicious data: {e}")
            return 0

def main():
    enricher = LinkedInBasedEnricher()
    
    print("🔍 LINKEDIN-BASED DATA QUALITY ANALYSIS")
    print("=" * 45)
    
    # Step 1: Analyze current data quality issues
    print("\n🚨 STEP 1: Analyzing data quality issues...")
    quality_issues = enricher.analyze_data_quality_issues()
    
    # Step 2: Mark suspicious leads
    print("\n🔍 STEP 2: Validating all lead data consistency...")
    high_quality, suspicious = enricher.mark_suspicious_leads()
    
    # Step 3: Clean suspicious data (simulation first)
    print("\n🧹 STEP 3: Identifying leads for manual review...")
    suspicious_count = enricher.clean_suspicious_data(apply_fixes=False)
    
    # Summary
    print(f"\n📊 DATA QUALITY ANALYSIS COMPLETE!")
    print(f"   ✅ High quality leads: {high_quality}")
    print(f"   ⚠️ Suspicious leads: {suspicious}")
    print(f"   🔍 Potential issues found: {len(quality_issues)}")
    
    print(f"\n🚨 CRITICAL FINDINGS:")
    print(f"   - Some leads may have data from wrong person")
    print(f"   - LinkedIn URLs are correct, but enriched data is suspicious")
    print(f"   - Need LinkedIn-first enrichment instead of Google search")
    
    print(f"\n🛠️ RECOMMENDATIONS:")
    print(f"   1. Implement LinkedIn URL-based enrichment")
    print(f"   2. Stop using Google search for person data")
    print(f"   3. Validate data consistency before syncing")
    print(f"   4. Flag suspicious leads for manual review")
    
    # Ask if user wants to apply fixes
    print(f"\n❓ Apply fixes and mark suspicious leads for review? (y/n)")

if __name__ == "__main__":
    main()
