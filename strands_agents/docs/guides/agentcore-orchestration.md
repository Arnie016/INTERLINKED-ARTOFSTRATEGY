# AgentCore Orchestration Guide

## Overview

This guide explains how the Orchestrator Agent uses AWS Bedrock AgentCore's native primitives for production-ready multi-agent coordination, context management, and deployment.

## Architecture

Instead of implementing custom orchestration logic, our system leverages AgentCore's built-in services:

- **AgentCore Memory**: Manages conversation history and context
- **AgentCore Runtime**: Handles deployment, scaling, and session management  
- **Strands Agents Hooks**: Integrates Memory with the agent framework
- **Claude 3.5 Sonnet**: Performs intelligent routing via system prompts

## Key Components

### 1. AgentCore Memory Integration

AgentCore Memory provides two types of memory:

#### Short-Term Memory (STM)
- **Purpose**: Session-based conversation history
- **Retention**: Configurable (e.g., 30 days)
- **Use Case**: Maintaining context within a single conversation
- **Retrieval**: Instant
- **Features**: Stores raw message history

#### Long-Term Memory (LTM)
- **Purpose**: Cross-session preferences and facts
- **Retention**: Configurable (e.g., 180 days)
- **Use Case**: Remembering user preferences across sessions
- **Retrieval**: 5-10 second extraction delay
- **Features**: Automatically extracts preferences and semantic facts

### 2. Memory Hook Implementation

The `AgentCoreMemoryHook` automatically manages conversation state:

```python
from strands_agents.src.agents.orchestrator_agent_agentcore import (
    create_orchestrator_with_agentcore
)
from bedrock_agentcore.memory import MemoryClient

# Initialize memory client
memory_client = MemoryClient(region_name='us-west-2')
memory_id = "your-memory-id-here"

# Create orchestrator with memory
orchestrator = create_orchestrator_with_agentcore(
    user_role="user",
    memory_client=memory_client,
    memory_id=memory_id,
    session_id="user-session-123"
)

# Process queries - context is automatically managed
response = orchestrator("Who are the key people in Engineering?")
print(response)
```

### 3. Intent Detection via System Prompt

Instead of custom keyword matching, Claude 3.5 Sonnet handles routing naturally:

```python
ORCHESTRATOR_SYSTEM_PROMPT = """
You are the Orchestrator Agent...

**Available Specialized Agents:**

1. **Graph Agent** (graph_agent)
   - Use for: Queries about people, processes, departments, systems
   - Examples: "Who reports to Alice?", "What processes does Engineering own?"

2. **Analyzer Agent** (analyzer_agent)
   - Use for: Advanced analytics and pattern detection
   - Examples: "Who are the key influencers?", "Find organizational bottlenecks"

3. **Extractor Agent** (extractor_agent)
   - Use for: Creating new nodes and relationships
   - Examples: "Add a new employee", "Create a relationship between X and Y"

4. **Admin Agent** (admin_agent)
   - Use for: Database maintenance and administrative tasks
   - Examples: "Reindex Person nodes", "Clean up orphaned data"

**Routing Guidelines:**
- For simple information retrieval → use **graph_agent**
- For analytical questions requiring metrics → use **analyzer_agent**
- For creating or modifying data → use **extractor_agent**
- For administrative operations → use **admin_agent** (check permissions first)
"""
```

## Deployment

### Step 1: Create Memory Resources

Run the setup script to create STM and LTM resources:

```bash
python strands_agents/examples/setup_agentcore_memory.py
```

This creates two memory resources and outputs their IDs:
- **STM ID**: For session-based memory
- **LTM ID**: For cross-session memory

### Step 2: Configure Deployment

```bash
cd strands_agents
agentcore configure --entrypoint examples/agentcore_deployment_handler.py
```

### Step 3: Set Environment Variables

```bash
# Choose STM or LTM
export MEMORY_ID=<your-memory-id>

# AWS Configuration
export AWS_REGION=us-west-2

# Neo4j Configuration (for graph operations)
export NEO4J_URI=<your-neo4j-uri>
export NEO4J_USERNAME=<username>
export NEO4J_PASSWORD=<password>

# Optional: User role (user, extractor, admin)
export USER_ROLE=user
```

### Step 4: Deploy

```bash
agentcore launch
```

AgentCore CLI handles:
- Container image creation
- IAM role setup
- Deployment to secure runtime
- Automatic scaling configuration

### Step 5: Test

```bash
# First interaction
agentcore invoke '{"prompt": "My name is Alice"}' --session-id alice-session

# Second interaction - agent remembers
agentcore invoke '{"prompt": "What is my name?"}' --session-id alice-session

# Cross-session memory (with LTM only)
agentcore invoke '{"prompt": "What are my preferences?"}' --session-id different-session
```

