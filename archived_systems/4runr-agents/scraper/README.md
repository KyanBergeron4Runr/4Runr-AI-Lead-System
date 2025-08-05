# LinkedIn Scraper

This directory contains the LinkedIn scraper agent that can either generate mock leads or scrape real leads from LinkedIn using Playwright.

## Features

- **Real LinkedIn Scraping**: Uses Playwright to log into LinkedIn and scrape search results
- **Mock Data Generation**: Generates realistic mock leads for testing
- **Flexible Search**: Supports both standard LinkedIn search and Sales Navigator URLs
- **Anti-Detection**: Includes random delays and human-like behavior to avoid blocking
- **Error Handling**: Robust error handling with retry logic
- **Logging**: Comprehensive logging for monitoring and debugging

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable real scraping (set to false for mock data)
USE_REAL_SCRAPING=true

# LinkedIn credentials
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Search URL (can be standard LinkedIn or Sales Navigator)
SEARCH_URL=https://www.linkedin.com/search/results/people/?keywords=CTO&origin=SWITCH_SEARCH_VERTICAL

# Scraping limits
MAX_LEADS_PER_RUN=20
MAX_PAGES_PER_RUN=3

# Browser settings
HEADLESS=true  # Set to false for debugging
```

### Search URL Examples

**Standard LinkedIn Search:**
```
https://www.linkedin.com/search/results/people/?keywords=CTO&origin=SWITCH_SEARCH_VERTICAL
```

**LinkedIn with Location Filter:**
```
https://www.linkedin.com/search/results/people/?keywords=CTO&geoUrn=%5B"103644278"%5D&origin=FACETED_SEARCH
```

**Sales Navigator Search:**
```
https://www.linkedin.com/sales/search/people?query=(title%3ACTO)
```

## Usage

### Testing the Scraper

Before running the full pipeline, test the scraper:

```bash
cd 4runr-agents/scraper
python test_linkedin_scraper.py
```

### Running with Docker

The scraper runs automatically as part of the Docker Compose setup:

```bash
cd 4runr-agents
docker-compose up scraper
```

### Manual Execution

To run the scraper manually:

```bash
cd 4runr-agents/scraper
python app.py
```

## Output Format

The scraper outputs leads in this format:

```json
{
  "name": "Jane Doe",
  "title": "CTO",
  "company": "TechCorp",
  "linkedin_url": "https://linkedin.com/in/janedoe",
  "email": "",
  "Needs Enrichment": true,
  "Status": "New",
  "Created At": "2024-01-15T10:30:00",
  "Updated At": "2024-01-15T10:30:00"
}
```

## Anti-Detection Features

- **Random Delays**: Adds random delays between actions to mimic human behavior
- **Realistic User Agent**: Uses a realistic browser user agent
- **Headless Mode**: Runs in headless mode by default for production
- **Error Handling**: Gracefully handles LinkedIn's anti-bot measures

## Troubleshooting

### Common Issues

1. **Login Failed**: 
   - Check your LinkedIn credentials
   - LinkedIn may require 2FA - disable it or use an app password
   - Your account might be temporarily restricted

2. **No Results Found**:
   - Verify your search URL is correct
   - Check if the search returns results when accessed manually
   - LinkedIn may have changed their HTML structure

3. **Browser Crashes**:
   - Increase Docker memory limits
   - Set `HEADLESS=false` for debugging
   - Check the logs for specific error messages

### Debugging

To debug the scraper:

1. Set `HEADLESS=false` in your `.env` file
2. Run the test script: `python test_linkedin_scraper.py`
3. Watch the browser automation in action

### Logs

The scraper logs all activities. Check the logs for:
- Login success/failure
- Number of leads found
- Extraction errors
- Navigation issues

## Security Notes

- **Credentials**: Never commit your LinkedIn credentials to version control
- **Rate Limiting**: The scraper includes delays to avoid overwhelming LinkedIn's servers
- **Terms of Service**: Ensure your use complies with LinkedIn's Terms of Service
- **Account Safety**: Use a dedicated LinkedIn account for scraping to avoid affecting your main account

## Development

### Adding New Selectors

If LinkedIn changes their HTML structure, update the selectors in `linkedin_scraper.py`:

```python
# Update these arrays with new selectors
name_selectors = [
    '.entity-result__title-text a span[aria-hidden="true"]',
    # Add new selectors here
]
```

### Extending Functionality

To add new features:
1. Modify `linkedin_scraper.py` for core scraping logic
2. Update `app.py` for integration with the pipeline
3. Add new environment variables to `.env.example`
4. Update this README with documentation

## Files

- `app.py`: Main scraper agent that integrates with the pipeline
- `linkedin_scraper.py`: Core LinkedIn scraping functionality using Playwright
- `test_linkedin_scraper.py`: Test script for the scraper
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container definition with Playwright setup
- `README.md`: This documentation