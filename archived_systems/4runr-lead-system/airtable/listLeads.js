/**
 * List Leads CLI
 * 
 * CLI entry point for listing leads that need enrichment.
 */

const { getLeadsNeedingEnrichment } = require('./leadManager');
const { loadConfig } = require('../config');
const logger = require('../utils/logger');
const chalk = require('chalk');

/**
 * Formats a lead for display in the console
 * @param {Object} lead - The lead to format
 * @returns {string} The formatted lead
 */
function formatLead(lead) {
  return `
${chalk.bold(lead.name)} ${chalk.gray(`(${lead.id})`)}
${chalk.blue(lead.title)} at ${chalk.green(lead.company)}
${chalk.cyan(lead.linkedInUrl)}
${lead.email ? chalk.yellow(`Email: ${lead.email}`) : chalk.red('Email: Missing')}
${chalk.gray(`Created: ${new Date(lead.createdAt).toLocaleString()}`)}
`;
}

/**
 * Main function to list leads that need enrichment
 */
async function main() {
  try {
    // Load configuration
    loadConfig();
    
    logger.info('Fetching leads that need enrichment');
    
    // Get leads that need enrichment
    const leads = await getLeadsNeedingEnrichment();
    
    // Display results
    console.log(chalk.bold(`\n=== Leads Needing Enrichment (${leads.length}) ===\n`));
    
    if (leads.length === 0) {
      console.log(chalk.yellow('No leads found that need enrichment.'));
    } else {
      leads.forEach((lead, index) => {
        console.log(`${chalk.bold(`Lead #${index + 1}`)}`);
        console.log(formatLead(lead));
      });
    }
    
    logger.success('Successfully listed leads that need enrichment');
  } catch (error) {
    logger.error('Failed to list leads', error);
    process.exit(1);
  }
}

// Run the list leads function if this file is executed directly
if (require.main === module) {
  main();
}

module.exports = {
  main
};