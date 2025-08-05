/**
 * Airtable Client Module
 * 
 * Provides an abstraction layer for interacting with the Airtable API,
 * handling authentication, error handling, and data transformation.
 */

const Airtable = require('airtable');
const { loadConfig } = require('../config');

// Maximum number of retries for API calls
const MAX_RETRIES = 3;
// Delay between retries in milliseconds
const RETRY_DELAY = 1000;

/**
 * Initialize the Airtable client with API key from configuration
 * @returns {Object} The initialized Airtable base
 */
function initializeAirtableClient() {
  const config = loadConfig();
  
  // Configure Airtable with API key
  Airtable.configure({
    apiKey: config.airtable.apiKey
  });
  
  // Return the base instance
  return Airtable.base(config.airtable.baseId);
}

/**
 * Get the Airtable table instance
 * @returns {Object} The Airtable table instance
 */
function getTable() {
  const base = initializeAirtableClient();
  const config = loadConfig();
  return base(config.airtable.tableName);
}

/**
 * Handles API errors with retry logic
 * @param {Function} apiCall - The API call function to execute
 * @param {number} retries - Number of retries remaining
 * @returns {Promise<any>} The API call result
 * @throws {Error} If all retries fail
 */
async function withRetry(apiCall, retries = MAX_RETRIES) {
  try {
    return await apiCall();
  } catch (error) {
    if (retries > 0 && isRetryableError(error)) {
      console.warn(`API call failed, retrying... (${retries} retries left)`);
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return withRetry(apiCall, retries - 1);
    }
    
    // Enhance error with more context
    error.message = `Airtable API Error: ${error.message}`;
    throw error;
  }
}

/**
 * Determines if an error is retryable
 * @param {Error} error - The error to check
 * @returns {boolean} True if the error is retryable
 */
function isRetryableError(error) {
  // Network errors, rate limiting, and server errors are retryable
  return (
    error.statusCode === 429 || // Rate limiting
    error.statusCode >= 500 ||  // Server errors
    error.code === 'ECONNRESET' || // Connection reset
    error.code === 'ETIMEDOUT' || // Timeout
    error.code === 'ENOTFOUND'    // DNS lookup failed
  );
}

module.exports = {
  initializeAirtableClient,
  getTable,
  withRetry
};