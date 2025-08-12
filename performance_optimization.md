# 🚀 Performance Optimization Guide

## Overview

This guide provides comprehensive performance optimization strategies for the 4Runr AI Lead System to ensure optimal performance under various load conditions.

## 🎯 Performance Targets

### Current Benchmarks
- **Lead Processing**: 1000+ leads/hour
- **Data Cleaning**: 95%+ accuracy in <2 seconds
- **API Response Time**: <500ms average
- **Database Operations**: <100ms for standard queries
- **System Uptime**: 99.9%+

### Scaling Targets
- **High Volume**: 5000+ leads/hour
- **Concurrent Users**: 50+ simultaneous operations
- **Database Size**: 1M+ leads with consistent performance

## 🔧 Database Optimization

### SQLite Optimization

```python
# Optimal SQLite configuration for high performance
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -128000;  # 128MB cache
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;  # 256MB memory map
```

### Connection Pool Settings

```env
# High Performance Settings
LEAD_DATABASE_MAX_CONNECTIONS=50
LEAD_DATABASE_CONNECTION_TIMEOUT=60
LEAD_DATABASE_CACHE_SIZE=-128000

# Memory Constrained Settings
LEAD_DATABASE_MAX_CONNECTIONS=10
LEAD_DATABASE_CONNECTION_TIMEOUT=30
LEAD_DATABASE_CACHE_SIZE=-32000
```

### Index Optimization

```sql
-- Essential indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company);
CREATE INDEX IF NOT EXISTS idx_leads_engagement_stage ON leads(engagement_stage);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_updated_at ON leads(updated_at);
CREATE INDEX IF NOT EXISTS idx_leads_last_contacted ON leads(last_contacted);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_leads_stage_email ON leads(engagement_stage, email);
CREATE INDEX IF NOT EXISTS idx_leads_company_stage ON leads(company, engagement_stage);
```

## 🚀 Application Performance

### Batch Processing Optimization

```python
# Optimal batch sizes for different operations
BATCH_SIZES = {
    'data_cleaning': 50,
    'enrichment': 20,
    'message_generation': 30,
    'airtable_sync': 100,
    'database_insert': 200
}

# Concurrent processing limits
CONCURRENT_LIMITS = {
    'high_memory': 10,
    'medium_memory': 5,
    'low_memory': 2
}
```

### Memory Management

```python
# Memory optimization strategies
import gc
import psutil

def optimize_memory():
    """Optimize memory usage"""
    # Force garbage collection
    gc.collect()
    
    # Check memory usage
    memory_percent = psutil.virtual_memory().percent
    
    if memory_percent > 80:
        # Reduce batch sizes
        return {
            'batch_size': 10,
            'concurrent_limit': 2,
            'cache_size': -16000
        }
    elif memory_percent > 60:
        return {
            'batch_size': 25,
            'concurrent_limit': 5,
            'cache_size': -64000
        }
    else:
        return {
            'batch_size': 50,
            'concurrent_limit': 10,
            'cache_size': -128000
        }
```

### Caching Strategies

```python
# Implement intelligent caching
from functools import lru_cache
import redis

# In-memory caching for frequently accessed data
@lru_cache(maxsize=1000)
def get_company_info(company_name):
    """Cache company information"""
    pass

# Redis caching for shared data
def setup_redis_cache():
    """Setup Redis for distributed caching"""
    return redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True,
        socket_keepalive=True,
        socket_keepalive_options={}
    )
```

## 🌐 API Performance

### Rate Limiting Optimization

```python
# Intelligent rate limiting
RATE_LIMITS = {
    'openai': {
        'requests_per_minute': 50,
        'tokens_per_minute': 40000,
        'backoff_strategy': 'exponential'
    },
    'airtable': {
        'requests_per_second': 5,
        'backoff_strategy': 'linear'
    },
    'serpapi': {
        'requests_per_hour': 100,
        'backoff_strategy': 'exponential'
    }
}

# Adaptive rate limiting based on response times
def adaptive_rate_limit(api_name, response_time):
    """Adjust rate limits based on API performance"""
    if response_time > 2.0:
        # Slow response, reduce rate
        return RATE_LIMITS[api_name]['requests_per_minute'] * 0.8
    elif response_time < 0.5:
        # Fast response, can increase rate
        return RATE_LIMITS[api_name]['requests_per_minute'] * 1.2
    else:
        return RATE_LIMITS[api_name]['requests_per_minute']
```

