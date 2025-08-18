#!/usr/bin/env python3
"""
Create EC2 Deployment Package for Enhanced 4Runr System
"""

import os
import shutil
from pathlib import Path

def main():
    print("🚀 Creating EC2 Deployment Package...")
    
    # Create deployment directory
    deploy_dir = Path("ec2_deployment")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Copy main enhanced organism
    shutil.copy2("real_autonomous_organism.py", deploy_dir / "real_autonomous_organism.py")
    print("✅ Copied enhanced organism")
    
    # Copy enrichment script
    if Path("run_field_enrichment.py").exists():
        shutil.copy2("run_field_enrichment.py", deploy_dir / "run_field_enrichment.py")
        print("✅ Copied field enrichment script")
    
    # Create deployment instructions
    with open(deploy_dir / "deploy.sh", 'w') as f:
        f.write('''#!/bin/bash

echo "🚀 Deploying Enhanced 4Runr System to EC2..."

# Backup current system
echo "📂 Creating backup..."
sudo systemctl stop 4runr-ai-system
sudo cp /opt/4runr-system/real_autonomous_organism.py /opt/4runr-system/real_autonomous_organism.py.backup

# Deploy enhanced organism
echo "🔄 Deploying enhanced organism..."
sudo cp real_autonomous_organism.py /opt/4runr-system/
sudo chmod +x /opt/4runr-system/real_autonomous_organism.py
sudo chown ec2-user:ec2-user /opt/4runr-system/real_autonomous_organism.py

# Test the system
echo "🧪 Testing enhanced system..."
cd /opt/4runr-system
python3 -c "
from real_autonomous_organism import RealAutonomousOrganism
organism = RealAutonomousOrganism()
print('✅ Enhanced organism ready!')
test_lead = {'full_name': 'Test User', 'company': 'Test Corp', 'job_title': 'CEO'}
enhanced = organism._apply_comprehensive_enrichment(test_lead)
print(f'✅ Enhanced {len(enhanced)} fields automatically!')
"

# Start enhanced system
echo "🚀 Starting enhanced system..."
sudo systemctl start 4runr-ai-system
sudo systemctl status 4runr-ai-system

echo "🎉 Enhanced 4Runr System Deployed!"
echo "📊 Monitor with: sudo journalctl -u 4runr-ai-system -f"
''')
    
    # Create quick instructions
    with open(deploy_dir / "README.md", 'w') as f:
        f.write('''# Enhanced 4Runr Deployment

## Quick Deploy
1. Upload this folder to EC2: `scp -r ec2_deployment/ ec2-user@YOUR-EC2-IP:/tmp/`
2. SSH to EC2: `ssh ec2-user@YOUR-EC2-IP`
3. Deploy: `cd /tmp/ec2_deployment && sudo bash deploy.sh`
4. Monitor: `sudo journalctl -u 4runr-ai-system -f`

## What's Enhanced
- ✅ All missing fields auto-populated
- ✅ LinkedIn URLs generated
- ✅ Industry/location/company size inference
- ✅ Business traits and pain points
- ✅ Website URLs generated
- ✅ Enhanced email metadata

Your leads will now have ALL fields filled automatically!
''')
    
    print("✅ Created deployment scripts")
    print(f"\n📦 Deployment package ready: {deploy_dir}/")
    print("\n🚀 Next Steps:")
    print(f"1. Upload to EC2: scp -r {deploy_dir}/ ec2-user@YOUR-EC2-IP:/tmp/")
    print("2. SSH to EC2 and run: cd /tmp/ec2_deployment && sudo bash deploy.sh")

if __name__ == "__main__":
    main()
