#!/bin/bash
# Debug Production System Script
# Run this on EC2 to diagnose why the system is stuck

echo "🔍 DEBUGGING PRODUCTION SYSTEM"
echo "=============================="

# Check service status
echo "📊 Service Status:"
sudo systemctl status clean-enrichment.service --no-pager -l

echo ""
echo "📝 Recent Logs (last 50 lines):"
journalctl -u clean-enrichment.service --no-pager -n 50

echo ""
echo "🔍 Process Information:"
ps aux | grep production_clean_organism

echo ""
echo "💾 Database Status:"
cd production_clean_system
source venv/bin/activate

python3 -c "
import sqlite3
import os

print('🔍 Database Analysis:')
if os.path.exists('data/unified_leads.db'):
    conn = sqlite3.connect('data/unified_leads.db')
    
    # Check lead count
    cursor = conn.execute('SELECT COUNT(*) FROM leads')
    total = cursor.fetchone()[0]
    print(f'📊 Total leads: {total}')
    
    # Check needs enrichment
    cursor = conn.execute('SELECT COUNT(*) FROM leads WHERE needs_enrichment = 1 OR needs_enrichment IS NULL')
    needs_enrichment = cursor.fetchone()[0]
    print(f'🎯 Needs enrichment: {needs_enrichment}')
    
    # Check recent leads
    cursor = conn.execute('SELECT COUNT(*) FROM leads WHERE date_scraped >= date(\"now\", \"-1 day\")')
    recent = cursor.fetchone()[0]
    print(f'📅 Recent leads (24h): {recent}')
    
    # Check email status
    cursor = conn.execute('SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != \"\"')
    with_email = cursor.fetchone()[0]
    print(f'📧 With email: {with_email}')
    
    conn.close()
else:
    print('❌ Database not found')

print('')
print('🔧 System Files:')
files = [
    'production_clean_organism.py',
    'ultimate_clean_enrichment_system.py', 
    'real_time_duplicate_prevention.py',
    'pattern_based_email_engine.py',
    'domain_discovery_breakthrough.py'
]

for f in files:
    if os.path.exists(f):
        print(f'✅ {f}')
    else:
        print(f'❌ {f}')
"

echo ""
echo "🔍 Environment Variables:"
echo "AIRTABLE_API_KEY: $(if [ -z "$AIRTABLE_API_KEY" ]; then echo "NOT SET"; else echo "SET"; fi)"
echo "SERPAPI_KEY: $(if [ -z "$SERPAPI_KEY" ]; then echo "NOT SET"; else echo "SET"; fi)"

echo ""
echo "🧪 Manual Test:"
echo "Running production organism manually to see what happens..."
timeout 30 python3 production_clean_organism.py

echo ""
echo "📊 Debug complete!"
