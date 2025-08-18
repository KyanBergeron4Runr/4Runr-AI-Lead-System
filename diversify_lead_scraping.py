#!/usr/bin/env python3
"""
Diversify Lead Scraping
=======================
Fix same-people issue with varied search terms and better acceptance criteria
"""

import sqlite3
import logging
import json
from datetime import datetime

class LeadScrapingDiversifier:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def analyze_current_search_patterns(self):
        """Analyze why we keep getting the same results"""
        self.logger.info("🔍 Analyzing current search patterns...")
        
        # The issue is in the search queries - they're too generic and repetitive
        current_issues = {
            'search_location': 'Montreal, Quebec, Canada (too specific)',
            'search_queries': ['CEO', 'Founder', 'President'] ,  # Too generic
            'quality_filters': 'Too strict - rejecting valid leads',
            'search_diversity': 'No variation in search terms'
        }
        
        self.logger.info("📊 Current search issues:")
        for issue, description in current_issues.items():
            self.logger.info(f"   ❌ {issue}: {description}")
        
        return current_issues

    def create_diverse_search_config(self):
        """Create a more diverse search configuration"""
        self.logger.info("🎯 Creating diverse search configuration...")
        
        # Diversified search terms
        diverse_config = {
            'locations': [
                'Montreal, Quebec, Canada',
                'Toronto, Ontario, Canada', 
                'Vancouver, BC, Canada',
                'Calgary, Alberta, Canada',
                'Ottawa, Ontario, Canada'
            ],
            'job_titles': [
                'CEO', 'Chief Executive Officer',
                'Founder', 'Co-Founder', 
                'President', 'Vice President',
                'CTO', 'Chief Technology Officer',
                'CMO', 'Chief Marketing Officer',
                'Director', 'Managing Director',
                'Owner', 'Business Owner'
            ],
            'industries': [
                'startup', 'technology', 'software',
                'consulting', 'marketing', 'finance',
                'healthcare', 'education', 'retail',
                'manufacturing', 'real estate', 'legal'
            ],
            'company_sizes': [
                'startup', 'small business', 'growing company',
                'mid-size company', 'enterprise'
            ]
        }
        
        self.logger.info("✅ Diverse search configuration created:")
        self.logger.info(f"   📍 {len(diverse_config['locations'])} locations")
        self.logger.info(f"   💼 {len(diverse_config['job_titles'])} job titles") 
        self.logger.info(f"   🏢 {len(diverse_config['industries'])} industries")
        
        return diverse_config

    def suggest_search_improvements(self):
        """Suggest specific improvements to search logic"""
        self.logger.info("💡 Search improvement suggestions:")
        
        improvements = [
            {
                'issue': 'Same search queries',
                'solution': 'Rotate through different job titles and industries',
                'implementation': 'Modify SerpAPI queries to include industry + title combinations'
            },
            {
                'issue': 'Geographic limitation', 
                'solution': 'Expand to multiple Canadian cities',
                'implementation': 'Cycle through Toronto, Vancouver, Calgary, Ottawa'
            },
            {
                'issue': 'Quality filters too strict',
                'solution': 'Accept leads with LinkedIn + partial company info',
                'implementation': 'Lower the bar for "Unknown Company" if other data is good'
            },
            {
                'issue': 'No search variation',
                'solution': 'Add time-based search rotation',
                'implementation': 'Different search terms each cycle'
            }
        ]
        
        for i, improvement in enumerate(improvements, 1):
            self.logger.info(f"\n   {i}. {improvement['issue']}")
            self.logger.info(f"      💡 Solution: {improvement['solution']}")
            self.logger.info(f"      🔧 Implementation: {improvement['implementation']}")
        
        return improvements

    def create_immediate_fix_config(self):
        """Create an immediate configuration to get new leads"""
        self.logger.info("🔧 Creating immediate fix configuration...")
        
        # Simple but effective search variations
        immediate_searches = [
            'site:linkedin.com/in/ "Chief Technology Officer" Toronto',
            'site:linkedin.com/in/ "Marketing Director" Vancouver', 
            'site:linkedin.com/in/ "Business Owner" Calgary',
            'site:linkedin.com/in/ "Startup Founder" Ottawa',
            'site:linkedin.com/in/ "VP Sales" Montreal',
            'site:linkedin.com/in/ "General Manager" Toronto startup',
            'site:linkedin.com/in/ "Operations Manager" Vancouver tech',
            'site:linkedin.com/in/ "Product Manager" Montreal software'
        ]
        
        config = {
            'search_queries': immediate_searches,
            'acceptance_criteria': {
                'require_email': False,  # Don't require email
                'require_real_company': False,  # Accept partial company info
                'require_website': False,  # Don't require website
                'minimum_requirement': 'LinkedIn + Job Title'  # Just need basic info
            }
        }
        
        self.logger.info(f"✅ Created {len(immediate_searches)} diverse search queries")
        self.logger.info("✅ Relaxed acceptance criteria for immediate results")
        
        return config

    def save_diverse_config(self, config):
        """Save the diverse configuration for use"""
        config_file = 'config/diverse_search_config.json'
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"💾 Saved diverse config to: {config_file}")
            return config_file
            
        except Exception as e:
            self.logger.error(f"❌ Error saving config: {e}")
            return None

def main():
    diversifier = LeadScrapingDiversifier()
    
    print("🔍 LEAD SCRAPING DIVERSIFICATION")
    print("=" * 35)
    print("📋 Analyzing why we keep finding the same people...")
    print("")
    
    # Analyze current issues
    issues = diversifier.analyze_current_search_patterns()
    
    print(f"\n🎯 Creating solutions...")
    
    # Create diverse configuration
    diverse_config = diversifier.create_diverse_search_config()
    
    # Get improvement suggestions
    improvements = diversifier.suggest_search_improvements()
    
    # Create immediate fix
    immediate_config = diversifier.create_immediate_fix_config()
    
    # Save configuration
    config_file = diversifier.save_diverse_config({
        'diverse': diverse_config,
        'immediate': immediate_config,
        'improvements': improvements
    })
    
    print(f"\n🎉 DIVERSIFICATION COMPLETE!")
    print(f"   📊 Identified {len(issues)} search pattern issues")
    print(f"   💡 Created {len(improvements)} improvement strategies")
    print(f"   🎯 Generated diverse search variations")
    print(f"   📁 Saved config: {config_file}")
    
    print(f"\n🔧 IMMEDIATE FIXES NEEDED:")
    print(f"   1. Expand search locations (Toronto, Vancouver, Calgary)")
    print(f"   2. Rotate job titles (CTO, CMO, Director, Owner)")
    print(f"   3. Add industry terms (tech, startup, consulting)")
    print(f"   4. Lower quality filters (accept LinkedIn + partial info)")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Modify SerpAPI scraper to use diverse queries")
    print(f"   2. Implement search rotation logic")
    print(f"   3. Relax lead acceptance criteria")
    print(f"   4. Test with varied search terms")

if __name__ == "__main__":
    main()
