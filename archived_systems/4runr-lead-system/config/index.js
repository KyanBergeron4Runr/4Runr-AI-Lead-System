/**
 * Configuration Module
 * 
 * Loads and provides access to environment variables and other configuration settings.
 * Uses dotenv to load environment variables from .env file.
 */

const dotenv = require('dotenv');
const path = require('path');
const fs = require('fs');

// Load environment variables from .env file
const envPath = path.resolve(process.cwd(), '.env');
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
} else {
  console.warn('No .env file found. Using environment variables from the system.');
}

/**
 * Required configuration keys and their validation functions
 */
const requiredConfig = {
  AIRTABLE_API_KEY: (val) => typeof val === 'string' && val.length > 0,
  AIRTABLE_BASE_ID: (val) => typeof val === 'string' && val.length > 0,
  AIRTABLE_TABLE_NAME: (val) => typeof val === 'string' && val.length > 0,
  OPENAI_API_KEY: (val) => typeof val === 'string' && val.length > 0,
};

/**
 * Optional configuration keys with default values
 */
const defaultConfig = {
  LOG_LEVEL: 'info',
  SCRAPER_LEAD_COUNT: '5',
  GRAPH_API_TOKEN: '',
};

/**
 * Validates that all required configuration values are present and valid
 * @throws {Error} If any required configuration is missing or invalid
 */
function validateConfig() {
  const missingKeys = [];
  
  for (const [key, validationFn] of Object.entries(requiredConfig)) {
    const value = process.env[key];
    if (!value || !validationFn(value)) {
      missingKeys.push(key);
    }
  }
  
  if (missingKeys.length > 0) {
    throw new Error(`Missing or invalid required configuration: ${missingKeys.join(', ')}`);
  }
}

/**
 * Gets a configuration value by key
 * @param {string} key - The configuration key to retrieve
 * @returns {string|undefined} The configuration value or undefined if not found
 */
function getConfig(key) {
  return process.env[key] || defaultConfig[key];
}

/**
 * Loads and validates the configuration
 * @returns {Object} The configuration object
 */
function loadConfig() {
  // Set default values for optional configuration
  for (const [key, defaultValue] of Object.entries(defaultConfig)) {
    if (!process.env[key]) {
      process.env[key] = defaultValue;
    }
  }
  
  // Validate required configuration
  validateConfig();
  
  return {
    airtable: {
      apiKey: getConfig('AIRTABLE_API_KEY'),
      baseId: getConfig('AIRTABLE_BASE_ID'),
      tableName: getConfig('AIRTABLE_TABLE_NAME'),
    },
    openai: getConfig('OPENAI_API_KEY'),
    graphToken: getConfig('GRAPH_API_TOKEN'),
    logLevel: getConfig('LOG_LEVEL'),
    app: {
      logLevel: getConfig('LOG_LEVEL'),
      scraperLeadCount: parseInt(getConfig('SCRAPER_LEAD_COUNT'), 10),
    }
  };
}

module.exports = {
  loadConfig,
  getConfig,
  validateConfig,
};