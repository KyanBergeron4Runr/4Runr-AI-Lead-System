#!/usr/bin/env python3
"""
Check for Fake URL Sources
==========================
Find what's still generating fake LinkedIn URLs with numbers
"""

import sqlite3
import json
from datetime import datetime, timedelta
import os
import glob

def check_recent_sources():
    """Check what sources have been creating leads recently"""
    print("🔍 CHECKING RECENT LEAD SOURCES")
    print("=" * 50)
    
    # Check database for recent sources
    conn = sqlite3.connect('data/unified_leads.db')
    conn.row_factory = sqlite3.Row
    
    # Get recent leads (last 7 days)
    recent_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    cursor = conn.execute('''
        SELECT source, linkedin_url, full_name, created_at, COUNT(*) as count
        FROM leads 
        WHERE created_at >= ? 
        GROUP BY source, DATE(created_at)
        ORDER BY created_at DESC
    ''', (recent_date,))
    
    recent_sources = [dict(row) for row in cursor.fetchall()]
    
    print(f"📊 Found {len(recent_sources)} recent source entries")
    
    # Analyze for fake patterns
    fake_sources = []
    for source in recent_sources:
        if source['linkedin_url'] and '-1749' in source['linkedin_url']:
            fake_sources.append(source)
            print(f"🚨 FAKE SOURCE: {source['source']} - {source['linkedin_url']}")
    
    conn.close()
    
    return recent_sources, fake_sources

def check_active_processes():
    """Check for active processes that might be generating leads"""
    print("\n🔍 CHECKING ACTIVE PROCESSES")
    print("=" * 50)
    
    # Look for recent log files
    log_patterns = [
        'logs/*.log',
        '*/logs/*.log',
        '*/trace_logs/*',
        'production_clean_system/logs/*'
    ]
    
    recent_logs = []
    for pattern in log_patterns:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            try:
                stat = os.stat(file)
                # Check if modified in last 24 hours
                if datetime.now().timestamp() - stat.st_mtime < 86400:
                    recent_logs.append({
                        'file': file,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            except:
                pass
    
    print(f"📊 Found {len(recent_logs)} recently active log files:")
    for log in recent_logs[:10]:  # Show first 10
        print(f"   {log['file']} - {log['size']} bytes - {log['modified']}")
    
    return recent_logs

def check_config_files():
    """Check for config files that might enable fake data generation"""
    print("\n🔍 CHECKING CONFIG FILES")
    print("=" * 50)
    
    config_patterns = [
        '**/config.json',
        '**/config.py',
        '**/settings.py',
        '**/*config*.json'
    ]
    
    configs = []
    for pattern in config_patterns:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            if os.path.isfile(file):
                configs.append(file)
    
    print(f"📊 Found {len(configs)} config files:")
    for config in configs:
        print(f"   {config}")
        
        # Check for mock/fake settings
        try:
            with open(config, 'r') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in ['mock', 'fake', 'test', 'autogen']):
                    print(f"   🚨 Contains fake/mock settings: {config}")
        except:
            pass
    
    return configs

def main():
    """Run comprehensive check for fake URL sources"""
    print("🚨 CHECKING FOR FAKE LINKEDIN URL SOURCES")
    print("=" * 60)
    print("Finding what's still generating URLs with numbers")
    print("")
    
    try:
        # Check recent sources
        recent_sources, fake_sources = check_recent_sources()
        
        # Check active processes
        recent_logs = check_active_processes()
        
        # Check config files
        configs = check_config_files()
        
        # Summary
        print(f"\n🎯 SUMMARY")
        print("=" * 50)
        print(f"📊 Recent sources: {len(recent_sources)}")
        print(f"🚨 Fake sources detected: {len(fake_sources)}")
        print(f"📋 Recent logs: {len(recent_logs)}")
        print(f"⚙️ Config files: {len(configs)}")
        
        if fake_sources:
            print(f"\n🚨 FAKE SOURCES STILL ACTIVE:")
            for source in fake_sources:
                print(f"   Source: {source['source']}")
                print(f"   URL: {source['linkedin_url']}")
                print(f"   Date: {source['created_at']}")
                print(f"   Count: {source['count']}")
                print("")
        else:
            print(f"\n✅ No recent fake sources detected")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'recent_sources': recent_sources,
            'fake_sources': fake_sources,
            'recent_logs': recent_logs,
            'configs': configs
        }
        
        with open(f"fake_source_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return len(fake_sources) == 0
        
    except Exception as e:
        print(f"❌ Check failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
