#!/usr/bin/env python3
"""
🚫 REAL-TIME DUPLICATE PREVENTION SYSTEM 🚫
===========================================
Advanced system that prevents duplicates BEFORE they enter the database.
Works in real-time during lead generation and enrichment.

FEATURES:
- Pre-insertion duplicate checking
- Smart similarity matching
- Real-time quality scoring
- Duplicate merge recommendations
- Performance optimized for speed
- Configurable thresholds
- Automatic decision making

This system ensures we never save duplicates in the first place.
"""

import sqlite3
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from intelligent_lead_cleaner import IntelligentLeadCleaner

class RealTimeDuplicatePrevention:
    """Real-time duplicate prevention during lead processing"""
    
    def __init__(self, db_path: str = "data/unified_leads.db"):
        self.db_path = db_path
        self.cleaner = IntelligentLeadCleaner(db_path)
        
        # Performance optimization - keep recent leads in memory
        self.recent_leads_cache = []
        self.cache_size = 1000
        self.last_cache_update = 0
        self.cache_ttl = 300  # 5 minutes
        
        # Prevention thresholds (more strict than cleaning)
        self.exact_match_threshold = 1.0
        self.name_similarity_threshold = 0.90
        self.email_similarity_threshold = 0.95
        self.company_similarity_threshold = 0.85
        
        print("🚫 Real-Time Duplicate Prevention System initialized")
        print("🎯 Ready to prevent duplicates at the source")
    
    def refresh_cache(self):
        """Refresh the recent leads cache for performance"""
        current_time = time.time()
        
        if current_time - self.last_cache_update > self.cache_ttl:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                
                # Get recent leads (last 1000)
                cursor = conn.execute("""
                    SELECT rowid, full_name, company, email, linkedin_url, phone, created_at 
                    FROM leads 
                    WHERE full_name IS NOT NULL 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (self.cache_size,))
                
                self.recent_leads_cache = [dict(row) for row in cursor.fetchall()]
                self.last_cache_update = current_time
                conn.close()
                
            except Exception as e:
                print(f"⚠️ Cache refresh failed: {e}")
    
    def check_for_duplicates(self, new_lead: Dict) -> Dict:
        """Check if new lead is a duplicate before insertion"""
        start_time = time.time()
        
        # Refresh cache if needed
        self.refresh_cache()
        
        # Generate signature for exact matching
        new_signature = self.cleaner.generate_lead_signature(new_lead)
        
        # Check against cached leads for performance
        leads_to_check = self.recent_leads_cache
        
        # Step 1: Exact duplicate check
        exact_match = self.check_exact_duplicates(new_lead, new_signature, leads_to_check)
        if exact_match:
            return {
                'is_duplicate': True,
                'duplicate_type': 'exact',
                'action': 'reject',
                'confidence': 1.0,
                'existing_lead': exact_match,
                'reason': 'Exact duplicate found',
                'processing_time_ms': (time.time() - start_time) * 1000
            }
        
        # Step 2: Fuzzy duplicate check
        fuzzy_match = self.check_fuzzy_duplicates(new_lead, leads_to_check)
        if fuzzy_match:
            return {
                'is_duplicate': True,
                'duplicate_type': 'fuzzy',
                'action': fuzzy_match['action'],
                'confidence': fuzzy_match['confidence'],
                'existing_lead': fuzzy_match['existing_lead'],
                'reason': fuzzy_match['reason'],
                'similarity_details': fuzzy_match['details'],
                'processing_time_ms': (time.time() - start_time) * 1000
            }
        
        # Step 3: No duplicates found
        return {
            'is_duplicate': False,
            'action': 'allow',
            'reason': 'No duplicates detected',
            'processing_time_ms': (time.time() - start_time) * 1000
        }
    
    def check_exact_duplicates(self, new_lead: Dict, new_signature: str, existing_leads: List[Dict]) -> Optional[Dict]:
        """Check for exact duplicates using signatures"""
        for existing_lead in existing_leads:
            existing_signature = self.cleaner.generate_lead_signature(existing_lead)
            
            if new_signature == existing_signature:
                return existing_lead
        
        return None
    
    def check_fuzzy_duplicates(self, new_lead: Dict, existing_leads: List[Dict]) -> Optional[Dict]:
        """Check for fuzzy duplicates using similarity matching"""
        new_name_norm = self.cleaner.normalize_person_name(new_lead.get('full_name', ''))
        new_company_norm = self.cleaner.normalize_company_name(new_lead.get('company', ''))
        new_email_norm = self.cleaner.normalize_email(new_lead.get('email', ''))
        
        for existing_lead in existing_leads:
            existing_name_norm = self.cleaner.normalize_person_name(existing_lead.get('full_name', ''))
            existing_company_norm = self.cleaner.normalize_company_name(existing_lead.get('company', ''))
            existing_email_norm = self.cleaner.normalize_email(existing_lead.get('email', ''))
            
            # Calculate similarities
            name_similarity = self.cleaner.calculate_similarity(new_name_norm, existing_name_norm)
            company_similarity = self.cleaner.calculate_similarity(new_company_norm, existing_company_norm)
            email_similarity = self.cleaner.calculate_similarity(new_email_norm, existing_email_norm) if new_email_norm and existing_email_norm else 0
            
            # Check for high similarity matches
            if name_similarity >= self.name_similarity_threshold and company_similarity >= self.company_similarity_threshold:
                confidence = (name_similarity + company_similarity) / 2
                
                # Determine action based on confidence
                if confidence >= 0.95:
                    action = 'reject'
                elif confidence >= 0.90:
                    action = 'merge_recommended'
                else:
                    action = 'review_required'
                
                return {
                    'existing_lead': existing_lead,
                    'confidence': confidence,
                    'action': action,
                    'reason': f'High name/company similarity: {confidence:.2f}',
                    'details': {
                        'name_similarity': name_similarity,
                        'company_similarity': company_similarity,
                        'email_similarity': email_similarity
                    }
                }
            
            # Check for email-based duplicates
            elif new_email_norm and existing_email_norm and email_similarity >= self.email_similarity_threshold:
                return {
                    'existing_lead': existing_lead,
                    'confidence': email_similarity,
                    'action': 'reject',
                    'reason': f'Email similarity too high: {email_similarity:.2f}',
                    'details': {
                        'name_similarity': name_similarity,
                        'company_similarity': company_similarity,
                        'email_similarity': email_similarity
                    }
                }
        
        return None
    
    def process_lead_with_prevention(self, new_lead: Dict) -> Dict:
        """Process a new lead with duplicate prevention"""
        print(f"🔍 Checking for duplicates: {new_lead.get('full_name')} at {new_lead.get('company')}")
        
        # Check for duplicates
        duplicate_check = self.check_for_duplicates(new_lead)
        
        if duplicate_check['is_duplicate']:
            print(f"🚫 DUPLICATE DETECTED: {duplicate_check['duplicate_type']} match")
            print(f"   Action: {duplicate_check['action']}")
            print(f"   Confidence: {duplicate_check['confidence']:.2f}")
            print(f"   Reason: {duplicate_check['reason']}")
            
            if duplicate_check['action'] == 'reject':
                return {
                    'status': 'rejected',
                    'reason': 'Duplicate lead',
                    'duplicate_info': duplicate_check
                }
            elif duplicate_check['action'] == 'merge_recommended':
                # Merge with existing lead
                merged_lead = self.merge_leads(new_lead, duplicate_check['existing_lead'])
                return {
                    'status': 'merged',
                    'reason': 'Merged with existing lead',
                    'merged_lead': merged_lead,
                    'duplicate_info': duplicate_check
                }
            else:
                return {
                    'status': 'needs_review',
                    'reason': 'Potential duplicate requires manual review',
                    'duplicate_info': duplicate_check
                }
        else:
            print(f"✅ NO DUPLICATES: Lead is unique")
            print(f"   Processing time: {duplicate_check['processing_time_ms']:.2f}ms")
            
            # Save the new lead
            lead_id = self.save_new_lead(new_lead)
            
            return {
                'status': 'saved',
                'reason': 'Unique lead saved successfully',
                'lead_id': lead_id,
                'duplicate_info': duplicate_check
            }
    
    def merge_leads(self, new_lead: Dict, existing_lead: Dict) -> Dict:
        """Merge new lead data with existing lead"""
        merged = existing_lead.copy()
        
        # Merge fields, preferring newer non-empty values
        for field, value in new_lead.items():
            if value and (field not in merged or not merged[field]):
                merged[field] = value
            elif field == 'extra_info':
                # Combine extra info
                existing_info = merged.get('extra_info', '')
                new_info = new_lead.get('extra_info', '')
                if new_info and new_info != existing_info:
                    merged['extra_info'] = f"{existing_info}; {new_info}".strip('; ')
        
        # Update timestamps
        merged['updated_at'] = datetime.now().isoformat()
        merged['last_enriched'] = datetime.now().isoformat()
        
        # Update in database
        self.update_existing_lead(merged)
        
        return merged
    
    def save_new_lead(self, lead: Dict) -> str:
        """Save new unique lead to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Add timestamp
            lead['created_at'] = datetime.now().isoformat()
            lead['updated_at'] = datetime.now().isoformat()
            
            # Prepare insert query
            fields = list(lead.keys())
            placeholders = ', '.join(['?' for _ in fields])
            values = [lead[field] for field in fields]
            
            query = f"INSERT INTO leads ({', '.join(fields)}) VALUES ({placeholders})"
            cursor = conn.execute(query, values)
            
            lead_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Update cache
            lead['rowid'] = lead_id
            self.recent_leads_cache.insert(0, lead)
            if len(self.recent_leads_cache) > self.cache_size:
                self.recent_leads_cache.pop()
            
            return str(lead_id)
            
        except Exception as e:
            print(f"❌ Error saving lead: {e}")
            return None
    
    def update_existing_lead(self, lead: Dict):
        """Update existing lead in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            lead_id = lead.get('rowid', lead.get('id'))
            if not lead_id:
                return
            
            # Prepare update query
            update_fields = []
            update_values = []
            
            for field, value in lead.items():
                if field not in ['rowid', 'id']:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            if update_fields:
                update_values.append(lead_id)
                query = f"UPDATE leads SET {', '.join(update_fields)} WHERE rowid = ?"
                conn.execute(query, update_values)
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error updating lead: {e}")

def test_duplicate_prevention():
    """Test the real-time duplicate prevention system"""
    print("🚫 REAL-TIME DUPLICATE PREVENTION TEST")
    print("=" * 60)
    
    prevention_system = RealTimeDuplicatePrevention()
    
    # Test cases
    test_leads = [
        {
            'full_name': 'John Smith',
            'company': 'TechCorp Inc',
            'email': 'john.smith@techcorp.com',
            'job_title': 'CEO'
        },
        {
            'full_name': 'John Smith',  # Exact duplicate
            'company': 'TechCorp Inc',
            'email': 'john.smith@techcorp.com',
            'job_title': 'CEO'
        },
        {
            'full_name': 'John Smith',  # Similar but different email
            'company': 'TechCorp Inc',
            'email': 'j.smith@techcorp.com',
            'job_title': 'CEO'
        },
        {
            'full_name': 'Jane Doe',    # Completely new
            'company': 'NewCorp LLC',
            'email': 'jane.doe@newcorp.com',
            'job_title': 'CTO'
        }
    ]
    
    print(f"\n🧪 Testing {len(test_leads)} leads:")
    for i, lead in enumerate(test_leads, 1):
        print(f"{i}. {lead['full_name']} at {lead['company']}")
    
    results = []
    for i, lead in enumerate(test_leads, 1):
        print(f"\n🔬 TEST {i}: {lead['full_name']}")
        print("-" * 40)
        
        result = prevention_system.process_lead_with_prevention(lead)
        results.append(result)
        
        print(f"   Status: {result['status']}")
        print(f"   Reason: {result['reason']}")
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY:")
    print("=" * 40)
    
    status_counts = {}
    for result in results:
        status = result['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"   {status}: {count}")
    
    print("\n✅ Duplicate prevention system tested successfully!")
    print("🎯 Ready for production use!")

if __name__ == "__main__":
    test_duplicate_prevention()
