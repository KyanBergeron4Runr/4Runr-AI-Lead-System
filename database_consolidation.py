#!/usr/bin/env python3
"""
4Runr AI Lead System - Database Consolidation Script
Unifies all scattered databases into a single, well-organized database structure
"""

import os
import sqlite3
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

class DatabaseConsolidator:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.unified_db_path = self.root_dir / "data" / "unified_leads.db"
        self.backup_dir = self.root_dir / "backups" / f"consolidation_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Database paths found in the system
        self.database_paths = {
            'primary': self.root_dir / "4runr-lead-scraper" / "data" / "leads.db",
            'outreach': self.root_dir / "4runr-outreach-system" / "data" / "leads_cache.db",
            'campaigns': self.root_dir / "4runr-outreach-system" / "campaign_system" / "campaigns.db",
            'root': self.root_dir / "data" / "leads.db",
            'test': self.root_dir / "4runr-outreach-system" / "test.db",
            'archived': self.root_dir / "archived_systems" / "4runr-agents" / "data" / "leads.db"
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.root_dir / "logs" / "database_consolidation.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log(self, message: str, level: str = "info"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if level == "error":
            self.logger.error(formatted_message)
        elif level == "warning":
            self.logger.warning(formatted_message)
        else:
            self.logger.info(formatted_message)
            
    def create_backup(self):
        """Create backup of all existing databases"""
        self.log("🔄 Creating backup of existing databases...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        for name, db_path in self.database_paths.items():
            if db_path.exists():
                backup_path = self.backup_dir / f"{name}_backup.db"
                shutil.copy2(db_path, backup_path)
                self.log(f"   ✅ Backed up {name}: {db_path} -> {backup_path}")
            else:
                self.log(f"   ⚠️ Database not found: {name} at {db_path}", "warning")
                
        # Create backup manifest
        manifest = {
            "consolidation_date": datetime.now().isoformat(),
            "backup_location": str(self.backup_dir),
            "databases_backed_up": [name for name, path in self.database_paths.items() if path.exists()],
            "total_databases": len([path for path in self.database_paths.values() if path.exists()])
        }
        
        with open(self.backup_dir / "backup_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
            
        self.log(f"✅ Backup complete: {self.backup_dir}")
        
    def analyze_database_schemas(self) -> Dict[str, Any]:
        """Analyze schemas of all existing databases"""
        self.log("🔍 Analyzing database schemas...")
        
        schemas = {}
        
        for name, db_path in self.database_paths.items():
            if not db_path.exists():
                continue
                
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get table information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                table_schemas = {}
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    table_schemas[table_name] = columns
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    row_count = cursor.fetchone()[0]
                    table_schemas[f"{table_name}_count"] = row_count
                
                schemas[name] = {
                    "path": str(db_path),
                    "tables": table_schemas,
                    "size_mb": db_path.stat().st_size / (1024 * 1024)
                }
                
                conn.close()
                self.log(f"   ✅ Analyzed {name}: {len(tables)} tables, {sum(table_schemas.get(f'{t[0]}_count', 0) for t in tables)} rows")
                
            except Exception as e:
                self.log(f"   ❌ Error analyzing {name}: {str(e)}", "error")
                schemas[name] = {"error": str(e)}
                
        return schemas
        
    def create_unified_schema(self) -> str:
        """Create unified database schema"""
        self.log("🏗️ Creating unified database schema...")
        
        # Create data directory if it doesn't exist
        self.unified_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Unified schema based on analysis of existing databases
        schema_sql = """
        -- Unified 4Runr AI Lead System Database Schema
        
        -- Main leads table
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            company TEXT,
            job_title TEXT,
            linkedin_url TEXT,
            website TEXT,
            industry TEXT,
            location TEXT,
            company_size TEXT,
            revenue TEXT,
            status TEXT DEFAULT 'new',
            engagement_status TEXT DEFAULT 'pending',
            engagement_level INTEGER DEFAULT 0,
            last_contact_date TEXT,
            next_contact_date TEXT,
            contact_attempts INTEGER DEFAULT 0,
            ai_message TEXT,
            company_description TEXT,
            business_type TEXT,
            website_insights TEXT,
            tone TEXT,
            top_services TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT DEFAULT 'manual',
            notes TEXT,
            tags TEXT,
            score INTEGER DEFAULT 0,
            verified BOOLEAN DEFAULT 0,
            enriched BOOLEAN DEFAULT 0,
            scraped BOOLEAN DEFAULT 0
        );
        
        -- Campaigns table
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            target_audience TEXT,
            message_template TEXT,
            schedule_config TEXT,
            performance_metrics TEXT
        );
        
        -- Campaign leads mapping
        CREATE TABLE IF NOT EXISTS campaign_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            lead_id INTEGER,
            status TEXT DEFAULT 'pending',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            response_received BOOLEAN DEFAULT 0,
            response_text TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
            FOREIGN KEY (lead_id) REFERENCES leads (id)
        );
        
        -- System logs table
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            component TEXT,
            message TEXT,
            details TEXT
        );
        
        -- Performance metrics table
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metric_name TEXT,
            metric_value REAL,
            component TEXT,
            details TEXT
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
        CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company);
        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
        CREATE INDEX IF NOT EXISTS idx_leads_engagement_status ON leads(engagement_status);
        CREATE INDEX IF NOT EXISTS idx_campaign_leads_campaign_id ON campaign_leads(campaign_id);
        CREATE INDEX IF NOT EXISTS idx_campaign_leads_lead_id ON campaign_leads(lead_id);
        CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_system_logs_component ON system_logs(component);
        """
        
        try:
            conn = sqlite3.connect(self.unified_db_path)
            conn.executescript(schema_sql)
            conn.close()
            self.log(f"✅ Unified schema created: {self.unified_db_path}")
            return schema_sql
        except Exception as e:
            self.log(f"❌ Error creating unified schema: {str(e)}", "error")
            raise
            
    def migrate_data(self, schemas: Dict[str, Any]):
        """Migrate data from all existing databases to unified database"""
        self.log("🔄 Migrating data to unified database...")
        
        migration_stats = {
            "total_leads_migrated": 0,
            "total_campaigns_migrated": 0,
            "databases_processed": 0,
            "errors": []
        }
        
        for db_name, db_info in schemas.items():
            if "error" in db_info:
                continue
                
            self.log(f"   📦 Migrating data from {db_name}...")
            
            try:
                source_conn = sqlite3.connect(db_info["path"])
                unified_conn = sqlite3.connect(self.unified_db_path)
                
                # Migrate leads table
                if "leads" in db_info["tables"]:
                    leads_migrated = self.migrate_leads_table(source_conn, unified_conn, db_name)
                    migration_stats["total_leads_migrated"] += leads_migrated
                    self.log(f"      ✅ Migrated {leads_migrated} leads from {db_name}")
                
                # Migrate campaigns table
                if "campaigns" in db_info["tables"]:
                    campaigns_migrated = self.migrate_campaigns_table(source_conn, unified_conn, db_name)
                    migration_stats["total_campaigns_migrated"] += campaigns_migrated
                    self.log(f"      ✅ Migrated {campaigns_migrated} campaigns from {db_name}")
                
                source_conn.close()
                unified_conn.close()
                migration_stats["databases_processed"] += 1
                
            except Exception as e:
                error_msg = f"Error migrating {db_name}: {str(e)}"
                self.log(f"      ❌ {error_msg}", "error")
                migration_stats["errors"].append(error_msg)
                
        self.log(f"✅ Migration complete: {migration_stats['total_leads_migrated']} leads, {migration_stats['total_campaigns_migrated']} campaigns")
        return migration_stats
        
    def migrate_leads_table(self, source_conn: sqlite3.Connection, unified_conn: sqlite3.Connection, source_name: str) -> int:
        """Migrate leads from source database to unified database"""
        try:
            # Get source table schema
            cursor = source_conn.cursor()
            cursor.execute("PRAGMA table_info(leads);")
            source_columns = [row[1] for row in cursor.fetchall()]
            
            # Get unified table schema
            unified_cursor = unified_conn.cursor()
            unified_cursor.execute("PRAGMA table_info(leads);")
            unified_columns = [row[1] for row in unified_cursor.fetchall()]
            
            # Get all leads from source
            cursor.execute("SELECT * FROM leads;")
            source_leads = cursor.fetchall()
            
            migrated_count = 0
            for lead in source_leads:
                lead_dict = dict(zip(source_columns, lead))
                
                # Check if lead already exists (by email or company)
                email = lead_dict.get('email', '')
                company = lead_dict.get('company', '')
                
                if email or company:
                    existing = unified_cursor.execute(
                        "SELECT id FROM leads WHERE email = ? OR company = ?", 
                        (email, company)
                    ).fetchone()
                    
                    if not existing:
                        # Prepare data for unified schema
                        unified_data = self.prepare_lead_data_for_unified(lead_dict, source_name)
                        
                        # Insert into unified database
                        columns = list(unified_data.keys())
                        placeholders = ','.join(['?' for _ in columns])
                        values = list(unified_data.values())
                        
                        unified_cursor.execute(
                            f"INSERT INTO leads ({','.join(columns)}) VALUES ({placeholders})",
                            values
                        )
                        migrated_count += 1
            
            unified_conn.commit()
            return migrated_count
            
        except Exception as e:
            self.log(f"Error migrating leads from {source_name}: {str(e)}", "error")
            return 0
            
    def prepare_lead_data_for_unified(self, lead_dict: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """Prepare lead data for unified schema"""
        unified_data = {
            'full_name': lead_dict.get('full_name', ''),
            'first_name': lead_dict.get('first_name', ''),
            'last_name': lead_dict.get('last_name', ''),
            'email': lead_dict.get('email', ''),
            'phone': lead_dict.get('phone', ''),
            'company': lead_dict.get('company', ''),
            'job_title': lead_dict.get('job_title', ''),
            'linkedin_url': lead_dict.get('linkedin_url', ''),
            'website': lead_dict.get('website', ''),
            'industry': lead_dict.get('industry', ''),
            'location': lead_dict.get('location', ''),
            'company_size': lead_dict.get('company_size', ''),
            'revenue': lead_dict.get('revenue', ''),
            'status': lead_dict.get('status', 'new'),
            'engagement_status': lead_dict.get('engagement_status', 'pending'),
            'engagement_level': lead_dict.get('engagement_level', 0),
            'last_contact_date': lead_dict.get('last_contact_date', ''),
            'next_contact_date': lead_dict.get('next_contact_date', ''),
            'contact_attempts': lead_dict.get('contact_attempts', 0),
            'ai_message': lead_dict.get('ai_message', ''),
            'company_description': lead_dict.get('company_description', ''),
            'business_type': lead_dict.get('business_type', ''),
            'website_insights': lead_dict.get('website_insights', ''),
            'tone': lead_dict.get('tone', ''),
            'top_services': lead_dict.get('top_services', ''),
            'created_at': lead_dict.get('created_at', datetime.now().isoformat()),
            'updated_at': lead_dict.get('updated_at', datetime.now().isoformat()),
            'source': source_name,
            'notes': lead_dict.get('notes', ''),
            'tags': lead_dict.get('tags', ''),
            'score': lead_dict.get('score', 0),
            'verified': lead_dict.get('verified', 0),
            'enriched': lead_dict.get('enriched', 0),
            'scraped': lead_dict.get('scraped', 0)
        }
        
        return unified_data
        
    def migrate_campaigns_table(self, source_conn: sqlite3.Connection, unified_conn: sqlite3.Connection, source_name: str) -> int:
        """Migrate campaigns from source database to unified database"""
        try:
            cursor = source_conn.cursor()
            cursor.execute("SELECT * FROM campaigns;")
            campaigns = cursor.fetchall()
            
            unified_cursor = unified_conn.cursor()
            migrated_count = 0
            
            for campaign in campaigns:
                # Simple migration - adjust based on actual schema
                unified_cursor.execute(
                    "INSERT INTO campaigns (name, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (campaign[1] if len(campaign) > 1 else f"Campaign from {source_name}", 
                     campaign[2] if len(campaign) > 2 else "",
                     campaign[3] if len(campaign) > 3 else "active",
                     datetime.now().isoformat(),
                     datetime.now().isoformat())
                )
                migrated_count += 1
            
            unified_conn.commit()
            return migrated_count
            
        except Exception as e:
            self.log(f"Error migrating campaigns from {source_name}: {str(e)}", "error")
            return 0
            
    def update_configuration_files(self):
        """Update all configuration files to point to unified database"""
        self.log("⚙️ Updating configuration files...")
        
        # Update .env files
        env_files = [
            ".env",
            "4runr-outreach-system/.env",
            "4runr-brain/.env"
        ]
        
        for env_file in env_files:
            env_path = self.root_dir / env_file
            if env_path.exists():
                self.update_env_file(env_path)
                self.log(f"   ✅ Updated {env_file}")
                
    def update_env_file(self, env_path: Path):
        """Update .env file to use unified database"""
        try:
            lines = []
            key_found = False
            
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update LEAD_DATABASE_PATH
            for i, line in enumerate(lines):
                if line.strip().startswith("LEAD_DATABASE_PATH="):
                    lines[i] = f"LEAD_DATABASE_PATH={self.unified_db_path}\n"
                    key_found = True
                    break
            
            if not key_found:
                lines.append(f"LEAD_DATABASE_PATH={self.unified_db_path}\n")
            
            with open(env_path, 'w') as f:
                f.writelines(lines)
                
        except Exception as e:
            self.log(f"Error updating {env_path}: {str(e)}", "error")
            
    def create_migration_report(self, schemas: Dict[str, Any], migration_stats: Dict[str, Any]):
        """Create comprehensive migration report"""
        self.log("📊 Creating migration report...")
        
        report = {
            "consolidation_date": datetime.now().isoformat(),
            "unified_database_path": str(self.unified_db_path),
            "backup_location": str(self.backup_dir),
            "database_analysis": schemas,
            "migration_results": migration_stats,
            "total_databases_processed": len([s for s in schemas.values() if "error" not in s]),
            "total_leads_consolidated": migration_stats["total_leads_migrated"],
            "total_campaigns_consolidated": migration_stats["total_campaigns_migrated"],
            "configuration_updated": True
        }
        
        report_path = self.root_dir / "database_consolidation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"✅ Migration report created: {report_path}")
        return report
        
    def run_consolidation(self):
        """Run the complete database consolidation process"""
        self.log("🚀 Starting database consolidation process...")
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Analyze existing schemas
            schemas = self.analyze_database_schemas()
            
            # Step 3: Create unified schema
            self.create_unified_schema()
            
            # Step 4: Migrate data
            migration_stats = self.migrate_data(schemas)
            
            # Step 5: Update configuration
            self.update_configuration_files()
            
            # Step 6: Create report
            report = self.create_migration_report(schemas, migration_stats)
            
            self.log("🎉 Database consolidation completed successfully!")
            self.log(f"📊 Summary:")
            self.log(f"   - Total leads consolidated: {migration_stats['total_leads_migrated']}")
            self.log(f"   - Total campaigns consolidated: {migration_stats['total_campaigns_migrated']}")
            self.log(f"   - Databases processed: {migration_stats['databases_processed']}")
            self.log(f"   - Unified database: {self.unified_db_path}")
            self.log(f"   - Backup location: {self.backup_dir}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Consolidation failed: {str(e)}", "error")
            return False

def main():
    """Main function to run database consolidation"""
    consolidator = DatabaseConsolidator()
    success = consolidator.run_consolidation()
    
    if success:
        print("\n🎉 Database consolidation completed successfully!")
        print("📋 Next steps:")
        print("   1. Test the unified database with existing applications")
        print("   2. Update any hardcoded database paths in the code")
        print("   3. Remove old database files after verification")
        print("   4. Update deployment scripts to use unified database")
    else:
        print("\n❌ Database consolidation failed. Check logs for details.")

if __name__ == "__main__":
    main()
