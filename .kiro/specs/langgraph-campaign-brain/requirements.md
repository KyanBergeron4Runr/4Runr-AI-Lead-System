# Requirements Document

## Introduction

The LangGraph Campaign Brain System represents a revolutionary upgrade to the 4Runr Autonomous Outreach System, replacing rule-based campaign flows with an intelligent AI agent that dynamically manages messaging, decision logic, memory, and sequencing. This system serves as the "thinking layer" that governs lead trait detection, campaign planning, message generation using GPT-4o, quality scoring, queue injection, and memory-aware decision flows. The LangGraph-powered agent provides sophisticated reasoning capabilities, adaptive campaign strategies, and continuous learning from campaign outcomes while maintaining 4Runr's elevated brand positioning.

## Requirements

### Requirement 1: LangGraph Agent Architecture

**User Story:** As a system architect, I want a LangGraph-powered AI agent that manages the entire campaign lifecycle through connected nodes, so that the system can make intelligent decisions and adapt strategies based on lead characteristics and campaign performance.

#### Acceptance Criteria

1. WHEN initializing the system THEN the agent SHALL create a connected graph of 7 core nodes: trait_detector, campaign_planner, message_generator, message_reviewer, quality_gatekeeper, injector, and memory_manager
2. WHEN processing leads THEN the agent SHALL flow data through nodes based on decision logic and quality gates
3. WHEN making decisions THEN each node SHALL have clear input/output specifications and processing logic
4. WHEN handling failures THEN the agent SHALL implement retry logic and fallback mechanisms
5. WHEN tracking execution THEN the system SHALL maintain comprehensive trace logs of decision paths
6. WHEN managing state THEN the agent SHALL persist campaign state and memory across executions
7. WHEN scaling operations THEN the architecture SHALL support concurrent processing of multiple leads

### Requirement 2: Intelligent Trait Detection

**User Story:** As a campaign strategist, I want AI-powered trait detection that analyzes lead and company data to identify strategic characteristics, so that campaigns can be tailored to specific business contexts and decision-maker profiles.

#### Acceptance Criteria

1. WHEN analyzing leads THEN the trait_detector SHALL process lead objects and scraped website content
2. WHEN identifying traits THEN the system SHALL output JSON lists of traits like ["enterprise", "travel_tech", "multi_language"]
3. WHEN detecting company characteristics THEN the system SHALL identify business model, technology stack, market position, and growth stage
4. WHEN analyzing decision makers THEN the system SHALL identify role-specific traits, seniority level, and likely priorities
5. WHEN processing website content THEN the system SHALL extract tone, messaging style, and strategic positioning
6. WHEN storing traits THEN the system SHALL maintain trait confidence scores and reasoning
7. WHEN updating traits THEN the system SHALL support both rule-based detection and future GPT-based enhancement

### Requirement 3: Dynamic Campaign Planning

**User Story:** As a campaign manager, I want intelligent campaign planning that maps detected traits to optimal messaging sequences, so that each lead receives a strategically designed campaign based on their specific characteristics.

#### Acceptance Criteria

1. WHEN receiving traits THEN the campaign_planner SHALL map traits to optimal campaign sequences
2. WHEN planning sequences THEN the system SHALL output campaign structures like ["hook", "proof", "fomo"] with tone and messaging angles
3. WHEN determining messaging angles THEN the planner SHALL select from strategic approaches based on trait combinations
4. WHEN setting campaign tone THEN the system SHALL match company communication style while maintaining 4Runr positioning
5. WHEN optimizing sequences THEN the planner SHALL use performance data to improve trait-to-sequence mappings
6. WHEN handling edge cases THEN the system SHALL provide fallback sequences for unknown trait combinations
7. WHEN tracking effectiveness THEN the planner SHALL log sequence performance for continuous improvement

### Requirement 4: GPT-4o Message Generation

**User Story:** As a content creator, I want GPT-4o powered message generation using modular prompts, so that each message type is crafted with specialized instructions while maintaining consistency across the campaign.

#### Acceptance Criteria

