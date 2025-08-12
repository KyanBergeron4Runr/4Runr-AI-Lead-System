# 📡 4Runr AI Lead System - API Documentation

## Overview

The 4Runr AI Lead System provides a comprehensive REST API for managing leads, campaigns, and system operations. All endpoints support JSON request/response format.

## Base URL

```
Production: https://your-domain.com/api/v1
Development: http://localhost:5000/api/v1
```

## Authentication

All API requests require authentication via API key in the header:

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

## Rate Limits

- **Standard**: 1000 requests/hour
- **Premium**: 5000 requests/hour
- **Enterprise**: Unlimited

## Core Endpoints

### 🎯 Lead Management

#### Get All Leads
```http
GET /leads
```

**Parameters:**
- `limit` (optional): Number of leads to return (default: 50, max: 1000)
- `offset` (optional): Pagination offset (default: 0)
- `stage` (optional): Filter by engagement stage
- `source` (optional): Filter by lead source

**Response:**
```json
{
  "success": true,
  "data": {
    "leads": [
      {
        "id": "rec123abc",
        "name": "John Doe",
        "email": "john@company.com",
        "company": "Tech Corp",
        "engagement_stage": "1st degree",
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:30:00Z"
      }
    ],
    "total": 150,
    "limit": 50,
    "offset": 0
  }
}
```

#### Get Single Lead
```http
GET /leads/{lead_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "rec123abc",
    "name": "John Doe",
    "email": "john@company.com",
    "company": "Tech Corp",
    "company_website": "https://techcorp.com",
    "engagement_stage": "1st degree",
    "ai_message": "Hi John, I noticed Tech Corp...",
    "last_contacted": null,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Create Lead
```http
POST /leads
```

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@startup.io",
  "company": "StartupIO",
  "company_website": "https://startup.io",
  "source": "manual_entry"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "rec456def",
    "message": "Lead created successfully"
  }
}
```

#### Update Lead
```http
PUT /leads/{lead_id}
```

**Request Body:**
```json
{
  "engagement_stage": "contacted",
  "ai_message": "Updated personalized message",
  "last_contacted": "2025-01-15T14:30:00Z"
}
```

#### Delete Lead
```http
DELETE /leads/{lead_id}
```

### 🔄 Data Synchronization

#### Sync with Airtable
```http
POST /sync/airtable
```

**Request Body:**
```json
{
  "force_full_sync": false,
  "clean_data": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "synced_leads": 34,
    "cleaned_leads": 34,
    "skipped_leads": 0,
    "sync_duration": "12.5s"
  }
}
```

#### Get Sync Status
```http
GET /sync/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "last_sync": "2025-01-15T06:00:00Z",
    "next_sync": "2025-01-16T06:00:00Z",
    "sync_status": "completed",
    "total_synced": 34
  }
}
```

### 🧹 Data Cleaning

#### Clean Lead Data
```http
POST /clean/lead
```

**Request Body:**
```json
{
  "lead_data": {
    "name": "  JOHN DOE  ",
    "email": "JOHN@COMPANY.COM",
    "company": "  Tech Corp Inc.  "
  },
  "context": {
    "source": "api",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cleaned_data": {
      "name": "John Doe",
      "email": "john@company.com",
      "company": "Tech Corp Inc"
    },
    "cleaning_stats": {
      "fields_cleaned": 3,
      "confidence_score": 0.95,
      "processing_time": 0.023
    }
  }
}
```

#### Bulk Clean Leads
```http
POST /clean/bulk
```

**Request Body:**
```json
{
  "lead_ids": ["rec123", "rec456", "rec789"],
  "force_reclean": false
}
```

### 🤖 AI Operations

#### Generate AI Message
```http
POST /ai/generate-message
```

**Request Body:**
```json
{
  "lead_id": "rec123abc",
  "message_type": "initial_outreach",
  "personalization_level": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ai_message": "Hi John, I noticed Tech Corp is expanding into AI solutions...",
    "confidence_score": 0.92,
    "personalization_elements": ["company_name", "industry", "recent_news"]
  }
}
```

#### Enrich Lead
```http
POST /ai/enrich-lead
```

**Request Body:**
```json
{
  "lead_id": "rec123abc",
  "enrichment_sources": ["google", "linkedin", "company_website"]
}
```

### 📧 Campaign Management

