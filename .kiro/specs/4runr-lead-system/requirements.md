# Requirements Document

## Introduction

The 4Runr Autonomous Outreach System is an intelligent lead engagement platform that scrapes company websites, generates personalized outreach messages, and sends them only to validated email addresses. The system consists of four autonomous modules: Website Scraper Agent, Message Generator Agent, Email Validation Upgrade, and Engager Agent. All engagement activities are logged in Airtable with comprehensive tracking. The system maintains 4Runr's helpful, strategic tone while ensuring no outreach is sent to fake or unvalidated leads.

## Requirements

### Requirement 1: LinkedIn Scraper (SerpAPI Agent) Website Extraction

**User Story:** As a business user, I want the LinkedIn scraper to extract website URLs from SerpAPI responses, so that I can obtain company websites for further enrichment.

#### Acceptance Criteria

1. WHEN processing SerpAPI responses THEN the system SHALL extract the website field if present in the response JSON.
2. WHEN website is found in SerpAPI response THEN the system SHALL add it to the scraped lead dictionary as "Website": website_url.
3. WHEN website is not found in SerpAPI response THEN the system SHALL set "Website": None to allow fallback Google scraping.
4. WHEN saving lead data THEN the system SHALL write the Website value to Airtable using existing integration.
5. WHEN processing leads THEN the system SHALL maintain existing SerpAPI response parsing logic without breaking changes.

### Requirement 2: Google Website Scraper (Playwright Agent)

**User Story:** As a business user, I want a Google search fallback to find company websites when SerpAPI doesn't provide them, so that I can maximize website discovery for enrichment.

#### Acceptance Criteria

1. WHEN Website field is None or empty THEN the system SHALL trigger Playwright-based Google search.
2. WHEN performing Google search THEN the system SHALL use full_name and optional company_name as search parameters.
3. WHEN searching Google THEN the system SHALL use query format "{full_name}" "{company_name}" site:.com OR site:.ca.
4. WHEN parsing search results THEN the system SHALL extract URL from first organic result (not ads).
5. WHEN website is found THEN the system SHALL save it to the Website field in Airtable.
6. WHEN no results are found THEN the system SHALL leave field blank and set Enrichment Status = Failed - No Website.
7. WHEN integrating with pipeline THEN the system SHALL only execute if lead.get("Website") is None or empty.

### Requirement 3: Website Content Scraper Agent

**User Story:** As a business user, I want an autonomous website scraper that extracts company information from discovered websites, so that I can understand each lead's business context for personalized outreach.

#### Acceptance Criteria

1. WHEN receiving a website URL from previous agents THEN the system SHALL scrape the website prioritizing /about, /services, /home, and /contact pages.
2. WHEN scraping fails on structured pages THEN the system SHALL use fallback logic to extract content from any available pages.
3. WHEN processing scraped content THEN the system SHALL remove navigation, footer, and cookie banner text to focus on meaningful content.
4. WHEN extracting company information THEN the system SHALL generate a Company_Description as a brief summary from About/Home pages.
5. WHEN identifying services THEN the system SHALL extract Top_Services as a list or summary of key offerings.
6. WHEN analyzing website content THEN the system SHALL estimate the company Tone (formal, bold, friendly, etc.).
7. WHEN saving results THEN the system SHALL store Website_Insights as raw scraped sections for context in Airtable.

### Requirement 4: Improved Enricher Agent

**User Story:** As a business user, I want an enhanced enricher that uses website content to extract business traits and insights, so that I can generate more targeted outreach messages.

#### Acceptance Criteria

1. WHEN Website exists THEN the system SHALL scrape homepage/meta content using existing scraper module.
2. WHEN analyzing website content THEN the system SHALL run OpenAI call to extract Business Type (e.g., "B2B SaaS", "e-commerce", "law firm").
3. WHEN processing website data THEN the system SHALL identify Traits (e.g., "local service", "AI-powered", "needs automation").
4. WHEN analyzing company messaging THEN the system SHALL infer Pain Points from product descriptions and website content.
5. WHEN saving enrichment results THEN the system SHALL update Response Notes field with extracted insights.
6. WHEN storing business classification THEN the system SHALL save Business Type as optional new field.
7. WHEN enrichment is complete THEN the system SHALL cache result in Airtable to avoid re-running.

