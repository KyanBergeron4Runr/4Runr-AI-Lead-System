#!/usr/bin/env python3
"""
Email Queue Sender

Sends emails from the campaign queue for testing
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent / "4runr-outreach-system"))
sys.path.append(str(Path(__file__).parent))

# Import campaign system components
try:
    from campaign_system.database.connection import get_database_connection
    from campaign_system.models.queue import MessageQueue, QueueStatus
    from campaign_system.delivery.email_sender import EmailSender
except ImportError as e:
    print(f"Campaign system components not available: {e}")
    print("This is expected if the campaign system is not fully set up")
    sys.exit(1)

def get_queued_messages(batch_size: int = 10):
    """Get messages from the queue ready for sending"""
    try:
        db = get_database_connection()
        
        # Get ready messages from queue
        query = """
        SELECT queue_id, campaign_id, lead_email, subject, message_content, 
               message_number, created_at, status
        FROM message_queue 
        WHERE status = 'ready' 
        ORDER BY created_at ASC 
        LIMIT ?
        """
        
        results = db.execute_query(query, (batch_size,))
        
        messages = []
        for row in results:
            messages.append({
                'queue_id': row[0],
                'campaign_id': row[1],
                'lead_email': row[2],
                'subject': row[3],
                'message_content': row[4],
                'message_number': row[5],
                'created_at': row[6],
                'status': row[7]
            })
        
        return messages
        
    except Exception as e:
        print(f"Error getting queued messages: {e}")
        return []

def send_batch_emails(batch_size: int = 3):
    """Send a batch of emails from the queue"""
    
    print("📧 Email Queue Sender")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get messages from queue
    messages = get_queued_messages(batch_size)
    
    if not messages:
        print("No messages found in queue ready for sending")
        return []
    
    print(f"📬 Found {len(messages)} messages ready for sending")
    
    # Initialize email sender
    try:
        email_sender = EmailSender()
    except Exception as e:
        print(f"❌ Failed to initialize email sender: {e}")
        return []
    
    results = []
    
    for i, message in enumerate(messages, 1):
        print(f"\n{i}. Sending email:")
        print(f"   📧 To: {message['lead_email']}")
        print(f"   📋 Subject: {message['subject']}")
        print(f"   🆔 Queue ID: {message['queue_id']}")
        print(f"   📅 Queued: {message['created_at']}")
        
        try:
            # Send the email
            success = email_sender.send_email(
                to_email=message['lead_email'],
                subject=message['subject'],
                body=message['message_content'],
                campaign_id=message['campaign_id']
            )
            
            if success:
                print(f"   ✅ Email sent successfully")
                
                # Update queue status
                db = get_database_connection()
                update_query = """
                UPDATE message_queue 
                SET status = 'sent', sent_at = datetime('now')
                WHERE queue_id = ?
                """
                db.execute_query(update_query, (message['queue_id'],))
                
                results.append({
                    'queue_id': message['queue_id'],
                    'lead_email': message['lead_email'],
                    'success': True
                })
            else:
                print(f"   ❌ Failed to send email")
                results.append({
                    'queue_id': message['queue_id'],
                    'lead_email': message['lead_email'],
                    'success': False,
                    'error': 'Send failed'
                })
                
        except Exception as e:
            print(f"   ❌ Error sending email: {str(e)}")
            results.append({
                'queue_id': message['queue_id'],
                'lead_email': message['lead_email'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 EMAIL SENDING SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in results if r.get('success'))
    print(f"✅ Emails processed: {len(results)}")
    print(f"📧 Successfully sent: {successful}")
    print(f"❌ Failed: {len(results) - successful}")
    
    if successful > 0:
        print(f"\n📬 Successfully sent {successful} emails to kyanberg@outlook.com")
        print("   Check your inbox for the test messages!")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Email Queue Sender')
    parser.add_argument('--batch-size', type=int, default=3, help='Number of emails to send')
    
    args = parser.parse_args()
    
    # Send batch emails
    results = send_batch_emails(args.batch_size)
    
    # Return success if all emails were sent successfully
    success_count = sum(1 for r in results if r.get('success'))
    return success_count == len(results) if results else False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)