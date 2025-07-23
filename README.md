# 4Runr AI Lead System

A comprehensive lead generation and outreach system with two main components:

1. **4runr-lead-system**: A Node.js backend for lead management and Airtable integration
2. **4runr-agents**: A Python-based multi-agent system for lead generation, enrichment, and engagement

## Repository Structure

This repository contains both systems:

- `/4runr-lead-system/`: The Node.js backend
- `/4runr-agents/`: The Python multi-agent system

## Getting Started

### Environment Setup

Before running either system, you need to set up the environment variables:

1. For the Node.js backend:
   - Copy `4runr-lead-system/.env.example` to `4runr-lead-system/.env`
   - Fill in your Airtable API key, Base ID, and other required credentials

2. For the Python multi-agent system:
   - Copy `4runr-agents/.env.example` to `4runr-agents/.env`
   - Fill in your Airtable API key, Base ID, and other required credentials

See the README.md files in each directory for detailed setup and usage instructions.

## Deployment

Both systems can be deployed to AWS EC2 using the provided scripts:

```bash
# For the Node.js backend
cd 4runr-lead-system
./scripts/init_ec2.sh

# For the Python multi-agent system
cd 4runr-agents
./scripts/init_ec2.sh
```

## License

UNLICENSED - Private use only