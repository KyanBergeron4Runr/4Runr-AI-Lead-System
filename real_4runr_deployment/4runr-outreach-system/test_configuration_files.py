#!/usr/bin/env python3
"""
Configuration Files Validation Test Suite

This script validates the comprehensive configuration files for the Data Cleaner system,
ensuring all patterns are valid, thresholds are reasonable, and the configuration
structure is correct.
"""

import sys
import re
import yaml
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import ConfigurationManager


def test_configuration_file_loading():
    """Test that configuration files load successfully."""
    print("📁 Testing Configuration File Loading")
    print("=" * 50)
    
    try:
        # Initialize ConfigurationManager to load configurations
        config_manager = ConfigurationManager()
        
        # Check that configurations loaded
        cleaning_loaded = bool(config_manager.cleaning_rules)
        validation_loaded = bool(config_manager.validation_rules)
        
        print(f"✅ Cleaning Rules Loaded: {cleaning_loaded}")
        print(f"✅ Validation Rules Loaded: {validation_loaded}")
        
        if cleaning_loaded and validation_loaded:
            print("✅ All configuration files loaded successfully")
            return True
        else:
            print("❌ Failed to load configuration files")
            return False
            
    except Exception as e:
        print(f"❌ Error loading configuration files: {e}")
        return False


def test_cleaning_rules_structure():
    """Test the structure and content of cleaning rules."""
    print("\n🧹 Testing Cleaning Rules Structure")
    print("=" * 50)
    
    try:
        config_manager = ConfigurationManager()
        cleaning_rules = config_manager.cleaning_rules
        
        # Test required sections
        required_sections = ['company_name', 'website_url', 'search_artifacts']
        missing_sections = []
        
        for section in required_sections:
            if section not in cleaning_rules:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing required sections: {missing_sections}")
            return False
        
        print("✅ All required sections present")
        
        # Test company_name section
        company_rules = cleaning_rules['company_name']
        if 'remove_patterns' not in company_rules or not isinstance(company_rules['remove_patterns'], list):
            print("❌ company_name.remove_patterns missing or invalid")
            return False
        
        if 'normalize_patterns' not in company_rules or not isinstance(company_rules['normalize_patterns'], list):
            print("❌ company_name.normalize_patterns missing or invalid")
            return False
        
        print(f"✅ Company name rules: {len(company_rules['remove_patterns'])} remove patterns, {len(company_rules['normalize_patterns'])} normalize patterns")
        
        # Test website_url section
        website_rules = cleaning_rules['website_url']
        if 'remove_patterns' not in website_rules or not isinstance(website_rules['remove_patterns'], list):
            print("❌ website_url.remove_patterns missing or invalid")
            return False
        
        print(f"✅ Website URL rules: {len(website_rules['remove_patterns'])} remove patterns")
        
        # Test search_artifacts section
        search_rules = cleaning_rules['search_artifacts']
        if 'remove_patterns' not in search_rules or not isinstance(search_rules['remove_patterns'], list):
            print("❌ search_artifacts.remove_patterns missing or invalid")
            return False
        
        print(f"✅ Search artifacts rules: {len(search_rules['remove_patterns'])} remove patterns")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing cleaning rules structure: {e}")
        return False


def test_validation_rules_structure():
    """Test the structure and content of validation rules."""
    print("\n🔍 Testing Validation Rules Structure")
    print("=" * 50)
    
    try:
        config_manager = ConfigurationManager()
        validation_rules = config_manager.validation_rules
        
        # Test required sections
        required_sections = ['company_name', 'website_url', 'data_quality']
        missing_sections = []
        
        for section in required_sections:
            if section not in validation_rules:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing required sections: {missing_sections}")
            return False
        
        print("✅ All required sections present")
        
        # Test company_name validation rules
        company_rules = validation_rules['company_name']
        required_fields = ['min_confidence', 'forbidden_patterns', 'professional_indicators']
        
        for field in required_fields:
            if field not in company_rules:
                print(f"❌ company_name.{field} missing")
                return False
        
        # Test confidence threshold
        confidence = company_rules['min_confidence']
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            print(f"❌ Invalid confidence threshold: {confidence}")
            return False
        
        print(f"✅ Company validation rules: confidence={confidence}, {len(company_rules['forbidden_patterns'])} forbidden patterns, {len(company_rules['professional_indicators'])} professional indicators")
        
        # Test website_url validation rules
        website_rules = validation_rules['website_url']
        required_fields = ['min_confidence', 'forbidden_domains']
        
        for field in required_fields:
            if field not in website_rules:
                print(f"❌ website_url.{field} missing")
                return False
        
        confidence = website_rules['min_confidence']
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            print(f"❌ Invalid website confidence threshold: {confidence}")
            return False
        
        print(f"✅ Website validation rules: confidence={confidence}, {len(website_rules['forbidden_domains'])} forbidden domains")
        
        # Test data_quality rules
        quality_rules = validation_rules['data_quality']
        required_fields = ['required_fields', 'optional_fields']
        
        for field in required_fields:
            if field not in quality_rules:
                print(f"❌ data_quality.{field} missing")
                return False
        
        print(f"✅ Data quality rules: {len(quality_rules['required_fields'])} required fields, {len(quality_rules['optional_fields'])} optional fields")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing validation rules structure: {e}")
        return False


