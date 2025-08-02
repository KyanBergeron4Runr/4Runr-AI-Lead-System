#!/usr/bin/env python3
"""
Comprehensive Outreach Agent
Sends personalized emails to enriched leads using Microsoft Graph or SMTP
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('outreach-agent')

class OutreachAgent:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / "shared"
        
        # Microsoft Graph configuration
        self.ms_graph_client_id = os.getenv('MS_GRAPH_CLIENT_ID')
        self.ms_graph_client_secret = os.getenv('MS_GRAPH_CLIENT_SECRET')
        self.ms_graph_tenant_id = os.getenv('MS_GRAPH_TENANT_ID')
        self.sender_email = os.getenv('MS_GRAPH_SENDER_EMAIL')
        
        # OpenAI for message generation
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
        
        # SMTP fallback configuration
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        logger.info("🚀 Outreach Agent initialized")
        logger.info(f"📧 Primary sender: {self.sender_email}")
        
        if self.ms_graph_client_id:
            logger.info("✅ Microsoft Graph configured")
        if self.smtp_host:
            logger.info("✅ SMTP fallback configured")
    
    def get_access_token(self):
        """Get Microsoft Graph access token"""
        if not all([self.ms_graph_client_id, self.ms_graph_client_secret, self.ms_graph_tenant_id]):
            logger.error("❌ Missing Microsoft Graph credentials")
            return None
        
        try:
            url = f"https://login.microsoftonline.com/{self.ms_graph_tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.ms_graph_client_id,
                'client_secret': self.ms_graph_client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                token = response.json()['access_token']
                logger.info("✅ Microsoft Graph access token obtained")
                return token
            else:
                logger.error(f"❌ Failed to get access token: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting access token: {str(e)}")
            return None
    
    def generate_personalized_message(self, lead):
        """Generate a personalized message using OpenAI"""
        if not self.openai_api_key:
            return self.get_fallback_message(lead)
        
        try:
            name = lead.get('full_name', 'there')
            first_name = name.split()[0] if name != 'there' else 'there'
            company = lead.get('company', 'your company')
            title = lead.get('title', 'your role')
            
            prompt = f"""Write a professional, personalized cold outreach email for:
            
Name: {first_name}
Company: {company}
Title: {title}

The email should:
- Be from Kyan Bergeron at 4Runr Tech
- Mention our AI automation solutions
- Be concise (under 100 words)
- Include a clear call to action
- Sound natural and not overly salesy
- Reference their specific role/company

Format as a complete email with subject line."""
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional business development expert writing personalized outreach emails."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            message = response.choices[0].message.content.strip()
            logger.info(f"✅ Generated personalized message for {first_name}")
            return message
            
        except Exception as e:
            logger.warning(f"⚠️ OpenAI message generation failed: {str(e)}")
            return self.get_fallback_message(lead)
    
    def get_fallback_message(self, lead):
        """Get a fallback message template"""
        name = lead.get('full_name', 'there')
        first_name = name.split()[0] if name != 'there' else 'there'
        company = lead.get('company', 'your company')
        title = lead.get('title', 'your role')
        
        subject = f"AI Automation Solutions for {company}"
        
        body = f"""Hi {first_name},

I came across your profile and was impressed by your work as {title} at {company}.

At 4Runr Tech, we're helping Montreal businesses like yours streamline operations with AI automation. Our solutions typically help companies:

• Reduce manual tasks by 40-60%
• Improve data accuracy and insights
• Scale operations without proportional headcount increases

Would you be open to a brief 15-minute call to discuss how this might benefit {company}?

