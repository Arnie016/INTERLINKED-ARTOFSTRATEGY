"""
Agent configuration settings for the Agent Tool Architecture.

This module provides configuration management for different agent types,
including model settings, behavior parameters, and operational limits.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ModelProvider(Enum):
    """Enumeration of supported model providers."""
    BEDROCK = "bedrock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class AgentType(Enum):
    """Enumeration of agent types."""
    GRAPH_AGENT = "graph_agent"
    EXTRACTOR_AGENT = "extractor_agent"
    ANALYZER_AGENT = "analyzer_agent"
    ADMIN_AGENT = "admin_agent"


class AgentConfig(BaseModel):
    """Base configuration for agents."""
    
    # Agent identification
    agent_type: AgentType = Field(..., description="Type of agent")
    role: str = Field(..., description="Agent role (extractor, analyzer, admin, user)")
    name: str = Field(..., description="Agent name")
    
    # Model configuration
    model_provider: ModelProvider = Field(ModelProvider.BEDROCK, description="Model provider")
    model_id: str = Field("anthropic.claude-3-haiku-20240307-v1:0", description="Model ID")
    max_tokens: int = Field(1000, description="Maximum tokens per response")
    temperature: float = Field(0.1, description="Model temperature")
    
    # Tool configuration
    enable_tools: bool = Field(True, description="Whether to enable tool use")
    max_tool_calls: int = Field(5, description="Maximum tool calls per request")
    tool_timeout: int = Field(30, description="Tool execution timeout in seconds")
    
    # Behavior configuration
    enable_memory: bool = Field(False, description="Whether to enable conversation memory")
    max_memory_size: int = Field(10, description="Maximum number of messages to remember")
    enable_streaming: bool = Field(False, description="Whether to enable streaming responses")
    
    # Safety configuration
    enable_safety_checks: bool = Field(True, description="Whether to enable safety checks")
    require_confirmation_for_dangerous_tools: bool = Field(True, description="Require confirmation for dangerous operations")
    max_query_complexity: int = Field(100, description="Maximum query complexity score")
    
    # Performance configuration
    request_timeout: int = Field(60, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    
    # Logging configuration
    log_level: str = Field("INFO", description="Logging level")
    log_tool_calls: bool = Field(True, description="Whether to log tool calls")
    log_responses: bool = Field(False, description="Whether to log model responses")
    
    class Config:
        use_enum_values = True


# Default configurations for different agent types
DEFAULT_CONFIGS = {
    AgentType.GRAPH_AGENT.value: {
        "agent_type": AgentType.GRAPH_AGENT.value,
        "role": "user",
        "name": "Graph Query Agent",
        "model_provider": ModelProvider.BEDROCK.value,
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 1000,
        "temperature": 0.1,
        "enable_tools": True,
        "max_tool_calls": 5,
        "tool_timeout": 30,
        "enable_memory": False,
        "max_memory_size": 10,
        "enable_streaming": False,
        "enable_safety_checks": True,
        "require_confirmation_for_dangerous_tools": True,
        "max_query_complexity": 100,
        "request_timeout": 60,
        "retry_attempts": 3,
        "retry_delay": 1.0,
        "log_level": "INFO",
        "log_tool_calls": True,
        "log_responses": False
    },
    
    AgentType.EXTRACTOR_AGENT.value: {
        "agent_type": AgentType.EXTRACTOR_AGENT.value,
        "role": "extractor",
        "name": "Data Extractor Agent",
        "model_provider": ModelProvider.BEDROCK.value,
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 2000,
        "temperature": 0.05,
        "enable_tools": True,
        "max_tool_calls": 10,
        "tool_timeout": 60,
        "enable_memory": True,
        "max_memory_size": 20,
        "enable_streaming": False,
        "enable_safety_checks": True,
        "require_confirmation_for_dangerous_tools": False,
        "max_query_complexity": 50,
        "request_timeout": 120,
        "retry_attempts": 5,
        "retry_delay": 2.0,
        "log_level": "DEBUG",
        "log_tool_calls": True,
        "log_responses": True
    },
    
    AgentType.ANALYZER_AGENT.value: {
        "agent_type": AgentType.ANALYZER_AGENT.value,
        "role": "analyzer",
        "name": "Pattern Analyzer Agent",
        "model_provider": ModelProvider.BEDROCK.value,
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 3000,
        "temperature": 0.2,
        "enable_tools": True,
        "max_tool_calls": 8,
        "tool_timeout": 45,
        "enable_memory": True,
        "max_memory_size": 15,
        "enable_streaming": False,
        "enable_safety_checks": True,
        "require_confirmation_for_dangerous_tools": True,
        "max_query_complexity": 200,
        "request_timeout": 90,
        "retry_attempts": 3,
        "retry_delay": 1.5,
        "log_level": "INFO",
        "log_tool_calls": True,
        "log_responses": False
    },
    
    AgentType.ADMIN_AGENT.value: {
        "agent_type": AgentType.ADMIN_AGENT.value,
        "role": "admin",
        "name": "Administrative Agent",
        "model_provider": ModelProvider.BEDROCK.value,
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 2000,
        "temperature": 0.1,
        "enable_tools": True,
        "max_tool_calls": 10,
        "tool_timeout": 60,
        "enable_memory": True,
        "max_memory_size": 25,
        "enable_streaming": False,
        "enable_safety_checks": True,
        "require_confirmation_for_dangerous_tools": True,
        "max_query_complexity": 500,
        "request_timeout": 120,
        "retry_attempts": 2,
        "retry_delay": 3.0,
        "log_level": "WARNING",
        "log_tool_calls": True,
        "log_responses": True
    }
}


def get_agent_config(agent_type: str, custom_config: Optional[Dict[str, Any]] = None) -> AgentConfig:
    """
    Get configuration for a specific agent type.
    
    Args:
        agent_type: Type of agent
        custom_config: Optional custom configuration overrides
    
    Returns:
        AgentConfig instance
    """
    if agent_type not in DEFAULT_CONFIGS:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    config_data = DEFAULT_CONFIGS[agent_type].copy()
    
    # Apply custom overrides if provided
    if custom_config:
        config_data.update(custom_config)
    
    return AgentConfig(**config_data)


def get_available_agent_types() -> List[str]:
    """
    Get list of available agent types.
    
    Returns:
        List of agent type names
    """
    return [agent_type.value for agent_type in AgentType]


def validate_agent_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate agent configuration.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dict with validation result and any issues
    """
    issues = []
    
    # Check required fields
    required_fields = ["agent_type", "role", "name"]
    for field in required_fields:
        if field not in config:
            issues.append(f"Missing required field: {field}")
    
    # Validate agent type
    if "agent_type" in config and config["agent_type"] not in get_available_agent_types():
        issues.append(f"Invalid agent_type: {config['agent_type']}")
    
    # Validate role
    valid_roles = ["extractor", "analyzer", "admin", "user"]
    if "role" in config and config["role"] not in valid_roles:
        issues.append(f"Invalid role: {config['role']}")
    
    # Validate numeric fields
    numeric_fields = ["max_tokens", "temperature", "max_tool_calls", "tool_timeout"]
    for field in numeric_fields:
        if field in config:
            if not isinstance(config[field], (int, float)):
                issues.append(f"{field} must be numeric")
            elif field == "temperature" and not (0 <= config[field] <= 1):
                issues.append("temperature must be between 0 and 1")
            elif field in ["max_tokens", "max_tool_calls", "tool_timeout"] and config[field] <= 0:
                issues.append(f"{field} must be positive")
    
    # Validate boolean fields
    boolean_fields = ["enable_tools", "enable_memory", "enable_streaming", "enable_safety_checks"]
    for field in boolean_fields:
        if field in config and not isinstance(config[field], bool):
            issues.append(f"{field} must be boolean")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


