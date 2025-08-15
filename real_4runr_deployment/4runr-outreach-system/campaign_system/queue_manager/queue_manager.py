"""
Message Queue Manager for Multi-Step Email Campaigns

Handles message delivery coordination, retry logic, and batch processing
for the campaign delivery system.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from campaign_system.models.queue import MessageQueue, QueueStatus
from campaign_system.database.connection import get_database_connection
from campaign_system.config import get_config


class MessageQueueManager:
    """Manages message delivery queue and coordination"""
    
    def __init__(self):
        self.config = get_config()
        self.db = get_database_connection()
        
        # Queue configuration
        self.batch_size = self.config.QUEUE_BATCH_SIZE
        self.max_attempts = self.config.MAX_DELIVERY_ATTEMPTS
        self.retry_delay_minutes = self.config.RETRY_DELAY_MINUTES
    
    def add_to_queue(self, campaign_id: str, message_number: int, lead_email: str,
                     subject: str, body: str, scheduled_for: datetime, priority: int = 5) -> str:
        """
        Add a message to the delivery queue
        
        Args:
            campaign_id: Campaign identifier
            message_number: Message sequence number (1, 2, 3)
            lead_email: Recipient email address
            subject: Email subject line
            body: Email body content
            scheduled_for: When to send the message
            priority: Queue priority (1-10, 1 is highest)
            
        Returns:
            Queue ID if successful, None if failed
        """
        try:
            queue_entry = MessageQueue(
                queue_id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                message_number=message_number,
                lead_email=lead_email,
                subject=subject,
                body=body,
                scheduled_for=scheduled_for,
                priority=priority
            )
            
            success = self._insert_queue_entry(queue_entry)
            return queue_entry.queue_id if success else None
            
        except Exception as e:
            print(f"❌ Error adding message to queue: {e}")
            return None
    
    def get_ready_messages(self, limit: Optional[int] = None) -> List[MessageQueue]:
        """
        Get messages ready for delivery
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of MessageQueue objects ready for sending
        """
        if limit is None:
            limit = self.batch_size
        
        try:
            query = """
            SELECT * FROM message_queue
            WHERE status IN ('queued', 'failed')
            AND scheduled_for <= ?
            AND attempts < max_attempts
            AND (last_attempt IS NULL OR datetime(last_attempt, '+{} minutes') <= datetime('now'))
            ORDER BY priority ASC, scheduled_for ASC
            LIMIT ?
            """.format(self.retry_delay_minutes)
            
            params = (datetime.now().isoformat(), limit)
            rows = self.db.execute_query(query, params)
            
            messages = []
            for row in rows:
                message = self._row_to_message_queue(row)
                messages.append(message)
            
            return messages
            
        except Exception as e:
            print(f"❌ Error getting ready messages: {e}")
            return []
    
    def mark_processing(self, queue_id: str) -> bool:
        """
        Mark a message as being processed
        
        Args:
            queue_id: Queue entry identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            UPDATE message_queue SET
                status = 'processing',
                last_attempt = ?
            WHERE queue_id = ?
            """
            
            params = (datetime.now().isoformat(), queue_id)
            self.db.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"❌ Error marking message as processing: {e}")
            return False
    
    def mark_sent(self, queue_id: str, delivery_id: Optional[str] = None) -> bool:
        """
        Mark a message as successfully sent
        
        Args:
            queue_id: Queue entry identifier
            delivery_id: External delivery service ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            UPDATE message_queue SET
                status = 'sent',
                last_attempt = ?
            WHERE queue_id = ?
            """
            
            params = (datetime.now().isoformat(), queue_id)
            self.db.execute_query(query, params)
            
            # Update campaign message status
            self._update_campaign_message_status(queue_id, 'sent')
            
            return True
            
        except Exception as e:
            print(f"❌ Error marking message as sent: {e}")
            return False
    
    def mark_failed(self, queue_id: str, error_message: str) -> bool:
        """
        Mark a message as failed
        
        Args:
            queue_id: Queue entry identifier
            error_message: Error description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current message to check attempts
            message = self._get_queue_entry(queue_id)
            if not message:
                return False
            
            new_attempts = message.attempts + 1
            new_status = 'dead_letter' if new_attempts >= self.max_attempts else 'failed'
            
            query = """
            UPDATE message_queue SET
                status = ?,
                attempts = ?,
                last_attempt = ?,
                error_message = ?
            WHERE queue_id = ?
            """
            
            params = (
                new_status,
                new_attempts,
                datetime.now().isoformat(),
                error_message,
                queue_id
            )
            
            self.db.execute_query(query, params)
            
            # Update campaign message status
            self._update_campaign_message_status(queue_id, 'failed')
            
            return True
            
        except Exception as e:
            print(f"❌ Error marking message as failed: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics
        
        Returns:
            Dictionary with queue statistics
        """
        try:
            query = """
            SELECT 
                status,
                COUNT(*) as count,
                MIN(scheduled_for) as earliest_scheduled,
                MAX(scheduled_for) as latest_scheduled
            FROM message_queue
            GROUP BY status
            """
            
            rows = self.db.execute_query(query)
            
            stats = {
                'total_messages': 0,
                'by_status': {},
                'earliest_scheduled': None,
                'latest_scheduled': None
            }
            
            for row in rows:
                status = row['status']
                count = row['count']
                
                stats['by_status'][status] = count
                stats['total_messages'] += count
                
                # Track earliest and latest scheduled times
                if row['earliest_scheduled']:
                    earliest = datetime.fromisoformat(row['earliest_scheduled'])
                    if not stats['earliest_scheduled'] or earliest < stats['earliest_scheduled']:
                        stats['earliest_scheduled'] = earliest
                
                if row['latest_scheduled']:
                    latest = datetime.fromisoformat(row['latest_scheduled'])
                    if not stats['latest_scheduled'] or latest > stats['latest_scheduled']:
                        stats['latest_scheduled'] = latest
            
            # Get ready messages count
            ready_query = """
            SELECT COUNT(*) as ready_count FROM message_queue
            WHERE status IN ('queued', 'failed')
            AND scheduled_for <= ?
            AND attempts < max_attempts
            """
            
            ready_rows = self.db.execute_query(ready_query, (datetime.now().isoformat(),))
            stats['ready_for_delivery'] = ready_rows[0]['ready_count'] if ready_rows else 0
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting queue stats: {e}")
            return {'error': str(e)}
    
    def get_campaign_queue_status(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get queue status for a specific campaign
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Dictionary with campaign queue status
        """
        try:
            query = """
            SELECT 
                message_number,
                status,
                scheduled_for,
                last_attempt,
                attempts,
                error_message
            FROM message_queue
            WHERE campaign_id = ?
            ORDER BY message_number ASC
            """
            
            rows = self.db.execute_query(query, (campaign_id,))
            
            messages = []
            for row in rows:
                message_info = {
                    'message_number': row['message_number'],
                    'status': row['status'],
                    'scheduled_for': row['scheduled_for'],
                    'last_attempt': row['last_attempt'],
                    'attempts': row['attempts'],
                    'error_message': row['error_message']
                }
                messages.append(message_info)
            
            return {
                'campaign_id': campaign_id,
                'messages': messages,
                'total_messages': len(messages)
            }
            
        except Exception as e:
            print(f"❌ Error getting campaign queue status: {e}")
            return {'error': str(e)}
    
    def cleanup_old_messages(self, days_old: int = 30) -> int:
        """
        Clean up old completed messages from the queue
        
        Args:
            days_old: Remove messages older than this many days
            
        Returns:
            Number of messages cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            query = """
            DELETE FROM message_queue
            WHERE status IN ('sent', 'dead_letter')
            AND created_at < ?
            """
            
            result = self.db.execute_query(query, (cutoff_date.isoformat(),))
            
            # Get count of deleted rows (this is database-specific)
            count_query = "SELECT changes() as deleted_count"
            count_rows = self.db.execute_query(count_query)
            deleted_count = count_rows[0]['deleted_count'] if count_rows else 0
            
            print(f"✅ Cleaned up {deleted_count} old messages")
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error cleaning up old messages: {e}")
            return 0
    
    def requeue_failed_messages(self, campaign_id: Optional[str] = None) -> int:
        """
        Requeue failed messages for retry
        
        Args:
            campaign_id: Optional campaign to limit requeuing to
            
        Returns:
            Number of messages requeued
        """
        try:
            base_query = """
            UPDATE message_queue SET
                status = 'queued',
                error_message = NULL
            WHERE status = 'failed'
            AND attempts < max_attempts
            """
            
            params = []
            if campaign_id:
                base_query += " AND campaign_id = ?"
                params.append(campaign_id)
            
            self.db.execute_query(base_query, params)
            
            # Get count of updated rows
            count_query = "SELECT changes() as updated_count"
            count_rows = self.db.execute_query(count_query)
            updated_count = count_rows[0]['updated_count'] if count_rows else 0
            
            print(f"✅ Requeued {updated_count} failed messages")
            return updated_count
            
        except Exception as e:
            print(f"❌ Error requeuing failed messages: {e}")
            return 0
    
    def _insert_queue_entry(self, queue_entry: MessageQueue) -> bool:
        """Insert message queue entry into database"""
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
    
    def _get_queue_entry(self, queue_id: str) -> Optional[MessageQueue]:
        """Get queue entry by ID"""
        try:
            query = "SELECT * FROM message_queue WHERE queue_id = ?"
            rows = self.db.execute_query(query, (queue_id,))
            
            if rows:
                return self._row_to_message_queue(rows[0])
            return None
            
        except Exception as e:
            print(f"❌ Error getting queue entry: {e}")
            return None
    
    def _row_to_message_queue(self, row: Dict[str, Any]) -> MessageQueue:
        """Convert database row to MessageQueue object"""
        return MessageQueue(
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
    
    def _update_campaign_message_status(self, queue_id: str, status: str) -> bool:
        """Update campaign message status based on queue entry"""
        try:
            # Get queue entry details
            queue_query = "SELECT campaign_id, message_number FROM message_queue WHERE queue_id = ?"
            queue_rows = self.db.execute_query(queue_query, (queue_id,))
            
            if not queue_rows:
                return False
            
            campaign_id = queue_rows[0]['campaign_id']
            message_number = queue_rows[0]['message_number']
            
            # Update campaign message status
            update_query = """
            UPDATE campaign_messages SET
                status = ?,
                sent_date = ?
            WHERE campaign_id = ? AND message_number = ?
            """
            
            sent_date = datetime.now().isoformat() if status == 'sent' else None
            params = (status, sent_date, campaign_id, message_number)
            
            self.db.execute_query(update_query, params)
            return True
            
        except Exception as e:
            print(f"❌ Error updating campaign message status: {e}")
            return False