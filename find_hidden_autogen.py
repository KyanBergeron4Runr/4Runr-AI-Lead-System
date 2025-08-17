#!/usr/bin/env python3
"""
Find Hidden AutoGen Source
===========================
Deep search for what's creating AutoGen_YYYYMMDD_HHMMSS entries
"""

import subprocess
import os
import sqlite3
import json
from datetime import datetime, timedelta
import re

class HiddenAutoGenFinder:
    def __init__(self):
        self.evidence = []
        
    def analyze_autogen_timing(self):
        """Analyze the exact timing pattern of AutoGen entries"""
        print("📊 ANALYZING AUTOGEN TIMING PATTERN")
        print("=" * 50)
        
        conn = sqlite3.connect('data/unified_leads.db')
        conn.row_factory = sqlite3.Row
        
        # Get all AutoGen entries with precise timestamps
        cursor = conn.execute('''
            SELECT source, created_at, full_name, linkedin_url, COUNT(*) as count
            FROM leads 
            WHERE source LIKE 'AutoGen_%'
            ORDER BY created_at DESC
            LIMIT 50
        ''')
        
        autogen_entries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"📊 Found {len(autogen_entries)} AutoGen entries")
        
        # Analyze timing patterns
        timing_analysis = {}
        for entry in autogen_entries:
            timestamp = entry['created_at']
            source = entry['source']
            
            # Extract time components
            try:
                dt = datetime.fromisoformat(timestamp)
                hour = dt.hour
                minute = dt.minute
                time_key = f"{hour:02d}:{minute:02d}"
                
                if time_key not in timing_analysis:
                    timing_analysis[time_key] = []
                timing_analysis[time_key].append({
                    'source': source,
                    'timestamp': timestamp,
                    'count': entry['count']
                })
            except:
                pass
        
        print(f"📊 Timing pattern analysis:")
        for time_key, entries in sorted(timing_analysis.items()):
            print(f"   {time_key}: {len(entries)} batches")
            if len(entries) >= 2:  # Show frequent times
                print(f"      Most recent: {entries[0]['source']}")
        
        return timing_analysis, autogen_entries
    
    def search_for_scheduler_code(self):
        """Search for code that might be scheduling AutoGen"""
        print("\n🔍 SEARCHING FOR SCHEDULER CODE")
        print("=" * 50)
        
        search_patterns = [
            'AutoGen_',
            'schedule',
            'cron',
            'timer',
            'interval',
            '1749',
            'every.*hour',
            'linkedin.*\d+',
            'fake.*url',
            'mock.*linkedin'
        ]
        
        search_paths = [
            '.',
            '4runr-brain',
            '4runr-lead-scraper', 
            '4runr-outreach-system',
            'production_clean_system',
            'archived_systems'
        ]
        
        found_files = {}
        
        for pattern in search_patterns:
            found_files[pattern] = []
            
            for path in search_paths:
                if os.path.exists(path):
                    try:
                        # Search for pattern in Python files
                        result = subprocess.run([
                            'grep', '-r', '-l', '--include=*.py', pattern, path
                        ], capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            files = result.stdout.strip().split('\n')
                            for file in files:
                                if file and file not in found_files[pattern]:
                                    found_files[pattern].append(file)
                                    print(f"🔍 Found '{pattern}' in: {file}")
                    except Exception as e:
                        pass
        
        return found_files
    
    def check_running_python_processes(self):
        """Check all running Python processes for AutoGen clues"""
        print("\n🔍 CHECKING ALL PYTHON PROCESSES")
        print("=" * 50)
        
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.split('\n')
            
            python_processes = []
            for process in processes:
                if 'python' in process and 'ubuntu' in process:
                    # Extract command and arguments
                    parts = process.split()
                    if len(parts) > 10:
                        command = ' '.join(parts[10:])
                        python_processes.append({
                            'pid': parts[1],
                            'command': command,
                            'full_line': process
                        })
                        print(f"🐍 Python process: PID {parts[1]} - {command}")
            
            return python_processes
            
        except Exception as e:
            print(f"❌ Error checking processes: {e}")
            return []
    
    def check_systemd_timers(self):
        """Check for systemd timers that might trigger AutoGen"""
        print("\n⏰ CHECKING SYSTEMD TIMERS")
        print("=" * 50)
        
        try:
            result = subprocess.run(['systemctl', 'list-timers'], capture_output=True, text=True)
            if result.returncode == 0:
                timers = result.stdout.split('\n')
                
                relevant_timers = []
                for timer in timers:
                    if any(keyword in timer.lower() for keyword in ['lead', 'scraper', 'gen', 'auto']):
                        relevant_timers.append(timer)
                        print(f"⏰ Relevant timer: {timer}")
                
                if not relevant_timers:
                    print("✅ No relevant systemd timers found")
                
                return relevant_timers
            else:
                print("❌ Could not list systemd timers")
                return []
                
        except Exception as e:
            print(f"❌ Error checking timers: {e}")
            return []
    
    def search_log_files(self):
        """Search log files for AutoGen generation clues"""
        print("\n📋 SEARCHING LOG FILES FOR AUTOGEN CLUES")
        print("=" * 50)
        
        log_locations = [
            'logs/',
            '*/logs/',
            'production_clean_system/logs/',
            '/var/log/',
            '/var/log/syslog*'
        ]
        
        autogen_logs = []
        
        for location in log_locations:
            try:
                # Find log files
                result = subprocess.run(['find', '.', '-path', location, '-type', 'f'], 
                                      capture_output=True, text=True)
                
                log_files = result.stdout.strip().split('\n')
                
                for log_file in log_files:
                    if log_file and os.path.isfile(log_file):
                        try:
                            # Search for AutoGen in logs
                            search_result = subprocess.run(['grep', '-l', 'AutoGen', log_file], 
                                                         capture_output=True, text=True)
                            if search_result.returncode == 0:
                                print(f"📋 Found AutoGen in log: {log_file}")
                                autogen_logs.append(log_file)
                                
                                # Show recent AutoGen entries
                                recent_result = subprocess.run(['grep', 'AutoGen', log_file], 
                                                             capture_output=True, text=True)
                                if recent_result.returncode == 0:
                                    lines = recent_result.stdout.split('\n')[-5:]  # Last 5 lines
                                    for line in lines:
                                        if line.strip():
                                            print(f"   📝 {line[:100]}...")
                        except:
                            pass
            except:
                pass
        
        return autogen_logs
    
    def predict_next_autogen(self, timing_analysis):
        """Predict when the next AutoGen will run"""
        print("\n🔮 PREDICTING NEXT AUTOGEN")
        print("=" * 50)
        
        # Look for the pattern (every 3 hours at minute 17)
        common_times = []
        for time_key, entries in timing_analysis.items():
            if len(entries) >= 2:  # Frequent times
                common_times.append(time_key)
        
        print(f"📊 Common AutoGen times: {common_times}")
        
        # Predict next occurrence
        now = datetime.now()
        next_predictions = []
        
        # Known pattern: XX:17 every 3 hours
        for hour in range(0, 24, 3):
            next_time = now.replace(hour=hour, minute=17, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            
            next_predictions.append(next_time)
        
        # Find the closest future time
        next_autogen = min(next_predictions, key=lambda x: x - now)
        
        time_until = next_autogen - now
        
        print(f"🔮 Next AutoGen predicted: {next_autogen.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Time remaining: {time_until}")
        
        if time_until.total_seconds() < 3600:  # Less than 1 hour
            print(f"🚨 WARNING: Next AutoGen in less than 1 hour!")
        
        return next_autogen, time_until
    
    def comprehensive_search(self):
        """Complete search for hidden AutoGen source"""
        print("🕵️ COMPREHENSIVE HIDDEN AUTOGEN SEARCH")
        print("=" * 60)
        print("Finding the mysterious AutoGen system generating fake URLs")
        print("")
        
        # Analyze timing
        timing_analysis, autogen_entries = self.analyze_autogen_timing()
        
        # Search code
        found_files = self.search_for_scheduler_code()
        
        # Check processes
        python_processes = self.check_running_python_processes()
        
        # Check timers
        timers = self.check_systemd_timers()
        
        # Search logs
        autogen_logs = self.search_log_files()
        
        # Predict next
        next_autogen, time_until = self.predict_next_autogen(timing_analysis)
        
        # Summary
        results = {
            'timestamp': datetime.now().isoformat(),
            'autogen_entries_count': len(autogen_entries),
            'timing_patterns': len(timing_analysis),
            'code_files_found': sum(len(files) for files in found_files.values()),
            'python_processes': len(python_processes),
            'systemd_timers': len(timers),
            'autogen_logs': len(autogen_logs),
            'next_autogen_predicted': next_autogen.isoformat(),
            'time_until_next': str(time_until)
        }
        
        print(f"\n🎯 SEARCH RESULTS SUMMARY")
        print("=" * 40)
        print(f"📊 AutoGen entries: {results['autogen_entries_count']}")
        print(f"⏰ Timing patterns: {results['timing_patterns']}")
        print(f"📁 Code files found: {results['code_files_found']}")
        print(f"🐍 Python processes: {results['python_processes']}")
        print(f"⏰ Systemd timers: {results['systemd_timers']}")
        print(f"📋 AutoGen logs: {results['autogen_logs']}")
        print(f"🔮 Next AutoGen: {next_autogen.strftime('%H:%M:%S')}")
        print(f"⏳ Time remaining: {time_until}")
        
        # Save detailed report
        detailed_report = {
            **results,
            'timing_analysis': timing_analysis,
            'found_files': found_files,
            'python_processes': python_processes,
            'timers': timers,
            'autogen_logs': autogen_logs
        }
        
        report_file = f"hidden_autogen_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(detailed_report, f, indent=2, default=str)
        
        print(f"📊 Detailed report saved to: {report_file}")
        
        return results

def main():
    """Run hidden AutoGen finder"""
    print("🕵️ Hidden AutoGen Finder")
    print("Searching for the mysterious AutoGen system")
    print("")
    
    try:
        finder = HiddenAutoGenFinder()
        results = finder.comprehensive_search()
        
        if results['code_files_found'] > 0 or results['python_processes'] > 0:
            print(f"\n🔍 POTENTIAL SOURCES FOUND!")
            print(f"Check the detailed report for file locations and process details")
        else:
            print(f"\n🤔 NO OBVIOUS AUTOGEN SOURCE FOUND")
            print(f"The AutoGen might be:")
            print(f"1. Running in a different container/environment")
            print(f"2. Triggered by an external system")
            print(f"3. Hidden in an unexpected location")
            print(f"4. Running as a different user")
        
        return 0
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return 1

if __name__ == "__main__":
    main()
