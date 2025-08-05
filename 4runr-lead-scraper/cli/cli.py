#!/usr/bin/env python3
"""
4Runr Lead Scraper CLI

Unified command-line interface for all lead scraping, enrichment, and management operations.
"""

import os
import sys
import click
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import get_lead_database
from scraper.serpapi_scraper import SerpAPILeadScraper
from scraper.lead_finder import LeadFinder
from enricher.email_enricher import EmailEnricher
from enricher.profile_enricher import ProfileEnricher
from sync.sync_manager import get_sync_manager
from scripts.migrate_data import DataMigrationTool
from scripts.daily_scraper import DailyScraperAgent
from config.settings import get_settings

# Import enhanced sync commands
from .sync_commands import sync as enhanced_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cli')

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', help='Path to configuration file')
@click.pass_context
def cli(ctx, verbose, config):
    """4Runr Lead Scraper - Unified lead management system."""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        ctx.obj['verbose'] = True
    
    if config:
        ctx.obj['config_path'] = config
    
    # Initialize components
    try:
        ctx.obj['db'] = get_lead_database()
        ctx.obj['settings'] = get_settings()
        
        if verbose:
            click.echo("🔧 CLI initialized with verbose logging")
    
    except Exception as e:
        click.echo(f"❌ Failed to initialize CLI: {e}", err=True)
        sys.exit(1)

@cli.group()
def scrape():
    """Lead scraping operations."""
    pass

@scrape.command()
@click.option('--max-leads', '-n', default=10, help='Maximum number of leads to scrape')
@click.option('--location', '-l', help='Search location (overrides config)')
@click.option('--save-to-db', is_flag=True, default=True, help='Save leads to database')
@click.pass_context
def leads(ctx, max_leads, location, save_to_db):
    """Scrape leads using SerpAPI."""
    click.echo(f"🔍 Scraping {max_leads} leads...")
    
    try:
        finder = LeadFinder()
        leads = finder.find_montreal_executives(max_leads=max_leads)
        
        if not leads:
            click.echo("⚠️ No leads found")
            return
        
        click.echo(f"✅ Found {len(leads)} leads")
        
        # Display leads
        for i, lead in enumerate(leads, 1):
            click.echo(f"  {i}. {lead['name']} - {lead['title']} at {lead['company']}")
            if ctx.obj.get('verbose'):
                click.echo(f"     LinkedIn: {lead.get('linkedin_url', 'N/A')}")
        
        # Save to database if requested
        if save_to_db:
            db = ctx.obj['db']
            saved_count = 0
            
            for lead in leads:
                try:
                    lead_id = db.create_lead(lead)
                    saved_count += 1
                    if ctx.obj.get('verbose'):
                        click.echo(f"     💾 Saved to database: {lead_id}")
                except Exception as e:
                    if ctx.obj.get('verbose'):
                        click.echo(f"     ⚠️ Failed to save: {e}")
            
            click.echo(f"💾 Saved {saved_count}/{len(leads)} leads to database")
    
    except Exception as e:
        click.echo(f"❌ Scraping failed: {e}", err=True)
        sys.exit(1)

@scrape.command()
@click.option('--industry', '-i', required=True, help='Industry to target')
@click.option('--max-leads', '-n', default=10, help='Maximum number of leads to scrape')
@click.option('--save-to-db', is_flag=True, default=True, help='Save leads to database')
@click.pass_context
def industry(ctx, industry, max_leads, save_to_db):
    """Scrape leads by industry."""
    click.echo(f"🔍 Scraping {max_leads} leads in {industry} industry...")
    
    try:
        finder = LeadFinder()
        leads = finder.find_leads_by_industry(industry, max_leads=max_leads)
        
        if not leads:
            click.echo("⚠️ No leads found")
            return
        
        click.echo(f"✅ Found {len(leads)} leads in {industry}")
        
        # Display and save similar to leads command
        for i, lead in enumerate(leads, 1):
            click.echo(f"  {i}. {lead['name']} - {lead['title']} at {lead['company']}")
        
        if save_to_db:
            db = ctx.obj['db']
            saved_count = 0
            
            for lead in leads:
                try:
                    lead_id = db.create_lead(lead)
                    saved_count += 1
                except Exception:
                    pass
            
            click.echo(f"💾 Saved {saved_count}/{len(leads)} leads to database")
    
    except Exception as e:
        click.echo(f"❌ Industry scraping failed: {e}", err=True)
        sys.exit(1)