## Local Development

For local testing without deployment:

```python
from strands_agents.src.agents.orchestrator_agent import create_orchestrator_agent

# Create simple orchestrator (no AgentCore dependencies)
orchestrator = create_orchestrator_agent(user_role="user")

# Process queries locally
response = orchestrator("Find all engineers")
print(response)
```

## Session Management

AgentCore Runtime automatically provides session management:

```python
@app.entrypoint
def invoke(payload, context):
    # Session ID is automatically provided by AgentCore
    session_id = context.session_id
    
    # Agent state is isolated per session
    orchestrator.state.set("session_id", session_id)
    
    # Process query
    response = orchestrator(payload.get("prompt"))
    return response
```

## Error Handling

The orchestrator includes comprehensive error handling:

```python
try:
    response = orchestrator(query)
except Exception as e:
    # AgentCore handles logging and monitoring
    logger.error(f"Error processing query: {e}", exc_info=True)
    
    # User-friendly error messages
    if "authentication" in str(e).lower():
        return "Permission error: Contact your administrator"
    elif "timeout" in str(e).lower():
        return "Operation timed out: Try a simpler query"
    else:
        return f"An error occurred: {str(e)}"
```

## Performance Optimization

### Memory Configuration

```python
# Configure retention policies
from bedrock_agentcore.memory import RetentionPolicy

retention_policies = {
    "user_profiles": RetentionPolicy(days=365, priority="high"),
    "conversations": RetentionPolicy(days=90, priority="medium"),
    "temporary_data": RetentionPolicy(days=7, priority="low")
}
```

### Caching

AgentCore Memory automatically caches frequently accessed memories for optimal performance.

## Monitoring

AgentCore provides built-in observability:

- **CloudWatch Logs**: All operations logged with structured context
- **CloudWatch Metrics**: Performance metrics automatically collected
- **X-Ray Tracing**: End-to-end request tracing
- **Memory Analytics**: Usage statistics and access patterns

Access monitoring through AWS Console or CLI:

```bash
# View logs
agentcore logs --tail

# View metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/AgentCore \
  --metric-name Invocations \
  --dimensions Name=AgentName,Value=orchestrator
```

## Best Practices

### 1. Choose the Right Memory Type

- **STM**: For testing, development, and sessions that don't need persistence
- **LTM**: For production, user preferences, and cross-session context

### 2. Session ID Strategy

- Use stable session IDs for consistent user experiences
- Include user ID in session ID for multi-tenant scenarios
- Example: `user-{user_id}-session-{timestamp}`

### 3. Role-Based Access Control

```python
# Configure different orchestrators for different roles
user_orchestrator = create_orchestrator_with_agentcore(user_role="user")
admin_orchestrator = create_orchestrator_with_agentcore(user_role="admin")
```

### 4. Error Recovery

- Let AgentCore handle retries for transient failures
- Implement graceful degradation when specialized agents are unavailable
- Provide clear user feedback on errors

### 5. Security

- Never log credentials or sensitive data
- Use AgentCore Identity for authentication
- Leverage encryption at rest and in transit
- Implement proper IAM policies

## Troubleshooting

### Memory Not Persisting

**Problem**: Conversations aren't being saved  
**Solution**: Verify `MEMORY_ID` is set and Memory resource exists

```bash
# List memory resources
aws bedrock-agent-runtime list-memories --region us-west-2
```

### Session Isolation Issues

**Problem**: Sessions are mixing context  
**Solution**: Ensure unique session IDs per conversation

```python
# Bad: Reusing session IDs
session_id = "default"

# Good: Unique session per user/conversation
session_id = f"user-{user_id}-{conversation_id}"
```

### High Latency

**Problem**: Slow response times  
**Solution**: 
- Use STM instead of LTM for faster retrieval
- Reduce number of conversation turns loaded (`k` parameter)
- Implement caching for frequently accessed data

### Deployment Failures

**Problem**: `agentcore launch` fails  
**Solution**:
- Verify AWS credentials are configured
- Check IAM permissions for AgentCore
- Ensure all environment variables are set
- Review CloudFormation stack errors

## Additional Resources

- [AWS Bedrock AgentCore Documentation](https://aws.github.io/bedrock-agentcore-starter-toolkit/)
- [Strands Agents Documentation](https://strandsagents.com/latest/documentation/)
- [AgentCore Memory API Reference](https://aws.github.io/bedrock-agentcore-starter-toolkit/api-reference/memory.md)
- [Deployment Guide](aws-setup.md)
- [Performance Optimization](performance-optimization.md)

