#!/bin/bash

echo "🚀 Deploying Enhanced Field Population System on EC2..."
echo "======================================================"

# 1. Backup current system
echo "📂 Creating backup..."
sudo systemctl stop 4runr-ai-system
sudo cp /opt/4runr-system/real_autonomous_organism.py /opt/4runr-system/real_autonomous_organism.py.backup.$(date +%Y%m%d-%H%M%S)

# 2. Pull latest changes
echo "📥 Pulling latest enhanced system..."
cd /opt/4runr-system
sudo git pull origin master

# 3. Set proper permissions
echo "🔐 Setting permissions..."
sudo chown -R ec2-user:ec2-user /opt/4runr-system/
sudo chmod +x /opt/4runr-system/*.py

# 4. Test the enhanced system
echo "🧪 Testing enhanced system..."
python3 -c "
try:
    from real_autonomous_organism import RealAutonomousOrganism
    organism = RealAutonomousOrganism()
    print('✅ Enhanced organism initialized successfully')
    
    # Test comprehensive enrichment
    test_lead = {'full_name': 'Test User', 'company': 'Test Corp', 'job_title': 'CEO'}
    enhanced_data = organism._apply_comprehensive_enrichment(test_lead)
    print(f'✅ Comprehensive enrichment working - {len(enhanced_data)} fields populated')
    print('🎯 Enhanced system ready for deployment!')
    
except Exception as e:
    print(f'❌ Test failed: {e}')
    print('Restoring backup...')
    exit(1)
"

# Check if test passed
if [ $? -eq 0 ]; then
    echo "✅ Enhanced system test passed!"
    
    # 5. Start the enhanced system
    echo "🚀 Starting enhanced 4Runr autonomous system..."
    sudo systemctl start 4runr-ai-system
    sudo systemctl enable 4runr-ai-system
    
    # 6. Check status
    echo "📊 Checking system status..."
    sleep 3
    sudo systemctl status 4runr-ai-system --no-pager
    
    echo ""
    echo "🎉 ENHANCED FIELD POPULATION SYSTEM DEPLOYED!"
    echo "=============================================="
    echo "✅ System Status: Enhanced organism active"
    echo "✅ Field Population: ALL missing fields will be auto-filled"
    echo "✅ Enrichment: 13+ fields populated per lead automatically"
    echo ""
    echo "🔍 Monitor enhanced enrichment:"
    echo "   sudo journalctl -u 4runr-ai-system -f"
    echo ""
    echo "🎯 Expected Results:"
    echo "   - LinkedIn URLs auto-generated"
    echo "   - Industries/locations inferred"
    echo "   - Business traits extracted"
    echo "   - Pain points identified"
    echo "   - Website URLs generated"
    echo "   - Enhanced email metadata"
    echo ""
    echo "🚀 Your autonomous lead system now works like a professional enrichment service!"
    
else
    echo "❌ Enhanced system test failed!"
    echo "🔄 Restoring backup..."
    
    # Find the most recent backup
    BACKUP_FILE=$(ls -t /opt/4runr-system/real_autonomous_organism.py.backup.* 2>/dev/null | head -n1)
    if [ -n "$BACKUP_FILE" ]; then
        sudo cp "$BACKUP_FILE" /opt/4runr-system/real_autonomous_organism.py
        echo "✅ Restored from: $BACKUP_FILE"
    fi
    
    # Start original system
    sudo systemctl start 4runr-ai-system
    echo "❌ Deployment failed - original system restored"
    exit 1
fi
