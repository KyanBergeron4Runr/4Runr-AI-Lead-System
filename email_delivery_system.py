#!/usr/bin/env python3
"""
4Runr AI Lead System - Email Delivery System
Handles actual email sending via SMTP and Microsoft Graph
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import sqlite3
import requests

class EmailDeliverySystem:
    def __init__(self):
        load_dotenv()
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Microsoft Graph settings
        self.graph_client_id = os.getenv('MS_GRAPH_CLIENT_ID')
        self.graph_client_secret = os.getenv('MS_GRAPH_CLIENT_SECRET')
        self.graph_tenant_id = os.getenv('MS_GRAPH_TENANT_ID')
        self.graph_sender_email = os.getenv('MS_GRAPH_SENDER_EMAIL')
        
        self.primary_db = "4runr-lead-scraper/data/leads.db"
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def get_pending_campaigns(self):
        """Get campaigns ready for sending"""
        try:
            conn = sqlite3.connect(self.primary_db)
            cursor = conn.execute("""
                SELECT id, email, company, ai_message, engagement_status 
                FROM leads 
                WHERE ai_message IS NOT NULL 
                AND ai_message != '' 
                AND engagement_status = 'Auto-Send'
                AND date_messaged IS NULL
                LIMIT 10
            """)
            
            campaigns = []
            for row in cursor.fetchall():
                campaigns.append({
                    'lead_id': row[0],
                    'email': row[1],
                    'company': row[2],
                    'message': row[3],
                    'status': row[4]
                })
            
            conn.close()
            return campaigns
            
        except Exception as e:
            self.log(f"❌ Error getting pending campaigns: {str(e)}")
            return []
    
    def send_via_smtp(self, to_email, subject, message_body):
        """Send email via SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                self.log("❌ SMTP credentials not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message_body, 'plain'))
            
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
    
    def send_via_graph(self, to_email, subject, message_body):
        """Send email via Microsoft Graph API"""
        try:
            if not all([self.graph_client_id, self.graph_client_secret, self.graph_tenant_id]):
                self.log("❌ Microsoft Graph credentials not configured")
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
                self.log(f"❌ Failed to get Graph token: {token_response.text}")
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
                        "content": message_body
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
            if send_response.status_code == 202:
                return True
            else:
                self.log(f"❌ Graph send failed: {send_response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Graph send failed: {str(e)}")
            return False
    
    def send_campaign(self, campaign):
        """Send a single campaign"""
        to_email = campaign['email']
        company = campaign['company']
        message = campaign['message']
        
        subject = f"Partnership Opportunity - {company}"
        
        # Try Microsoft Graph first, fallback to SMTP
        success = False
        method = ""
        
        if self.graph_client_id:
            success = self.send_via_graph(to_email, subject, message)
            method = "Microsoft Graph"
        
        if not success and self.smtp_username:
            success = self.send_via_smtp(to_email, subject, message)
            method = "SMTP"
        
        if success:
            self.log(f"✅ Email sent to {to_email} via {method}")
            self.mark_campaign_sent(campaign['lead_id'])
        else:
            self.log(f"❌ Failed to send email to {to_email}")
            self.mark_campaign_failed(campaign['lead_id'])
        
        return success
    
    def mark_campaign_sent(self, lead_id):
        """Mark campaign as sent in database"""
        try:
            conn = sqlite3.connect(self.primary_db)
            conn.execute("""
                UPDATE leads 
                SET date_messaged = ?, engagement_status = 'Sent'
                WHERE id = ?
            """, (datetime.now().isoformat(), lead_id))
            conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"❌ Error marking campaign sent: {str(e)}")
    
    def mark_campaign_failed(self, lead_id):
        """Mark campaign as failed in database"""
        try:
            conn = sqlite3.connect(self.primary_db)
            conn.execute("""
                UPDATE leads 
                SET engagement_status = 'Send Failed'
                WHERE id = ?
            """, (lead_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"❌ Error marking campaign failed: {str(e)}")
    
    def process_email_queue(self, max_emails=5):
        """Process pending email campaigns"""
        self.log("📧 Processing email queue...")
        
        campaigns = self.get_pending_campaigns()
        if not campaigns:
            self.log("   ℹ️ No pending campaigns found")
            return True
        
        self.log(f"   📋 Found {len(campaigns)} pending campaigns")
        
        sent_count = 0
        failed_count = 0
        
        for i, campaign in enumerate(campaigns[:max_emails]):
            self.log(f"   📤 Sending {i+1}/{min(len(campaigns), max_emails)}: {campaign['email']}")
            
            if self.send_campaign(campaign):
                sent_count += 1
            else:
                failed_count += 1
            
            # Rate limiting - wait between sends
            if i < len(campaigns) - 1:
                import time
                time.sleep(2)  # 2 second delay between emails
        
        self.log(f"✅ Email processing complete: {sent_count} sent, {failed_count} failed")
        return sent_count > 0
    
    def test_email_configuration(self):
        """Test email configuration"""
        self.log("🧪 Testing email configuration...")
        
        # Test SMTP
        if self.smtp_username and self.smtp_password:
            try:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.quit()
                self.log("   ✅ SMTP configuration valid")
            except Exception as e:
                self.log(f"   ❌ SMTP configuration failed: {str(e)}")
        else:
            self.log("   ⚠️ SMTP not configured")
        
        # Test Microsoft Graph
        if all([self.graph_client_id, self.graph_client_secret, self.graph_tenant_id]):
            try:
                token_url = f"https://login.microsoftonline.com/{self.graph_tenant_id}/oauth2/v2.0/token"
                token_data = {
                    'client_id': self.graph_client_id,
                    'client_secret': self.graph_client_secret,
                    'scope': 'https://graph.microsoft.com/.default',
                    'grant_type': 'client_credentials'
                }
                
                response = requests.post(token_url, data=token_data)
                if response.status_code == 200:
                    self.log("   ✅ Microsoft Graph configuration valid")
                else:
                    self.log(f"   ❌ Microsoft Graph configuration failed: {response.text}")
            except Exception as e:
                self.log(f"   ❌ Microsoft Graph test failed: {str(e)}")
        else:
            self.log("   ⚠️ Microsoft Graph not configured")

def main():
    import sys
    
    delivery_system = EmailDeliverySystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--test":
            delivery_system.test_email_configuration()
        elif command == "--send":
            max_emails = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            delivery_system.process_email_queue(max_emails)
        elif command == "--queue":
            campaigns = delivery_system.get_pending_campaigns()
            print(f"Pending campaigns: {len(campaigns)}")
            for campaign in campaigns:
                print(f"  - {campaign['email']} ({campaign['company']})")
        else:
            print("Usage: python email_delivery_system.py [--test|--send [count]|--queue]")
    else:
        # Default: process queue
        delivery_system.process_email_queue()

if __name__ == "__main__":
    main()