### Requirement 5: Enhanced Message Generator Agent with Fallback Logic

**User Story:** As a business user, I want an AI-powered message generator with fallback capabilities, so that every lead receives outreach even when enrichment data is incomplete.

#### Acceptance Criteria

1. WHEN Response Notes and Website are available THEN the system SHALL use Company_Description, Top_Services, Tone, Lead_Name, Lead_Role, Company_Name, and Email_Confidence_Level as inputs.
2. WHEN Response Notes or Website are missing THEN the system SHALL generate fallback message using person name, email domain, job title, and generic pain points.
3. WHEN creating fallback messages THEN the system SHALL use email domain (e.g., @xyz.com → xyz) for company context.
4. WHEN generating fallback content THEN the system SHALL apply generic pain points based on industry guess from domain/title.
5. WHEN using fallback logic THEN the system SHALL mark message with Used Fallback: ✅ flag in Airtable.
6. WHEN creating outreach content THEN the system SHALL generate Custom_Message as a short outreach email in 4Runr's helpful, strategic tone.
7. WHEN determining send eligibility THEN the system SHALL set Engagement_Status to Auto-Send only if Email_Confidence_Level is Real or Pattern.
8. WHEN Email_Confidence_Level is Guess or empty THEN the system SHALL set Engagement_Status to Skip.
9. WHEN message quality is uncertain THEN the system SHALL set Engagement_Status to Needs Review.
10. WHEN crafting messages THEN the system SHALL ensure content is helpful, strategic, tailored to available data, non-salesy but clear in value.
11. WHEN generating content THEN the system SHALL avoid templates or generic intros, ensuring each message is unique and personalized.

### Requirement 6: Email Validation Upgrade

**User Story:** As a system administrator, I want enhanced email validation that classifies email confidence levels, so that outreach is only sent to validated email addresses.

#### Acceptance Criteria

1. WHEN processing enriched leads THEN the system SHALL classify each email based on its source and reliability.
2. WHEN email is found via direct scrape (mailto: or page copy) THEN the system SHALL mark Email_Confidence_Level as Real.
3. WHEN email follows standard patterns (john.doe@company.com) THEN the system SHALL mark Email_Confidence_Level as Pattern.
4. WHEN email is generated through fallback logic only THEN the system SHALL mark Email_Confidence_Level as Guess.
5. WHEN saving validation results THEN the system SHALL store Email_Confidence_Level (Real/Pattern/Guess) in Airtable.
6. WHEN validating email format THEN the system SHALL perform syntax validation and domain verification.
7. WHEN confidence level is determined THEN the system SHALL use this information to gate message sending.

### Requirement 7: Engager Agent

**User Story:** As a business user, I want an autonomous engager that sends personalized messages only to validated emails, so that outreach efforts are focused on real prospects.

#### Acceptance Criteria

1. WHEN processing leads for engagement THEN the system SHALL only send messages if Email_Confidence_Level is Real or Pattern.
2. WHEN Email_Confidence_Level is Guess or empty THEN the system SHALL skip the lead and not attempt contact.
3. WHEN sending messages THEN the system SHALL use the Custom_Message generated by the Message Generator Agent.
4. WHEN engagement is completed THEN the system SHALL update Engagement_Status to Sent, Skipped, or Error in Airtable.
5. WHEN messages are sent THEN the system SHALL save Message_Preview as a snapshot of the sent content.
6. WHEN contact is made THEN the system SHALL record Last_Contacted_Date as today's date.
7. WHEN updating records THEN the system SHALL set Delivery_Method to Email, LinkedIn DM, or Skipped based on the action taken.

### Requirement 8: Airtable Field Structure

**User Story:** As a system administrator, I want comprehensive Airtable field structure to track all outreach activities, so that engagement history and lead status are properly maintained.

#### Acceptance Criteria