1. WHEN generating messages THEN the message_generator SHALL use GPT-4o for all content creation
2. WHEN loading prompts THEN the system SHALL use external .j2 files for each message type (hook.j2, proof.j2, fomo.j2)
3. WHEN creating content THEN each message SHALL include both subject line and body content
4. WHEN maintaining consistency THEN all messages SHALL use consistent lead information and company insights
5. WHEN personalizing content THEN the generator SHALL incorporate detected traits and messaging angles
6. WHEN handling failures THEN the system SHALL implement retry logic with prompt variations
7. WHEN optimizing prompts THEN the system SHALL support A/B testing of different prompt templates

### Requirement 5: Comprehensive Message Review

**User Story:** As a quality assurance manager, I want automated message review that evaluates personalization, strategic insight, tone fit, and clarity, so that only high-quality messages proceed to the sending queue.

#### Acceptance Criteria

1. WHEN reviewing messages THEN the message_reviewer SHALL evaluate personalization quality and relevance
2. WHEN assessing content THEN the system SHALL check for strategic insight and business value
3. WHEN validating tone THEN the reviewer SHALL ensure consistency with company communication style
4. WHEN measuring clarity THEN the system SHALL assess message readability and call-to-action effectiveness
5. WHEN scoring messages THEN the reviewer SHALL return raw scores (0-100) with detailed validation feedback
6. WHEN identifying issues THEN the system SHALL flag specific problems like generic language or poor personalization
7. WHEN providing feedback THEN the reviewer SHALL suggest specific improvements for failed messages

### Requirement 6: Quality Gatekeeper Logic

**User Story:** As a campaign manager, I want intelligent quality gates that determine whether messages meet sending standards, so that only approved content reaches prospects while failed messages are handled appropriately.

#### Acceptance Criteria

1. WHEN evaluating messages THEN the quality_gatekeeper SHALL use score thresholds (≥80 to continue)
2. WHEN messages fail THEN the system SHALL retry generation with improved prompts (maximum 2 retries)
3. WHEN retries are exhausted THEN the gatekeeper SHALL flag campaigns for manual review
4. WHEN approving messages THEN the system SHALL proceed to queue injection
5. WHEN rejecting messages THEN the system SHALL set campaign status to "stalled" with detailed reasoning
6. WHEN tracking attempts THEN the gatekeeper SHALL log all retry attempts and outcomes
7. WHEN escalating issues THEN the system SHALL provide actionable feedback for manual intervention

### Requirement 7: Queue Injection and Campaign Management

**User Story:** As a delivery manager, I want automated queue injection for approved messages and proper campaign status management, so that high-quality campaigns are delivered while problematic ones are handled appropriately.

#### Acceptance Criteria

1. WHEN messages are approved AND lead has valid email THEN the injector SHALL send campaigns to the MessageQueue system
2. WHEN injection succeeds THEN the system SHALL update campaign status to "queued" or "active"
3. WHEN injection fails THEN the system SHALL retry injection and log failure reasons
4. WHEN campaigns are rejected THEN the injector SHALL set status to "stalled" with detailed error information
5. WHEN managing status THEN the system SHALL maintain campaign state consistency across all components
6. WHEN tracking delivery THEN the injector SHALL coordinate with existing delivery systems
7. WHEN handling errors THEN the system SHALL provide clear escalation paths for failed injections

### Requirement 7.1: LinkedIn Manual Messaging for Leads Without Email

**User Story:** As a campaign manager, I want leads without valid email addresses but with LinkedIn URLs to be processed through the full Campaign Brain and saved for manual LinkedIn outreach, so that no qualified leads are missed due to missing email addresses.

#### Acceptance Criteria

1. WHEN processing leads THEN the system SHALL identify leads with LinkedIn URLs but no valid email addresses
2. WHEN lead has LinkedIn URL AND no valid email THEN the system SHALL process through full Campaign Brain (trait detection → sequence planning → message generation)
3. WHEN lead lacks valid email THEN the system SHALL NOT inject into email delivery queue
4. WHEN campaign is generated for LinkedIn lead THEN the system SHALL format the 3-message campaign as a combined text block
5. WHEN saving LinkedIn campaigns THEN the system SHALL update Airtable "AI Message" field with formatted campaign content
6. WHEN updating lead status THEN the system SHALL set "Messaging Method" to "Manual LinkedIn"
7. WHEN campaign is saved THEN the system SHALL NOT mark as messaged or delivered in the delivery system

