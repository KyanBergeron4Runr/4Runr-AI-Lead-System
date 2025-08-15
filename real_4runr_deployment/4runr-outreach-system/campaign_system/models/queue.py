"""
Message Queue data model for campaign message delivery
"""

from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class QueueStatus(Enum):
    """Message queue status enumeration"""
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class MessageQueue:
    """Message queue entry for scheduled delivery"""
    queue_id: str
    campaign_id: str
    message_number: int
    lead_email: str
    subject: str
    body: str
    scheduled_for: datetime
    priority: int = 5  # 1-10 scale, 1 is highest priority
    attempts: int = 0
    status: QueueStatus = QueueStatus.QUEUED
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    max_attempts: int = 3
    
    def increment_attempts(self) -> None:
        """Increment delivery attempts"""
        self.attempts += 1
        self.last_attempt = datetime.now()
        
        if self.attempts >= self.max_attempts:
            self.status = QueueStatus.DEAD_LETTER
    
    def mark_processing(self) -> None:
        """Mark message as being processed"""
        self.status = QueueStatus.PROCESSING
        self.last_attempt = datetime.now()
    
    def mark_sent(self) -> None:
        """Mark message as successfully sent"""
        self.status = QueueStatus.SENT
        self.last_attempt = datetime.now()
    
    def mark_failed(self, error: str) -> None:
        """Mark message as failed with error"""
        self.status = QueueStatus.FAILED
        self.error_message = error
        self.increment_attempts()
    
    def is_ready_for_delivery(self) -> bool:
        """Check if message is ready for delivery"""
        return (
            self.status in [QueueStatus.QUEUED, QueueStatus.FAILED] and
            self.attempts < self.max_attempts and
            datetime.now() >= self.scheduled_for
        )
    
    def is_dead_letter(self) -> bool:
        """Check if message is in dead letter queue"""
        return self.status == QueueStatus.DEAD_LETTER
    
    def to_dict(self) -> Dict:
        """Convert queue entry to dictionary for storage"""
        return {
            'queue_id': self.queue_id,
            'campaign_id': self.campaign_id,
            'message_number': self.message_number,
            'lead_email': self.lead_email,
            'subject': self.subject,
            'body': self.body,
            'scheduled_for': self.scheduled_for.isoformat(),
            'priority': self.priority,
            'attempts': self.attempts,
            'status': self.status.value,
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'max_attempts': self.max_attempts
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MessageQueue':
        """Create queue entry from dictionary"""
        return cls(
            queue_id=data['queue_id'],
            campaign_id=data['campaign_id'],
            message_number=data['message_number'],
            lead_email=data['lead_email'],
            subject=data['subject'],
            body=data['body'],
            scheduled_for=datetime.fromisoformat(data['scheduled_for']),
            priority=data.get('priority', 5),
            attempts=data.get('attempts', 0),
            status=QueueStatus(data['status']),
            last_attempt=datetime.fromisoformat(data['last_attempt']) if data['last_attempt'] else None,
            error_message=data.get('error_message'),
            created_at=datetime.fromisoformat(data['created_at']),
            max_attempts=data.get('max_attempts', 3)
        )