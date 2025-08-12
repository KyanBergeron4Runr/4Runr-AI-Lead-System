#!/usr/bin/env python3
"""
Working email sender using Microsoft Graph API with proper error handling and debugging.
"""

import sys
import json
import requests
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def get_access_token_detailed(client_id, client_secret, tenant_id):
    """Get access token with detailed error reporting."""
    print(f"🔑 Getting access token...")
    print(f"   Client ID: {client_id}")
    print(f"   Tenant ID: {tenant_id}")
    
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }
    
    print(f"   Token URL: {url}")
    
    response = requests.post(url, data=data)
    
    print(f"   Response Status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print("✅ Access token obtained successfully")
        return token_data['access_token']
    else:
        print(f"❌ Failed to get access token")
        print(f"   Error: {response.text}")
        raise Exception(f"Failed to get access token: {response.text}")

def check_permissions(access_token, sender_email):
    """Check what permissions the app has."""
    print(f"\n🔍 Checking app permissions...")
    
    # Try to get user info first
    url = f"https://graph.microsoft.com/v1.0/users/{sender_email}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    print(f"   User info check: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Can access user: {user_data.get('displayName', 'Unknown')}")
        return True
    else:
        print(f"❌ Cannot access user: {response.text}")
        return False

def send_email_with_debugging(access_token, sender_email, recipient_email, subject, message_content):
    """Send email with detailed debugging."""
    print(f"\n📧 Attempting to send email...")
    print(f"   From: {sender_email}")
    print(f"   To: {recipient_email}")
    print(f"   Subject: {subject}")
    
    # Try different API endpoints
    endpoints_to_try = [
        f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail",
        f"https://graph.microsoft.com/v1.0/me/sendMail",
        f"https://graph.microsoft.com/beta/users/{sender_email}/sendMail"
    ]
    
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
    
    for i, url in enumerate(endpoints_to_try):
        print(f"\n   Trying endpoint {i+1}: {url}")
        
        response = requests.post(url, headers=headers, json=email_data)
        print(f"   Response: {response.status_code}")
        
        if response.status_code == 202:
            print("✅ Email sent successfully!")
            return True
        elif response.status_code == 200:
            print("✅ Email sent successfully!")
            return True
        else:
            print(f"   Error: {response.text}")
            
            # Parse error for specific issues
            try:
                error_data = response.json()
                error_code = error_data.get('error', {}).get('code', 'Unknown')
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                
                print(f"   Error Code: {error_code}")
                print(f"   Error Message: {error_message}")
                
                if 'Forbidden' in error_code or 'AccessDenied' in error_code:
                    print("   💡 This looks like a permissions issue")
                elif 'Unauthorized' in error_code:
                    print("   💡 This looks like an authentication issue")
                    
            except:
                pass
    
    return False

def try_alternative_approach(access_token, sender_email, recipient_email, subject, message_content):
    """Try alternative approaches if direct sending fails."""
    print(f"\n🔄 Trying alternative approaches...")
    
    # Try creating a draft first
    print("   Attempting to create draft...")
    
    url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/messages"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    draft_data = {
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
    
    response = requests.post(url, headers=headers, json=draft_data)
    print(f"   Draft creation: {response.status_code}")
    
    if response.status_code == 201:
        draft_data = response.json()
        draft_id = draft_data['id']
        print(f"✅ Draft created: {draft_id}")
        
        # Try to send the draft
        send_url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/messages/{draft_id}/send"
        send_response = requests.post(send_url, headers=headers)
        
        print(f"   Send draft: {send_response.status_code}")
        
        if send_response.status_code == 202:
            print("✅ Draft sent successfully!")
            return True
        else:
            print(f"   Send error: {send_response.text}")
    else:
        print(f"   Draft error: {response.text}")
    
    return False

def main():
    """Main function to test email sending."""
    print("📧 4Runr Email Sender - Debugging Mode")
    print("=" * 60)
    
    try:
        # Load configuration
        sys.path.append('4runr-outreach-system')
        from shared.config import config
        
        # Get Microsoft Graph configuration
        client_id = config.get('MS_GRAPH_CLIENT_ID')
        client_secret = config.get('MS_GRAPH_CLIENT_SECRET')
        tenant_id = config.get('MS_GRAPH_TENANT_ID')
        sender_email = config.get('MS_GRAPH_SENDER_EMAIL')
        
        print(f"📋 Configuration:")
        print(f"   Client ID: {client_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Sender: {sender_email}")
        print(f"   Secret: {'*' * len(client_secret) if client_secret else 'NOT SET'}")
        
        if not all([client_id, client_secret, tenant_id, sender_email]):
            print("❌ Missing required configuration!")
            return False
        
        # Get access token
        access_token = get_access_token_detailed(client_id, client_secret, tenant_id)
        
        # Check permissions
        can_access_user = check_permissions(access_token, sender_email)
        
        # Prepare message
        recipient = "kyanberg@outlook.com"
        subject = "🤖 Test: AI-Generated Outreach Message - 4Runr Partnership"
        message_content = """Hi Kyan,

I've been following 4Runr's work in AI-powered business automation and I'm impressed by your approach to helping companies streamline their operations through intelligent solutions.

As a founder in the AI automation space, you're likely focused on scaling your lead generation systems and optimizing client acquisition processes. Your expertise in custom automation systems and strategic AI consulting puts you at the forefront of this rapidly evolving industry.

I'd love to explore how we might collaborate or share insights about emerging trends in AI-driven business automation. Would you be open to a brief conversation about your current priorities and the challenges you're seeing in the market?

Best regards,
4Runr Team

---
This message was generated by the 4Runr Autonomous Outreach System
Website analyzed: https://4runrtech.com/
Generated on: 2025-07-29
Method: Microsoft Graph API (Debugging Mode)"""
        
        # Try to send email
        success = send_email_with_debugging(access_token, sender_email, recipient, subject, message_content)
        
        if not success:
            print("\n🔄 Primary method failed, trying alternatives...")
            success = try_alternative_approach(access_token, sender_email, recipient, subject, message_content)
        
        if success:
            print(f"\n🎉 SUCCESS!")
            print(f"Email sent to {recipient}")
            print(f"Check your inbox!")
        else:
            print(f"\n❌ All sending methods failed")
            print(f"\n💡 Possible solutions:")
            print(f"   1. Check Azure AD app permissions (Mail.Send)")
            print(f"   2. Grant admin consent for the app")
            print(f"   3. Verify the app has delegated or application permissions")
            print(f"   4. Check if the sender email is correct")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)