"""
Shared Constants and Enums

Defines constants used across all agents including:
- Node labels
- Relationship types
- Operation types
- Status codes
- Default values
"""

from enum import Enum
from typing import Set


# ============================================================================
# Node Labels
# ============================================================================

class NodeLabel(Enum):
    """Valid node labels in the graph."""
    
    PERSON = "Person"
    ORGANIZATION = "Organization"
    PROJECT = "Project"
    TECHNOLOGY = "Technology"
    RESOURCE = "Resource"


# Set of all valid node labels
VALID_NODE_LABELS: Set[str] = {label.value for label in NodeLabel}


# ============================================================================
# Relationship Types
# ============================================================================

class RelationshipType(Enum):
    """Valid relationship types in the graph."""
    
    WORKS_AT = "WORKS_AT"
    MANAGES = "MANAGES"
    REPORTS_TO = "REPORTS_TO"
    PARTICIPATES_IN = "PARTICIPATES_IN"
    USES = "USES"
    RELATES_TO = "RELATES_TO"


# Set of all valid relationship types
VALID_RELATIONSHIP_TYPES: Set[str] = {rel.value for rel in RelationshipType}


# ============================================================================
# Operation Types
# ============================================================================

class OperationType(Enum):
    """Types of graph operations."""
    
    READ = "read"
    WRITE = "write"
    SEARCH = "search"
    ANALYZE = "analyze"
    ADMIN = "admin"


# ============================================================================
# Query Types
# ============================================================================

class QueryType(Enum):
    """Types of user queries."""
    
    SEARCH_PERSON = "search_person"
    SEARCH_ORGANIZATION = "search_organization"
    FIND_RELATIONSHIPS = "find_relationships"
    FIND_PATH = "find_path"
    ANALYTICS = "analytics"
    CREATE_NODE = "create_node"
    UPDATE_NODE = "update_node"
    DELETE_NODE = "delete_node"
    ADMIN_OPERATION = "admin_operation"


# ============================================================================
# Status Codes
# ============================================================================

