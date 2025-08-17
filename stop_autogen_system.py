#!/usr/bin/env python3
"""
Stop AutoGen System
===================
Find and stop the AutoGen system creating fake LinkedIn URLs
"""

import subprocess
import os
import signal
import sqlite3
from datetime import datetime
import json

class AutoGenStopper:
    def __init__(self):
        self.processes_found = []
        self.services_found = []
        self.cron_jobs_found = []
        
    def find_running_processes(self):
        """Find running processes related to AutoGen"""
        print("🔍 FINDING AUTOGEN PROCESSES")
        print("=" * 40)
        
        try:
            # Check for python processes with AutoGen in name or command
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.split('\n')
            
            autogen_processes = []
            for process in processes:
                if 'python' in process.lower() and any(keyword in process.lower() for keyword in ['autogen', 'auto_gen', 'generator', 'mock']):
                    autogen_processes.append(process)
                    print(f"🚨 Found process: {process}")
            
            self.processes_found = autogen_processes
            
            if not autogen_processes:
                print("✅ No AutoGen processes currently running")
            
            return autogen_processes
            
        except Exception as e:
            print(f"❌ Error finding processes: {e}")
            return []
    
    def check_systemd_services(self):
        """Check for systemd services that might be running AutoGen"""
        print("\n🔍 CHECKING SYSTEMD SERVICES")
        print("=" * 40)
        
        services_to_check = [
            'autogen',
            'auto-gen',
            'lead-generator',
            'mock-generator',
            'data-generator',
            'clean-enrichment',
            'scraper',
            'lead-scraper'
        ]
        
        active_services = []
        
        for service in services_to_check:
            try:
                result = subprocess.run(['systemctl', 'is-active', f'{service}.service'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and 'active' in result.stdout:
                    active_services.append(service)
                    print(f"🚨 Active service: {service}.service")
                    
                    # Get service details
                    status_result = subprocess.run(['systemctl', 'status', f'{service}.service'], 
                                                 capture_output=True, text=True)
                    print(f"   Status: {status_result.stdout[:200]}...")
                    
            except Exception as e:
                print(f"   Error checking {service}: {e}")
        
        self.services_found = active_services
        
        if not active_services:
            print("✅ No suspicious systemd services running")
        
        return active_services
    
    def check_cron_jobs(self):
        """Check for cron jobs that might be generating fake data"""
        print("\n🔍 CHECKING CRON JOBS")
        print("=" * 40)
        
        try:
            # Check system crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                cron_lines = result.stdout.split('\n')
                autogen_crons = [line for line in cron_lines if line.strip() and any(
                    keyword in line.lower() for keyword in ['autogen', 'generator', 'mock', 'fake']
                )]
                
                if autogen_crons:
                    print("🚨 Found suspicious cron jobs:")
                    for cron in autogen_crons:
                        print(f"   {cron}")
                        self.cron_jobs_found.append(cron)
                else:
                    print("✅ No suspicious cron jobs found")
            else:
                print("✅ No user crontab found")
                
        except Exception as e:
            print(f"❌ Error checking cron: {e}")
        
        return self.cron_jobs_found
    
    def check_for_autogen_files(self):
        """Look for AutoGen source files"""
        print("\n🔍 CHECKING FOR AUTOGEN FILES")
        print("=" * 40)
        
        # Common locations to check
        search_paths = [
            '/home/ubuntu/4Runr-AI-Lead-System',
            '/home/ubuntu',
            '/opt',
            '/usr/local'
        ]
        
        autogen_files = []
        
        for path in search_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run(['find', path, '-name', '*autogen*', '-o', '-name', '*AutoGen*'], 
                                          capture_output=True, text=True)
                    files = [f for f in result.stdout.split('\n') if f.strip()]
                    
                    for file in files:
                        if os.path.isfile(file):
                            print(f"📄 Found AutoGen file: {file}")
                            autogen_files.append(file)
                            
                except Exception as e:
                    print(f"❌ Error searching {path}: {e}")
        
        return autogen_files
    
    def stop_autogen_processes(self, confirm_stop=False):
        """Stop running AutoGen processes"""
        print("\n🛑 STOPPING AUTOGEN PROCESSES")
        print("=" * 40)
        
        if not self.processes_found and not self.services_found:
            print("✅ No AutoGen processes to stop")
            return True
        
        if not confirm_stop:
            print("⚠️ SIMULATION MODE - Not actually stopping processes")
            print("To actually stop processes, run with confirm_stop=True")
            return False
        
        stopped_count = 0
        
        # Stop systemd services
        for service in self.services_found:
            try:
                print(f"🛑 Stopping service: {service}.service")
                result = subprocess.run(['sudo', 'systemctl', 'stop', f'{service}.service'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ Stopped {service}.service")
                    stopped_count += 1
                else:
                    print(f"   ❌ Failed to stop {service}.service: {result.stderr}")
            except Exception as e:
                print(f"   ❌ Error stopping {service}: {e}")
        
        # Kill processes (extract PIDs)
        for process_line in self.processes_found:
            try:
                # Extract PID (second column in ps aux output)
                parts = process_line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    print(f"🛑 Killing process PID: {pid}")
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"   ✅ Killed PID {pid}")
                    stopped_count += 1
            except Exception as e:
                print(f"   ❌ Error killing process: {e}")
        
        print(f"🎯 Stopped {stopped_count} AutoGen processes/services")
        return stopped_count > 0
    
    def disable_autogen_services(self, confirm_disable=False):
        """Disable AutoGen services from starting automatically"""
        print("\n🚫 DISABLING AUTOGEN SERVICES")
        print("=" * 40)
        
        if not self.services_found:
            print("✅ No services to disable")
            return True
        
        if not confirm_disable:
            print("⚠️ SIMULATION MODE - Not actually disabling services")
            return False
        
        disabled_count = 0
        
        for service in self.services_found:
            try:
                print(f"🚫 Disabling service: {service}.service")
                result = subprocess.run(['sudo', 'systemctl', 'disable', f'{service}.service'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ Disabled {service}.service")
                    disabled_count += 1
                else:
                    print(f"   ❌ Failed to disable {service}.service: {result.stderr}")
            except Exception as e:
                print(f"   ❌ Error disabling {service}: {e}")
        
        print(f"🎯 Disabled {disabled_count} AutoGen services")
        return disabled_count > 0
    
    def comprehensive_autogen_stop(self, confirm_changes=False):
        """Complete AutoGen system shutdown"""
        print("🚨 COMPREHENSIVE AUTOGEN SYSTEM SHUTDOWN")
        print("=" * 60)
        print("Finding and stopping all AutoGen fake data generation")
        print("")
        
        # Step 1: Find everything
        processes = self.find_running_processes()
        services = self.check_systemd_services()
        crons = self.check_cron_jobs()
        files = self.check_for_autogen_files()
        
        # Step 2: Stop active processes/services
        stopped = self.stop_autogen_processes(confirm_changes)
        disabled = self.disable_autogen_services(confirm_changes)
        
        # Step 3: Summary
        results = {
            'timestamp': datetime.now().isoformat(),
            'processes_found': len(processes),
            'services_found': len(services),
            'cron_jobs_found': len(crons),
            'files_found': len(files),
            'processes_stopped': stopped,
            'services_disabled': disabled,
            'simulation_mode': not confirm_changes
        }
        
        print(f"\n🎯 AUTOGEN SHUTDOWN RESULTS")
        print("=" * 40)
        print(f"📊 Processes found: {results['processes_found']}")
        print(f"📊 Services found: {results['services_found']}")
        print(f"📊 Cron jobs found: {results['cron_jobs_found']}")
        print(f"📊 Files found: {results['files_found']}")
        print(f"🛑 Processes stopped: {results['processes_stopped']}")
        print(f"🚫 Services disabled: {results['services_disabled']}")
        print(f"⚠️ Mode: {'SIMULATION' if not confirm_changes else 'CHANGES APPLIED'}")
        
        # Save report
        report_file = f"autogen_shutdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📊 Report saved to: {report_file}")
        
        if not confirm_changes:
            print(f"\n⚠️ TO ACTUALLY STOP AUTOGEN:")
            print(f"python3 stop_autogen_system.py --stop")
        
        return results

def main():
    """Run AutoGen system stopper"""
    import sys
    
    print("🛑 AutoGen System Stopper")
    print("Finds and stops fake LinkedIn URL generation")
    print("")
    
    try:
        stopper = AutoGenStopper()
        
        # Check for stop flag
        confirm_changes = '--stop' in sys.argv
        
        results = stopper.comprehensive_autogen_stop(confirm_changes)
        
        if results['processes_found'] > 0 or results['services_found'] > 0:
            if confirm_changes:
                print("🎉 AUTOGEN SYSTEM STOPPED!")
                print("✅ No more fake LinkedIn URLs should be generated")
            else:
                print("🚨 AUTOGEN SYSTEM IS RUNNING!")
                print("⚠️ Run with --stop flag to actually stop it")
        else:
            print("✅ No AutoGen system detected")
        
        return 0
        
    except Exception as e:
        print(f"❌ AutoGen stop failed: {e}")
        return 1

if __name__ == "__main__":
    main()
