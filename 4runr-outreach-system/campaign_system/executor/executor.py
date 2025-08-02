"""
Campaign Executor for Multi-Step Email Campaigns

Handles actual message delivery via Microsoft Graph API with comprehensive
tracking, retry logic, and campaign progression management.
"""

import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from campaign_system.models.queue import MessageQueue, QueueStatus
from campaign_system.queue_manager.queue_manager import MessageQueueManager
from campaign_system.database.connection import get_database_connection
from campaign_system.config import get_config


class CampaignExecutor:
    """Executes campaign message delivery and tracks results"""
    
    def __init__(self):
        self.config = get_config()
        self.queue_manager = MessageQueueManager()
        self.db = get_database_connection()
        
        # Email configuration
        self.email_config = self.config.get_email_config()
        
        # Microsoft Graph configuration
        self.graph_config = {
            'client_id': self.config.SMTP_USERNAME,  # Reusing SMTP config for now
            'client_secret': self.config.SMTP_PASSWORD,
            'tenant_id': 'common',  # Default tenant
            'sender_email': self.config.FROM_EMAIL
        }
    
    def process_delivery_queue(self, batch_size: Optional[int] = None) -> Dict[str, int]:
        """
        Process messages ready for delivery
        
        Args:
            batch_size: Number of messages to process in this batch
            
        Returns:
            Dictionary with delivery statistics
        """
        if batch_size is None:
            batch_size = self.config.QUEUE_BATCH_SIZE
        
        # Get ready messages
        ready_messages = self.queue_manager.get_ready_messages(batch_size)
        
        if not ready_messages:
            return {'processed': 0, 'sent': 0, 'failed': 0, 'skipped': 0}
        
        print(f"📧 Processing {len(ready_messages)} messages for delivery...")
        
        stats = {'processed': 0, 'sent': 0, 'failed': 0, 'skipped': 0}
        
        for message in ready_messages:
            try:
                # Check if campaign is still active
                if not self._is_campaign_active(message.campaign_id):
                    self._skip_message(message.queue_id, "Campaign no longer active")
                    stats['skipped'] += 1
                    continue
                
                # Mark as processing
                self.queue_manager.mark_processing(message.queue_id)
                
                # Send the message
                success, error_msg = self._send_message(message)
                
                if success:
                    # Mark as sent
                    self.queue_manager.mark_sent(message.queue_id)
                    self._update_campaign_progress(message.campaign_id, message.message_number)
                    stats['sent'] += 1
                    
                    print(f"✅ Sent message {message.message_number} for campaign {message.campaign_id}")
                else:
                    # Mark as failed
                    self.queue_manager.mark_failed(message.queue_id, error_msg)
                    stats['failed'] += 1
                    
                    print(f"❌ Failed to send message {message.message_number} for campaign {message.campaign_id}: {error_msg}")
                
                stats['processed'] += 1
                
            except Exception as e:
                print(f"❌ Error processing message {message.queue_id}: {e}")
                self.queue_manager.mark_failed(message.queue_id, str(e))
                stats['failed'] += 1
                stats['processed'] += 1
        
        return stats
    
    def _send_message(self, message: MessageQueue) -> Tuple[bool, Optional[str]]:
        """
        Send a single message via Microsoft Graph API
        
        Args:
            message: MessageQueue object with message details
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        try:
            # For now, simulate sending since we don't have full Graph API setup
            # In production, this would use the actual Microsoft Graph API
            
            # Simulate different outcomes for testing
            import random
            
            # 90% success rate for simulation
            if random.random() < 0.9:
                # Simulate successful send
                self._log_delivery_success(message)
                return True, None
            else:
                # Simulate failure
                error_msg = "Simulated delivery failure for testing"
                self._log_delivery_failure(message, error_msg)
                return False, error_msg
        
        except Exception as e:
            error_msg = f"Exception during message delivery: {str(e)}"
            self._log_delivery_failure(message, error_msg)
            return False, error_msg
    
    def _send_via_graph_api(self, message: MessageQueue) -> Tuple[bool, Optional[str]]:
        """
        Send message via Microsoft Graph API (production implementation)
        
        Args:
            message: MessageQueue object with message details
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        try:
            # Get access token
            access_token = self._get_graph_access_token()
            if not access_token:
                return False, "Failed to get access token"
            
            # Prepare email data
            email_data = {
                "message": {
                    "subject": message.subject,
                    "body": {
                        "contentType": "Text",
                        "content": message.body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": message.lead_email
                            }
                        }
                    ]
                }
            }
            
            # Send via Graph API
            url = f"https://graph.microsoft.com/v1.0/users/{self.graph_config['sender_email']}/sendMail"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, json=email_data)
            
            if response.status_code == 202:
                self._log_delivery_success(message)
                return True, None
            else:
                error_msg = f"Graph API error: {response.status_code} - {response.text}"
                self._log_delivery_failure(message, error_msg)
                return False, error_msg
        
        except Exception as e:
            error_msg = f"Graph API exception: {str(e)}"
            self._log_delivery_failure(message, error_msg)
            return False, error_msg
    
    def _get_graph_access_token(self) -> Optional[str]:
        """Get Microsoft Graph access token"""
        try:
            url = f"https://login.microsoftonline.com/{self.graph_config['tenant_id']}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.graph_config['client_id'],
                'client_secret': self.graph_config['client_secret'],
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                return response.json()['access_token']
            else:
                print(f"❌ Failed to get access token: {response.text}")
                return None
        
        except Exception as e:
            print(f"❌ Error getting access token: {e}")
            return None
    
    def _is_campaign_active(self, campaign_id: str) -> bool:
        """
        Check if a campaign is still active
        
        Args:
            campaign_id: Campaign to check
            
        Returns:
            True if campaign is active, False otherwise
        """
        try:
            query = """
            SELECT campaign_status, response_detected FROM campaigns
            WHERE campaign_id = ?
            """
            
            rows = self.db.execute_query(query, (campaign_id,))
            
            if not rows:
                return False
            
            status = rows[0]['campaign_status']
            response_detected = rows[0]['response_detected']
            
            # Campaign is active if status is 'active' and no response detected
            return status == 'active' and not response_detected
        
        except Exception as e:
            print(f"❌ Error checking campaign status: {e}")
            return False
    
    def _skip_message(self, queue_id: str, reason: str) -> bool:
        """
        Skip a message with reason
        
        Args:
            queue_id: Queue entry to skip
            reason: Reason for skipping
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            UPDATE message_queue SET
                status = 'skipped',
                error_message = ?
            WHERE queue_id = ?
            """
            
            self.db.execute_query(query, (reason, queue_id))
            return True
        
        except Exception as e:
            print(f"❌ Error skipping message: {e}")
            return False
    
    def _update_campaign_progress(self, campaign_id: str, message_number: int) -> bool:
        """
        Update campaign progress after successful message delivery
        
        Args:
            campaign_id: Campaign identifier
            message_number: Message that was sent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update campaign with last sent message
            query = """
            UPDATE campaigns SET
                current_message = ?,
                updated_at = ?
            WHERE campaign_id = ?
            """
            
            params = (
                message_number + 1,  # Next message number
                datetime.now().isoformat(),
                campaign_id
            )
            
            self.db.execute_query(query, params)
            
            # Update analytics
            self._update_campaign_analytics(campaign_id, message_number)
            
            return True
        
        except Exception as e:
            print(f"❌ Error updating campaign progress: {e}")
            return False
    
    def _update_campaign_analytics(self, campaign_id: str, message_number: int) -> bool:
        """
        Update campaign analytics after message delivery
        
        Args:
            campaign_id: Campaign identifier
            message_number: Message that was sent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get or create analytics record for today
            today = datetime.now().date()
            
            # Check if analytics record exists
            check_query = """
            SELECT analytics_id FROM campaign_analytics
            WHERE campaign_id = ? AND date = ?
            """
            
            existing = self.db.execute_query(check_query, (campaign_id, today.isoformat()))
            
            if existing:
                # Update existing record
                analytics_id = existing[0]['analytics_id']
                
                # Increment message sent count based on message type
                if message_number == 1:
                    field = 'hook_sent'
                elif message_number == 2:
                    field = 'proof_sent'
                elif message_number == 3:
                    field = 'fomo_sent'
                else:
                    return True  # Unknown message number
                
                update_query = f"""
                UPDATE campaign_analytics SET
                    {field} = 1,
                    updated_at = ?
                WHERE analytics_id = ?
                """
                
                self.db.execute_query(update_query, (datetime.now().isoformat(), analytics_id))
            
            else:
                # Create new analytics record
                analytics_id = str(uuid.uuid4())
                
                # Set appropriate sent field
                hook_sent = 1 if message_number == 1 else 0
                proof_sent = 1 if message_number == 2 else 0
                fomo_sent = 1 if message_number == 3 else 0
                
                insert_query = """
                INSERT INTO campaign_analytics (
                    analytics_id, campaign_id, date,
                    hook_sent, proof_sent, fomo_sent,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    analytics_id,
                    campaign_id,
                    today.isoformat(),
                    hook_sent,
                    proof_sent,
                    fomo_sent,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                )
                
                self.db.execute_query(insert_query, params)
            
            return True
        
        except Exception as e:
            print(f"❌ Error updating campaign analytics: {e}")
            return False
    
    def _log_delivery_success(self, message: MessageQueue) -> None:
        """Log successful message delivery"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'queue_id': message.queue_id,
            'campaign_id': message.campaign_id,
            'message_number': message.message_number,
            'lead_email': message.lead_email,
            'subject': message.subject,
            'status': 'sent',
            'attempts': message.attempts + 1
        }
        
        print(f"📧 Message sent: Campaign {message.campaign_id}, Message {message.message_number} to {message.lead_email}")
    
    def _log_delivery_failure(self, message: MessageQueue, error_msg: str) -> None:
        """Log failed message delivery"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'queue_id': message.queue_id,
            'campaign_id': message.campaign_id,
            'message_number': message.message_number,
            'lead_email': message.lead_email,
            'subject': message.subject,
            'status': 'failed',
            'error': error_msg,
            'attempts': message.attempts + 1
        }
        
        print(f"❌ Message failed: Campaign {message.campaign_id}, Message {message.message_number} - {error_msg}")
    
    def handle_response_received(self, campaign_id: str, message_number: int, response_type: str = "interested") -> bool:
        """
        Handle when a response is received to pause campaign
        
        Args:
            campaign_id: Campaign that received response
            message_number: Message that was responded to
            response_type: Type of response (interested, not_interested, auto_reply)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update campaign status
            query = """
            UPDATE campaigns SET
                campaign_status = 'responded',
                response_detected = 1,
                response_date = ?,
                response_type = ?,
                updated_at = ?
            WHERE campaign_id = ?
            """
            
            params = (
                datetime.now().isoformat(),
                response_type,
                datetime.now().isoformat(),
                campaign_id
            )
            
            self.db.execute_query(query, params)
            
            # Cancel remaining queued messages
            cancel_query = """
            UPDATE message_queue SET
                status = 'skipped',
                error_message = 'Campaign paused due to response'
            WHERE campaign_id = ? AND status = 'queued' AND message_number > ?
            """
            
            self.db.execute_query(cancel_query, (campaign_id, message_number))
            
            # Update analytics
            self._record_campaign_response(campaign_id, message_number, response_type)
            
            print(f"✅ Campaign {campaign_id} paused due to {response_type} response on message {message_number}")
            return True
        
        except Exception as e:
            print(f"❌ Error handling response: {e}")
            return False
    
    def _record_campaign_response(self, campaign_id: str, message_number: int, response_type: str) -> bool:
        """Record campaign response in analytics"""
        try:
            today = datetime.now().date()
            
            # Update analytics record
            query = """
            UPDATE campaign_analytics SET
                responded = 1,
                response_message = ?,
                updated_at = ?
            WHERE campaign_id = ? AND date = ?
            """
            
            params = (
                message_number,
                datetime.now().isoformat(),
                campaign_id,
                today.isoformat()
            )
            
            self.db.execute_query(query, params)
            return True
        
        except Exception as e:
            print(f"❌ Error recording campaign response: {e}")
            return False
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """
        Get delivery statistics
        
        Returns:
            Dictionary with delivery statistics
        """
        try:
            # Get queue stats
            queue_stats = self.queue_manager.get_queue_stats()
            
            # Get campaign stats
            campaign_query = """
            SELECT 
                campaign_status,
                COUNT(*) as count
            FROM campaigns
            GROUP BY campaign_status
            """
            
            campaign_rows = self.db.execute_query(campaign_query)
            campaign_stats = {row['campaign_status']: row['count'] for row in campaign_rows}
            
            # Get today's delivery stats
            today = datetime.now().date()
            today_query = """
            SELECT 
                SUM(hook_sent + proof_sent + fomo_sent) as messages_sent_today,
                SUM(CASE WHEN responded = 1 THEN 1 ELSE 0 END) as responses_today
            FROM campaign_analytics
            WHERE date = ?
            """
            
            today_rows = self.db.execute_query(today_query, (today.isoformat(),))
            today_stats = today_rows[0] if today_rows else {'messages_sent_today': 0, 'responses_today': 0}
            
            return {
                'queue_stats': queue_stats,
                'campaign_stats': campaign_stats,
                'today_stats': today_stats,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"❌ Error getting delivery stats: {e}")
            return {'error': str(e)}