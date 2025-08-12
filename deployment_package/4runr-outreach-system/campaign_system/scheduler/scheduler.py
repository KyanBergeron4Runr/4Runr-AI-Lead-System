"""
Campaign Scheduler for Multi-Step Email Campaigns

Manages intelligent timing and scheduling for Hook → Proof → FOMO message sequences
with business day awareness and response-based progression control.
"""

import uuid
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from campaign_system.models.campaign import Campaign, CampaignMessage, MessageType, CampaignStatus
from campaign_system.models.queue import MessageQueue, QueueStatus
from campaign_system.database.connection import get_database_connection
from campaign_system.config import get_config


class CampaignScheduler:
    """Intelligent scheduler for multi-step email campaigns"""
    
    def __init__(self):
        self.config = get_config()
        self.db = get_database_connection()
        
        # Default scheduling intervals
        self.message_delays = self.config.get_message_delays()
        self.respect_business_days = self.config.RESPECT_BUSINESS_DAYS
    
    def schedule_campaign(self, campaign: Campaign, start_date: Optional[datetime] = None) -> bool:
        """
        Schedule all messages in a campaign for delivery
        
        Args:
            campaign: Campaign object with messages to schedule
            start_date: When to start the campaign (defaults to now)
            
        Returns:
            True if scheduling successful, False otherwise
        """
        if start_date is None:
            start_date = datetime.now()
        
        try:
            # Calculate send dates for each message
            send_dates = self._calculate_send_dates(start_date)
            
            # Schedule each message
            for i, message in enumerate(campaign.messages):
                if i < len(send_dates):
                    scheduled_date = send_dates[i]
                    
                    # Create queue entry
                    queue_entry = MessageQueue(
                        queue_id=str(uuid.uuid4()),
                        campaign_id=campaign.campaign_id,
                        message_number=message.message_number,
                        lead_email=self._get_lead_email(campaign.lead_id),
                        subject=message.subject,
                        body=message.body,
                        scheduled_for=scheduled_date,
                        priority=self._calculate_priority(message.message_type, campaign)
                    )
                    
                    # Insert into queue
                    self._insert_queue_entry(queue_entry)
                    
                    # Update message scheduled date
                    message.scheduled_date = scheduled_date
            
            # Update campaign status
            campaign.started_at = start_date
            campaign.campaign_status = CampaignStatus.ACTIVE
            self._update_campaign(campaign)
            
            return True
            
        except Exception as e:
            print(f"❌ Error scheduling campaign {campaign.campaign_id}: {e}")
            return False
    
    def _calculate_send_dates(self, start_date: datetime) -> List[datetime]:
        """
        Calculate optimal send dates for Hook, Proof, FOMO sequence
        
        Args:
            start_date: Campaign start date
            
        Returns:
            List of datetime objects for each message
        """
        send_dates = []
        
        # Hook message (Day 0)
        hook_date = start_date
        if self.respect_business_days:
            hook_date = self._adjust_for_business_day(hook_date)
        send_dates.append(hook_date)
        
        # Proof message (Day 3)
        proof_date = hook_date + timedelta(days=self.message_delays['proof'])
        if self.respect_business_days:
            proof_date = self._adjust_for_business_day(proof_date)
        send_dates.append(proof_date)
        
        # FOMO message (Day 7)
        fomo_date = hook_date + timedelta(days=self.message_delays['fomo'])
        if self.respect_business_days:
            fomo_date = self._adjust_for_business_day(fomo_date)
        send_dates.append(fomo_date)
        
        return send_dates
    
    def _adjust_for_business_day(self, target_date: datetime) -> datetime:
        """
        Adjust date to next business day if it falls on weekend
        
        Args:
            target_date: Original target date
            
        Returns:
            Adjusted datetime for business day
        """
        # If it's Saturday (5) or Sunday (6), move to Monday
        while target_date.weekday() >= 5:
            target_date += timedelta(days=1)
        
        return target_date
    
    def _calculate_priority(self, message_type: MessageType, campaign: Campaign) -> int:
        """
        Calculate message priority for queue processing
        
        Args:
            message_type: Type of message (hook, proof, fomo)
            campaign: Campaign object
            
        Returns:
            Priority level (1-10, 1 is highest)
        """
        # Base priority by message type
        type_priority = {
            MessageType.HOOK: 3,    # High priority - start of sequence
            MessageType.PROOF: 5,   # Medium priority
            MessageType.FOMO: 7     # Lower priority - final message
        }
        
        base_priority = type_priority.get(message_type, 5)
        
        # Adjust based on campaign factors
        # Higher quality campaigns get higher priority
        if hasattr(campaign, 'overall_quality_score'):
            if campaign.overall_quality_score >= 90:
                base_priority -= 1  # Higher priority
            elif campaign.overall_quality_score < 70:
                base_priority += 1  # Lower priority
        
        return max(1, min(10, base_priority))
    
    def _get_lead_email(self, lead_id: str) -> str:
        """
        Get lead email address from lead_id
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            Email address or empty string if not found
        """
        # This would typically query the lead database or Airtable
        # For now, return a placeholder
        return f"lead_{lead_id}@example.com"
    
    def _insert_queue_entry(self, queue_entry: MessageQueue) -> bool:
        """
        Insert message queue entry into database
        
        Args:
            queue_entry: MessageQueue object to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            INSERT INTO message_queue (
                queue_id, campaign_id, message_number, lead_email, subject, body,
                scheduled_for, priority, attempts, status, created_at, max_attempts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                queue_entry.queue_id,
                queue_entry.campaign_id,
                queue_entry.message_number,
                queue_entry.lead_email,
                queue_entry.subject,
                queue_entry.body,
                queue_entry.scheduled_for.isoformat(),
                queue_entry.priority,
                queue_entry.attempts,
                queue_entry.status.value,
                queue_entry.created_at.isoformat(),
                queue_entry.max_attempts
            )
            
            self.db.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"❌ Error inserting queue entry: {e}")
            return False
    
    def _update_campaign(self, campaign: Campaign) -> bool:
        """
        Update campaign in database
        
        Args:
            campaign: Campaign object to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            UPDATE campaigns SET
                started_at = ?,
                updated_at = ?,
                campaign_status = ?
            WHERE campaign_id = ?
            """
            
            params = (
                campaign.started_at.isoformat() if campaign.started_at else None,
                campaign.updated_at.isoformat(),
                campaign.campaign_status.value,
                campaign.campaign_id
            )
            
            self.db.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"❌ Error updating campaign: {e}")
            return False
    
    def pause_campaign(self, campaign_id: str, reason: str = "Manual pause") -> bool:
        """
        Pause an active campaign
        
        Args:
            campaign_id: Campaign to pause
            reason: Reason for pausing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update campaign status
            query = """
            UPDATE campaigns SET
                campaign_status = 'paused',
                updated_at = ?
            WHERE campaign_id = ?
            """
            
            self.db.execute_query(query, (datetime.now().isoformat(), campaign_id))
            
            # Update pending queue entries
            queue_query = """
            UPDATE message_queue SET
                status = 'paused'
            WHERE campaign_id = ? AND status = 'queued'
            """
            
            self.db.execute_query(queue_query, (campaign_id,))
            
            print(f"✅ Campaign {campaign_id} paused: {reason}")
            return True
            
        except Exception as e:
            print(f"❌ Error pausing campaign {campaign_id}: {e}")
            return False
    
    def resume_campaign(self, campaign_id: str) -> bool:
        """
        Resume a paused campaign
        
        Args:
            campaign_id: Campaign to resume
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update campaign status
            query = """
            UPDATE campaigns SET
                campaign_status = 'active',
                updated_at = ?
            WHERE campaign_id = ?
            """
            
            self.db.execute_query(query, (datetime.now().isoformat(), campaign_id))
            
            # Update paused queue entries
            queue_query = """
            UPDATE message_queue SET
                status = 'queued'
            WHERE campaign_id = ? AND status = 'paused'
            """
            
            self.db.execute_query(queue_query, (campaign_id,))
            
            print(f"✅ Campaign {campaign_id} resumed")
            return True
            
        except Exception as e:
            print(f"❌ Error resuming campaign {campaign_id}: {e}")
            return False
    
    def check_response_and_pause(self, campaign_id: str, message_number: int) -> bool:
        """
        Check if a campaign should be paused due to response
        
        Args:
            campaign_id: Campaign to check
            message_number: Message that received response
            
        Returns:
            True if campaign was paused, False otherwise
        """
        try:
            # Mark campaign as responded
            query = """
            UPDATE campaigns SET
                campaign_status = 'responded',
                response_detected = 1,
                response_date = ?,
                updated_at = ?
            WHERE campaign_id = ?
            """
            
            params = (
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                campaign_id
            )
            
            self.db.execute_query(query, params)
            
            # Cancel remaining queued messages
            cancel_query = """
            UPDATE message_queue SET
                status = 'skipped'
            WHERE campaign_id = ? AND status = 'queued' AND message_number > ?
            """
            
            self.db.execute_query(cancel_query, (campaign_id, message_number))
            
            print(f"✅ Campaign {campaign_id} paused due to response on message {message_number}")
            return True
            
        except Exception as e:
            print(f"❌ Error pausing campaign due to response: {e}")
            return False
    
    def get_ready_messages(self, limit: int = 50) -> List[MessageQueue]:
        """
        Get messages ready for delivery
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of MessageQueue objects ready for sending
        """
        try:
            query = """
            SELECT * FROM message_queue
            WHERE status = 'queued'
            AND scheduled_for <= ?
            AND attempts < max_attempts
            ORDER BY priority ASC, scheduled_for ASC
            LIMIT ?
            """
            
            params = (datetime.now().isoformat(), limit)
            rows = self.db.execute_query(query, params)
            
            messages = []
            for row in rows:
                message = MessageQueue(
                    queue_id=row['queue_id'],
                    campaign_id=row['campaign_id'],
                    message_number=row['message_number'],
                    lead_email=row['lead_email'],
                    subject=row['subject'],
                    body=row['body'],
                    scheduled_for=datetime.fromisoformat(row['scheduled_for']),
                    priority=row['priority'],
                    attempts=row['attempts'],
                    status=QueueStatus(row['status']),
                    last_attempt=datetime.fromisoformat(row['last_attempt']) if row['last_attempt'] else None,
                    error_message=row['error_message'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    max_attempts=row['max_attempts']
                )
                messages.append(message)
            
            return messages
            
        except Exception as e:
            print(f"❌ Error getting ready messages: {e}")
            return []
    
    def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a campaign
        
        Args:
            campaign_id: Campaign to check
            
        Returns:
            Dictionary with campaign status information
        """
        try:
            # Get campaign info
            campaign_query = """
            SELECT * FROM campaigns WHERE campaign_id = ?
            """
            
            campaign_rows = self.db.execute_query(campaign_query, (campaign_id,))
            if not campaign_rows:
                return {'error': 'Campaign not found'}
            
            campaign_row = campaign_rows[0]
            
            # Get queue status
            queue_query = """
            SELECT status, COUNT(*) as count FROM message_queue
            WHERE campaign_id = ?
            GROUP BY status
            """
            
            queue_rows = self.db.execute_query(queue_query, (campaign_id,))
            queue_status = {row['status']: row['count'] for row in queue_rows}
            
            return {
                'campaign_id': campaign_id,
                'status': campaign_row['campaign_status'],
                'created_at': campaign_row['created_at'],
                'started_at': campaign_row['started_at'],
                'response_detected': bool(campaign_row['response_detected']),
                'response_date': campaign_row['response_date'],
                'queue_status': queue_status,
                'total_messages': sum(queue_status.values())
            }
            
        except Exception as e:
            print(f"❌ Error getting campaign status: {e}")
            return {'error': str(e)}