class NodeStatus(Enum):
    """Status values for nodes."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    PENDING = "pending"


class OperationStatus(Enum):
    """Status of operations."""
    
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"


# ============================================================================
# Agent Names
# ============================================================================

class AgentName(Enum):
    """Names of specialized agents."""
    
    ORCHESTRATOR = "orchestrator"
    GRAPH = "graph"
    ANALYZER = "analyzer"
    EXTRACTOR = "extractor"
    ADMIN = "admin"


# ============================================================================
# Default Values
# ============================================================================

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000
DEFAULT_OFFSET = 0

# Timeouts
DEFAULT_QUERY_TIMEOUT = 30  # seconds
DEFAULT_CONNECTION_TIMEOUT = 10  # seconds
DEFAULT_RETRY_COUNT = 3

# Rate Limiting
DEFAULT_RATE_LIMIT = 100  # requests per second
DEFAULT_BURST_LIMIT = 200

# Query Complexity
MAX_QUERY_COMPLEXITY = 1000
MAX_RESULT_SIZE = 1000

# Bulk Operations
MAX_BULK_CREATE = 100
MAX_BULK_UPDATE = 100
MAX_BULK_DELETE = 50

# Memory
DEFAULT_MEMORY_RETENTION_DAYS = 7

# Model Configuration
DEFAULT_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7

# ============================================================================
# Property Keys
# ============================================================================

class PropertyKey(Enum):
    """Common property keys for nodes and relationships."""
    
    # Identity
    ID = "id"
    NAME = "name"
    TITLE = "title"
    
    # Contact
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    
    # Metadata
    DESCRIPTION = "description"
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    CREATED_BY = "created_by"
    
    # Organizational
    DEPARTMENT = "department"
    ROLE = "role"
    LEVEL = "level"
    
    # Technical
    VERSION = "version"
    TYPE = "type"
    CATEGORY = "category"


# ============================================================================
# Error Messages
# ============================================================================

ERROR_MESSAGES = {
    "node_not_found": "Node with ID '{node_id}' not found",
    "relationship_not_found": "Relationship with ID '{rel_id}' not found",
    "invalid_label": "Invalid node label: {label}",
    "invalid_relationship": "Invalid relationship type: {rel_type}",
    "permission_denied": "Permission denied for operation: {operation}",
    "connection_failed": "Failed to connect to graph database",
    "query_timeout": "Query execution timed out after {timeout} seconds",
    "invalid_input": "Invalid input: {details}",
    "bulk_limit_exceeded": "Bulk operation exceeds maximum limit of {max_items} items"
}


# ============================================================================
# Success Messages
# ============================================================================

SUCCESS_MESSAGES = {
    "node_created": "Node created successfully",
    "node_updated": "Node updated successfully",
    "node_deleted": "Node deleted successfully",
    "relationship_created": "Relationship created successfully",
    "relationship_deleted": "Relationship deleted successfully",
    "query_executed": "Query executed successfully",
    "bulk_operation_completed": "Bulk operation completed",
    "reindex_started": "Reindexing operation started"
}


# ============================================================================
# Graph Patterns
# ============================================================================

# Common Cypher patterns for reuse
CYPHER_PATTERNS = {
    "find_node_by_id": "MATCH (n) WHERE elementId(n) = $node_id RETURN n",
    "find_node_by_property": "MATCH (n:{label}) WHERE n.{property} = $value RETURN n",
    "find_relationships": "MATCH (a)-[r]->(b) WHERE elementId(a) = $node_id RETURN r, b",
    "create_node": "CREATE (n:{label} $properties) RETURN n",
    "update_node": "MATCH (n) WHERE elementId(n) = $node_id SET n += $properties RETURN n",
    "delete_node": "MATCH (n) WHERE elementId(n) = $node_id DETACH DELETE n",
    "create_relationship": "MATCH (a), (b) WHERE elementId(a) = $from_id AND elementId(b) = $to_id CREATE (a)-[r:{rel_type} $properties]->(b) RETURN r"
}


# ============================================================================
# Observability
# ============================================================================

# Event types for logging
class EventType(Enum):
    """Types of events for observability."""
    
    AGENT_INVOCATION = "agent_invocation"
    TOOL_EXECUTION = "tool_execution"
    MODEL_CALL = "model_call"
    GRAPH_QUERY = "graph_query"
    GRAPH_WRITE = "graph_write"
    ERROR = "error"
    PERFORMANCE = "performance"


# Metric names
METRIC_NAMES = {
    "query_duration_ms": "query_duration_ms",
    "tool_duration_ms": "tool_duration_ms",
    "model_input_tokens": "model_input_tokens",
    "model_output_tokens": "model_output_tokens",
    "nodes_returned": "nodes_returned",
    "relationships_returned": "relationships_returned",
    "error_count": "error_count"
}


# ============================================================================
# File Paths
# ============================================================================

# Relative to project root
CONFIG_DIR = "deployment"
LOGS_DIR = "logs"
DATA_DIR = "data"
TESTS_DIR = "tests"


# ============================================================================
# Environment Names
# ============================================================================

class Environment(Enum):
    """Deployment environments."""
    
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


# ============================================================================
# AWS Configuration
# ============================================================================

# Bedrock
BEDROCK_REGION = "us-west-2"
BEDROCK_MODEL_FAMILIES = {
    "anthropic": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
    "amazon": ["titan-text", "titan-embed"],
    "meta": ["llama-3"]
}

# AgentCore
AGENTCORE_FEATURES = {
    "memory": "Memory",
    "observability": "Observability",
    "identity": "Identity",
    "gateway": "Gateway",
    "code_interpreter": "Code Interpreter"
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_error_message(key: str, **kwargs) -> str:
    """
    Get formatted error message.
    
    Args:
        key: Error message key
        **kwargs: Format parameters
    
    Returns:
        Formatted error message
    
    Example:
        >>> get_error_message("node_not_found", node_id="123")
        "Node with ID '123' not found"
    """
    template = ERROR_MESSAGES.get(key, "Unknown error")
    return template.format(**kwargs)


def get_success_message(key: str) -> str:
    """
    Get success message.
    
    Args:
        key: Success message key
    
    Returns:
        Success message
    """
    return SUCCESS_MESSAGES.get(key, "Operation completed successfully")

