"""
Schema Validation Utilities

Provides validation functions for graph operations including:
- Node creation/update validation
- Relationship validation
- Query parameter validation
- Input sanitization
"""

from typing import Dict, Any, List, Optional, Set
import re
from .errors import ValidationError


# Valid node labels from configuration
VALID_NODE_LABELS = {
    "Person",
    "Organization",
    "Project",
    "Technology",
    "Resource"
}

# Valid relationship types from configuration
VALID_RELATIONSHIP_TYPES = {
    "WORKS_AT",
    "MANAGES",
    "PARTICIPATES_IN",
    "USES",
    "RELATES_TO"
}

# Common required properties for different node types
REQUIRED_NODE_PROPERTIES = {
    "Person": {"name"},
    "Organization": {"name"},
    "Project": {"name"},
    "Technology": {"name"},
    "Resource": {"name"}
}

# Property type definitions
PROPERTY_TYPES = {
    "name": str,
    "email": str,
    "title": str,
    "description": str,
    "created_at": str,
    "updated_at": str,
    "status": str,
    "url": str,
    "id": (str, int)
}


def validate_node_label(label: str) -> str:
    """
    Validate node label against allowed labels.
    
    Args:
        label: Node label to validate
    
    Returns:
        Validated label
    
    Raises:
        ValidationError: If label is invalid
    
    Example:
        >>> validate_node_label("Person")
        'Person'
        >>> validate_node_label("InvalidLabel")
        ValidationError: Invalid node label: InvalidLabel
    """
    if not label:
        raise ValidationError("Node label cannot be empty", field="label")
    
    if label not in VALID_NODE_LABELS:
        raise ValidationError(
            f"Invalid node label: {label}. Allowed labels: {', '.join(VALID_NODE_LABELS)}",
            field="label",
            details={"provided_label": label, "allowed_labels": list(VALID_NODE_LABELS)}
        )
    
    return label


def validate_relationship_type(rel_type: str) -> str:
    """
    Validate relationship type against allowed types.
    
    Args:
        rel_type: Relationship type to validate
    
    Returns:
        Validated relationship type
    
    Raises:
        ValidationError: If relationship type is invalid
    
    Example:
        >>> validate_relationship_type("WORKS_AT")
        'WORKS_AT'
    """
    if not rel_type:
        raise ValidationError("Relationship type cannot be empty", field="rel_type")
    
    if rel_type not in VALID_RELATIONSHIP_TYPES:
        raise ValidationError(
            f"Invalid relationship type: {rel_type}. Allowed types: {', '.join(VALID_RELATIONSHIP_TYPES)}",
            field="rel_type",
            details={"provided_type": rel_type, "allowed_types": list(VALID_RELATIONSHIP_TYPES)}
        )
    
    return rel_type


def validate_node_properties(
    label: str,
    properties: Dict[str, Any],
    check_required: bool = True
) -> Dict[str, Any]:
    """
    Validate node properties for a given label.
    
    Args:
        label: Node label
        properties: Dictionary of properties to validate
        check_required: Whether to check for required properties
    
    Returns:
        Validated properties dictionary
    
    Raises:
        ValidationError: If properties are invalid
    
    Example:
        >>> validate_node_properties("Person", {"name": "Alice", "email": "alice@example.com"})
        {'name': 'Alice', 'email': 'alice@example.com'}
    """
    # Validate label first
    validate_node_label(label)
    
    # Check for required properties
    if check_required and label in REQUIRED_NODE_PROPERTIES:
        required_props = REQUIRED_NODE_PROPERTIES[label]
        missing_props = required_props - set(properties.keys())
        
        if missing_props:
            raise ValidationError(
                f"Missing required properties for {label}: {', '.join(missing_props)}",
                field="properties",
                details={"missing_properties": list(missing_props)}
            )
    
    # Validate property types
    validated_props = {}
    for key, value in properties.items():
        if key in PROPERTY_TYPES:
            expected_type = PROPERTY_TYPES[key]
            
            # Handle union types
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Property '{key}' must be one of types: {expected_type}",
                        field=key,
                        details={"expected_types": [t.__name__ for t in expected_type], "actual_type": type(value).__name__}
                    )
            else:
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Property '{key}' must be of type {expected_type.__name__}",
                        field=key,
                        details={"expected_type": expected_type.__name__, "actual_type": type(value).__name__}
                    )
        
        validated_props[key] = value
    
    return validated_props


