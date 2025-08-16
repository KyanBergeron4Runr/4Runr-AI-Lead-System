#!/usr/bin/env python3
"""
Premium Data Cleaner for 4Runr System
=====================================
Remove duplicates, low-quality leads, and clean data for premium operation
"""

import sqlite3
import logging
import sys
from datetime import datetime

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger('premium_cleaner')

def clean_duplicates(conn, logger):
    """Remove duplicate leads based on multiple criteria"""
    logger.info("🧹 Cleaning duplicate leads...")
    
    # Remove duplicates by LinkedIn URL (keep highest quality score)
    cursor = conn.execute("""
        DELETE FROM leads 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM (
                SELECT id, linkedin_url, 
                       ROW_NUMBER() OVER (PARTITION BY linkedin_url ORDER BY quality_score DESC, created_at DESC) as rn
                FROM leads 
                WHERE linkedin_url IS NOT NULL AND linkedin_url != ''
            ) 
            WHERE rn = 1
        )
        AND linkedin_url IS NOT NULL AND linkedin_url != ''
    """)
    linkedin_removed = cursor.rowcount
    logger.info(f"  ❌ Removed {linkedin_removed} LinkedIn URL duplicates")
    
    # Remove duplicates by email (keep highest quality score)
    cursor = conn.execute("""
        DELETE FROM leads 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM (
                SELECT id, email, 
                       ROW_NUMBER() OVER (PARTITION BY email ORDER BY quality_score DESC, created_at DESC) as rn
                FROM leads 
                WHERE email IS NOT NULL AND email != ''
            ) 
            WHERE rn = 1
        )
        AND email IS NOT NULL AND email != ''
    """)
    email_removed = cursor.rowcount
    logger.info(f"  ❌ Removed {email_removed} email duplicates")
    
    # Remove duplicates by name + company (keep highest quality score)
    cursor = conn.execute("""
        DELETE FROM leads 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM (
                SELECT id, full_name, company, 
                       ROW_NUMBER() OVER (PARTITION BY full_name, company ORDER BY quality_score DESC, created_at DESC) as rn
                FROM leads 
                WHERE full_name IS NOT NULL AND full_name != '' 
                  AND company IS NOT NULL AND company != ''
            ) 
            WHERE rn = 1
        )
        AND full_name IS NOT NULL AND full_name != ''
        AND company IS NOT NULL AND company != ''
    """)
    name_company_removed = cursor.rowcount
    logger.info(f"  ❌ Removed {name_company_removed} name+company duplicates")
    
    total_removed = linkedin_removed + email_removed + name_company_removed
    logger.info(f"✅ Total duplicates removed: {total_removed}")
    
    return total_removed

def clean_low_quality_leads(conn, logger, min_quality_score=75):
    """Remove low-quality leads"""
    logger.info(f"🔍 Cleaning leads with quality score < {min_quality_score}...")
    
    # Remove leads with invalid names
    cursor = conn.execute("""
        DELETE FROM leads 
        WHERE full_name IS NULL 
           OR full_name = '' 
           OR LENGTH(full_name) < 3 
           OR full_name NOT LIKE '% %'
           OR full_name LIKE '%test%'
           OR full_name LIKE '%example%'
           OR full_name LIKE '%sample%'
    """)
    invalid_names = cursor.rowcount
    logger.info(f"  ❌ Removed {invalid_names} leads with invalid names")
    
    # Remove leads with no LinkedIn URL
    cursor = conn.execute("""
        DELETE FROM leads 
        WHERE linkedin_url IS NULL 
           OR linkedin_url = '' 
           OR linkedin_url NOT LIKE '%linkedin.com/in/%'
    """)
    no_linkedin = cursor.rowcount
    logger.info(f"  ❌ Removed {no_linkedin} leads without valid LinkedIn URLs")
    
    # Remove leads with low quality scores
    cursor = conn.execute("""
        DELETE FROM leads 
        WHERE quality_score < ? OR quality_score IS NULL
    """, (min_quality_score,))
    low_quality = cursor.rowcount
    logger.info(f"  ❌ Removed {low_quality} leads with quality score < {min_quality_score}")
    
    total_removed = invalid_names + no_linkedin + low_quality
    logger.info(f"✅ Total low-quality leads removed: {total_removed}")
    
    return total_removed

