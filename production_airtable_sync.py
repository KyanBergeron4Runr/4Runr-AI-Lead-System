#!/usr/bin/env python3
"""
Production Airtable Sync System
- Works with existing fields and provides setup guide for missing fields
- Intelligent lead quality calculation 
- Real-time capable for EC2 deployment
"""

import sqlite3
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionAirtableSync:
    """Production-ready Airtable sync with intelligent scoring"""
    
    def __init__(self, db_path: str = "data/unified_leads.db"):
        self.db_path = db_path
        
        # Airtable credentials
        self.api_key = 'pat1EXE7KfOBTgJl6.28307c0b4f5eb80de65d01de18ecead5da6e7bc98f04ceea7e60b540e9773923'
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_name = 'Table 1'
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        self.airtable_url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_name}'
        
        # Currently existing fields in Airtable (verified)
        self.existing_fields = {
            'AI Message', 'Business_Type', 'Company', 'Created At', 'Email',
            'Email_Confidence_Level', 'Full Name', 'Job Title', 'Lead Quality',
            'LinkedIn URL', 'Website'
        }
        
    def calculate_intelligent_lead_quality(self, lead: Dict[str, Any]) -> str:
        """Calculate intelligent lead quality based on multiple factors"""
        
        score = 0
        
        # Email Quality (35 points)
        if lead.get('verified'):
            score += 30
        elif lead.get('email') and '@' in lead.get('email', ''):
            email = lead['email']
            domain = email.split('@')[1] if '@' in email else ''
            if domain and not any(provider in domain.lower() for provider in ['gmail', 'yahoo', 'hotmail']):
                score += 25  # Corporate email
            else:
                score += 15  # Personal email
        
        # Company Data Quality (25 points)
        if lead.get('company'):
            score += 5
        if lead.get('industry'):
            score += 5
        if lead.get('company_size'):
            score += 5
            # Enterprise bonus
            if any(size in lead.get('company_size', '').lower() for size in ['large', 'enterprise', '1000+', '500+']):
                score += 5
        if lead.get('website'):
            score += 5
        
        # Engagement Potential (25 points)
        job_title = lead.get('job_title', '').lower()
        if any(role in job_title for role in ['ceo', 'cto', 'founder', 'president', 'director', 'vp']):
            score += 20  # Decision maker
        elif any(role in job_title for role in ['manager', 'lead', 'senior']):
            score += 15  # Senior role
        elif job_title:
            score += 10  # Has title
            
        if lead.get('linkedin_url'):
            score += 5
        
        # Data Completeness (15 points)
        if lead.get('ai_message') and len(lead.get('ai_message', '')) > 200:
            score += 10  # Good AI message
        if lead.get('company_description'):
            score += 5
        
        # Determine tier
        if score >= 80:
            return "Hot"
        elif score >= 60:
            return "Warm"
        else:
            return "Cold"
    
    def sync_with_existing_fields(self) -> Dict[str, Any]:
        """Sync using only currently existing fields in Airtable"""
        
        logger.info("Starting production Airtable sync with existing fields...")
        
        # Get leads from database
        leads = self._get_leads_from_db()
        logger.info(f"Retrieved {len(leads)} leads from database")
        
        # Get existing Airtable records
        existing_records = self._get_existing_airtable_records()
        email_to_record = {record.get('fields', {}).get('Email', '').lower(): record['id'] 
                          for record in existing_records if record.get('fields', {}).get('Email')}
        
        stats = {'processed': 0, 'updated': 0, 'errors': 0, 'error_details': []}
        
        for lead in leads:
            try:
                # Calculate intelligent quality
                quality = self.calculate_intelligent_lead_quality(lead)
                
                # Map to existing fields only
                airtable_fields = {
                    'Full Name': lead.get('full_name', ''),
                    'Email': lead.get('email', ''),
                    'Company': lead.get('company', ''),
                    'Job Title': lead.get('job_title', '') or 'Not specified',
                    'LinkedIn URL': lead.get('linkedin_url', ''),
                    'Website': lead.get('website', ''),
                    'AI Message': lead.get('ai_message', ''),
                    'Business_Type': lead.get('business_type', '') or 'Other',
                    'Lead Quality': quality,
                    'Email_Confidence_Level': 'Real' if lead.get('verified') else 'Pattern'
                }
                
                # Clean empty fields
                cleaned_fields = {k: v for k, v in airtable_fields.items() if v not in [None, '', 'Not specified']}
                
                # Update existing record
                email = lead.get('email', '').lower()
                if email and email in email_to_record:
                    success = self._update_airtable_record(email_to_record[email], cleaned_fields)
                    if success:
                        stats['updated'] += 1
                        logger.info(f"✅ Updated: {lead.get('full_name', 'Unknown')} - Quality: {quality}")
                    else:
                        stats['errors'] += 1
                
                stats['processed'] += 1
                
            except Exception as e:
                stats['errors'] += 1
                stats['error_details'].append(f"{lead.get('full_name', 'Unknown')}: {str(e)}")
                logger.error(f"Error processing {lead.get('full_name', 'Unknown')}: {e}")
        
        logger.info(f"Sync completed: {stats['updated']} updated, {stats['errors']} errors")
        
        # Show field setup guide
        self._show_missing_fields_guide()
        
        return stats
    
    def _show_missing_fields_guide(self):
        """Show guide for setting up missing fields in Airtable"""
        
        print("\n" + "="*60)
        print("🔧 AIRTABLE SETUP GUIDE - Missing Fields")
        print("="*60)
        print("To get ALL your data in Airtable, add these fields manually:")
        print()
        
        missing_fields = [
            ("Source", "Single select", "Search, Comment, Other"),
            ("Needs Enrichment", "Checkbox", ""),
            ("Replied", "Checkbox", ""),
            ("Response Date", "Date", ""),
            ("Response Notes", "Long text", ""),
            ("Date Scraped", "Date", ""),
            ("Date Enriched", "Date", ""),
            ("Date Messaged", "Date", ""),
            ("Extra info", "Long text", ""),
            ("Level Engaged", "Multiple select", "1st degree, 2nd degree, 3rd degree, retry"),
            ("Engagement_Status", "Single select", "Sent, Auto-Send, Skip, Needs Review"),
            ("Follow_Up_Stage", "Single select", "Initial Contact, First Follow-up, Second Follow-up, Final Follow-up"),
            ("Response_Status", "Single select", "Pending, Received, No Response"),
            ("Company_Description", "Long text", "")
        ]
        
        for i, (field_name, field_type, options) in enumerate(missing_fields, 1):
            print(f"{i:2d}. {field_name}")
            print(f"    Type: {field_type}")
            if options:
                print(f"    Options: {options}")
            print()
        
        print("📋 HOW TO ADD FIELDS:")
        print("1. Go to your Airtable base")
        print("2. Click the '+' button to add a new field")
        print("3. Enter the field name exactly as shown above")
        print("4. Select the correct field type")
        print("5. Add the options for select fields")
        print()
        print("🚀 After adding these fields, run this script again to populate them!")
        print("="*60)
    
    def sync_with_all_fields(self) -> Dict[str, Any]:
        """Sync with all fields (use this after creating missing fields in Airtable)"""
        
        logger.info("Starting full sync with all fields...")
        
        # Check if new fields exist
        sample_record = self._get_existing_airtable_records()
        if sample_record:
            available_fields = set(sample_record[0].get('fields', {}).keys())
            
            # Update our known fields
            self.existing_fields = available_fields
            logger.info(f"Detected {len(available_fields)} fields in Airtable")
        
        # Get leads from database
        leads = self._get_leads_from_db()
        
        # Get existing Airtable records
        existing_records = self._get_existing_airtable_records()
        email_to_record = {record.get('fields', {}).get('Email', '').lower(): record['id'] 
                          for record in existing_records if record.get('fields', {}).get('Email')}
        
        stats = {'processed': 0, 'updated': 0, 'errors': 0, 'error_details': []}
        
        for lead in leads:
            try:
                # Calculate intelligent quality
                quality = self.calculate_intelligent_lead_quality(lead)
                
                # Map ALL available fields
                all_fields = self._map_all_available_fields(lead, quality)
                
                # Filter to only existing fields
                filtered_fields = {k: v for k, v in all_fields.items() if k in self.existing_fields}
                
                # Update existing record
                email = lead.get('email', '').lower()
                if email and email in email_to_record:
                    success = self._update_airtable_record(email_to_record[email], filtered_fields)
                    if success:
                        stats['updated'] += 1
                        logger.info(f"✅ Updated: {lead.get('full_name', 'Unknown')} - {len(filtered_fields)} fields")
                    else:
                        stats['errors'] += 1
                
                stats['processed'] += 1
                
            except Exception as e:
                stats['errors'] += 1
                stats['error_details'].append(f"{lead.get('full_name', 'Unknown')}: {str(e)}")
                logger.error(f"Error processing {lead.get('full_name', 'Unknown')}: {e}")
        
        logger.info(f"Full sync completed: {stats['updated']} updated, {stats['errors']} errors")
        return stats
    
    def _map_all_available_fields(self, lead: Dict[str, Any], quality: str) -> Dict[str, Any]:
        """Map all possible fields (for when they exist in Airtable)"""
        
        fields = {}
        
        # Basic fields
        if lead.get('full_name'):
            fields['Full Name'] = lead['full_name']
        if lead.get('email'):
            fields['Email'] = lead['email']
        if lead.get('company'):
            fields['Company'] = lead['company']
        if lead.get('job_title'):
            fields['Job Title'] = lead['job_title']
        if lead.get('linkedin_url'):
            fields['LinkedIn URL'] = lead['linkedin_url']
        if lead.get('website'):
            fields['Website'] = lead['website']
        
        # Quality and source
        fields['Lead Quality'] = quality
        fields['Email_Confidence_Level'] = 'Real' if lead.get('verified') else 'Pattern'
        fields['Source'] = self._map_source(lead.get('source', ''))
        fields['Needs Enrichment'] = not bool(lead.get('enriched'))
        
        # Business info
        if lead.get('business_type'):
            fields['Business_Type'] = lead['business_type']
        if lead.get('company_description'):
            fields['Company_Description'] = lead['company_description'][:1000]
        
        # Messages and responses
        if lead.get('ai_message'):
            fields['AI Message'] = lead['ai_message']
        fields['Replied'] = bool(lead.get('response_received'))
        fields['Response_Status'] = 'Received' if lead.get('response_received') else 'Pending'
        
        # Engagement
        fields['Engagement_Status'] = self._map_engagement_status(lead.get('engagement_status', ''))
        fields['Follow_Up_Stage'] = self._map_follow_up_stage(lead)
        
        # Level engaged
        engagement_level = lead.get('engagement_level', 1)
        if engagement_level >= 3:
            fields['Level Engaged'] = ['3rd degree']
        elif engagement_level == 2:
            fields['Level Engaged'] = ['2nd degree']
        else:
            fields['Level Engaged'] = ['1st degree']
        
        # Dates
        if lead.get('scraped_at'):
            fields['Date Scraped'] = self._format_date(lead['scraped_at'])
        if lead.get('updated_at') and lead.get('enriched'):
            fields['Date Enriched'] = self._format_date(lead['updated_at'])
        if lead.get('message_generated_at'):
            fields['Date Messaged'] = self._format_date(lead['message_generated_at'])
        if lead.get('last_engagement_date') and lead.get('response_received'):
            fields['Response Date'] = self._format_date(lead['last_engagement_date'])
        
        # Notes
        notes_parts = []
        if lead.get('engagement_notes'):
            notes_parts.append(f"Engagement: {lead['engagement_notes']}")
        if lead.get('notes'):
            notes_parts.append(f"Notes: {lead['notes']}")
        if notes_parts:
            fields['Response Notes'] = " | ".join(notes_parts)
        
        # Extra info
        extra_parts = []
        if lead.get('industry'):
            extra_parts.append(f"Industry: {lead['industry']}")
        if lead.get('location'):
            extra_parts.append(f"Location: {lead['location']}")
        if lead.get('company_size'):
            extra_parts.append(f"Company Size: {lead['company_size']}")
        if lead.get('phone'):
            extra_parts.append(f"Phone: {lead['phone']}")
        if lead.get('contact_attempts'):
            extra_parts.append(f"Contact Attempts: {lead['contact_attempts']}")
        
        if extra_parts:
            fields['Extra info'] = "\\n".join(extra_parts)
        
        return {k: v for k, v in fields.items() if v not in [None, '', [], ['']]}
    
    def _map_source(self, source: str) -> str:
        """Map source to Airtable values"""
        source_lower = source.lower() if source else ""
        if "search" in source_lower:
            return "Search"
        elif "comment" in source_lower:
            return "Comment"
        else:
            return "Other"
    
    def _map_engagement_status(self, status: str) -> str:
        """Map engagement status"""
        status_lower = status.lower() if status else ""
        if "sent" in status_lower:
            return "Sent"
        elif "auto" in status_lower:
            return "Auto-Send"
        elif "skip" in status_lower:
            return "Skip"
        else:
            return "Needs Review"
    
    def _map_follow_up_stage(self, lead: Dict[str, Any]) -> str:
        """Map follow-up stage"""
        follow_up_count = lead.get('follow_up_count', 0)
        contact_attempts = lead.get('contact_attempts', 0)
        
        total_attempts = max(follow_up_count, contact_attempts)
        
        if total_attempts >= 3:
            return "Final Follow-up"
        elif total_attempts >= 2:
            return "Second Follow-up"
        elif total_attempts >= 1:
            return "First Follow-up"
        else:
            return "Initial Contact"
    
    def _format_date(self, date_str: str) -> str:
        """Format date for Airtable"""
        if not date_str:
            return ""
        
        try:
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            else:
                return date_str
        except:
            return date_str
    
    def _get_leads_from_db(self) -> List[Dict[str, Any]]:
        """Get leads from database"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT 
                full_name, email, company, job_title, linkedin_url, website,
                industry, location, company_size, phone, business_type, 
                company_description, ai_message, created_at, updated_at, 
                scraped_at, message_generated_at, verified, enriched, 
                score, engagement_level, engagement_status, response_received,
                contact_attempts, follow_up_count, last_engagement_date,
                engagement_notes, source, notes
            FROM leads 
            WHERE ai_message IS NOT NULL AND ai_message != ''
        """)
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leads
    
    def _get_existing_airtable_records(self) -> List[Dict[str, Any]]:
        """Get existing Airtable records"""
        
        try:
            response = requests.get(self.airtable_url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get('records', [])
            else:
                logger.error(f"Failed to get Airtable records: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting Airtable records: {e}")
            return []
    
    def _update_airtable_record(self, record_id: str, fields: Dict[str, Any]) -> bool:
        """Update Airtable record"""
        
        try:
            update_data = {"fields": fields}
            response = requests.patch(f"{self.airtable_url}/{record_id}", 
                                    headers=self.headers, json=update_data)
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {e}")
            return False


def main():
    """Main function - choose sync type"""
    
    sync_manager = ProductionAirtableSync()
    
    print("🚀 4Runr Production Airtable Sync")
    print("="*40)
    print("1. Quick sync (existing fields only)")
    print("2. Full sync (after adding missing fields)")
    print()
    
    choice = input("Choose sync type (1 or 2): ").strip()
    
    if choice == "1":
        results = sync_manager.sync_with_existing_fields()
    elif choice == "2":
        results = sync_manager.sync_with_all_fields()
    else:
        print("Running quick sync by default...")
        results = sync_manager.sync_with_existing_fields()
    
    print(f"\n✅ Sync Results:")
    print(f"Processed: {results['processed']} leads")
    print(f"Updated: {results['updated']} records")
    print(f"Errors: {results['errors']}")


if __name__ == "__main__":
    main()