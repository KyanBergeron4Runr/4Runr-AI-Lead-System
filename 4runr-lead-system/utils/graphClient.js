/**
 * Microsoft Graph Client Module
 * 
 * Provides functionality to interact with Microsoft Graph API.
 * Currently using a temporary manual token for authentication.
 */

const axios = require('axios');
const { getConfig } = require('../config');
const logger = require('./logger');

// Base URL for Microsoft Graph API
const GRAPH_API_BASE_URL = 'https://graph.microsoft.com/v1.0';

/**
 * Creates an authenticated Graph API client
 * @returns {Object} The Graph API client
 */
function createGraphClient() {
  // Get the token from environment variables
  const token = getConfig('GRAPH_API_TOKEN');
  
  // TODO: Replace manual token with full OAuth flow later
  
  if (!token) {
    logger.warn('No Graph API token found. Graph functionality will not work.');
  }
  
  // Create an axios instance with the token
  const client = axios.create({
    baseURL: GRAPH_API_BASE_URL,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  // Add response interceptor for error handling
  client.interceptors.response.use(
    response => response,
    error => {
      if (error.response) {
        const { status, data } = error.response;
        
        if (status === 401) {
          logger.error('Graph API authentication failed. Token may be expired.');
        } else {
          logger.error(`Graph API error: ${status}`, data);
        }
      } else if (error.request) {
        logger.error('No response received from Graph API', error.request);
      } else {
        logger.error('Error setting up Graph API request', error.message);
      }
      
      return Promise.reject(error);
    }
  );
  
  return client;
}

/**
 * Sends an email using Microsoft Graph API
 * @param {Object} options - Email options
 * @param {string} options.to - Recipient email address
 * @param {string} options.subject - Email subject
 * @param {string} options.body - Email body (HTML)
 * @returns {Promise<Object>} The API response
 */
async function sendEmail({ to, subject, body }) {
  const client = createGraphClient();
  
  try {
    const response = await client.post('/me/sendMail', {
      message: {
        subject,
        body: {
          contentType: 'HTML',
          content: body
        },
        toRecipients: [
          {
            emailAddress: {
              address: to
            }
          }
        ]
      },
      saveToSentItems: true
    });
    
    logger.info(`Email sent to ${to}`);
    return response.data;
  } catch (error) {
    logger.error(`Failed to send email to ${to}`, error);
    throw error;
  }
}

/**
 * Gets the current user's profile from Microsoft Graph API
 * @returns {Promise<Object>} The user profile
 */
async function getUserProfile() {
  const client = createGraphClient();
  
  try {
    const response = await client.get('/me');
    return response.data;
  } catch (error) {
    logger.error('Failed to get user profile', error);
    throw error;
  }
}

module.exports = {
  createGraphClient,
  sendEmail,
  getUserProfile
};