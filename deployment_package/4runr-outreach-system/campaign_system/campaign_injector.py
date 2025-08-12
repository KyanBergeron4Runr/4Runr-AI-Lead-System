"""
Campaign Injector

Takes validated campaigns and injects them into the delivery queue
with proper scheduling and progression logic.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from campaign_system.models.campaign import Campaign, CampaignMessage, MessageType, CampaignStatus, MessageStatus
from campaign_system.scheduler.scheduler import CampaignScheduler
from campaign_system.database.connection import get_database_connection
from campaign_system.config import get_config


class CampaignInjector:
    """Injects validated campaigns into the delivery system"""
    
    def __init__(self):
        self.config = get_config()
        self.scheduler = CampaignScheduler()
        self.db = get_database_connection()
    
    def inject_campaign(self, campaign_data: Dict[str, Any], lead_data: Dict[str, Any]) -> bool:
        """
        Inject a validated campaign into the delivery system
        
        Args:
            campaign_data: Generated campaign with quality validation
            lead_data: Lead information including email
            
        Returns:
            True if injection successful, False otherwise
        """
        # Check if campaign meets injection criteria
        if not self._should_inject_campaign(campaign_data):
            return False
        
        try:
            # Create campaign object
            campaign = self._create_campaign_object(campaign_data, lead_data)
            
            # Store campaign in database
            if not self._store_campaign(campaign):
                return False
            
            # Schedule campaign messages
            if not self.scheduler.schedule_campaign(campaign):
                return False
            
            print(f"✅ Campaign {campaign.campaign_id} injected successfully for {lead_data.get('Name', 'Unknown')}")
            return True
        
        except Exception as e:
            print(f"❌ Error injecting campaign: {e}")
            return False
    
    def inject_multiple_campaigns(self, campaigns_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Inject multiple campaigns in batch
        
        Args:
            campaigns_data: List of campaign data with lead info
            
        Returns:
            Dictionary with injection statistics
        """
        stats = {'processed': 0, 'injected': 0, 'rejected': 0, 'errors': 0}
        
        for campaign_item in campaigns_data:
            try:
                campaign_data = campaign_item.get('campaign_data', {})
                lead_data = campaign_item.get('lead_data', {})
                
                stats['processed'] += 1
                
                if self.inject_campaign(campaign_data, lead_data):
                    stats['injected'] += 1
                else:
                    stats['rejected'] += 1
            
            except Exception as e:
                print(f"❌ Error processing campaign: {e}")
                stats['errors'] += 1
                stats['processed'] += 1
        
        return stats
    
    def _should_inject_campaign(self, campaign_data: Dict[str, Any]) -> bool:
        """
        Check if campaign meets injection criteria
        
        Args:
            campaign_data: Campaign data to validate
            
        Returns:
            True if campaign should be injected, False otherwise
        """
        # Check if campaign is ready to send
        if not campaign_data.get('ready_to_send', False):
            print(f"⚠️  Campaign not ready to send: ready_to_send = {campaign_data.get('ready_to_send')}")
            return False
        
        # Check quality score threshold
        quality_score = campaign_data.get('overall_quality_score', 0)
        if quality_score < 80:
            print(f"⚠️  Campaign quality score too low: {quality_score}/100 (minimum: 80)")
            return False
        
        # Check that we have all required messages
        messages = campaign_data.get('messages', [])
        if len(messages) != 3:
            print(f"⚠️  Campaign must have exactly 3 messages, got {len(messages)}")
            return False
        
        # Check message types
        expected_types = ['hook', 'proof', 'fomo']
        actual_types = [msg.get('type') for msg in messages]
        
        if actual_types != expected_types:
            print(f"⚠️  Invalid message types: expected {expected_types}, got {actual_types}")
            return False
        
        return True
    
    def _create_campaign_object(self, campaign_data: Dict[str, Any], lead_data: Dict[str, Any]) -> Campaign:
        """
        Create Campaign object from campaign data
        
        Args:
            campaign_data: Generated campaign data
            lead_data: Lead information
            
        Returns:
            Campaign object
        """
        campaign_id = str(uuid.uuid4())
        
        # Create campaign
        campaign = Campaign(
            campaign_id=campaign_id,
            lead_id=lead_data.get('id', str(uuid.uuid4())),
            company=lead_data.get('Company', 'Unknown Company'),
            campaign_type='standard',
            created_at=datetime.now(),
            campaign_status=CampaignStatus.ACTIVE,
            lead_traits=lead_data,
            company_insights=campaign_data.get('company_insights', {})
        )
        
        # Set additional attributes
        campaign.overall_quality_score = campaign_data.get('overall_quality_score', 0)
        
        # Add messages
        messages = campaign_data.get('messages', [])
        for i, msg_data in enumerate(messages, 1):
            message_type = MessageType(msg_data.get('type', 'hook'))
            
            message = CampaignMessage(
                message_number=i,
                message_type=message_type,
                subject=msg_data.get('subject', ''),
                body=msg_data.get('body', ''),
                scheduled_date=datetime.now(),  # Will be updated by scheduler
                status=MessageStatus.SCHEDULED
            )
            
            # Set additional attributes
            message.quality_score = msg_data.get('quality_score', 0)
            message.issues_detected = msg_data.get('issues_detected', [])
            
            campaign.add_message(message)
        
        return campaign
    
    def _store_campaign(self, campaign: Campaign) -> bool:
        """
        Store campaign in database
        
        Args:
            campaign: Campaign object to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Insert campaign record
            campaign_query = """
            INSERT INTO campaigns (
                campaign_id, lead_id, company, campaign_type, created_at,
                updated_at, campaign_status, current_message, response_detected,
                total_opens, total_clicks, conversion_rate, engagement_score,
                airtable_record_id, lead_traits, company_insights
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            import json
            
            campaign_params = (
                campaign.campaign_id,
                campaign.lead_id,
                campaign.company,
                campaign.campaign_type,
                campaign.created_at.isoformat(),
                campaign.updated_at.isoformat(),
                campaign.campaign_status.value,
                campaign.current_message,
                campaign.response_detected,
                campaign.total_opens,
                campaign.total_clicks,
                campaign.conversion_rate,
                campaign.engagement_score,
                campaign.airtable_record_id,
                json.dumps(campaign.lead_traits),
                json.dumps(campaign.company_insights)
            )
            
            self.db.execute_query(campaign_query, campaign_params)
            
            # Insert campaign messages
            for message in campaign.messages:
                message_query = """
                INSERT INTO campaign_messages (
                    campaign_id, message_number, message_type, subject, body,
                    scheduled_date, status, opens, clicks, bounced, replied
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                message_params = (
                    campaign.campaign_id,
                    message.message_number,
                    message.message_type.value,
                    message.subject,
                    message.body,
                    message.scheduled_date.isoformat(),
                    message.status.value,
                    message.opens,
                    message.clicks,
                    message.bounced,
                    message.replied
                )
                
                self.db.execute_query(message_query, message_params)
            
            return True
        
        except Exception as e:
            print(f"❌ Error storing campaign: {e}")
            return False
    
    def get_injection_stats(self) -> Dict[str, Any]:
        """
        Get campaign injection statistics
        
        Returns:
            Dictionary with injection statistics
        """
        try:
            # Get campaign counts by status
            status_query = """
            SELECT campaign_status, COUNT(*) as count
            FROM campaigns
            GROUP BY campaign_status
            """
            
            status_rows = self.db.execute_query(status_query)
            status_stats = {row['campaign_status']: row['count'] for row in status_rows}
            
            # Get recent injection activity
            recent_query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM campaigns
            WHERE created_at >= date('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """
            
            recent_rows = self.db.execute_query(recent_query)
            recent_activity = {row['date']: row['count'] for row in recent_rows}
            
            # Get quality score distribution
            quality_query = """
            SELECT 
                CASE 
                    WHEN engagement_score >= 90 THEN 'Excellent'
                    WHEN engagement_score >= 80 THEN 'Good'
                    WHEN engagement_score >= 70 THEN 'Acceptable'
                    ELSE 'Poor'
                END as quality_tier,
                COUNT(*) as count
            FROM campaigns
            GROUP BY quality_tier
            """
            
            quality_rows = self.db.execute_query(quality_query)
            quality_distribution = {row['quality_tier']: row['count'] for row in quality_rows}
            
            return {
                'total_campaigns': sum(status_stats.values()),
                'by_status': status_stats,
                'recent_activity': recent_activity,
                'quality_distribution': quality_distribution,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"❌ Error getting injection stats: {e}")
            return {'error': str(e)}
    
    def get_campaign_details(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific campaign
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Dictionary with campaign details or None if not found
        """
        try:
            # Get campaign info
            campaign_query = """
            SELECT * FROM campaigns WHERE campaign_id = ?
            """
            
            campaign_rows = self.db.execute_query(campaign_query, (campaign_id,))
            if not campaign_rows:
                return None
            
            campaign_row = campaign_rows[0]
            
            # Get campaign messages
            messages_query = """
            SELECT * FROM campaign_messages 
            WHERE campaign_id = ? 
            ORDER BY message_number ASC
            """
            
            message_rows = self.db.execute_query(messages_query, (campaign_id,))
            
            # Get queue status
            queue_query = """
            SELECT message_number, status, scheduled_for, attempts, error_message
            FROM message_queue
            WHERE campaign_id = ?
            ORDER BY message_number ASC
            """
            
            queue_rows = self.db.execute_query(queue_query, (campaign_id,))
            
            return {
                'campaign_info': dict(campaign_row),
                'messages': [dict(row) for row in message_rows],
                'queue_status': [dict(row) for row in queue_rows],
                'retrieved_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"❌ Error getting campaign details: {e}")
            return None