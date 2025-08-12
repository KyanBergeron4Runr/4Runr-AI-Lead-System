#!/usr/bin/env python3
"""
Sync CLI Commands

Command-line interface for managing Airtable synchronization.
"""

import click
import json
from datetime import datetime
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.sync_scheduler import get_sync_scheduler
from sync.airtable_sync import sync_to_airtable, sync_from_airtable, get_sync_status
from utils.logging import get_logger

logger = get_logger('sync-cli')

@click.group()
def sync():
    """Airtable synchronization commands."""
    pass

@sync.command()
@click.option('--force', is_flag=True, help='Force sync even if already synced')
@click.option('--max-leads', type=int, help='Maximum leads to sync')
def to_airtable(force: bool, max_leads: int):
    """Sync leads to Airtable."""
    try:
        click.echo("📤 Syncing leads to Airtable...")
        
        # Get leads to sync
        from ..database.models import get_lead_database
        db = get_lead_database()
        
        if max_leads:
            leads = db.search_leads({'sync_status': 'pending'}, limit=max_leads)
        else:
            leads = None
        
        # Perform sync
        result = sync_to_airtable(leads, force=force)
        
        if result['success']:
            click.echo(f"✅ Successfully synced {result['synced_count']} leads to Airtable")
            if result['failed_count'] > 0:
                click.echo(f"⚠️ {result['failed_count']} leads failed to sync")
                for error in result.get('errors', []):
                    click.echo(f"   Error: {error}")
        else:
            click.echo(f"❌ Sync failed: {result.get('errors', [])}")
            return 1
        
        return 0
        
    except Exception as e:
        click.echo(f"❌ Sync to Airtable failed: {str(e)}")
        return 1

@sync.command()
@click.option('--force', is_flag=True, help='Force sync regardless of last sync time')
def from_airtable(force: bool):
    """Sync updates from Airtable."""
    try:
        click.echo("📥 Syncing updates from Airtable...")
        
        result = sync_from_airtable(force=force)
        
        if result['success']:
            click.echo(f"✅ Successfully synced {result['synced_count']} updates from Airtable")
            if result['failed_count'] > 0:
                click.echo(f"⚠️ {result['failed_count']} updates failed to sync")
                for error in result.get('errors', []):
                    click.echo(f"   Error: {error}")
        else:
            click.echo(f"❌ Sync failed: {result.get('errors', [])}")
            return 1
        
        return 0
        
    except Exception as e:
        click.echo(f"❌ Sync from Airtable failed: {str(e)}")
        return 1

@sync.command()
@click.option('--json', 'output_json', is_flag=True, help='Output status as JSON')
def status(output_json: bool):
    """Show sync status and statistics."""
    try:
        status_data = get_sync_status()
        
        if output_json:
            click.echo(json.dumps(status_data, indent=2))
            return 0
        
        # Format human-readable output
        click.echo("📊 Airtable Sync Status")
        click.echo("=" * 30)
        
        # Basic status
        if status_data.get('error'):
            click.echo(f"❌ Error: {status_data['error']}")
            return 1
        
        # Scheduler status
        scheduler_info = status_data.get('scheduler', {})
        if scheduler_info:
            click.echo(f"🔄 Scheduler: {'Running' if scheduler_info.get('scheduler_running') else 'Stopped'}")
            click.echo(f"⚡ Immediate Sync: {'Enabled' if scheduler_info.get('immediate_sync_enabled') else 'Disabled'}")
            click.echo(f"📅 Daily Sync Time: {scheduler_info.get('daily_sync_time', 'Not set')}")
            click.echo(f"📋 Pending Leads: {scheduler_info.get('pending_leads_count', 0)}")
            
            # Last sync times
            last_to = scheduler_info.get('last_sync_to_airtable')
            last_from = scheduler_info.get('last_sync_from_airtable')
            
            click.echo(f"📤 Last Sync to Airtable: {_format_timestamp(last_to)}")
            click.echo(f"📥 Last Sync from Airtable: {_format_timestamp(last_from)}")
        
        # Sync statistics
        sync_stats = status_data.get('sync_statistics', {})
        if sync_stats:
            click.echo("\n📈 Recent Sync Statistics (Last 7 days):")
            for operation, stats in sync_stats.items():
                for status_type, info in stats.items():
                    click.echo(f"   {operation} ({status_type}): {info['count']} times")
        
        return 0
        
    except Exception as e:
        click.echo(f"❌ Failed to get sync status: {str(e)}")
        return 1

