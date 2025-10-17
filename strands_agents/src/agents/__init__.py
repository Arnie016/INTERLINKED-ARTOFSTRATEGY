"""
Strands Agents for Organizational Graph Analysis.

This package implements a multi-agent system using the "Agents as Tools" pattern
for interacting with an organizational Neo4j graph database.

Agent Architecture:
- OrchestratorAgent: Main entry point that routes queries to specialized agents
- GraphAgent: Read-only graph queries and search operations
- AnalyzerAgent: Advanced analytics and pattern detection
- ExtractorAgent: Data ingestion and write operations
- AdminAgent: Privileged administrative operations

All agents use AWS Bedrock with Claude 3.5 Sonnet as the base model.
"""

from .orchestrator_agent import (
    create_orchestrator_agent,
    process_query,
    ORCHESTRATOR_SYSTEM_PROMPT
)
from .orchestrator_agent_agentcore import (
    create_orchestrator_with_agentcore,
    create_agentcore_app,
    AgentCoreMemoryHook,
    AgentType,
    IntentConfidence
)
from .graph_agent import (
    graph_agent,
    create_graph_agent,
    GRAPH_AGENT_SYSTEM_PROMPT
)
from .analyzer_agent import (
    analyzer_agent,
    create_analyzer_agent,
    ANALYZER_AGENT_SYSTEM_PROMPT
)
from .extractor_agent import (
    extractor_agent,
    create_extractor_agent,
    EXTRACTOR_AGENT_SYSTEM_PROMPT
)
from .admin_agent import (
    admin_agent,
    create_admin_agent,
    ADMIN_AGENT_SYSTEM_PROMPT
)

__all__ = [
    # Orchestrator - Simple (no AgentCore dependencies, for local testing)
    "create_orchestrator_agent",
    "process_query",
    "ORCHESTRATOR_SYSTEM_PROMPT",
    # Orchestrator - AgentCore Integration (for production deployment)
    "create_orchestrator_with_agentcore",
    "create_agentcore_app",
    "AgentCoreMemoryHook",
    "AgentType",
    "IntentConfidence",
    # Graph Agent
    "graph_agent",
    "create_graph_agent",
    "GRAPH_AGENT_SYSTEM_PROMPT",
    # Analyzer Agent
    "analyzer_agent",
    "create_analyzer_agent",
    "ANALYZER_AGENT_SYSTEM_PROMPT",
    # Extractor Agent
    "extractor_agent",
    "create_extractor_agent",
    "EXTRACTOR_AGENT_SYSTEM_PROMPT",
    # Admin Agent
    "admin_agent",
    "create_admin_agent",
    "ADMIN_AGENT_SYSTEM_PROMPT",
]

__version__ = "0.1.0"