def create_custom_config(base_agent_type: str, overrides: Dict[str, Any]) -> AgentConfig:
    """
    Create a custom configuration based on a base agent type with overrides.
    
    Args:
        base_agent_type: Base agent type to start from
        overrides: Configuration overrides
    
    Returns:
        AgentConfig instance
    """
    # Validate overrides
    validation_result = validate_agent_config(overrides)
    if not validation_result["valid"]:
        raise ValueError(f"Invalid configuration overrides: {validation_result['issues']}")
    
    return get_agent_config(base_agent_type, overrides)


def get_config_summary(config: AgentConfig) -> Dict[str, Any]:
    """
    Get a summary of agent configuration.
    
    Args:
        config: AgentConfig instance
    
    Returns:
        Dict with configuration summary
    """
    return {
        "agent_type": config.agent_type,
        "role": config.role,
        "name": config.name,
        "model": f"{config.model_provider}:{config.model_id}",
        "capabilities": {
            "tools_enabled": config.enable_tools,
            "max_tool_calls": config.max_tool_calls,
            "memory_enabled": config.enable_memory,
            "streaming_enabled": config.enable_streaming,
            "safety_checks": config.enable_safety_checks
        },
        "performance": {
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "timeout": config.request_timeout,
            "retry_attempts": config.retry_attempts
        },
        "logging": {
            "level": config.log_level,
            "log_tool_calls": config.log_tool_calls,
            "log_responses": config.log_responses
        }
    }
