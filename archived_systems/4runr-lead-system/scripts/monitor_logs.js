#!/usr/bin/env node
/**
 * Log Monitoring Script
 * 
 * This script monitors the logs of the 4Runr Lead System.
 * It checks for errors and warnings in the logs and sends alerts if necessary.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { promisify } = require('util');

// Constants
const LOG_DIR = path.join(__dirname, '..', 'logs');
const ERROR_PATTERN = /error|exception|fail|critical/i;
const WARNING_PATTERN = /warning|warn/i;
const DEFAULT_INTERVAL = 60; // seconds
const DEFAULT_ALERT_THRESHOLD = 5;

// Promisify fs functions
const readdir = promisify(fs.readdir);
const stat = promisify(fs.stat);

/**
 * Get a list of log files in the logs directory
 * @returns {Promise<string[]>} Array of log file paths
 */
async function getLogFiles() {
  try {
    // Check if the logs directory exists
    if (!fs.existsSync(LOG_DIR)) {
      console.error(`Logs directory not found: ${LOG_DIR}`);
      return [];
    }
    
    // Get all files in the logs directory
    const files = await readdir(LOG_DIR);
    
    // Filter for log files
    return files
      .filter(file => file.endsWith('.log'))
      .map(file => path.join(LOG_DIR, file));
  } catch (error) {
    console.error(`Error getting log files: ${error.message}`);
    return [];
  }
}

/**
 * Check a log file for errors and warnings
 * @param {string} logFile - Path to the log file
 * @param {Date} [since] - Only check entries since this time
 * @returns {Promise<{errors: number, warnings: number}>} Count of errors and warnings
 */
async function checkLogFile(logFile, since = null) {
  try {
    // Check if the file exists
    if (!fs.existsSync(logFile)) {
      console.error(`Log file not found: ${logFile}`);
      return { errors: 0, warnings: 0 };
    }
    
    // Get the file modification time
    const stats = await stat(logFile);
    if (since && stats.mtime < since) {
      // File hasn't been modified since the specified time
      return { errors: 0, warnings: 0 };
    }
    
    // Read the file line by line
    const fileStream = fs.createReadStream(logFile);
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity
    });
    
    let errorCount = 0;
    let warningCount = 0;
    
    for await (const line of rl) {
      if (ERROR_PATTERN.test(line)) {
        errorCount++;
      } else if (WARNING_PATTERN.test(line)) {
        warningCount++;
      }
    }
    
    return { errors: errorCount, warnings: warningCount };
  } catch (error) {
    console.error(`Error checking log file ${logFile}: ${error.message}`);
    return { errors: 0, warnings: 0 };
  }
}

/**
 * Monitor logs for errors and warnings
 * @param {number} interval - Check interval in seconds
 * @param {number} alertThreshold - Number of errors to trigger an alert
 */
async function monitorLogs(interval = DEFAULT_INTERVAL, alertThreshold = DEFAULT_ALERT_THRESHOLD) {
  console.log(`Starting log monitoring (interval: ${interval}s, alert threshold: ${alertThreshold} errors)`);
  
  let lastCheck = new Date();
  
  while (true) {
    // Get the list of log files
    const logFiles = await getLogFiles();
    
    if (logFiles.length === 0) {
      console.warn('No log files found');
      await new Promise(resolve => setTimeout(resolve, interval * 1000));
      continue;
    }
    
    // Check each log file
    let totalErrors = 0;
    let totalWarnings = 0;
    
    for (const logFile of logFiles) {
      const { errors, warnings } = await checkLogFile(logFile, lastCheck);
      totalErrors += errors;
      totalWarnings += warnings;
      
      if (errors > 0 || warnings > 0) {
        console.log(`${path.basename(logFile)}: ${errors} errors, ${warnings} warnings`);
      }
    }
    
    // Send alerts if necessary
    if (totalErrors >= alertThreshold) {
      console.error(`ALERT: ${totalErrors} errors found in logs`);
      // In a real implementation, this would send an email or other alert
    }
    
    // Update the last check time
    lastCheck = new Date();
    
    // Sleep until the next check
    await new Promise(resolve => setTimeout(resolve, interval * 1000));
  }
}

/**
 * Main function to run the log monitor
 */
async function main() {
  console.log('Starting log monitor...');
  
  // Parse command-line arguments
  const args = process.argv.slice(2);
  const interval = args[0] ? parseInt(args[0], 10) : DEFAULT_INTERVAL;
  const alertThreshold = args[1] ? parseInt(args[1], 10) : DEFAULT_ALERT_THRESHOLD;
  
  if (isNaN(interval)) {
    console.error(`Invalid interval: ${args[0]}`);
    process.exit(1);
  }
  
  if (isNaN(alertThreshold)) {
    console.error(`Invalid alert threshold: ${args[1]}`);
    process.exit(1);
  }
  
  try {
    await monitorLogs(interval, alertThreshold);
  } catch (error) {
    console.error(`Error in log monitor: ${error.message}`);
    process.exit(1);
  }
}

// Run the main function
main().catch(error => {
  console.error(`Unhandled error: ${error.message}`);
  process.exit(1);
});