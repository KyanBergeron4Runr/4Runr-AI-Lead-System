#!/usr/bin/env python3
"""
Test script for the Enhanced Message Generator functionality.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.message_generator_enhanced import MessageGeneratorEnhanced


def test_message_generator():
    """Test the Enhanced Message Generator functionality."""
    print("🧪 Testing Enhanced Message Generator...")
    
    # Test 1: Initialize generator
    print("\n1. Testing generator initialization...")
    try:
        generator = MessageGeneratorEnhanced()
        print("   ✅ Generator initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize generator: {e}")
        return False
    
    # Test 2: Test basic generation capability
    print("\n2. Testing basic generation capability...")
    try:
        can_generate = generator.test_message_generation("Acme Corp")
        print(f"   {'✅' if can_generate else '❌'} Basic generation capability: {can_generate}")
    except Exception as e:
        print(f"   ❌ Generation capability test failed: {e}")
    
    # Test 3: Test tone guidance for different engagement levels
    print("\n3. Testing engagement level tone guidance...")
    levels = ['1st degree', '2nd degree', '3rd degree', 'retry']
    
    for level in levels:
        tone = generator._get_tone_for_engagement_level(level)
        print(f"   📋 {level}: {tone[:80]}...")
    
    # Test 4: Test message validation
    print("\n4. Testing message validation...")
    test_lead = {
        'id': 'test_123',
        'Name': 'John Doe',
        'Company': 'Test Company',
        'Email': 'john@testcompany.com'
    }
    
    validation_tests = [
        ("Short message", "Hi there", False),
        ("Missing 4Runr", "This is a long message about systems and infrastructure for Test Company but missing the key brand name.", False),
        ("Missing company", "4Runr specializes in systems and infrastructure solutions for businesses.", False),
        ("Good message", "4Runr specializes in systems thinking and infrastructure solutions for Test Company. Our approach helps businesses achieve operational excellence through intelligent systems that scale with growth.", True),
        ("Generic opening", "I hope this email finds you well. 4Runr specializes in systems and infrastructure for Test Company.", False)
    ]
    
    for test_name, message, expected in validation_tests:
        result = generator._validate_message_quality(message, test_lead)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {test_name}: {result} (expected: {expected})")
    
    # Test 5: Test fallback messages for all engagement levels
    print("\n5. Testing fallback messages...")
    for level in levels:
        fallback = generator._get_fallback_message(test_lead, level)
        print(f"   📧 {level} fallback: {len(fallback)} characters")
        
        # Validate fallback meets basic requirements
        has_company = test_lead['Company'].lower() in fallback.lower()
        has_4runr = '4runr' in fallback.lower()
        has_systems = 'systems' in fallback.lower() or 'infrastructure' in fallback.lower()
        
        all_good = has_company and has_4runr and has_systems
        print(f"      {'✅' if all_good else '❌'} Contains required elements: company={has_company}, 4runr={has_4runr}, systems/infra={has_systems}")
    
    # Test 6: Test system prompt generation
    print("\n6. Testing system prompt generation...")
    for level in levels:
        system_prompt = generator._get_system_prompt(level)
        print(f"   📝 {level} system prompt: {len(system_prompt)} characters")
        
        # Check that it contains level-specific guidance
        has_level_guidance = level.replace(' ', '').lower() in system_prompt.lower().replace(' ', '')
        print(f"      {'✅' if has_level_guidance else '⚠️'} Contains level-specific guidance: {has_level_guidance}")
    
    # Test 7: Test full message generation (will use fallback without OpenAI API)
    print("\n7. Testing full message generation...")
    try:
        test_knowledge = """4Runr Knowledge Base
        
        Core Philosophy:
        - Systems thinking approach
        - Infrastructure-first mindset  
        - AI-as-a-layer philosophy
        - Business value language
        
        We build intelligent infrastructure that scales with business growth."""
        
        test_company_summary = "Test Company is a growing technology firm focused on business automation solutions."
        
        message = generator.generate_personalized_message(
            test_lead, test_knowledge, test_company_summary, '1st degree'
        )
        
        print(f"   📧 Generated message: {len(message)} characters")
        print(f"   📄 Preview: {message[:200]}...")
        
        # Basic validation
        is_valid = generator._validate_message_quality(message, test_lead)
        print(f"   {'✅' if is_valid else '❌'} Message passes validation: {is_valid}")
        
    except Exception as e:
        print(f"   ⚠️  Full generation test failed (expected without OpenAI API): {e}")
    
    print("\n🎉 Enhanced Message Generator tests completed!")
    return True


if __name__ == '__main__':
    success = test_message_generator()
    sys.exit(0 if success else 1)