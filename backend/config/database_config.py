"""
Database configuration settings for the Agent Tool Architecture.

This module provides configuration management for database connections,
including Neo4j settings, connection pooling, and performance tuning.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
import os


class DatabaseConfig(BaseModel):
    """Configuration for database connections."""
    
    # Neo4j connection settings
    neo4j_uri: str = Field(..., description="Neo4j database URI")
    neo4j_username: str = Field(..., description="Neo4j username")
    neo4j_password: str = Field(..., description="Neo4j password")
    neo4j_database: str = Field("neo4j", description="Neo4j database name")
    
    # Connection pool settings
    max_connection_pool_size: int = Field(50, description="Maximum connection pool size")
    connection_timeout: int = Field(30, description="Connection timeout in seconds")
    max_transaction_retry_time: int = Field(30, description="Maximum transaction retry time")
    
    # Performance settings
    enable_ssl: bool = Field(True, description="Enable SSL for connections")
    max_retry_time: int = Field(30, description="Maximum retry time for failed operations")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    
    # Query settings
    default_query_timeout: int = Field(60, description="Default query timeout in seconds")
    max_query_complexity: int = Field(100, description="Maximum query complexity score")
    enable_query_logging: bool = Field(False, description="Enable query logging")
    
    # Security settings
    enable_encryption: bool = Field(True, description="Enable connection encryption")
    trust_strategy: str = Field("TRUST_SYSTEM_CA_SIGNED_CERTIFICATES", description="SSL trust strategy")
    
    # Monitoring settings
    enable_metrics: bool = Field(True, description="Enable database metrics collection")
    metrics_interval: int = Field(60, description="Metrics collection interval in seconds")
    
    @validator('neo4j_uri')
    def validate_neo4j_uri(cls, v):
        if not v.startswith(('bolt://', 'bolt+s://', 'bolt+ssc://', 'neo4j://', 'neo4j+s://', 'neo4j+ssc://')):
            raise ValueError('Neo4j URI must start with bolt://, neo4j://, or their secure variants')
        return v
    
    @validator('max_connection_pool_size')
    def validate_pool_size(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Connection pool size must be between 1 and 1000')
        return v
    
    @validator('connection_timeout')
    def validate_connection_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError('Connection timeout must be between 1 and 300 seconds')
        return v
    
    @validator('trust_strategy')
    def validate_trust_strategy(cls, v):
        valid_strategies = [
            'TRUST_SYSTEM_CA_SIGNED_CERTIFICATES',
            'TRUST_ALL_CERTIFICATES',
            'TRUST_CUSTOM_CA_SIGNED_CERTIFICATES'
        ]
        if v not in valid_strategies:
            raise ValueError(f'Trust strategy must be one of: {valid_strategies}')
        return v


def get_database_config(env_prefix: str = "NEO4J") -> DatabaseConfig:
    """
    Get database configuration from environment variables.
    
    Args:
        env_prefix: Environment variable prefix
    
    Returns:
        DatabaseConfig instance
    """
    config_data = {
        "neo4j_uri": os.getenv(f"{env_prefix}_URI", "bolt://localhost:7687"),
        "neo4j_username": os.getenv(f"{env_prefix}_USERNAME", "neo4j"),
        "neo4j_password": os.getenv(f"{env_prefix}_PASSWORD", "password"),
        "neo4j_database": os.getenv(f"{env_prefix}_DATABASE", "neo4j"),
        "max_connection_pool_size": int(os.getenv(f"{env_prefix}_MAX_POOL_SIZE", "50")),
        "connection_timeout": int(os.getenv(f"{env_prefix}_CONNECTION_TIMEOUT", "30")),
        "max_transaction_retry_time": int(os.getenv(f"{env_prefix}_MAX_RETRY_TIME", "30")),
        "enable_ssl": os.getenv(f"{env_prefix}_ENABLE_SSL", "true").lower() == "true",
        "max_retry_time": int(os.getenv(f"{env_prefix}_MAX_RETRY_TIME", "30")),
        "retry_delay": float(os.getenv(f"{env_prefix}_RETRY_DELAY", "1.0")),
        "default_query_timeout": int(os.getenv(f"{env_prefix}_QUERY_TIMEOUT", "60")),
        "max_query_complexity": int(os.getenv(f"{env_prefix}_MAX_QUERY_COMPLEXITY", "100")),
        "enable_query_logging": os.getenv(f"{env_prefix}_ENABLE_QUERY_LOGGING", "false").lower() == "true",
        "enable_encryption": os.getenv(f"{env_prefix}_ENABLE_ENCRYPTION", "true").lower() == "true",
        "trust_strategy": os.getenv(f"{env_prefix}_TRUST_STRATEGY", "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES"),
        "enable_metrics": os.getenv(f"{env_prefix}_ENABLE_METRICS", "true").lower() == "true",
        "metrics_interval": int(os.getenv(f"{env_prefix}_METRICS_INTERVAL", "60"))
    }
    
    return DatabaseConfig(**config_data)


def create_custom_database_config(overrides: Dict[str, Any]) -> DatabaseConfig:
    """
    Create a custom database configuration with overrides.
    
    Args:
        overrides: Configuration overrides
    
    Returns:
        DatabaseConfig instance
    """
    # Start with default config
    base_config = get_database_config()
    config_data = base_config.dict()
    
    # Apply overrides
    config_data.update(overrides)
    
    return DatabaseConfig(**config_data)


def validate_database_config(config: DatabaseConfig) -> Dict[str, Any]:
    """
    Validate database configuration.
    
    Args:
        config: DatabaseConfig instance
    
    Returns:
        Dict with validation result and any issues
    """
    issues = []
    
    # Test connection (if possible)
    try:
        from neo4j import GraphDatabase
        # Build driver configuration
        driver_config = {
            "auth": (config.neo4j_username, config.neo4j_password),
            "max_connection_pool_size": config.max_connection_pool_size,
            "connection_timeout": config.connection_timeout,
            "max_transaction_retry_time": config.max_transaction_retry_time,
        }
        
        # Only add SSL configuration if URI doesn't already specify it
        # URI schemes like neo4j+ssc://, neo4j+s:// already include SSL settings
        uri = config.neo4j_uri.lower()
        if config.enable_ssl and not any(scheme in uri for scheme in ['+ssc', '+s']):
            driver_config["encrypted"] = True
        
        driver = GraphDatabase.driver(config.neo4j_uri, **driver_config)
        
        # Test connection
        with driver.session() as session:
            session.run("RETURN 1")
        
        driver.close()
        
    except Exception as e:
        issues.append(f"Database connection test failed: {str(e)}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


def get_connection_string(config: DatabaseConfig) -> str:
    """
    Get formatted connection string for logging (without password).
    
    Args:
        config: DatabaseConfig instance
    
    Returns:
        Formatted connection string
    """
    return f"{config.neo4j_uri} (user: {config.neo4j_username}, database: {config.neo4j_database})"


def get_performance_settings(config: DatabaseConfig) -> Dict[str, Any]:
    """
    Get performance-related settings from configuration.
    
    Args:
        config: DatabaseConfig instance
    
    Returns:
        Dict with performance settings
    """
    return {
        "max_connection_pool_size": config.max_connection_pool_size,
        "connection_timeout": config.connection_timeout,
        "max_transaction_retry_time": config.max_transaction_retry_time,
        "default_query_timeout": config.default_query_timeout,
        "max_query_complexity": config.max_query_complexity,
        "retry_delay": config.retry_delay
    }


def get_security_settings(config: DatabaseConfig) -> Dict[str, Any]:
    """
    Get security-related settings from configuration.
    
    Args:
        config: DatabaseConfig instance
    
    Returns:
        Dict with security settings
    """
    return {
        "enable_ssl": config.enable_ssl,
        "enable_encryption": config.enable_encryption,
        "trust_strategy": config.trust_strategy
    }


def get_monitoring_settings(config: DatabaseConfig) -> Dict[str, Any]:
    """
    Get monitoring-related settings from configuration.
    
    Args:
        config: DatabaseConfig instance
    
    Returns:
        Dict with monitoring settings
    """
    return {
        "enable_metrics": config.enable_metrics,
        "metrics_interval": config.metrics_interval,
        "enable_query_logging": config.enable_query_logging
    }


# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": {
        "max_connection_pool_size": 10,
        "connection_timeout": 15,
        "enable_query_logging": True,
        "enable_metrics": True,
        "metrics_interval": 30
    },
    "staging": {
        "max_connection_pool_size": 25,
        "connection_timeout": 20,
        "enable_query_logging": True,
        "enable_metrics": True,
        "metrics_interval": 60
    },
    "production": {
        "max_connection_pool_size": 50,
        "connection_timeout": 30,
        "enable_query_logging": False,
        "enable_metrics": True,
        "metrics_interval": 300
    }
}


def get_environment_config(environment: str) -> Dict[str, Any]:
    """
    Get configuration for a specific environment.
    
    Args:
        environment: Environment name (development, staging, production)
    
    Returns:
        Dict with environment-specific configuration
    """
    return ENVIRONMENT_CONFIGS.get(environment, {})


def create_environment_database_config(environment: str, base_config: Optional[DatabaseConfig] = None) -> DatabaseConfig:
    """
    Create database configuration for a specific environment.
    
    Args:
        environment: Environment name
        base_config: Optional base configuration to start from
    
    Returns:
        DatabaseConfig instance for the environment
    """
    if base_config is None:
        base_config = get_database_config()
    
    env_overrides = get_environment_config(environment)
    config_data = base_config.dict()
    config_data.update(env_overrides)
    
    return DatabaseConfig(**config_data)
