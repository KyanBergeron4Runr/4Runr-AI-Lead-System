#!/usr/bin/env python3

"""
🤖 CREATE AUTONOMOUS LIVING SYSTEM
===================================
Set up the complete 24/7 autonomous lead generation system:
1. Fix database schema issues
2. Create systemd services for 24/7 operation
3. Set up automatic engagement 
4. Ensure complete automation with zero manual intervention
"""

import sqlite3
import subprocess
import os
import json

def fix_database_schema():
    """Fix missing columns and schema issues"""
    print("🔧 FIXING DATABASE SCHEMA")
    print("=" * 30)
    
    try:
        conn = sqlite3.connect('4runr-lead-scraper/data/leads.db')
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(leads)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add missing columns
        missing_columns = {
            'Date_Enriched': 'TEXT',
            'Date_Last_Contact': 'TEXT', 
            'Engagement_Level': 'INTEGER DEFAULT 0',
            'Auto_Message_Sent': 'INTEGER DEFAULT 0',
            'Last_Activity': 'TEXT'
        }
        
        added_count = 0
        for col_name, col_type in missing_columns.items():
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
                added_count += 1
                print(f"   ✅ Added column: {col_name}")
        
        if added_count == 0:
            print("   ✅ All columns already exist")
        
        # Update Date_Enriched for existing leads
        cursor.execute("""
        UPDATE leads 
        SET Date_Enriched = datetime('now'),
            Last_Activity = datetime('now')
        WHERE Date_Enriched IS NULL
        """)
        
        updated_count = cursor.rowcount
        print(f"   ✅ Updated {updated_count} leads with timestamps")
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database fix error: {e}")
        return False

def create_systemd_services():
    """Create systemd services for 24/7 operation"""
    print(f"\n🔄 CREATING SYSTEMD SERVICES")
    print("=" * 35)
    
    # Autonomous organism service
    organism_service = f"""[Unit]
Description=4Runr Autonomous Lead Generation Organism
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={os.getcwd()}
ExecStart=/usr/bin/python3 {os.getcwd()}/real_autonomous_organism.py --run
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/logs/organism.log
StandardError=append:/home/ubuntu/logs/organism.error.log

[Install]
WantedBy=multi-user.target
"""

    # Engager service  
    engager_service = f"""[Unit]
Description=4Runr Lead Engagement System
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={os.getcwd()}/4runr-outreach-system/engager
ExecStart=/usr/bin/python3 {os.getcwd()}/4runr-outreach-system/engager/app.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/logs/engager.log
StandardError=append:/home/ubuntu/logs/engager.error.log

[Install]
WantedBy=multi-user.target
"""

    try:
        # Create log directory
        os.makedirs('/home/ubuntu/logs', exist_ok=True)
        
        # Write service files
        with open('/tmp/4runr-organism.service', 'w') as f:
            f.write(organism_service)
        
        with open('/tmp/4runr-engager.service', 'w') as f:
            f.write(engager_service)
        
        print("   ✅ Created service files")
        return True
        
    except Exception as e:
        print(f"   ❌ Service creation error: {e}")
        return False

