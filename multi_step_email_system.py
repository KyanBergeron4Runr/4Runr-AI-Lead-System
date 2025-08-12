#!/usr/bin/env python3
"""
Multi-Step Email Campaign System
Sends campaigns in increments (Day 0, Day 3, Day 7) and tracks responses
"""

import os
import sqlite3
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

class MultiStepEmailSystem:
    def __init__(self):
        load_dotenv()
        self.campaign_db = "4runr-outreach-system/campaign_system/campaigns.db"
        self.leads_db = "4runr-lead-scraper/data/leads.db"
        
        # Email configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Microsoft Graph settings
        self.graph_client_id = os.getenv('MS_GRAPH_CLIENT_ID')
        self.graph_client_secret = os.getenv('MS_GRAPH_CLIENT_SECRET')
        self.graph_tenant_id = os.getenv('MS_GRAPH_TENANT_ID')
        self.graph_sender_email = os.getenv('MS_GRAPH_SENDER_EMAIL')
        
        # Airtable settings
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
        self.airtable_table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def get_campaigns_ready_to_send(self):
        """Get campaigns with messages ready to send based on schedule"""
        try:
            conn = sqlite3.connect(self.campaign_db)
            
            # Get campaigns with messages that are scheduled and ready
            query = """
            SELECT 
                c.campaign_id,
                c.lead_id,
                c.company,
                cm.message_number,
                cm.message_type,
                cm.subject,
                cm.body,
                cm.scheduled_date
            FROM campaigns c
            JOIN campaign_messages cm ON c.campaign_id = cm.campaign_id
            WHERE c.campaign_status = 'active'
            AND cm.status = 'scheduled'
            AND datetime(cm.scheduled_date) <= datetime('now')
            AND c.response_detected = 0
            ORDER BY cm.scheduled_date ASC
            LIMIT 10
            """
            
            # Connect to leads database for email info
            leads_conn = sqlite3.connect(self.leads_db)
            
            cursor = conn.execute(query)
            campaigns = []
            
            for row in cursor.fetchall():
                campaign_id, lead_id, company, message_number, message_type, subject, body, scheduled_date = row
                
                # Get email from leads database
                lead_cursor = leads_conn.execute("SELECT email, name, airtable_id FROM leads WHERE id = ?", (lead_id,))
                lead_row = lead_cursor.fetchone()
                
                if lead_row:
                    email, name, airtable_id = lead_row
                else:
                    email, name, airtable_id = None, None, None
                
                if email:
                    campaigns.append({
                        'campaign_id': campaign_id,
                        'lead_id': lead_id,
                        'company': company,
                        'message_number': message_number,
                        'message_type': message_type,
                        'subject': subject,
                        'body': body,
                        'scheduled_date': scheduled_date,
                        'email': email,
                        'name': name,
                        'airtable_id': airtable_id
                    })
            
            conn.close()
            leads_conn.close()
            return campaigns
            
        except Exception as e:
            self.log(f"❌ Error getting campaigns ready to send: {str(e)}")
            return []
    
    def send_campaign_message(self, campaign):
        """Send a single campaign message"""
        try:
            to_email = campaign['email']
            subject = campaign['subject']
            body = campaign['body']
            
            # Try Microsoft Graph first, fallback to SMTP
            success = False
            method = ""
            
            if self.graph_client_id:
                success = self.send_via_graph(to_email, subject, body)
                method = "Microsoft Graph"
            
            if not success and self.smtp_username:
                success = self.send_via_smtp(to_email, subject, body)
                method = "SMTP"
            
            if success:
                self.log(f"✅ Sent {campaign['message_type']} message to {to_email} via {method}")
                self.mark_message_sent(campaign)
                self.update_airtable_status(campaign, 'sent')
                return True
            else:
                self.log(f"❌ Failed to send message to {to_email}")
                self.mark_message_failed(campaign)
                return False
                
        except Exception as e:
            self.log(f"❌ Error sending campaign message: {str(e)}")
            return False
    
    def send_via_smtp(self, to_email, subject, body):
        """Send email via SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_username, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            self.log(f"❌ SMTP send failed: {str(e)}")
            return False
    
    def send_via_graph(self, to_email, subject, body):
        """Send email via Microsoft Graph API"""
        try:
            if not all([self.graph_client_id, self.graph_client_secret, self.graph_tenant_id]):
                return False
            
            # Get access token
            token_url = f"https://login.microsoftonline.com/{self.graph_tenant_id}/oauth2/v2.0/token"
            token_data = {
                'client_id': self.graph_client_id,
                'client_secret': self.graph_client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            token_response = requests.post(token_url, data=token_data)
            if token_response.status_code != 200:
                return False
            
            access_token = token_response.json()['access_token']
            
            # Send email
            send_url = f"https://graph.microsoft.com/v1.0/users/{self.graph_sender_email}/sendMail"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "Text",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                }
            }
            
            send_response = requests.post(send_url, headers=headers, json=email_data)
            return send_response.status_code == 202
                
        except Exception as e:
            self.log(f"❌ Graph send failed: {str(e)}")
            return False
    
    def mark_message_sent(self, campaign):
        """Mark message as sent and schedule next message"""
        try:
            conn = sqlite3.connect(self.campaign_db)
            
            # Update current message status
            conn.execute("""
                UPDATE campaign_messages 
                SET status = 'sent', sent_date = ?
                WHERE campaign_id = ? AND message_number = ?
            """, (datetime.now().isoformat(), campaign['campaign_id'], campaign['message_number']))
            
            # Schedule next message if this isn't the last one
            if campaign['message_number'] < 3:
                next_message_number = campaign['message_number'] + 1
                
                # Calculate next send date based on message type
                if next_message_number == 2:  # Proof message (Day 3)
                    next_date = datetime.now() + timedelta(days=3)
                elif next_message_number == 3:  # FOMO message (Day 7)
                    next_date = datetime.now() + timedelta(days=4)  # 4 more days after proof
                
                conn.execute("""
                    UPDATE campaign_messages 
                    SET scheduled_date = ?
                    WHERE campaign_id = ? AND message_number = ?
                """, (next_date.isoformat(), campaign['campaign_id'], next_message_number))
                
                self.log(f"📅 Scheduled message {next_message_number} for {next_date.strftime('%Y-%m-%d')}")
            else:
                # Mark campaign as completed
                conn.execute("""
                    UPDATE campaigns 
                    SET campaign_status = 'completed', updated_at = ?
                    WHERE campaign_id = ?
                """, (datetime.now().isoformat(), campaign['campaign_id']))
                
                self.log(f"✅ Campaign completed for {campaign['company']}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log(f"❌ Error marking message sent: {str(e)}")
    
    def mark_message_failed(self, campaign):
        """Mark message as failed"""
        try:
            conn = sqlite3.connect(self.campaign_db)
            
            conn.execute("""
                UPDATE campaign_messages 
                SET status = 'failed', error_message = 'Send failed'
                WHERE campaign_id = ? AND message_number = ?
            """, (campaign['campaign_id'], campaign['message_number']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log(f"❌ Error marking message failed: {str(e)}")
    
    def update_airtable_status(self, campaign, status):
        """Update Airtable with email status"""
        try:
            if not campaign.get('airtable_id') or not self.airtable_api_key:
                return
            
            # Update Airtable record
            url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_name}/{campaign['airtable_id']}"
            headers = {
                'Authorization': f'Bearer {self.airtable_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Determine status field based on message type
            if status == 'sent':
                if campaign['message_number'] == 1:
                    field_name = 'Hook Message Sent'
                elif campaign['message_number'] == 2:
                    field_name = 'Proof Message Sent'
                elif campaign['message_number'] == 3:
                    field_name = 'FOMO Message Sent'
                else:
                    field_name = 'Email Status'
                
                data = {
                    'fields': {
                        field_name: True,
                        'Last Contact Date': datetime.now().strftime('%Y-%m-%d'),
                        'Campaign Status': f"{campaign['message_type'].title()} Sent"
                    }
                }
            elif status == 'replied':
                data = {
                    'fields': {
                        'Replied': True,
                        'Reply Date': datetime.now().strftime('%Y-%m-%d'),
                        'Campaign Status': 'Replied - Follow Up'
                    }
                }
            
            response = requests.patch(url, headers=headers, json=data)
            if response.status_code == 200:
                self.log(f"✅ Updated Airtable status for {campaign['company']}")
            else:
                self.log(f"⚠️ Failed to update Airtable: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Error updating Airtable: {str(e)}")
    
    def check_for_replies(self):
        """Check for email replies and pause campaigns"""
        # This would integrate with email monitoring
        # For now, we'll implement a simple manual check
        self.log("📧 Checking for email replies...")
        
        # TODO: Implement IMAP checking for replies
        # When reply detected, mark campaign as responded
        pass
    
    def mark_campaign_replied(self, campaign_id, reply_email):
        """Mark campaign as replied and pause further messages"""
        try:
            conn = sqlite3.connect(self.campaign_db)
            
            # Mark campaign as responded
            conn.execute("""
                UPDATE campaigns 
                SET response_detected = 1, campaign_status = 'responded', updated_at = ?
                WHERE campaign_id = ?
            """, (datetime.now().isoformat(), campaign_id))
            
            # Cancel any pending messages
            conn.execute("""
                UPDATE campaign_messages 
                SET status = 'cancelled'
                WHERE campaign_id = ? AND status = 'scheduled'
            """, (campaign_id,))
            
            conn.commit()
            conn.close()
            
            # Update Airtable
            campaign_info = self.get_campaign_info(campaign_id)
            if campaign_info:
                self.update_airtable_status(campaign_info, 'replied')
            
            self.log(f"✅ Campaign {campaign_id} marked as replied")
            
        except Exception as e:
            self.log(f"❌ Error marking campaign replied: {str(e)}")
    
    def get_campaign_info(self, campaign_id):
        """Get campaign information"""
        try:
            conn = sqlite3.connect(self.campaign_db)
            cursor = conn.execute("""
                SELECT campaign_id, lead_id, company
                FROM campaigns 
                WHERE campaign_id = ?
            """, (campaign_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'campaign_id': row[0],
                    'lead_id': row[1],
                    'company': row[2]
                }
            return None
            
        except Exception as e:
            self.log(f"❌ Error getting campaign info: {str(e)}")
            return None
    
    def process_email_campaigns(self, max_emails=5):
        """Process pending email campaigns"""
        self.log("📧 Processing multi-step email campaigns...")
        
        # Get campaigns ready to send
        campaigns = self.get_campaigns_ready_to_send()
        
        if not campaigns:
            self.log("   ℹ️ No campaigns ready to send")
            return {'sent': 0, 'failed': 0}
        
        self.log(f"   📋 Found {len(campaigns)} messages ready to send")
        
        sent_count = 0
        failed_count = 0
        
        for i, campaign in enumerate(campaigns[:max_emails]):
            self.log(f"   📤 Sending {i+1}/{min(len(campaigns), max_emails)}: {campaign['message_type']} to {campaign['email']}")
            
            if self.send_campaign_message(campaign):
                sent_count += 1
            else:
                failed_count += 1
            
            # Rate limiting - wait between sends
            if i < len(campaigns) - 1:
                import time
                time.sleep(3)  # 3 second delay between emails
        
        self.log(f"✅ Campaign processing complete: {sent_count} sent, {failed_count} failed")
        return {'sent': sent_count, 'failed': failed_count}
    
    def get_campaign_stats(self):
        """Get campaign statistics"""
        try:
            conn = sqlite3.connect(self.campaign_db)
            
            # Get campaign counts by status
            cursor = conn.execute("""
                SELECT campaign_status, COUNT(*) 
                FROM campaigns 
                GROUP BY campaign_status
            """)
            
            status_counts = dict(cursor.fetchall())
            
            # Get message stats
            cursor = conn.execute("""
                SELECT message_type, status, COUNT(*) 
                FROM campaign_messages 
                GROUP BY message_type, status
            """)
            
            message_stats = {}
            for message_type, status, count in cursor.fetchall():
                if message_type not in message_stats:
                    message_stats[message_type] = {}
                message_stats[message_type][status] = count
            
            # Get pending messages
            cursor = conn.execute("""
                SELECT COUNT(*) 
                FROM campaign_messages 
                WHERE status = 'scheduled' 
                AND datetime(scheduled_date) <= datetime('now')
            """)
            
            pending_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'campaign_status': status_counts,
                'message_stats': message_stats,
                'pending_messages': pending_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.log(f"❌ Error getting campaign stats: {str(e)}")
            return {'error': str(e)}

def main():
    import sys
    
    email_system = MultiStepEmailSystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--send":
            max_emails = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            result = email_system.process_email_campaigns(max_emails)
            print(f"Results: {result}")
        elif command == "--stats":
            stats = email_system.get_campaign_stats()
            print(json.dumps(stats, indent=2))
        elif command == "--check-replies":
            email_system.check_for_replies()
        elif command == "--mark-replied":
            if len(sys.argv) > 2:
                campaign_id = sys.argv[2]
                email_system.mark_campaign_replied(campaign_id, "manual")
        else:
            print("Usage: python multi_step_email_system.py [--send [count]|--stats|--check-replies|--mark-replied <campaign_id>]")
    else:
        # Default: process campaigns
        email_system.process_email_campaigns()

if __name__ == "__main__":
    main()