@cli.group()
def list():
    """List and view leads."""
    pass

@list.command()
@click.option('--status', '-s', help='Filter by status')
@click.option('--limit', '-l', default=20, help='Maximum number of leads to show')
@click.option('--enriched', is_flag=True, help='Show only enriched leads')
@click.option('--ready', is_flag=True, help='Show only leads ready for outreach')
@click.pass_context
def leads(ctx, status, limit, enriched, ready):
    """List leads from database."""
    try:
        db = ctx.obj['db']
        
        # Build filters
        filters = {}
        if status:
            filters['status'] = status
        if enriched:
            filters['enriched'] = True
        if ready:
            filters['ready_for_outreach'] = True
        
        leads = db.search_leads(filters, limit=limit)
        
        if not leads:
            click.echo("📭 No leads found matching criteria")
            return
        
        click.echo(f"📋 Found {len(leads)} leads:")
        click.echo()
        
        for i, lead in enumerate(leads, 1):
            status_icon = "✅" if lead.enriched else "⏳"
            ready_icon = "🚀" if lead.ready_for_outreach else "📝"
            
            click.echo(f"{i:2d}. {status_icon} {ready_icon} {lead.name}")
            click.echo(f"     Company: {lead.company or 'Unknown'}")
            click.echo(f"     Title: {lead.title or 'Unknown'}")
            click.echo(f"     Email: {lead.email or 'Not found'}")
            click.echo(f"     Status: {lead.status}")
            click.echo(f"     Scraped: {lead.scraped_at or 'Unknown'}")
            
            if ctx.obj.get('verbose'):
                click.echo(f"     ID: {lead.id}")
                click.echo(f"     LinkedIn: {lead.linkedin_url or 'N/A'}")
            
            click.echo()
    
    except Exception as e:
        click.echo(f"❌ Failed to list leads: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('lead_id')
@click.pass_context
def show(ctx, lead_id):
    """Show detailed information for a specific lead."""
    try:
        db = ctx.obj['db']
        lead = db.get_lead(lead_id)
        
        if not lead:
            click.echo(f"❌ Lead not found: {lead_id}")
            return
        
        click.echo(f"👤 Lead Details: {lead.name}")
        click.echo("=" * 50)
        click.echo(f"ID: {lead.id}")
        click.echo(f"Name: {lead.name}")
        click.echo(f"Email: {lead.email or 'Not found'}")
        click.echo(f"Company: {lead.company or 'Unknown'}")
        click.echo(f"Title: {lead.title or 'Unknown'}")
        click.echo(f"LinkedIn: {lead.linkedin_url or 'N/A'}")
        click.echo(f"Phone: {lead.phone or 'N/A'}")
        click.echo(f"Location: {lead.location or 'Unknown'}")
        click.echo()
        click.echo("Status Information:")
        click.echo(f"  Status: {lead.status}")
        click.echo(f"  Enriched: {'Yes' if lead.enriched else 'No'}")
        click.echo(f"  Ready for Outreach: {'Yes' if lead.ready_for_outreach else 'No'}")
        click.echo(f"  Verified: {'Yes' if lead.verified else 'No'}")
        click.echo()
        click.echo("Timestamps:")
        click.echo(f"  Created: {lead.created_at}")
        click.echo(f"  Updated: {lead.updated_at}")
        click.echo(f"  Scraped: {lead.scraped_at or 'Unknown'}")
        
        if lead.enriched:
            click.echo(f"  Enriched: {lead.enrichment_last_attempt or 'Unknown'}")
        
        if lead.airtable_id:
            click.echo()
            click.echo("Sync Information:")
            click.echo(f"  Airtable ID: {lead.airtable_id}")
            click.echo(f"  Last Synced: {lead.airtable_synced or 'Never'}")
            click.echo(f"  Sync Status: {lead.sync_status}")
    
    except Exception as e:
        click.echo(f"❌ Failed to show lead: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    try:
        db = ctx.obj['db']
        stats = db.get_lead_statistics()
        
        click.echo("📊 Lead Database Statistics")
        click.echo("=" * 30)
        click.echo(f"Total Leads: {stats.get('total_leads', 0)}")
        click.echo(f"Enriched Leads: {stats.get('enriched_leads', 0)}")
        click.echo(f"Ready for Outreach: {stats.get('ready_for_outreach', 0)}")
        click.echo(f"Scraped Last 7 Days: {stats.get('scraped_last_7_days', 0)}")
        click.echo()
        
        # Status breakdown
        status_breakdown = stats.get('by_status', {})
        if status_breakdown:
            click.echo("Status Breakdown:")
            for status, count in status_breakdown.items():
                click.echo(f"  {status}: {count}")
        
        # Database info
        db_info = db.db.get_database_info()
        click.echo()
        click.echo("Database Information:")
        click.echo(f"  Path: {db_info.get('database_path')}")
        click.echo(f"  Size: {db_info.get('database_size_mb', 0):.2f} MB")
        click.echo(f"  Last Checked: {db_info.get('last_checked')}")
    
    except Exception as e:
        click.echo(f"❌ Failed to get statistics: {e}", err=True)
        sys.exit(1)

@cli.group()
def enrich():
    """Lead enrichment operations."""
    pass

@enrich.command()
@click.option('--max-leads', '-n', default=50, help='Maximum number of leads to enrich')
@click.option('--email-only', is_flag=True, help='Only enrich emails')
@click.option('--profile-only', is_flag=True, help='Only enrich profiles')
@click.pass_context
def leads(ctx, max_leads, email_only, profile_only):
    """Enrich leads that need enrichment."""
    try:
        db = ctx.obj['db']
        
        # Get leads needing enrichment
        leads_to_enrich = db.get_leads_needing_enrichment(limit=max_leads)
        
        if not leads_to_enrich:
            click.echo("✅ No leads need enrichment")
            return
        
        click.echo(f"🔄 Enriching {len(leads_to_enrich)} leads...")
        
        enriched_count = 0
        
        for i, lead in enumerate(leads_to_enrich, 1):
            click.echo(f"Processing {i}/{len(leads_to_enrich)}: {lead.name}")
            
            enrichment_data = {}
            
            try:
                # Email enrichment
                if not email_only or not profile_only:  # Default: both
                    if not lead.email:
                        email_enricher = EmailEnricher()
                        email_result = email_enricher.enrich_lead_email(lead.to_dict())
                        
                        if email_result.get('success'):
                            enrichment_data['email'] = email_result['email']
                            enrichment_data['enrichment_method'] = email_result['method']
                            click.echo(f"  ✅ Found email: {email_result['email']}")
                        else:
                            click.echo(f"  📭 No email found")
                
                # Profile enrichment
                if not email_only:
                    profile_enricher = ProfileEnricher()
                    profile_result = profile_enricher.enrich_lead_profile(lead.to_dict())
                    
                    if profile_result.get('success'):
                        company_data = profile_result.get('company_data', {})
                        if company_data.get('industry'):
                            enrichment_data['industry'] = company_data['industry']
                        if company_data.get('estimated_size'):
                            enrichment_data['company_size'] = company_data['estimated_size']
                        if company_data.get('website_url'):
                            enrichment_data['company_website'] = company_data['website_url']
                        
                        click.echo(f"  ✅ Profile enriched")
                
                # Update database if we found anything
                if enrichment_data:
                    success = db.mark_lead_enriched(lead.id, enrichment_data)
                    if success:
                        enriched_count += 1
                        click.echo(f"  💾 Updated database")
                    else:
                        click.echo(f"  ⚠️ Failed to update database")
                else:
                    click.echo(f"  📭 No enrichment data found")
            
            except Exception as e:
                click.echo(f"  ❌ Enrichment failed: {e}")
                continue
        
        click.echo(f"✅ Enrichment completed: {enriched_count}/{len(leads_to_enrich)} leads enriched")
    
    except Exception as e:
        click.echo(f"❌ Enrichment failed: {e}", err=True)
        sys.exit(1)

@enrich.command()
@click.argument('lead_id')
@click.pass_context
def lead(ctx, lead_id):
    """Enrich a specific lead by ID."""
    try:
        db = ctx.obj['db']
        lead = db.get_lead(lead_id)
        
        if not lead:
            click.echo(f"❌ Lead not found: {lead_id}")
            return
        
        click.echo(f"🔄 Enriching lead: {lead.name}")
        
        enrichment_data = {}
        
        # Email enrichment
        if not lead.email:
            email_enricher = EmailEnricher()
            email_result = email_enricher.enrich_lead_email(lead.to_dict())
            
            if email_result.get('success'):
                enrichment_data['email'] = email_result['email']
                enrichment_data['enrichment_method'] = email_result['method']
                click.echo(f"✅ Found email: {email_result['email']}")
        
        # Profile enrichment
        profile_enricher = ProfileEnricher()
        profile_result = profile_enricher.enrich_lead_profile(lead.to_dict())
        
        if profile_result.get('success'):
            company_data = profile_result.get('company_data', {})
            if company_data.get('industry'):
                enrichment_data['industry'] = company_data['industry']
            if company_data.get('estimated_size'):
                enrichment_data['company_size'] = company_data['estimated_size']
            
            click.echo(f"✅ Profile enriched")
        
        # Update database
        if enrichment_data:
            success = db.mark_lead_enriched(lead.id, enrichment_data)
            if success:
                click.echo(f"💾 Lead updated in database")
            else:
                click.echo(f"⚠️ Failed to update database")
        else:
            click.echo(f"📭 No new enrichment data found")
    
    except Exception as e:
        click.echo(f"❌ Lead enrichment failed: {e}", err=True)
        sys.exit(1)

@cli.group()
def db():
    """Database operations."""
    pass

@db.command()
@click.option('--path', help='Backup file path')
@click.pass_context
def backup(ctx, path):
    """Create database backup."""
    try:
        db = ctx.obj['db']
        backup_path = db.db.backup_database(path)
        click.echo(f"✅ Database backed up to: {backup_path}")
    
    except Exception as e:
        click.echo(f"❌ Backup failed: {e}", err=True)
        sys.exit(1)

@db.command()
@click.argument('backup_path')
@click.option('--confirm', is_flag=True, help='Confirm restoration')
@click.pass_context
def restore(ctx, backup_path, confirm):
    """Restore database from backup."""
    if not confirm:
        click.echo("⚠️ This will overwrite the current database!")
        click.echo("Use --confirm to proceed")
        return
    
    try:
        db = ctx.obj['db']
        success = db.db.restore_database(backup_path)
        
        if success:
            click.echo(f"✅ Database restored from: {backup_path}")
        else:
            click.echo(f"❌ Restore failed")
    
    except Exception as e:
        click.echo(f"❌ Restore failed: {e}", err=True)
        sys.exit(1)

@db.command()
@click.argument('query')
@click.pass_context
def query(ctx, query):
    """Execute SQL query."""
    try:
        db = ctx.obj['db']
        cursor = db.db.execute_query(query)
        results = cursor.fetchall()
        
        if results:
            # Print column headers
            columns = [description[0] for description in cursor.description]
            click.echo(" | ".join(columns))
            click.echo("-" * (len(" | ".join(columns))))
            
            # Print rows
            for row in results:
                click.echo(" | ".join(str(value) for value in row))
            
            click.echo(f"\n({len(results)} rows)")
        else:
            click.echo("No results")
    
    except Exception as e:
        click.echo(f"❌ Query failed: {e}", err=True)
        sys.exit(1)

@db.command()
@click.pass_context
def health(ctx):
    """Check database health."""
    try:
        db = ctx.obj['db']
        health = db.db.health_check()
        
        status_icon = "✅" if health['status'] == 'healthy' else "❌"
        click.echo(f"{status_icon} Database Status: {health['status']}")
        
        if health['status'] == 'healthy':
            click.echo(f"Response Time: {health['response_time_seconds']:.3f}s")
            click.echo(f"Leads Count: {health['leads_count']}")
        else:
            click.echo(f"Error: {health.get('error', 'Unknown error')}")
    
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}", err=True)
        sys.exit(1)

@db.command()
@click.option('--discover-only', is_flag=True, help='Only discover sources, do not migrate')
@click.option('--dry-run', is_flag=True, help='Show what would be migrated without doing it')
@click.pass_context
def migrate(ctx, discover_only, dry_run):
    """Migrate data from existing databases."""
    try:
        migration_tool = DataMigrationTool()
        
        # Discover sources
        sources = migration_tool.discover_existing_databases()
        
        if not sources:
            click.echo("ℹ️ No data sources found to migrate")
            return
        
        click.echo(f"🔍 Discovered {len(sources)} data sources:")
        for source in sources:
            click.echo(f"  📁 {source.name}: {source.path} ({source.type})")
            click.echo(f"     {source.description}")
        
        if discover_only:
            return
        
        if dry_run:
            click.echo("\n🧪 DRY RUN MODE - No data will be modified")
            click.echo(f"Would migrate {len(sources)} sources")
            return
        
        # Confirm migration
        if not click.confirm(f"\n⚠️ This will migrate data from {len(sources)} sources. Continue?"):
            click.echo("Migration cancelled")
            return
        
        # Perform migration
        click.echo("🚀 Starting data migration...")
        result = migration_tool.migrate_all_data(sources)
        
        # Display results
        click.echo(f"\n🎯 Migration Results:")
        click.echo(f"  Sources Processed: {result['sources_processed']}")
        click.echo(f"  Total Leads Migrated: {result['total_leads_migrated']}")
        click.echo(f"  Total Leads Merged: {result['total_leads_merged']}")
        click.echo(f"  Success: {'✅' if result['success'] else '❌'}")
        click.echo(f"  Backup Directory: {result['backup_directory']}")
        
        if result.get('report_file'):
            click.echo(f"  Report: {result['report_file']}")
        
        # Show detailed results if verbose
        if ctx.obj.get('verbose') and result.get('results'):
            click.echo("\nDetailed Results:")
            for source_result in result['results']:
                status = "✅" if source_result['success'] else "❌"
                click.echo(f"  {status} {source_result['source_name']}: "
                          f"{source_result['leads_migrated']} migrated, "
                          f"{source_result['leads_merged']} merged")
                
                if source_result['errors']:
                    for error in source_result['errors']:
                        click.echo(f"    Error: {error}")
        
        if not result['success']:
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Migration failed: {e}", err=True)
        sys.exit(1)

@cli.group()
def sync():
    """Synchronization operations."""
    pass

@sync.command()
@click.option('--force', is_flag=True, help='Force sync even if recently synced')
@click.pass_context
def to_airtable(ctx, force):
    """Sync leads from database to Airtable."""
    try:
        sync_manager = get_sync_manager()
        
        click.echo("📤 Starting sync to Airtable...")
        result = sync_manager.sync_to_airtable(force=force)
        
        if result['success']:
            click.echo(f"✅ Sync completed: {result['synced_count']} leads synced")
            if result['failed_count'] > 0:
                click.echo(f"⚠️ {result['failed_count']} leads failed to sync")
        else:
            click.echo(f"❌ Sync failed: {result['failed_count']} failures")
            if ctx.obj.get('verbose') and result.get('errors'):
                for error in result['errors']:
                    click.echo(f"   Error: {error}")
    
    except Exception as e:
        click.echo(f"❌ Sync to Airtable failed: {e}", err=True)
        sys.exit(1)

@sync.command()
@click.option('--force', is_flag=True, help='Force sync regardless of last sync time')
@click.pass_context
def from_airtable(ctx, force):
    """Sync updates from Airtable to database."""
    try:
        sync_manager = get_sync_manager()
        
        click.echo("📥 Starting sync from Airtable...")
        result = sync_manager.sync_from_airtable(force=force)
        
        if result['success']:
            click.echo(f"✅ Sync completed: {result['synced_count']} leads updated")
            if result['failed_count'] > 0:
                click.echo(f"⚠️ {result['failed_count']} leads failed to sync")
        else:
            click.echo(f"❌ Sync failed: {result['failed_count']} failures")
            if ctx.obj.get('verbose') and result.get('errors'):
                for error in result['errors']:
                    click.echo(f"   Error: {error}")
    
    except Exception as e:
        click.echo(f"❌ Sync from Airtable failed: {e}", err=True)
        sys.exit(1)

@sync.command()
@click.option('--force', is_flag=True, help='Force bidirectional sync')
@click.pass_context
def bidirectional(ctx, force):
    """Perform bidirectional sync (both directions)."""
    try:
        sync_manager = get_sync_manager()
        
        click.echo("🔄 Starting bidirectional sync...")
        result = sync_manager.sync_bidirectional(force=force)
        
        if result['success']:
            click.echo(f"✅ Bidirectional sync completed:")
            click.echo(f"   To Airtable: {result['to_airtable'].get('synced_count', 0)} synced")
            click.echo(f"   From Airtable: {result['from_airtable'].get('synced_count', 0)} updated")
            click.echo(f"   Total: {result['total_synced']} operations")
        else:
            click.echo(f"❌ Bidirectional sync had failures:")
            click.echo(f"   Total failed: {result['total_failed']}")
    
    except Exception as e:
        click.echo(f"❌ Bidirectional sync failed: {e}", err=True)
        sys.exit(1)

@sync.command()
@click.pass_context
def status(ctx):
    """Show synchronization status."""
    try:
        sync_manager = get_sync_manager()
        status = sync_manager.get_sync_status()
        
        click.echo("🔄 Synchronization Status")
        click.echo("=" * 30)
        
        # Sync manager status
        manager_stats = status.get('sync_manager', {})
        click.echo(f"Auto Sync Enabled: {manager_stats.get('auto_sync_enabled', False)}")
        click.echo(f"Sync Interval: {manager_stats.get('sync_interval_minutes', 0)} minutes")
        click.echo(f"Sync Thread Active: {manager_stats.get('sync_thread_active', False)}")
        
        # Statistics
        stats = manager_stats.get('statistics', {})
        click.echo()
        click.echo("Statistics:")
        click.echo(f"  Total Syncs: {stats.get('total_syncs', 0)}")
        click.echo(f"  Successful: {stats.get('successful_syncs', 0)}")
        click.echo(f"  Failed: {stats.get('failed_syncs', 0)}")
        click.echo(f"  Last Sync to Airtable: {stats.get('last_sync_to_airtable', 'Never')}")
        click.echo(f"  Last Sync from Airtable: {stats.get('last_sync_from_airtable', 'Never')}")
        
        # Airtable sync status
        airtable_status = status.get('airtable_sync', {})
        if 'pending_sync_count' in airtable_status:
            click.echo()
            click.echo(f"Pending Sync Count: {airtable_status['pending_sync_count']}")
    
    except Exception as e:
        click.echo(f"❌ Failed to get sync status: {e}", err=True)
        sys.exit(1)

@sync.command()
@click.pass_context
def start_auto(ctx):
    """Start automatic synchronization."""
    try:
        sync_manager = get_sync_manager()
        sync_manager.start_automatic_sync()
        click.echo("🚀 Automatic synchronization started")
    
    except Exception as e:
        click.echo(f"❌ Failed to start automatic sync: {e}", err=True)
        sys.exit(1)

@sync.command()
@click.pass_context
def stop_auto(ctx):
    """Stop automatic synchronization."""
    try:
        sync_manager = get_sync_manager()
        sync_manager.stop_automatic_sync()
        click.echo("⏹️ Automatic synchronization stopped")
    
    except Exception as e:
        click.echo(f"❌ Failed to stop automatic sync: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--max-leads', type=int, help='Maximum leads to process')
@click.option('--dry-run', is_flag=True, help='Run in dry-run mode (no database changes)')
@click.option('--scrape-only', is_flag=True, help='Only run scraping phase')
@click.option('--enrich-only', is_flag=True, help='Only run enrichment phase')
@click.option('--sync-only', is_flag=True, help='Only run sync phase')
@click.option('--save-report', is_flag=True, help='Save execution report to file')
@click.pass_context
def daily(ctx, max_leads, dry_run, scrape_only, enrich_only, sync_only, save_report):
    """Run daily automation pipeline."""
    try:
        # Initialize daily scraper agent
        agent = DailyScraperAgent(max_leads=max_leads, dry_run=dry_run)
        
        if dry_run:
            click.echo("🧪 Running in DRY RUN mode - no database changes will be made")
        
        # Run specific phases or full pipeline
        if scrape_only:
            click.echo("🔍 Running scraping phase only...")
            result = agent._run_scraping_phase()
            
            click.echo(f"✅ Scraping completed:")
            click.echo(f"  Leads Found: {result['leads_found']}")
            click.echo(f"  Leads Saved: {result['leads_saved']}")
            click.echo(f"  Duration: {result['duration']:.1f}s")
            
        elif enrich_only:
            click.echo("💎 Running enrichment phase only...")
            result = agent._run_enrichment_phase()
            
            click.echo(f"✅ Enrichment completed:")
            click.echo(f"  Leads Processed: {result['leads_processed']}")
            click.echo(f"  Leads Enriched: {result['leads_enriched']}")
            click.echo(f"  Duration: {result['duration']:.1f}s")
            
        elif sync_only:
            click.echo("🔄 Running sync phase only...")
            result = agent._run_sync_phase()
            
            click.echo(f"✅ Sync completed:")
            click.echo(f"  Leads Synced: {result['leads_synced']}")
            click.echo(f"  Success: {'✅' if result['sync_success'] else '❌'}")
            click.echo(f"  Duration: {result['duration']:.1f}s")
            
        else:
            # Run full pipeline
            click.echo("🚀 Running full daily pipeline...")
            summary = agent.run_daily_pipeline()
            
            # Display summary
            click.echo(f"\n🎯 Daily Pipeline Summary:")
            click.echo(f"  Execution ID: {summary['execution_id']}")
            click.echo(f"  Duration: {summary['total_duration_seconds']:.1f}s")
            click.echo(f"  Success: {'✅' if summary['success'] else '❌'}")
            click.echo(f"  Leads Scraped: {summary['statistics']['leads_scraped']}")
            click.echo(f"  Leads Enriched: {summary['statistics']['leads_enriched']}")
            click.echo(f"  Leads Synced: {summary['statistics']['leads_synced']}")
            click.echo(f"  Errors: {summary['statistics']['total_errors']}")
            
            # Save report if requested
            if save_report:
                report_path = agent.save_execution_report(summary)
                if report_path:
                    click.echo(f"  Report: {report_path}")
            
            # Show detailed results if verbose
            if ctx.obj.get('verbose'):
                click.echo("\nPhase Details:")
                for phase, result in summary['phase_results'].items():
                    click.echo(f"  {phase.title()}: {result}")
            
            result = summary
        
        if not result.get('success', True):
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Daily automation failed: {e}", err=True)
        sys.exit(1)

# Add enhanced sync commands as a subgroup
cli.add_command(enhanced_sync, name='sync-enhanced')

if __name__ == '__main__':
    cli()