### Requirement 8: Memory-Aware Decision Flow

**User Story:** As a system administrator, I want memory management that tracks lead interactions and campaign history, so that the agent can make informed decisions based on previous attempts and outcomes.

#### Acceptance Criteria

1. WHEN processing leads THEN the memory_manager SHALL track per-lead traits, messages attempted, and score outcomes
2. WHEN storing memory THEN the system SHALL maintain campaign status and decision history
3. WHEN making decisions THEN nodes SHALL access memory to inform strategy and avoid repetition
4. WHEN updating memory THEN the system SHALL record all significant events and outcomes
5. WHEN persisting data THEN memory SHALL be stored in Redis or similar fast-access storage
6. WHEN retrieving memory THEN the system SHALL provide quick access to lead history and performance data
7. WHEN managing memory THEN the system SHALL implement data retention policies and cleanup procedures

### Requirement 9: Comprehensive Trace Logging

**User Story:** As a system analyst, I want detailed trace logs that capture decision paths and reasoning, so that campaign performance can be analyzed and the system can be continuously improved.

#### Acceptance Criteria

1. WHEN executing campaigns THEN the system SHALL generate comprehensive trace logs for each lead
2. WHEN logging decisions THEN traces SHALL include node execution, decision reasoning, and data flow
3. WHEN recording outcomes THEN logs SHALL capture message scores, quality flags, and final decisions
4. WHEN storing traces THEN the system SHALL save logs as structured JSON files with unique identifiers
5. WHEN analyzing performance THEN traces SHALL enable reconstruction of complete decision paths
6. WHEN debugging issues THEN logs SHALL provide sufficient detail for troubleshooting and optimization
7. WHEN managing logs THEN the system SHALL implement log rotation and archival policies

### Requirement 10: CLI Testing and Development Interface

**User Story:** As a developer, I want a CLI interface for testing individual leads and analyzing campaign brain performance, so that the system can be developed, tested, and optimized efficiently.

#### Acceptance Criteria

1. WHEN testing leads THEN the CLI SHALL accept lead JSON files and process them through the complete graph
2. WHEN displaying results THEN the interface SHALL show message objects, scores, trait tags, and decision paths
3. WHEN providing output THEN results SHALL be available in both human-readable and JSON formats
4. WHEN debugging campaigns THEN the CLI SHALL support verbose logging and step-by-step execution
5. WHEN analyzing performance THEN the interface SHALL display execution timing and resource usage
6. WHEN testing variations THEN the CLI SHALL support different configuration parameters and prompt templates
7. WHEN validating functionality THEN the CLI SHALL provide comprehensive test coverage of all graph nodes

### Requirement 11: Modular Prompt Architecture

**User Story:** As a content strategist, I want modular prompt templates that can be independently optimized, so that message generation can be continuously improved without affecting other system components.

#### Acceptance Criteria

1. WHEN organizing prompts THEN the system SHALL use separate .j2 template files for each message type
2. WHEN loading templates THEN prompts SHALL be dynamically loaded and support variable substitution
3. WHEN customizing content THEN templates SHALL support trait-based variations and personalization
4. WHEN optimizing prompts THEN individual templates SHALL be updatable without system restart
5. WHEN testing variations THEN the system SHALL support A/B testing of different prompt versions
6. WHEN maintaining consistency THEN all prompts SHALL follow 4Runr brand guidelines and positioning
7. WHEN scaling content THEN the prompt architecture SHALL support additional message types and variations

### Requirement 12: Integration with Existing Systems

**User Story:** As a system integrator, I want seamless integration with existing 4Runr systems, so that the LangGraph campaign brain enhances current capabilities without disrupting established workflows.

#### Acceptance Criteria

