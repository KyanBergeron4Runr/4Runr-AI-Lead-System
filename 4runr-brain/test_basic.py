#!/usr/bin/env python3
"""
Basic test to verify the Campaign Brain system works
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from campaign_brain import CampaignBrainGraph, CampaignBrainConfig


async def test_basic_functionality():
    """Test basic campaign brain functionality"""
    
    print("🧪 Testing Campaign Brain Basic Functionality")
    print("=" * 50)
    
    # Set up minimal config for testing
    os.environ['OPENAI_API_KEY'] = 'test-key-for-validation'
    
    try:
        # Initialize config
        config = CampaignBrainConfig()
        print("✅ Configuration initialized")
        
        # Create test lead data
        test_lead = {
            "id": "test_001",
            "Name": "Sarah Johnson",
            "Title": "VP of Product",
            "Company": "CloudTech Solutions",
            "Email": "sarah.johnson@cloudtech.com",
            "company_data": {
                "description": "CloudTech provides SaaS solutions for enterprise workflow management",
                "services": "Software as a Service, API integrations, Cloud platforms",
                "tone": "Professional"
            },
            "scraped_content": {
                "homepage_text": "Transform your business with cloud-native solutions that scale with your growth.",
                "about_page": "Founded in 2018, CloudTech has been at the forefront of enterprise digital transformation."
            }
        }
        print("✅ Test lead data created")
        
        # Initialize campaign brain (this will test node imports)
        brain = CampaignBrainGraph(config)
        print("✅ Campaign brain initialized")
        print("✅ All nodes imported successfully")
        
        # Test individual node initialization
        from nodes.trait_detector import TraitDetectorNode
        from nodes.campaign_planner import CampaignPlannerNode
        from nodes.memory_manager import MemoryManagerNode
        
        trait_detector = TraitDetectorNode(config)
        campaign_planner = CampaignPlannerNode(config)
        memory_manager = MemoryManagerNode(config)
        
        print("✅ Individual nodes can be instantiated")
        
        print("\n🎉 Basic functionality test PASSED!")
        print("\nNext steps:")
        print("1. Set your OPENAI_API_KEY environment variable")
        print("2. Run: python run_campaign_brain.py --create-sample sample_lead.json")
        print("3. Run: python run_campaign_brain.py --lead sample_lead.json --verbose")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    sys.exit(0 if success else 1)