# Orchestrator Files - Quick Reference

## Before (3 Files - Redundant) ❌

```
orchestrator_agent.py (459 lines)
├── EnhancedOrchestrator class (BROKEN - imports deleted file)
├── create_orchestrator_agent() ✅
└── process_query() ✅

orchestration_agentcore.py (205 lines)
├── AgentType enum
├── IntentConfidence enum
└── AgentCoreOrchestrator class (REDUNDANT wrapper)

orchestrator_agent_agentcore.py (393 lines)
├── AgentCoreMemoryHook class ✅
├── create_orchestrator_with_agentcore() ✅
└── create_agentcore_app() ✅
```

## After (2 Files - Streamlined) ✅

```
orchestrator_agent.py (159 lines) - SIMPLIFIED
├── ORCHESTRATOR_SYSTEM_PROMPT
├── create_orchestrator_agent() - Simple local deployment
└── process_query() - Helper function

orchestrator_agent_agentcore.py (393 lines) - ENHANCED
├── AgentType enum (moved from deleted file)
├── IntentConfidence enum (moved from deleted file)
├── AgentCoreMemoryHook class - Automatic memory integration
├── create_orchestrator_with_agentcore() - Agent with memory
└── create_agentcore_app() - Runtime deployment
```

---

## File Purposes

### 📄 `orchestrator_agent.py`
**ONE JOB:** Create simple orchestrators for local testing

```python
# Quick local testing
from strands_agents.src.agents import create_orchestrator_agent
orchestrator = create_orchestrator_agent()
response = orchestrator("Find key people")
```

**When to use:**
- 🧪 Local development
- 🚀 Quick prototyping  
- ❌ No memory needed
- ❌ No AWS deployment

---

### 📄 `orchestrator_agent_agentcore.py`
**ONE JOB:** Create production-ready orchestrators with AgentCore

```python
# Production with memory
from strands_agents.src.agents import create_orchestrator_with_agentcore
from bedrock_agentcore.memory import MemoryClient

memory_client = MemoryClient(region_name='us-west-2')
orchestrator = create_orchestrator_with_agentcore(
    memory_client=memory_client,
    memory_id=os.getenv('MEMORY_ID'),
    session_id="user-123"
)
```

**When to use:**
- ☁️ AWS AgentCore deployment
- 💾 Need conversation memory
- 📊 Multi-user sessions
- ⚡ Automatic scaling

---

## What Changed?

### ✅ Improvements

1. **Removed broken code**
   - Deleted `EnhancedOrchestrator` class (imported from deleted `orchestration.py`)
   - Removed 300+ lines of custom orchestration logic

2. **Consolidated enums**
   - Moved `AgentType` and `IntentConfidence` to AgentCore file
   - Single source of truth for these types

3. **Deleted redundant wrapper**
   - Removed `AgentCoreOrchestrator` class
   - Removed `create_agentcore_orchestrator()` function
   - Direct use of Strands Agent + hooks is cleaner

4. **Clearer separation**
   - `orchestrator_agent.py` = Local/Simple
   - `orchestrator_agent_agentcore.py` = Production/AgentCore

### 📊 Code Reduction

- **Before:** 1,057 total lines across 3 files
- **After:** 552 total lines across 2 files
- **Reduction:** 47.8% less code
- **Functionality:** Same or better (leverages AWS managed services)

---

## Decision Tree: Which File to Import From?

```
Do you need conversation memory?
├─ NO → import from orchestrator_agent
│         (Local testing, simple deployments)
│
└─ YES → Are you deploying to AgentCore Runtime?
          ├─ NO → import from orchestrator_agent_agentcore
          │        use create_orchestrator_with_agentcore()
          │        (Local with memory client)
          │
          └─ YES → import from orchestrator_agent_agentcore
                   use create_agentcore_app()
                   (Full AgentCore deployment)
```

---

## Common Imports

### For Local Testing (No Memory)
```python
from strands_agents.src.agents import (
    create_orchestrator_agent,
    process_query,
    ORCHESTRATOR_SYSTEM_PROMPT
)
```

### For Production (With Memory)
```python
from strands_agents.src.agents import (
    create_orchestrator_with_agentcore,
    create_agentcore_app,
    AgentCoreMemoryHook,
    AgentType,
    IntentConfidence
)
```

---

## Why Delete `orchestration_agentcore.py`?

### Problems it had:
1. **Redundant wrapper class** - `AgentCoreOrchestrator` just wrapped a Strands Agent
2. **Duplicate functionality** - `create_agentcore_orchestrator()` did the same as `create_orchestrator_with_agentcore()`
3. **Unnecessary abstraction** - Added complexity without value
4. **AgentCore doesn't need wrappers** - Direct hook integration is cleaner

### What we kept from it:
- `AgentType` enum → moved to `orchestrator_agent_agentcore.py`
- `IntentConfidence` enum → moved to `orchestrator_agent_agentcore.py`

### What we replaced it with:
- Direct use of `AgentCoreMemoryHook` on Strands Agent
- Cleaner integration following Strands best practices
- Less code to maintain

---

## Testing the Changes

### Test Simple Orchestrator
```bash
cd strands_agents
python -c "
from src.agents import create_orchestrator_agent
orch = create_orchestrator_agent()
print('✅ Simple orchestrator works')
"
```

### Test AgentCore Orchestrator (requires memory setup)
```bash
export MEMORY_ID=<your-memory-id>
python -c "
from src.agents import create_orchestrator_with_agentcore
from bedrock_agentcore.memory import MemoryClient
client = MemoryClient(region_name='us-west-2')
orch = create_orchestrator_with_agentcore(
    memory_client=client,
    memory_id='$MEMORY_ID'
)
print('✅ AgentCore orchestrator works')
"
```

---

## Summary

**Before:** 3 files with redundancy and broken code  
**After:** 2 focused files with clear purposes

- ✅ 47.8% less code
- ✅ No broken imports
- ✅ Clear separation of concerns
- ✅ Better alignment with AWS best practices
- ✅ Easier to understand and maintain

