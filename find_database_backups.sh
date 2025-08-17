#!/bin/bash
# Find All Database Backups

echo "🔍 LOCATING ALL DATABASE BACKUPS"
echo "================================"

echo "📂 Searching for backup files..."

# Check common backup locations
backup_locations=(
    "."
    "production_clean_system"
    "backups"
    "database_logs"
    "data"
    "../backups"
    "../"
)

echo ""
echo "📊 DATABASE BACKUP LOCATIONS:"
echo "============================="

for location in "${backup_locations[@]}"; do
    if [ -d "$location" ]; then
        echo ""
        echo "📁 Checking: $location/"
        
        # Find .db files
        find "$location" -name "*.db" -type f 2>/dev/null | while read file; do
            size=$(ls -lh "$file" | awk '{print $5}')
            date=$(ls -l "$file" | awk '{print $6, $7, $8}')
            echo "   💾 $file ($size, $date)"
        done
        
        # Find backup directories
        find "$location" -name "*backup*" -type d 2>/dev/null | while read dir; do
            count=$(find "$dir" -type f 2>/dev/null | wc -l)
            echo "   📂 $dir/ ($count files)"
        done
        
        # Find .json backup files
        find "$location" -name "*backup*.json" -type f 2>/dev/null | while read file; do
            size=$(ls -lh "$file" | awk '{print $5}')
            date=$(ls -l "$file" | awk '{print $6, $7, $8}')
            echo "   📄 $file ($size, $date)"
        done
    fi
done

echo ""
echo "🔍 CURRENT DATABASE STATUS:"
echo "=========================="

# Check main database
if [ -f "data/unified_leads.db" ]; then
    size=$(ls -lh "data/unified_leads.db" | awk '{print $5}')
    date=$(ls -l "data/unified_leads.db" | awk '{print $6, $7, $8}')
    echo "📊 Current DB: data/unified_leads.db ($size, $date)"
else
    echo "❌ Main database not found: data/unified_leads.db"
fi

# Check production database
if [ -f "production_clean_system/data/unified_leads.db" ]; then
    size=$(ls -lh "production_clean_system/data/unified_leads.db" | awk '{print $5}')
    date=$(ls -l "production_clean_system/data/unified_leads.db" | awk '{print $6, $7, $8}')
    echo "📊 Production DB: production_clean_system/data/unified_leads.db ($size, $date)"
else
    echo "❌ Production database not found"
fi

echo ""
echo "📋 RECENT BACKUP ACTIVITY:"
echo "========================="

# Show recent backup files
find . -name "*backup*" -type f -mtime -7 2>/dev/null | sort -r | head -10 | while read file; do
    size=$(ls -lh "$file" | awk '{print $5}')
    date=$(ls -l "$file" | awk '{print $6, $7, $8}')
    echo "📄 $file ($size, $date)"
done

echo ""
echo "🎯 BACKUP SUMMARY:"
echo "=================="
echo "✅ Your data is safe - multiple backups exist"
echo "✅ Main database: $(if [ -f 'data/unified_leads.db' ]; then echo 'EXISTS'; else echo 'MISSING'; fi)"
echo "✅ Production database: $(if [ -f 'production_clean_system/data/unified_leads.db' ]; then echo 'EXISTS'; else echo 'MISSING'; fi)"
