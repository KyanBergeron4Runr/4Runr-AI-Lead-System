/**
 * Validator Utility
 * 
 * Provides data validation functions for lead objects and other data.
 */

/**
 * Validates that a value is not empty (undefined, null, or empty string)
 * @param {any} value - The value to check
 * @returns {boolean} True if the value is not empty
 */
function isNotEmpty(value) {
  return value !== undefined && value !== null && value !== '';
}

/**
 * Validates that a value is a string
 * @param {any} value - The value to check
 * @returns {boolean} True if the value is a string
 */
function isString(value) {
  return typeof value === 'string';
}

/**
 * Validates that a value is a valid URL
 * @param {string} value - The value to check
 * @returns {boolean} True if the value is a valid URL
 */
function isValidUrl(value) {
  try {
    new URL(value);
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Validates that a value is a valid LinkedIn URL
 * @param {string} value - The value to check
 * @returns {boolean} True if the value is a valid LinkedIn URL
 */
function isValidLinkedInUrl(value) {
  return isValidUrl(value) && value.startsWith('https://www.linkedin.com/');
}

/**
 * Validates that a value is a valid email address
 * @param {string} value - The value to check
 * @returns {boolean} True if the value is a valid email address
 */
function isValidEmail(value) {
  if (!value) return true; // Allow empty email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(value);
}

/**
 * Validates a lead object
 * @param {Object} lead - The lead object to validate
 * @returns {Object} Validation result with isValid and errors properties
 */
function validateLead(lead) {
  const errors = [];
  
  // Check if lead is an object
  if (!lead || typeof lead !== 'object') {
    return { isValid: false, errors: ['Lead must be an object'] };
  }
  
  // Validate required fields
  if (!isNotEmpty(lead.name) || !isString(lead.name)) {
    errors.push('Name is required and must be a string');
  }
  
  if (!isNotEmpty(lead.linkedInUrl) || !isString(lead.linkedInUrl)) {
    errors.push('LinkedIn URL is required and must be a string');
  } else if (!isValidLinkedInUrl(lead.linkedInUrl)) {
    errors.push('LinkedIn URL must be a valid LinkedIn URL (https://www.linkedin.com/...)');
  }
  
  if (!isNotEmpty(lead.company) || !isString(lead.company)) {
    errors.push('Company is required and must be a string');
  }
  
  if (!isNotEmpty(lead.title) || !isString(lead.title)) {
    errors.push('Title is required and must be a string');
  }
  
  // Validate optional fields
  if (lead.email !== undefined && lead.email !== null && !isValidEmail(lead.email)) {
    errors.push('Email must be a valid email address');
  }
  
  if (lead.status !== undefined && !isString(lead.status)) {
    errors.push('Status must be a string');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

module.exports = {
  isNotEmpty,
  isString,
  isValidUrl,
  isValidLinkedInUrl,
  isValidEmail,
  validateLead
};