def update_missing_fields(conn, logger):
    """Update missing fields with default values"""
    logger.info("🔧 Updating missing fields...")
    
    # Update missing quality scores
    cursor = conn.execute("""
        UPDATE leads 
        SET quality_score = 60 
        WHERE quality_score IS NULL OR quality_score = 0
    """)
    logger.info(f"  ✅ Updated {cursor.rowcount} missing quality scores")
    
    # Update missing lead quality labels
    cursor = conn.execute("""
        UPDATE leads 
        SET lead_quality = CASE 
            WHEN quality_score >= 90 THEN 'Hot'
            WHEN quality_score >= 80 THEN 'Warm'
            ELSE 'Cold'
        END
        WHERE lead_quality IS NULL OR lead_quality = ''
    """)
    logger.info(f"  ✅ Updated {cursor.rowcount} missing lead quality labels")
    
    # Update missing source
    cursor = conn.execute("""
        UPDATE leads 
        SET source = 'SerpAPI_Real' 
        WHERE source IS NULL OR source = ''
    """)
    logger.info(f"  ✅ Updated {cursor.rowcount} missing sources")
    
    # Update missing enrichment flags
    cursor = conn.execute("""
        UPDATE leads 
        SET enriched = 1, ready_for_outreach = 1 
        WHERE enriched IS NULL OR enriched = 0
    """)
    logger.info(f"  ✅ Updated {cursor.rowcount} enrichment flags")

def generate_stats(conn, logger):
    """Generate database statistics"""
    logger.info("📊 Generating database statistics...")
    
    # Total leads
    cursor = conn.execute("SELECT COUNT(*) FROM leads")
    total_leads = cursor.fetchone()[0]
    logger.info(f"  📈 Total leads: {total_leads}")
    
    # By quality
    cursor = conn.execute("""
        SELECT lead_quality, COUNT(*) 
        FROM leads 
        GROUP BY lead_quality 
        ORDER BY COUNT(*) DESC
    """)
    quality_stats = cursor.fetchall()
    for quality, count in quality_stats:
        logger.info(f"  🎯 {quality}: {count}")
    
    # By source
    cursor = conn.execute("""
        SELECT source, COUNT(*) 
        FROM leads 
        GROUP BY source 
        ORDER BY COUNT(*) DESC
    """)
    source_stats = cursor.fetchall()
    for source, count in source_stats:
        logger.info(f"  🔍 {source}: {count}")
    
    # Quality score distribution
    cursor = conn.execute("""
        SELECT 
            AVG(quality_score) as avg_score,
            MIN(quality_score) as min_score,
            MAX(quality_score) as max_score
        FROM leads 
        WHERE quality_score IS NOT NULL
    """)
    score_stats = cursor.fetchone()
    if score_stats:
        avg, min_score, max_score = score_stats
        logger.info(f"  📊 Quality scores - Avg: {avg:.1f}, Min: {min_score}, Max: {max_score}")
    
    # With emails
    cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
    with_emails = cursor.fetchone()[0]
    logger.info(f"  📧 Leads with emails: {with_emails} ({with_emails/total_leads*100:.1f}%)")
    
    # With websites
    cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE website IS NOT NULL AND website != ''")
    with_websites = cursor.fetchone()[0]
    logger.info(f"  🌐 Leads with websites: {with_websites} ({with_websites/total_leads*100:.1f}%)")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Premium Data Cleaner for 4Runr System')
    parser.add_argument('--clean', action='store_true', help='Clean duplicates and low-quality leads')
    parser.add_argument('--stats', action='store_true', help='Show database statistics only')
    parser.add_argument('--quality-threshold', type=int, default=75, help='Minimum quality score to keep')
    parser.add_argument('--database', default='data/unified_leads.db', help='Database path')
    
    args = parser.parse_args()
    
    logger = setup_logging()
    
    try:
        # Connect to database
        conn = sqlite3.connect(args.database)
        logger.info(f"🔗 Connected to database: {args.database}")
        
        if args.stats:
            # Show statistics only
            generate_stats(conn, logger)
        elif args.clean:
            # Clean the database
            logger.info("🚀 Starting premium data cleaning...")
            
            # Remove duplicates
            duplicates_removed = clean_duplicates(conn, logger)
            
            # Remove low-quality leads
            low_quality_removed = clean_low_quality_leads(conn, logger, args.quality_threshold)
            
            # Update missing fields
            update_missing_fields(conn, logger)
            
            # Commit changes
            conn.commit()
            logger.info("💾 Changes committed to database")
            
            # Show final statistics
            logger.info("\n" + "="*50)
            logger.info("FINAL DATABASE STATISTICS")
            logger.info("="*50)
            generate_stats(conn, logger)
            
            total_removed = duplicates_removed + low_quality_removed
            logger.info(f"\n🎉 Cleaning complete! Removed {total_removed} leads total")
            
        else:
            # Default: show stats
            generate_stats(conn, logger)
            logger.info("\nUse --clean to clean the database or --stats to show statistics")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
