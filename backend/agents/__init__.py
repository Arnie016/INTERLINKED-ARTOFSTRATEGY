"""
Agents Package

This package contains all agents organized into two main categories:

1. LLM Agents (llm_agents): Agents that interact with Large Language Models
   for user queries and graph analysis. These handle user-facing operations.

2. Data Agents (data_agents): Agents that handle data processing operations,
   separate from user-facing LLM interactions. These focus on loading and
   managing data without direct user interaction.

The separation allows for:
- Clear distinction between user interaction logic and data processing logic
- Independent development and testing of each agent type
- Better maintainability and code organization
"""

# Import from subpackages
from .llm_agents import (
    BaseAgent,
    GraphAgent,
    ExtractorAgent, 
    AnalyzerAgent,
    AdminAgent,
    AgentOrchestrator
)

from .data_agents import (
    DataLoaderAgent
)

__all__ = [
    # LLM Agents
    'BaseAgent',
    'GraphAgent',
    'ExtractorAgent', 
    'AnalyzerAgent',
    'AdminAgent',
    'AgentOrchestrator',
    
    # Data Agents
    'DataLoaderAgent'
]
