#!/usr/bin/env python3
"""
Working CLI for 4runr-lead-scraper

A fully functional command-line interface that works without import issues.
"""
import sqlite3
import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

class WorkingCLI:
    """Working CLI implementation"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "data" / "leads.db"
        self.env_path = Path(__file__).parent / ".env"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, str]:
        """Load configuration from .env file"""
        config = {}
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config
    
    def _get_db_connection(self):
        """Get database connection"""
        if not self.db_path.exists():
            raise Exception(f"Database not found: {self.db_path}")
        return sqlite3.connect(str(self.db_path))
    
    def stats(self):
        """Show database statistics"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute("SELECT COUNT(*) FROM leads")
            total_leads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
            with_email = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Ready for Outreach'")
            ready_for_outreach = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM leads WHERE enriched = 1")
            enriched = cursor.fetchone()[0]
            
            # Status breakdown
            cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
            status_counts = cursor.fetchall()
            
            print("📊 4Runr Lead Scraper Statistics")
            print("=" * 40)
            print(f"Total Leads: {total_leads}")
            print(f"With Email: {with_email} ({with_email/total_leads*100:.1f}%)")
            print(f"Enriched: {enriched} ({enriched/total_leads*100:.1f}%)")
            print(f"Ready for Outreach: {ready_for_outreach}")
            
            print("\nStatus Breakdown:")
            for status, count in status_counts:
                print(f"  {status}: {count}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def list_leads(self, limit: int = 10, status: Optional[str] = None):
        """List leads"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT full_name, email, company, status, enriched, linkedin_url
                FROM leads 
            """
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            leads = cursor.fetchall()
            
            filter_text = f" (status: {status})" if status else ""
            print(f"📋 Recent Leads{filter_text} (showing {len(leads)})")
            print("=" * 60)
            
            for name, email, company, lead_status, enriched, linkedin in leads:
                enriched_status = "✅" if enriched else "⏳"
                print(f"{enriched_status} {name}")
                print(f"   📧 {email or 'No email'}")
                print(f"   🏢 {company or 'No company'}")
                print(f"   📊 {lead_status}")
                if linkedin:
                    print(f"   🔗 {linkedin}")
                print()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_lead(self, lead_id: str):
        """Show detailed lead information"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
            lead = cursor.fetchone()
            
            if not lead:
                print(f"❌ Lead not found: {lead_id}")
                return
            
            # Get column names
            cursor.execute("PRAGMA table_info(leads)")
            columns = [col[1] for col in cursor.fetchall()]
            
            lead_dict = dict(zip(columns, lead))
            
            print(f"👤 Lead Details: {lead_dict.get('full_name', 'Unknown')}")
            print("=" * 50)
            
            for key, value in lead_dict.items():
                if value:
                    print(f"{key}: {value}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def test_config(self):
        """Test configuration"""
        print("⚙️  Configuration Test")
        print("=" * 30)
        
        required_keys = ['SERPAPI_API_KEY', 'AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID']
        
        for key in required_keys:
            if key in self.config and self.config[key]:
                print(f"✅ {key}: Configured")
            else:
                print(f"❌ {key}: Missing")
        
        # Test database
        if self.db_path.exists():
            print(f"✅ Database: Found at {self.db_path}")
        else:
            print(f"❌ Database: Not found at {self.db_path}")
    
    def backup_db(self):
        """Create database backup"""
        try:
            if not self.db_path.exists():
                print("❌ Database not found")
                return
            
            backup_dir = Path(__file__).parent.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"leads_backup_{timestamp}.db"
            
            # Copy database
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            print(f"✅ Database backed up to: {backup_path}")
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
    
    def search_leads(self, query: str):
        """Search leads by name, email, or company"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            search_query = f"%{query}%"
            cursor.execute("""
                SELECT full_name, email, company, status 
                FROM leads 
                WHERE full_name LIKE ? OR email LIKE ? OR company LIKE ?
                ORDER BY full_name
            """, (search_query, search_query, search_query))
            
            results = cursor.fetchall()
            
            print(f"🔍 Search Results for '{query}' ({len(results)} found)")
            print("=" * 50)
            
            for name, email, company, status in results:
                print(f"👤 {name}")
                print(f"   📧 {email or 'No email'}")
                print(f"   🏢 {company or 'No company'}")
                print(f"   📊 {status}")
                print()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def help(self):
        """Show help information"""
        print("🚀 4Runr Lead Scraper - Working CLI")
        print("=" * 40)
        print("Available commands:")
        print("  stats                    - Show database statistics")
        print("  list [N] [--status=X]    - List recent leads")
        print("  show <lead_id>           - Show detailed lead info")
        print("  search <query>           - Search leads")
        print("  config                   - Test configuration")
        print("  backup                   - Create database backup")
        print("  help                     - Show this help")
        print()
        print("Examples:")
        print("  python working_cli.py stats")
        print("  python working_cli.py list 20")
        print("  python working_cli.py list 10 --status='Ready for Outreach'")
        print("  python working_cli.py search 'TechCorp'")
        print("  python working_cli.py backup")

def main():
    """Main CLI function"""
    cli = WorkingCLI()
    
    if len(sys.argv) < 2:
        cli.help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "stats":
            cli.stats()
        elif command == "list":
            limit = 10
            status = None
            
            # Parse arguments
            for arg in sys.argv[2:]:
                if arg.startswith("--status="):
                    status = arg.split("=", 1)[1].strip("'\"")
                elif arg.isdigit():
                    limit = int(arg)
            
            cli.list_leads(limit, status)
        elif command == "show":
            if len(sys.argv) < 3:
                print("Please provide a lead ID")
                return
            cli.show_lead(sys.argv[2])
        elif command == "search":
            if len(sys.argv) < 3:
                print("Please provide a search query")
                return
            cli.search_leads(" ".join(sys.argv[2:]))
        elif command == "config":
            cli.test_config()
        elif command == "backup":
            cli.backup_db()
        elif command == "help":
            cli.help()
        else:
            print(f"Unknown command: {command}")
            cli.help()
    except Exception as e:
        print(f"Command failed: {e}")

if __name__ == "__main__":
    main()