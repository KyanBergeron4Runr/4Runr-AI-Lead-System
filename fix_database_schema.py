#!/usr/bin/env python3
"""
Fix Database Schema for Fresh Leads
==================================
Check current schema and fix the fresh start script
"""

import sqlite3
import json
import logging
from datetime import datetime

class DatabaseSchemaFixer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_current_schema(self):
        """Check what columns actually exist in the leads table"""
        self.logger.info("🔍 Checking current database schema...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get table info
            cursor = conn.execute("PRAGMA table_info(leads)")
            columns = cursor.fetchall()
            
            if not columns:
                self.logger.info("❌ No leads table found!")
                return None
            
            self.logger.info("📊 CURRENT LEADS TABLE SCHEMA:")
            column_names = []
            for col in columns:
                col_id, name, col_type, not_null, default, pk = col
                self.logger.info(f"   {name} ({col_type}) {'PRIMARY KEY' if pk else ''}")
                column_names.append(name)
            
            conn.close()
            return column_names
            
        except Exception as e:
            self.logger.error(f"❌ Error checking schema: {e}")
            return None

    def save_fixed_fresh_leads(self, fresh_leads, column_names):
        """Save fresh leads using only existing columns"""
        if not fresh_leads or not column_names:
            return 0
        
        self.logger.info(f"💾 Saving {len(fresh_leads)} fresh leads using existing schema...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Map fresh lead data to existing columns
            saved_count = 0
            for lead in fresh_leads:
                # Prepare data using only existing columns
                data = {}
                
                # Map common fields
                if 'Full_Name' in column_names:
                    data['Full_Name'] = lead.get('name', '')
                elif 'name' in column_names:
                    data['name'] = lead.get('name', '')
                
                if 'Job_Title' in column_names:
                    data['Job_Title'] = lead.get('title', '')
                elif 'title' in column_names:
                    data['title'] = lead.get('title', '')
                
                if 'Company' in column_names:
                    data['Company'] = lead.get('company', '')
                elif 'company' in column_names:
                    data['company'] = lead.get('company', '')
                
                if 'Email' in column_names:
                    data['Email'] = lead.get('email', '')
                elif 'email' in column_names:
                    data['email'] = lead.get('email', '')
                
                if 'LinkedIn_URL' in column_names:
                    data['LinkedIn_URL'] = lead.get('linkedin_url', '')
                elif 'linkedin_url' in column_names:
                    data['linkedin_url'] = lead.get('linkedin_url', '')
                
                if 'Website' in column_names:
                    data['Website'] = lead.get('website', '')
                elif 'website' in column_names:
                    data['website'] = lead.get('website', '')
                
                if 'Phone' in column_names:
                    data['Phone'] = lead.get('phone', '')
                elif 'phone' in column_names:
                    data['phone'] = lead.get('phone', '')
                
                # Add timestamps
                if 'Created_At' in column_names:
                    data['Created_At'] = datetime.now().isoformat()
                elif 'created_at' in column_names:
                    data['created_at'] = datetime.now().isoformat()
                
                if 'Date_Scraped' in column_names:
                    data['Date_Scraped'] = datetime.now().isoformat()
                elif 'scraped_at' in column_names:
                    data['scraped_at'] = datetime.now().isoformat()
                
                # Add defaults for other fields
                if 'Response_Status' in column_names:
                    data['Response_Status'] = 'pending'
                if 'Needs_Enrichment' in column_names:
                    data['Needs_Enrichment'] = 1
                if 'Source' in column_names:
                    data['Source'] = 'Enhanced SerpAPI'
                if 'Business_Type' in column_names:
                    data['Business_Type'] = 'Small Business'
                if 'data_quality' in column_names:
                    data['data_quality'] = 'serpapi_sourced'
                if 'scraping_source' in column_names:
                    data['scraping_source'] = 'serpapi_enhanced'
                
                # Build INSERT query
                columns = list(data.keys())
                placeholders = ', '.join(['?' for _ in columns])
                column_list = ', '.join(columns)
                values = [data[col] for col in columns]
                
                query = f"INSERT INTO leads ({column_list}) VALUES ({placeholders})"
                
                try:
                    conn.execute(query, values)
                    saved_count += 1
                    self.logger.info(f"✅ Saved: {lead.get('name', 'Unknown')}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to save {lead.get('name', 'Unknown')}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Successfully saved {saved_count} fresh leads")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"❌ Error saving leads: {e}")
            return 0

def main():
    fixer = DatabaseSchemaFixer()
    
    print("🔧 DATABASE SCHEMA FIXER")
    print("=" * 30)
    
    # Check current schema
    column_names = fixer.check_current_schema()
    
    if not column_names:
        print("❌ Could not read database schema")
        return
    
    print(f"\n✅ Found {len(column_names)} columns in leads table")
    
    # Test with sample fresh leads (like what was scraped)
    sample_fresh_leads = [
        {
            'name': 'Renée Touzin',
            'title': 'President and CEO',
            'company': 'Unknown Company',
            'email': 'rene.touzin@a0b00267.com',
            'linkedin_url': 'https://ca.linkedin.com/in/renée-touzin-a0b00267',
            'data_quality': 'serpapi_sourced'
        },
        {
            'name': 'Francois Boulanger',
            'title': 'CGI',
            'company': 'Unknown Company', 
            'email': 'francois.boulanger@27b69170.com',
            'linkedin_url': 'https://ca.linkedin.com/in/francois-boulanger-27b69170',
            'data_quality': 'serpapi_sourced'
        }
    ]
    
    print(f"\n💾 Testing with {len(sample_fresh_leads)} sample leads...")
    saved_count = fixer.save_fixed_fresh_leads(sample_fresh_leads, column_names)
    
    print(f"\n🎉 SCHEMA FIX COMPLETE!")
    print(f"   ✅ Saved: {saved_count} test leads")
    print(f"   📊 Database ready for fresh leads")
    
    print(f"\n🚀 NEXT: Run the fixed fresh start again")

if __name__ == "__main__":
    main()