#### Get Campaigns
```http
GET /campaigns
```

#### Create Campaign
```http
POST /campaigns
```

**Request Body:**
```json
{
  "name": "Q1 Tech Outreach",
  "target_stage": "1st degree",
  "message_template": "Hi {name}, I noticed {company}...",
  "schedule": {
    "start_date": "2025-01-20",
    "frequency": "daily",
    "max_sends_per_day": 50
  }
}
```

#### Start Campaign
```http
POST /campaigns/{campaign_id}/start
```

#### Pause Campaign
```http
POST /campaigns/{campaign_id}/pause
```

### 📊 Analytics & Reporting

#### System Health
```http
GET /health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system_status": "healthy",
    "database_status": "connected",
    "airtable_status": "synced",
    "automation_status": "running",
    "last_health_check": "2025-01-15T15:30:00Z",
    "uptime": "7d 12h 45m"
  }
}
```

#### Lead Statistics
```http
GET /analytics/leads
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_leads": 150,
    "by_stage": {
      "1st degree": 45,
      "ready_for_contact": 30,
      "contacted": 50,
      "responded": 15,
      "qualified": 10
    },
    "by_source": {
      "airtable": 120,
      "manual": 20,
      "api": 10
    },
    "quality_metrics": {
      "with_email": 140,
      "with_company": 145,
      "fully_enriched": 130
    }
  }
}
```

#### Campaign Performance
```http
GET /analytics/campaigns
```

### 🔧 System Operations

#### Automation Status
```http
GET /automation/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "automation_engine": "running",
    "last_cycle": "2025-01-15T15:25:00Z",
    "next_cycle": "2025-01-15T15:30:00Z",
    "cycles_completed": 2880,
    "average_cycle_time": "2.3s"
  }
}
```

#### Trigger Manual Operations
```http
POST /automation/trigger
```

**Request Body:**
```json
{
  "operation": "enrich_leads",
  "parameters": {
    "limit": 10,
    "force": false
  }
}
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```

### Common Error Codes

- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error (system error)

## Webhooks

### Webhook Events

The system can send webhooks for the following events:

- `lead.created` - New lead added
- `lead.updated` - Lead information changed
- `lead.enriched` - Lead enrichment completed
- `campaign.started` - Campaign execution began
- `campaign.completed` - Campaign finished
- `sync.completed` - Airtable sync finished

### Webhook Payload Example
```json
{
  "event": "lead.enriched",
  "timestamp": "2025-01-15T15:30:00Z",
  "data": {
    "lead_id": "rec123abc",
    "enrichment_source": "google",
    "fields_enriched": ["email", "company_website"],
    "confidence_score": 0.89
  }
}
```

## SDK Examples

### Python SDK
```python
from runr_api import RunrClient

client = RunrClient(api_key="your_api_key")

# Get leads
leads = client.leads.list(limit=10, stage="1st degree")

# Create lead
new_lead = client.leads.create({
    "name": "John Doe",
    "email": "john@company.com",
    "company": "Tech Corp"
})

# Sync with Airtable
sync_result = client.sync.airtable(clean_data=True)
```

### JavaScript SDK
```javascript
const { RunrClient } = require('@4runr/api-client');

const client = new RunrClient({ apiKey: 'your_api_key' });

// Get leads
const leads = await client.leads.list({ limit: 10, stage: '1st degree' });

// Generate AI message
const message = await client.ai.generateMessage({
  leadId: 'rec123abc',
  messageType: 'initial_outreach'
});
```

## Rate Limiting

Rate limits are enforced per API key:

- **Headers returned with each request:**
  - `X-RateLimit-Limit`: Request limit per hour
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

## Pagination

For endpoints returning multiple items:

```http
GET /leads?limit=50&offset=100
```

**Response includes pagination info:**
```json
{
  "data": { ... },
  "pagination": {
    "limit": 50,
    "offset": 100,
    "total": 500,
    "has_more": true
  }
}
```

## Testing

### Test Environment
```
Base URL: https://test-api.4runr.com/v1
```

### Postman Collection
Download our Postman collection: [4Runr API Collection](./postman/4runr-api.json)

---

**Need Help?**
- 📧 Email: api-support@4runr.com
- 📚 Documentation: https://docs.4runr.com
- 🐛 Issues: https://github.com/4runr/api-issues