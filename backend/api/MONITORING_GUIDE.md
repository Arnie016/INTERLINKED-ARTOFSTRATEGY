# FastAPI Proxy Monitoring & Observability Guide

Comprehensive guide for monitoring, logging, and observability features in the FastAPI proxy.

## Table of Contents

- [Overview](#overview)
- [Structured Logging](#structured-logging)
- [Request Tracing](#request-tracing)
- [Performance Metrics](#performance-metrics)
- [Health Monitoring](#health-monitoring)
- [Error Handling](#error-handling)
- [Circuit Breaker](#circuit-breaker)
- [Production Deployment](#production-deployment)

## Overview

The FastAPI proxy includes comprehensive monitoring and observability features:

- **Structured JSON Logging** - Machine-readable logs with correlation IDs
- **Request Tracing** - Track requests across the system with unique IDs
- **Performance Metrics** - Response times, error rates, throughput
- **Health Monitoring** - System health checks and component status
- **Circuit Breaker** - Automatic failure protection and recovery
- **Error Handling** - Graceful error responses with proper status codes

## Structured Logging

### Configuration

Configure logging via environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR)
export PROXY_LOG_LEVEL=INFO

# Log format (json for production, text for development)
export PROXY_LOG_FORMAT=json
```

### Log Format

Logs are output in JSON format for easy parsing by log aggregation tools:

```json
{
  "timestamp": "2025-10-17T10:30:00.123Z",
  "level": "INFO",
  "logger": "proxy.router",
  "message": "Processing chat request",
  "request_id": "req-abc123",
  "session_id": "sess-xyz789",
  "method": "POST",
  "path": "/api/chat",
  "execution_time_ms": 245.3
}
```

### Correlation IDs

Every request is assigned a unique request ID for tracing:

- **Request ID**: Unique identifier for each HTTP request
- **Session ID**: Identifier for user sessions across multiple requests
- **Automatic propagation**: IDs are included in all log entries

### Log Levels

**DEBUG**: Detailed information for debugging
- Request/response payloads (sanitized)
- Internal state changes
- Cache operations

**INFO**: Normal operational events
- Request start/completion
- Successful operations
- Configuration changes

**WARNING**: Potentially problematic situations
- Validation failures
- Retry attempts
- Degraded performance

**ERROR**: Error conditions
- Request failures
- Exception traces
- System errors

## Request Tracing

### Headers

The proxy uses headers for request correlation:

**Request Headers:**
- `X-Request-ID` - Optional request ID (generated if not provided)
- `X-Session-ID` - Optional session ID for correlation

**Response Headers:**
- `X-Request-ID` - Request correlation ID
- `X-Process-Time` - Request processing time in milliseconds

### Example

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "X-Request-ID: my-request-123" \
  -H "X-Session-ID: my-session-456" \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "agent_type": "graph"}'
```

Response includes:
```
X-Request-ID: my-request-123
X-Process-Time: 245.30ms
```

## Performance Metrics

### Metrics Endpoint

Get current performance metrics:

```bash
GET /api/proxy/metrics
```

**Response:**
```json
{
  "request_count": 1000,
  "error_count": 5,
  "error_rate": 0.005,
  "avg_response_time_ms": 245.3,
  "p50_response_time_ms": 210.0,
  "p95_response_time_ms": 450.0,
  "p99_response_time_ms": 850.0,
  "errors_by_type": {
    "AgentTimeoutError": 3,
    "ValidationError": 2
  },
  "circuit_breaker_state": {
    "state": "CLOSED",
    "failure_count": 0
  },
  "timestamp": "2025-10-17T10:30:00.000Z"
}
```

### Metrics Collected

**Request Metrics:**
- Total request count
- Error count and rate
- Requests per second (calculated from time series)

**Response Time Metrics:**
- Average response time
- 50th percentile (median)
- 95th percentile
- 99th percentile

**Error Metrics:**
- Errors by type
- Error rate percentage
- Most common error types

### Reset Metrics

Reset metrics counters (useful for testing):

```bash
POST /api/proxy/metrics/reset
```

## Health Monitoring

### Health Check Endpoint

Check system health and component status:

```bash
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "components": {
    "session_manager": {
      "status": "operational",
      "backend": "file",
      "active_sessions": 42
    },
    "strands_agent": {
      "status": "ready",
      "cached_agents": 15,
      "use_agentcore": true
    }
  },
  "timestamp": "2025-10-17T10:30:00.000Z"
}
```

### Health Status Values

- **healthy**: All components operational
- **degraded**: Some components experiencing issues but system functional
- **unhealthy**: Critical components down, system not operational

### Component Checks

The health endpoint checks:
- **Session Manager**: Storage backend availability
- **Strands Agent**: Agent system readiness
- **Neo4j**: Database connectivity (if direct access)
- **AgentCore Memory**: Memory service status

## Error Handling

### Error Response Format

All errors return consistent JSON format:

```json
{
  "success": false,
  "error": "AGENT_TIMEOUT",
  "message": "The request took too long to process",
  "path": "/api/chat",
  "detail": {
    "timeout_seconds": 60
  },
  "timestamp": "2025-10-17T10:30:00.000Z"
}
```

### Error Types

**Client Errors (4xx):**
- `VALIDATION_ERROR` (400) - Invalid input
- `AUTHENTICATION_ERROR` (401) - Auth failure
- `NOT_FOUND` (404) - Resource not found

**Server Errors (5xx):**
- `TIMEOUT` (504) - Request timeout
- `SERVICE_UNAVAILABLE` (503) - Service down
- `AGENT_ERROR` (500) - Agent processing error
- `INTERNAL_ERROR` (500) - Unexpected error

### Error Details

Enable detailed error information for development:

```bash
export PROXY_ENABLE_ERROR_DETAILS=true
```

This includes:
- Exception type and message
- Stack traces
- Internal state information

⚠️ **Warning**: Never enable in production (security risk)

## Circuit Breaker

### Configuration

Enable circuit breaker for resilience:

```bash
export PROXY_ENABLE_CIRCUIT_BREAKER=true
export PROXY_CIRCUIT_BREAKER_THRESHOLD=5
export PROXY_CIRCUIT_BREAKER_TIMEOUT=60
```

### Circuit States

**CLOSED** (Normal Operation):
- Requests flow through normally
- Failures are tracked

**OPEN** (Circuit Tripped):
- Requests immediately rejected
- System given time to recover
- Returns 503 Service Unavailable

**HALF_OPEN** (Testing Recovery):
- Limited requests allowed through
- Success → back to CLOSED
- Failure → back to OPEN

### Circuit Breaker Metrics

Check circuit breaker state:

```bash
GET /api/proxy/metrics
```

Response includes:
```json
{
  "circuit_breaker_state": {
    "state": "CLOSED",
    "failure_count": 2,
    "failure_threshold": 5,
    "time_until_half_open": 0
  }
}
```

### Behavior

1. **Failure Tracking**: Counts consecutive failures
2. **Threshold**: Opens after N failures (default: 5)
3. **Recovery**: Waits M seconds before testing (default: 60)
4. **Half-Open**: Tests with limited requests
5. **Recovery**: Closes after N successful requests (default: 3)

## Production Deployment

### Environment Variables

**Required:**
```bash
# Session backend (file for dev, s3 for prod)
export PROXY_SESSION_BACKEND=s3
export PROXY_SESSION_S3_BUCKET=interlinked-aos-sessions

# AWS configuration
export AWS_REGION=us-west-2

# AgentCore Memory (if using)
export PROXY_USE_AGENTCORE_MEMORY=true
export MEMORY_ID=mem-abc123

# Neo4j credentials (via Secrets Manager in prod)
export NEO4J_URI=bolt://neo4j.example.com:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=secure-password
```

**Recommended:**
```bash
# Logging
export PROXY_LOG_LEVEL=INFO
export PROXY_LOG_FORMAT=json

# Error handling
export PROXY_ENABLE_ERROR_DETAILS=false  # Never true in prod

# Resilience
export PROXY_ENABLE_CIRCUIT_BREAKER=true
export PROXY_CIRCUIT_BREAKER_THRESHOLD=5
export PROXY_CIRCUIT_BREAKER_TIMEOUT=60

# Performance
export PROXY_AGENT_TIMEOUT_SECONDS=60
```

### CloudWatch Integration

Logs are compatible with CloudWatch Logs Insights:

**Query Examples:**

```sql
-- Error rate by hour
fields @timestamp, level, message
| filter level = "ERROR"
| stats count() as errors by bin(1h)

-- Slow requests (>1s)
fields @timestamp, path, execution_time_ms
| filter execution_time_ms > 1000
| sort execution_time_ms desc

-- Requests by session
fields @timestamp, session_id, path
| stats count() by session_id
| sort count desc

-- Error types
fields @timestamp, error_type, error_message
| filter level = "ERROR"
| stats count() by error_type
```

### Monitoring Dashboards

**Key Metrics to Monitor:**

1. **Request Rate**
   - Requests per second
   - Trend over time
   - Spike detection

2. **Error Rate**
   - Percentage of failed requests
   - Alert threshold: > 5%
   - Errors by type

3. **Response Time**
   - P50, P95, P99 percentiles
   - Alert on P95 > 5s
   - Slow endpoint identification

4. **System Health**
   - Component availability
   - Circuit breaker trips
   - Session/agent cache size

5. **Business Metrics**
   - Active sessions
   - Agent invocations
   - Cache hit rate

### Alerting

**Critical Alerts:**
- Error rate > 10% for 5 minutes
- P95 response time > 10 seconds
- Circuit breaker opens
- Health check fails

**Warning Alerts:**
- Error rate > 5% for 10 minutes
- P95 response time > 5 seconds
- Cache size exceeds threshold
- Memory usage > 80%

### Example Alert Configuration

```yaml
# CloudWatch Alarm
ErrorRateAlarm:
  Threshold: 0.05  # 5%
  EvaluationPeriods: 2
  Period: 300  # 5 minutes
  Metric: error_rate
  
ResponseTimeAlarm:
  Threshold: 5000  # 5 seconds
  EvaluationPeriods: 3
  Period: 300
  Statistic: p95
```

## Debugging

### View Recent Errors

```bash
# Get recent logs
tail -f /var/log/proxy/app.log | jq 'select(.level == "ERROR")'

# Or with CloudWatch
aws logs tail /aws/proxy/production \
  --filter-pattern '{ $.level = "ERROR" }' \
  --follow
```

### Trace Specific Request

Use request ID to trace through logs:

```bash
# Find all logs for a request
grep "req-abc123" /var/log/proxy/app.log | jq .

# Or with CloudWatch
aws logs filter-log-events \
  --log-group-name /aws/proxy/production \
  --filter-pattern "req-abc123"
```

### Analyze Performance

```bash
# Get metrics
curl http://localhost:8000/api/proxy/metrics | jq .

# Check health
curl http://localhost:8000/api/health | jq .

# View configuration
curl http://localhost:8000/api/proxy/config | jq .
```

## Best Practices

1. **Always use JSON logging in production**
2. **Enable circuit breaker for resilience**
3. **Monitor P95/P99 response times, not just averages**
4. **Set up alerting on error rates and health checks**
5. **Use correlation IDs for troubleshooting**
6. **Review error types regularly for patterns**
7. **Test circuit breaker behavior before production**
8. **Configure appropriate timeout values**
9. **Monitor cache sizes and memory usage**
10. **Regular health check automated tests**

## Troubleshooting

### High Error Rate

1. Check error types: `GET /api/proxy/metrics`
2. Review recent errors in logs
3. Check agent system health
4. Verify Neo4j connectivity
5. Review timeout settings

### Slow Response Times

1. Check P95/P99 metrics
2. Identify slow endpoints
3. Review agent performance
4. Check session storage performance
5. Monitor database query times

### Circuit Breaker Tripping

1. Check failure threshold configuration
2. Review recent error spike
3. Verify external dependencies
4. Check system resources
5. Review recovery timeout setting

### Memory Issues

1. Check cache sizes
2. Review session cleanup
3. Monitor agent instance count
4. Check for memory leaks
5. Review resource limits

## Additional Resources

- [PROXY_IMPLEMENTATION.md](./PROXY_IMPLEMENTATION.md) - Architecture documentation
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - Testing documentation
- [FastAPI Middleware](https://fastapi.tiangolo.com/advanced/middleware/)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)

