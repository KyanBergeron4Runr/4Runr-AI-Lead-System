#!/usr/bin/env python3
"""
Test script for the Enhanced Engager Agent.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.enhanced_engager_agent import EnhancedEngagerAgent


def test_enhanced_agent():
    """Test the Enhanced Engager Agent functionality."""
    print("🧪 Testing Enhanced Engager Agent...")
    
    # Test 1: Initialize enhanced agent
    print("\n1. Testing enhanced agent initialization...")
    try:
        agent = EnhancedEngagerAgent()
        print("   ✅ Enhanced agent initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize enhanced agent: {e}")
        return False
    
    # Test 2: Health check
    print("\n2. Testing health check...")
    try:
        health = agent.health_check()
        print(f"   🏥 Overall health: {health['overall_status']}")
        print(f"   📊 Components checked: {len(health.get('components', {}))}")
        
        for component, status in health.get('components', {}).items():
            status_icon = "✅" if status == 'healthy' else "⚠️" if status == 'degraded' else "❌"
            print(f"      {status_icon} {component}: {status}")
            
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
    
    # Test 3: Enhanced processing stats
    print("\n3. Testing enhanced processing statistics...")
    try:
        stats = agent.get_enhanced_processing_stats()
        print(f"   📈 Statistics retrieved successfully")
        
        if 'enhanced_components_status' in stats:
            print(f"   🔧 Component status:")
            for component, status in stats['enhanced_components_status'].items():
                status_icon = "✅" if status == 'operational' else "⚠️"
                print(f"      {status_icon} {component}: {status}")
        
        if 'knowledge_base_valid' in stats:
            kb_status = "✅" if stats['knowledge_base_valid'] else "❌"
            print(f"   📚 Knowledge base: {kb_status} {stats['knowledge_base_valid']}")
            
    except Exception as e:
        print(f"   ❌ Enhanced stats failed: {e}")
    
    # Test 4: Test company summary generation
    print("\n4. Testing company summary generation...")
    try:
        summary = agent._get_company_summary("https://example.com", "Test Company")
        print(f"   📄 Company summary: {summary[:100]}...")
        
        # Test with no website
        summary_no_site = agent._get_company_summary("", "Test Company")
        print(f"   📄 No website summary: {summary_no_site[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Company summary test failed: {e}")
    
    # Test 5: Test enhanced validation
    print("\n5. Testing enhanced lead validation...")
    try:
        test_leads = [
            {'Level Engaged': 'retry', 'Email': 'test@example.com', 'Email_Confidence_Level': 'Real', 'Engagement_Status': 'Auto-Send'},
            {'Level Engaged': '1st degree', 'Email': 'test@example.com', 'Email_Confidence_Level': 'Real', 'Engagement_Status': 'Auto-Send'},
            {'Level Engaged': '', 'Email': 'test@example.com', 'Email_Confidence_Level': 'Real', 'Engagement_Status': 'Auto-Send'}
        ]
        
        for i, lead in enumerate(test_leads):
            should_engage = agent._should_engage_lead_enhanced(lead)
            level = agent.engagement_tracker.get_current_engagement_level(lead)
            print(f"   📋 Lead {i+1} (level: {level}): {'✅ engage' if should_engage else '⏭️ skip'}")
            
    except Exception as e:
        print(f"   ❌ Enhanced validation test failed: {e}")
    
    print("\n🎉 Enhanced Engager Agent tests completed!")
    return True


if __name__ == '__main__':
    success = test_enhanced_agent()
    sys.exit(0 if success else 1)