#!/bin/bash
# Fix Enrichment Flags - Reset leads to need enrichment again

echo "🔧 FIXING ENRICHMENT FLAGS"
echo "========================="

cd production_clean_system
source venv/bin/activate

echo "📊 Current state:"
python3 -c "
import sqlite3
conn = sqlite3.connect('data/unified_leads.db')

cursor = conn.execute('SELECT COUNT(*) FROM leads')
total = cursor.fetchone()[0]
print(f'Total leads: {total}')

cursor = conn.execute('SELECT COUNT(*) FROM leads WHERE needs_enrichment = 1 OR needs_enrichment IS NULL')
needs_enrichment = cursor.fetchone()[0]
print(f'Needs enrichment: {needs_enrichment}')

cursor = conn.execute('SELECT COUNT(*) FROM leads WHERE email IS NULL OR email = \"\"')
no_email = cursor.fetchone()[0]
print(f'Without email: {no_email}')

conn.close()
"

echo ""
echo "🔧 Resetting enrichment flags..."
python3 -c "
import sqlite3
conn = sqlite3.connect('data/unified_leads.db')

# Reset enrichment flags for leads that could benefit from re-enrichment
# Option 1: Reset all leads to need enrichment
cursor = conn.execute('UPDATE leads SET needs_enrichment = 1')
print(f'✅ Reset {cursor.rowcount} leads to need enrichment')

# Option 2: Reset only leads without emails or with poor data
# cursor = conn.execute('UPDATE leads SET needs_enrichment = 1 WHERE email IS NULL OR email = \"\" OR ai_message IS NULL OR lead_quality IS NULL')
# print(f'✅ Reset {cursor.rowcount} leads without good data')

conn.commit()
conn.close()
"

echo ""
echo "📊 After fix:"
python3 -c "
import sqlite3
conn = sqlite3.connect('data/unified_leads.db')

cursor = conn.execute('SELECT COUNT(*) FROM leads WHERE needs_enrichment = 1 OR needs_enrichment IS NULL')
needs_enrichment = cursor.fetchone()[0]
print(f'✅ Leads now needing enrichment: {needs_enrichment}')

conn.close()
"

echo ""
echo "🎯 Testing system with reset flags..."
timeout 15 python3 production_clean_organism.py

echo ""
echo "✅ ENRICHMENT FLAGS FIXED!"
echo "🚀 System should now process leads actively"
