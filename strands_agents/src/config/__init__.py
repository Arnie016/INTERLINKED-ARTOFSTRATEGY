"""
Configuration Package for Strands Agents

Provides configuration management including:
- Environment-specific configuration loading
- Neo4j database configuration
- Shared constants and enums
- Model configuration utilities
"""

from .config_loader import Config, load_config, get_config
from .neo4j_config import (
    Neo4jConnectionConfig,
    Neo4jSettings,
    get_neo4j_config,
    validate_required_env_vars,
    create_custom_config,
    is_gateway_mode_enabled,
    get_gateway_url,
    get_config_instance,
    reset_config_instance,
    load_dotenv_if_exists,
    ENVIRONMENT_PRESETS
)
from .secrets_manager import (
    SecretsManagerClient,
    get_neo4j_credentials_from_secrets,
    get_secret_name_for_environment,
    validate_secret_structure,
    create_secret_json,
    get_secrets_client,
    reset_secrets_client
)
from .constants import (
    # Enums
    NodeLabel,
    RelationshipType,
    OperationType,
    QueryType,
    NodeStatus,
    OperationStatus,
    AgentName,
    PropertyKey,
    EventType,
    Environment,
    
    # Sets
    VALID_NODE_LABELS,
    VALID_RELATIONSHIP_TYPES,
    
    # Defaults
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DEFAULT_OFFSET,
    DEFAULT_QUERY_TIMEOUT,
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RATE_LIMIT,
    DEFAULT_BURST_LIMIT,
    MAX_QUERY_COMPLEXITY,
    MAX_RESULT_SIZE,
    MAX_BULK_CREATE,
    MAX_BULK_UPDATE,
    MAX_BULK_DELETE,
    DEFAULT_MEMORY_RETENTION_DAYS,
    DEFAULT_MODEL_ID,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    
    # Messages
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    get_error_message,
    get_success_message,
    
    # Patterns
    CYPHER_PATTERNS,
    
    # Metrics
    METRIC_NAMES
)
from .model_config import (
    ModelConfig,
    REASONING_MODEL,
    FAST_MODEL,
    CREATIVE_MODEL,
    PRECISE_MODEL,
    AGENT_MODEL_CONFIGS,
    get_model_config,
    create_custom_model_config,
    get_model_config_from_yaml,
    estimate_token_count,
    validate_token_budget,
    get_recommended_model,
    MODEL_CAPABILITIES,
    get_model_capabilities
)

__all__ = [
    # Config Loader
    "Config",
    "load_config",
    "get_config",
    
    # Neo4j Configuration
    "Neo4jConnectionConfig",
    "Neo4jSettings",
    "get_neo4j_config",
    "validate_required_env_vars",
    "create_custom_config",
    "is_gateway_mode_enabled",
    "get_gateway_url",
    "get_config_instance",
    "reset_config_instance",
    "load_dotenv_if_exists",
    "ENVIRONMENT_PRESETS",
    
    # AWS Secrets Manager
    "SecretsManagerClient",
    "get_neo4j_credentials_from_secrets",
    "get_secret_name_for_environment",
    "validate_secret_structure",
    "create_secret_json",
    "get_secrets_client",
    "reset_secrets_client",
    
    # Constants - Enums
    "NodeLabel",
    "RelationshipType",
    "OperationType",
    "QueryType",
    "NodeStatus",
    "OperationStatus",
    "AgentName",
    "PropertyKey",
    "EventType",
    "Environment",
    
    # Constants - Sets
    "VALID_NODE_LABELS",
    "VALID_RELATIONSHIP_TYPES",
    
    # Constants - Defaults
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "DEFAULT_OFFSET",
    "DEFAULT_QUERY_TIMEOUT",
    "DEFAULT_CONNECTION_TIMEOUT",
    "DEFAULT_RETRY_COUNT",
    "DEFAULT_RATE_LIMIT",
    "DEFAULT_BURST_LIMIT",
    "MAX_QUERY_COMPLEXITY",
    "MAX_RESULT_SIZE",
    "MAX_BULK_CREATE",
    "MAX_BULK_UPDATE",
    "MAX_BULK_DELETE",
    "DEFAULT_MEMORY_RETENTION_DAYS",
    "DEFAULT_MODEL_ID",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    
    # Constants - Messages
    "ERROR_MESSAGES",
    "SUCCESS_MESSAGES",
    "get_error_message",
    "get_success_message",
    
    # Constants - Patterns
    "CYPHER_PATTERNS",
    
    # Constants - Metrics
    "METRIC_NAMES",
    
    # Model Config
    "ModelConfig",
    "REASONING_MODEL",
    "FAST_MODEL",
    "CREATIVE_MODEL",
    "PRECISE_MODEL",
    "AGENT_MODEL_CONFIGS",
    "get_model_config",
    "create_custom_model_config",
    "get_model_config_from_yaml",
    "estimate_token_count",
    "validate_token_budget",
    "get_recommended_model",
    "MODEL_CAPABILITIES",
    "get_model_capabilities"
]

