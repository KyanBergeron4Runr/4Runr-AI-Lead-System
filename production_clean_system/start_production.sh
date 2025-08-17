#!/bin/bash
# Production Clean System Startup Script

echo "🌟 STARTING PRODUCTION CLEAN ENRICHMENT SYSTEM"
echo "=" * 60

# Check dependencies
echo "🔍 Checking dependencies..."
python3 -c "import sqlite3, requests, json, time; print('✅ Dependencies OK')"

# Check database
if [ -f "data/unified_leads.db" ]; then
    echo "✅ Clean database found"
else
    echo "❌ Database not found!"
    exit 1
fi

# Check environment variables
if [ -z "$AIRTABLE_API_KEY" ]; then
    echo "⚠️ AIRTABLE_API_KEY not set"
fi

# Start production organism
echo "🚀 Starting production organism..."
python3 production_clean_organism.py

echo "🏁 Production system stopped"
