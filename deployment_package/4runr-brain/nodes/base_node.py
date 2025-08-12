"""
Base Node Class

Abstract base class for all campaign brain nodes with common functionality
for logging, error handling, and performance tracking.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Import after path setup to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from campaign_state import CampaignState
    from campaign_brain import CampaignBrainConfig


class CampaignNodeError(Exception):
    """Base exception for campaign node errors"""
    pass


class RetryableError(CampaignNodeError):
    """Error that can be retried"""
    pass


class FatalError(CampaignNodeError):
    """Error that should not be retried"""
    pass


class CampaignNode(ABC):
    """Abstract base class for all campaign brain nodes"""
    
    def __init__(self, config):
        self.config = config
        self.node_name = self.__class__.__name__.replace('Node', '').lower()
        self.logger = self._setup_logging()
        self.execution_count = 0
        self.total_execution_time = 0.0
    
    def _setup_logging(self) -> logging.Logger:
        """Set up node-specific logging"""
        logger = logging.getLogger(f'campaign_brain.{self.node_name}')
        logger.setLevel(getattr(logging, self.config.log_level))
        return logger
    
    async def execute(self, state) -> 'CampaignState':
        """Execute node logic with error handling and performance tracking"""
        start_time = time.time()
        self.execution_count += 1
        
        # Track node execution
        state.add_node_to_path(self.node_name)
        
        self.logger.info(f"Executing {self.node_name} for lead: {state.lead_data.get('Name', 'Unknown')}")
        
        try:
            # Validate input
            if not self.validate_input(state):
                raise FatalError(f"Input validation failed for {self.node_name}")
            
            # Execute node-specific logic
            result_state = await self._execute_node_logic(state)
            
            # Track execution time
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            self.logger.info(f"{self.node_name} completed in {execution_time:.2f}s")
            
            return result_state
            
        except Exception as error:
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            self.logger.error(f"{self.node_name} failed after {execution_time:.2f}s: {str(error)}")
            
            # Handle error and update state
            return self.handle_error(error, state)
    
    @abstractmethod
    async def _execute_node_logic(self, state) -> 'CampaignState':
        """Execute the core node logic - must be implemented by subclasses"""
        pass
    
    def validate_input(self, state) -> bool:
        """Validate required input data - can be overridden by subclasses"""
        # Basic validation - ensure we have lead data
        if not state.lead_data:
            self.logger.error("No lead data provided")
            return False
        
        return True
    
    def handle_error(self, error: Exception, state) -> 'CampaignState':
        """Handle node-specific errors"""
        # Add error to state
        state.add_error(self.node_name, error, {
            'execution_count': self.execution_count,
            'node_path': state.node_path
        })
        
        # Determine if error is retryable
        if isinstance(error, RetryableError):
            self.logger.warning(f"Retryable error in {self.node_name}: {str(error)}")
            state.warnings.append(f"{self.node_name}: {str(error)}")
        else:
            self.logger.error(f"Fatal error in {self.node_name}: {str(error)}")
            from campaign_brain import CampaignStatus
            state.final_status = CampaignStatus.ERROR
            state.status_reason = f"{self.node_name} failed: {str(error)}"
        
        return state
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this node"""
        avg_execution_time = (
            self.total_execution_time / self.execution_count 
            if self.execution_count > 0 else 0
        )
        
        return {
            'node_name': self.node_name,
            'execution_count': self.execution_count,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': avg_execution_time
        }
    
    def log_decision(self, state, decision: str, reasoning: str = ""):
        """Log a decision made by this node"""
        decision_text = f"{self.node_name}: {decision}"
        if reasoning:
            decision_text += f" ({reasoning})"
        
        state.add_decision(decision_text, reasoning)
        self.logger.info(f"Decision: {decision_text}")
    
    def extract_company_keywords(self, company_data: Dict[str, Any]) -> List[str]:
        """Extract keywords from company data for analysis"""
        keywords = []
        
        # Extract from description
        description = company_data.get('description', '').lower()
        if description:
            keywords.extend(description.split())
        
        # Extract from services
        services = company_data.get('services', '').lower()
        if services:
            keywords.extend(services.split())
        
        # Clean and deduplicate
        keywords = [
            word.strip('.,!?;:()[]{}"\'-') 
            for word in keywords 
            if len(word) > 2
        ]
        
        return list(set(keywords))
    
    def calculate_confidence_score(self, matches: List[str], total_indicators: List[str]) -> float:
        """Calculate confidence score based on matches"""
        if not total_indicators:
            return 0.0
        
        match_count = len(matches)
        total_count = len(total_indicators)
        
        # Base confidence from match ratio
        base_confidence = (match_count / total_count) * 100
        
        # Boost confidence for multiple matches
        if match_count >= 3:
            base_confidence = min(95.0, base_confidence * 1.2)
        elif match_count >= 2:
            base_confidence = min(90.0, base_confidence * 1.1)
        
        return round(base_confidence, 1)