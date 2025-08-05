#!/usr/bin/env python3
"""
LinkedIn URL Verification Tool

Verifies that all LinkedIn URLs in our data files are working properly
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict

# Add shared modules to path
sys.path.append(str(Path(__file__).parent / 'shared'))
from linkedin_url_validator import validate_linkedin_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('url-verifier')

class LinkedInURLVerifier:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / 'shared'
        
        # Files to check
        self.data_files = [
            'raw_leads.json',
            'verified_leads.json',
            'enriched_leads.json',
            'engaged_leads.json',
            'test_leads.json'
        ]
    
    def verify_file_urls(self, filename: str) -> Dict:
        """Verify LinkedIn URLs in a specific file"""
        file_path = self.shared_dir / filename
        
        result = {
            'file': filename,
            'exists': file_path.exists(),
            'total_leads': 0,
            'urls_tested': 0,
            'valid_urls': 0,
            'invalid_urls': 0,
            'issues': []
        }
        
        if not file_path.exists():
            logger.info(f"⚪ {filename}: File not found")
            return result
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                leads = json.load(f)
            
            if not isinstance(leads, list):
                result['issues'].append("File is not a list of leads")
                return result
            
            result['total_leads'] = len(leads)
            
            logger.info(f"🔍 Verifying {filename} ({len(leads)} leads)")
            
            for i, lead in enumerate(leads, 1):
                linkedin_url = lead.get('linkedin_url')
                name = lead.get('name', lead.get('full_name', f'Lead {i}'))
                
                if not linkedin_url:
                    logger.debug(f"   {i}. {name}: No LinkedIn URL")
                    continue
                
                result['urls_tested'] += 1
                
                # Validate the URL
                validation_result = validate_linkedin_url(linkedin_url, test_accessibility=True)
                
                if validation_result['overall_valid']:
                    result['valid_urls'] += 1
                    logger.info(f"   ✅ {i}. {name}: URL valid ({validation_result['status_code']}, {validation_result['response_time']}s)")
                else:
                    result['invalid_urls'] += 1
                    issues = ', '.join(validation_result['issues'])
                    logger.warning(f"   ❌ {i}. {name}: URL invalid - {issues}")
                    
                    result['issues'].append({
                        'lead_name': name,
                        'url': linkedin_url,
                        'issues': validation_result['issues']
                    })
                
                # Small delay to be respectful
                import time
                time.sleep(0.5)
            
            logger.info(f"📊 {filename} results: {result['valid_urls']}/{result['urls_tested']} URLs valid")
            
        except json.JSONDecodeError as e:
            result['issues'].append(f"Invalid JSON: {str(e)}")
            logger.error(f"❌ {filename}: Invalid JSON - {e}")
        except Exception as e:
            result['issues'].append(f"Error processing file: {str(e)}")
            logger.error(f"❌ {filename}: Error - {e}")
        
        return result
    
    def verify_all_files(self) -> Dict:
        """Verify LinkedIn URLs in all data files"""
        logger.info("🔍 Starting LinkedIn URL verification for all files")
        
        overall_results = {
            'files_checked': 0,
            'total_leads': 0,
            'total_urls_tested': 0,
            'total_valid_urls': 0,
            'total_invalid_urls': 0,
            'file_results': [],
            'summary': {}
        }
        
        for filename in self.data_files:
            file_result = self.verify_file_urls(filename)
            
            if file_result['exists']:
                overall_results['files_checked'] += 1
                overall_results['total_leads'] += file_result['total_leads']
                overall_results['total_urls_tested'] += file_result['urls_tested']
                overall_results['total_valid_urls'] += file_result['valid_urls']
                overall_results['total_invalid_urls'] += file_result['invalid_urls']
            
            overall_results['file_results'].append(file_result)
        
        # Generate summary
        if overall_results['total_urls_tested'] > 0:
            success_rate = (overall_results['total_valid_urls'] / overall_results['total_urls_tested']) * 100
            overall_results['summary']['success_rate'] = round(success_rate, 1)
        else:
            overall_results['summary']['success_rate'] = 0
        
        return overall_results
    
    def print_summary_report(self, results: Dict):
        """Print a comprehensive summary report"""
        logger.info("\n" + "="*80)
        logger.info("📊 LINKEDIN URL VERIFICATION SUMMARY")
        logger.info("="*80)
        
        logger.info(f"Files checked: {results['files_checked']}")
        logger.info(f"Total leads: {results['total_leads']}")
        logger.info(f"URLs tested: {results['total_urls_tested']}")
        logger.info(f"Valid URLs: {results['total_valid_urls']}")
        logger.info(f"Invalid URLs: {results['total_invalid_urls']}")
        logger.info(f"Success rate: {results['summary']['success_rate']}%")
        
        logger.info(f"\n📋 FILE BREAKDOWN:")
        for file_result in results['file_results']:
            if file_result['exists']:
                success_rate = 0
                if file_result['urls_tested'] > 0:
                    success_rate = (file_result['valid_urls'] / file_result['urls_tested']) * 100
                
                logger.info(f"   {file_result['file']}: {file_result['valid_urls']}/{file_result['urls_tested']} valid ({success_rate:.1f}%)")
            else:
                logger.info(f"   {file_result['file']}: Not found")
        
        # Show issues if any
        invalid_count = 0
        for file_result in results['file_results']:
            invalid_count += len(file_result['issues'])
        
        if invalid_count > 0:
            logger.info(f"\n❌ INVALID URLs FOUND ({invalid_count}):")
            for file_result in results['file_results']:
                if file_result['issues']:
                    logger.info(f"   {file_result['file']}:")
                    for issue in file_result['issues'][:5]:  # Show first 5 issues
                        if isinstance(issue, dict):
                            logger.info(f"      - {issue['lead_name']}: {', '.join(issue['issues'])}")
                    
                    if len(file_result['issues']) > 5:
                        logger.info(f"      ... and {len(file_result['issues']) - 5} more issues")
        
        logger.info("="*80)
    
    def fix_invalid_urls(self, results: Dict) -> int:
        """Attempt to fix invalid URLs where possible"""
        logger.info("🔧 Attempting to fix invalid URLs...")
        
        fixed_count = 0
        
        for file_result in results['file_results']:
            if not file_result['exists'] or not file_result['issues']:
                continue
            
            filename = file_result['file']
            file_path = self.shared_dir / filename
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    leads = json.load(f)
                
                modified = False
                
                for lead in leads:
                    linkedin_url = lead.get('linkedin_url')
                    name = lead.get('name', lead.get('full_name', 'Unknown'))
                    
                    if linkedin_url:
                        # Try to clean and fix the URL
                        from linkedin_url_validator import clean_linkedin_url
                        cleaned_url = clean_linkedin_url(linkedin_url)
                        
                        if cleaned_url and cleaned_url != linkedin_url:
                            # Test the cleaned URL
                            validation_result = validate_linkedin_url(cleaned_url, test_accessibility=True)
                            
                            if validation_result['overall_valid']:
                                logger.info(f"   ✅ Fixed URL for {name}: {linkedin_url} → {cleaned_url}")
                                lead['linkedin_url'] = cleaned_url
                                modified = True
                                fixed_count += 1
                
                if modified:
                    # Save the updated file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(leads, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"💾 Updated {filename} with fixed URLs")
                
            except Exception as e:
                logger.error(f"❌ Error fixing URLs in {filename}: {e}")
        
        logger.info(f"🔧 Fixed {fixed_count} URLs")
        return fixed_count

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify LinkedIn URLs in data files')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix invalid URLs')
    args = parser.parse_args()
    
    verifier = LinkedInURLVerifier()
    
    # Run verification
    results = verifier.verify_all_files()
    
    # Print summary
    verifier.print_summary_report(results)
    
    # Fix URLs if requested
    if args.fix and results['total_invalid_urls'] > 0:
        fixed_count = verifier.fix_invalid_urls(results)
        
        if fixed_count > 0:
            logger.info("🔄 Re-running verification after fixes...")
            results = verifier.verify_all_files()
            verifier.print_summary_report(results)
    
    # Return success if most URLs are valid
    success_rate = results['summary']['success_rate']
    
    if success_rate >= 80:
        logger.info("✅ LinkedIn URL verification passed")
        return True
    else:
        logger.error(f"❌ LinkedIn URL verification failed - only {success_rate}% valid")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)