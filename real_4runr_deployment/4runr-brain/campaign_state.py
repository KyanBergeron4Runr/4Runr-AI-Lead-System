"""
Campaign State Data Models

Core data structures for the LangGraph Campaign Brain System.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


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
    """Central state object that flows through the LangGraph system"""
    
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
    is_low_context: bool = False
    
    # Data Quality Assessment
    data_quality: Dict[str, Any] = field(default_factory=dict)
    fallback_mode: bool = False
    
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
    delivery_method: str = ""  # "email_queue" or "linkedin_manual"
    queue_id: Optional[str] = None  # For email delivery
    airtable_update_status: Optional[str] = None  # For LinkedIn delivery
    formatted_linkedin_campaign: Optional[str] = None  # Formatted text for manual sending
    delivery_schedule: Optional[Dict[str, datetime]] = None
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        result['timestamp'] = self.timestamp.isoformat()
        if self.delivery_schedule:
            result['delivery_schedule'] = {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in self.delivery_schedule.items()
            }
        return result