@sync.command()
def start_scheduler():
    """Start the automatic sync scheduler."""
    try:
        click.echo("🚀 Starting sync scheduler...")
        
        scheduler = get_sync_scheduler()
        scheduler.start()
        
        click.echo("✅ Sync scheduler started successfully")
        click.echo("📊 Scheduler will run:")
        click.echo("   • Immediate sync when leads are created/updated")
        click.echo("   • Daily sync from Airtable at configured time")
        click.echo("   • Use 'sync stop-scheduler' to stop")
        
        return 0
        
    except Exception as e:
        click.echo(f"❌ Failed to start sync scheduler: {str(e)}")
        return 1

@sync.command()
def stop_scheduler():
    """Stop the automatic sync scheduler."""
    try:
        click.echo("🛑 Stopping sync scheduler...")
        
        scheduler = get_sync_scheduler()
        scheduler.stop()
        
        click.echo("✅ Sync scheduler stopped successfully")
        return 0
        
    except Exception as e:
        click.echo(f"❌ Failed to stop sync scheduler: {str(e)}")
        return 1

@sync.command()
@click.option('--lead-id', help='Sync a specific lead by ID')
def immediate(lead_id: str):
    """Trigger immediate sync for a specific lead or all pending leads."""
    try:
        scheduler = get_sync_scheduler()
        
        if lead_id:
            click.echo(f"📤 Immediately syncing lead {lead_id}...")
            result = scheduler.sync_lead_to_airtable_immediately(lead_id)
        else:
            click.echo("📤 Immediately syncing all pending leads...")
            result = scheduler.sync_all_pending_to_airtable()
        
        if result['success']:
            if result.get('skipped'):
                click.echo("⏭️ Immediate sync is disabled")
            else:
                synced_count = result.get('synced_count', 1 if lead_id else 0)
                click.echo(f"✅ Successfully synced {synced_count} lead(s)")
        else:
            click.echo(f"❌ Immediate sync failed: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
        
    except Exception as e:
        click.echo(f"❌ Immediate sync failed: {str(e)}")
        return 1

@sync.command()
def test():
    """Test sync operations."""
    try:
        click.echo("🧪 Testing Airtable Sync Operations")
        click.echo("=" * 40)
        
        # Test 1: Sync status
        click.echo("1. Testing sync status...")
        status_result = get_sync_status()
        if status_result.get('error'):
            click.echo(f"   ❌ Status check failed: {status_result['error']}")
            return 1
        else:
            click.echo("   ✅ Status check passed")
        
        # Test 2: Sync from Airtable
        click.echo("2. Testing sync from Airtable...")
        from_result = sync_from_airtable()
        if from_result['success']:
            click.echo(f"   ✅ Success: {from_result['synced_count']} updates received")
        else:
            click.echo(f"   ❌ Failed: {from_result.get('errors', [])}")
        
        # Test 3: Sync to Airtable
        click.echo("3. Testing sync to Airtable...")
        to_result = sync_to_airtable()
        if to_result['success']:
            click.echo(f"   ✅ Success: {to_result['synced_count']} leads synced")
        else:
            click.echo(f"   ❌ Failed: {to_result.get('errors', [])}")
        
        click.echo("✅ Sync tests completed")
        return 0
        
    except Exception as e:
        click.echo(f"❌ Sync test failed: {str(e)}")
        return 1

def _format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display."""
    if not timestamp_str:
        return "Never"
    
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return timestamp_str

if __name__ == "__main__":
    sync()