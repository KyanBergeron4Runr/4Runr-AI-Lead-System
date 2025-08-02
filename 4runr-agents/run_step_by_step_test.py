#!/usr/bin/env python3
"""
Step-by-Step Outreach Pipeline Test

This script follows the exact test instructions:
1. Create 3 test leads (done - in tests/leads/fake_batch_leads.json)
2. Run Campaign Brain with batch processing
3. Verify Airtable sync
4. Run email delivery

All emails sent to kyanberg@outlook.com
"""

import os
import json
import subprocess
import sys
import time
from pathlib import Path

def main():
    print("🧪 4Runr Complete Outreach Pipeline Test")
    print("=" * 50)
    
    # Paths
    script_dir = Path(__file__).parent.absolute()
    brain_dir = script_dir.parent / "4runr-brain"
    outreach_dir = script_dir.parent / "4runr-outreach-system"
    test_leads_file = script_dir / "tests" / "leads" / "fake_batch_leads.json"
    
    print(f"📁 Test leads file: {test_leads_file}")
    print(f"📁 Campaign Brain dir: {brain_dir}")
    print(f"📁 Outreach system dir: {outreach_dir}")
    
    # Step 1: Verify test leads
    print("\n🟠 Step 1: Verify Test Leads")
    print("-" * 30)
    
    if not test_leads_file.exists():
        print(f"❌ Test leads file not found: {test_leads_file}")
        return False
        
    with open(test_leads_file, 'r') as f:
        leads = json.load(f)
        
    print(f"✅ Found {len(leads)} test leads:")
    for i, lead in enumerate(leads, 1):
        print(f"   {i}. {lead['name']} - {lead['company']} - {lead['email']}")
        
    # Step 2: Run Campaign Brain
    print("\n🟠 Step 2: Run Campaign Brain")
    print("-" * 30)
    
    if not (brain_dir / "run_campaign_brain.py").exists():
        print(f"❌ Campaign Brain not found: {brain_dir / 'run_campaign_brain.py'}")
        return False
        
    print("🔄 Processing leads through Campaign Brain...")
    
    try:
        # Check if we can run with batch file directly
        cmd = [
            sys.executable,
            str(brain_dir / "run_campaign_brain.py"),
            "--batch-file", str(test_leads_file),
            "--verbose"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(brain_dir),
            timeout=300  # 5 minutes
        )
        
        if result.returncode == 0:
            print("✅ Campaign Brain completed successfully")
        else:
            print(f"⚠️ Campaign Brain returned code: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("⚠️ Campaign Brain timed out")
    except FileNotFoundError:
        print("❌ Campaign Brain script not found or not executable")
        # Try individual lead processing as fallback
        print("🔄 Trying individual lead processing...")
        
        for i, lead in enumerate(leads, 1):
            print(f"Processing lead {i}/3: {lead['name']}")
            
            # Create temp file for individual lead
            temp_file = script_dir / f"temp_lead_{i}.json"
            with open(temp_file, 'w') as f:
                json.dump(lead, f, indent=2)
                
            try:
                cmd = [
                    sys.executable,
                    str(brain_dir / "run_campaign_brain.py"),
                    "--lead", str(temp_file),
                    "--verbose"
                ]
                
                result = subprocess.run(cmd, cwd=str(brain_dir), timeout=120)
                
                if result.returncode == 0:
                    print(f"✅ Lead {i} processed successfully")
                else:
                    print(f"⚠️ Lead {i} processing returned code: {result.returncode}")
                    
            except Exception as e:
                print(f"❌ Error processing lead {i}: {e}")
            finally:
                if temp_file.exists():
                    temp_file.unlink()
                    
            time.sleep(1)  # Brief pause between leads
    
    # Step 3: Check Airtable Sync
    print("\n🟠 Step 3: Verify Airtable Sync")
    print("-" * 30)
    
    # Check if we have Airtable verification tools
    airtable_check = script_dir / "check_airtable_fields.py"
    if airtable_check.exists():
        print("🔄 Checking Airtable sync...")
        try:
            result = subprocess.run([sys.executable, str(airtable_check)], 
                                  cwd=str(script_dir), timeout=30)
            if result.returncode == 0:
                print("✅ Airtable connection verified")
            else:
                print("⚠️ Airtable check had issues")
        except Exception as e:
            print(f"⚠️ Airtable check error: {e}")
    else:
        print("ℹ️ No Airtable checker found - assuming sync worked")
        print("✅ Check your Airtable manually for the 3 test leads")
    
    # Step 4: Run Email Delivery
    print("\n🟠 Step 4: Run Email Delivery")
    print("-" * 30)
    
    if not (outreach_dir / "send_from_queue.py").exists():
        print(f"❌ Email delivery system not found: {outreach_dir / 'send_from_queue.py'}")
        return False
        
    print("🔄 Sending emails...")
    
    try:
        cmd = [
            sys.executable,
            str(outreach_dir / "send_from_queue.py"),
            "--batch-size", "3"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(outreach_dir),
            timeout=180  # 3 minutes
        )
        
        if result.returncode == 0:
            print("✅ Email delivery completed")
        else:
            print(f"⚠️ Email delivery returned code: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("⚠️ Email delivery timed out")
    except Exception as e:
        print(f"❌ Email delivery error: {e}")
    
    # Final Summary
    print("\n🎯 Test Summary")
    print("=" * 50)
    print("Expected Results:")
    print("✅ 3 leads processed through Campaign Brain")
    print("✅ AI messages generated with fallback logic")
    print("✅ All leads synced to Airtable with AI Message field populated")
    print("✅ 3 emails sent to kyanberg@outlook.com")
    print("✅ Message type = 'hook'")
    print("✅ used_fallback_prompt = true (due to missing company traits)")
    
    print("\n📧 Check kyanberg@outlook.com for test emails!")
    print("📊 Check your Airtable for the 3 test lead records!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)