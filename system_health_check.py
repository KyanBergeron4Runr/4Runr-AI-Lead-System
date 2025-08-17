#!/usr/bin/env python3
"""
System Health Check
==================
Verify what's running and check data field completeness
"""

import subprocess
import sqlite3
import os
import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict

class SystemHealthChecker:
    def __init__(self):
        self.db_path = 'data/unified_leads.db'
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_id = 'tblbBSE2jJv9am7ZA'
    
    def check_running_processes(self):
        """Check what Python processes are currently running"""
        print("🔍 CHECKING RUNNING PROCESSES")
        print("=" * 50)
        
        try:
            # Get all Python processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.split('\n')
            
            python_processes = []
            for process in processes:
                if 'python' in process.lower() and 'ubuntu' in process:
                    parts = process.split()
                    if len(parts) > 10:
                        pid = parts[1]
                        command = ' '.join(parts[10:])
                        cpu = parts[2]
                        memory = parts[3]
                        
                        python_processes.append({
                            'pid': pid,
                            'command': command,
                            'cpu': cpu,
                            'memory': memory
                        })
            
            print(f"🐍 Found {len(python_processes)} Python processes:")
            for proc in python_processes:
                print(f"   PID {proc['pid']}: {proc['command'][:80]}...")
                print(f"      CPU: {proc['cpu']}%, Memory: {proc['memory']}%")
            
            return python_processes
            
        except Exception as e:
            print(f"❌ Error checking processes: {e}")
            return []
    
    def check_systemd_services(self):
        """Check active systemd services"""
        print("\n⚙️ CHECKING SYSTEMD SERVICES")
        print("=" * 50)
        
        try:
            # Check all active services
            result = subprocess.run(['systemctl', 'list-units', '--type=service', '--state=active'], 
                                  capture_output=True, text=True)
            
            services = []
            for line in result.stdout.split('\n'):
                if any(keyword in line.lower() for keyword in ['4runr', 'organism', 'lead', 'scraper', 'enricher']):
                    services.append(line.strip())
            
            print(f"🔧 Found {len(services)} relevant active services:")
            for service in services:
                print(f"   {service}")
            
            return services
            
        except Exception as e:
            print(f"❌ Error checking services: {e}")
            return []
    
    def check_cron_jobs(self):
        """Check active cron jobs"""
        print("\n⏰ CHECKING CRON JOBS")
        print("=" * 50)
        
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            if result.returncode == 0:
                cron_lines = [line for line in result.stdout.split('\n') if line.strip() and not line.startswith('#')]
                print(f"📅 Found {len(cron_lines)} active cron jobs:")
                for line in cron_lines:
                    print(f"   {line}")
                return cron_lines
            else:
                print("✅ No user cron jobs found")
                return []
                
        except Exception as e:
            print(f"❌ Error checking cron: {e}")
            return []
    
    def analyze_database_fields(self):
        """Analyze database field completeness"""
        print("\n📊 DATABASE FIELD ANALYSIS")
        print("=" * 50)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all columns
            cursor = conn.execute("PRAGMA table_info(leads)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Get all records
            cursor = conn.execute("SELECT * FROM leads ORDER BY created_at DESC")
            records = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            print(f"📋 Database has {len(columns)} columns and {len(records)} records")
            
            # Analyze field completeness
            field_stats = {}
            for col in columns:
                filled = sum(1 for record in records if record.get(col) not in [None, '', 'NULL'])
                field_stats[col] = {
                    'filled': filled,
                    'empty': len(records) - filled,
                    'fill_rate': (filled / len(records) * 100) if records else 0
                }
            
            print(f"\n📊 FIELD COMPLETENESS:")
            for field, stats in sorted(field_stats.items(), key=lambda x: x[1]['fill_rate']):
                fill_rate = stats['fill_rate']
                status = "🔴" if fill_rate < 50 else "🟡" if fill_rate < 90 else "🟢"
                print(f"   {status} {field}: {fill_rate:.1f}% ({stats['filled']}/{len(records)})")
            
            # Check recent records
            recent_cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            recent_records = [r for r in records if r.get('created_at', '') > recent_cutoff]
            
            print(f"\n📅 Recent records (24h): {len(recent_records)}")
            if recent_records:
                print("   Latest record fields:")
                latest = recent_records[0]
                for field, value in latest.items():
                    status = "✅" if value not in [None, '', 'NULL'] else "❌"
                    print(f"   {status} {field}: {str(value)[:50]}...")
            
            return field_stats, records
            
        except Exception as e:
            print(f"❌ Error analyzing database: {e}")
            return {}, []
    
    def check_airtable_sync(self):
        """Check Airtable connectivity and data sync"""
        print("\n🔗 AIRTABLE SYNC CHECK")
        print("=" * 50)
        
        if not self.api_key:
            print("❌ AIRTABLE_API_KEY not set")
            return False
        
        try:
            url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}'
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = requests.get(url, headers=headers, params={'maxRecords': 5})
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                print(f"✅ Airtable connected: {len(records)} sample records")
                
                if records:
                    latest = records[0]['fields']
                    print("   Latest Airtable record fields:")
                    for field, value in latest.items():
                        status = "✅" if value not in [None, '', 'NULL'] else "❌"
                        print(f"   {status} {field}: {str(value)[:50]}...")
                
                return True
            else:
                print(f"❌ Airtable error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Airtable check failed: {e}")
            return False
    
    def check_log_files(self):
        """Check recent log activity"""
        print("\n📋 LOG FILE ANALYSIS")
        print("=" * 50)
        
        log_dirs = ['logs/', '4runr-outreach-system/logs/', 'production_clean_system/logs/']
        
        recent_logs = []
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                try:
                    for file in os.listdir(log_dir):
                        if file.endswith('.log'):
                            filepath = os.path.join(log_dir, file)
                            stat = os.stat(filepath)
                            
                            # Check if modified in last 24 hours
                            if datetime.now().timestamp() - stat.st_mtime < 86400:
                                recent_logs.append({
                                    'file': filepath,
                                    'size': stat.st_size,
                                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                                })
                except Exception as e:
                    print(f"⚠️ Error reading {log_dir}: {e}")
        
        print(f"📋 Found {len(recent_logs)} recently active log files:")
        for log in sorted(recent_logs, key=lambda x: x['modified'], reverse=True):
            print(f"   {log['file']} - {log['size']} bytes - {log['modified']}")
        
        return recent_logs
    
    def comprehensive_health_check(self):
        """Run complete system health check"""
        print("🔍 COMPREHENSIVE SYSTEM HEALTH CHECK")
        print("=" * 60)
        print("Checking system status and data completeness")
        print("")
        
        # Run all checks
        processes = self.check_running_processes()
        services = self.check_systemd_services()
        crons = self.check_cron_jobs()
        field_stats, records = self.analyze_database_fields()
        airtable_ok = self.check_airtable_sync()
        logs = self.check_log_files()
        
        # Generate health report
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'system_status': {
                'python_processes': len(processes),
                'active_services': len(services),
                'cron_jobs': len(crons),
                'recent_logs': len(logs)
            },
            'data_status': {
                'total_records': len(records),
                'field_completeness': field_stats,
                'airtable_connected': airtable_ok
            },
            'processes': processes,
            'services': services,
            'crons': crons,
            'logs': logs
        }
        
        # Summary
        print(f"\n🎯 HEALTH SUMMARY")
        print("=" * 40)
        print(f"🐍 Python processes: {len(processes)}")
        print(f"⚙️ Active services: {len(services)}")
        print(f"⏰ Cron jobs: {len(crons)}")
        print(f"📊 Database records: {len(records)}")
        print(f"🔗 Airtable connected: {'✅' if airtable_ok else '❌'}")
        print(f"📋 Recent logs: {len(logs)}")
        
        # Data quality assessment
        if field_stats:
            low_quality_fields = [f for f, s in field_stats.items() if s['fill_rate'] < 70]
            if low_quality_fields:
                print(f"\n⚠️ FIELDS NEEDING ATTENTION:")
                for field in low_quality_fields:
                    print(f"   🔴 {field}: {field_stats[field]['fill_rate']:.1f}% complete")
            else:
                print(f"\n✅ All fields have good data coverage (>70%)")
        
        # Save report
        report_file = f"system_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(health_report, f, indent=2, default=str)
        
        print(f"\n📊 Detailed report saved to: {report_file}")
        
        return health_report

def main():
    """Run system health check"""
    print("🔍 System Health Check")
    print("Verifying system status and data completeness")
    print("")
    
    try:
        checker = SystemHealthChecker()
        report = checker.comprehensive_health_check()
        
        print(f"\n🎯 RECOMMENDATIONS:")
        
        # Process recommendations
        if report['system_status']['python_processes'] == 0:
            print("⚠️ No Python processes running - system may be idle")
        elif report['system_status']['python_processes'] > 5:
            print("⚠️ Many Python processes running - check for duplicates")
        
        # Data recommendations
        if not report['data_status']['airtable_connected']:
            print("🔴 Fix Airtable connection issues")
        
        if report['data_status']['total_records'] == 0:
            print("🔴 No records in database - system may not be working")
        
        print("\n✅ System health check completed!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1

if __name__ == "__main__":
    main()