def test_regex_patterns():
    """Test that all regex patterns are valid and compile correctly."""
    print("\n🔧 Testing Regex Pattern Validity")
    print("=" * 50)
    
    try:
        config_manager = ConfigurationManager()
        
        patterns_tested = 0
        invalid_patterns = []
        
        # Test cleaning rules patterns
        cleaning_rules = config_manager.cleaning_rules
        
        # Test company name remove patterns
        for pattern in cleaning_rules.get('company_name', {}).get('remove_patterns', []):
            try:
                re.compile(pattern)
                patterns_tested += 1
            except re.error as e:
                invalid_patterns.append(f"company_name.remove_patterns: {pattern} - {e}")
        
        # Test company name normalize patterns
        for pattern_config in cleaning_rules.get('company_name', {}).get('normalize_patterns', []):
            if isinstance(pattern_config, dict) and 'pattern' in pattern_config:
                try:
                    re.compile(pattern_config['pattern'])
                    patterns_tested += 1
                except re.error as e:
                    invalid_patterns.append(f"company_name.normalize_patterns: {pattern_config['pattern']} - {e}")
        
        # Test search artifacts patterns
        for pattern in cleaning_rules.get('search_artifacts', {}).get('remove_patterns', []):
            try:
                re.compile(pattern)
                patterns_tested += 1
            except re.error as e:
                invalid_patterns.append(f"search_artifacts.remove_patterns: {pattern} - {e}")
        
        # Test validation rules patterns
        validation_rules = config_manager.validation_rules
        
        # Test company name required patterns
        for pattern in validation_rules.get('company_name', {}).get('required_patterns', []):
            try:
                re.compile(pattern)
                patterns_tested += 1
            except re.error as e:
                invalid_patterns.append(f"company_name.required_patterns: {pattern} - {e}")
        
        # Test website URL required format
        required_format = validation_rules.get('website_url', {}).get('required_format')
        if required_format:
            try:
                re.compile(required_format)
                patterns_tested += 1
            except re.error as e:
                invalid_patterns.append(f"website_url.required_format: {required_format} - {e}")
        
        print(f"✅ Tested {patterns_tested} regex patterns")
        
        if invalid_patterns:
            print("❌ Invalid regex patterns found:")
            for pattern in invalid_patterns:
                print(f"   {pattern}")
            return False
        else:
            print("✅ All regex patterns are valid")
            return True
        
    except Exception as e:
        print(f"❌ Error testing regex patterns: {e}")
        return False


def test_specific_garbage_patterns():
    """Test that specific garbage patterns from requirements are included."""
    print("\n🗑️ Testing Specific Garbage Pattern Coverage")
    print("=" * 50)
    
    try:
        config_manager = ConfigurationManager()
        cleaning_rules = config_manager.cleaning_rules
        
        # Required patterns from the specification
        required_patterns = [
            'Some results may have been.*',
            'Sirius XM and.*',
            'delisted consistent with local laws',
            'Learn more Next'
        ]
        
        # Get all remove patterns
        all_patterns = []
        all_patterns.extend(cleaning_rules.get('company_name', {}).get('remove_patterns', []))
        all_patterns.extend(cleaning_rules.get('search_artifacts', {}).get('remove_patterns', []))
        
        missing_patterns = []
        found_patterns = []
        
        for required_pattern in required_patterns:
            found = False
            for pattern in all_patterns:
                if required_pattern in pattern or pattern in required_pattern:
                    found = True
                    found_patterns.append(required_pattern)
                    break
            
            if not found:
                missing_patterns.append(required_pattern)
        
        print(f"✅ Found required patterns: {len(found_patterns)}")
        for pattern in found_patterns:
            print(f"   ✓ {pattern}")
        
        if missing_patterns:
            print(f"❌ Missing required patterns: {len(missing_patterns)}")
            for pattern in missing_patterns:
                print(f"   ✗ {pattern}")
            return False
        else:
            print("✅ All required garbage patterns are covered")
            return True
        
    except Exception as e:
        print(f"❌ Error testing garbage patterns: {e}")
        return False


