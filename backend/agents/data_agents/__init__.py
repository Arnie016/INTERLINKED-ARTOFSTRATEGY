"""
Data Agents Package

This package contains agents that handle data processing operations,
separate from user-facing LLM interactions. These agents focus on
loading, processing, and managing data without direct user interaction.

Agents in this package:
- DataLoaderAgent: Dedicated agent for loading generated data into Neo4j
"""

from .data_loader_agent import DataLoaderAgent

__all__ = [
    'DataLoaderAgent'
]
