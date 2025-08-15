#!/usr/bin/env python3
"""
Production Database Access

Direct database access for production use.
Bypasses connection pooling for reliability.
"""

import os
import sys
import json
import logging
from production_db_manager import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_lead_fast(lead_data):
    """Add lead using fast direct database access."""
    try:
        success = db_manager.add_lead(lead_data)
        if success:
            logger.info(f"[FAST DB] Added lead: {lead_data.get('email', 'no-email')}")
        return success
    except Exception as e:
        logger.error(f"[FAST DB] Failed to add lead: {e}")
        return False

def get_leads_for_airtable():
    """Get leads ready for Airtable sync."""
    try:
        leads = db_manager.get_leads_for_sync()
        logger.info(f"[FAST DB] Found {len(leads)} leads for sync")
        return leads
    except Exception as e:
        logger.error(f"[FAST DB] Failed to get leads: {e}")
        return []

def update_lead_fast(lead_id, updates):
    """Update lead using fast direct access."""
    try:
        success = db_manager.update_lead(lead_id, updates)
        if success:
            logger.info(f"[FAST DB] Updated lead: {lead_id}")
        return success
    except Exception as e:
        logger.error(f"[FAST DB] Failed to update lead: {e}")
        return False

def get_db_stats():
    """Get database statistics."""
    try:
        stats = db_manager.get_database_stats()
        logger.info(f"[FAST DB] Database stats: {stats}")
        return stats
    except Exception as e:
        logger.error(f"[FAST DB] Failed to get stats: {e}")
        return {}

if __name__ == "__main__":
    # Test the fast database access
    stats = get_db_stats()
    print(f"Database Statistics: {json.dumps(stats, indent=2)}")
