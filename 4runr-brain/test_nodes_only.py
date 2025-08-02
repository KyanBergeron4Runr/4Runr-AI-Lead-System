#!/usr/bin/env python3
"""
Test individual nodes without LangGraph dependencies
"""

import asyncio
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
from enum import Enum

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

class CampaignStatus(Enum):
    """Campaign execution status"""
    PROCESSING = "processing"
    APPROVED = "approved"
    RETRY = "retry"
    MANUAL_REVIEW = "manual_review"
    STALLED = "stalled"
    ERROR = "error"

@dataclass
class CampaignMessage:
    """Individual message within a campaign"""
    message_type: str  # hook, proof, fomo
    subject: str = ""
    body: str = ""
    generation_attempt: int = 1
    quality_score: float = 0.0
    quality_issues: List[str] = field(default_factory=list)
    personalization_elements: Dict[str, bool] = field(default_factory=dict)
    strategic_elements: List[str] = field(default_factory=list)
    tone_indicators: List[str] = field(default_factory=list)
    word_count: int = 0
    readability_score: float = 0.0
    brand_compliance_score: float = 0.0

@dataclass
class CampaignState:
    """Central state object that flows through the system"""
    
    # Execution Metadata
    execution_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    node_path: List[str] = field(default_factory=list)
    
    # Lead Information
    lead_data: Dict[str, Any] = field(default_factory=dict)
    company_data: Dict[str, Any] = field(default_factory=dict)
    scraped_content: Dict[str, Any] = field(default_factory=dict)
    
    # Trait Detection Results
    traits: List[str] = field(default_factory=list)
    trait_confidence: Dict[str, float] = field(default_factory=dict)
    trait_reasoning: Dict[str, str] = field(default_factory=dict)
    primary_trait: str = ""
    
    # Campaign Planning Results
    campaign_sequence: List[str] = field(default_factory=list)
    messaging_angle: str = ""
    campaign_tone: str = ""
    sequence_reasoning: str = ""
    
    # Message Generation Results
    messages: List[CampaignMessage] = field(default_factory=list)
    generation_attempts: Dict[str, int] = field(default_factory=dict)
    generation_errors: List[str] = field(default_factory=list)
    
    # Quality Assessment Results
    quality_scores: Dict[str, float] = field(default_factory=dict)
    quality_issues: List[str] = field(default_factory=list)
    quality_feedback: Dict[str, List[str]] = field(default_factory=dict)
    overall_quality_score: float = 0.0
    
    # Decision Tracking
    decision_path: List[str] = field(default_factory=list)
    retry_count: int = 0
    final_status: CampaignStatus = CampaignStatus.PROCESSING
    status_reason: str = ""
    
    # Memory and Context
    memory_context: Dict[str, Any] = field(default_factory=dict)
    historical_insights: List[str] = field(default_factory=list)
    
    # Execution Results
    injection_status: str = ""
    queue_id: str = None
    delivery_schedule: Dict[str, datetime] = None
    
    # Error Handling
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_node_to_path(self, node_name: str):
        """Track node execution path"""
        self.node_path.append(f"{node_name}_{datetime.now().isoformat()}")
    
    def add_error(self, node_name: str, error: Exception, context: Dict[str, Any] = None):
        """Add error with context"""
        error_info = {
            'node': node_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        self.errors.append(error_info)
    
    def add_decision(self, decision: str, reasoning: str = ""):
        """Track decision points"""
        decision_entry = f"{decision}"
        if reasoning:
            decision_entry += f": {reasoning}"
        self.decision_path.append(decision_entry)

class MockConfig:
    """Mock configuration for testing"""
    def __init__(self):
        self.quality_pass_threshold = 80.0
        self.max_retries = 2
        self.log_level = 'INFO'

async def test_trait_detector():
    """Test trait detector node"""
    print("\n🔍 Testing TraitDetectorNode...")
    
    try:
        from nodes.trait_detector import TraitDetectorNode
        
        config = MockConfig()
        node = TraitDetectorNode(config)
        
        # Create test state
        state = CampaignState(
            execution_id="test_001",
            lead_data={
                "Name": "Sarah Johnson",
                "Title": "VP of Product",
                "Company": "CloudTech Solutions"
            },
            company_data={
                "description": "CloudTech provides SaaS solutions for enterprise workflow management",
                "services": "Software as a Service, API integrations, Cloud platforms"
            },
            scraped_content={
                "homepage_text": "Transform your business with cloud-native solutions"
            }
        )
        
        # Execute node
        result = await node._execute_node_logic(state)
        
        print(f"  ✅ Detected {len(result.traits)} traits: {result.traits}")
        print(f"  ✅ Primary trait: {result.primary_trait}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ TraitDetector test failed: {str(e)}")
        return False

async def test_campaign_planner():
    """Test campaign planner node"""
    print("\n📋 Testing CampaignPlannerNode...")
    
    try:
        from nodes.campaign_planner import CampaignPlannerNode
        
        config = MockConfig()
        node = CampaignPlannerNode(config)
        
        # Create test state with traits
        state = CampaignState(
            execution_id="test_002",
            traits=["enterprise", "saas", "role_vp"],
            trait_confidence={"enterprise": 85.0, "saas": 78.0, "role_vp": 90.0},
            company_data={"tone": "Professional"}
        )
        
        # Execute node
        result = await node._execute_node_logic(state)
        
        print(f"  ✅ Messaging angle: {result.messaging_angle}")
        print(f"  ✅ Campaign tone: {result.campaign_tone}")
        print(f"  ✅ Sequence: {result.campaign_sequence}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ CampaignPlanner test failed: {str(e)}")
        return False

async def test_memory_manager():
    """Test memory manager node"""
    print("\n🧠 Testing MemoryManagerNode...")
    
    try:
        from nodes.memory_manager import MemoryManagerNode
        
        config = MockConfig()
        node = MemoryManagerNode(config)
        
        # Create test state
        state = CampaignState(
            execution_id="test_003",
            lead_data={
                "Name": "Sarah Johnson",
                "Email": "sarah@cloudtech.com",
                "Company": "CloudTech"
            },
            traits=["enterprise", "saas"],
            messaging_angle="competitive_advantage",
            overall_quality_score=85.0,
            final_status=CampaignStatus.APPROVED
        )
        
        # Execute node
        result = await node._execute_node_logic(state)
        
        print(f"  ✅ Memory context loaded: {len(result.memory_context)} items")
        print(f"  ✅ Historical insights: {len(result.historical_insights)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MemoryManager test failed: {str(e)}")
        return False

async def main():
    """Run all node tests"""
    print("🧪 Testing Campaign Brain Nodes")
    print("=" * 40)
    
    tests = [
        test_trait_detector,
        test_campaign_planner,
        test_memory_manager
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All node tests PASSED!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set OPENAI_API_KEY environment variable")
        print("3. Run full system test: python run_campaign_brain.py --create-sample sample.json")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)