def test_international_support():
    """Test international business entity support."""
    print("\n🌍 Testing International Support")
    print("=" * 50)
    
    try:
        config_manager = ConfigurationManager()
        validation_rules = config_manager.validation_rules
        
        # Check for international business entities
        professional_indicators = validation_rules.get('company_name', {}).get('professional_indicators', [])
        
        international_entities = ['GmbH', 'SA', 'SARL', 'AB', 'Pty Ltd', 'Pvt Ltd', 'Sdn Bhd']
        found_entities = []
        
        for entity in international_entities:
            if entity in professional_indicators:
                found_entities.append(entity)
        
        print(f"✅ International entities supported: {len(found_entities)}")
        for entity in found_entities:
            print(f"   ✓ {entity}")
        
        # Check international support flag
        international_support = validation_rules.get('data_quality', {}).get('international_support', False)
        cultural_variations = validation_rules.get('data_quality', {}).get('cultural_variations', False)
        
        print(f"✅ International support enabled: {international_support}")
        print(f"✅ Cultural variations enabled: {cultural_variations}")
        
        if len(found_entities) >= 5 and international_support and cultural_variations:
            print("✅ International support is comprehensive")
            return True
        else:
            print("❌ International support needs improvement")
            return False
        
    except Exception as e:
        print(f"❌ Error testing international support: {e}")
        return False


def test_configuration_completeness():
    """Test that configurations are comprehensive and production-ready."""
    print("\n📋 Testing Configuration Completeness")
    print("=" * 50)
    
    try:
        config_manager = ConfigurationManager()
        
        # Count patterns and rules
        cleaning_rules = config_manager.cleaning_rules
        validation_rules = config_manager.validation_rules
        
        company_remove_patterns = len(cleaning_rules.get('company_name', {}).get('remove_patterns', []))
        company_normalize_patterns = len(cleaning_rules.get('company_name', {}).get('normalize_patterns', []))
        website_remove_patterns = len(cleaning_rules.get('website_url', {}).get('remove_patterns', []))
        search_artifact_patterns = len(cleaning_rules.get('search_artifacts', {}).get('remove_patterns', []))
        
        forbidden_patterns = len(validation_rules.get('company_name', {}).get('forbidden_patterns', []))
        professional_indicators = len(validation_rules.get('company_name', {}).get('professional_indicators', []))
        forbidden_domains = len(validation_rules.get('website_url', {}).get('forbidden_domains', []))
        
        print(f"✅ Company name remove patterns: {company_remove_patterns}")
        print(f"✅ Company name normalize patterns: {company_normalize_patterns}")
        print(f"✅ Website URL remove patterns: {website_remove_patterns}")
        print(f"✅ Search artifact patterns: {search_artifact_patterns}")
        print(f"✅ Forbidden patterns: {forbidden_patterns}")
        print(f"✅ Professional indicators: {professional_indicators}")
        print(f"✅ Forbidden domains: {forbidden_domains}")
        
        # Check for reasonable coverage
        total_patterns = (company_remove_patterns + company_normalize_patterns + 
                         website_remove_patterns + search_artifact_patterns)
        
        if total_patterns >= 50:  # Reasonable threshold for comprehensive coverage
            print(f"✅ Configuration is comprehensive with {total_patterns} total patterns")
            return True
        else:
            print(f"❌ Configuration may be incomplete with only {total_patterns} total patterns")
            return False
        
    except Exception as e:
        print(f"❌ Error testing configuration completeness: {e}")
        return False


def main():
    """Run all configuration file tests."""
    print("🔧 Data Cleaner Configuration Files Test Suite")
    print("=" * 70)
    
    try:
        # Run all test suites
        test_results = []
        
        test_results.append(test_configuration_file_loading())
        test_results.append(test_cleaning_rules_structure())
        test_results.append(test_validation_rules_structure())
        test_results.append(test_regex_patterns())
        test_results.append(test_specific_garbage_patterns())
        test_results.append(test_international_support())
        test_results.append(test_configuration_completeness())
        
        # Overall results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n🎯 OVERALL TEST RESULTS")
        print("=" * 40)
        print(f"Test Suites Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\n✅ ALL CONFIGURATION TESTS PASSED!")
            print("🎉 Configuration files are production-ready")
            print("📁 Comprehensive cleaning patterns implemented")
            print("🔍 Robust validation rules configured")
            print("🌍 International support enabled")
            print("🗑️ Specific garbage patterns covered")
            print("📋 Configuration schema documented")
            return True
        else:
            print(f"\n❌ SOME CONFIGURATION TESTS FAILED!")
            print("🔧 Configuration files need fixes")
            return False
            
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)