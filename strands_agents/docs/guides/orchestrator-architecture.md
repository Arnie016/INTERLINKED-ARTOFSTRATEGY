# Orchestrator Architecture

## Overview

The orchestrator implementation has been streamlined to **2 files** instead of 3, eliminating redundancy while providing clear separation between local and production deployments.

## File Structure

### 1. `orchestrator_agent.py` - Simple Local Deployment
**Use Case:** Local testing, simple FastAPI servers, non-AgentCore environments

**Key Features:**
- ✅ Zero AgentCore dependencies
- ✅ Simple stateless operation
- ✅ Fast startup for testing
- ✅ No memory/session management overhead

**Functions:**
- `create_orchestrator_agent()` - Creates basic Strands Agent
- `process_query()` - Simple query processing helper
- `ORCHESTRATOR_SYSTEM_PROMPT` - Agent routing instructions

**Example:**
```python
from strands_agents.src.agents import create_orchestrator_agent

# Create simple orchestrator for local testing
orchestrator = create_orchestrator_agent(user_role="user")

# Process query (no memory, stateless)
response = orchestrator("Who are the key people in Engineering?")
print(response)
```

---

### 2. `orchestrator_agent_agentcore.py` - Production AgentCore Deployment
**Use Case:** Production deployments with AWS Bedrock AgentCore Runtime and Memory

**Key Features:**
- ✅ AgentCore Memory integration (STM + LTM)
- ✅ AgentCore Runtime deployment
- ✅ Session management via hooks
- ✅ Conversation history preservation
- ✅ Automatic scaling and managed infrastructure

**Components:**

#### Enums
- `AgentType` - Available specialized agents (GRAPH, ANALYZER, EXTRACTOR, ADMIN)
- `IntentConfidence` - Intent detection confidence levels (HIGH, MEDIUM, LOW)

#### Classes
- `AgentCoreMemoryHook` - Strands hook for automatic memory integration
  - `on_agent_initialized()` - Loads previous conversation on startup
  - `on_message_added()` - Saves each message to AgentCore Memory

#### Functions
- `create_orchestrator_with_agentcore()` - Creates Agent with Memory hooks
- `create_agentcore_app()` - Creates BedrockAgentCoreApp for Runtime deployment

**Example - Local with Memory:**
```python
from bedrock_agentcore.memory import MemoryClient
from strands_agents.src.agents import create_orchestrator_with_agentcore

# Create memory client
memory_client = MemoryClient(region_name='us-west-2')
memory_id = "your-memory-id"  # From setup_agentcore_memory.py

# Create orchestrator with memory
orchestrator = create_orchestrator_with_agentcore(
    user_role="user",
    memory_client=memory_client,
    memory_id=memory_id,
    session_id="user-session-123"
)

# Process queries - memory is automatic
response = orchestrator("Who are the key people?")
print(response)

# Follow-up question uses conversation history
response = orchestrator("What processes do they own?")
print(response)
```

**Example - AgentCore Runtime Deployment:**
```python
# examples/agentcore_deployment_handler.py
from strands_agents.src.agents import create_agentcore_app
import os

# Environment-based configuration
USER_ROLE = os.getenv("USER_ROLE", "user")
MEMORY_ID = os.getenv("MEMORY_ID")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

# Create app
app = create_agentcore_app(
    user_role=USER_ROLE,
    memory_id=MEMORY_ID
)

# Deploy
if __name__ == "__main__":
    app.run()
```

---

## Removed File

### ❌ `orchestration_agentcore.py` (DELETED)
**Reason for Removal:** 
- The `AgentCoreOrchestrator` wrapper class added no value
- All functionality is better handled by:
  - Strands Agent's built-in capabilities
  - AgentCore Memory hooks
  - AgentCore Runtime session management
- Enums moved to `orchestrator_agent_agentcore.py`

**What it contained:**
- `AgentCoreOrchestrator` class - Unnecessary wrapper around Agent
- `create_agentcore_orchestrator()` - Redundant with `create_orchestrator_with_agentcore()`
- Enums - Now in `orchestrator_agent_agentcore.py`

---

## When to Use Which File

### Use `orchestrator_agent.py` when:
- 🧪 Local testing and development
- 🚀 Quick prototyping
- 📦 Simple FastAPI proxy deployments
- ❌ No need for conversation memory
- ❌ No need for session management
- ❌ Running outside AWS

### Use `orchestrator_agent_agentcore.py` when:
- ☁️ Deploying to AWS Bedrock AgentCore Runtime
- 💾 Need conversation history (Short-Term Memory)
- 🧠 Need intelligent fact/preference extraction (Long-Term Memory)
- 📊 Need session isolation for multi-user scenarios
- ⚡ Need automatic scaling
- 🔒 Need managed infrastructure and security

---

## Key Differences Summary

| Feature | orchestrator_agent.py | orchestrator_agent_agentcore.py |
|---------|----------------------|--------------------------------|
| **Dependencies** | Strands only | Strands + bedrock_agentcore |
| **Memory** | None | STM + LTM via AgentCore |
| **Sessions** | Stateless | Session-aware |
| **Deployment** | Any Python env | AgentCore Runtime |
| **Scaling** | Manual | Automatic |
| **Context** | None | Automatic via hooks |
| **Use Case** | Testing/Local | Production |
| **Complexity** | Low | Medium |
| **Setup Time** | Instant | ~5-10 min (memory setup) |

---

## Migration Path

### From Simple → AgentCore (Production)

1. **Set up AgentCore Memory** (one-time):
   ```bash
   python examples/setup_agentcore_memory.py
   # Save the returned MEMORY_ID
   ```

2. **Update code**:
   ```python
   # OLD - Simple
   from strands_agents.src.agents import create_orchestrator_agent
   orchestrator = create_orchestrator_agent()
   
   # NEW - AgentCore
   from strands_agents.src.agents import create_orchestrator_with_agentcore
   from bedrock_agentcore.memory import MemoryClient
   
   memory_client = MemoryClient(region_name='us-west-2')
   orchestrator = create_orchestrator_with_agentcore(
       memory_client=memory_client,
       memory_id=os.getenv('MEMORY_ID'),
       session_id="user-123"
   )
   ```

3. **Deploy to Runtime**:
   ```bash
   agentcore configure --entrypoint examples/agentcore_deployment_handler.py
   export MEMORY_ID=<your-memory-id>
   agentcore launch
   ```

---

## Architecture Principles

### Why This Structure?

1. **Separation of Concerns**
   - Local development doesn't need production complexity
   - Production deployments leverage managed AWS services
   
2. **AWS Best Practices**
   - Use managed services instead of custom implementations
   - Leverage AgentCore's built-in primitives
   - Minimize custom orchestration code

3. **Developer Experience**
   - Simple file for simple needs
   - Clear upgrade path to production
   - No unnecessary abstraction layers

4. **Cost Optimization**
   - Local testing is free (no AgentCore calls)
   - Production uses efficient managed services
   - Pay only for what you use

---

## Related Documentation

- [AgentCore Deployment Guide](./agentcore-deployment.md)
- [AgentCore Memory Setup](../../examples/setup_agentcore_memory.py)
- [Deployment Handler](../../examples/agentcore_deployment_handler.py)
- [AWS Setup Guide](./aws-setup.md)

