/**
 * Lead Manager Module
 * 
 * Provides functions for managing leads in Airtable,
 * including adding new leads and fetching leads that need enrichment.
 */

const { getTable, withRetry } = require('./airtableClient');

/**
 * Validates a lead object to ensure it has all required fields
 * @param {Object} lead - The lead object to validate
 * @throws {Error} If the lead is invalid
 */
function validateLead(lead) {
  const requiredFields = ['name', 'linkedInUrl', 'company', 'title'];
  const missingFields = requiredFields.filter(field => !lead[field]);
  
  if (missingFields.length > 0) {
    throw new Error(`Invalid lead: missing required fields: ${missingFields.join(', ')}`);
  }
  
  // Validate LinkedIn URL format
  if (lead.linkedInUrl && !lead.linkedInUrl.startsWith('https://www.linkedin.com/')) {
    throw new Error('Invalid lead: LinkedIn URL must start with https://www.linkedin.com/');
  }
}

/**
 * Transforms a lead object to Airtable record format
 * @param {Object} lead - The lead object to transform
 * @returns {Object} The Airtable record
 */
function transformLeadToAirtableRecord(lead) {
  return {
    fields: {
      'Name': lead.name,
      'LinkedIn URL': lead.linkedInUrl,
      'Company': lead.company,
      'Title': lead.title,
      'Email': lead.email || '',
      'Needs Enrichment': lead.needsEnrichment !== false, // Default to true if not specified
      'Status': lead.status || 'New',
      'Created At': lead.createdAt || new Date().toISOString(),
      'Updated At': new Date().toISOString()
    }
  };
}

/**
 * Transforms an Airtable record to a lead object
 * @param {Object} record - The Airtable record to transform
 * @returns {Object} The lead object
 */
function transformAirtableRecordToLead(record) {
  return {
    id: record.id,
    name: record.fields['Name'],
    linkedInUrl: record.fields['LinkedIn URL'],
    company: record.fields['Company'],
    title: record.fields['Title'],
    email: record.fields['Email'] || null,
    needsEnrichment: record.fields['Needs Enrichment'] || false,
    status: record.fields['Status'] || 'New',
    createdAt: record.fields['Created At'],
    updatedAt: record.fields['Updated At']
  };
}

/**
 * Adds a new lead to Airtable
 * @param {Object} lead - The lead object to add
 * @returns {Promise<Object>} The created lead with ID
 * @throws {Error} If the lead is invalid or the API call fails
 */
async function addLead(lead) {
  // Validate the lead
  validateLead(lead);
  
  // Set default values
  const now = new Date().toISOString();
  const leadWithDefaults = {
    ...lead,
    needsEnrichment: lead.needsEnrichment !== false, // Default to true if not specified
    status: lead.status || 'New',
    createdAt: lead.createdAt || now,
    updatedAt: now
  };
  
  // Transform to Airtable record format
  const record = transformLeadToAirtableRecord(leadWithDefaults);
  
  // Add to Airtable
  const table = getTable();
  const createdRecord = await withRetry(() => table.create(record));
  
  // Return the created lead with ID
  return transformAirtableRecordToLead(createdRecord);
}

/**
 * Fetches leads that need enrichment from Airtable
 * @returns {Promise<Array<Object>>} The leads that need enrichment
 * @throws {Error} If the API call fails
 */
async function getLeadsNeedingEnrichment() {
  const table = getTable();
  
  // Query Airtable for leads that need enrichment
  const records = await withRetry(() => 
    table.select({
      filterByFormula: '{Needs Enrichment} = 1',
      sort: [{ field: 'Created At', direction: 'desc' }]
    }).all()
  );
  
  // Transform records to lead objects
  return records.map(transformAirtableRecordToLead);
}

module.exports = {
  addLead,
  getLeadsNeedingEnrichment,
  validateLead
};