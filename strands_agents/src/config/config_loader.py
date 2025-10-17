"""
Configuration Loader for Strands Agents

Loads environment-specific configuration from YAML files with:
- Environment detection (dev/test/prod)
- Configuration validation
- Environment variable overrides
- Default values
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.errors import ConfigurationError
from utils.logging import get_logger

logger = get_logger(__name__)


class Config:
    """
    Configuration container with environment-specific settings.
    
    Loads configuration from YAML files and applies environment overrides.
    """
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize configuration.
        
        Args:
            config_data: Dictionary of configuration data
        """
        self._config = config_data
        self.environment = config_data.get("environment", "development")
        self.region = config_data.get("region", "us-west-2")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Dot-separated configuration key (e.g., 'agents.orchestrator.model')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Agent configuration dictionary
        
        Raises:
            ConfigurationError: If agent not configured
        """
        agent_config = self.get(f"agents.{agent_name}")
        
        if not agent_config:
            raise ConfigurationError(
                f"Agent '{agent_name}' not found in configuration",
                details={"agent_name": agent_name, "environment": self.environment}
            )
        
        return agent_config
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j configuration."""
        neo4j_config = self.get("neo4j", {})
        
        # Apply environment variable overrides
        if os.getenv("NEO4J_URI"):
            neo4j_config["uri"] = os.getenv("NEO4J_URI")
        if os.getenv("NEO4J_USERNAME"):
            neo4j_config["username"] = os.getenv("NEO4J_USERNAME")
        if os.getenv("NEO4J_PASSWORD"):
            neo4j_config["password"] = os.getenv("NEO4J_PASSWORD")
        
        return neo4j_config
    
    def get_agentcore_config(self) -> Dict[str, Any]:
        """Get AgentCore configuration."""
        return self.get("agentcore", {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self.get("security", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.get("performance", {})
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self._config.copy()


def get_config_path(environment: Optional[str] = None) -> Path:
    """
    Get path to configuration file for environment.
    
    Args:
        environment: Environment name (development, production, test)
    
    Returns:
        Path to configuration file
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    # Map common variants to standard names
    env_map = {
        "dev": "dev",
        "development": "dev",
        "prod": "prod",
        "production": "prod",
        "test": "test"
    }
    
    normalized_env = env_map.get(environment.lower(), "dev")
    
    # Get project root (assumes this file is in src/config/)
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / "deployment" / normalized_env / "config.yaml"
    
    if not config_file.exists():
        raise ConfigurationError(
            f"Configuration file not found: {config_file}",
            details={"environment": environment, "expected_path": str(config_file)}
        )
    
    return config_file


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
    
    Returns:
        Configuration dictionary
    
    Raises:
        ConfigurationError: If file cannot be loaded
    """
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        if not config_data:
            raise ConfigurationError(
                "Configuration file is empty",
                details={"config_path": str(config_path)}
            )
        
        return config_data
    
    except yaml.YAMLError as e:
        raise ConfigurationError(
            "Failed to parse YAML configuration",
            details={"config_path": str(config_path), "error": str(e)},
            original_error=e
        )
    except IOError as e:
        raise ConfigurationError(
            "Failed to read configuration file",
            details={"config_path": str(config_path), "error": str(e)},
            original_error=e
        )


def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.
    
    Args:
        config: Base configuration dictionary
    
    Returns:
        Configuration with environment overrides applied
    """
    # AWS Region override
    if os.getenv("AWS_REGION"):
        config["region"] = os.getenv("AWS_REGION")
    
    # Log level override
    if os.getenv("LOG_LEVEL"):
        if "agentcore" not in config:
            config["agentcore"] = {}
        if "observability" not in config["agentcore"]:
            config["agentcore"]["observability"] = {}
        config["agentcore"]["observability"]["log_level"] = os.getenv("LOG_LEVEL")
    
    # Gateway endpoint override
    if os.getenv("GATEWAY_ENDPOINT"):
        if "neo4j" not in config:
            config["neo4j"] = {}
        config["neo4j"]["gateway_endpoint"] = os.getenv("GATEWAY_ENDPOINT")
    
    return config


def load_config(environment: Optional[str] = None) -> Config:
    """
    Load configuration for specified environment.
    
    Args:
        environment: Environment name (defaults to ENVIRONMENT env var)
    
    Returns:
        Config instance
    
    Raises:
        ConfigurationError: If configuration cannot be loaded
    
    Example:
        >>> config = load_config("development")
        >>> config.get("agents.orchestrator.model")
        'anthropic.claude-3-5-sonnet-20241022-v2:0'
        >>> config.get_agent_config("orchestrator")
        {'name': '...', 'model': '...'}
    """
    # Determine environment
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    logger.info(f"Loading configuration for environment: {environment}")
    
    # Get config file path
    config_path = get_config_path(environment)
    logger.debug(f"Configuration file: {config_path}")
    
    # Load YAML
    config_data = load_yaml_config(config_path)
    
    # Apply environment overrides
    config_data = apply_env_overrides(config_data)
    
    # Create config instance
    config = Config(config_data)
    
    logger.info(
        f"Configuration loaded successfully",
        environment=config.environment,
        region=config.region
    )
    
    return config


# Global config instance (lazy-loaded)
_global_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get global configuration instance.
    
    Args:
        reload: Force reload configuration
    
    Returns:
        Config instance
    
    Example:
        >>> config = get_config()
        >>> model = config.get("agents.graph.model")
    """
    global _global_config
    
    if _global_config is None or reload:
        _global_config = load_config()
    
    return _global_config

