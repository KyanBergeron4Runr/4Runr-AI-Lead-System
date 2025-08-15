#!/usr/bin/env python3
"""
Simple Email Sender for Testing

Sends test emails using the Microsoft Graph API configuration
"""

import sys
import os
import requests
import argparse
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent / "4runr-outreach-system"))

from shared.config import config

def get_graph_access_token():
    """Get Microsoft Graph access token"""
    try:
        graph_config = {
            'client_id': config.get('MS_GRAPH_CLIENT_ID'),
            'client_secret': config.get('MS_GRAPH_CLIENT_SECRET'),
            'tenant_id': config.get('MS_GRAPH_TENANT_ID'),
            'sender_email': config.get('MS_GRAPH_SENDER_EMAIL')
        }
        
        if not all(graph_config.values()):
            print("❌ Microsoft Graph configuration not available")
            return None, None
        
        url = f"https://login.microsoftonline.com/{graph_config['tenant_id']}/oauth2/v2.0/token"
        
        data = {
            'client_id': graph_config['client_id'],
            'client_secret': graph_config['client_secret'],
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            return response.json()['access_token'], graph_config['sender_email']
        else:
            print(f"❌ Failed to get access token: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        return None, None

def send_test_email(access_token, sender_email, recipient_email, subject, body):
    """Send test email using Microsoft Graph API"""
    try:
        url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
        
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
                            "address": recipient_email
                        }
                    }
                ]
            }
        }
        
        response = requests.post(url, headers=headers, json=email_data)
        
        if response.status_code == 202:
            return True
        else:
            print(f"❌ Microsoft Graph API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def send_test_batch():
    """Send test batch of emails"""
    
    print("📧 Simple Email Sender - Test Batch")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get access token
    access_token, sender_email = get_graph_access_token()
    
    if not access_token:
        print("❌ Cannot send emails without access token")
        return False
    
    print(f"✅ Got access token for {sender_email}")
    
    # Test messages (simulating the generated messages)
    test_messages = [
        {
            'name': 'Sarah Mitchell',
            'company': 'PulseNova',
            'subject': 'Strategic Partnership Opportunity',
            'body': '''Sarah, not many know about us — and we like it that way. At 4Runr, we are selective about who we partner with, and for a good reason. Our strategic AI solutions quietly amplify businesses, creating an edge that our clients would rather keep under wraps. Are you prepared to unlock the unadvertised potential that could redefine PulseNova's trajectory? Let's explore what 4Runr could mean for you.'''
        },
        {
            'name': 'David Chen',
            'company': 'BrightForge',
            'subject': 'Strategic Partnership Opportunity',
            'body': '''Hello David,
You may not have heard of us - that's by design. We're 4Runr, the secret weapon behind some of the most successful businesses. Our work is not advertised, it's quietly transforming operations, optimizing efficiency and boosting bottom lines.

We're selective about who we partner with, but we see a potential alignment with BrightForge. Are you ready to uncover the strategic advantage that others would rather keep hidden?

Let's explore this further.
Best,
[Your Name]'''
        },
        {
            'name': 'Emma Rodriguez',
            'company': 'TechFlow',
            'subject': 'Strategic Partnership Opportunity',
            'body': '''Hi Emma,
Ever wondered how behind-the-scenes efficiency could power TechFlow's next leap? We've done it for others, and we can do it for you. Intrigued? Let's connect.

– 4Runr Team'''
        }
    ]
    
    recipient_email = "kyanberg@outlook.com"
    results = []
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Sending email to {message['name']} at {message['company']}")
        print(f"   📧 To: {recipient_email}")
        print(f"   📋 Subject: {message['subject']}")
        
        success = send_test_email(
            access_token=access_token,
            sender_email=sender_email,
            recipient_email=recipient_email,
            subject=message['subject'],
            body=message['body']
        )
        
        if success:
            print(f"   ✅ Email sent successfully")
            results.append({'name': message['name'], 'success': True})
        else:
            print(f"   ❌ Failed to send email")
            results.append({'name': message['name'], 'success': False})
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 EMAIL SENDING SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in results if r.get('success'))
    print(f"✅ Emails processed: {len(results)}")
    print(f"📧 Successfully sent: {successful}")
    print(f"❌ Failed: {len(results) - successful}")
    
    if successful > 0:
        print(f"\n📬 Successfully sent {successful} emails to {recipient_email}")
        print("   Check your inbox for the test messages!")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return successful == len(results)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Simple Email Sender')
    parser.add_argument('--batch-size', type=int, default=3, help='Number of emails to send')
    
    args = parser.parse_args()
    
    # Send test batch
    success = send_test_batch()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)