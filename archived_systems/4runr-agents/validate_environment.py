#!/usr/bin/env python3
"""
Environment Validation Script

This script validates that all required environment variables are set
for real LinkedIn scraping and the full pipeline.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_environment():
    """Validate all required environment variables"""
    print("🔍 Validating Environment Setup")
    print("=" * 50)
    
    # Required variables for LinkedIn scraping
    linkedin_vars = {
        'USE_REAL_SCRAPING': 'Enable real LinkedIn scraping',
        'LINKEDIN_EMAIL': 'LinkedIn login email',
        'LINKEDIN_PASSWORD': 'LinkedIn login password',
        'SEARCH_URL': 'LinkedIn search URL for CEOs in Montreal',
        'MAX_LEADS_PER_RUN': 'Maximum leads to scrape per run',
        'MAX_PAGES_PER_RUN': 'Maximum pages to scrape per run',
        'HEADLESS': 'Run browser in headless mode'
    }
    
    # Required variables for Airtable
    airtable_vars = {
        'AIRTABLE_API_KEY': 'Airtable API key',
        'AIRTABLE_BASE_ID': 'Airtable base ID',
        'AIRTABLE_TABLE_NAME': 'Airtable table name'
    }
    
    # Optional but recommended variables
    optional_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for enrichment',
        'SMTP_HOST': 'SMTP server for email engagement',
        'SMTP_USERNAME': 'SMTP username',
        'SMTP_PASSWORD': 'SMTP password'
    }
    
    all_good = True
    
    # Check LinkedIn variables
    print("📧 LinkedIn Scraping Configuration:")
    for var, description in linkedin_vars.items():
        value = os.getenv(var)
        if value and value != 'your_linkedin_email@example.com' and value != 'your_linkedin_password':
            if var == 'LINKEDIN_PASSWORD':
                print(f"  ✅ {var}: {'*' * len(value)} ({description})")
            else:
                print(f"  ✅ {var}: {value} ({description})")
        else:
            print(f"  ❌ {var}: Not set or using placeholder ({description})")
            all_good = False
    
    print()
    
    # Check Airtable variables
    print("📊 Airtable Configuration:")
    for var, description in airtable_vars.items():
        value = os.getenv(var)
        if value and not value.startswith('your_') and not value.startswith('placeholder_'):
            if 'API_KEY' in var:
                print(f"  ✅ {var}: {value[:10]}... ({description})")
            else:
                print(f"  ✅ {var}: {value} ({description})")
        else:
            print(f"  ❌ {var}: Not set or using placeholder ({description})")
            all_good = False
    
    print()
    
    # Check optional variables
    print("🔧 Optional Configuration:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and not value.startswith('your_') and not value.startswith('placeholder_'):
            if 'API_KEY' in var or 'PASSWORD' in var:
                print(f"  ✅ {var}: {value[:10]}... ({description})")
            else:
                print(f"  ✅ {var}: {value} ({description})")
        else:
            print(f"  ⚠️  {var}: Not set ({description})")
    
    print()
    
    # Overall status
    if all_good:
        print("🎉 Environment validation passed! Ready for real LinkedIn scraping.")
        
        # Show search URL details
        search_url = os.getenv('SEARCH_URL', '')
        if 'montreal' in search_url.lower() or '105015875' in search_url:
            print("🌍 Search configured for Montreal CEOs")
        elif 'CEO' in search_url:
            print("👔 Search configured for CEOs")
        else:
            print("🔍 Custom search URL configured")
            
        return True
    else:
        print("❌ Environment validation failed. Please update your .env file.")
        print("\nTo fix:")
        print("1. Copy .env.example to .env")
        print("2. Update the placeholder values with your real credentials")
        print("3. Run this script again to validate")
        return False

def show_next_steps():
    """Show next steps for running the scraper"""
    print("\n🚀 Next Steps:")
    print("1. Build the updated scraper container:")
    print("   docker-compose build scraper")
    print()
    print("2. Run the scraper:")
    print("   docker-compose up -d scraper")
    print()
    print("3. Check the logs:")
    print("   docker-compose logs -f scraper")
    print()
    print("4. Run the full system test:")
    print("   ./run_full_system_test.sh")

if __name__ == "__main__":
    if validate_environment():
        show_next_steps()
    else:
        print("\n❌ Please fix the environment configuration before proceeding.")