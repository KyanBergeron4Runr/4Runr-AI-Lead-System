# 🔌 Ultimate 4Runr API Documentation

## System API Endpoints

The Ultimate 4Runr system provides these APIs for integration:

### Health Check
```
GET /health
```
Returns system health status and performance metrics.

### Enrich Lead
```
POST /enrich
{
  "full_name": "John Smith",
  "company": "TechCorp",
  "linkedin_url": "https://linkedin.com/in/johnsmith"
}
```

### Get Performance Stats
```
GET /stats
```
Returns real-time performance statistics.

### Run Tests
```
POST /test
{
  "test_type": "hardcore|accuracy|stress"
}
```

## Integration Examples

### Python
```python
import requests

# Enrich a lead
response = requests.post('http://localhost:8080/enrich', json={
    'full_name': 'Jane Doe',
    'company': 'Marketing Inc'
})

result = response.json()
print(f"Email: {result['email']}")
print(f"Confidence: {result['confidence']}%")
```

### cURL
```bash
curl -X POST http://localhost:8080/enrich \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Bob Johnson", "company": "Consulting LLC"}'
```

---

**🚀 Ready for enterprise integration!**
