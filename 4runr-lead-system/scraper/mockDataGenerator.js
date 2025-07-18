/**
 * Mock Data Generator
 * 
 * Generates realistic mock lead data for testing and development.
 */

// Sample data for generating mock leads
const firstNames = [
  'John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'Robert', 'Lisa',
  'William', 'Jennifer', 'Richard', 'Elizabeth', 'Joseph', 'Susan', 'Thomas', 'Karen'
];

const lastNames = [
  'Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson',
  'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin'
];

const companies = [
  'Acme Corp', 'Globex', 'Initech', 'Umbrella Corp', 'Stark Industries',
  'Wayne Enterprises', 'Cyberdyne Systems', 'Soylent Corp', 'Massive Dynamic',
  'Hooli', 'Pied Piper', 'Dunder Mifflin', 'Wonka Industries', 'Oceanic Airlines'
];

const titles = [
  'CEO', 'CTO', 'CFO', 'COO', 'VP of Sales', 'VP of Marketing',
  'Director of Engineering', 'Director of Product', 'Product Manager',
  'Software Engineer', 'Data Scientist', 'Marketing Manager',
  'Sales Representative', 'Customer Success Manager', 'HR Manager'
];

/**
 * Generates a random integer between min and max (inclusive)
 * @param {number} min - The minimum value
 * @param {number} max - The maximum value
 * @returns {number} A random integer
 */
function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Picks a random item from an array
 * @param {Array} array - The array to pick from
 * @returns {any} A random item from the array
 */
function getRandomItem(array) {
  return array[getRandomInt(0, array.length - 1)];
}

/**
 * Generates a random LinkedIn URL for a person
 * @param {string} firstName - The person's first name
 * @param {string} lastName - The person's last name
 * @returns {string} A LinkedIn URL
 */
function generateLinkedInUrl(firstName, lastName) {
  const variations = [
    `${firstName.toLowerCase()}-${lastName.toLowerCase()}`,
    `${firstName.toLowerCase()}.${lastName.toLowerCase()}`,
    `${firstName.toLowerCase()}${lastName.toLowerCase()}`,
    `${firstName.toLowerCase()[0]}${lastName.toLowerCase()}`
  ];
  
  const randomVariation = getRandomItem(variations);
  const randomNumber = Math.random() < 0.3 ? getRandomInt(1, 999) : '';
  
  return `https://www.linkedin.com/in/${randomVariation}${randomNumber}`;
}

/**
 * Generates a mock lead object
 * @returns {Object} A mock lead object
 */
function generateMockLead() {
  const firstName = getRandomItem(firstNames);
  const lastName = getRandomItem(lastNames);
  const company = getRandomItem(companies);
  const title = getRandomItem(titles);
  const linkedInUrl = generateLinkedInUrl(firstName, lastName);
  
  return {
    name: `${firstName} ${lastName}`,
    linkedInUrl,
    company,
    title,
    email: null, // Email is intentionally missing
    needsEnrichment: true,
    status: 'New',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
}

/**
 * Generates multiple mock leads
 * @param {number} count - The number of leads to generate
 * @returns {Array<Object>} An array of mock lead objects
 */
function generateMockLeads(count) {
  const leads = [];
  
  for (let i = 0; i < count; i++) {
    leads.push(generateMockLead());
  }
  
  return leads;
}

module.exports = {
  generateMockLead,
  generateMockLeads
};