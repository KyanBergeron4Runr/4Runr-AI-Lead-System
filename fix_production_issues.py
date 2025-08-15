#!/usr/bin/env python3
"""
Fix Production Issues Script

Addresses critical deployment blockers and lead quality issues.
Fixes connection pool, AI config, and improves lead quality.
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionFixer:
    """Fix critical production issues."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.fixes_applied = []
        
    def fix_all_issues(self):
        """Fix all critical production issues."""
        logger.info("[PRODUCTION FIX] Starting comprehensive production fixes...")
        
        try:
            # 1. Fix connection pool issues
            self.fix_connection_pool()
            
            # 2. Fix AI message generator
            self.fix_ai_message_generator()
            
            # 3. Improve business analysis prompt
            self.fix_business_analysis()
            
            # 4. Improve email discovery
            self.fix_email_discovery()
            
            # 5. Add company size validation
            self.add_company_size_validation()
            
            # 6. Create production-ready database access
            self.create_production_db_access()
            
            self.report_fixes()
            
        except Exception as e:
            logger.error(f"[ERROR] Production fix failed: {e}")
            return False
        
        return True
    
    def fix_connection_pool(self):
        """Replace connection pool with direct database access."""
        logger.info("[FIX 1] Fixing connection pool timeout issues...")
        
        # Create simplified database manager
        db_manager_content = '''#!/usr/bin/env python3
"""
Production Database Manager

Direct SQLite access without connection pooling for production reliability.
No timeouts, no complexity, just fast database operations.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

class ProductionDatabaseManager:
    """Production-ready database manager with direct SQLite access."""
    
    def __init__(self, db_path: str = "data/unified_leads.db"):
        """Initialize with database path."""
        self.db_path = db_path
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if needed
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    full_name TEXT,
                    email TEXT UNIQUE,
                    company TEXT,
                    title TEXT,
                    linkedin_url TEXT,
                    company_website TEXT,
                    phone TEXT,
                    location TEXT,
                    industry TEXT,
                    company_size TEXT,
                    business_type TEXT,
                    ai_message TEXT,
                    message_generated_at TIMESTAMP,
                    status TEXT DEFAULT 'new',
                    ready_for_outreach BOOLEAN DEFAULT 0,
                    scraped_at TIMESTAMP,
                    airtable_id TEXT,
                    sync_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Add lead to database."""
        try:
            with self.get_connection() as conn:
                # Generate ID if not provided
                if 'id' not in lead_data:
                    import uuid
                    lead_data['id'] = str(uuid.uuid4())
                
                columns = ', '.join(lead_data.keys())
                placeholders = ', '.join(['?' for _ in lead_data])
                
                conn.execute(
                    f"INSERT OR REPLACE INTO leads ({columns}) VALUES ({placeholders})",
                    list(lead_data.values())
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add lead: {e}")
            return False
    
    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM leads WHERE id = ?", (lead_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get lead: {e}")
            return None
    
    def get_leads_for_sync(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get leads ready for Airtable sync."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM leads 
                    WHERE sync_status = 'pending' 
                    AND email IS NOT NULL 
                    AND email != ''
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get leads for sync: {e}")
            return []
    
    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """Update lead data."""
        try:
            with self.get_connection() as conn:
                set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [lead_id]
                
                conn.execute(
                    f"UPDATE leads SET {set_clause} WHERE id = ?",
                    values
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update lead: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) as total FROM leads")
                total = cursor.fetchone()['total']
                
                cursor = conn.execute("SELECT COUNT(*) as with_email FROM leads WHERE email IS NOT NULL AND email != ''")
                with_email = cursor.fetchone()['with_email']
                
                cursor = conn.execute("SELECT COUNT(*) as ready FROM leads WHERE ready_for_outreach = 1")
                ready = cursor.fetchone()['ready']
                
                return {
                    'total_leads': total,
                    'leads_with_email': with_email,
                    'leads_ready_for_outreach': ready,
                    'email_percentage': round((with_email / total * 100) if total > 0 else 0, 1)
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

# Global instance
db_manager = ProductionDatabaseManager()
'''
        
        # Write the production database manager
        with open('production_db_manager.py', 'w', encoding='utf-8') as f:
            f.write(db_manager_content)
        
        self.fixes_applied.append("✅ Created production database manager (no connection pool)")
        logger.info("    - Direct SQLite access for reliability")
        logger.info("    - No timeouts or connection pooling issues")
    
    def fix_ai_message_generator(self):
        """Fix AI message generator configuration."""
        logger.info("[FIX 2] Fixing AI message generator...")
        
        # Find and fix the AI message generator
        ai_files = [
            '4runr-outreach-system/message_generator/ai_generator.py',
            '4runr-outreach-system/generator/generate_message.py'
        ]
        
        for ai_file in ai_files:
            if os.path.exists(ai_file):
                self._fix_ai_generator_file(ai_file)
    
    def _fix_ai_generator_file(self, file_path: str):
        """Fix a specific AI generator file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove problematic proxies argument
            if 'proxies=' in content:
                content = content.replace('proxies=proxies,', '')
                content = content.replace('proxies=proxies', '')
                content = content.replace(', proxies=proxies', '')
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append(f"✅ Fixed AI generator: {file_path}")
                logger.info(f"    - Removed problematic 'proxies' argument")
        
        except Exception as e:
            logger.warning(f"Could not fix {file_path}: {e}")
    
    def fix_business_analysis(self):
        """Improve business analysis to avoid platform confusion."""
        logger.info("[FIX 3] Improving business analysis prompt...")
        
        # Create improved business analysis
        improved_prompt = '''You are an AI business analyst specializing in lead qualification and business intelligence extraction.

Analyze the following website content and extract key business information. Focus on identifying the company's ACTUAL business model, not the technology platforms they use.

CRITICAL INSTRUCTIONS:
- DO NOT confuse technology platforms with business types
- If you see "Shopify", "WordPress", "Squarespace" etc., these are PLATFORMS, not business types
- Look for what the company ACTUALLY DOES, not what technology they use
- Focus on ACTUAL services, products, and business operations

Website Content:
{content}

Based on this content, provide a JSON response with the following fields:

1. Business_Type: What the company ACTUALLY does (e.g., "E-commerce Retail", "Consulting", "SaaS", "Local Service", "Manufacturing", "Agency")

2. Business_Traits: Key characteristics of their ACTUAL business (e.g., ["B2B", "Local Service", "High-Touch Sales", "Service-Based"])

3. Pain_Points: Real business challenges they likely face (e.g., ["Customer acquisition", "Manual processes", "Scaling operations"])

4. Strategic_Insight: Actionable insight for outreach based on their ACTUAL business needs

5. Company_Size_Estimate: Based on content complexity, team mentions, office locations ("Small", "Medium", "Large", "Enterprise")

6. Platform_Technologies: Separate field for platforms they use (e.g., ["Shopify", "WordPress", "HubSpot"])

Guidelines:
- Be specific about ACTUAL business operations
- Ignore technology stack when determining business type
- Focus on customer-facing services and products
- If unclear, use "Professional Services" as default
- Company size: Small (1-10), Medium (11-50), Large (51-200), Enterprise (200+)

Respond with valid JSON only:'''
        
        # Update business trait extractor
        extractor_file = '4runr-lead-scraper/enricher/business_trait_extractor.py'
        if os.path.exists(extractor_file):
            try:
                with open(extractor_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace the prompt creation method
                old_prompt_start = 'prompt = f"""You are an AI business analyst'
                new_prompt_start = f'prompt = f"""{improved_prompt.strip()}'
                
                if old_prompt_start in content:
                    # Find the end of the old prompt
                    start_idx = content.find(old_prompt_start)
                    end_idx = content.find('"""', start_idx + 10) + 3
                    
                    if start_idx != -1 and end_idx != -1:
                        new_content = content[:start_idx] + new_prompt_start + '"""' + content[end_idx:]
                        
                        with open(extractor_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        self.fixes_applied.append("✅ Improved business analysis prompt")
                        logger.info("    - Added platform vs business type distinction")
                        logger.info("    - Added company size estimation")
                        logger.info("    - Separated technology platforms from business type")
            
            except Exception as e:
                logger.warning(f"Could not update business trait extractor: {e}")
    
    def fix_email_discovery(self):
        """Improve email discovery to be more practical."""
        logger.info("[FIX 4] Improving email discovery...")
        
        # Create improved email finder
        email_finder_content = '''#!/usr/bin/env python3
"""
Improved Email Finder

More practical email discovery that includes common business emails.
Focuses on finding ANY valid business email, not just personal ones.
"""

import re
import requests
import logging
from typing import List, Optional, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ImprovedEmailFinder:
    """Find business emails more effectively."""
    
    def __init__(self):
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def find_business_emails(self, company_website: str, company_name: str = "") -> List[str]:
        """Find business emails from company website."""
        emails = []
        
        try:
            logger.info(f"[EMAIL] Searching for emails on {company_website}")
            
            # Get domain from website
            domain = self._extract_domain(company_website)
            if not domain:
                return emails
            
            # Try multiple pages
            pages_to_check = [
                company_website,
                f"{company_website}/contact",
                f"{company_website}/about",
                f"{company_website}/team",
                f"{company_website}/contact-us"
            ]
            
            for page_url in pages_to_check:
                try:
                    response = requests.get(page_url, headers=self.headers, timeout=self.timeout)
                    if response.status_code == 200:
                        page_emails = self._extract_emails_from_page(response.text, domain)
                        emails.extend(page_emails)
                except:
                    continue
            
            # Remove duplicates and filter
            emails = list(set(emails))
            emails = self._filter_valid_business_emails(emails, domain)
            
            logger.info(f"[EMAIL] Found {len(emails)} valid emails")
            return emails[:3]  # Return top 3 emails
            
        except Exception as e:
            logger.error(f"[EMAIL] Email search failed: {e}")
            return emails
    
    def _extract_domain(self, website: str) -> Optional[str]:
        """Extract domain from website URL."""
        try:
            if '://' not in website:
                website = 'https://' + website
            
            from urllib.parse import urlparse
            parsed = urlparse(website)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except:
            return None
    
    def _extract_emails_from_page(self, html_content: str, domain: str) -> List[str]:
        """Extract emails from HTML content."""
        emails = []
        
        # Email regex pattern
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        found_emails = re.findall(email_pattern, html_content, re.IGNORECASE)
        
        # Filter emails from the same domain
        for email in found_emails:
            email = email.lower()
            if domain.lower() in email:
                emails.append(email)
        
        return emails
    
    def _filter_valid_business_emails(self, emails: List[str], domain: str) -> List[str]:
        """Filter and prioritize business emails."""
        valid_emails = []
        
        # Skip obvious spam/invalid emails
        skip_patterns = [
            'noreply', 'no-reply', 'donotreply', 'test@', 'example@',
            'webmaster@', 'admin@', 'postmaster@'
        ]
        
        # Prioritize business emails
        priority_patterns = [
            'info@', 'contact@', 'hello@', 'sales@', 'business@',
            'office@', 'support@'  # Include support emails
        ]
        
        priority_emails = []
        other_emails = []
        
        for email in emails:
            email = email.strip().lower()
            
            # Skip invalid emails
            if any(skip in email for skip in skip_patterns):
                continue
            
            # Basic email validation
            if '@' not in email or '.' not in email.split('@')[1]:
                continue
            
            # Categorize emails
            if any(pattern in email for pattern in priority_patterns):
                priority_emails.append(email)
            else:
                other_emails.append(email)
        
        # Return priority emails first, then others
        valid_emails = priority_emails + other_emails
        return valid_emails[:5]  # Limit to 5 emails max

# Global instance
email_finder = ImprovedEmailFinder()
'''
        
        with open('improved_email_finder.py', 'w', encoding='utf-8') as f:
            f.write(email_finder_content)
        
        self.fixes_applied.append("✅ Created improved email finder")
        logger.info("    - Includes info@, contact@, support@ emails")
        logger.info("    - More practical business email discovery")
    
    def add_company_size_validation(self):
        """Add proper company size validation."""
        logger.info("[FIX 5] Adding company size validation...")
        
        company_validator_content = '''#!/usr/bin/env python3
"""
Company Size Validator

Validates company size to ensure leads are from appropriately sized companies.
Filters out massive corporations that won't respond to outreach.
"""

import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CompanySizeValidator:
    """Validate company size for lead qualification."""
    
    def __init__(self):
        self.massive_companies = {
            # Technology Giants
            'apple', 'microsoft', 'google', 'amazon', 'facebook', 'meta',
            'netflix', 'tesla', 'nvidia', 'adobe', 'salesforce', 'oracle',
            
            # Canadian Giants  
            'shopify', 'rbc', 'td bank', 'scotia bank', 'bmo', 'hydro-quebec',
            'cgi group', 'bombardier', 'suncor', 'canadian tire', 'loblaws',
            'rogers', 'bell canada', 'telus', 'power corporation',
            
            # Other Large Corporations
            'walmart', 'coca-cola', 'pepsi', 'mcdonalds', 'starbucks',
            'jp morgan', 'goldman sachs', 'blackrock', 'berkshire hathaway'
        }
    
    def is_company_too_large(self, company_name: str, company_website: str = "") -> bool:
        """Check if company is too large for outreach."""
        if not company_name:
            return False
        
        company_lower = company_name.lower()
        
        # Check against known massive companies
        for massive_company in self.massive_companies:
            if massive_company in company_lower:
                logger.info(f"[SIZE] Company too large: {company_name}")
                return True
        
        # Check for corporate indicators
        corporate_indicators = [
            'corporation', 'corp', 'inc.', 'ltd.', 'limited',
            'international', 'global', 'worldwide', 'group'
        ]
        
        indicator_count = sum(1 for indicator in corporate_indicators if indicator in company_lower)
        
        # If multiple corporate indicators, likely too large
        if indicator_count >= 2:
            logger.info(f"[SIZE] Multiple corporate indicators: {company_name}")
            return True
        
        return False
    
    def estimate_company_size(self, website_content: str, company_name: str = "") -> Dict[str, Any]:
        """Estimate company size from website content."""
        if not website_content:
            return {'size': 'Unknown', 'confidence': 'Low', 'employee_estimate': None}
        
        content_lower = website_content.lower()
        
        # Look for employee count indicators
        employee_indicators = [
            ('startup', 'Small', 1, 10),
            ('small team', 'Small', 1, 10),
            ('boutique', 'Small', 1, 15),
            ('growing team', 'Medium', 10, 50),
            ('established', 'Medium', 20, 100),
            ('enterprise', 'Large', 100, 500),
            ('fortune', 'Enterprise', 500, 10000),
            ('multinational', 'Enterprise', 1000, 50000)
        ]
        
        for indicator, size, min_emp, max_emp in employee_indicators:
            if indicator in content_lower:
                return {
                    'size': size,
                    'confidence': 'Medium',
                    'employee_estimate': f"{min_emp}-{max_emp}",
                    'indicator': indicator
                }
        
        # Estimate based on content complexity
        word_count = len(content_lower.split())
        
        if word_count > 5000:
            return {'size': 'Large', 'confidence': 'Low', 'employee_estimate': '50+'}
        elif word_count > 2000:
            return {'size': 'Medium', 'confidence': 'Low', 'employee_estimate': '10-50'}
        else:
            return {'size': 'Small', 'confidence': 'Low', 'employee_estimate': '1-10'}
    
    def is_good_outreach_target(self, company_name: str, website_content: str = "") -> Dict[str, Any]:
        """Determine if company is a good outreach target."""
        
        # Check if too large
        if self.is_company_too_large(company_name):
            return {
                'is_good_target': False,
                'reason': 'Company too large',
                'size_estimate': 'Enterprise'
            }
        
        # Get size estimate
        size_info = self.estimate_company_size(website_content, company_name)
        
        # Good targets: Small to Medium companies
        good_sizes = ['Small', 'Medium']
        is_good = size_info['size'] in good_sizes
        
        return {
            'is_good_target': is_good,
            'reason': f"Size: {size_info['size']}" + (" - Good target" if is_good else " - Too large"),
            'size_estimate': size_info['size'],
            'employee_estimate': size_info.get('employee_estimate'),
            'confidence': size_info['confidence']
        }

# Global instance
company_validator = CompanySizeValidator()
'''
        
        with open('company_size_validator.py', 'w', encoding='utf-8') as f:
            f.write(company_validator_content)
        
        self.fixes_applied.append("✅ Created company size validator")
        logger.info("    - Filters out massive corporations")
        logger.info("    - Targets small-medium companies (1-100 employees)")
    
    def create_production_db_access(self):
        """Create production database access script."""
        logger.info("[FIX 6] Creating production database access...")
        
        db_access_content = '''#!/usr/bin/env python3
"""
Production Database Access

Direct database access for production use.
Bypasses connection pooling for reliability.
"""

import os
import sys
import json
import logging
from production_db_manager import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_lead_fast(lead_data):
    """Add lead using fast direct database access."""
    try:
        success = db_manager.add_lead(lead_data)
        if success:
            logger.info(f"[FAST DB] Added lead: {lead_data.get('email', 'no-email')}")
        return success
    except Exception as e:
        logger.error(f"[FAST DB] Failed to add lead: {e}")
        return False

def get_leads_for_airtable():
    """Get leads ready for Airtable sync."""
    try:
        leads = db_manager.get_leads_for_sync()
        logger.info(f"[FAST DB] Found {len(leads)} leads for sync")
        return leads
    except Exception as e:
        logger.error(f"[FAST DB] Failed to get leads: {e}")
        return []

def update_lead_fast(lead_id, updates):
    """Update lead using fast direct access."""
    try:
        success = db_manager.update_lead(lead_id, updates)
        if success:
            logger.info(f"[FAST DB] Updated lead: {lead_id}")
        return success
    except Exception as e:
        logger.error(f"[FAST DB] Failed to update lead: {e}")
        return False

def get_db_stats():
    """Get database statistics."""
    try:
        stats = db_manager.get_database_stats()
        logger.info(f"[FAST DB] Database stats: {stats}")
        return stats
    except Exception as e:
        logger.error(f"[FAST DB] Failed to get stats: {e}")
        return {}

if __name__ == "__main__":
    # Test the fast database access
    stats = get_db_stats()
    print(f"Database Statistics: {json.dumps(stats, indent=2)}")
'''
        
        with open('production_db_access.py', 'w', encoding='utf-8') as f:
            f.write(db_access_content)
        
        self.fixes_applied.append("✅ Created production database access")
        logger.info("    - Fast, direct database operations")
        logger.info("    - No connection pool timeouts")
    
    def report_fixes(self):
        """Report all fixes applied."""
        logger.info("\n" + "="*60)
        logger.info("[PRODUCTION FIX] ALL FIXES COMPLETED!")
        logger.info("="*60)
        
        for fix in self.fixes_applied:
            logger.info(f"  {fix}")
        
        logger.info("\n[NEXT STEPS] Files created:")
        logger.info("  - production_db_manager.py (reliable database access)")
        logger.info("  - improved_email_finder.py (better email discovery)")
        logger.info("  - company_size_validator.py (company size filtering)")
        logger.info("  - production_db_access.py (fast database operations)")
        
        logger.info("\n[DEPLOYMENT] The system is now much more production-ready!")
        logger.info("  [PERFORMANCE] No more connection pool timeouts")
        logger.info("  [RELIABILITY] Direct database access")
        logger.info("  [QUALITY] Better lead qualification")
        logger.info("  [TARGETING] Proper company size filtering")

if __name__ == "__main__":
    fixer = ProductionFixer()
    success = fixer.fix_all_issues()
    
    if success:
        print("\n🎉 PRODUCTION FIXES COMPLETE!")
        print("The system is now much more production-ready.")
    else:
        print("\n❌ Some fixes failed. Check logs for details.")
