"""
Utilities Package for Strands Agents

Provides shared utilities for all agents including:
- Logging with AgentCore Observability integration
- Error handling and custom exceptions
- Input validation
- Authentication and authorization
- Response formatting
- Testing utilities
"""

from .logging import AgentLogger, get_logger
from .errors import (
    AgentError,
    ConfigurationError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    GraphConnectionError,
    GraphQueryError,
    GraphSchemaError,
    GraphWriteError,
    ToolExecutionError,
    ModelError,
    RateLimitError,
    ErrorCode,
    handle_error
)
from .validation import (
    validate_node_label,
    validate_relationship_type,
    validate_node_properties,
    validate_relationship_properties,
    sanitize_cypher_input,
    validate_pagination_params,
    validate_search_query,
    validate_node_id,
    validate_bulk_operation,
    VALID_NODE_LABELS,
    VALID_RELATIONSHIP_TYPES
)
from .auth import (
    AuthContext,
    Role,
    Permission,
    validate_token,
    create_auth_context,
    require_admin,
    check_write_permission,
    check_read_permission,
    get_user_context_for_logging
)
from .response import (
    AgentResponse,
    PaginatedResponse,
    ResponseStatus,
    success_response,
    error_response,
    paginated_response,
    partial_response,
    format_node_response,
    format_relationship_response,
    format_graph_response,
    add_performance_metadata
)

__all__ = [
    # Logging
    "AgentLogger",
    "get_logger",
    
    # Errors
    "AgentError",
    "ConfigurationError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "GraphConnectionError",
    "GraphQueryError",
    "GraphSchemaError",
    "GraphWriteError",
    "ToolExecutionError",
    "ModelError",
    "RateLimitError",
    "ErrorCode",
    "handle_error",
    
    # Validation
    "validate_node_label",
    "validate_relationship_type",
    "validate_node_properties",
    "validate_relationship_properties",
    "sanitize_cypher_input",
    "validate_pagination_params",
    "validate_search_query",
    "validate_node_id",
    "validate_bulk_operation",
    "VALID_NODE_LABELS",
    "VALID_RELATIONSHIP_TYPES",
    
    # Auth
    "AuthContext",
    "Role",
    "Permission",
    "validate_token",
    "create_auth_context",
    "require_admin",
    "check_write_permission",
    "check_read_permission",
    "get_user_context_for_logging",
    
    # Response
    "AgentResponse",
    "PaginatedResponse",
    "ResponseStatus",
    "success_response",
    "error_response",
    "paginated_response",
    "partial_response",
    "format_node_response",
    "format_relationship_response",
    "format_graph_response",
    "add_performance_metadata"
]

