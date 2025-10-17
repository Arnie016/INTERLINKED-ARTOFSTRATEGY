# FastAPI Proxy for Strands Agents

This module provides backward-compatible API endpoints that forward requests to the new Strands agent implementation while maintaining the existing frontend contract.

## Architecture

```
Frontend (existing) → FastAPI Proxy → Strands Orchestrator → Specialized Agents
                                     ↓
                               Session Management (File/S3)
                                     ↓
                               AgentCore Memory (Optional)
```

## Components

### Models (`models.py`)
- **ChatMessage**: Incoming frontend request format
- **ChatResponse**: Outgoing frontend response format
- **StrandsAgentRequest**: Internal Strands agent format
- **StrandsAgentResponse**: Internal Strands response format
- **ProxyConfig**: Configuration settings

### Session Management (`session.py`)
- **SessionManager**: Manages session IDs and creates Strands session managers
- Supports both file-based (dev) and S3-based (prod) storage
- Extracts session IDs from headers/cookies or generates new ones

### Agent Client (`client.py`)
- **StrandsAgentClient**: Wrapper for invoking Strands agents
- Handles agent creation, caching, and invocation
- Integrates with AgentCore Memory (optional)
- Provides error handling and performance metrics

### Transformers (`transformers.py`)
- **RequestTransformer**: Converts frontend requests to Strands format
- **ResponseTransformer**: Converts Strands responses to frontend format
- Validation and sanitization utilities

### Router (`router.py`)
- **POST /api/chat**: Main chat endpoint (backward compatible)
- **GET /api/health**: Health check endpoint
- **GET /api/proxy/config**: Configuration endpoint
- **POST /api/proxy/clear-cache**: Cache management endpoint

## Configuration

Configuration is loaded from environment variables with the `PROXY_` prefix:

```bash
# Session Management
PROXY_SESSION_BACKEND=file  # or 's3' for production
PROXY_SESSION_STORAGE_DIR=/path/to/sessions  # for file backend
PROXY_SESSION_S3_BUCKET=my-sessions-bucket  # for S3 backend
PROXY_SESSION_S3_PREFIX=interlinked-aos-dev/sessions/

# AgentCore Integration
PROXY_USE_AGENTCORE_MEMORY=true
MEMORY_ID=mem-abc123

# Feature Flags
PROXY_ENABLE_REQUEST_LOGGING=true
PROXY_ENABLE_ERROR_DETAILS=true  # dev mode
PROXY_ENABLE_PERFORMANCE_METRICS=true

# Timeouts & Limits
PROXY_AGENT_TIMEOUT_SECONDS=60

# AWS
AWS_REGION=us-west-2
```

## Usage

### Development (File-based sessions)

```bash
# Set environment variables
export PROXY_SESSION_BACKEND=file
export PROXY_USE_AGENTCORE_MEMORY=false
export AWS_REGION=us-west-2

# Run the server
python main_proxy.py
```

### Production (S3-based sessions with AgentCore Memory)

```bash
# Set environment variables
export PROXY_SESSION_BACKEND=s3
export PROXY_SESSION_S3_BUCKET=interlinked-aos-sessions-prod
export PROXY_USE_AGENTCORE_MEMORY=true
export MEMORY_ID=mem-prod-abc123
export AWS_REGION=us-west-2

# Run the server
python main_proxy.py
```

## API Endpoints

### POST /api/chat

Chat with the AI agent system.

**Request:**
```json
{
  "message": "Who are the key people in the organization?",
  "agent_type": "graph"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Found 15 people in the organization...",
  "agent_type": "graph",
  "timestamp": "2025-10-17T10:30:00Z",
  "session_id": "sess-abc123"
}
```

**Headers:**
- `X-Session-ID` (optional): Existing session ID
- Response sets `session_id` cookie for subsequent requests

### GET /api/health

Health check for all components.

