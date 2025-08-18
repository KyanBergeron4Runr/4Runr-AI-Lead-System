#!/usr/bin/env python3
"""
Complete system status check and data sync
- Check autonomous system status
- Sync enriched leads to Airtable
- Restart system if needed
"""

import subprocess
import sqlite3
import requests
import json
import logging
import os
from datetime import datetime

class SystemStatusChecker:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def check_autonomous_system_status(self):
        """Check if the autonomous system is running"""
        self.logger.info("🔍 Checking autonomous system status...")
        
        try:
            # Check for running real_autonomous_organism processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout
            
            organism_processes = [line for line in processes.split('\n') if 'real_autonomous_organism' in line and 'python' in line]
            
            if organism_processes:
                self.logger.info(f"✅ Found {len(organism_processes)} autonomous organism process(es) running")
                for proc in organism_processes:
                    self.logger.info(f"   {proc.strip()}")
                return True
            else:
                self.logger.warning("⚠️ No autonomous organism processes found running")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error checking process status: {e}")
            return False

    def sync_enriched_leads_to_airtable(self):
        """Sync recently enriched leads to Airtable"""
        self.logger.info("📤 Syncing enriched leads to Airtable...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get leads that need syncing (recently enriched)
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Full_Name IS NOT NULL AND Full_Name != ''
                AND Date_Enriched IS NOT NULL
                AND (Response_Status != 'synced' OR Response_Status IS NULL)
                ORDER BY Date_Enriched DESC
                LIMIT 10
            """)
            
            leads_to_sync = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if not leads_to_sync:
                self.logger.info("📋 No leads need syncing")
                return 0
            
            self.logger.info(f"📋 Found {len(leads_to_sync)} leads to sync")
            
            # Use the organism's sync method
            from real_autonomous_organism import RealAutonomousOrganism
            organism = RealAutonomousOrganism()
            
            synced_count = 0
            for lead in leads_to_sync:
                try:
                    success = organism.sync_lead_to_airtable(lead)
                    if success:
                        # Mark as synced
                        organism.mark_lead_as_synced(lead['id'])
                        synced_count += 1
                        self.logger.info(f"✅ Synced: {lead.get('Full_Name', 'Unknown')}")
                    else:
                        self.logger.error(f"❌ Failed to sync: {lead.get('Full_Name', 'Unknown')}")
                except Exception as e:
                    self.logger.error(f"❌ Sync error for {lead.get('Full_Name', 'Unknown')}: {e}")
            
            self.logger.info(f"📤 Successfully synced {synced_count}/{len(leads_to_sync)} leads")
            return synced_count
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing leads: {e}")
            return 0

    def get_current_database_stats(self):
        """Get current database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Total leads
            total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            
            # Enriched leads
            enriched = conn.execute("SELECT COUNT(*) FROM leads WHERE Date_Enriched IS NOT NULL").fetchone()[0]
            
            # Synced leads
            synced = conn.execute("SELECT COUNT(*) FROM leads WHERE Response_Status = 'synced'").fetchone()[0]
            
            # Recent activity (last 24 hours)
            yesterday = (datetime.now() - datetime.fromordinal(datetime.now().toordinal() - 1)).isoformat()
            recent_enriched = conn.execute("SELECT COUNT(*) FROM leads WHERE Date_Enriched >= ?", (yesterday,)).fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'enriched': enriched,
                'synced': synced,
                'recent_enriched': recent_enriched
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting database stats: {e}")
            return None

    def restart_autonomous_system(self):
        """Restart the autonomous system"""
        self.logger.info("🔄 Restarting autonomous system...")
        
        try:
            # Kill existing processes
            subprocess.run(['pkill', '-f', 'real_autonomous_organism'], capture_output=True)
            self.logger.info("🛑 Stopped existing autonomous processes")
            
            # Start new process
            log_file = 'logs/autonomous-system.log'
            subprocess.Popen([
                'nohup', 'python3', 'real_autonomous_organism.py', '--run'
            ], stdout=open(log_file, 'a'), stderr=subprocess.STDOUT)
            
            self.logger.info("🚀 Started new autonomous system process")
            self.logger.info(f"📊 Monitor with: tail -f {log_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error restarting system: {e}")
            return False

def main():
    checker = SystemStatusChecker()
    
    print("🔍 COMPLETE SYSTEM STATUS CHECK & SYNC")
    print("=" * 45)
    
    # Check current database stats
    stats = checker.get_current_database_stats()
    if stats:
        print(f"📊 DATABASE STATUS:")
        print(f"   📋 Total leads: {stats['total']}")
        print(f"   🧠 Enriched leads: {stats['enriched']}")
        print(f"   📤 Synced leads: {stats['synced']}")
        print(f"   🕐 Recently enriched: {stats['recent_enriched']}")
    
    # Check autonomous system status
    print(f"\n🤖 AUTONOMOUS SYSTEM STATUS:")
    system_running = checker.check_autonomous_system_status()
    
    # Sync enriched leads to Airtable
    print(f"\n📤 SYNCING TO AIRTABLE:")
    synced_count = checker.sync_enriched_leads_to_airtable()
    
    # Provide recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    
    if synced_count > 0:
        print(f"   ✅ {synced_count} leads synced to Airtable")
    
    if not system_running:
        print("   ⚠️ Autonomous system is not running")
        restart = input("   🔄 Restart autonomous system? (y/n): ").lower().strip()
        if restart == 'y':
            if checker.restart_autonomous_system():
                print("   ✅ Autonomous system restarted")
            else:
                print("   ❌ Failed to restart autonomous system")
    else:
        print("   ✅ Autonomous system is running")
    
    # Final status
    print(f"\n🎉 SYSTEM STATUS SUMMARY:")
    print(f"   📊 Database: {stats['total'] if stats else 'Unknown'} total leads")
    print(f"   📤 Airtable: {synced_count} leads just synced")
    print(f"   🤖 Autonomous: {'Running' if system_running else 'Needs restart'}")
    
    print(f"\n📋 Monitor system:")
    print(f"   tail -f logs/autonomous-system.log")

if __name__ == "__main__":
    main()