### Connection Pooling

```python
# HTTP connection pooling for external APIs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_optimized_session():
    """Create optimized HTTP session"""
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # HTTP adapter with connection pooling
    adapter = HTTPAdapter(
        pool_connections=20,
        pool_maxsize=20,
        max_retries=retry_strategy
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
```

## 🔄 Data Processing Optimization

### Parallel Processing

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Async processing for I/O bound operations
async def process_leads_async(leads):
    """Process leads asynchronously"""
    async with aiohttp.ClientSession() as session:
        tasks = [enrich_lead_async(session, lead) for lead in leads]
        return await asyncio.gather(*tasks)

# Thread pool for I/O bound operations
def process_with_threads(leads, max_workers=10):
    """Process leads with thread pool"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_lead, lead) for lead in leads]
        return [future.result() for future in futures]

# Process pool for CPU bound operations
def process_with_processes(leads, max_workers=4):
    """Process leads with process pool"""
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(cpu_intensive_task, lead) for lead in leads]
        return [future.result() for future in futures]
```

### Data Streaming

```python
# Stream processing for large datasets
def stream_process_leads(batch_size=100):
    """Stream process leads to avoid memory issues"""
    offset = 0
    
    while True:
        # Get batch of leads
        leads = get_leads_batch(offset, batch_size)
        
        if not leads:
            break
        
        # Process batch
        for lead in leads:
            yield process_lead(lead)
        
        offset += batch_size
        
        # Memory cleanup
        gc.collect()
```

## 📊 Monitoring and Profiling

### Performance Monitoring

```python
import time
import psutil
from functools import wraps

def performance_monitor(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        # Log performance metrics
        logger.info(f"{func.__name__}: {execution_time:.2f}s, {memory_used/1024/1024:.2f}MB")
        
        return result
    return wrapper

# System resource monitoring
def monitor_system_resources():
    """Monitor system resources"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'network_io': psutil.net_io_counters(),
        'process_count': len(psutil.pids())
    }
```

### Database Query Optimization

```python
# Query optimization techniques
def optimize_database_queries():
    """Optimize database queries"""
    
    # Use prepared statements
    conn.execute("PRAGMA optimize")
    
    # Analyze query performance
    conn.execute("EXPLAIN QUERY PLAN SELECT * FROM leads WHERE email = ?")
    
    # Update statistics
    conn.execute("ANALYZE")

# Efficient bulk operations
def bulk_insert_leads(leads):
    """Efficient bulk insert"""
    conn.executemany(
        "INSERT OR REPLACE INTO leads (id, name, email, company) VALUES (?, ?, ?, ?)",
        [(lead['id'], lead['name'], lead['email'], lead['company']) for lead in leads]
    )
```

## 🎛️ Configuration Tuning

### Environment-Specific Settings

```env
# Production High-Performance Settings
BATCH_SIZE=100
CONCURRENT_LIMIT=20
RATE_LIMIT_DELAY=0.5
EXECUTION_TIMEOUT=600
LEAD_DATABASE_MAX_CONNECTIONS=50
LEAD_DATABASE_CACHE_SIZE=-256000

# Development Settings
BATCH_SIZE=10
CONCURRENT_LIMIT=3
RATE_LIMIT_DELAY=2
EXECUTION_TIMEOUT=300
LEAD_DATABASE_MAX_CONNECTIONS=10
LEAD_DATABASE_CACHE_SIZE=-32000

