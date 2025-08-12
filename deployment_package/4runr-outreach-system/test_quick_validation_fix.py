#!/usr/bin/env python3
"""
Quick validation test to verify the corporation fix.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import DataCleaner

def test_corporation_fix():
    """Test that Microsoft Corporation is now accepted."""
    print("🔧 Testing Corporation Fix")
    print("=" * 40)
    
    data_cleaner = DataCleaner()
    
    # Test cases that were failing
    test_cases = [
        {
            'name': 'Microsoft Corporation',
            'data': {'Company': 'Microsoft Corporation', 'Website': 'https://microsoft.com'},
            'should_pass': True
        },
        {
            'name': 'Johnson & Johnson Inc',
            'data': {'Company': 'Johnson & Johnson Inc', 'Website': 'https://jnj.com'},
            'should_pass': True
        },
        {
            'name': 'Apple Inc',
            'data': {'Company': 'Apple Inc', 'Website': 'https://apple.com'},
            'should_pass': True
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\\n🧪 Test {i}: {test['name']}")
        
        context = {'id': f'test_{i}', 'Full Name': 'Test User', 'source': 'validation_fix'}
        result = data_cleaner.clean_and_validate(test['data'], context)
        
        print(f"   Success: {result.success}")
        print(f"   Cleaned Data: {result.cleaned_data}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        
        if result.success == test['should_pass']:
            print(f"   ✅ PASS")
            passed += 1
        else:
            print(f"   ❌ FAIL")
            if result.rejection_reasons:
                print(f"   Rejection: {result.rejection_reasons}")
    
    print(f"\\n📊 Results: {passed}/{total} passed ({passed/total:.1%})")
    
    if passed == total:
        print("\\n✅ CORPORATION FIX SUCCESSFUL!")
        print("🚀 System may be ready for deployment")
        return True
    else:
        print("\\n❌ Corporation fix incomplete")
        return False

if __name__ == '__main__':
    success = test_corporation_fix()
    sys.exit(0 if success else 1)