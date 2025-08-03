-- Lead Database Schema
-- SQLite database schema for the 4Runr lead management system

-- Main leads table
CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    uuid TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    linkedin_url TEXT,
    email TEXT,
    company TEXT,
    title TEXT,
    location TEXT,
    industry TEXT,
    company_size TEXT,
    verified BOOLEAN DEFAULT FALSE,
    enriched BOOLEAN DEFAULT FALSE,
    needs_enrichment BOOLEAN DEFAULT TRUE,
    status TEXT DEFAULT 'new',
    source TEXT,
    scraped_at TIMESTAMP,
    enriched_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    airtable_id TEXT,
    airtable_synced BOOLEAN DEFAULT FALSE,
    sync_pending BOOLEAN DEFAULT TRUE,
    last_sync_attempt TIMESTAMP,
    sync_error TEXT,
    raw_data TEXT  -- JSON blob for additional fields
);

-- Sync status tracking table
CREATE TABLE IF NOT EXISTS sync_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id TEXT NOT NULL,
    operation TEXT NOT NULL,  -- 'create', 'update', 'delete'
    status TEXT NOT NULL,     -- 'pending', 'success', 'failed'
    attempt_count INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- Migration log table
CREATE TABLE IF NOT EXISTS migration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    leads_migrated INTEGER DEFAULT 0,
    leads_failed INTEGER DEFAULT 0,
    migration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,  -- 'started', 'completed', 'failed'
    error_details TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_linkedin_url ON leads(linkedin_url);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_full_name ON leads(full_name);
CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company);
CREATE INDEX IF NOT EXISTS idx_leads_sync_pending ON leads(sync_pending);
CREATE INDEX IF NOT EXISTS idx_leads_airtable_synced ON leads(airtable_synced);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_updated_at ON leads(updated_at);

CREATE INDEX IF NOT EXISTS idx_sync_status_lead_id ON sync_status(lead_id);
CREATE INDEX IF NOT EXISTS idx_sync_status_status ON sync_status(status);
CREATE INDEX IF NOT EXISTS idx_sync_status_operation ON sync_status(operation);

-- Unique constraints for duplicate prevention
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_linkedin_unique ON leads(linkedin_url) WHERE linkedin_url IS NOT NULL AND linkedin_url != '';
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_email_unique ON leads(email) WHERE email IS NOT NULL AND email != '';