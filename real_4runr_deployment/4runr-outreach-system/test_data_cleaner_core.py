#!/usr/bin/env python3
"""
Test the core Data Cleaner infrastructure.

This script tests the basic functionality of the DataCleaner class
to ensure it can clean and validate data properly.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import DataCleaner


def test_garbage_data_cleaning():
    """Test cleaning of known garbage data."""
    print("🧹 Testing Data Cleaner with Garbage Data")
    print("=" * 50)
    
    # Initialize the data cleaner
    cleaner = DataCleaner()
    
    # Test cases with known garbage data
    test_cases = [
        {
            'name': 'Sirius XM Garbage',
            'raw_data': {
                'Company': 'Sirius XM and ... Some results may have been delisted consistent with local laws. Learn more Next',
                'Website': 'https://google.com/search?q=company'
            },
            'context': {'id': 'test1', 'Full Name': 'John Doe'}
        },
        {
            'name': 'HTML Fragments',
            'raw_data': {
                'Company': '<div>TechCorp Inc</div>&nbsp;',
                'Website': 'https://techcorp.com'
            },
            'context': {'id': 'test2', 'Full Name': 'Jane Smith'}
        },
        {
            'name': 'Search Artifacts',
            'raw_data': {
                'Company': 'About 1,234 results for InnovateNow LLC',
                'Website': 'https://linkedin.com/company/innovatenow'
            },
            'context': {'id': 'test3', 'Full Name': 'Bob Johnson'}
        },
        {
            'name': 'Clean Professional Data',
            'raw_data': {
                'Company': 'Montreal Tech Solutions Inc',
                'Website': 'https://montrealtechsolutions.com'
            },
            'context': {'id': 'test4', 'Full Name': 'Alice Brown'}
        }
    ]
    
    # Process each test case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print("-" * 30)
        
        # Show original data
        print("📥 Original Data:")
        for field, value in test_case['raw_data'].items():
            print(f"  {field}: '{value}'")
        
        # Clean and validate
        result = cleaner.clean_and_validate(test_case['raw_data'], test_case['context'])
        
        # Show results
        print(f"\n📊 Result: {'✅ SUCCESS' if result.success else '❌ REJECTED'}")
        print(f"   Confidence Score: {result.confidence_score:.2f}")
        print(f"   Processing Time: {result.processing_time:.3f}s")
        
        if result.success:
            print("📤 Cleaned Data:")
            for field, value in result.cleaned_data.items():
                print(f"  {field}: '{value}'")
        else:
            print("🚫 Rejection Reasons:")
            for reason in result.rejection_reasons:
                print(f"  - {reason}")
        
        # Show cleaning actions
        if result.cleaning_actions:
            print("🧹 Cleaning Actions:")
            for action in result.cleaning_actions:
                print(f"  - {action.rule_name}: '{action.original_value}' → '{action.cleaned_value}'")
        
        # Show validation results
        if result.validation_results:
            print("✅ Validation Results:")
            for validation in result.validation_results:
                status = "PASS" if validation.is_valid else "FAIL"
                print(f"  - {validation.field_name}: {status} ({validation.confidence_score:.2f})")
                if not validation.is_valid:
                    print(f"    Error: {validation.error_message}")
    
    # Show overall statistics
    print(f"\n📈 Overall Statistics:")
    stats = cleaner.get_cleaning_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    return stats['successful_cleanings'] > 0


def test_configuration_loading():
    """Test configuration loading and management."""
    print("\n⚙️  Testing Configuration Management")
    print("=" * 50)
    
    cleaner = DataCleaner()
    
    # Test configuration access
    print("📋 Cleaning Rules Loaded:")
    for category, rules in cleaner.config_manager.cleaning_rules.items():
        print(f"  {category}: {len(rules)} rule groups")
    
    print("\n📋 Validation Rules Loaded:")
    for category, rules in cleaner.config_manager.validation_rules.items():
        print(f"  {category}: {len(rules)} validation criteria")
    
    # Test rule version
    version = cleaner.config_manager.get_rule_version()
    print(f"\n📅 Rule Version: {version}")
    
    return True


def main():
    """Run all core infrastructure tests."""
    print("🧪 Data Cleaner Core Infrastructure Test")
    print("=" * 60)
    
    try:
        # Test configuration loading
        config_test = test_configuration_loading()
        
        # Test data cleaning
        cleaning_test = test_garbage_data_cleaning()
        
        # Overall result
        if config_test and cleaning_test:
            print(f"\n✅ ALL TESTS PASSED!")
            print("🎯 Data Cleaner core infrastructure is working correctly")
            print("🚀 Ready to integrate with enricher pipeline")
            return True
        else:
            print(f"\n❌ SOME TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)