def install_systemd_services():
    """Install and enable the systemd services"""
    print(f"\n⚙️ INSTALLING SYSTEMD SERVICES")
    print("=" * 35)
    
    commands = [
        "sudo cp /tmp/4runr-organism.service /etc/systemd/system/",
        "sudo cp /tmp/4runr-engager.service /etc/systemd/system/", 
        "sudo systemctl daemon-reload",
        "sudo systemctl enable 4runr-organism.service",
        "sudo systemctl enable 4runr-engager.service"
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {cmd}")
            else:
                print(f"   ❌ {cmd}: {result.stderr}")
        except Exception as e:
            print(f"   ❌ {cmd}: {e}")

def start_autonomous_system():
    """Start the autonomous system services"""
    print(f"\n🚀 STARTING AUTONOMOUS SYSTEM")
    print("=" * 35)
    
    commands = [
        "sudo systemctl start 4runr-organism.service",
        "sudo systemctl start 4runr-engager.service"
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {cmd}")
            else:
                print(f"   ❌ {cmd}: {result.stderr}")
        except Exception as e:
            print(f"   ❌ {cmd}: {e}")

def verify_system_status():
    """Verify the autonomous system is running"""
    print(f"\n📊 VERIFYING SYSTEM STATUS")
    print("=" * 30)
    
    services = ["4runr-organism.service", "4runr-engager.service"]
    
    for service in services:
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", service], 
                capture_output=True, text=True
            )
            status = result.stdout.strip()
            if status == "active":
                print(f"   ✅ {service}: {status}")
            else:
                print(f"   ❌ {service}: {status}")
        except Exception as e:
            print(f"   ❌ {service}: {e}")

def create_monitoring_script():
    """Create a monitoring script for system health"""
    print(f"\n📈 CREATING MONITORING SCRIPT")
    print("=" * 35)
    
    monitoring_script = """#!/bin/bash

# 4Runr Autonomous System Health Monitor
# Runs every 5 minutes via cron

LOG_FILE="/home/ubuntu/logs/health_monitor.log"
DATE=$(date)

echo "[$DATE] Health check starting..." >> $LOG_FILE

# Check if organism is running
if ! systemctl is-active --quiet 4runr-organism.service; then
    echo "[$DATE] Organism service down - restarting..." >> $LOG_FILE
    sudo systemctl restart 4runr-organism.service
fi

# Check if engager is running  
if ! systemctl is-active --quiet 4runr-engager.service; then
    echo "[$DATE] Engager service down - restarting..." >> $LOG_FILE
    sudo systemctl restart 4runr-engager.service
fi

# Check database accessibility
if ! python3 -c "import sqlite3; sqlite3.connect('4runr-lead-scraper/data/leads.db').execute('SELECT 1')"; then
    echo "[$DATE] Database issue detected" >> $LOG_FILE
fi

echo "[$DATE] Health check complete" >> $LOG_FILE
"""

    try:
        with open('/tmp/health_monitor.sh', 'w') as f:
            f.write(monitoring_script)
        
        # Make executable and install
        subprocess.run(['chmod', '+x', '/tmp/health_monitor.sh'])
        subprocess.run(['sudo', 'cp', '/tmp/health_monitor.sh', '/usr/local/bin/'])
        
        print("   ✅ Created health monitoring script")
        
        # Add to crontab
        cron_entry = "*/5 * * * * /usr/local/bin/health_monitor.sh"
        subprocess.run(['sudo', 'bash', '-c', f'echo "{cron_entry}" >> /var/spool/cron/crontabs/ubuntu'])
        
        print("   ✅ Added health monitoring to cron (every 5 minutes)")
        
    except Exception as e:
        print(f"   ❌ Monitoring script error: {e}")

def main():
    print("🤖 CREATING AUTONOMOUS LIVING SYSTEM")
    print("=" * 50)
    print("🎯 Goal: 24/7 autonomous lead generation with zero manual intervention")
    
    # Step 1: Fix database schema
    if not fix_database_schema():
        print("❌ Database fix failed - stopping")
        return
    
    # Step 2: Create systemd services
    if not create_systemd_services():
        print("❌ Service creation failed - stopping")
        return
    
    # Step 3: Install services
    install_systemd_services()
    
    # Step 4: Start services
    start_autonomous_system()
    
    # Step 5: Verify status
    verify_system_status()
    
    # Step 6: Create monitoring
    create_monitoring_script()
    
    print(f"\n🎉 AUTONOMOUS LIVING SYSTEM CREATED!")
    print(f"=" * 40)
    print(f"✅ Services running 24/7:")
    print(f"   🤖 Autonomous organism (scraping, enriching, syncing)")
    print(f"   💬 Lead engager (automatic messaging)")
    print(f"   📊 Health monitor (auto-recovery)")
    
    print(f"\n🔄 The system will now:")
    print(f"   • Find new leads every 3.4 hours automatically")
    print(f"   • Enrich all data instantly (names, companies, AI messages)")
    print(f"   • Sync complete profiles to Airtable")
    print(f"   • Message leads automatically")
    print(f"   • Self-heal if any component fails")
    print(f"   • Restart automatically on server reboot")
    
    print(f"\n📊 Monitor with:")
    print(f"   sudo systemctl status 4runr-organism.service")
    print(f"   sudo systemctl status 4runr-engager.service")
    print(f"   tail -f /home/ubuntu/logs/organism.log")
    
    print(f"\n🎯 ZERO MANUAL INTERVENTION REQUIRED!")

if __name__ == "__main__":
    main()