**Response:**
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "components": {
    "session_manager": {
      "status": "operational",
      "backend": "file",
      "active_sessions": 5
    },
    "strands_agent": {
      "status": "ready",
      "cached_agents": 3,
      "use_agentcore": true
    }
  },
  "timestamp": "2025-10-17T10:30:00Z"
}
```

### GET /api/proxy/config

Get current proxy configuration (non-sensitive).

**Response:**
```json
{
  "session_backend": "file",
  "use_agentcore_memory": false,
  "aws_region": "us-west-2",
  "active_sessions": 5,
  "cached_agents": 3,
  "agent_timeout_seconds": 60
}
```

### POST /api/proxy/clear-cache

Clear cached sessions and agents.

**Query Parameters:**
- `session_id` (optional): Specific session to clear, or omit to clear all

**Response:**
```json
{
  "success": true,
  "message": "Cleared 2 sessions and 2 agents",
  "session_id": "sess-abc123",
  "sessions_cleared": 2,
  "agents_cleared": 2
}
```

## Session Management

### Session ID Flow

1. **First Request**: No session ID provided
   - Generate new UUID-based session ID
   - Create new session in storage
   - Set `session_id` cookie in response

2. **Subsequent Requests**: Session ID in cookie or header
   - Extract existing session ID
   - Load conversation history from storage
   - Maintain context across requests

3. **Session Storage**:
   - **File Backend**: Stored in `.sessions/` directory
   - **S3 Backend**: Stored in configured S3 bucket

### AgentCore Memory Integration

When `use_agentcore_memory=true`:

1. Conversations are stored in AgentCore Memory
2. Short-term memory (STM) for session context
3. Long-term memory (LTM) for cross-session facts
4. Automatic memory loading/saving via hooks

## Error Handling

The proxy handles errors gracefully and transforms them to frontend-compatible responses:

- **AgentTimeoutError**: Returns user-friendly timeout message
- **AgentConfigurationError**: Returns 503 Service Unavailable
- **AgentInvocationError**: Returns generic error message
- **Validation Errors**: Returns 400 Bad Request with details

All errors are logged with full context for debugging.

## Testing

### Unit Tests

```bash
# Test transformers
pytest tests/test_transformers.py

# Test session management
pytest tests/test_session.py

# Test agent client
pytest tests/test_client.py
```

### Integration Tests

```bash
# Test end-to-end flow
pytest tests/test_integration.py
```

### Manual Testing

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "agent_type": "orchestrator"}'

# Test with session ID
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: sess-test123" \
  -d '{"message": "Who are the key people?", "agent_type": "graph"}'

# Test health endpoint
curl http://localhost:8000/api/health
```

## Performance Considerations

- **Agent Caching**: Agents are cached per session to avoid recreation overhead
- **Session Caching**: Session managers are cached to reduce storage I/O
- **Connection Pooling**: Neo4j connections are pooled automatically
- **Timeout Management**: Configurable timeouts prevent runaway requests

## Security Considerations

- **Session Cookies**: HttpOnly, SameSite=Lax (set Secure=True in production)
- **Input Validation**: All inputs validated and sanitized
- **Error Messages**: Generic messages in production, detailed in development
- **Rate Limiting**: Configurable (disabled by default)

## Troubleshooting

### "Session manager not initialized"
- Ensure `initialize_session_manager()` is called during app startup
- Check `main_proxy.py` lifespan context manager

### "Agent client not initialized"
- Ensure `initialize_agent_client()` is called during app startup
- Check `main_proxy.py` lifespan context manager

### "Failed to create agent"
- Check Strands agents are installed: `pip list | grep strands`
- Verify `strands_agents/src` is in Python path
- Check agent import errors in logs

### S3 session backend errors
- Verify S3 bucket exists and is accessible
- Check AWS credentials and permissions
- Verify `PROXY_SESSION_S3_BUCKET` is set correctly

### AgentCore Memory errors
- Verify `MEMORY_ID` is set and valid
- Check AgentCore Memory resource is created
- Verify AWS credentials have Memory permissions

## Migration Guide

### From Old Backend to Proxy

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set environment variables**: Configure session backend and AgentCore
3. **Update frontend**: No changes needed (backward compatible)
4. **Start proxy**: `python main_proxy.py` instead of `python main.py`
5. **Test**: Verify frontend still works with new backend

### Gradual Rollout

You can run both backends simultaneously:

- Old backend: `python main.py` on port 8000
- New proxy: `python main_proxy.py` on port 8001
- Update frontend to use port 8001 when ready

## Future Enhancements

- [ ] Add rate limiting support
- [ ] Add request/response middleware for logging
- [ ] Add metrics collection (Prometheus/CloudWatch)
- [ ] Add distributed tracing (X-Ray)
- [ ] Add request replay for debugging
- [ ] Add A/B testing support for agent versions

