# 4Runr Autonomous Outreach System

An intelligent lead engagement platform that scrapes company websites, generates personalized outreach messages, and sends them only to validated email addresses.

## System Overview

The 4Runr Autonomous Outreach System consists of four autonomous modules:

1. **Website Scraper Agent**: Extracts company information from websites
2. **Message Generator Agent**: Creates personalized outreach messages using AI
3. **Email Validation Upgrade**: Classifies email confidence levels
4. **Engager Agent**: Sends messages only to validated email addresses

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Airtable account with API key
- OpenAI API key for message generation

### Installation

1. Clone and navigate to the project:
   ```bash
   cd 4runr-outreach-system
   ```

2. Create environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run individual modules:
   ```bash
   python website_scraper/app.py
   python message_generator/app.py
   python email_validator/app.py
   python engager/app.py
   ```

5. Or run the complete pipeline:
   ```bash
   python run_outreach_pipeline.py
   ```

## Module Architecture

Each module can be run independently and communicates through Airtable:

- **Website Scraper**: Processes leads with `company_website_url` → Updates with company insights
- **Message Generator**: Uses company data → Creates personalized messages
- **Email Validator**: Classifies email confidence → Sets validation levels
- **Engager**: Sends to validated emails only → Logs engagement results

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

The system implements strict validation gates:
- Only sends to Real or Pattern email confidence levels
- Skips Guess or empty email addresses
- Maintains 4Runr's helpful, strategic tone
- Prevents template-like or generic messages
- Comprehensive logging for audit trails

## License

UNLICENSED - Private use only