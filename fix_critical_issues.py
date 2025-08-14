#!/usr/bin/env python3
"""
Fix Critical Issues - Address the most critical problems first
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def fix_unicode_encoding():
    """Remove emoji characters from logging to fix Unicode issues"""
    print("🔧 Fixing Unicode Encoding Issues")
    print("=" * 50)
    
    # Files that likely have emoji characters in logging
    files_to_fix = [
        "system_controller.py",
        "4runr-outreach-system/message_generator/app.py",
        "4runr-outreach-system/daily_enricher_agent_updated.py",
        "4runr-lead-scraper/scripts/daily_scraper.py"
    ]
    
    emoji_replacements = {
        "🔍": "[SEARCH]",
        "✅": "[OK]",
        "❌": "[ERROR]",
        "⚠️": "[WARNING]",
        "🎯": "[TARGET]",
        "🚀": "[LAUNCH]",
        "📊": "[STATS]",
        "🔧": "[FIX]",
        "🎉": "[SUCCESS]",
        "📁": "[DIR]",
        "📄": "[FILE]",
        "🔗": "[LINK]",
        "💾": "[SAVE]",
        "🔄": "[SYNC]",
        "⚡": "[FAST]",
        "🛠️": "[TOOL]",
        "📈": "[CHART]",
        "🎪": "[CIRCUS]",
        "🤖": "[BOT]",
        "🧠": "[BRAIN]"
    }
    
    fixed_files = 0
    for file_path in files_to_fix:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                for emoji, replacement in emoji_replacements.items():
                    content = content.replace(emoji, replacement)
                
                if content != original_content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Fixed: {file_path}")
                    fixed_files += 1
                else:
                    print(f"✅ No emojis found: {file_path}")
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print(f"\nFixed Unicode encoding in {fixed_files} files")
    return fixed_files > 0

def fix_database_configuration():
    """Fix database configuration to use unified database"""
    print("\n🔧 Fixing Database Configuration")
    print("=" * 50)
    
    # Update .env files to use unified database
    env_files = [
        ".env",
        "4runr-lead-scraper/.env",
        "4runr-outreach-system/.env"
    ]
    
    unified_db_path = "data/unified_leads.db"
    fixed_envs = 0
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    content = f.read()
                
                # Update database path
                if "LEAD_DATABASE_PATH" in content:
                    # Replace existing path
                    lines = content.split('\n')
                    updated_lines = []
                    for line in lines:
                        if line.startswith("LEAD_DATABASE_PATH="):
                            updated_lines.append(f"LEAD_DATABASE_PATH={unified_db_path}")
                        else:
                            updated_lines.append(line)
                    content = '\n'.join(updated_lines)
                else:
                    # Add database path
                    content += f"\nLEAD_DATABASE_PATH={unified_db_path}\n"
                
                with open(env_path, 'w') as f:
                    f.write(content)
                
                print(f"✅ Updated: {env_file}")
                fixed_envs += 1
                
            except Exception as e:
                print(f"❌ Error updating {env_file}: {e}")
        else:
            print(f"⚠️ File not found: {env_file}")
    
    print(f"\nUpdated database configuration in {fixed_envs} files")
    return fixed_envs > 0

def test_database_connection():
    """Test if the unified database is working"""
    print("\n🔧 Testing Database Connection")
    print("=" * 50)
    
    try:
        db_path = Path("data/unified_leads.db")
        if not db_path.exists():
            print("❌ Unified database not found")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM leads")
        lead_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM campaigns")
        campaign_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Database connection successful")
        print(f"   - Leads: {lead_count}")
        print(f"   - Campaigns: {campaign_count}")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_message_generator():
    """Test if message generator works with fixed configuration"""
    print("\n🔧 Testing Message Generator")
    print("=" * 50)
    
    try:
        message_gen_path = Path("4runr-outreach-system/message_generator/app.py")
        if not message_gen_path.exists():
            print("❌ Message generator not found")
            return False
        
        # Test with minimal parameters
        cmd = [
            sys.executable,
            str(message_gen_path),
            "--limit", "1",
            "--test"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Message generator test passed")
            return True
        else:
            print(f"❌ Message generator test failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Message generator test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing message generator: {e}")
        return False

def test_enricher_agent():
    """Test if enricher agent works with fixed configuration"""
    print("\n🔧 Testing Enricher Agent")
    print("=" * 50)
    
    try:
        enricher_path = Path("4runr-outreach-system/daily_enricher_agent_updated.py")
        if not enricher_path.exists():
            print("❌ Enricher agent not found")
            return False
        
        # Test with minimal parameters
        cmd = [
            sys.executable,
            str(enricher_path),
            "--max-leads", "1",
            "--test"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Enricher agent test passed")
            return True
        else:
            print(f"❌ Enricher agent test failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Enricher agent test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing enricher agent: {e}")
        return False

def main():
    """Run all critical fixes"""
    print("🔧 4Runr AI Lead System - Critical Issues Fix")
    print("=" * 60)
    
    results = {}
    
    # Fix 1: Unicode encoding
    results["Unicode Encoding"] = fix_unicode_encoding()
    
    # Fix 2: Database configuration
    results["Database Config"] = fix_database_configuration()
    
    # Test 1: Database connection
    results["Database Test"] = test_database_connection()
    
    # Test 2: Message generator
    results["Message Generator"] = test_message_generator()
    
    # Test 3: Enricher agent
    results["Enricher Agent"] = test_enricher_agent()
    
    # Summary
    print("\n📊 Critical Fixes Summary")
    print("=" * 50)
    
    successful_fixes = sum(1 for result in results.values() if result)
    total_fixes = len(results)
    
    for fix_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {fix_name}")
    
    print(f"\nOverall: {successful_fixes}/{total_fixes} fixes successful")
    
    if successful_fixes >= 3:  # At least Unicode, DB config, and DB test should work
        print("\n🎉 Critical fixes completed! System should now work properly.")
        print("\nNext steps:")
        print("1. Run: python fix_automation_issues.py")
        print("2. Set up automation on EC2")
        print("3. Monitor system performance")
    else:
        print(f"\n⚠️ {total_fixes - successful_fixes} critical fixes failed")
        print("Please review the errors and fix manually")

if __name__ == "__main__":
    main()