def validate_relationship_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate relationship properties.
    
    Args:
        properties: Dictionary of relationship properties
    
    Returns:
        Validated properties dictionary
    
    Raises:
        ValidationError: If properties are invalid
    """
    validated_props = {}
    
    for key, value in properties.items():
        if key in PROPERTY_TYPES:
            expected_type = PROPERTY_TYPES[key]
            
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Relationship property '{key}' must be one of types: {expected_type}",
                        field=key
                    )
            else:
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Relationship property '{key}' must be of type {expected_type.__name__}",
                        field=key
                    )
        
        validated_props[key] = value
    
    return validated_props


def sanitize_cypher_input(value: str) -> str:
    """
    Sanitize input for Cypher queries to prevent injection attacks.
    
    Args:
        value: String value to sanitize
    
    Returns:
        Sanitized string
    
    Note:
        This is a basic sanitization. Always use parameterized queries
        for production use.
    
    Example:
        >>> sanitize_cypher_input("Alice'; DROP DATABASE;--")
        'Alice DROP DATABASE'
    """
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[;\'"\\]', '', value)
    
    # Remove SQL/Cypher keywords that could be malicious
    dangerous_keywords = [
        'DROP', 'DELETE', 'DETACH', 'REMOVE', 'CREATE INDEX',
        'DROP INDEX', 'CREATE CONSTRAINT', 'DROP CONSTRAINT'
    ]
    
    for keyword in dangerous_keywords:
        sanitized = re.sub(keyword, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()


def validate_pagination_params(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    max_limit: int = 1000,
    default_limit: int = 50
) -> Dict[str, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        max_limit: Maximum allowed limit
        default_limit: Default limit if none provided
    
    Returns:
        Dictionary with validated limit and offset
    
    Raises:
        ValidationError: If parameters are invalid
    
    Example:
        >>> validate_pagination_params(limit=100, offset=0)
        {'limit': 100, 'offset': 0}
    """
    # Validate limit
    if limit is None:
        limit = default_limit
    elif not isinstance(limit, int):
        raise ValidationError("Limit must be an integer", field="limit")
    elif limit < 1:
        raise ValidationError("Limit must be greater than 0", field="limit")
    elif limit > max_limit:
        raise ValidationError(
            f"Limit cannot exceed {max_limit}",
            field="limit",
            details={"max_limit": max_limit}
        )
    
    # Validate offset
    if offset is None:
        offset = 0
    elif not isinstance(offset, int):
        raise ValidationError("Offset must be an integer", field="offset")
    elif offset < 0:
        raise ValidationError("Offset cannot be negative", field="offset")
    
    return {"limit": limit, "offset": offset}


def validate_search_query(query: str, min_length: int = 1, max_length: int = 500) -> str:
    """
    Validate search query string.
    
    Args:
        query: Search query to validate
        min_length: Minimum allowed query length
        max_length: Maximum allowed query length
    
    Returns:
        Validated query string
    
    Raises:
        ValidationError: If query is invalid
    
    Example:
        >>> validate_search_query("Find Alice")
        'Find Alice'
    """
    if not query or not query.strip():
        raise ValidationError("Search query cannot be empty", field="query")
    
    query = query.strip()
    
    if len(query) < min_length:
        raise ValidationError(
            f"Query must be at least {min_length} characters",
            field="query",
            details={"min_length": min_length}
        )
    
    if len(query) > max_length:
        raise ValidationError(
            f"Query cannot exceed {max_length} characters",
            field="query",
            details={"max_length": max_length}
        )
    
    return query


def validate_node_id(node_id: Any) -> str:
    """
    Validate node identifier.
    
    Args:
        node_id: Node ID to validate
    
    Returns:
        Validated node ID as string
    
    Raises:
        ValidationError: If node ID is invalid
    """
    if node_id is None:
        raise ValidationError("Node ID cannot be null", field="node_id")
    
    # Convert to string for consistent handling
    node_id_str = str(node_id)
    
    if not node_id_str.strip():
        raise ValidationError("Node ID cannot be empty", field="node_id")
    
    return node_id_str


def validate_bulk_operation(
    items: List[Dict[str, Any]],
    max_items: int = 100
) -> List[Dict[str, Any]]:
    """
    Validate bulk operation items.
    
    Args:
        items: List of items for bulk operation
        max_items: Maximum allowed items per operation
    
    Returns:
        Validated items list
    
    Raises:
        ValidationError: If bulk operation is invalid
    
    Example:
        >>> items = [{"label": "Person", "properties": {"name": "Alice"}}]
        >>> validate_bulk_operation(items)
        [{'label': 'Person', 'properties': {'name': 'Alice'}}]
    """
    if not items:
        raise ValidationError("Bulk operation cannot be empty", field="items")
    
    if not isinstance(items, list):
        raise ValidationError("Items must be a list", field="items")
    
    if len(items) > max_items:
        raise ValidationError(
            f"Bulk operation cannot exceed {max_items} items",
            field="items",
            details={"max_items": max_items, "provided_items": len(items)}
        )
    
    return items

