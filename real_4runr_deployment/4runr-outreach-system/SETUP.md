# 4Runr Outreach System Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and configuration
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

## Detailed Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- API keys for Airtable and OpenAI

### Step 1: Environment Setup

#### Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: If you encounter issues with playwright, you may need to install browser binaries:
```bash
playwright install
```

### Step 2: Configuration

#### Environment Variables
Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Edit `.env` with your actual values:

**Required Configuration:**
- `AIRTABLE_API_KEY`: Your Airtable API key
- `AIRTABLE_BASE_ID`: Your Airtable base ID
- `OPENAI_API_KEY`: Your OpenAI API key

**Optional Configuration:**
- `SMTP_*`: Email sending configuration
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `BATCH_SIZE`: Number of leads to process at once

#### API Key Setup

**Airtable API Key:**
1. Go to https://airtable.com/account
2. Generate a personal access token
3. Copy the token to `AIRTABLE_API_KEY` in your `.env` file

**OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key to `OPENAI_API_KEY` in your `.env` file

### Step 3: Verification

#### Test Dependencies
```bash
python test_dependencies.py
```
Expected output:
```
✅ python-dotenv: Successfully imported
✅ pyairtable: Successfully imported
✅ validators: Successfully imported
✅ requests: Successfully imported
✅ beautifulsoup4: Successfully imported
✅ playwright: Successfully imported
✅ openai: Successfully imported
✅ jinja2: Successfully imported
🎉 All dependencies are working correctly!
```

#### Test Knowledge Base
```bash
python verify_knowledge_base_fix.py
```
Expected output:
```
✅ PASS: Knowledge base validation successful
✅ All required sections present
✅ Content length: 7006 characters (good)
🎉 KNOWLEDGE BASE FIX VERIFIED!
```

#### Test Complete System
```bash
python -m engager.enhanced_engager_agent --dry-run --limit 1
```
Expected success message:
```
✅ 4Runr knowledge base loaded successfully
```

### Step 4: Usage

#### Basic Usage
```bash
# Run in dry-run mode (no actual emails sent)
python -m engager.enhanced_engager_agent --dry-run --limit 5

# Run with actual email sending
python -m engager.enhanced_engager_agent --limit 5

# Process specific lead by ID
python -m engager.enhanced_engager_agent --lead-id rec123456789
```

#### Module-Specific Usage
```bash
# Run only the website scraper
python -m website_scraper.app --limit 5

# Run only the message generator
python -m message_generator.app --limit 5

# Run only the email validator
python -m email_validator.app --limit 5
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` or `ImportError`
**Solution**: 
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Check if you're in the correct directory
pwd  # Should show the 4runr-outreach-system directory

# Try with PYTHONPATH
PYTHONPATH=. python -m engager.enhanced_engager_agent --dry-run --limit 1
```

#### 2. Knowledge Base Issues
**Problem**: "Knowledge base missing sections" error
**Solution**:
```bash
# Run the knowledge base verification
python verify_knowledge_base_fix.py

# If it fails, check that data/4runr_knowledge.md exists and has all required sections
```

#### 3. API Connection Issues
**Problem**: Airtable or OpenAI API errors
**Solution**:
- Verify API keys in `.env` file
- Check API key permissions and quotas
- Ensure internet connection is working

#### 4. Playwright Issues
**Problem**: Browser automation errors
**Solution**:
```bash
# Install browser binaries
playwright install

# Or install specific browser
playwright install chromium
```

### Verification Commands

Run these commands to verify your setup:

```bash
# 1. Test all dependencies
python test_dependencies.py

# 2. Test knowledge base
python verify_knowledge_base_fix.py

# 3. Test complete system
python test_complete_system_functionality.py

# 4. Final verification
python final_system_verification.py

# 5. Test actual engager agent
python -m engager.enhanced_engager_agent --dry-run --limit 1
```

### Expected Success Indicators

When everything is working correctly, you should see:

1. ✅ All dependencies import successfully
2. ✅ Knowledge base validation passes
3. ✅ System logs: "4Runr knowledge base loaded successfully"
4. ✅ No "missing sections" warnings
5. ✅ Agent initializes all components successfully

## Development Workflow

### Making Changes

1. **Before making changes**: Run verification tests
2. **After making changes**: Run verification tests again
3. **Before committing**: Ensure all tests pass

### Testing Changes

```bash
# Quick verification
python verify_knowledge_base_fix.py

# Comprehensive testing
python test_complete_system_functionality.py

# Test with actual agent
python -m engager.enhanced_engager_agent --dry-run --limit 1
```

### Updating Dependencies

When adding new dependencies:

1. Install the package: `pip install package_name`
2. Update requirements.txt: `pip freeze > requirements.txt`
3. Test that everything still works
4. Update this documentation if needed

## Support

If you encounter issues not covered in this guide:

1. Check the logs in the `logs/` directory
2. Run the verification scripts to identify the specific issue
3. Ensure all environment variables are properly set
4. Verify that all API keys have the necessary permissions

## File Structure

```
4runr-outreach-system/
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── SETUP.md                 # This setup guide
├── data/
│   └── 4runr_knowledge.md   # Knowledge base content
├── engager/                 # Main engager module
├── shared/                  # Shared utilities
├── test_*.py               # Test scripts
└── verify_*.py             # Verification scripts
```