"""
Lead Data Model

Clean, consistent data model for lead management.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Lead:
    """
    Lead data model representing a potential customer.
    
    This is the single source of truth for lead data structure.
    """
    # Core identification
    id: Optional[int] = None
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic information
    full_name: str = ""
    email: str = ""
    company: str = ""
    title: str = ""
    
    # Contact information
    linkedin_url: str = ""
    website: str = ""
    phone: str = ""
    location: str = ""
    
    # Company information
    industry: str = ""
    company_size: str = ""
    
    # AI-generated content
    ai_message: str = ""
    
    # Status flags
    status: str = "new"  # new, enriched, ready, contacted, converted
    verified: bool = False
    enriched: bool = False
    ready_for_outreach: bool = False
    
    # Timestamps
    scraped_at: Optional[datetime] = None
    enriched_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Airtable sync
    airtable_id: Optional[str] = None
    airtable_synced: bool = False
    sync_pending: bool = True
    last_sync_attempt: Optional[datetime] = None
    sync_error: Optional[str] = None
    
    # Metadata
    source: str = ""  # serpapi, manual, import, etc.
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and clean data after initialization."""
        self._clean_data()
    
    def _clean_data(self):
        """Clean and standardize data fields."""
        # Clean strings
        self.full_name = self.full_name.strip() if self.full_name else ""
        self.email = self.email.strip().lower() if self.email else ""
        self.company = self.company.strip() if self.company else ""
        self.title = self.title.strip() if self.title else ""
        self.linkedin_url = self.linkedin_url.strip() if self.linkedin_url else ""
        self.website = self.website.strip() if self.website else ""
        self.phone = self.phone.strip() if self.phone else ""
        self.location = self.location.strip() if self.location else ""
        self.industry = self.industry.strip() if self.industry else ""
        self.company_size = self.company_size.strip() if self.company_size else ""
        self.ai_message = self.ai_message.strip() if self.ai_message else ""
        self.source = self.source.strip() if self.source else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert lead to dictionary for database storage."""
        return {
            'uuid': self.uuid,
            'full_name': self.full_name,
            'email': self.email,
            'company': self.company,
            'title': self.title,
            'linkedin_url': self.linkedin_url,
            'website': self.website,
            'phone': self.phone,
            'location': self.location,
            'industry': self.industry,
            'company_size': self.company_size,
            'ai_message': self.ai_message,
            'status': self.status,
            'verified': self.verified,
            'enriched': self.enriched,
            'ready_for_outreach': self.ready_for_outreach,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'enriched_at': self.enriched_at.isoformat() if self.enriched_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'airtable_id': self.airtable_id,
            'airtable_synced': self.airtable_synced,
            'sync_pending': self.sync_pending,
            'last_sync_attempt': self.last_sync_attempt.isoformat() if self.last_sync_attempt else None,
            'sync_error': self.sync_error,
            'source': self.source,
            'raw_data': str(self.raw_data) if self.raw_data else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        """Create lead from dictionary (from database)."""
        # Parse timestamps
        scraped_at = datetime.fromisoformat(data['scraped_at']) if data.get('scraped_at') else None
        enriched_at = datetime.fromisoformat(data['enriched_at']) if data.get('enriched_at') else None
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        last_sync_attempt = datetime.fromisoformat(data['last_sync_attempt']) if data.get('last_sync_attempt') else None
        
        # Parse raw_data
        raw_data = {}
        if data.get('raw_data'):
            try:
                import json
                raw_data = json.loads(data['raw_data'])
            except:
                raw_data = {}
        
        return cls(
            id=data.get('id'),
            uuid=data.get('uuid', str(uuid.uuid4())),
            full_name=data.get('full_name', ''),
            email=data.get('email', ''),
            company=data.get('company', ''),
            title=data.get('title', ''),
            linkedin_url=data.get('linkedin_url', ''),
            website=data.get('website', ''),
            phone=data.get('phone', ''),
            location=data.get('location', ''),
            industry=data.get('industry', ''),
            company_size=data.get('company_size', ''),
            ai_message=data.get('ai_message', ''),
            status=data.get('status', 'new'),
            verified=data.get('verified', False),
            enriched=data.get('enriched', False),
            ready_for_outreach=data.get('ready_for_outreach', False),
            scraped_at=scraped_at,
            enriched_at=enriched_at,
            created_at=created_at,
            updated_at=updated_at,
            airtable_id=data.get('airtable_id'),
            airtable_synced=data.get('airtable_synced', False),
            sync_pending=data.get('sync_pending', True),
            last_sync_attempt=last_sync_attempt,
            sync_error=data.get('sync_error'),
            source=data.get('source', ''),
            raw_data=raw_data
        )
    
    def is_complete(self) -> bool:
        """Check if lead has all required information."""
        return bool(
            self.full_name and 
            self.email and 
            self.company and 
            self.linkedin_url
        )
    
    def needs_enrichment(self) -> bool:
        """Check if lead needs enrichment."""
        return not self.enriched or not (self.industry and self.company_size)
    
    def is_ready_for_outreach(self) -> bool:
        """Check if lead is ready for outreach."""
        return (
            self.is_complete() and 
            self.enriched and 
            self.ai_message and 
            not self.airtable_synced
        )
    
    def mark_enriched(self):
        """Mark lead as enriched."""
        self.enriched = True
        self.enriched_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_synced(self, airtable_id: Optional[str] = None):
        """Mark lead as synced to Airtable."""
        self.airtable_synced = True
        self.sync_pending = False
        self.last_sync_attempt = datetime.now()
        self.sync_error = None
        self.updated_at = datetime.now()
        if airtable_id:
            self.airtable_id = airtable_id
    
    def mark_sync_failed(self, error: str):
        """Mark lead sync as failed."""
        self.airtable_synced = False
        self.sync_pending = True
        self.last_sync_attempt = datetime.now()
        self.sync_error = error
        self.updated_at = datetime.now()
