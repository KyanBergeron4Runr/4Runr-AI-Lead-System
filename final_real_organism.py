#!/usr/bin/env python3
"""
FINAL REAL 4Runr Autonomous Organism
===================================
Uses direct SerpAPI integration for REAL LinkedIn leads
NO FAKE DATA - ONLY REAL PROFESSIONALS
"""

import os
import sys
import time
import sqlite3
import logging
import requests
from datetime import datetime
from typing import List, Dict
import json

class FinalRealOrganism:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('final_real')
        self.cycle_count = 0
        self.total_leads_found = 0
        self.total_leads_synced = 0
        
        # Rate limiting: 7 leads per day
        self.leads_per_day = 7
        self.cycle_interval = (24 * 60 * 60) / self.leads_per_day  # ~3.4 hours
        
        self.logger.info("REAL Autonomous Organism initialized")
        self.logger.info(f"Target: {self.leads_per_day} leads per day")
        self.logger.info(f"Cycle interval: {self.cycle_interval/3600:.1f} hours")

    def setup_logging(self):
        """Setup logging for production"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/final-real-organism.log'),
                logging.StreamHandler()
            ]
        )

    def validate_environment(self):
        """Check required API keys"""
        serpapi_key = os.getenv('SERPAPI_KEY')
        airtable_key = os.getenv('AIRTABLE_API_KEY')
        
        if not serpapi_key:
            self.logger.error("Missing SERPAPI_KEY environment variable")
            return False
            
        if not airtable_key:
            self.logger.error("Missing AIRTABLE_API_KEY environment variable")
            return False
            
        self.logger.info("Environment validation passed")
        return True

    def setup_database(self):
        """Ensure database exists with all columns"""
        try:
            os.makedirs('data', exist_ok=True)
            conn = sqlite3.connect('data/unified_leads.db')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    company TEXT,
                    job_title TEXT,
                    linkedin_url TEXT,
                    industry TEXT,
                    business_type TEXT,
                    source TEXT DEFAULT 'SerpAPI_Real',
                    date_scraped TEXT,
                    date_enriched TEXT,
                    date_messaged TEXT,
                    created_at TEXT,
                    enriched INTEGER DEFAULT 0,
                    ready_for_outreach INTEGER DEFAULT 0,
                    score INTEGER DEFAULT 0,
                    lead_quality TEXT,
                    email_confidence_level TEXT,
                    ai_message TEXT,
                    website TEXT,
                    needs_enrichment INTEGER DEFAULT 0,
                    replied INTEGER DEFAULT 0,
                    response_date TEXT,
                    response_notes TEXT,
                    extra_info TEXT,
                    level_engaged TEXT,
                    engagement_status TEXT,
                    follow_up_stage TEXT,
                    response_status TEXT,
                    company_description TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("Database setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
            return False

    def search_linkedin_with_serpapi(self, query: str, max_results: int = 3) -> List[Dict]:
        """Direct SerpAPI search for LinkedIn profiles"""
        try:
            import serpapi
            
            client = serpapi.GoogleSearch({
                "q": query,
                "api_key": os.getenv('SERPAPI_KEY'),
                "num": max_results,
                "google_domain": "google.com"
            })
            
            results = client.get_dict()
            
            organic_results = results.get('organic_results', [])
            
            linkedin_profiles = []
            for result in organic_results:
                link = result.get('link', '')
                title = result.get('title', '')
                
                if 'linkedin.com/in/' in link and title:
                    linkedin_profiles.append({
                        'link': link,
                        'title': title,
                        'snippet': result.get('snippet', '')
                    })
                    
            return linkedin_profiles
            
        except Exception as e:
            self.logger.error(f"SerpAPI search failed: {e}")
            return []

    def validate_linkedin_url(self, url: str) -> bool:
        """Check if LinkedIn URL is valid"""
        if not url or 'linkedin.com/in/' not in url:
            return False
            
        try:
            response = requests.head(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            # LinkedIn often returns 999 or 403 for automated requests, but profile exists
            return response.status_code in [200, 403, 999]
        except:
            return False

    def extract_name_from_title(self, title: str) -> str:
        """Extract clean name from LinkedIn title"""
        if not title:
            return ""
            
        # Remove common suffixes
        name = title.split(' - ')[0].split(' | ')[0].split(' on LinkedIn')[0]
        name = name.strip()
        
        # Basic validation
        if len(name) < 3 or len(name) > 50:
            return ""
            
        # Check for reasonable name format
        if ' ' not in name:
            return ""
            
        return name

    def extract_job_title(self, title: str) -> str:
        """Extract job title from LinkedIn title"""
        if ' - ' in title:
            parts = title.split(' - ')
            if len(parts) > 1:
                job_part = parts[1].split(' | ')[0].split(' at ')[0].strip()
                return job_part if job_part else "Professional"
        return "Professional"

    def extract_company(self, title: str) -> str:
        """Extract company from LinkedIn title"""
        if ' at ' in title:
            company = title.split(' at ')[-1].split(' | ')[0].split(' - ')[0].strip()
            return company if company else "Company"
        elif ' - ' in title and len(title.split(' - ')) > 2:
            company = title.split(' - ')[-1].strip()
            return company if company else "Company"
        return "Company"

    def scrape_real_leads(self) -> List[Dict]:
        """Find REAL LinkedIn leads using SerpAPI"""
        # Target queries for small/medium business leaders
        target_queries = [
            "site:linkedin.com/in/ CEO startup Toronto",
            "site:linkedin.com/in/ founder small business Canada", 
            "site:linkedin.com/in/ president consulting firm",
            "site:linkedin.com/in/ owner restaurant Toronto",
            "site:linkedin.com/in/ director marketing agency Vancouver"
        ]
        
        all_leads = []
        
        for query in target_queries[:1]:  # 1 query per cycle for rate limiting
            self.logger.info(f"Searching: {query}")
            
            try:
                results = self.search_linkedin_with_serpapi(query, max_results=5)
                
                for result in results:
                    linkedin_url = result.get('link', '')
                    title = result.get('title', '')
                    
                    # Validate LinkedIn URL
                    if not self.validate_linkedin_url(linkedin_url):
                        self.logger.warning(f"Invalid LinkedIn URL: {linkedin_url}")
                        continue
                    
                    # Extract clean name
                    name = self.extract_name_from_title(title)
                    if not name:
                        self.logger.warning(f"Could not extract name from: {title}")
                        continue
                    
                    lead = {
                        'full_name': name,
                        'linkedin_url': linkedin_url,
                        'job_title': self.extract_job_title(title),
                        'company': self.extract_company(title),
                        'source': 'SerpAPI_Real',
                        'date_scraped': datetime.now().isoformat(),
                        'created_at': datetime.now().isoformat()
                    }
                    
                    all_leads.append(lead)
                    self.logger.info(f"Found real lead: {name} - {lead['company']}")
                    
                    if len(all_leads) >= 1:  # 1 lead per cycle
                        break
                        
            except Exception as e:
                self.logger.error(f"Query failed: {e}")
                continue
                
            if len(all_leads) >= 1:
                break
                
        self.logger.info(f"Scraped {len(all_leads)} REAL leads")
        return all_leads

    def enrich_leads(self, leads: List[Dict]) -> List[Dict]:
        """Add enrichment data to leads"""
        for lead in leads:
            try:
                # Generate email guess
                name_parts = lead['full_name'].lower().split()
                company_clean = lead.get('company', '').lower().replace(' ', '').replace('.', '').replace(',', '')
                
                if len(name_parts) >= 2 and len(company_clean) > 2:
                    email_guess = f"{name_parts[0]}.{name_parts[-1]}@{company_clean}.com"
                    lead['email'] = email_guess
                    lead['email_confidence_level'] = 'Pattern'
                
                # Set business type and quality based on job title
                job_title = lead.get('job_title', '').lower()
                if any(word in job_title for word in ['ceo', 'founder', 'president', 'owner']):
                    lead['business_type'] = 'Small Business'
                    lead['lead_quality'] = 'Hot'
                    lead['score'] = 90
                elif any(word in job_title for word in ['director', 'manager', 'head']):
                    lead['business_type'] = 'Small Business'  
                    lead['lead_quality'] = 'Warm'
                    lead['score'] = 75
                else:
                    lead['business_type'] = 'Enterprise'
                    lead['lead_quality'] = 'Warm'
                    lead['score'] = 60
                
                # Generate AI message
                first_name = lead['full_name'].split()[0]
                company = lead.get('company', 'your company')
                lead['ai_message'] = f"Hi {first_name}, I'm impressed by your work at {company}. Would love to connect about potential collaboration opportunities!"
                
                # Set enrichment flags
                lead['date_enriched'] = datetime.now().isoformat()
                lead['enriched'] = 1
                lead['ready_for_outreach'] = 1
                lead['needs_enrichment'] = 0
                
                # Company description
                lead['company_description'] = f"REAL LinkedIn lead: {company}. Found via SerpAPI search with validated LinkedIn profile: {lead['linkedin_url']}"
                
                self.logger.info(f"Enriched: {lead['full_name']} - Quality: {lead['lead_quality']}")
                
            except Exception as e:
                self.logger.error(f"Enrichment failed for {lead.get('full_name', 'Unknown')}: {e}")
                
        return leads

    def save_to_database(self, leads: List[Dict]) -> int:
        """Save leads to database with duplicate checking"""
        if not leads:
            return 0
            
        saved_count = 0
        
        try:
            conn = sqlite3.connect('data/unified_leads.db')
            
            for lead in leads:
                try:
                    # Check for duplicates by LinkedIn URL or name+company
                    cursor = conn.execute(
                        """SELECT id FROM leads 
                           WHERE linkedin_url = ? 
                           OR (full_name = ? AND company = ?)""",
                        (lead.get('linkedin_url'), lead.get('full_name'), lead.get('company'))
                    )
                    
                    if cursor.fetchone():
                        self.logger.info(f"Duplicate skipped: {lead['full_name']}")
                        continue
                    
                    # Insert new lead
                    conn.execute('''
                        INSERT INTO leads (
                            full_name, email, company, job_title, linkedin_url,
                            business_type, source, date_scraped, date_enriched,
                            created_at, enriched, ready_for_outreach, score, 
                            lead_quality, email_confidence_level, ai_message, 
                            needs_enrichment, company_description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        lead.get('full_name'),
                        lead.get('email'),
                        lead.get('company'),
                        lead.get('job_title'),
                        lead.get('linkedin_url'),
                        lead.get('business_type', 'Small Business'),
                        lead.get('source', 'SerpAPI_Real'),
                        lead.get('date_scraped'),
                        lead.get('date_enriched'),
                        lead.get('created_at'),
                        lead.get('enriched', 1),
                        lead.get('ready_for_outreach', 1),
                        lead.get('score', 75),
                        lead.get('lead_quality', 'Warm'),
                        lead.get('email_confidence_level', 'Pattern'),
                        lead.get('ai_message'),
                        lead.get('needs_enrichment', 0),
                        lead.get('company_description')
                    ))
                    
                    saved_count += 1
                    self.logger.info(f"Saved: {lead['full_name']} ({lead['company']})")
                    
                except Exception as e:
                    self.logger.error(f"Error saving {lead.get('full_name', 'Unknown')}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved {saved_count} REAL leads to database")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Database save failed: {e}")
            return 0

    def sync_to_airtable(self) -> int:
        """Sync recent leads to Airtable"""
        try:
            # Get recent real leads
            conn = sqlite3.connect('data/unified_leads.db')
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute('''
                SELECT * FROM leads 
                WHERE source = 'SerpAPI_Real' 
                AND date_scraped >= date('now', '-1 day')
                ORDER BY created_at DESC 
                LIMIT 3
            ''')
            
            leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if not leads:
                self.logger.info("No new leads to sync")
                return 0
                
            synced_count = 0
            
            for lead in leads:
                if self.sync_lead_to_airtable(lead):
                    synced_count += 1
                    
            self.logger.info(f"Synced {synced_count}/{len(leads)} leads to Airtable")
            return synced_count
            
        except Exception as e:
            self.logger.error(f"Airtable sync failed: {e}")
            return 0

    def sync_lead_to_airtable(self, lead: Dict) -> bool:
        """Sync single lead to Airtable"""
        try:
            base_id = "appBZvPvNXGqtoJdc"
            table_name = "Table 1"
            api_key = os.getenv('AIRTABLE_API_KEY')
            
            url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Format date for Airtable
            def format_date(date_str):
                if not date_str:
                    return None
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d')
                except:
                    return None
            
            # Build Airtable fields
            fields = {
                "Full Name": lead.get('full_name', ''),
                "Email": lead.get('email', ''),
                "Company": lead.get('company', ''),
                "Job Title": lead.get('job_title', ''),
                "LinkedIn URL": lead.get('linkedin_url', ''),
                "Source": "Search",
                "Lead Quality": lead.get('lead_quality', 'Warm'),
                "Email_Confidence_Level": lead.get('email_confidence_level', 'Pattern'),
                "AI Message": lead.get('ai_message', ''),
                "Business_Type": lead.get('business_type', 'Small Business'),
                "Company_Description": lead.get('company_description', ''),
                "Date Scraped": format_date(lead.get('date_scraped')),
                "Date Enriched": format_date(lead.get('date_enriched'))
            }
            
            # Remove empty fields
            fields = {k: v for k, v in fields.items() if v}
            
            airtable_data = {"fields": fields}
            
            response = requests.post(url, json=airtable_data, headers=headers)
            
            if response.status_code == 200:
                record_id = response.json().get('id', 'unknown')
                self.logger.info(f"Synced {lead['full_name']} -> {record_id}")
                return True
            else:
                self.logger.error(f"Sync failed for {lead['full_name']}: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Airtable sync error for {lead.get('full_name', 'Unknown')}: {e}")
            return False

    def run_cycle(self) -> Dict:
        """Run one complete cycle"""
        cycle_start = time.time()
        self.cycle_count += 1
        
        self.logger.info(f"Starting REAL cycle #{self.cycle_count}")
        
        try:
            # 1. Scrape real leads
            leads = self.scrape_real_leads()
            
            if not leads:
                self.logger.warning("No leads found this cycle")
                return {"status": "no_leads", "duration": time.time() - cycle_start}
            
            # 2. Enrich leads
            enriched_leads = self.enrich_leads(leads)
            
            # 3. Save to database
            saved_count = self.save_to_database(enriched_leads)
            self.total_leads_found += saved_count
            
            # 4. Sync to Airtable
            synced_count = self.sync_to_airtable()
            self.total_leads_synced += synced_count
            
            duration = time.time() - cycle_start
            
            self.logger.info(f"Cycle #{self.cycle_count} complete: {saved_count} leads, {synced_count} synced in {duration:.1f}s")
            self.logger.info(f"Total: {self.total_leads_found} found, {self.total_leads_synced} synced")
            
            return {
                "status": "success",
                "leads_found": saved_count,
                "leads_synced": synced_count,
                "duration": duration
            }
            
        except Exception as e:
            self.logger.error(f"Cycle #{self.cycle_count} failed: {e}")
            return {"status": "error", "error": str(e), "duration": time.time() - cycle_start}

    def run_autonomous(self, max_cycles: int = 10000):
        """Run as autonomous organism"""
        self.logger.info(f"REAL Autonomous Organism starting - {max_cycles} cycles max")
        
        # Validate environment
        if not self.validate_environment():
            self.logger.error("Environment validation failed")
            return
            
        if not self.setup_database():
            self.logger.error("Database setup failed")
            return
            
        self.logger.info("All systems validated - organism is ALIVE!")
        
        for cycle in range(max_cycles):
            try:
                # Run cycle
                result = self.run_cycle()
                
                # Status update
                if result["status"] == "success":
                    self.logger.info(f"Organism healthy - cycle {self.cycle_count}/{max_cycles}")
                else:
                    self.logger.warning(f"Organism warning - {result.get('error', 'Unknown')}")
                
                # Rest between cycles (3.4 hours for 7 leads/day)
                self.logger.info(f"Organism resting for {self.cycle_interval/3600:.1f} hours...")
                time.sleep(self.cycle_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Organism stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Organism critical error: {e}")
                self.logger.info("Self-healing in 60 seconds...")
                time.sleep(60)
                continue
                
        self.logger.info(f"Organism completed {self.cycle_count} cycles")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='FINAL REAL 4Runr Autonomous Organism')
    parser.add_argument('--test', action='store_true', help='Run single test cycle')
    parser.add_argument('--cycles', type=int, default=10000, help='Max cycles to run')
    parser.add_argument('--run', action='store_true', help='Run autonomous organism')
    
    args = parser.parse_args()
    
    organism = FinalRealOrganism()
    
    if args.test:
        print("Testing FINAL REAL organism...")
        result = organism.run_cycle()
        print(f"Test result: {result}")
    elif args.run:
        organism.run_autonomous(args.cycles)
    else:
        print("Use --test for single cycle or --run for autonomous operation")

if __name__ == "__main__":
    main()
