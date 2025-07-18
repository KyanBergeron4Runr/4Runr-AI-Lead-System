# 4Runr AI Lead System

A backend-only lead generation and outreach system designed to automate the process of finding, enriching, and engaging with potential leads through LinkedIn and email.

## Project Overview

The 4Runr AI Lead System is a modular pipeline with scraping, enrichment, and engagement logic — all coordinated through code and Airtable. Phase 1 establishes the foundation with a clean backend structure, Airtable integration, and a simulated scraper agent.

This system is built using Node.js and uses Airtable as its primary data store. It's designed to be run as CLI commands or scheduled tasks, either manually or via cron jobs.

## Features (Phase 1)

- Clean, modular backend architecture
- Secure Airtable API integration
- Simulated LinkedIn scraper that generates realistic mock lead data
- Configuration management through environment variables
- Comprehensive error handling and logging
- Docker containerization for consistent deployment
- AWS EC2 deployment support
- CLI entry points for manual execution

## Architecture

The system follows a modular architecture with clear separation of concerns:

1. **Configuration Module**: Manages environment variables and configuration settings
2. **Airtable Client Module**: Provides an abstraction layer for interacting with the Airtable API
3. **Scraper Module**: Simulates the scraping of lead information from LinkedIn
4. **Utility Modules**: Provides common functionality like logging and validation

## Directory Structure

```
/4runr-lead-system/
├── airtable/                 # Airtable client and related functionality
│   ├── airtableClient.js     # Base Airtable client functionality
│   ├── leadManager.js        # Lead management functions
│   └── listLeads.js          # CLI entry point for listing leads
├── config/                   # Configuration management
│   └── index.js              # Configuration loading and validation
├── scraper/                  # Simulated LinkedIn scraper
│   ├── mockDataGenerator.js  # Generates realistic mock lead data
│   └── scrapeLinkedIn.js     # Main scraper functionality
├── utils/                    # Utility functions
│   ├── logger.js             # Logging utility with chalk
│   └── validator.js          # Data validation functions
├── .env                      # Environment variables (not committed to Git)
├── .env.example              # Example environment variables template
├── package.json              # Project metadata and dependencies
└── README.md                 # Project documentation
```

## Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/4runr/lead-system.git
   cd 4runr-lead-system
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Airtable credentials
   ```

### Docker Installation and Usage

#### Building the Docker Image

Build the Docker image with:

```bash
docker build -t 4runr-lead-system .
```

#### Running with Docker

Run the scraper with Docker:

```bash
docker run --env-file .env 4runr-lead-system
```

Run the lead listing tool with Docker:

```bash
docker run --env-file .env 4runr-lead-system npm run list-leads
```

#### Using Docker Compose

For development, you can use Docker Compose:

```bash
# Run the scraper
docker-compose up app

# Run the lead listing tool
docker-compose up list-leads
```

#### Production Docker Commands

For production environments:

```bash
# Build optimized production image
docker build -t 4runr-lead-system:prod .

# Run with specific environment variables
docker run -e AIRTABLE_API_KEY=your_key -e AIRTABLE_BASE_ID=your_base_id -e AIRTABLE_TABLE_NAME=Leads 4runr-lead-system:prod

# Run with mounted volume for logs
docker run -v /path/to/logs:/app/logs --env-file .env 4runr-lead-system:prod
```

#### Scheduling with Docker

For scheduled execution with cron, create a script like `run-scraper.sh`:

```bash
#!/bin/bash
docker run --rm --env-file /path/to/.env 4runr-lead-system:prod >> /path/to/logs/scraper.log 2>&1
```

Then add it to crontab:

```
0 9 * * * /path/to/run-scraper.sh
```

## Configuration

The system uses environment variables for configuration. Create a `.env` file with the following variables:

```
# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
AIRTABLE_TABLE_NAME=Leads

# Application Configuration
LOG_LEVEL=info  # debug, info, warn, error
SCRAPER_LEAD_COUNT=5  # Number of mock leads to generate per run
```

## Airtable Schema

The system expects an Airtable base with a "Leads" table containing the following fields:

- Name (Single line text)
- LinkedIn URL (URL)
- Company (Single line text)
- Title (Single line text)
- Email (Email - can be empty)
- Needs Enrichment (Checkbox)
- Status (Single select: New, Contacted, Responded, Not Interested, Converted)
- Created At (Date)
- Updated At (Date)

## Usage

### Running the Scraper

The scraper generates mock lead data and saves it to Airtable:

```bash
npm run scrape
```

This will:
1. Generate the specified number of mock leads (default: 5)
2. Mark all leads as needing enrichment
3. Save the leads to Airtable
4. Output the results to the console

### Listing Leads That Need Enrichment

To list all leads that need enrichment:

```bash
npm run list-leads
```

This will fetch all leads marked as "Needs Enrichment" from Airtable and display them in the console.

## Deployment

### AWS EC2 Deployment

The system can be deployed to AWS EC2 (Ubuntu 22.04 LTS) using Docker:

1. Set up an EC2 instance with Ubuntu 22.04 LTS
2. Install Docker on the instance
3. Clone the repository and build the Docker image
4. Create a `.env` file with your configuration
5. Run the container manually or set up cron jobs

### Cron Job Configuration

Example cron job to run the scraper daily at 9 AM:

```
0 9 * * * cd /path/to/4runr-lead-system && docker run --env-file .env 4runr-lead-system npm run scrape >> /var/log/4runr-scraper.log 2>&1
```

## Error Handling

The system implements a comprehensive error handling strategy:

1. **Validation Errors**: Thrown when input data does not meet validation requirements
2. **API Errors**: Thrown when there are issues with Airtable API calls
3. **Configuration Errors**: Thrown when required configuration is missing or invalid

All errors are logged with appropriate context and stack traces.

## Next Steps (Phase 2)

Future enhancements planned for the system include:

1. **Enrichment Module**: Will add missing information to leads (e.g., email addresses)
   - Integration with email finding services
   - AI-powered data enrichment

2. **Engagement Module**: Will generate and send messages to leads
   - Personalized message templates
   - Scheduling and follow-up logic

3. **LangGraph Integration**: Will incorporate AI logic for message generation and lead qualification
   - Custom messaging based on lead characteristics
   - Sentiment analysis of responses

## License

UNLICENSED - Private use only