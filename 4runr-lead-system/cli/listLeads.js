#!/usr/bin/env node
/**
 * CLI script to list leads from Airtable
 * 
 * This script is used to test the Airtable connection and credentials.
 * It fetches and displays all leads from the Airtable base.
 */

const { getLeadsNeedingEnrichment } = require('../airtable/leadManager');
const { loadConfig } = require('../config');
const logger = require('../utils/logger');
const chalk = require('chalk');

/**
 * Main function to list all leads from Airtable
 */
async function main() {
  try {
    // Load and validate configuration
    const config = loadConfig();
    logger.info('Configuration loaded successfully');
    logger.info(`Using Airtable base: ${config.airtable.baseId}`);
    logger.info(`Using Airtable table: ${config.airtable.tableName}`);
    
    // Fetch leads from Airtable
    logger.info('Fetching leads from Airtable...');
    const leads = await getLeadsNeedingEnrichment();
    
    // Display results
    console.log(chalk.bold(`\n=== Leads in Airtable (${leads.length}) ===\n`));
    
    if (leads.length === 0) {
      console.log(chalk.yellow('No leads found in Airtable.'));
    } else {
      // Output leads as formatted JSON
      console.log(JSON.stringify(leads, null, 2));
    }
    
    logger.success('Airtable connection test completed successfully');
  } catch (error) {
    logger.error('Failed to connect to Airtable', error);
    console.error(chalk.red(`\nError: ${error.message}`));
    console.error(chalk.yellow('\nPlease check your Airtable credentials in .env file:'));
    console.error(chalk.yellow('- AIRTABLE_API_KEY'));
    console.error(chalk.yellow('- AIRTABLE_BASE_ID'));
    console.error(chalk.yellow('- AIRTABLE_TABLE_NAME'));
    console.error(chalk.yellow('\nRefer to Airtable API documentation: https://airtable.com/api\n'));
    process.exit(1);
  }
}

// Run the main function if this file is executed directly
if (require.main === module) {
  main();
}

module.exports = { main };