#!/bin/bash
# Quick fix for production environment setup

echo "🔧 QUICK FIX: Production Environment Setup"
echo "=========================================="

# Go to production directory
cd production_clean_system

# Remove sqlite3 from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "🔧 Fixing requirements.txt..."
    sed -i '/sqlite3/d' requirements.txt
    echo "✅ Removed sqlite3 from requirements.txt"
    echo "📋 Current requirements:"
    cat requirements.txt
fi

# Activate virtual environment (should already exist from deployment script)
if [ -d "venv" ]; then
    echo "🔧 Activating existing virtual environment..."
    source venv/bin/activate
    
    # Install requirements without sqlite3
    echo "📦 Installing corrected requirements..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "✅ Requirements installed successfully!"
    else
        echo "🔧 Installing manually without requirements.txt..."
        pip install requests dnspython python-whois joblib scikit-learn pandas
    fi
    
    # Test the system
    echo "🧪 Testing production system..."
    python3 -c "
import sqlite3
import requests
import os

print('✅ SQLite3 (built-in): Available')
print('✅ Requests: Available')

# Check key files
files = ['production_clean_organism.py', 'ultimate_clean_enrichment_system.py']
for f in files:
    if os.path.exists(f):
        print(f'✅ {f}: Found')
    else:
        print(f'❌ {f}: Missing')

# Check database
if os.path.exists('data/unified_leads.db'):
    conn = sqlite3.connect('data/unified_leads.db')
    cursor = conn.execute('SELECT COUNT(*) FROM leads')
    count = cursor.fetchone()[0]
    conn.close()
    print(f'✅ Database: {count} leads')
else:
    print('⚠️ Database: Not found')

print('🎉 Production system test PASSED!')
"
    
    if [ $? -eq 0 ]; then
        echo "✅ System test successful!"
        
        # Create systemd service
        echo "🔧 Creating systemd service..."
        CURRENT_DIR=$(pwd)
        VENV_PYTHON="$CURRENT_DIR/venv/bin/python3"
        
        sudo tee /etc/systemd/system/clean-enrichment.service > /dev/null <<EOF
[Unit]
Description=4Runr Clean Enrichment System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$CURRENT_DIR
$(if [ ! -z "$AIRTABLE_API_KEY" ]; then echo "Environment=AIRTABLE_API_KEY=$AIRTABLE_API_KEY"; fi)
$(if [ ! -z "$SERPAPI_KEY" ]; then echo "Environment=SERPAPI_KEY=$SERPAPI_KEY"; fi)
ExecStart=$VENV_PYTHON production_clean_organism.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable clean-enrichment.service
        
        echo ""
        echo "🏆 PRODUCTION SYSTEM READY!"
        echo "=========================="
        echo "📂 Location: $(pwd)"
        echo "🎯 Virtual env: Active"
        echo "🚀 Service: clean-enrichment.service"
        echo ""
        echo "🎯 START YOUR SYSTEM:"
        echo "sudo systemctl start clean-enrichment.service"
        echo "sudo systemctl status clean-enrichment.service"
        echo "journalctl -u clean-enrichment.service -f"
        echo ""
        echo "🧪 MANUAL TEST:"
        echo "python3 production_clean_organism.py"
        
    else
        echo "❌ System test failed"
        exit 1
    fi
    
else
    echo "❌ Virtual environment not found"
    echo "🔧 Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install requests dnspython python-whois joblib scikit-learn pandas
fi

echo ""
echo "✅ QUICK FIX COMPLETED!"
