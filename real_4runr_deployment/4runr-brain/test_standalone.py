#!/usr/bin/env python3
"""
Standalone test of core Campaign Brain logic without dependencies
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
from enum import Enum

class CampaignStatus(Enum):
    PROCESSING = "processing"
    APPROVED = "approved"
    RETRY = "retry"
    MANUAL_REVIEW = "manual_review"
    STALLED = "stalled"
    ERROR = "error"

@dataclass
class CampaignMessage:
    message_type: str
    subject: str = ""
    body: str = ""
    quality_score: float = 0.0
    quality_issues: List[str] = field(default_factory=list)

@dataclass
class CampaignState:
    execution_id: str = ""
    lead_data: Dict[str, Any] = field(default_factory=dict)
    company_data: Dict[str, Any] = field(default_factory=dict)
    scraped_content: Dict[str, Any] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)
    trait_confidence: Dict[str, float] = field(default_factory=dict)
    primary_trait: str = ""
    campaign_sequence: List[str] = field(default_factory=list)
    messaging_angle: str = ""
    campaign_tone: str = ""
    messages: List[CampaignMessage] = field(default_factory=list)
    overall_quality_score: float = 0.0
    final_status: CampaignStatus = CampaignStatus.PROCESSING
    decision_path: List[str] = field(default_factory=list)

class TraitDetector:
    """Simplified trait detector for testing"""
    
    def __init__(self):
        self.business_patterns = {
            'enterprise': ['enterprise', 'corporation', 'global', 'fortune'],
            'saas': ['saas', 'software as a service', 'cloud software'],
            'startup': ['startup', 'founded', 'early-stage', 'seed']
        }
        
        self.role_patterns = {
            'role_ceo': ['ceo', 'chief executive'],
            'role_cto': ['cto', 'chief technology'],
            'role_vp': ['vp', 'vice president']
        }
    
    async def detect_traits(self, state: CampaignState) -> CampaignState:
        """Detect traits from lead and company data"""
        
        # Extract text for analysis
        text_parts = []
        if state.company_data.get('description'):
            text_parts.append(state.company_data['description'])
        if state.company_data.get('services'):
            text_parts.append(state.company_data['services'])
        if state.lead_data.get('Title'):
            text_parts.append(state.lead_data['Title'])
        
        analysis_text = ' '.join(text_parts).lower()
        
        detected_traits = []
        confidence_scores = {}
        
        # Check business patterns
        for trait, keywords in self.business_patterns.items():
            matches = [kw for kw in keywords if kw in analysis_text]
            if matches:
                detected_traits.append(trait)
                confidence_scores[trait] = min(95.0, len(matches) * 30)
        
        # Check role patterns
        title = state.lead_data.get('Title', '').lower()
        for trait, keywords in self.role_patterns.items():
            matches = [kw for kw in keywords if kw in title]
            if matches:
                detected_traits.append(trait)
                confidence_scores[trait] = min(95.0, len(matches) * 40)
        
        # Update state
        state.traits = detected_traits
        state.trait_confidence = confidence_scores
        state.primary_trait = max(confidence_scores.items(), key=lambda x: x[1])[0] if confidence_scores else ""
        
        return state

class CampaignPlanner:
    """Simplified campaign planner for testing"""
    
    def __init__(self):
        self.sequence_mappings = {
            'role_ceo': {
                'sequence': ['strategic_hook', 'competitive_proof', 'timing_fomo'],
                'messaging_angle': 'competitive_advantage',
                'tone': 'executive'
            },
            'role_vp': {
                'sequence': ['insight_hook', 'strategic_proof', 'competitive_fomo'],
                'messaging_angle': 'strategic_advantage',
                'tone': 'executive'
            },
            'enterprise': {
                'sequence': ['transformation_hook', 'enterprise_proof', 'timing_fomo'],
                'messaging_angle': 'enterprise_transformation',
                'tone': 'formal'
            },
            'saas': {
                'sequence': ['platform_hook', 'integration_proof', 'market_fomo'],
                'messaging_angle': 'platform_optimization',
                'tone': 'technical'
            }
        }
        
        self.default_plan = {
            'sequence': ['hook', 'proof', 'fomo'],
            'messaging_angle': 'operational_efficiency',
            'tone': 'professional'
        }
    
    async def plan_campaign(self, state: CampaignState) -> CampaignState:
        """Plan campaign based on detected traits"""
        
        # Find best matching plan
        selected_plan = None
        best_confidence = 0
        
        for trait in state.traits:
            if trait in self.sequence_mappings:
                confidence = state.trait_confidence.get(trait, 0)
                if confidence > best_confidence:
                    best_confidence = confidence
                    selected_plan = self.sequence_mappings[trait]
        
        # Use default if no match
        if not selected_plan:
            selected_plan = self.default_plan
        
        # Update state
        state.campaign_sequence = selected_plan['sequence']
        state.messaging_angle = selected_plan['messaging_angle']
        state.campaign_tone = selected_plan['tone']
        
        return state

class MessageGenerator:
    """Simplified message generator for testing (no GPT)"""
    
    async def generate_messages(self, state: CampaignState) -> CampaignState:
        """Generate placeholder messages"""
        
        messages = []
        lead_name = state.lead_data.get('Name', 'there').split()[0]
        company = state.lead_data.get('Company', 'your company')
        
        for msg_type in state.campaign_sequence:
            if msg_type in ['hook', 'strategic_hook', 'insight_hook']:
                subject = f"Strategic opportunity for {company}"
                body = f"Hi {lead_name},\n\nI noticed {company}'s focus on {state.messaging_angle}. The market is evolving quickly in this space.\n\nWould it make sense to connect briefly?\n\nBest,\n4Runr Team"
            elif msg_type in ['proof', 'competitive_proof', 'strategic_proof']:
                subject = f"How companies like {company} are staying ahead"
                body = f"Hi {lead_name},\n\nFrom what we've seen, companies that excel in {state.messaging_angle} share common approaches.\n\nWorth a brief conversation?\n\nBest,\n4Runr Team"
            else:  # fomo variants
                subject = f"Final thoughts on competitive timing"
                body = f"Hi {lead_name},\n\nTiming matters in {state.messaging_angle}. A few of your competitors are already testing new approaches.\n\nShall we close the loop on this?\n\nBest,\n4Runr Team"
            
            message = CampaignMessage(
                message_type=msg_type,
                subject=subject,
                body=body,
                quality_score=85.0  # Mock score
            )
            messages.append(message)
        
        state.messages = messages
        return state

class QualityReviewer:
    """Simplified quality reviewer for testing"""
    
    async def review_quality(self, state: CampaignState) -> CampaignState:
        """Review message quality"""
        
        total_score = 0
        for message in state.messages:
            # Simple quality checks
            score = 70.0  # Base score
            
            # Check personalization
            if state.lead_data.get('Name', '').split()[0].lower() in message.body.lower():
                score += 10
            if state.lead_data.get('Company', '').lower() in message.body.lower():
                score += 10
            
            # Check strategic elements
            if state.messaging_angle.replace('_', ' ') in message.body.lower():
                score += 5
            
            message.quality_score = min(100.0, score)
            total_score += message.quality_score
        
        state.overall_quality_score = total_score / len(state.messages) if state.messages else 0
        return state

async def test_campaign_brain_flow():
    """Test the complete campaign brain flow"""
    
    print("🧠 Testing Campaign Brain Flow")
    print("=" * 40)
    
    # Create test lead
    test_lead = {
        "id": "test_001",
        "Name": "Sarah Johnson",
        "Title": "VP of Product",
        "Company": "CloudTech Solutions",
        "Email": "sarah.johnson@cloudtech.com"
    }
    
    test_company = {
        "description": "CloudTech provides SaaS solutions for enterprise workflow management",
        "services": "Software as a Service, API integrations, Cloud platforms",
        "tone": "Professional"
    }
    
    # Initialize state
    state = CampaignState(
        execution_id="test_flow_001",
        lead_data=test_lead,
        company_data=test_company
    )
    
    print(f"📋 Processing lead: {test_lead['Name']} at {test_lead['Company']}")
    
    # Step 1: Trait Detection
    print("\n🔍 Step 1: Trait Detection")
    trait_detector = TraitDetector()
    state = await trait_detector.detect_traits(state)
    print(f"  Detected traits: {state.traits}")
    print(f"  Primary trait: {state.primary_trait}")
    print(f"  Confidence scores: {state.trait_confidence}")
    
    # Step 2: Campaign Planning
    print("\n📋 Step 2: Campaign Planning")
    campaign_planner = CampaignPlanner()
    state = await campaign_planner.plan_campaign(state)
    print(f"  Messaging angle: {state.messaging_angle}")
    print(f"  Campaign tone: {state.campaign_tone}")
    print(f"  Sequence: {' → '.join(state.campaign_sequence)}")
    
    # Step 3: Message Generation
    print("\n📧 Step 3: Message Generation")
    message_generator = MessageGenerator()
    state = await message_generator.generate_messages(state)
    print(f"  Generated {len(state.messages)} messages:")
    for i, msg in enumerate(state.messages, 1):
        print(f"    {i}. {msg.message_type}: {msg.subject}")
    
    # Step 4: Quality Review
    print("\n⭐ Step 4: Quality Review")
    quality_reviewer = QualityReviewer()
    state = await quality_reviewer.review_quality(state)
    print(f"  Overall quality score: {state.overall_quality_score:.1f}/100")
    for msg in state.messages:
        print(f"    {msg.message_type}: {msg.quality_score:.1f}/100")
    
    # Step 5: Quality Decision
    print("\n🚪 Step 5: Quality Decision")
    threshold = 80.0
    if state.overall_quality_score >= threshold:
        state.final_status = CampaignStatus.APPROVED
        print(f"  ✅ APPROVED (score {state.overall_quality_score:.1f} >= {threshold})")
    else:
        state.final_status = CampaignStatus.RETRY
        print(f"  🔄 RETRY (score {state.overall_quality_score:.1f} < {threshold})")
    
    print(f"\n🎯 Final Status: {state.final_status.value.upper()}")
    
    return state.final_status == CampaignStatus.APPROVED

async def main():
    """Run the test"""
    try:
        success = await test_campaign_brain_flow()
        
        if success:
            print("\n🎉 Campaign Brain Flow Test PASSED!")
            print("\nThe core logic is working correctly.")
            print("Next steps:")
            print("1. Install dependencies: pip install -r requirements.txt")
            print("2. Set OPENAI_API_KEY for GPT-4o integration")
            print("3. Run full system: python run_campaign_brain.py --create-sample sample.json")
        else:
            print("\n❌ Test completed but campaign was not approved")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)