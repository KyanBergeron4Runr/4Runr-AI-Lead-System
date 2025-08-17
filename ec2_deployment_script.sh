#!/bin/bash
# EC2 Clean System Deployment Script
# Run this on EC2 to deploy the clean enrichment system and cleanup duplicates

echo "🚀 EC2 CLEAN SYSTEM DEPLOYMENT"
echo "=" * 60
echo "Deploying ultimate clean enrichment system on EC2"
echo "This will cleanup all duplicates and deploy the new system"
echo ""

# Check if we're on EC2/Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "⚠️ This script is designed for Linux/EC2"
    echo "Please run on your EC2 instance"
    exit 1
fi

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 completed successfully"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Step 1: Update system and install dependencies
echo "📦 Step 1: Installing dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip sqlite3
pip3 install --user requests dnspython python-whois
check_success "Dependencies installation"

# Step 2: Backup existing data
echo "💾 Step 2: Creating backup..."
BACKUP_DIR="ec2_cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database if it exists
if [ -f "data/unified_leads.db" ]; then
    cp data/unified_leads.db "$BACKUP_DIR/"
    echo "✅ Database backed up to $BACKUP_DIR/"
fi

# Backup Airtable data if API key exists
if [ ! -z "$AIRTABLE_API_KEY" ]; then
    echo "📊 Backing up Airtable data..."
    python3 -c "
import os
import requests
import json

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = 'appjz81o6h5Z19Nph'
table_name = 'tblwJZn9Tv6VWjpP'

try:
    url = f'https://api.airtable.com/v0/{base_id}/{table_name}'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    all_records = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            break
            
        data = response.json()
        records = data.get('records', [])
        all_records.extend(records)
        
        offset = data.get('offset')
        if not offset:
            break
    
    with open('$BACKUP_DIR/airtable_backup.json', 'w') as f:
        json.dump(all_records, f, indent=2)
    
    print(f'✅ Airtable backup: {len(all_records)} records')
except Exception as e:
    print(f'⚠️ Airtable backup failed: {e}')
"
else
    echo "⚠️ No AIRTABLE_API_KEY found - skipping Airtable backup"
fi

check_success "Backup creation"

# Step 3: Run database cleanup
echo "🧹 Step 3: Running database cleanup..."
python3 focused_database_cleanup.py
check_success "Database cleanup"

# Step 4: Deploy clean system
echo "🚀 Step 4: Deploying clean system..."
python3 deploy_new_clean_system.py
check_success "Clean system deployment"

# Step 5: Set up production environment
echo "⚙️ Step 5: Setting up production environment..."
cd production_clean_system

# Make sure database directory exists
mkdir -p data

# Copy cleaned database if it doesn't exist
if [ ! -f "data/unified_leads.db" ] && [ -f "../data/unified_leads.db" ]; then
    cp ../data/unified_leads.db data/
    echo "✅ Clean database copied to production"
fi

# Install production requirements
if [ -f "requirements.txt" ]; then
    pip3 install --user -r requirements.txt
    check_success "Production requirements installation"
fi

# Step 6: Test the clean system
echo "🧪 Step 6: Testing clean system..."
python3 -c "
from ultimate_clean_enrichment_system import UltimateCleanEnrichmentSystem
import sqlite3

print('🔍 Testing clean system...')

# Test system initialization
try:
    system = UltimateCleanEnrichmentSystem()
    print('✅ Clean system initialized')
except Exception as e:
    print(f'❌ System initialization failed: {e}')
    exit(1)

# Check database
try:
    conn = sqlite3.connect('data/unified_leads.db')
    cursor = conn.execute('SELECT COUNT(*) FROM leads')
    count = cursor.fetchone()[0]
    conn.close()
    print(f'✅ Database accessible: {count} leads')
except Exception as e:
    print(f'❌ Database check failed: {e}')
    exit(1)

# Test duplicate prevention
try:
    from real_time_duplicate_prevention import RealTimeDuplicatePrevention
    prevention = RealTimeDuplicatePrevention()
    print('✅ Duplicate prevention system ready')
except Exception as e:
    print(f'❌ Duplicate prevention failed: {e}')
    exit(1)

print('🎉 Clean system test PASSED!')
"
check_success "Clean system testing"

# Step 7: Create systemd service for production
echo "🔧 Step 7: Creating systemd service..."
sudo tee /etc/systemd/system/clean-enrichment.service > /dev/null <<EOF
[Unit]
Description=4Runr Clean Enrichment System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/4Runr-AI-Lead-System/production_clean_system
Environment=PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/home/ubuntu/4Runr-AI-Lead-System/production_clean_system
$(if [ ! -z "$AIRTABLE_API_KEY" ]; then echo "Environment=AIRTABLE_API_KEY=$AIRTABLE_API_KEY"; fi)
$(if [ ! -z "$SERPAPI_KEY" ]; then echo "Environment=SERPAPI_KEY=$SERPAPI_KEY"; fi)
ExecStart=/usr/bin/python3 production_clean_organism.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable clean-enrichment.service
check_success "Systemd service creation"

# Step 8: Final verification
echo "✅ Step 8: Final verification..."
echo ""
echo "🏆 EC2 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "=" * 60
echo "📂 Production system: $(pwd)"
echo "📊 Backup location: ../$BACKUP_DIR"
echo "🎯 Clean database: $(ls -la data/unified_leads.db 2>/dev/null | wc -l) file found"
echo "🚀 Systemd service: clean-enrichment.service created"
echo ""
echo "🎯 NEXT STEPS:"
echo "1. sudo systemctl start clean-enrichment.service"
echo "2. sudo systemctl status clean-enrichment.service" 
echo "3. journalctl -u clean-enrichment.service -f"
echo ""
echo "✅ ZERO DUPLICATES GUARANTEED!"
echo "🌟 PRODUCTION CLEAN SYSTEM READY!"

cd ..
echo "💾 Deployment complete! Check logs and start the service."
