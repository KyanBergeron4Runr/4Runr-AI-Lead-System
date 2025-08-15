"""
Campaign Analytics data model for performance tracking
"""

from datetime import date, datetime
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class CampaignAnalytics:
    """Campaign performance analytics data"""
    analytics_id: str
    campaign_id: str
    date: date
    
    # Message Performance
    hook_opens: int = 0
    hook_clicks: int = 0
    hook_sent: bool = False
    proof_opens: int = 0
    proof_clicks: int = 0
    proof_sent: bool = False
    fomo_opens: int = 0
    fomo_clicks: int = 0
    fomo_sent: bool = False
    
    # Campaign Outcomes
    responded: bool = False
    response_message: Optional[int] = None  # Which message got response (1-3)
    response_time_hours: Optional[int] = None  # Hours from first message to response
    campaign_completed: bool = False
    
    # Segmentation Data
    industry: Optional[str] = None
    company_size: Optional[str] = None
    lead_role: Optional[str] = None
    email_confidence: Optional[str] = None
    
    # Performance Metrics
    engagement_rate: float = 0.0  # Overall engagement percentage
    conversion_rate: float = 0.0  # Response rate
    progression_rate: float = 0.0  # Percentage who engaged with multiple messages
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def calculate_engagement_rate(self) -> float:
        """Calculate overall engagement rate"""
        total_sent = sum([self.hook_sent, self.proof_sent, self.fomo_sent])
        if total_sent == 0:
            return 0.0
        
        total_opens = self.hook_opens + self.proof_opens + self.fomo_opens
        self.engagement_rate = total_opens / total_sent
        return self.engagement_rate
    
    def calculate_conversion_rate(self) -> float:
        """Calculate conversion rate (response rate)"""
        self.conversion_rate = 1.0 if self.responded else 0.0
        return self.conversion_rate
    
    def calculate_progression_rate(self) -> float:
        """Calculate progression rate (engagement with multiple messages)"""
        messages_with_engagement = 0
        if self.hook_opens > 0 or self.hook_clicks > 0:
            messages_with_engagement += 1
        if self.proof_opens > 0 or self.proof_clicks > 0:
            messages_with_engagement += 1
        if self.fomo_opens > 0 or self.fomo_clicks > 0:
            messages_with_engagement += 1
        
        total_sent = sum([self.hook_sent, self.proof_sent, self.fomo_sent])
        if total_sent <= 1:
            self.progression_rate = 0.0
        else:
            self.progression_rate = messages_with_engagement / total_sent
        
        return self.progression_rate
    
    def update_metrics(self) -> None:
        """Update all calculated metrics"""
        self.calculate_engagement_rate()
        self.calculate_conversion_rate()
        self.calculate_progression_rate()
        self.updated_at = datetime.now()
    
    def get_total_opens(self) -> int:
        """Get total opens across all messages"""
        return self.hook_opens + self.proof_opens + self.fomo_opens
    
    def get_total_clicks(self) -> int:
        """Get total clicks across all messages"""
        return self.hook_clicks + self.proof_clicks + self.fomo_clicks
    
    def get_total_sent(self) -> int:
        """Get total messages sent"""
        return sum([self.hook_sent, self.proof_sent, self.fomo_sent])
    
    def to_dict(self) -> Dict:
        """Convert analytics to dictionary for storage"""
        return {
            'analytics_id': self.analytics_id,
            'campaign_id': self.campaign_id,
            'date': self.date.isoformat(),
            'hook_opens': self.hook_opens,
            'hook_clicks': self.hook_clicks,
            'hook_sent': self.hook_sent,
            'proof_opens': self.proof_opens,
            'proof_clicks': self.proof_clicks,
            'proof_sent': self.proof_sent,
            'fomo_opens': self.fomo_opens,
            'fomo_clicks': self.fomo_clicks,
            'fomo_sent': self.fomo_sent,
            'responded': self.responded,
            'response_message': self.response_message,
            'response_time_hours': self.response_time_hours,
            'campaign_completed': self.campaign_completed,
            'industry': self.industry,
            'company_size': self.company_size,
            'lead_role': self.lead_role,
            'email_confidence': self.email_confidence,
            'engagement_rate': self.engagement_rate,
            'conversion_rate': self.conversion_rate,
            'progression_rate': self.progression_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CampaignAnalytics':
        """Create analytics from dictionary"""
        return cls(
            analytics_id=data['analytics_id'],
            campaign_id=data['campaign_id'],
            date=date.fromisoformat(data['date']),
            hook_opens=data.get('hook_opens', 0),
            hook_clicks=data.get('hook_clicks', 0),
            hook_sent=data.get('hook_sent', False),
            proof_opens=data.get('proof_opens', 0),
            proof_clicks=data.get('proof_clicks', 0),
            proof_sent=data.get('proof_sent', False),
            fomo_opens=data.get('fomo_opens', 0),
            fomo_clicks=data.get('fomo_clicks', 0),
            fomo_sent=data.get('fomo_sent', False),
            responded=data.get('responded', False),
            response_message=data.get('response_message'),
            response_time_hours=data.get('response_time_hours'),
            campaign_completed=data.get('campaign_completed', False),
            industry=data.get('industry'),
            company_size=data.get('company_size'),
            lead_role=data.get('lead_role'),
            email_confidence=data.get('email_confidence'),
            engagement_rate=data.get('engagement_rate', 0.0),
            conversion_rate=data.get('conversion_rate', 0.0),
            progression_rate=data.get('progression_rate', 0.0),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )