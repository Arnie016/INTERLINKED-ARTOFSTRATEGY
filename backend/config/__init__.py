"""
Configuration package for the Agent Tool Architecture.

This package contains configuration files for:
- tool_permissions.py: Role-based access control for tools
- agent_config.py: Agent-specific configurations
- database_config.py: Database connection and settings
"""

try:
    from .tool_permissions import ROLE_PERMISSIONS, get_tools_for_role, validate_role_access, validate_tool_parameters
    from .agent_config import AgentConfig, get_agent_config
    from .database_config import DatabaseConfig, get_database_config
except ImportError:
    # Handle direct execution
    from tool_permissions import ROLE_PERMISSIONS, get_tools_for_role, validate_role_access, validate_tool_parameters
    from agent_config import AgentConfig, get_agent_config
    from database_config import DatabaseConfig, get_database_config

__all__ = [
    'ROLE_PERMISSIONS', 'get_tools_for_role', 'validate_role_access', 'validate_tool_parameters',
    'AgentConfig', 'get_agent_config',
    'DatabaseConfig', 'get_database_config'
]
