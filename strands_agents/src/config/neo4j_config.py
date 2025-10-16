"""
Neo4j Database Configuration Module for Strands Agents

This module provides secure configuration management for Neo4j database connections
with support for both local development (.env files) and production environments
(AWS Secrets Manager integration).

Features:
- Environment variable loading with validation
- Secure credential handling (no logging, no exposure)
- Connection pooling configuration
- Performance tuning parameters
- Environment-specific settings (dev/staging/prod)
- Configuration toggle for direct vs Gateway access
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator, SecretStr
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from pathlib import Path

try:
    # Try relative imports first (when used as a package)
    from .constants import Environment, DEFAULT_CONNECTION_TIMEOUT, DEFAULT_QUERY_TIMEOUT
    from ..utils.errors import ConfigurationError
    from ..utils.logging import get_logger
except ImportError:
    # Fall back to absolute imports (when used in tests)
    from constants import Environment, DEFAULT_CONNECTION_TIMEOUT, DEFAULT_QUERY_TIMEOUT
    from utils.errors import ConfigurationError
    from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class Neo4jConnectionConfig(BaseModel):
    """Neo4j connection configuration with validation."""
    
    # Required connection settings
    uri: str = Field(..., description="Neo4j database URI (bolt:// or neo4j://)")
    username: str = Field(..., description="Neo4j username")
    password: SecretStr = Field(..., description="Neo4j password (secured)")
    database: str = Field(default="neo4j", description="Neo4j database name")
    
    # Connection pool settings
    max_connection_pool_size: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum connection pool size"
    )
    connection_timeout: int = Field(
        default=DEFAULT_CONNECTION_TIMEOUT,
        ge=1,
        le=300,
        description="Connection timeout in seconds"
    )
    max_transaction_retry_time: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Maximum transaction retry time in seconds"
    )
    
    # Security settings
    enable_ssl: bool = Field(default=True, description="Enable SSL/TLS for connections")
    encrypted: bool = Field(default=True, description="Enable connection encryption")
    trust_strategy: str = Field(
        default="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
        description="SSL/TLS certificate trust strategy"
    )
    
    # Performance settings
    default_query_timeout: int = Field(
        default=DEFAULT_QUERY_TIMEOUT,
        ge=1,
        le=600,
        description="Default query timeout in seconds"
    )
    max_retry_time: int = Field(
        default=30,
        ge=0,
        le=300,
        description="Maximum retry time for failed operations"
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Delay between retries in seconds"
    )
    
    # Feature flags
    enable_query_logging: bool = Field(
        default=False,
        description="Enable query logging (dev only)"
    )
    enable_metrics: bool = Field(
        default=True,
        description="Enable connection metrics collection"
    )
    
    @validator('uri')
    def validate_uri(cls, v: str) -> str:
        """Validate Neo4j URI format."""
        valid_schemes = [
            'bolt://', 'bolt+s://', 'bolt+ssc://',
            'neo4j://', 'neo4j+s://', 'neo4j+ssc://'
        ]
        if not any(v.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(
                f"Neo4j URI must start with one of: {', '.join(valid_schemes)}"
            )
        return v
    
    @validator('trust_strategy')
    def validate_trust_strategy(cls, v: str) -> str:
        """Validate SSL/TLS trust strategy."""
        valid_strategies = [
            'TRUST_SYSTEM_CA_SIGNED_CERTIFICATES',
            'TRUST_ALL_CERTIFICATES',
            'TRUST_CUSTOM_CA_SIGNED_CERTIFICATES'
        ]
        if v not in valid_strategies:
            raise ValueError(
                f"Trust strategy must be one of: {', '.join(valid_strategies)}"
            )
        return v
    
    def get_driver_config(self) -> Dict[str, Any]:
        """
        Get Neo4j driver configuration dictionary.
        
        Returns:
            Dict with driver configuration parameters
        """
        config = {
            "max_connection_pool_size": self.max_connection_pool_size,
            "connection_timeout": self.connection_timeout,
            "max_transaction_retry_time": self.max_transaction_retry_time,
        }
        
        # Add encryption if enabled and not already in URI
        uri_lower = self.uri.lower()
        if self.encrypted and not any(s in uri_lower for s in ['+s', '+ssc']):
            config["encrypted"] = True
        
        return config
    
    def get_connection_string_safe(self) -> str:
        """
        Get connection string for logging (without password).
        
        Returns:
            Safe connection string without credentials
        """
        return f"{self.uri} (user: {self.username}, database: {self.database})"
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            SecretStr: lambda v: "***REDACTED***"
        }


class Neo4jSettings(BaseSettings):
    """
    Neo4j settings loaded from environment variables.
    
    Loads configuration from .env file in development and environment
    variables in production.
    """
    
    # Required environment variables
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_username: str = Field(..., env="NEO4J_USERNAME")
    neo4j_password: SecretStr = Field(..., env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    # Optional environment variables with defaults
    neo4j_max_pool_size: int = Field(default=50, env="NEO4J_MAX_POOL_SIZE")
    neo4j_connection_timeout: int = Field(
        default=DEFAULT_CONNECTION_TIMEOUT,
        env="NEO4J_CONNECTION_TIMEOUT"
    )
    neo4j_enable_ssl: bool = Field(default=True, env="NEO4J_ENABLE_SSL")
    neo4j_enable_query_logging: bool = Field(
        default=False,
        env="NEO4J_ENABLE_QUERY_LOGGING"
    )
    neo4j_enable_metrics: bool = Field(default=True, env="NEO4J_ENABLE_METRICS")
    
    # Gateway mode configuration
    use_gateway: bool = Field(default=False, env="NEO4J_USE_GATEWAY")
    gateway_url: Optional[str] = Field(default=None, env="NEO4J_GATEWAY_URL")
    
    # Environment detection
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables
        
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            # Prioritize environment variables over .env file
            return env_settings, file_secret_settings, init_settings


# Environment-specific configuration presets
ENVIRONMENT_PRESETS: Dict[str, Dict[str, Any]] = {
    Environment.DEVELOPMENT.value: {
        "max_connection_pool_size": 10,
        "connection_timeout": 15,
        "enable_query_logging": True,
        "enable_metrics": True,
    },
    Environment.TEST.value: {
        "max_connection_pool_size": 25,
        "connection_timeout": 20,
        "enable_query_logging": True,
        "enable_metrics": True,
    },
    Environment.PRODUCTION.value: {
        "max_connection_pool_size": 50,
        "connection_timeout": 30,
        "enable_query_logging": False,
        "enable_metrics": True,
    }
}


def load_dotenv_if_exists() -> bool:
    """
    Load .env file if it exists in the project root.
    
    Returns:
        True if .env was loaded, False otherwise
    """
    # Look for .env in current directory and parent directories
    env_path = Path.cwd() / ".env"
    
    # Also check project root (strands_agents directory)
    project_root = Path(__file__).parent.parent.parent
    project_env_path = project_root / ".env"
    
    # Try project root first
    if project_env_path.exists():
        load_dotenv(project_env_path, override=True)
        logger.info(f"Loaded environment from: {project_env_path}")
        return True
    
    # Fall back to current directory
    if env_path.exists():
        load_dotenv(env_path, override=True)
        logger.info(f"Loaded environment from: {env_path}")
        return True
    
    logger.debug("No .env file found, using system environment variables")
    return False


def get_neo4j_config(
    environment: Optional[str] = None,
    use_dotenv: bool = True,
    use_secrets_manager: Optional[bool] = None
) -> Neo4jConnectionConfig:
    """
    Get Neo4j configuration from environment variables or AWS Secrets Manager.
    
    This function loads configuration from:
    1. AWS Secrets Manager (if use_secrets_manager=True or in production)
    2. .env file (if use_dotenv=True and file exists)
    3. System environment variables
    4. Environment-specific presets
    
    Args:
        environment: Target environment (development/staging/production).
                    If None, uses ENVIRONMENT env var or defaults to 'development'
        use_dotenv: Whether to load .env file if it exists
        use_secrets_manager: Whether to use AWS Secrets Manager.
                           If None, auto-detects based on environment
    
    Returns:
        Neo4jConnectionConfig instance
    
    Raises:
        ConfigurationError: If required environment variables are missing or invalid
    
    Example:
        >>> # Development: uses .env file
        >>> config = get_neo4j_config(environment="development")
        >>> 
        >>> # Production: uses AWS Secrets Manager
        >>> config = get_neo4j_config(environment="production")
        >>> 
        >>> driver = GraphDatabase.driver(
        ...     config.uri,
        ...     auth=(config.username, config.password.get_secret_value()),
        ...     **config.get_driver_config()
        ... )
    """
    try:
        # Determine environment
        env = environment or os.getenv('ENVIRONMENT', 'development')
        
        # Auto-detect Secrets Manager usage
        if use_secrets_manager is None:
            # Use Secrets Manager for production/staging, .env for development
            use_secrets_manager = env.lower() in ['production', 'staging', 'prod', 'stage']
        
        # Try AWS Secrets Manager first (production environments)
        if use_secrets_manager:
            try:
                from .secrets_manager import get_neo4j_credentials_from_secrets
                
                logger.info(f"Attempting to load credentials from AWS Secrets Manager for: {env}")
                credentials = get_neo4j_credentials_from_secrets(
                    environment=env,
                    enable_fallback=True  # Fallback to env vars if Secrets Manager fails
                )
                
                # Get environment-specific presets
                env_preset = ENVIRONMENT_PRESETS.get(env, {})
                
                # Build configuration from Secrets Manager credentials
                config_data = {
                    "uri": credentials['uri'],
                    "username": credentials['username'],
                    "password": credentials['password'],
                    "database": credentials.get('database', 'neo4j'),
                    "max_connection_pool_size": env_preset.get(
                        "max_connection_pool_size",
                        50
                    ),
                    "connection_timeout": env_preset.get(
                        "connection_timeout",
                        DEFAULT_CONNECTION_TIMEOUT
                    ),
                    "enable_ssl": True,  # Always use SSL in production
                    "enable_query_logging": env_preset.get(
                        "enable_query_logging",
                        False
                    ),
                    "enable_metrics": env_preset.get(
                        "enable_metrics",
                        True
                    ),
                }
                
                config = Neo4jConnectionConfig(**config_data)
                
                logger.info(
                    f"Neo4j configuration loaded from AWS Secrets Manager for: {env}",
                    extra={
                        "connection": config.get_connection_string_safe(),
                        "pool_size": config.max_connection_pool_size
                    }
                )
                
                return config
                
            except Exception as e:
                logger.warning(
                    f"Failed to load from AWS Secrets Manager, falling back to environment variables: {str(e)}"
                )
                # Continue to environment variable loading below
        
        # Load from environment variables (.env file or system env)
        if use_dotenv:
            load_dotenv_if_exists()
        
        # Load settings from environment
        settings = Neo4jSettings()
        
        # Get environment-specific presets
        env_preset = ENVIRONMENT_PRESETS.get(env, {})
        
        # Build configuration
        config_data = {
            "uri": settings.neo4j_uri,
            "username": settings.neo4j_username,
            "password": settings.neo4j_password,
            "database": settings.neo4j_database,
            "max_connection_pool_size": env_preset.get(
                "max_connection_pool_size",
                settings.neo4j_max_pool_size
            ),
            "connection_timeout": env_preset.get(
                "connection_timeout",
                settings.neo4j_connection_timeout
            ),
            "enable_ssl": settings.neo4j_enable_ssl,
            "enable_query_logging": env_preset.get(
                "enable_query_logging",
                settings.neo4j_enable_query_logging
            ),
            "enable_metrics": env_preset.get(
                "enable_metrics",
                settings.neo4j_enable_metrics
            ),
        }
        
        # Create and validate configuration
        config = Neo4jConnectionConfig(**config_data)
        
        # Log successful configuration (without credentials)
        logger.info(
            f"Neo4j configuration loaded from environment for: {env}",
            extra={
                "connection": config.get_connection_string_safe(),
                "pool_size": config.max_connection_pool_size,
                "gateway_mode": settings.use_gateway
            }
        )
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to load Neo4j configuration: {str(e)}")
        raise ConfigurationError(
            f"Failed to load Neo4j configuration: {str(e)}"
        ) from e


def validate_required_env_vars() -> Dict[str, bool]:
    """
    Validate that required environment variables are set.
    
    Returns:
        Dict mapping variable names to whether they are set
    
    Example:
        >>> validation = validate_required_env_vars()
        >>> if not all(validation.values()):
        ...     missing = [k for k, v in validation.items() if not v]
        ...     print(f"Missing required variables: {missing}")
    """
    required_vars = [
        "NEO4J_URI",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD"
    ]
    
    validation = {}
    for var in required_vars:
        value = os.getenv(var)
        is_set = value is not None and value.strip() != ""
        validation[var] = is_set
        
        if not is_set:
            logger.warning(f"Required environment variable not set: {var}")
    
    return validation


def create_custom_config(overrides: Dict[str, Any]) -> Neo4jConnectionConfig:
    """
    Create a custom Neo4j configuration with overrides.
    
    Starts with configuration from environment, then applies overrides.
    Useful for testing or special configurations.
    
    Args:
        overrides: Configuration overrides
    
    Returns:
        Neo4jConnectionConfig instance with overrides applied
    
    Example:
        >>> config = create_custom_config({
        ...     "max_connection_pool_size": 100,
        ...     "enable_query_logging": True
        ... })
    """
    try:
        # Get base configuration from environment
        base_config = get_neo4j_config()
        config_dict = base_config.dict()
        
        # Apply overrides (excluding password to maintain security)
        safe_overrides = {
            k: v for k, v in overrides.items()
            if k != "password"
        }
        config_dict.update(safe_overrides)
        
        # Create new configuration
        return Neo4jConnectionConfig(**config_dict)
        
    except Exception as e:
        logger.error(f"Failed to create custom configuration: {str(e)}")
        raise ConfigurationError(
            f"Failed to create custom configuration: {str(e)}"
        ) from e


def is_gateway_mode_enabled() -> bool:
    """
    Check if Gateway mode is enabled via environment variable.
    
    Returns:
        True if Gateway mode should be used, False for direct Neo4j access
    
    Example:
        >>> if is_gateway_mode_enabled():
        ...     # Use AgentCore Gateway
        ...     client = create_gateway_client()
        ... else:
        ...     # Use direct Neo4j connection
        ...     driver = create_neo4j_driver()
    """
    load_dotenv_if_exists()
    use_gateway = os.getenv("NEO4J_USE_GATEWAY", "false").lower() == "true"
    
    if use_gateway:
        logger.info("Gateway mode enabled for Neo4j access")
    else:
        logger.info("Direct mode enabled for Neo4j access")
    
    return use_gateway


def get_gateway_url() -> Optional[str]:
    """
    Get Gateway URL from environment if Gateway mode is enabled.
    
    Returns:
        Gateway URL if configured, None otherwise
    """
    if not is_gateway_mode_enabled():
        return None
    
    load_dotenv_if_exists()
    gateway_url = os.getenv("NEO4J_GATEWAY_URL")
    
    if not gateway_url:
        logger.warning(
            "Gateway mode enabled but NEO4J_GATEWAY_URL not set"
        )
    
    return gateway_url


# Singleton configuration instance (lazy loaded)
_config_instance: Optional[Neo4jConnectionConfig] = None


def get_config_instance() -> Neo4jConnectionConfig:
    """
    Get singleton Neo4j configuration instance.
    
    Lazy loads configuration on first access and caches it.
    Useful for avoiding repeated environment variable reads.
    
    Returns:
        Cached Neo4jConnectionConfig instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = get_neo4j_config()
    
    return _config_instance


def reset_config_instance() -> None:
    """
    Reset singleton configuration instance.
    
    Useful for testing or when configuration needs to be reloaded.
    """
    global _config_instance
    _config_instance = None
    logger.debug("Configuration instance reset")

