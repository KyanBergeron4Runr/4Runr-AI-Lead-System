#!/bin/bash

echo "Deploying Enhanced 4Runr System to EC2..."

# Backup current system
echo "Creating backup..."
sudo systemctl stop 4runr-ai-system
sudo cp /opt/4runr-system/real_autonomous_organism.py /opt/4runr-system/real_autonomous_organism.py.backup

# Deploy enhanced organism
echo "Deploying enhanced organism..."
sudo cp real_autonomous_organism.py /opt/4runr-system/
sudo chmod +x /opt/4runr-system/real_autonomous_organism.py
sudo chown ec2-user:ec2-user /opt/4runr-system/real_autonomous_organism.py

# Test the system
echo "Testing enhanced system..."
cd /opt/4runr-system
python3 -c "
from real_autonomous_organism import RealAutonomousOrganism
organism = RealAutonomousOrganism()
print('Enhanced organism ready!')
test_lead = {'full_name': 'Test User', 'company': 'Test Corp', 'job_title': 'CEO'}
enhanced = organism._apply_comprehensive_enrichment(test_lead)
print(f'Enhanced {len(enhanced)} fields automatically!')
"

if [ $? -eq 0 ]; then
    # Start enhanced system
    echo "Starting enhanced system..."
    sudo systemctl start 4runr-ai-system
    sudo systemctl status 4runr-ai-system
    
    echo "Enhanced 4Runr System Deployed Successfully!"
    echo "Monitor with: sudo journalctl -u 4runr-ai-system -f"
else
    echo "Test failed, restoring backup..."
    sudo cp /opt/4runr-system/real_autonomous_organism.py.backup /opt/4runr-system/real_autonomous_organism.py
    sudo systemctl start 4runr-ai-system
fi
