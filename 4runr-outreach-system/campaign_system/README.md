# Multi-Step Email Campaign System

A sophisticated email sequencing system that extends the 4Runr Autonomous Outreach System with strategic multi-message campaigns.

## Overview

This system transforms single-touch outreach into strategic multi-step campaigns that build relationships through progressive engagement. Each campaign consists of three strategically crafted messages:

- **Hook** (Day 0): Positioning & curiosity with light CTA
- **Proof** (Day 3): Differentiation & value without pitching  
- **FOMO** (Day 7): Urgency & scarcity while maintaining professionalism

## Features

✅ **Strategic Message Progression**: Each message serves a distinct purpose in building relationships
✅ **Intelligent Scheduling**: Automated timing with business day awareness
✅ **Response Detection**: Automatic campaign pausing when leads respond
✅ **Comprehensive Analytics**: Performance tracking by message type and conversion funnels
✅ **Quality Control**: Maintains 4Runr's elevated brand positioning throughout
✅ **Seamless Integration**: Builds on existing lead validation and enrichment

## Architecture

```
Campaign System/
├── models/              # Data models (Campaign, Queue, Analytics)
├── database/            # Database schema and connection management
├── campaign_generator/  # AI-powered campaign creation
├── scheduler/           # Campaign timing and scheduling
├── queue_manager/       # Message delivery coordination
├── executor/            # Message sending and tracking
├── response_monitor/    # Response detection and campaign management
└── analytics/           # Performance tracking and reporting
```

## Quick Start

### 1. Initialize the System

```bash
cd 4runr-outreach-system
python campaign_system/init_campaign_system.py
```

### 2. Test the Foundation

```bash
python test_campaign_foundation.py
```

### 3. Environment Configuration

Add these variables to your `.env` file:

```env
# Campaign Timing
HOOK_MESSAGE_DELAY_DAYS=0
PROOF_MESSAGE_DELAY_DAYS=3
FOMO_MESSAGE_DELAY_DAYS=7

# Campaign Behavior
RESPECT_BUSINESS_DAYS=true
DEFAULT_TIMEZONE=UTC
MAX_CAMPAIGNS_PER_BATCH=50

# AI Configuration (extends existing)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4
AI_TEMPERATURE=0.7

# Database
CAMPAIGN_DATABASE_PATH=campaigns.db

# Response Monitoring
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USERNAME=your_email@gmail.com
IMAP_PASSWORD=your_app_password
```

## Data Models

### Campaign Model
Represents a complete multi-step campaign with messages, status tracking, and performance metrics.

### Message Queue Model  
Manages scheduled message delivery with retry logic and failure handling.

### Campaign Analytics Model
Tracks performance metrics, engagement rates, and conversion data.

## Database Schema

The system uses SQLite with the following tables:
- `campaigns` - Main campaign records
- `campaign_messages` - Individual messages within campaigns
- `message_queue` - Scheduled message delivery queue
- `campaign_analytics` - Performance tracking data

## Integration Points

### Existing Lead System
- Uses validated leads (Real/Pattern email confidence only)
- Leverages Company_Description, Top_Services, and Tone data
- Respects existing engagement status
- Integrates with Airtable field structure

### External Services
- **AI/LLM**: OpenAI GPT for message generation
- **Email**: SMTP providers for delivery
- **Monitoring**: IMAP for response detection
- **Analytics**: Performance tracking and reporting

## Message Examples

### Hook Message (Day 0)
```
Subject: Travel tech is evolving fast — is trivago still ahead?

Hi Johannes,

Platforms like trivago changed the game by making hotel search effortless. But now, even that category is evolving — faster personalization, AI-native flows, zero-friction booking.

We're helping companies stay ahead of the curve without duct-taping new tools onto old infrastructure.

Would it make sense to connect briefly and compare notes on where things are heading?

— 4Runr Team
```

### Proof Message (Day 3)
```
Subject: What makes the fastest travel platforms win?

Hi Johannes,

From what we've seen, it's not the brand or budget that wins in travel tech anymore — it's the system layer.

The teams getting ahead are building lean, modular infrastructure that:
• Cuts booking flow friction by 25–40%
• Personalizes without compromising speed
• Automates decisions, not just responses

That's exactly what we help optimize — quietly, and often invisibly.

Let me know if it's worth a quick chat on what's working best at your scale.

— 4Runr Team
```

### FOMO Message (Day 7)
```
Subject: Final note — some platforms are locking in their edge

Hi Johannes,

A few of your competitors are already testing systems that streamline booking flow logic and reduce decision drop-offs. Quiet upgrades — big results.

That edge compounds fast.

If you're open to it, I'd love to share how we're helping similar platforms unlock performance without adding complexity.

No pressure — just figured I'd close the loop.

— 4Runr Team
```

## Development Status

### ✅ Completed (Task 1)
- [x] Campaign system foundation and data models
- [x] Database schema and migration scripts  
- [x] Configuration management
- [x] Core data models (Campaign, Queue, Analytics)
- [x] Foundation testing and validation

### 🚧 In Progress
- [ ] Campaign Generator with AI integration
- [ ] Campaign Scheduler with intelligent timing
- [ ] Message Queue Manager
- [ ] Campaign Executor
- [ ] Response Monitor
- [ ] Analytics and Reporting

## Testing

Run the foundation tests:
```bash
python test_campaign_foundation.py
```

## Contributing

This system follows the existing 4Runr codebase patterns and integrates seamlessly with the current outreach infrastructure.

## License

Part of the 4Runr Autonomous Outreach System.