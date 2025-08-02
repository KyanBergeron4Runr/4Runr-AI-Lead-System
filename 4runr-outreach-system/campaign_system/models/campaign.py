"""
Campaign data model for multi-step email campaigns
"""

from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class CampaignStatus(Enum):
    """Campaign status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    RESPONDED = "responded"


class MessageType(Enum):
    """Message type enumeration for campaign progression"""
    HOOK = "hook"
    PROOF = "proof"
    FOMO = "fomo"


class MessageStatus(Enum):
    """Individual message status enumeration"""
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class ResponseType(Enum):
    """Response type categorization"""
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    AUTO_REPLY = "auto_reply"
    OUT_OF_OFFICE = "out_of_office"


@dataclass
class CampaignMessage:
    """Individual message within a campaign"""
    message_number: int
    message_type: MessageType
    subject: str
    body: str
    scheduled_date: datetime
    sent_date: Optional[datetime] = None
    status: MessageStatus = MessageStatus.SCHEDULED
    delivery_id: Optional[str] = None
    opens: int = 0
    clicks: int = 0
    bounced: bool = False
    replied: bool = False
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary for storage"""
        return {
            'message_number': self.message_number,
            'message_type': self.message_type.value,
            'subject': self.subject,
            'body': self.body,
            'scheduled_date': self.scheduled_date.isoformat(),
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'status': self.status.value,
            'delivery_id': self.delivery_id,
            'opens': self.opens,
            'clicks': self.clicks,
            'bounced': self.bounced,
            'replied': self.replied
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CampaignMessage':
        """Create message from dictionary"""
        return cls(
            message_number=data['message_number'],
            message_type=MessageType(data['message_type']),
            subject=data['subject'],
            body=data['body'],
            scheduled_date=datetime.fromisoformat(data['scheduled_date']),
            sent_date=datetime.fromisoformat(data['sent_date']) if data['sent_date'] else None,
            status=MessageStatus(data['status']),
            delivery_id=data.get('delivery_id'),
            opens=data.get('opens', 0),
            clicks=data.get('clicks', 0),
            bounced=data.get('bounced', False),
            replied=data.get('replied', False)
        )


@dataclass
class Campaign:
    """Complete multi-step email campaign"""
    campaign_id: str
    lead_id: str
    company: str
    campaign_type: str = "standard"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.now)
    campaign_status: CampaignStatus = CampaignStatus.ACTIVE
    current_message: int = 1
    response_detected: bool = False
    response_date: Optional[datetime] = None
    response_type: Optional[ResponseType] = None
    messages: List[CampaignMessage] = field(default_factory=list)
    total_opens: int = 0
    total_clicks: int = 0
    conversion_rate: float = 0.0
    engagement_score: float = 0.0
    airtable_record_id: Optional[str] = None
    lead_traits: Dict = field(default_factory=dict)
    company_insights: Dict = field(default_factory=dict)
    
    def add_message(self, message: CampaignMessage) -> None:
        """Add a message to the campaign"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_message_by_type(self, message_type: MessageType) -> Optional[CampaignMessage]:
        """Get message by type"""
        for message in self.messages:
            if message.message_type == message_type:
                return message
        return None
    
    def get_current_message(self) -> Optional[CampaignMessage]:
        """Get the current message to be sent"""
        for message in self.messages:
            if message.message_number == self.current_message:
                return message
        return None
    
    def mark_response_received(self, response_type: ResponseType, message_number: int) -> None:
        """Mark campaign as having received a response"""
        self.response_detected = True
        self.response_date = datetime.now()
        self.response_type = response_type
        self.campaign_status = CampaignStatus.RESPONDED
        self.updated_at = datetime.now()
        
        # Mark the specific message as replied
        for message in self.messages:
            if message.message_number == message_number:
                message.replied = True
                break
    
    def pause_campaign(self) -> None:
        """Pause the campaign"""
        self.campaign_status = CampaignStatus.PAUSED
        self.updated_at = datetime.now()
    
    def resume_campaign(self) -> None:
        """Resume the campaign"""
        if self.campaign_status == CampaignStatus.PAUSED:
            self.campaign_status = CampaignStatus.ACTIVE
            self.updated_at = datetime.now()
    
    def complete_campaign(self) -> None:
        """Mark campaign as completed"""
        self.campaign_status = CampaignStatus.COMPLETED
        self.updated_at = datetime.now()
    
    def calculate_metrics(self) -> None:
        """Calculate campaign performance metrics"""
        if not self.messages:
            return
        
        self.total_opens = sum(msg.opens for msg in self.messages)
        self.total_clicks = sum(msg.clicks for msg in self.messages)
        
        # Calculate conversion rate (response rate)
        self.conversion_rate = 1.0 if self.response_detected else 0.0
        
        # Calculate engagement score based on opens and clicks
        total_sent = sum(1 for msg in self.messages if msg.status == MessageStatus.SENT)
        if total_sent > 0:
            open_rate = self.total_opens / total_sent
            click_rate = self.total_clicks / total_sent if self.total_opens > 0 else 0
            self.engagement_score = (open_rate * 0.7) + (click_rate * 0.3)
        
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert campaign to dictionary for storage"""
        return {
            'campaign_id': self.campaign_id,
            'lead_id': self.lead_id,
            'company': self.company,
            'campaign_type': self.campaign_type,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'updated_at': self.updated_at.isoformat(),
            'campaign_status': self.campaign_status.value,
            'current_message': self.current_message,
            'response_detected': self.response_detected,
            'response_date': self.response_date.isoformat() if self.response_date else None,
            'response_type': self.response_type.value if self.response_type else None,
            'messages': [msg.to_dict() for msg in self.messages],
            'total_opens': self.total_opens,
            'total_clicks': self.total_clicks,
            'conversion_rate': self.conversion_rate,
            'engagement_score': self.engagement_score,
            'airtable_record_id': self.airtable_record_id,
            'lead_traits': self.lead_traits,
            'company_insights': self.company_insights
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Campaign':
        """Create campaign from dictionary"""
        campaign = cls(
            campaign_id=data['campaign_id'],
            lead_id=data['lead_id'],
            company=data['company'],
            campaign_type=data.get('campaign_type', 'standard'),
            created_at=datetime.fromisoformat(data['created_at']),
            started_at=datetime.fromisoformat(data['started_at']) if data['started_at'] else None,
            updated_at=datetime.fromisoformat(data['updated_at']),
            campaign_status=CampaignStatus(data['campaign_status']),
            current_message=data.get('current_message', 1),
            response_detected=data.get('response_detected', False),
            response_date=datetime.fromisoformat(data['response_date']) if data['response_date'] else None,
            response_type=ResponseType(data['response_type']) if data['response_type'] else None,
            total_opens=data.get('total_opens', 0),
            total_clicks=data.get('total_clicks', 0),
            conversion_rate=data.get('conversion_rate', 0.0),
            engagement_score=data.get('engagement_score', 0.0),
            airtable_record_id=data.get('airtable_record_id'),
            lead_traits=data.get('lead_traits', {}),
            company_insights=data.get('company_insights', {})
        )
        
        # Add messages
        for msg_data in data.get('messages', []):
            campaign.add_message(CampaignMessage.from_dict(msg_data))
        
        return campaign