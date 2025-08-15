#!/usr/bin/env python3
"""
Production Lead Scraper - The Heart of 4Runr Lead System
Finds SMB owners, startup founders, and growing companies (10-500 employees)
"""

import requests
import os
import json
import time
import random
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import re
from urllib.parse import urlparse

class ProductionLeadScraper:
    """Production-ready lead scraper for 4Runr system"""
    
    def __init__(self):
        """Initialize production scraper with proper configuration"""
        
        # Load API configuration
        self.api_key = self._load_serpapi_key()
        self.db_path = "data/unified_leads.db"
        
        # Target parameters
        self.target_company_sizes = ["10-50", "51-200", "201-500"]
        self.excluded_keywords = [
            'walmart', 'amazon', 'google', 'microsoft', 'apple', 'meta', 'facebook',
            'shopify', 'bombardier', 'cgi', 'teck', 'bell', 'rogers', 'telus',
            'rbc', 'td bank', 'bmo', 'scotiabank', 'desjardins', 'manulife',
            'power corporation', 'brookfield', 'magna', 'loblaws', 'canadian tire'
        ]
        
        print("🚀 Production Lead Scraper initialized")
        print(f"   Target: SMB owners, startup founders (10-500 employees)")
        print(f"   Excludes: {len(self.excluded_keywords)} large corporations")
    
    def _load_serpapi_key(self):
        """Load SerpAPI key from configuration"""
        env_path = "4runr-lead-scraper/.env"
        
        if not os.path.exists(env_path):
            raise ValueError("SerpAPI configuration not found")
        
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('SERPAPI_API_KEY='):
                    return line.split('=', 1)[1].strip()
        
        raise ValueError("SERPAPI_API_KEY not found in configuration")
    
    def scrape_ideal_prospects(self, max_leads=10):
        """Scrape ideal prospects for 4Runr - SMB owners and startup founders"""
        
        print(f"\n🎯 SCRAPING {max_leads} IDEAL PROSPECTS FOR 4RUNR")
        print("=" * 60)
        
        # Proven search strategies that find the right prospects
        search_strategies = [
            {
                'name': 'Tech Startup Founders',
                'query': 'site:linkedin.com/in/ "startup founder" OR "co-founder" tech saas software -amazon -google -microsoft',
                'target_type': 'tech_startup'
            },
            {
                'name': 'Small Business Owners',
                'query': 'site:linkedin.com/in/ "business owner" OR "company owner" small business -corporation -enterprise',
                'target_type': 'small_business'
            },
            {
                'name': 'Agency Owners',
                'query': 'site:linkedin.com/in/ "agency owner" OR "agency founder" marketing digital creative',
                'target_type': 'agency'
            },
            {
                'name': 'Consultants & Advisors',
                'query': 'site:linkedin.com/in/ "independent consultant" OR "consulting firm founder" -mckinsey -deloitte',
                'target_type': 'consulting'
            },
            {
                'name': 'E-commerce Entrepreneurs',
                'query': 'site:linkedin.com/in/ "e-commerce founder" OR "online business owner" -amazon -shopify',
                'target_type': 'ecommerce'
            }
        ]
        
        all_prospects = []
        leads_per_strategy = max(1, max_leads // len(search_strategies))
        
        for strategy in search_strategies:
            if len(all_prospects) >= max_leads:
                break
            
            print(f"\n🔍 Strategy: {strategy['name']}")
            prospects = self._execute_search_strategy(strategy, leads_per_strategy)
            
            # Quality filter each prospect
            qualified = self._quality_filter_prospects(prospects, strategy['target_type'])
            
            all_prospects.extend(qualified)
            print(f"   ✅ Found {len(qualified)} qualified prospects")
            
            # Rate limiting
            time.sleep(2)
        
        # Remove duplicates and limit results
        unique_prospects = self._remove_duplicates(all_prospects)[:max_leads]
        
        # Final validation
        validated_prospects = self._final_validation(unique_prospects)
        
        print(f"\n📊 SCRAPING RESULTS:")
        print(f"   Raw prospects found: {len(all_prospects)}")
        print(f"   After deduplication: {len(unique_prospects)}")
        print(f"   Final validated: {len(validated_prospects)}")
        
        return validated_prospects
    
    def _execute_search_strategy(self, strategy, max_results):
        """Execute a specific search strategy"""
        
        try:
            params = {
                'api_key': self.api_key,
                'engine': 'google',
                'q': strategy['query'],
                'num': str(min(max_results * 3, 20)),  # Get extra for filtering
                'hl': 'en'
            }
            
            response = requests.get('https://serpapi.com/search', params=params, timeout=20)
            
            if response.status_code != 200:
                print(f"   ❌ Search failed: {response.status_code}")
                return []
            
            results = response.json()
            organic_results = results.get('organic_results', [])
            
            prospects = []
            for result in organic_results:
                prospect = self._extract_prospect_data(result, strategy['target_type'])
                if prospect:
                    prospects.append(prospect)
            
            return prospects
            
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            return []
    
    def _extract_prospect_data(self, result, target_type):
        """Extract clean prospect data from search result"""
        
        try:
            title = result.get('title', '')
            link = result.get('link', '')
            snippet = result.get('snippet', '')
            
            # Must be LinkedIn profile
            if 'linkedin.com/in/' not in link:
                return None
            
            # Extract name and job title from LinkedIn title format
            name, job_info = self._parse_linkedin_title(title)
            if not name:
                return None
            
            # Extract company information
            company_info = self._extract_company_info(snippet, job_info)
            
            # Generate contact information
            contact_info = self._generate_contact_info(name, company_info)
            
            # Build prospect object
            prospect = {
                'name': name,
                'job_title': job_info.get('title', 'Founder'),
                'company': company_info.get('name', f"{name} Ventures"),
                'linkedin_url': link,
                'email': contact_info['email'],
                'industry': self._map_industry(target_type),
                'business_type': self._map_business_type(target_type),
                'target_type': target_type,
                'snippet': snippet,
                'company_size_estimate': self._estimate_company_size(snippet, company_info),
                'scraped_at': datetime.now().isoformat(),
                'prospect_score': self._calculate_prospect_score(job_info, company_info, snippet)
            }
            
            return prospect
            
        except Exception as e:
            print(f"   ⚠️ Extraction error: {e}")
            return None
    
    def _parse_linkedin_title(self, title):
        """Parse LinkedIn title to extract name and job info"""
        
        # Clean title
        title = title.replace(' | LinkedIn', '').replace(' - LinkedIn', '').strip()
        
        # LinkedIn format: "Name - Job Title at Company" or "Name - Job Title"
        if ' - ' in title:
            name_part = title.split(' - ')[0].strip()
            job_part = ' - '.join(title.split(' - ')[1:]).strip()
        else:
            name_part = title.strip()
            job_part = ""
        
        # Validate name
        if not name_part or len(name_part.split()) < 1:
            return None, {}
        
        # Parse job information
        job_info = {}
        if job_part:
            if ' at ' in job_part:
                job_info['title'] = job_part.split(' at ')[0].strip()
                job_info['company'] = job_part.split(' at ')[1].strip()
            else:
                job_info['title'] = job_part
        
        return name_part, job_info
    
    def _extract_company_info(self, snippet, job_info):
        """Extract company information from snippet"""
        
        company_info = {
            'name': job_info.get('company'),
            'indicators': []
        }
        
        # Look for company indicators in snippet
        startup_indicators = ['startup', 'founder', 'co-founder', 'entrepreneur']
        small_biz_indicators = ['small business', 'owner', 'independent', 'boutique']
        growth_indicators = ['growing', 'scaling', 'expanding', 'rapid growth']
        
        snippet_lower = snippet.lower()
        
        if any(indicator in snippet_lower for indicator in startup_indicators):
            company_info['indicators'].append('startup')
        
        if any(indicator in snippet_lower for indicator in small_biz_indicators):
            company_info['indicators'].append('small_business')
        
        if any(indicator in snippet_lower for indicator in growth_indicators):
            company_info['indicators'].append('growth_stage')
        
        # Extract company from snippet if not in job_info
        if not company_info['name']:
            company_info['name'] = self._extract_company_from_snippet(snippet)
        
        return company_info
    
    def _extract_company_from_snippet(self, snippet):
        """Extract company name from snippet text"""
        
        # Look for "Experience: Company" pattern
        if 'Experience:' in snippet:
            exp_part = snippet.split('Experience:')[1].split('·')[0].strip()
            if exp_part and len(exp_part) < 50:  # Reasonable company name length
                return exp_part
        
        # Look for "at Company" pattern
        if ' at ' in snippet:
            parts = snippet.split(' at ')
            for part in parts[1:]:
                potential_company = part.split('·')[0].split('.')[0].strip()
                if potential_company and len(potential_company) < 50:
                    return potential_company
        
        return None
    
    def _generate_contact_info(self, name, company_info):
        """Generate contact information for prospect"""
        
        # Generate email pattern
        name_parts = name.lower().replace(',', '').replace('.', '').split()
        first = name_parts[0] if name_parts else 'contact'
        last = name_parts[-1] if len(name_parts) > 1 else 'business'
        
        # Generate domain from company
        company_name = company_info.get('name', '')
        if company_name and company_name.lower() not in ['none', 'unknown', '']:
            domain_base = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())
            if len(domain_base) > 20:
                domain_base = domain_base[:20]
            domain = f"{domain_base}.com"
        else:
            domain = f"{first}{last}ventures.com"
        
        email = f"{first}.{last}@{domain}"
        
        return {
            'email': email,
            'first_name': first.title(),
            'last_name': last.title()
        }
    
    def _estimate_company_size(self, snippet, company_info):
        """Estimate company size from available information"""
        
        indicators = company_info.get('indicators', [])
        snippet_lower = snippet.lower()
        
        # Size indicators
        if 'startup' in indicators or 'startup' in snippet_lower:
            return '10-50'
        elif 'small business' in indicators or any(term in snippet_lower for term in ['small business', 'boutique', 'independent']):
            return '10-100'
        elif 'growth_stage' in indicators or any(term in snippet_lower for term in ['growing', 'scaling']):
            return '50-200'
        else:
            return '10-100'  # Default for SMB
    
    def _calculate_prospect_score(self, job_info, company_info, snippet):
        """Calculate prospect quality score (0-100)"""
        
        score = 0
        
        # Job title scoring
        title = (job_info.get('title') or '').lower()
        if any(term in title for term in ['founder', 'co-founder', 'owner']):
            score += 30
        elif any(term in title for term in ['ceo', 'president', 'managing director']):
            score += 25
        elif any(term in title for term in ['director', 'vp', 'head of']):
            score += 15
        
        # Company indicators scoring
        indicators = company_info.get('indicators', [])
        if 'startup' in indicators:
            score += 20
        if 'small_business' in indicators:
            score += 15
        if 'growth_stage' in indicators:
            score += 10
        
        # Snippet quality scoring
        snippet_lower = (snippet or '').lower()
        if any(term in snippet_lower for term in ['tech', 'software', 'saas', 'digital']):
            score += 10
        if any(term in snippet_lower for term in ['entrepreneur', 'innovation', 'growth']):
            score += 5
        
        return min(score, 100)
    
    def _quality_filter_prospects(self, prospects, target_type):
        """Apply quality filters to prospects"""
        
        qualified = []
        
        for prospect in prospects:
            # Basic validation
            if not prospect.get('name') or not prospect.get('linkedin_url'):
                continue
            
            # Exclude large corporations
            company = (prospect.get('company') or '').lower()
            if any(excluded in company for excluded in self.excluded_keywords):
                continue
            
            # Score threshold
            if prospect.get('prospect_score', 0) < 30:
                continue
            
            # Company size validation
            if not self._is_target_company_size(prospect):
                continue
            
            qualified.append(prospect)
        
        return qualified
    
    def _is_target_company_size(self, prospect):
        """Check if prospect is from target company size"""
        
        snippet = (prospect.get('snippet') or '').lower()
        company_size = prospect.get('company_size_estimate') or ''
        
        # Exclude enterprise indicators
        enterprise_indicators = [
            'fortune 500', 'multinational', 'global corporation', 'enterprise',
            'publicly traded', 'nasdaq', 'tsx', 'stock exchange'
        ]
        
        if any(indicator in snippet for indicator in enterprise_indicators):
            return False
        
        # Target size indicators
        target_indicators = [
            'startup', 'small business', 'growing company', 'boutique',
            'independent', 'emerging', 'scale-up'
        ]
        
        if any(indicator in snippet for indicator in target_indicators):
            return True
        
        # Default to include if unclear (better to over-include than miss)
        return True
    
    def _final_validation(self, prospects):
        """Final validation and scoring of prospects"""
        
        validated = []
        
        for prospect in prospects:
            # Add validation metadata
            prospect['validation_score'] = self._validate_prospect(prospect)
            prospect['ideal_fit_reason'] = self._determine_ideal_fit(prospect)
            
            # Only include high-quality prospects
            if prospect['validation_score'] >= 70:
                validated.append(prospect)
        
        # Sort by validation score
        validated.sort(key=lambda x: x['validation_score'], reverse=True)
        
        return validated
    
    def _validate_prospect(self, prospect):
        """Validate prospect and assign validation score"""
        
        score = prospect.get('prospect_score', 0)
        
        # Additional validation factors
        name_quality = len(prospect.get('name', '').split()) >= 2
        if name_quality:
            score += 10
        
        company_quality = prospect.get('company') and prospect.get('company') != 'Unknown'
        if company_quality:
            score += 10
        
        linkedin_quality = 'linkedin.com/in/' in prospect.get('linkedin_url', '')
        if linkedin_quality:
            score += 10
        
        return min(score, 100)
    
    def _determine_ideal_fit(self, prospect):
        """Determine why this prospect is ideal for 4Runr"""
        
        reasons = []
        
        title = (prospect.get('job_title') or '').lower()
        target_type = prospect.get('target_type') or ''
        indicators = prospect.get('company_size_estimate') or ''
        
        if 'founder' in title:
            reasons.append("Startup founder - growth-focused")
        elif 'owner' in title:
            reasons.append("Business owner - decision maker")
        elif 'ceo' in title:
            reasons.append("CEO of growing company")
        
        if target_type == 'tech_startup':
            reasons.append("Tech startup - ready for AI")
        elif target_type == 'agency':
            reasons.append("Agency owner - values efficiency")
        elif target_type == 'consulting':
            reasons.append("Consultant - needs automation")
        
        if '10-50' in indicators:
            reasons.append("Perfect size for 4Runr (10-50 employees)")
        
        return "; ".join(reasons[:2]) if reasons else "SMB leader - ideal for automation"
    
    def add_prospects_to_database(self, prospects):
        """Add scraped prospects to the database"""
        
        if not prospects:
            print("No prospects to add to database")
            return 0
        
        print(f"\n💾 ADDING {len(prospects)} PROSPECTS TO DATABASE")
        print("-" * 50)
        
        conn = sqlite3.connect(self.db_path)
        added_count = 0
        
        for prospect in prospects:
            # Check if prospect already exists
            cursor = conn.execute(
                "SELECT id FROM leads WHERE linkedin_url = ? OR email = ?",
                (prospect['linkedin_url'], prospect['email'])
            )
            
            if cursor.fetchone():
                print(f"⚠️  {prospect['name']} already exists")
                continue
            
            # Insert new prospect
            try:
                conn.execute("""
                    INSERT INTO leads (
                        full_name, email, company, linkedin_url, job_title,
                        industry, business_type, source, scraped_at, created_at,
                        enriched, ready_for_outreach, score, lead_quality
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
                """, (
                    prospect['name'], prospect['email'], prospect['company'],
                    prospect['linkedin_url'], prospect['job_title'], prospect['industry'],
                    prospect['business_type'], 'Search', prospect['scraped_at'],
                    datetime.now().isoformat(), prospect['validation_score'],
                    'Warm' if prospect['validation_score'] >= 80 else 'Cold'
                ))
                
                added_count += 1
                print(f"✅ {prospect['name']}")
                print(f"   {prospect['job_title']} at {prospect['company']}")
                print(f"   Score: {prospect['validation_score']}/100")
                print(f"   Why ideal: {prospect['ideal_fit_reason']}")
                print()
                
            except Exception as e:
                print(f"❌ Failed to add {prospect['name']}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"📊 DATABASE UPDATE COMPLETE:")
        print(f"   Added: {added_count} new prospects")
        print(f"   Total processed: {len(prospects)}")
        
        return added_count
    
    def _map_industry(self, target_type):
        """Map target type to industry"""
        mapping = {
            'tech_startup': 'Technology & Innovation',
            'small_business': 'Professional Services',
            'agency': 'Marketing & Creative',
            'consulting': 'Consulting & Advisory',
            'ecommerce': 'E-commerce & Digital'
        }
        return mapping.get(target_type, 'Growing Business')
    
    def _map_business_type(self, target_type):
        """Map target type to business type"""
        mapping = {
            'tech_startup': 'Technology Startup',
            'small_business': 'Service Provider',
            'agency': 'Marketing & Creative',
            'consulting': 'Consulting & Advisory',
            'ecommerce': 'E-commerce & Digital'
        }
        return mapping.get(target_type, 'Growing Company')
    
    def _remove_duplicates(self, prospects):
        """Remove duplicate prospects"""
        seen_urls = set()
        unique_prospects = []
        
        for prospect in prospects:
            url = prospect.get('linkedin_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_prospects.append(prospect)
        
        return unique_prospects

def run_production_scraper(max_leads=5):
    """Run the production scraper and add results to database"""
    
    print("🚀 RUNNING PRODUCTION LEAD SCRAPER")
    print("=" * 60)
    print("Target: SMB owners, startup founders, growing companies")
    print("Exclude: Large corporations, Fortune 500, enterprises")
    print()
    
    try:
        # Initialize scraper
        scraper = ProductionLeadScraper()
        
        # Scrape prospects
        prospects = scraper.scrape_ideal_prospects(max_leads)
        
        if not prospects:
            print("❌ No prospects found")
            return False
        
        # Add to database
        added_count = scraper.add_prospects_to_database(prospects)
        
        if added_count > 0:
            print(f"\n🎉 SUCCESS! Added {added_count} ideal prospects to system")
            
            # Run pipeline on new prospects
            print(f"\n🔄 Processing through pipeline...")
            run_pipeline_on_new_leads()
            
            # Sync to Airtable
            print(f"\n📤 Syncing to Airtable...")
            sync_to_airtable()
            
            print(f"\n✅ PRODUCTION SCRAPER COMPLETE!")
            print(f"🎯 {added_count} new prospects ready for outreach")
            
            return True
        else:
            print("⚠️ No new prospects added (all already exist)")
            return False
        
    except Exception as e:
        print(f"❌ Production scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_pipeline_on_new_leads():
    """Run enrichment pipeline on new leads"""
    try:
        from ml_data_enricher import MLDataEnricher
        enricher = MLDataEnricher()
        enricher.run_complete_enrichment()
        
        from complete_data_pipeline import CompleteDataPipeline
        pipeline = CompleteDataPipeline()
        pipeline.process_scraped_leads()
        
        print("✅ Pipeline processing complete")
    except Exception as e:
        print(f"⚠️ Pipeline error: {e}")

def sync_to_airtable():
    """Sync new leads to Airtable"""
    try:
        from safe_complete_sync import safe_complete_sync
        safe_complete_sync()
        print("✅ Airtable sync complete")
    except Exception as e:
        print(f"⚠️ Sync error: {e}")

if __name__ == "__main__":
    # Run production scraper with 5 prospects
    success = run_production_scraper(max_leads=5)
    
    if success:
        print(f"\n🎯 PRODUCTION SCRAPER IS WORKING!")
        print("The heart of your lead system is now functioning properly.")
    else:
        print(f"\n❌ Production scraper needs attention.")
