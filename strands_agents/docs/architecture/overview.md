# Strands Agents Architecture Overview

A multi-agent system built with AWS Bedrock and Strands Agents SDK for analyzing organizational graph data stored in Neo4j.

## Architecture Pattern

This project implements the **"Agents as Tools"** pattern, where specialized agents are wrapped as callable functions that can be orchestrated by a main agent.

### Agent Hierarchy

```
OrchestratorAgent (Main Entry Point)
├── GraphAgent (Read-only queries and search)
├── AnalyzerAgent (Advanced analytics and insights)
├── ExtractorAgent (Data ingestion and writes)
└── AdminAgent (Privileged admin operations)
```

## Agent Descriptions

### 1. OrchestratorAgent
- **Purpose**: Main entry point that routes user queries to specialized agents
- **Capabilities**: Intent detection, multi-agent coordination, response integration
- **Model**: Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20241022-v2:0)
- **Temperature**: 0.5 (moderate reasoning)

### 2. GraphAgent
- **Purpose**: Read-only graph queries and exploration
- **Capabilities**: 
  - Search nodes by text query
  - Find related nodes and relationships
  - Get graph snapshots for visualization
  - Explain paths between entities
- **Model**: Claude 3.5 Sonnet
- **Temperature**: 0.3 (factual responses)
- **Access**: Read-only, available to all users

### 3. AnalyzerAgent
- **Purpose**: Advanced analytics and pattern detection
- **Capabilities**:
  - Centrality analysis (PageRank, betweenness, etc.)
  - Community detection (Louvain, label propagation)
  - Graph statistics and metrics
  - Bottleneck identification
- **Model**: Claude 3.5 Sonnet
- **Temperature**: 0.2 (analytical precision)
- **Access**: Read-only, available to all users

### 4. ExtractorAgent
- **Purpose**: Data ingestion and graph construction
- **Capabilities**:
  - Create nodes (Person, Process, Department, System)
  - Create relationships
  - Bulk data ingestion
  - Schema validation
- **Model**: Claude 3.5 Sonnet
- **Temperature**: 0.1 (precise operations)
- **Access**: Write operations, requires 'extractor' or 'admin' role

### 5. AdminAgent
- **Purpose**: Database administration and maintenance
- **Capabilities**:
  - Reindexing operations
  - Label migrations
  - Orphan node cleanup
  - Schema management
- **Model**: Claude 3.5 Sonnet
- **Temperature**: 0.0 (maximum precision)
- **Access**: Privileged operations, requires 'admin' role

## Graph Schema

### Node Types
- **Person**: Employees with properties (name, role, department, skills)
- **Process**: Business processes (name, description, owner)
- **Department**: Organizational units (name, description)
- **System**: Applications and tools (name, description, type)

### Relationship Types
- **PERFORMS**: Person → Process
- **OWNS**: Person → Process
- **REPORTS_TO**: Person → Person
- **COLLABORATES_WITH**: Person ↔ Person
- **DEPENDS_ON**: Process → Process
- **USES**: Person → System
- **SUPPORTS**: System → Process

## Key Design Decisions

### 1. Temperature Tuning
Different agents use different temperatures based on their purpose:
- **Admin (0.0)**: Maximum precision for critical operations
- **Extractor (0.1)**: High precision for data operations
- **Analyzer (0.2)**: Analytical accuracy
- **Graph (0.3)**: Factual but conversational
- **Orchestrator (0.5)**: Balanced reasoning for routing

### 2. System Prompts
Each agent has a focused system prompt that:
- Clearly defines responsibilities
- Lists available capabilities
- Specifies safety constraints
- Provides response guidelines
- Includes usage examples

### 3. Role-Based Access
The orchestrator enforces role-based access:
- **user**: GraphAgent + AnalyzerAgent (read-only)
- **extractor**: + ExtractorAgent (write operations)
- **admin**: + AdminAgent (privileged operations)

### 4. Error Handling
All agent tools include:
- Try-catch blocks
- Informative error messages
- Graceful degradation
- User-friendly error formatting

## Security Considerations

1. **Authentication**: Verify user identity before agent invocation
2. **Authorization**: Role-based access control enforced by orchestrator
3. **Input Validation**: All tools validate inputs against schemas
4. **Audit Logging**: All operations logged with user context
5. **Rate Limiting**: Consider implementing rate limits for production
6. **Dry-Run Mode**: Admin operations require dry-run first

## Related Documentation

- [Integration Guide](integration.md) - How to integrate shared utilities
- [Implementation Details](../implementation/) - Detailed implementation summaries
- [Setup Guides](../guides/) - Getting started documentation