Best regards,
Kyan Bergeron
Founder, 4Runr Tech
KyanBergeron@4runrtech.com"""

        return f"Subject: {subject}\n\n{body}"
    
    def send_email_via_graph(self, access_token, recipient_email, subject, message_content):
        """Send email using Microsoft Graph API"""
        try:
            url = f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "Text",
                        "content": message_content
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": recipient_email
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=email_data, timeout=30)
            
            if response.status_code == 202:  # Accepted
                logger.info(f"✅ Email sent via Microsoft Graph to {recipient_email}")
                return True
            else:
                logger.error(f"❌ Microsoft Graph send failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Microsoft Graph send error: {str(e)}")
            return False
    
    def send_email_via_smtp(self, recipient_email, subject, message_content):
        """Send email using SMTP as fallback"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
                logger.error("❌ SMTP credentials not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message_content, 'plain'))
            
            server = smtplib.SMTP(self.smtp_host, 587)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_username, recipient_email, text)
            server.quit()
            
            logger.info(f"✅ Email sent via SMTP to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP send error: {str(e)}")
            return False
    
    def send_outreach_email(self, lead):
        """Send outreach email to a lead"""
        email = lead.get('email')
        if not email:
            logger.warning(f"⚠️ No email for {lead.get('full_name', 'Unknown')}")
            return False
        
        name = lead.get('full_name', 'Unknown')
        logger.info(f"📧 Sending outreach email to {name} ({email})")
        
        # Generate personalized message
        full_message = self.generate_personalized_message(lead)
        
        # Extract subject and body
        if "Subject:" in full_message:
            lines = full_message.split('\n')
            subject_line = lines[0].replace('Subject:', '').strip()
            body = '\n'.join(lines[2:]).strip()  # Skip subject and empty line
        else:
            subject_line = f"AI Solutions for {lead.get('company', 'Your Business')}"
            body = full_message
        
        # Try Microsoft Graph first
        access_token = self.get_access_token()
        if access_token:
            success = self.send_email_via_graph(access_token, email, subject_line, body)
            if success:
                return True
        
        # Fallback to SMTP
        logger.info("🔄 Falling back to SMTP...")
        return self.send_email_via_smtp(email, subject_line, body)
    
    def get_leads_ready_for_outreach(self):
        """Get leads that are ready for outreach"""
        raw_leads_file = self.shared_dir / "raw_leads.json"
        
        if not raw_leads_file.exists():
            logger.warning("⚠️ No raw_leads.json found")
            return []
        
        try:
            with open(raw_leads_file, 'r', encoding='utf-8') as f:
                leads = json.load(f)
            
            # Filter leads ready for outreach
            ready_leads = []
            for lead in leads:
                if (lead.get('enriched') and 
                    lead.get('email') and 
                    not lead.get('outreach_sent')):
                    ready_leads.append(lead)
            
            logger.info(f"📋 Found {len(ready_leads)} leads ready for outreach")
            return ready_leads
            
        except Exception as e:
            logger.error(f"❌ Error reading leads: {str(e)}")
            return []
    
    def update_lead_outreach_status(self, lead, success):
        """Update lead with outreach status"""
        lead['outreach_sent'] = success
        lead['outreach_sent_at'] = datetime.now().isoformat()
        lead['outreach_method'] = 'email'
        
        if success:
            lead['engagement_method'] = 'email_sent'
            lead['ready_for_followup'] = True
    
    def save_leads(self, leads):
        """Save updated leads back to file"""
        raw_leads_file = self.shared_dir / "raw_leads.json"
        
        try:
            with open(raw_leads_file, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            
            logger.info("💾 Updated leads saved")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving leads: {str(e)}")
            return False
    
    def run_outreach_campaign(self, max_emails=5):
        """Run outreach campaign for ready leads"""
        logger.info(f"🚀 Starting outreach campaign (max {max_emails} emails)")
        
        # Get leads ready for outreach
        leads = self.get_leads_ready_for_outreach()
        
        if not leads:
            logger.info("✅ No leads ready for outreach")
            return
        
        # Limit to max_emails
        leads_to_contact = leads[:max_emails]
        logger.info(f"📧 Sending outreach to {len(leads_to_contact)} leads")
        
        sent_count = 0
        failed_count = 0
        
        for i, lead in enumerate(leads_to_contact, 1):
            try:
                logger.info(f"🔄 Processing lead {i}/{len(leads_to_contact)}")
                
                # Send outreach email
                success = self.send_outreach_email(lead)
                
                # Update lead status
                self.update_lead_outreach_status(lead, success)
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting between emails
                if i < len(leads_to_contact):
                    time.sleep(30)  # 30 seconds between emails
                
            except Exception as e:
                logger.error(f"❌ Error processing lead {i}: {str(e)}")
                failed_count += 1
        
        # Save updated leads
        self.save_leads(leads)
        
        # Summary
        logger.info(f"🎯 Outreach campaign complete:")
        logger.info(f"   ✅ Sent: {sent_count}")
        logger.info(f"   ❌ Failed: {failed_count}")

def main():
    """Main function"""
    logger.info("🚀 Starting Outreach Agent...")
    
    agent = OutreachAgent()
    agent.run_outreach_campaign(max_emails=3)  # Start with 3 emails for testing
    
    logger.info("✅ Outreach Agent completed")

if __name__ == "__main__":
    main()