1. WHEN storing website URLs THEN the system SHALL create Website field as URL for discovered company websites.
2. WHEN storing website data THEN the system SHALL create Company_Description field as Long text for site summary.
3. WHEN saving service information THEN the system SHALL create Top_Services field as Long text for key offerings.
4. WHEN recording website analysis THEN the system SHALL create Tone field as Single select (Bold, Formal, Friendly, etc.).
5. WHEN preserving context THEN the system SHALL create Website_Insights field as Long text for raw scraped content.
6. WHEN storing enrichment data THEN the system SHALL create Response Notes field as Long text for business insights.
7. WHEN classifying businesses THEN the system SHALL create Business Type field as Single select for business categories.
8. WHEN tracking fallback usage THEN the system SHALL create Used Fallback field as Checkbox for fallback message tracking.
9. WHEN tracking email quality THEN the system SHALL create Email_Confidence_Level field as Single select (Real/Pattern/Guess).
10. WHEN storing messages THEN the system SHALL create Custom_Message field as Long text for generated outreach.
11. WHEN tracking engagement THEN the system SHALL create Engagement_Status field as Single select (Sent/Skipped/Needs Review/Error/Failed - No Website).
12. WHEN preserving message history THEN the system SHALL create Message_Preview field as Long text for message snapshots.
13. WHEN recording contact dates THEN the system SHALL create Last_Contacted_Date field as Date for tracking.
14. WHEN logging delivery methods THEN the system SHALL create Delivery_Method field as Single select (Email/LinkedIn DM/Skipped).

### Requirement 9: Modular Architecture

**User Story:** As a developer, I want a modular system architecture, so that individual components can be run independently and the system is maintainable.

#### Acceptance Criteria

1. WHEN designing the system THEN each module (LinkedIn Scraper, Google Scraper, Website Scraper, Enricher, Message Generator, Email Validation, Engager) SHALL be independently executable.
2. WHEN running components THEN each agent SHALL be runnable independently of other modules.
3. WHEN organizing code THEN the system SHALL follow existing agent boundaries without restructuring shared code.
4. WHEN implementing modules THEN each SHALL have well-defined inputs and outputs for integration.
5. WHEN creating interfaces THEN modules SHALL communicate through standardized data formats.
6. WHEN adding new functionality THEN the system SHALL reuse existing components and follow modular agent flow.

### Requirement 10: Quality Assurance and Validation

**User Story:** As a business user, I want quality assurance measures that prevent sending to fake leads, so that 4Runr's reputation is protected and outreach is effective.

#### Acceptance Criteria

1. WHEN processing leads THEN the system SHALL implement validation gates to prevent sending to fake leads.
2. WHEN generating messages THEN the system SHALL ensure message quality reflects 4Runr's standards with no templates or generic content.
3. WHEN validating emails THEN the system SHALL enforce strict validation before allowing message sending.
4. WHEN encountering low-quality data THEN the system SHALL skip rather than attempt contact.
5. WHEN processing leads THEN the system SHALL maintain audit trails for all validation decisions.

### Requirement 11: Logging and Monitoring

**User Story:** As a system administrator, I want comprehensive logging and monitoring, so that I can track system performance and troubleshoot issues.

#### Acceptance Criteria

1. WHEN processing leads THEN the system SHALL log all activities in terminal with clear status updates.
2. WHEN completing engagements THEN the system SHALL optionally save JSON logs of each engagement attempt.
3. WHEN errors occur THEN the system SHALL log detailed error information for troubleshooting.
4. WHEN modules execute THEN the system SHALL provide progress indicators and completion status.
5. WHEN saving logs THEN the system SHALL include timestamps, lead identifiers, and action results.

### Requirement 12: Configuration and Environment Management

**User Story:** As a system administrator, I want secure configuration management, so that API keys and settings are properly managed.

#### Acceptance Criteria

1. WHEN setting up the system THEN configuration SHALL be managed through environment variables.
2. WHEN accessing external services THEN API keys SHALL be stored securely in .env files.
3. WHEN deploying the system THEN sensitive information SHALL never be committed to version control.
4. WHEN configuring modules THEN each SHALL access configuration through a centralized config system.
5. WHEN documenting setup THEN clear instructions SHALL be provided for environment configuration.