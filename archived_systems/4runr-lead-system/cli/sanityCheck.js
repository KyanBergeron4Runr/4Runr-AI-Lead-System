#!/usr/bin/env node
/**
 * Sanity Check Script
 * 
 * This script performs a sanity check on the system configuration and connections.
 * It verifies that all required environment variables are loaded correctly and
 * that the Airtable connection is working.
 */

// Check if dependencies are installed
try {
  require('dotenv');
  require('chalk');
} catch (error) {
  console.error('Error: Required dependencies are not installed.');
  console.error('Please run "npm install" in the 4runr-lead-system directory.');
  process.exit(1);
}

const fs = require('fs');
const path = require('path');

// Load dotenv manually
const dotenv = require('dotenv');
const envPath = path.resolve(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
  console.log('Loaded environment variables from .env file');
} else {
  console.warn('No .env file found. Using environment variables from the system.');
}

// Import other modules
const chalk = require('chalk');

// Define a simple logger if the actual logger module is not available
let logger;
try {
  logger = require('../utils/logger');
} catch (error) {
  logger = {
    info: (msg) => console.log(msg),
    error: (msg, err) => console.error(msg, err),
    success: (msg) => console.log(msg)
  };
}

// Try to load config
let config;
try {
  const { loadConfig } = require('../config');
  config = loadConfig();
} catch (error) {
  console.error('Error loading configuration:', error.message);
  process.exit(1);
}

/**
 * Checks that all environment variables are loaded correctly
 * @returns {boolean} True if all variables are loaded correctly
 */
async function checkEnvironmentVariables() {
  try {
    const config = loadConfig();
    
    console.log(chalk.bold('\nEnvironment Variables:'));
    
    // Check Airtable configuration
    console.log(chalk.bold('\nAirtable Configuration:'));
    console.log(`AIRTABLE_API_KEY: ${maskString(config.airtable.apiKey)}`);
    console.log(`AIRTABLE_BASE_ID: ${maskString(config.airtable.baseId)}`);
    console.log(`AIRTABLE_TABLE_NAME: ${config.airtable.tableName}`);
    
    // Check OpenAI configuration
    console.log(chalk.bold('\nOpenAI Configuration:'));
    console.log(`OPENAI_API_KEY: ${maskString(config.openai)}`);
    
    // Check Graph API configuration
    console.log(chalk.bold('\nGraph API Configuration:'));
    if (config.graphToken) {
      console.log(`GRAPH_API_TOKEN: ${maskString(config.graphToken)}`);
    } else {
      console.log(chalk.yellow('GRAPH_API_TOKEN: Not set'));
    }
    
    // Check application configuration
    console.log(chalk.bold('\nApplication Configuration:'));
    console.log(`LOG_LEVEL: ${config.logLevel}`);
    console.log(`SCRAPER_LEAD_COUNT: ${config.app.scraperLeadCount}`);
    
    return true;
  } catch (error) {
    console.error(chalk.red(`\nError checking environment variables: ${error.message}`));
    return false;
  }
}

/**
 * Checks that the Airtable connection is working
 * @returns {boolean} True if the Airtable connection is working
 */
async function checkAirtableConnection() {
  try {
    // Try to import the Airtable client
    let getTable;
    try {
      getTable = require('../airtable/airtableClient').getTable;
    } catch (error) {
      console.error(chalk.red(`\nError importing Airtable client: ${error.message}`));
      return false;
    }

    const table = getTable();
    
    // Try to fetch a single record to test the connection
    const records = await table.select({
      maxRecords: 1
    }).firstPage();
    
    console.log(chalk.green(`\nAirtable connection successful! Found ${records.length} records.`));
    
    return true;
  } catch (error) {
    console.error(chalk.red(`\nError connecting to Airtable: ${error.message}`));
    return false;
  }
}

/**
 * Checks that the Graph API connection is working
 * @returns {boolean} True if the Graph API connection is working
 */
async function checkGraphConnection() {
  try {
    const config = loadConfig();
    
    if (!config.graphToken) {
      console.log(chalk.yellow('\nSkipping Graph API check: No token provided'));
      return true;
    }
    
    // Try to import the Graph client
    let getUserProfile;
    try {
      getUserProfile = require('../utils/graphClient').getUserProfile;
    } catch (error) {
      console.error(chalk.red(`\nError importing Graph client: ${error.message}`));
      return false;
    }
    
    // Try to get the user profile to test the connection
    const profile = await getUserProfile();
    
    console.log(chalk.green(`\nGraph API connection successful! Connected as: ${profile.displayName} (${profile.userPrincipalName})`));
    
    return true;
  } catch (error) {
    console.error(chalk.red(`\nError connecting to Graph API: ${error.message}`));
    return false;
  }
}

/**
 * Masks a string for display (shows only the first 4 characters)
 * @param {string} str - The string to mask
 * @returns {string} The masked string
 */
function maskString(str) {
  if (!str) return '';
  return str.substring(0, 4) + '*'.repeat(str.length - 4);
}

/**
 * Main function to run the sanity check
 */
async function main() {
  console.log(chalk.bold('4Runr Lead System Sanity Check'));
  console.log(chalk.bold('============================'));
  
  let success = true;
  
  // Check environment variables
  console.log(chalk.bold('\nChecking environment variables...'));
  if (await checkEnvironmentVariables()) {
    console.log(chalk.green('\n✓ Environment variables check passed'));
  } else {
    console.log(chalk.red('\n✗ Environment variables check failed'));
    success = false;
  }
  
  // Check Airtable connection
  console.log(chalk.bold('\nChecking Airtable connection...'));
  if (await checkAirtableConnection()) {
    console.log(chalk.green('\n✓ Airtable connection check passed'));
  } else {
    console.log(chalk.red('\n✗ Airtable connection check failed'));
    success = false;
  }
  
  // Check Graph API connection
  console.log(chalk.bold('\nChecking Graph API connection...'));
  if (await checkGraphConnection()) {
    console.log(chalk.green('\n✓ Graph API connection check passed'));
  } else {
    console.log(chalk.yellow('\n⚠ Graph API connection check failed (optional)'));
    // Don't fail the overall check for Graph API
  }
  
  // Summary
  console.log(chalk.bold('\nSanity Check Summary:'));
  if (success) {
    console.log(chalk.green('\n✓ All required checks passed! The system is properly configured.'));
  } else {
    console.log(chalk.red('\n✗ Some checks failed. Please fix the issues and try again.'));
    process.exit(1);
  }
}

// Run the main function if this file is executed directly
if (require.main === module) {
  main().catch(error => {
    logger.error('Unhandled error in sanity check', error);
    process.exit(1);
  });
}

module.exports = { main };