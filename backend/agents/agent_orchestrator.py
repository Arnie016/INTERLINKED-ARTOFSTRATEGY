"""
Agent Orchestrator - Main entry point for the Agent Tool Architecture.

This module provides a unified interface for managing and interacting with
different types of agents based on the user's needs and permissions.
"""

from typing import Dict, List, Any, Optional, Union
import logging
from enum import Enum

try:
    from .base_agent import BaseAgent
    from .graph_agent import GraphAgent
    from .extractor_agent import ExtractorAgent
    from .analyzer_agent import AnalyzerAgent
    from .admin_agent import AdminAgent
    from ..config import AgentConfig, DatabaseConfig, get_agent_config, get_database_config
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.base_agent import BaseAgent
    from agents.graph_agent import GraphAgent
    from agents.extractor_agent import ExtractorAgent
    from agents.analyzer_agent import AnalyzerAgent
    from agents.admin_agent import AdminAgent
    from config import AgentConfig, DatabaseConfig, get_agent_config, get_database_config


class AgentType(Enum):
    """Enumeration of available agent types."""
    GRAPH = "graph"
    EXTRACTOR = "extractor"
    ANALYZER = "analyzer"
    ADMIN = "admin"


class AgentOrchestrator:
    """
    Main orchestrator for managing and routing requests to appropriate agents.
    
    This class provides a unified interface for interacting with different
    types of agents based on the user's needs and permissions.
    """
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize the agent orchestrator.
        
        Args:
            db_config: Optional database configuration (uses default if not provided)
        """
        self.db_config = db_config or get_database_config()
        self.logger = self._setup_logging()
        
        # Initialize agent registry
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        
        # Load default agent configurations
        self._load_default_configs()
        
        self.logger.info("Agent Orchestrator initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the orchestrator."""
        logger = logging.getLogger("AgentOrchestrator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_default_configs(self):
        """Load default configurations for all agent types."""
        agent_types = ["graph_agent", "extractor_agent", "analyzer_agent", "admin_agent"]
        
        for agent_type in agent_types:
            try:
                config = get_agent_config(agent_type)
                self.agent_configs[agent_type] = config
                self.logger.info(f"Loaded configuration for {agent_type}")
            except Exception as e:
                self.logger.error(f"Failed to load configuration for {agent_type}: {str(e)}")
    
    def get_agent(self, agent_type: Union[str, AgentType], 
                  custom_config: Optional[AgentConfig] = None) -> BaseAgent:
        """
        Get an agent instance of the specified type.
        
        Args:
            agent_type: Type of agent to get
            custom_config: Optional custom configuration
        
        Returns:
            Agent instance
        """
        # Normalize agent type
        if isinstance(agent_type, AgentType):
            agent_type = agent_type.value
        
        # Map agent type to class
        agent_classes = {
            "graph": GraphAgent,
            "extractor": ExtractorAgent,
            "analyzer": AnalyzerAgent,
            "admin": AdminAgent
        }
        
        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Check if agent already exists
        agent_key = f"{agent_type}_{id(custom_config) if custom_config else 'default'}"
        if agent_key in self.agents:
            return self.agents[agent_key]
        
        # Get configuration
        if custom_config:
            config = custom_config
        else:
            config_key = f"{agent_type}_agent"
            if config_key not in self.agent_configs:
                raise ValueError(f"No configuration found for agent type: {agent_type}")
            config = self.agent_configs[config_key]
        
        # Create agent instance
        try:
            agent_class = agent_classes[agent_type]
            agent = agent_class(config, self.db_config)
            self.agents[agent_key] = agent
            self.logger.info(f"Created {agent_type} agent")
            return agent
        except Exception as e:
            self.logger.error(f"Failed to create {agent_type} agent: {str(e)}")
            raise
    
    def process_query(self, query: str, agent_type: Union[str, AgentType] = "graph") -> str:
        """
        Process a query using the specified agent type.
        
        Args:
            query: User query string
            agent_type: Type of agent to use
        
        Returns:
            Response string
        """
        try:
            agent = self.get_agent(agent_type)
            return agent.process_query(query)
        except Exception as e:
            error_msg = f"Failed to process query with {agent_type} agent: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def get_agent_capabilities(self, agent_type: Union[str, AgentType]) -> Dict[str, Any]:
        """
        Get capabilities of a specific agent type.
        
        Args:
            agent_type: Type of agent
        
        Returns:
            Dict containing agent capabilities
        """
        try:
            agent = self.get_agent(agent_type)
            return agent.get_capabilities()
        except Exception as e:
            return {
                "error": f"Failed to get capabilities for {agent_type}: {str(e)}"
            }
    
    def get_all_agent_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of all available agent types."""
        capabilities = {}
        
        for agent_type in ["graph", "extractor", "analyzer", "admin"]:
            try:
                capabilities[agent_type] = self.get_agent_capabilities(agent_type)
            except Exception as e:
                capabilities[agent_type] = {"error": str(e)}
        
        return capabilities
    
    def list_available_agents(self) -> List[Dict[str, Any]]:
        """List all available agent types with their descriptions."""
        return [
            {
                "type": "graph",
                "name": "Graph Query Agent",
                "description": "User-facing agent for safe graph queries and analysis",
                "role": "user",
                "capabilities": ["Organizational analysis", "Process bottleneck detection", "Team structure analysis"]
            },
            {
                "type": "extractor",
                "name": "Data Extractor Agent",
                "description": "Agent for data ingestion and extraction",
                "role": "extractor",
                "capabilities": ["Data ingestion", "Entity creation", "Relationship management"]
            },
            {
                "type": "analyzer",
                "name": "Pattern Analyzer Agent",
                "description": "Agent for pattern analysis and insights",
                "role": "analyzer",
                "capabilities": ["Pattern detection", "Insight generation", "Performance analysis"]
            },
            {
                "type": "admin",
                "name": "Administrative Agent",
                "description": "Agent for database administration and management",
                "role": "admin",
                "capabilities": ["Database administration", "Backup/restore", "Schema management"],
                "warning": "Has access to destructive operations"
            }
        ]
    
    def create_custom_agent(self, agent_type: Union[str, AgentType], 
                           config_overrides: Dict[str, Any]) -> BaseAgent:
        """
        Create a custom agent with overridden configuration.
        
        Args:
            agent_type: Type of agent to create
            config_overrides: Configuration overrides
        
        Returns:
            Custom agent instance
        """
        # Get base configuration
        if isinstance(agent_type, AgentType):
            agent_type = agent_type.value
        
        config_key = f"{agent_type}_agent"
        if config_key not in self.agent_configs:
            raise ValueError(f"No base configuration found for agent type: {agent_type}")
        
        base_config = self.agent_configs[config_key]
        
        # Create custom configuration
        try:
            from ..config import create_custom_config
        except ImportError:
            from config import create_custom_config
        custom_config = create_custom_config(config_key, config_overrides)
        
        # Create agent with custom configuration
        return self.get_agent(agent_type, custom_config)
    
    def close_all_agents(self):
        """Close all active agent connections."""
        for agent_key, agent in self.agents.items():
            try:
                agent.close()
                self.logger.info(f"Closed agent: {agent_key}")
            except Exception as e:
                self.logger.error(f"Failed to close agent {agent_key}: {str(e)}")
        
        self.agents.clear()
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get status of the orchestrator and all agents."""
        return {
            "orchestrator": {
                "status": "active",
                "active_agents": len(self.agents),
                "available_agent_types": list(self.agent_configs.keys())
            },
            "agents": {
                agent_key: {
                    "type": agent.__class__.__name__,
                    "role": agent.role,
                    "name": agent.name,
                    "available_tools": len(agent.get_available_tools())
                }
                for agent_key, agent in self.agents.items()
            },
            "database": {
                "uri": self.db_config.neo4j_uri,
                "database": self.db_config.neo4j_database,
                "username": self.db_config.neo4j_username
            }
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_all_agents()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close_all_agents()


# Convenience functions for easy access
def get_graph_agent(custom_config: Optional[AgentConfig] = None) -> GraphAgent:
    """Get a graph agent instance."""
    orchestrator = AgentOrchestrator()
    return orchestrator.get_agent("graph", custom_config)


def get_extractor_agent(custom_config: Optional[AgentConfig] = None) -> ExtractorAgent:
    """Get an extractor agent instance."""
    orchestrator = AgentOrchestrator()
    return orchestrator.get_agent("extractor", custom_config)


def get_analyzer_agent(custom_config: Optional[AgentConfig] = None) -> AnalyzerAgent:
    """Get an analyzer agent instance."""
    orchestrator = AgentOrchestrator()
    return orchestrator.get_agent("analyzer", custom_config)


def get_admin_agent(custom_config: Optional[AgentConfig] = None) -> AdminAgent:
    """Get an admin agent instance."""
    orchestrator = AgentOrchestrator()
    return orchestrator.get_agent("admin", custom_config)


def process_query_with_agent(query: str, agent_type: str = "graph") -> str:
    """Process a query with the specified agent type."""
    orchestrator = AgentOrchestrator()
    return orchestrator.process_query(query, agent_type)
