# 4Runr Multi-Agent LinkedIn System

A production-ready, Dockerized multi-agent system for LinkedIn lead generation, enrichment, and engagement.

## System Overview

The 4Runr Multi-Agent System is a modular pipeline that automates the process of finding, enriching, and engaging with potential leads. It consists of three independent agents that work together:

1. **Scraper Agent**: Collects lead data from LinkedIn using real browser automation with Playwright
2. **Enricher Agent**: Adds additional information to leads (e.g., email addresses)
3. **Engager Agent**: Sends personalized outreach messages to leads via email or LinkedIn

The agents communicate through shared files in a Docker volume and can be run independently or as a complete pipeline.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Airtable account with API key
- OpenAI API key (optional, for enhanced personalization)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/4runr/multi-agent-system.git
   cd 4runr-agents
   ```

2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. Start the system:
   ```bash
   ./scripts/start.sh
   ```

4. Check the logs:
   ```bash
   docker-compose logs -f
   ```

5. To stop the system:
   ```bash
   ./scripts/stop.sh
   ```

## Data Flow

The multi-agent system follows this data flow:

```
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐
│ Scraper │ ──> │ Enricher │ ──> │ Engager │ ──> │ Airtable│
└─────────┘     └──────────┘     └─────────┘     └─────────┘
     │               │               │
     └───────────────┼───────────────┘
                     ▼
               shared/leads.json
```

1. **Scraper Agent**: Generates leads with basic information (name, LinkedIn URL, company, title)
2. **Enricher Agent**: Adds email addresses and additional details to the leads
3. **Engager Agent**: Sends personalized messages and updates lead status
4. **Airtable**: All leads are synced to Airtable for tracking and reporting

## Required Environment Variables

The following environment variables are required in the `.env` file:

```
# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
AIRTABLE_TABLE_NAME=Leads

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here
```

See `.env.example` for a complete list of available configuration options.

## Directory Structure

```
/4runr-agents/
├── scraper/           # LinkedIn data scraper agent
│   ├── app.py         # Agent logic
│   ├── Dockerfile     # Container definition
│   └── requirements.txt # Python dependencies
├── enricher/          # Data enrichment agent
│   ├── app.py         # Agent logic
│   ├── Dockerfile     # Container definition
│   └── requirements.txt # Python dependencies
├── engager/           # Outreach message sender agent
│   ├── app.py         # Agent logic
│   ├── Dockerfile     # Container definition
│   └── requirements.txt # Python dependencies
├── shared/            # Shared modules and data exchange
│   ├── airtable_client.py # Airtable integration
│   └── __init__.py    # Package initialization
├── scripts/           # Utility scripts
│   ├── start.sh       # Start the system
│   ├── stop.sh        # Stop the system
│   ├── init_ec2.sh    # Initialize EC2 instance
│   ├── health_check.py # System health check
│   └── monitor_logs.py # Log monitoring
├── logs/              # Log files (created at runtime)
├── run_pipeline.py    # CLI entry point for running the pipeline
├── .env               # Environment variables (not in Git)
├── .env.example       # Example environment variables
├── .gitignore         # Git ignore rules
├── docker-compose.yml # Docker Compose configuration
├── pipeline.Dockerfile # Dockerfile for the pipeline runner
└── README.md          # This documentation
```

## Running in Production

### AWS EC2 Deployment

To deploy the system to an AWS EC2 instance:

1. Launch an Ubuntu 22.04 LTS EC2 instance
2. SSH into the instance
3. Run the initialization script:
   ```bash
   curl -s https://raw.githubusercontent.com/4runr/multi-agent-system/main/scripts/init_ec2.sh | sudo bash -s -- https://github.com/4runr/multi-agent-system.git
   ```
4. Edit the `.env` file with your configuration:
   ```bash
   nano /home/ubuntu/4runr-agents/.env
   ```
5. Restart the services:
   ```bash
   cd /home/ubuntu/4runr-agents && docker-compose restart
   ```

### Scheduled Execution with Cron

The system is configured to run automatically via cron jobs:

- Pipeline: Every 6 hours
- Scraper: Every 4 hours
- Enricher: Every 2 hours
- Engager: Every hour

You can customize the schedule by editing the crontab file:

```bash
crontab -e
```

See `scripts/cron_examples.md` for example cron job configurations.

## Monitoring and Logs

All agents log their activity to the `logs` directory. You can monitor the logs with:

```bash
docker-compose logs -f
```

To view logs for a specific agent:

```bash
docker-compose logs -f scraper
docker-compose logs -f enricher
docker-compose logs -f engager
```

The system includes a health check script that can be run to verify that everything is working correctly:

```bash
python scripts/health_check.py
```

And a log monitoring script that can alert you to errors:

```bash
python scripts/monitor_logs.py
```

## Adding New Agents

To add a new agent to the system:

1. Create a new directory for the agent:
   ```bash
   mkdir -p new-agent
   ```

2. Create the agent files:
   - `app.py`: Agent logic
   - `Dockerfile`: Container definition
   - `requirements.txt`: Python dependencies

3. Add the agent to `docker-compose.yml`:
   ```yaml
   new-agent:
     build: 
       context: ./new-agent
       dockerfile: Dockerfile
       target: production
     image: 4runr/new-agent:latest
     container_name: 4runr-new-agent
     volumes:
       - ./shared:/shared
       - ./logs:/app/logs
     env_file:
       - .env
     restart: unless-stopped
     networks:
       - 4runr-network
   ```

4. Update the pipeline script (`run_pipeline.py`) to include the new agent

## Security Notes

- API keys and credentials are stored in the `.env` file, which is not committed to Git
- Each agent runs in its own container with minimal permissions
- No hardcoded credentials in the codebase
- Logs are stored in a dedicated directory and rotated regularly

## Troubleshooting

If you encounter issues:

1. Check the logs for errors:
   ```bash
   docker-compose logs
   ```

2. Run the health check script:
   ```bash
   python scripts/health_check.py
   ```

3. Verify that the `.env` file contains all required variables

4. Restart the services:
   ```bash
   docker-compose restart
   ```

5. If all else fails, rebuild the containers:
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```

## License

UNLICENSED - Private use only