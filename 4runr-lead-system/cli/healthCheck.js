#!/usr/bin/env node
/**
 * Health Check Script
 * 
 * This script performs a health check on the 4Runr Lead System.
 * It verifies that the configuration is loaded correctly and that
 * the Airtable connection is working.
 */

const { loadConfig } = require('../config');
const logger = require('../utils/logger');

/**
 * Main function to run the health check
 */
async function main() {
  try {
    // Try to load the configuration
    const config = loadConfig();
    
    // Check that required configuration values are present
    if (!config.airtable.apiKey || !config.airtable.baseId || !config.airtable.tableName) {
      console.error('Missing required Airtable configuration');
      process.exit(1);
    }
    
    // Try to import the Airtable client
    const { getTable } = require('../airtable/airtableClient');
    
    // Try to get the Airtable table
    const table = getTable();
    
    // If we got here, the health check passed
    console.log('Health check passed');
    process.exit(0);
  } catch (error) {
    console.error(`Health check failed: ${error.message}`);
    process.exit(1);
  }
}

// Run the health check
main().catch(error => {
  logger.error('Unhandled error in health check', error);
  process.exit(1);
});