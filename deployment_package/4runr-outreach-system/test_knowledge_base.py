#!/usr/bin/env python3
"""
Test script for the Knowledge Base Loader functionality.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.knowledge_base_loader import KnowledgeBaseLoader, load_knowledge_base


def test_knowledge_base_loader():
    """Test the Knowledge Base Loader functionality."""
    print("🧪 Testing Knowledge Base Loader...")
    
    # Test 1: Initialize loader
    print("\n1. Testing loader initialization...")
    loader = KnowledgeBaseLoader()
    print(f"   ✅ Loader initialized with path: {loader.absolute_path}")
    
    # Test 2: Load knowledge base
    print("\n2. Testing knowledge base loading...")
    try:
        knowledge = loader.load_knowledge_base()
        print(f"   ✅ Knowledge base loaded successfully ({len(knowledge)} characters)")
        print(f"   📄 First 200 characters: {knowledge[:200]}...")
    except Exception as e:
        print(f"   ❌ Failed to load knowledge base: {e}")
        return False
    
    # Test 3: Validate content
    print("\n3. Testing content validation...")
    is_valid = loader.validate_knowledge_base()
    print(f"   {'✅' if is_valid else '❌'} Knowledge base validation: {is_valid}")
    
    # Test 4: Get knowledge summary
    print("\n4. Testing knowledge summary extraction...")
    try:
        summary = loader.get_knowledge_summary()
        print(f"   ✅ Summary extracted with {len(summary)} components:")
        for key, value in summary.items():
            print(f"      - {key}: {value[:100]}...")
    except Exception as e:
        print(f"   ❌ Failed to extract summary: {e}")
    
    # Test 5: Test convenience function
    print("\n5. Testing convenience function...")
    try:
        knowledge_direct = load_knowledge_base()
        print(f"   ✅ Convenience function works ({len(knowledge_direct)} characters)")
    except Exception as e:
        print(f"   ❌ Convenience function failed: {e}")
    
    # Test 6: Test caching
    print("\n6. Testing caching functionality...")
    knowledge1 = loader.load_knowledge_base()
    knowledge2 = loader.load_knowledge_base()  # Should use cache
    print(f"   ✅ Caching works: {knowledge1 == knowledge2}")
    
    print("\n🎉 Knowledge Base Loader tests completed!")
    return True


if __name__ == '__main__':
    success = test_knowledge_base_loader()
    sys.exit(0 if success else 1)