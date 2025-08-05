/**
 * Logger Utility
 * 
 * Provides logging functionality with different log levels and colorized output.
 * Uses chalk for colorized console output.
 */

const chalk = require('chalk');
const { getConfig } = require('../config');

// Log levels with their numeric values
const LOG_LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3
};

/**
 * Gets the current log level from configuration
 * @returns {number} The numeric log level
 */
function getLogLevel() {
  const configLevel = getConfig('LOG_LEVEL') || 'info';
  return LOG_LEVELS[configLevel.toLowerCase()] || LOG_LEVELS.info;
}

/**
 * Formats a log message with timestamp and optional metadata
 * @param {string} level - The log level
 * @param {string} message - The log message
 * @param {Object} [metadata] - Optional metadata to include in the log
 * @returns {string} The formatted log message
 */
function formatLogMessage(level, message, metadata) {
  const timestamp = new Date().toISOString();
  let formattedMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
  
  if (metadata) {
    formattedMessage += '\n' + JSON.stringify(metadata, null, 2);
  }
  
  return formattedMessage;
}

/**
 * Logs a debug message
 * @param {string} message - The message to log
 * @param {Object} [metadata] - Optional metadata to include in the log
 */
function debug(message, metadata) {
  if (getLogLevel() <= LOG_LEVELS.debug) {
    console.log(chalk.gray(formatLogMessage('debug', message, metadata)));
  }
}

/**
 * Logs an info message
 * @param {string} message - The message to log
 * @param {Object} [metadata] - Optional metadata to include in the log
 */
function info(message, metadata) {
  if (getLogLevel() <= LOG_LEVELS.info) {
    console.log(chalk.blue(formatLogMessage('info', message, metadata)));
  }
}

/**
 * Logs a warning message
 * @param {string} message - The message to log
 * @param {Object} [metadata] - Optional metadata to include in the log
 */
function warn(message, metadata) {
  if (getLogLevel() <= LOG_LEVELS.warn) {
    console.log(chalk.yellow(formatLogMessage('warn', message, metadata)));
  }
}

/**
 * Logs an error message
 * @param {string} message - The message to log
 * @param {Error|Object} [error] - Optional error or metadata to include in the log
 */
function error(message, error) {
  if (getLogLevel() <= LOG_LEVELS.error) {
    let metadata = null;
    
    if (error instanceof Error) {
      metadata = {
        message: error.message,
        stack: error.stack,
        ...error
      };
    } else if (error) {
      metadata = error;
    }
    
    console.error(chalk.red(formatLogMessage('error', message, metadata)));
  }
}

/**
 * Logs a success message
 * @param {string} message - The message to log
 * @param {Object} [metadata] - Optional metadata to include in the log
 */
function success(message, metadata) {
  if (getLogLevel() <= LOG_LEVELS.info) {
    console.log(chalk.green(formatLogMessage('success', message, metadata)));
  }
}

module.exports = {
  debug,
  info,
  warn,
  error,
  success
};