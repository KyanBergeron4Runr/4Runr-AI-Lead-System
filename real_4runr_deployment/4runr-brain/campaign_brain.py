#!/usr/bin/env python3
"""
LangGraph Campaign Brain System

The intelligent "thinking layer" of the 4Runr Autonomous Outreach System.
Manages lead trait detection, campaign planning, message generation,
quality scoring, and queue injection through a connected graph of AI nodes.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END

# Import state models
from campaign_state import CampaignState, CampaignStatus, CampaignMessage

# Import nodes
try:
    from nodes.trait_detector import TraitDetectorNode
    from nodes.campaign_planner import CampaignPlannerNode
    from nodes.message_generator import MessageGeneratorNode
    from nodes.message_reviewer import MessageReviewerNode
    from nodes.quality_gatekeeper import QualityGatekeeperNode
    from nodes.injector import InjectorNode
    from nodes.memory_manager import MemoryManagerNode
except ImportError as e:
    print(f"Error importing nodes: {e}")
    print("Make sure you're running from the 4runr-brain directory")
    sys.exit(1)


class CampaignBrainConfig:
    """Configuration management for the campaign brain"""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment variables"""
        # Load .env file
        load_dotenv()
        # Quality thresholds
        self.quality_pass_threshold = float(os.getenv('CAMPAIGN_QUALITY_THRESHOLD', '80.0'))
        self.max_retries = int(os.getenv('CAMPAIGN_MAX_RETRIES', '2'))
        
        # API configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.openai_max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '500'))
        self.openai_temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        
        # Redis configuration for memory
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        
        # Logging configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.trace_logs_enabled = os.getenv('TRACE_LOGS_ENABLED', 'true').lower() == 'true'
        
        # Performance settings
        self.execution_timeout = int(os.getenv('EXECUTION_TIMEOUT', '300'))  # 5 minutes
        self.concurrent_limit = int(os.getenv('CONCURRENT_LIMIT', '10'))
    
    def validate(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        if not self.openai_api_key:
            issues.append("OPENAI_API_KEY is required")
        
        if self.quality_pass_threshold < 0 or self.quality_pass_threshold > 100:
            issues.append("CAMPAIGN_QUALITY_THRESHOLD must be between 0 and 100")
        
        if self.max_retries < 0 or self.max_retries > 5:
            issues.append("CAMPAIGN_MAX_RETRIES must be between 0 and 5")
        
        return issues


class CampaignBrainGraph:
    """Main LangGraph workflow for campaign brain processing"""
    
    def __init__(self, config: CampaignBrainConfig = None):
        self.config = config or CampaignBrainConfig()
        self.logger = self._setup_logging()
        self.graph = self._create_graph()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging"""
        logger = logging.getLogger('campaign_brain')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(CampaignState)
        
        # Initialize nodes
        trait_detector = TraitDetectorNode(self.config)
        memory_manager = MemoryManagerNode(self.config)
        campaign_planner = CampaignPlannerNode(self.config)
        message_generator = MessageGeneratorNode(self.config)
        message_reviewer = MessageReviewerNode(self.config)
        quality_gatekeeper = QualityGatekeeperNode(self.config)
        injector = InjectorNode(self.config)
        
        # Add nodes to graph
        workflow.add_node("trait_detector", trait_detector.execute)
        workflow.add_node("memory_manager", memory_manager.execute)
        workflow.add_node("campaign_planner", campaign_planner.execute)
        workflow.add_node("message_generator", message_generator.execute)
        workflow.add_node("message_reviewer", message_reviewer.execute)
        workflow.add_node("quality_gatekeeper", quality_gatekeeper.execute)
        workflow.add_node("injector", injector.execute)
        
        # Define linear workflow edges
        workflow.add_edge("trait_detector", "memory_manager")
        workflow.add_edge("memory_manager", "campaign_planner")
        workflow.add_edge("campaign_planner", "message_generator")
        workflow.add_edge("message_generator", "message_reviewer")
        workflow.add_edge("message_reviewer", "quality_gatekeeper")
        
        # Conditional edges for retry logic
        workflow.add_conditional_edges(
            "quality_gatekeeper",
            self._should_retry,
            {
                "retry": "message_generator",
                "approve": "injector",
                "manual_review": END
            }
        )
        
        workflow.add_edge("injector", END)
        workflow.set_entry_point("trait_detector")
        
        return workflow.compile()
    
    def _should_retry(self, state: CampaignState) -> str:
        """Determine next step based on quality gatekeeper decision"""
        if state.final_status == CampaignStatus.APPROVED:
            return "approve"
        elif state.final_status == CampaignStatus.RETRY and state.retry_count < self.config.max_retries:
            return "retry"
        else:
            return "manual_review"
    
    async def execute(self, lead_data: Dict[str, Any]) -> CampaignState:
        """Execute the campaign brain workflow for a single lead"""
        # Initialize state
        state = CampaignState(
            execution_id=f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{lead_data.get('id', 'unknown')}",
            lead_data=lead_data,
            company_data=lead_data.get('company_data', {}),
            scraped_content=lead_data.get('scraped_content', {})
        )
        
        self.logger.info(f"Starting campaign brain execution for lead: {lead_data.get('Name', 'Unknown')}")
        
        try:
            # Execute the graph
            result = await self.graph.ainvoke(state)
            
            # Handle the case where LangGraph returns a dict instead of CampaignState
            if isinstance(result, dict):
                # Copy the original state and update with result values
                final_state = state
                for key, value in result.items():
                    if hasattr(final_state, key):
                        setattr(final_state, key, value)
            else:
                final_state = result
            
            # Save trace log if enabled
            if self.config.trace_logs_enabled:
                await self._save_trace_log(final_state)
            
            self.logger.info(f"Campaign brain execution completed with status: {final_state.final_status.value}")
            return final_state
            
        except Exception as e:
            self.logger.error(f"Campaign brain execution failed: {str(e)}")
            state.add_error("graph_execution", e)
            state.final_status = CampaignStatus.ERROR
            state.status_reason = f"Graph execution failed: {str(e)}"
            return state
    
    async def _save_trace_log(self, state: CampaignState):
        """Save detailed trace log for analysis"""
        trace_dir = Path(__file__).parent / "trace_logs"
        trace_dir.mkdir(exist_ok=True)
        
        trace_file = trace_dir / f"{state.execution_id}.json"
        
        try:
            with open(trace_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2, default=str)
            
            self.logger.debug(f"Trace log saved: {trace_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save trace log: {str(e)}")


async def main():
    """Main entry point for testing"""
    # Example lead data
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
            "homepage_text": "Transform your business with cloud-native solutions...",
            "about_page": "Founded in 2018, CloudTech has been at the forefront of enterprise digital transformation..."
        }
    }
    
    # Initialize and run campaign brain
    config = CampaignBrainConfig()
    validation_issues = config.validate()
    
    if validation_issues:
        print("Configuration issues found:")
        for issue in validation_issues:
            print(f"  - {issue}")
        return
    
    brain = CampaignBrainGraph(config)
    result = await brain.execute(test_lead)
    
    print(f"\nCampaign Brain Results:")
    print(f"Status: {result.final_status.value}")
    print(f"Traits: {result.traits}")
    print(f"Campaign Sequence: {result.campaign_sequence}")
    print(f"Messages Generated: {len(result.messages)}")
    print(f"Overall Quality Score: {result.overall_quality_score}")
    print(f"Decision Path: {' → '.join(result.decision_path)}")


if __name__ == "__main__":
    asyncio.run(main())