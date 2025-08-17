#!/usr/bin/env python3
"""
Security Audit
==============
Comprehensive security verification of ports, data, and infrastructure
"""

import subprocess
import os
import json
import socket
import requests
from datetime import datetime
import re

class SecurityAuditor:
    def __init__(self):
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'security_status': 'CHECKING',
            'vulnerabilities': [],
            'recommendations': []
        }
    
    def check_open_ports(self):
        """Check for open ports and services"""
        print("🔒 CHECKING OPEN PORTS & SERVICES")
        print("=" * 50)
        
        try:
            # Check listening ports
            result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True)
            
            open_ports = []
            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        address = parts[3]
                        process = parts[-1] if len(parts) > 6 else 'unknown'
                        
                        # Extract port
                        if ':' in address:
                            port = address.split(':')[-1]
                            open_ports.append({
                                'port': port,
                                'address': address,
                                'process': process
                            })
            
            print(f"🔍 Found {len(open_ports)} listening ports:")
            
            critical_ports = []
            for port_info in open_ports:
                port = port_info['port']
                process = port_info['process']
                address = port_info['address']
                
                # Check for security concerns
                status = "🟢"
                notes = ""
                
                if port in ['22']:  # SSH
                    status = "🟡"
                    notes = "SSH - ensure key-based auth"
                elif port in ['80', '8080']:  # HTTP
                    status = "🟡" 
                    notes = "HTTP - should use HTTPS"
                elif port in ['443', '8443']:  # HTTPS
                    status = "🟢"
                    notes = "HTTPS - secure"
                elif port in ['3306', '5432', '27017']:  # Databases
                    status = "🔴"
                    notes = "Database - should not be exposed"
                    critical_ports.append(port_info)
                elif '0.0.0.0' in address:  # Exposed to all interfaces
                    status = "🟡"
                    notes = "Exposed to all interfaces"
                
                print(f"   {status} Port {port}: {process} ({notes})")
            
            if critical_ports:
                self.audit_results['vulnerabilities'].append({
                    'type': 'EXPOSED_DATABASES',
                    'severity': 'HIGH',
                    'ports': critical_ports,
                    'description': 'Database ports exposed to network'
                })
            
            return open_ports
            
        except Exception as e:
            print(f"❌ Error checking ports: {e}")
            return []
    
    def check_firewall_status(self):
        """Check firewall configuration"""
        print("\n🛡️ CHECKING FIREWALL STATUS")
        print("=" * 50)
        
        try:
            # Check UFW status
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
            
            if 'Status: active' in result.stdout:
                print("✅ UFW firewall is active")
                
                # Show rules
                rules = []
                for line in result.stdout.split('\n'):
                    if 'ALLOW' in line or 'DENY' in line:
                        rules.append(line.strip())
                        print(f"   📋 {line.strip()}")
                
                return {'status': 'active', 'rules': rules}
            else:
                print("🔴 UFW firewall is inactive")
                self.audit_results['vulnerabilities'].append({
                    'type': 'FIREWALL_DISABLED',
                    'severity': 'HIGH',
                    'description': 'System firewall is not active'
                })
                return {'status': 'inactive', 'rules': []}
                
        except Exception as e:
            print(f"❌ Error checking firewall: {e}")
            return {'status': 'unknown', 'rules': []}
    
    def check_ssh_security(self):
        """Check SSH security configuration"""
        print("\n🔑 CHECKING SSH SECURITY")
        print("=" * 50)
        
        ssh_config = '/etc/ssh/sshd_config'
        
        if not os.path.exists(ssh_config):
            print("⚠️ SSH config file not found")
            return {}
        
        try:
            with open(ssh_config, 'r') as f:
                config_content = f.read()
            
            security_checks = {
                'PasswordAuthentication': 'no',
                'PermitRootLogin': 'no',
                'Protocol': '2'
            }
            
            ssh_status = {}
            
            for setting, secure_value in security_checks.items():
                # Look for setting in config
                pattern = rf'^{setting}\s+(.+)$'
                match = re.search(pattern, config_content, re.MULTILINE | re.IGNORECASE)
                
                if match:
                    current_value = match.group(1).strip()
                    ssh_status[setting] = current_value
                    
                    if current_value.lower() == secure_value.lower():
                        print(f"✅ {setting}: {current_value}")
                    else:
                        print(f"🔴 {setting}: {current_value} (should be {secure_value})")
                        self.audit_results['vulnerabilities'].append({
                            'type': 'SSH_INSECURE_CONFIG',
                            'severity': 'MEDIUM',
                            'setting': setting,
                            'current': current_value,
                            'recommended': secure_value
                        })
                else:
                    print(f"⚠️ {setting}: not explicitly set")
                    ssh_status[setting] = 'default'
            
            return ssh_status
            
        except Exception as e:
            print(f"❌ Error checking SSH config: {e}")
            return {}
    
    def check_file_permissions(self):
        """Check critical file permissions"""
        print("\n📁 CHECKING FILE PERMISSIONS")
        print("=" * 50)
        
        critical_files = [
            {'path': '~/.ssh/authorized_keys', 'expected': '600'},
            {'path': '~/.ssh/id_rsa', 'expected': '600'},
            {'path': '/etc/ssh/sshd_config', 'expected': '644'},
            {'path': os.path.expanduser('~/.bashrc'), 'expected': '644'},
            {'path': 'data/unified_leads.db', 'expected': '640'}
        ]
        
        permission_issues = []
        
        for file_info in critical_files:
            file_path = os.path.expanduser(file_info['path'])
            expected = file_info['expected']
            
            if os.path.exists(file_path):
                try:
                    stat_info = os.stat(file_path)
                    actual_perms = oct(stat_info.st_mode)[-3:]
                    
                    if actual_perms == expected:
                        print(f"✅ {file_path}: {actual_perms}")
                    else:
                        print(f"🔴 {file_path}: {actual_perms} (should be {expected})")
                        permission_issues.append({
                            'file': file_path,
                            'current': actual_perms,
                            'expected': expected
                        })
                except Exception as e:
                    print(f"❌ Error checking {file_path}: {e}")
            else:
                print(f"⚠️ {file_path}: not found")
        
        if permission_issues:
            self.audit_results['vulnerabilities'].append({
                'type': 'INSECURE_FILE_PERMISSIONS',
                'severity': 'MEDIUM',
                'files': permission_issues
            })
        
        return permission_issues
    
    def check_environment_variables(self):
        """Check for exposed sensitive environment variables"""
        print("\n🔐 CHECKING ENVIRONMENT VARIABLES")
        print("=" * 50)
        
        sensitive_vars = [
            'AIRTABLE_API_KEY',
            'SERPAPI_KEY',
            'OPENAI_API_KEY',
            'DATABASE_PASSWORD',
            'SECRET_KEY'
        ]
        
        exposed_vars = []
        
        for var in sensitive_vars:
            value = os.getenv(var)
            if value:
                # Check if it's properly secured (not default/weak)
                if len(value) < 20:
                    print(f"🔴 {var}: Too short ({len(value)} chars)")
                    exposed_vars.append({'var': var, 'issue': 'too_short'})
                elif value in ['test', 'default', 'changeme', 'password']:
                    print(f"🔴 {var}: Weak value")
                    exposed_vars.append({'var': var, 'issue': 'weak_value'})
                else:
                    print(f"✅ {var}: Set securely ({len(value)} chars)")
            else:
                print(f"⚠️ {var}: Not set")
        
        return exposed_vars
    
    def check_system_updates(self):
        """Check for available security updates"""
        print("\n🔄 CHECKING SYSTEM UPDATES")
        print("=" * 50)
        
        try:
            # Check for security updates
            result = subprocess.run(['apt', 'list', '--upgradable'], capture_output=True, text=True)
            
            if result.returncode == 0:
                upgradable = result.stdout.count('\n') - 1  # Subtract header line
                
                if upgradable > 0:
                    print(f"⚠️ {upgradable} packages can be upgraded")
                    
                    # Check for security updates specifically
                    security_result = subprocess.run(['apt', 'list', '--upgradable'], 
                                                   capture_output=True, text=True)
                    security_updates = [line for line in security_result.stdout.split('\n') 
                                      if 'security' in line.lower()]
                    
                    if security_updates:
                        print(f"🔴 {len(security_updates)} security updates available")
                        self.audit_results['vulnerabilities'].append({
                            'type': 'SECURITY_UPDATES_AVAILABLE',
                            'severity': 'MEDIUM',
                            'count': len(security_updates)
                        })
                else:
                    print("✅ System is up to date")
            
            return upgradable
            
        except Exception as e:
            print(f"❌ Error checking updates: {e}")
            return 0
    
    def check_data_encryption(self):
        """Check data encryption status"""
        print("\n🔒 CHECKING DATA ENCRYPTION")
        print("=" * 50)
        
        # Check database file encryption
        db_path = 'data/unified_leads.db'
        
        if os.path.exists(db_path):
            try:
                with open(db_path, 'rb') as f:
                    header = f.read(16)
                
                # SQLite files start with "SQLite format 3"
                if b'SQLite format 3' in header:
                    print("🔴 Database is not encrypted")
                    self.audit_results['vulnerabilities'].append({
                        'type': 'UNENCRYPTED_DATABASE',
                        'severity': 'HIGH',
                        'file': db_path,
                        'description': 'Lead database contains unencrypted sensitive data'
                    })
                else:
                    print("🟡 Database may be encrypted (cannot confirm)")
                    
            except Exception as e:
                print(f"❌ Error checking database encryption: {e}")
        else:
            print("⚠️ Database file not found")
        
        # Check for plaintext files with sensitive data
        sensitive_patterns = [
            'password', 'api_key', 'secret', 'token', 'credential'
        ]
        
        try:
            result = subprocess.run(['find', '.', '-name', '*.txt', '-o', '-name', '*.log'], 
                                  capture_output=True, text=True)
            
            for file_path in result.stdout.split('\n'):
                if file_path.strip():
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            
                        for pattern in sensitive_patterns:
                            if pattern in content:
                                print(f"⚠️ Potential sensitive data in: {file_path}")
                                break
                    except:
                        pass  # Skip binary or unreadable files
                        
        except Exception as e:
            print(f"❌ Error scanning for sensitive files: {e}")
    
    def comprehensive_security_audit(self):
        """Run complete security audit"""
        print("🔒 COMPREHENSIVE SECURITY AUDIT")
        print("=" * 60)
        print("Verifying system security and data protection")
        print("")
        
        # Run all security checks
        open_ports = self.check_open_ports()
        firewall = self.check_firewall_status()
        ssh_security = self.check_ssh_security()
        file_perms = self.check_file_permissions()
        env_vars = self.check_environment_variables()
        updates = self.check_system_updates()
        self.check_data_encryption()
        
        # Calculate security score
        total_vulnerabilities = len(self.audit_results['vulnerabilities'])
        high_severity = len([v for v in self.audit_results['vulnerabilities'] if v['severity'] == 'HIGH'])
        medium_severity = len([v for v in self.audit_results['vulnerabilities'] if v['severity'] == 'MEDIUM'])
        
        if high_severity > 0:
            security_status = 'CRITICAL'
        elif medium_severity > 2:
            security_status = 'POOR'
        elif total_vulnerabilities > 0:
            security_status = 'FAIR'
        else:
            security_status = 'GOOD'
        
        self.audit_results['security_status'] = security_status
        
        # Generate recommendations
        if firewall['status'] != 'active':
            self.audit_results['recommendations'].append("Enable UFW firewall: sudo ufw enable")
        
        if high_severity > 0:
            self.audit_results['recommendations'].append("Address HIGH severity vulnerabilities immediately")
        
        if updates > 0:
            self.audit_results['recommendations'].append("Update system packages: sudo apt update && sudo apt upgrade")
        
        # Security summary
        print(f"\n🎯 SECURITY SUMMARY")
        print("=" * 40)
        print(f"🔒 Security Status: {security_status}")
        print(f"🚨 Total Vulnerabilities: {total_vulnerabilities}")
        print(f"🔴 High Severity: {high_severity}")
        print(f"🟡 Medium Severity: {medium_severity}")
        print(f"🔧 Open Ports: {len(open_ports)}")
        print(f"🛡️ Firewall: {firewall['status']}")
        
        if self.audit_results['recommendations']:
            print(f"\n📋 SECURITY RECOMMENDATIONS:")
            for i, rec in enumerate(self.audit_results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Save security report
        report_file = f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
        print(f"\n📊 Security report saved to: {report_file}")
        
        return self.audit_results

def main():
    """Run security audit"""
    print("🔒 Security Audit")
    print("Comprehensive security verification")
    print("")
    
    try:
        auditor = SecurityAuditor()
        report = auditor.comprehensive_security_audit()
        
        if report['security_status'] in ['CRITICAL', 'POOR']:
            print(f"\n🚨 URGENT: Security status is {report['security_status']}")
            print("Address vulnerabilities immediately!")
        elif report['security_status'] == 'FAIR':
            print(f"\n⚠️ Security status is {report['security_status']}")
            print("Consider implementing recommended improvements")
        else:
            print(f"\n✅ Security status is {report['security_status']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Security audit failed: {e}")
        return 1

if __name__ == "__main__":
    main()