1. WHEN processing leads THEN the system SHALL use existing lead validation and enrichment data
2. WHEN generating messages THEN the brain SHALL leverage existing company insights and website scraping
3. WHEN injecting campaigns THEN the system SHALL integrate with existing MessageQueue and delivery systems
4. WHEN logging activities THEN the brain SHALL use existing logging infrastructure and monitoring
5. WHEN managing configuration THEN the system SHALL use existing environment variable and API key management
6. WHEN storing data THEN the brain SHALL coordinate with existing Airtable integration and data structures
7. WHEN handling errors THEN the system SHALL integrate with existing error handling and alerting systems

### Requirement 13: Performance and Scalability

**User Story:** As a system administrator, I want high-performance campaign processing that can handle multiple leads concurrently, so that the system can scale with business growth and campaign volume.

#### Acceptance Criteria

1. WHEN processing multiple leads THEN the system SHALL support concurrent execution of campaign graphs
2. WHEN managing resources THEN the brain SHALL optimize GPT-4o API usage and response times
3. WHEN scaling operations THEN the system SHALL handle increasing lead volumes without performance degradation
4. WHEN caching data THEN the system SHALL implement intelligent caching of traits, prompts, and decisions
5. WHEN monitoring performance THEN the system SHALL track execution times and resource utilization
6. WHEN optimizing throughput THEN the brain SHALL support batch processing and parallel execution
7. WHEN handling load THEN the system SHALL implement graceful degradation and queue management

### Requirement 14: Configuration and Customization

**User Story:** As a campaign manager, I want configurable parameters for quality thresholds, retry limits, and decision logic, so that the system can be tuned for optimal performance and business requirements.

#### Acceptance Criteria

1. WHEN setting thresholds THEN quality score limits SHALL be configurable through environment variables
2. WHEN managing retries THEN maximum retry attempts SHALL be adjustable per node type
3. WHEN customizing logic THEN decision rules SHALL support configuration without code changes
4. WHEN optimizing performance THEN timeout values and resource limits SHALL be configurable
5. WHEN testing variations THEN A/B testing parameters SHALL be manageable through configuration
6. WHEN updating settings THEN configuration changes SHALL be applied without system restart
7. WHEN monitoring operations THEN configuration SHALL include logging levels and trace detail settings

### Requirement 15: LinkedIn Campaign Formatting and Airtable Integration

**User Story:** As an operator, I want LinkedIn campaigns formatted in a clear, actionable format with proper Airtable field updates, so that I can efficiently send personalized LinkedIn messages manually.

#### Acceptance Criteria

1. WHEN formatting LinkedIn campaigns THEN the system SHALL create a combined text block with clearly labeled Hook, Proof, and FOMO sections
2. WHEN formatting messages THEN each section SHALL be prefixed with "HOOK:", "PROOF:", and "FOMO:" labels
3. WHEN including personalization THEN the system SHALL use {{first_name}} and {{company}} placeholders for manual customization
4. WHEN saving to Airtable THEN the system SHALL update the "AI Message" field with the formatted campaign content
5. WHEN updating lead status THEN the system SHALL set "Messaging Method" field to "Manual LinkedIn"
6. WHEN processing LinkedIn leads THEN the system SHALL optionally support a "Manual Message Sent" checkbox field for tracking
7. WHEN formatting content THEN the system SHALL ensure messages are optimized for LinkedIn DM character limits and style

### Requirement 16: Error Handling and Recovery

**User Story:** As a reliability engineer, I want comprehensive error handling and recovery mechanisms, so that the system maintains high availability and gracefully handles failures.

#### Acceptance Criteria

1. WHEN encountering errors THEN each node SHALL implement appropriate error handling and recovery logic
2. WHEN API calls fail THEN the system SHALL retry with exponential backoff and circuit breaker patterns
3. WHEN memory access fails THEN the brain SHALL gracefully degrade and continue processing
4. WHEN quality gates fail THEN campaigns SHALL be properly flagged and escalated for manual review
5. WHEN injection fails THEN the system SHALL maintain campaign state consistency and retry appropriately
6. WHEN logging errors THEN all failures SHALL be captured with sufficient context for debugging
7. WHEN recovering from failures THEN the system SHALL resume processing from appropriate checkpoints