# Memory-Constrained Settings
BATCH_SIZE=5
CONCURRENT_LIMIT=2
RATE_LIMIT_DELAY=3
EXECUTION_TIMEOUT=180
LEAD_DATABASE_MAX_CONNECTIONS=5
LEAD_DATABASE_CACHE_SIZE=-16000
```

### Adaptive Configuration

```python
def get_optimal_config():
    """Get optimal configuration based on system resources"""
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()
    
    if memory_gb >= 8 and cpu_count >= 4:
        return {
            'batch_size': 100,
            'concurrent_limit': min(cpu_count * 2, 20),
            'cache_size': -256000,
            'max_connections': 50
        }
    elif memory_gb >= 4 and cpu_count >= 2:
        return {
            'batch_size': 50,
            'concurrent_limit': min(cpu_count * 2, 10),
            'cache_size': -128000,
            'max_connections': 25
        }
    else:
        return {
            'batch_size': 20,
            'concurrent_limit': 3,
            'cache_size': -64000,
            'max_connections': 10
        }
```

## 🚨 Performance Troubleshooting

### Common Performance Issues

#### Slow Database Queries
```bash
# Identify slow queries
sqlite3 data/leads_cache.db "PRAGMA compile_options;"
sqlite3 data/leads_cache.db ".timer on" ".explain on"

# Check database integrity
sqlite3 data/leads_cache.db "PRAGMA integrity_check;"
```

#### Memory Leaks
```python
# Memory leak detection
import tracemalloc

tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

#### High CPU Usage
```bash
# Profile CPU usage
python -m cProfile -o profile_output.prof your_script.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile_output.prof'); p.sort_stats('cumulative').print_stats(20)"
```

### Performance Benchmarking

```python
def benchmark_system():
    """Benchmark system performance"""
    import time
    
    # Database performance
    start = time.time()
    conn.execute("SELECT COUNT(*) FROM leads")
    db_time = time.time() - start
    
    # Data cleaning performance
    start = time.time()
    cleaner.clean_and_validate(sample_data, sample_context)
    cleaning_time = time.time() - start
    
    # API performance
    start = time.time()
    # Make API call
    api_time = time.time() - start
    
    return {
        'database_query_time': db_time,
        'data_cleaning_time': cleaning_time,
        'api_response_time': api_time
    }
```

## 📈 Scaling Strategies

### Horizontal Scaling
- Use multiple EC2 instances with load balancing
- Implement distributed task queues (Redis/Celery)
- Use shared database (PostgreSQL/MySQL)
- Implement caching layer (Redis/Memcached)

### Vertical Scaling
- Increase EC2 instance size (CPU/Memory)
- Optimize database configuration
- Increase connection pool sizes
- Use SSD storage for better I/O

### Auto-Scaling
```python
def auto_scale_decision():
    """Determine if auto-scaling is needed"""
    metrics = monitor_system_resources()
    
    if metrics['cpu_percent'] > 80 or metrics['memory_percent'] > 85:
        return 'scale_up'
    elif metrics['cpu_percent'] < 20 and metrics['memory_percent'] < 30:
        return 'scale_down'
    else:
        return 'maintain'
```

## 🎯 Best Practices

1. **Monitor Continuously**: Use the monitoring dashboard to track performance
2. **Profile Regularly**: Identify bottlenecks before they become problems
3. **Test Under Load**: Simulate high-load conditions during testing
4. **Optimize Incrementally**: Make small, measurable improvements
5. **Cache Intelligently**: Cache frequently accessed data
6. **Batch Operations**: Process data in optimal batch sizes
7. **Use Async When Possible**: For I/O bound operations
8. **Monitor Resource Usage**: Keep track of CPU, memory, and disk usage
9. **Plan for Growth**: Design for 10x current load
10. **Document Changes**: Keep track of performance optimizations

## 📊 Performance Metrics Dashboard

Access real-time performance metrics:
```bash
python monitoring_dashboard.py
# Open http://localhost:8080/performance
```

Key metrics to monitor:
- Lead processing rate (leads/hour)
- API response times
- Database query performance
- Memory usage patterns
- Error rates and retry counts
- System resource utilization

---

*For specific performance issues, check the troubleshooting guide or contact the development team.*