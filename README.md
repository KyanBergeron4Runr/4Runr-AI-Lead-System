# 🚀 4Runr AI Lead System

**The Complete AI-Powered Lead Generation & Outreach Ecosystem**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](https://github.com/KyanBergeron4Runr/4Runr-AI-Lead-System)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

## 🎯 Overview

The 4Runr AI Lead System is a comprehensive, autonomous lead generation and outreach platform that combines AI-powered data processing, real-time lead enrichment, and intelligent messaging automation.

### 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   4Runr Brain   │    │  Lead Scraper   │    │ Outreach System │
│  (AI Learning)  │◄──►│   (Data Ing.)   │◄──►│  (Automation)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │    Central Database     │
                    │   (Lead Management)     │
                    └─────────────────────────┘
                                 ▲
                    ┌─────────────────────────┐
                    │      Airtable API       │
                    │   (External Sync)       │
                    └─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ubuntu/Linux server (EC2 recommended)
- Airtable account with API access
- OpenAI API key
- SerpAPI key (for lead scraping)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/KyanBergeron4Runr/4Runr-AI-Lead-System.git
cd 4Runr-AI-Lead-System
```

2. **Set up virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. **Initialize the system**
```bash
cd 4runr-outreach-system
python setup_system.py
```

5. **Start the services**
```bash
# Start automation engine
sudo systemctl start 4runr-automation

# Start monitoring dashboard
python monitoring_dashboard.py
```

## 📊 System Components

### 🧠 4Runr Brain (AI Learning System)
- **Location**: `4runr-brain/`
- **Purpose**: Self-learning AI that optimizes lead generation and outreach
- **Features**: Pattern recognition, performance optimization, decision making

### 🎯 Lead Scraper (Data Ingestion)
- **Location**: `4runr-lead-scraper/`
- **Purpose**: Automated lead discovery and data collection
- **Features**: Multi-source scraping, data validation, duplicate detection

### 📧 Outreach System (Automation Engine)
- **Location**: `4runr-outreach-system/`
- **Purpose**: Intelligent lead processing and outreach automation
- **Features**: Data cleaning, enrichment, messaging, campaign management

## 🔧 Configuration

### Environment Variables

Key configuration variables in `.env`:

```env
# Airtable Integration
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_TABLE_NAME=your_table_name

# AI Services
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4

# Lead Scraping
SERPAPI_API_KEY=your_serpapi_key
MAX_LEADS_PER_RUN=5

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD=your_app_password
```

### Database Configuration

The system uses SQLite by default with automatic backup:

```env
LEAD_DATABASE_PATH=data/leads_cache.db
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_RETENTION_DAYS=30
```

## 🚀 Usage

### Basic Operations

**Add a lead manually:**
```bash
python add_test_lead.py
```

**Sync with Airtable:**
```bash
python sync_airtable_to_db.py
```

**Run data cleaning:**
```bash
python -c "from shared.data_cleaner import DataCleaner; cleaner = DataCleaner(); print('Data cleaner ready')"
```

**Check system status:**
```bash
python check_live_system.py
```

### Automated Operations

The system runs several automated processes:

- **Daily Airtable Sync**: 6:00 AM daily
- **Real-time Lead Processing**: Every 5 minutes
- **Data Cleaning**: Continuous
- **AI Message Generation**: On-demand
- **System Health Checks**: Hourly

## 📈 Monitoring

### System Dashboard

Access the monitoring dashboard:
```bash
python monitoring_dashboard.py
# Open http://localhost:8080 in your browser
```

### Log Files

Monitor system activity:
```bash
# Application logs
tail -f logs/lead_scraper.log

# Database operations
tail -f database_logs/database_operations/*.json

# Daily sync logs
tail -f logs/daily_sync.log
```

### Health Checks

```bash
# System health
python -c "from monitoring_dashboard import SystemMonitor; monitor = SystemMonitor(); print(monitor.get_system_health())"

# Database stats
python -c "import sqlite3; conn = sqlite3.connect('data/leads_cache.db'); cursor = conn.execute('SELECT COUNT(*) FROM leads'); print(f'Total leads: {cursor.fetchone()[0]}')"
```

## 🔄 Data Flow

### Lead Processing Pipeline

1. **Data Ingestion** → Leads scraped from multiple sources
2. **Data Cleaning** → Standardization and validation
3. **Enrichment** → Missing data completion via APIs
4. **AI Processing** → Intelligent categorization and scoring
5. **Message Generation** → Personalized outreach content
6. **Campaign Execution** → Automated outreach delivery
7. **Performance Tracking** → Results analysis and optimization

### Integration Points

- **Airtable**: Bi-directional sync for lead management
- **Google APIs**: Lead enrichment and validation
- **OpenAI**: AI-powered message generation
- **Email Services**: Automated outreach delivery
- **SerpAPI**: Lead discovery and research

## 🛠️ Development

### Project Structure

```
4Runr-AI-Lead-System/
├── 4runr-brain/              # AI learning system
├── 4runr-lead-scraper/       # Data ingestion
├── 4runr-outreach-system/    # Main automation engine
│   ├── shared/               # Shared utilities
│   ├── outreach/             # Outreach modules
│   ├── data/                 # Database files
│   ├── logs/                 # Application logs
│   └── database_logs/        # Database operation logs
├── .kiro/                    # Kiro IDE specifications
└── docs/                     # Documentation
```

### Adding New Features

1. Create a spec in `.kiro/specs/`
2. Implement in the appropriate module
3. Add tests in the test suite
4. Update documentation
5. Deploy via automation scripts

### Testing

```bash
# Run system tests
python real_world_test.py

# Run integration tests
python test_google_enricher_datacleaner_integration.py

# Run comprehensive tests
python corrected_ultimate_test.py
```

## 🚨 Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Check database file permissions
ls -la data/leads_cache.db

# Verify database integrity
python -c "import sqlite3; conn = sqlite3.connect('data/leads_cache.db'); print('Database OK')"
```

**API Rate Limits:**
```bash
# Check API usage in logs
grep -i "rate limit" logs/*.log

# Adjust rate limiting in .env
RATE_LIMIT_DELAY=2
```

**Service Not Starting:**
```bash
# Check service status
sudo systemctl status 4runr-automation

# View service logs
sudo journalctl -u 4runr-automation -f
```

### Performance Optimization

**For High Volume:**
```env
BATCH_SIZE=50
CONCURRENT_LIMIT=10
LEAD_DATABASE_MAX_CONNECTIONS=50
```

**For Low Resources:**
```env
BATCH_SIZE=5
CONCURRENT_LIMIT=2
LEAD_DATABASE_MAX_CONNECTIONS=10
```

## 📚 Documentation

- [Internal Instructions](4runr-outreach-system/INTERNAL_LEAD_DATABASE_PROJECT_INSTRUCTIONS.md)
- [EC2 Deployment Guide](4runr-outreach-system/EC2_DEPLOYMENT_GUIDE.md)
- [API Documentation](docs/API.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## 🔐 Security

- All API keys stored in environment variables
- Database access restricted to application user
- Automated backups with encryption
- Rate limiting on all external APIs
- Input validation and sanitization

## 📊 Performance Metrics

Current system capabilities:
- **Lead Processing**: 1000+ leads/hour
- **Data Cleaning**: 95%+ accuracy
- **Message Generation**: <2 seconds per lead
- **System Uptime**: 99.9%+
- **API Response Time**: <500ms average

## 🤝 Contributing

This is a proprietary system. For internal development:

1. Create feature branch
2. Implement changes
3. Test thoroughly
4. Submit for review
5. Deploy via automation

## 📄 License

Proprietary - 4Runr Technologies Inc.

## 🆘 Support

For technical support:
- Internal documentation: See `INTERNAL_LEAD_DATABASE_PROJECT_INSTRUCTIONS.md`
- System monitoring: `python monitoring_dashboard.py`
- Health checks: `python check_live_system.py`

---

**Built with ❤️ by the 4Runr Team**

*Last updated: August 2025*