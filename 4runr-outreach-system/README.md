# 4Runr Autonomous Outreach System

An intelligent lead engagement platform that scrapes company websites, generates personalized outreach messages using 4Runr's strategic messaging framework, and sends them only to validated email addresses.

## System Overview

The 4Runr Autonomous Outreach System consists of integrated modules that work together to deliver intelligent, personalized outreach:

1. **Enhanced Engager Agent**: Main orchestrator with AI-driven personalization
2. **Website Scraper Service**: Extracts company insights and context
3. **Message Generator**: Creates strategic messages using 4Runr knowledge base
4. **Email Validator**: Classifies email confidence and validation levels
5. **Engagement Tracker**: Monitors and optimizes engagement patterns

## Quick Start

### Automated Setup (Recommended)

```bash
# Run the automated setup script
python setup.py
```

### Manual Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see SETUP.md for details)
   ```

3. **Verify Installation**
   ```bash
   python verify_knowledge_base_fix.py
   python test_dependencies.py
   ```

4. **Test System**
   ```bash
   python -m engager.enhanced_engager_agent --dry-run --limit 1
   ```

### Expected Success Message
When properly configured, you should see:
```
✅ 4Runr knowledge base loaded successfully
```

## Prerequisites

- **Python 3.8+** (tested with 3.8-3.11)
- **API Keys Required:**
  - Airtable API key and base ID
  - OpenAI API key for message generation
- **Optional:** SMTP credentials for email sending

## Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup instructions and troubleshooting
- **[Knowledge Base Testing Guide](knowledge_base_testing_guide.md)** - Testing and validation
- **[Dependency Audit Results](dependency_audit_results.md)** - System dependencies overview

## Usage

### Basic Usage
```bash
# Run in dry-run mode (recommended for testing)
python -m engager.enhanced_engager_agent --dry-run --limit 5

# Run with actual email sending
python -m engager.enhanced_engager_agent --limit 5

# Process specific lead
python -m engager.enhanced_engager_agent --lead-id rec123456789
```

### Module-Specific Usage
```bash
# Website scraping only
python -m website_scraper.app --limit 5

# Message generation only  
python -m message_generator.app --limit 5

# Email validation only
python -m email_validator.app --limit 5
```

## System Architecture

The system uses a modular architecture with shared components:

- **Enhanced Engager Agent**: Orchestrates the complete engagement process
- **Knowledge Base**: Contains 4Runr's strategic messaging framework and brand guidelines
- **Website Scraper Service**: Extracts company insights using multiple scraping strategies
- **Message Generator**: Creates personalized messages aligned with 4Runr's positioning
- **Engagement Tracker**: Monitors engagement levels and prevents over-communication
- **Quality Control**: Ensures message quality and brand consistency

### Data Flow
1. Leads are retrieved from Airtable with engagement criteria
2. Company websites are scraped for context and insights
3. Messages are generated using AI with 4Runr knowledge base
4. Quality control validates message content and tone
5. Emails are sent only to validated addresses
6. Engagement results are tracked and logged

## Airtable Fields

The system uses these Airtable fields:

**Website Scraping Fields:**
- Company_Description (Long text)
- Top_Services (Long text)
- Tone (Single select)
- Website_Insights (Long text)

**Email Validation Fields:**
- Email_Confidence_Level (Single select: Real/Pattern/Guess)

**Message Generation Fields:**
- Custom_Message (Long text)
- Engagement_Status (Single select: Sent/Skipped/Needs Review/Error)

**Engagement Tracking Fields:**
- Message_Preview (Long text)
- Last_Contacted_Date (Date)
- Delivery_Method (Single select)

## Quality Assurance

The system implements comprehensive quality controls:

- **Email Validation**: Only sends to Real or Pattern confidence levels
- **Brand Consistency**: All messages align with 4Runr's strategic positioning
- **Content Quality**: Prevents generic or template-like messages
- **Engagement Limits**: Respects communication frequency and engagement levels
- **Audit Trails**: Comprehensive logging for all system activities
- **Knowledge Base Validation**: Ensures consistent access to 4Runr messaging framework

## Testing and Verification

The system includes comprehensive testing tools:

```bash
# Quick verification
python verify_knowledge_base_fix.py

# Comprehensive system test
python test_complete_system_functionality.py

# Final verification
python final_system_verification.py

# Dependency testing
python test_dependencies.py
```

## Troubleshooting

### Common Issues

1. **Knowledge Base Errors**: Run `python verify_knowledge_base_fix.py`
2. **Dependency Issues**: Run `python test_dependencies.py`
3. **API Connection**: Check API keys in `.env` file
4. **Import Errors**: Ensure you're in the correct directory and dependencies are installed

See [SETUP.md](SETUP.md) for detailed troubleshooting guide.

## Recent Updates

- ✅ Fixed knowledge base structure validation
- ✅ Updated dependencies (added jinja2, playwright)
- ✅ Enhanced error handling and logging
- ✅ Improved setup documentation and automation
- ✅ Added comprehensive testing suite

## License

UNLICENSED - Private use only