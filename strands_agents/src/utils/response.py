"""
Response Formatting Utilities

Provides standardized response formatting for agent operations:
- Success responses
- Error responses
- Paginated responses
- Metadata inclusion
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
from enum import Enum

T = TypeVar('T')


class ResponseStatus(Enum):
    """Standard response status codes."""
    
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class AgentResponse(Generic[T]):
    """
    Standardized response wrapper for agent operations.
    
    Provides consistent structure across all agent responses with:
    - Status indicator
    - Data payload
    - Metadata
    - Error information
    - Timing information
    """
    
    def __init__(
        self,
        status: ResponseStatus,
        data: Optional[T] = None,
        error: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ):
        """
        Initialize agent response.
        
        Args:
            status: Response status (success, error, partial)
            data: Response data payload
            error: Error information if status is error
            metadata: Additional metadata
            message: Optional human-readable message
        """
        self.status = status
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.message = message
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert response to dictionary.
        
        Returns:
            Dictionary representation of response
        """
        response = {
            "status": self.status.value,
            "timestamp": self.timestamp
        }
        
        if self.message:
            response["message"] = self.message
        
        if self.data is not None:
            response["data"] = self.data
        
        if self.error is not None:
            response["error"] = self.error
        
        if self.metadata:
            response["metadata"] = self.metadata
        
        return response


class PaginatedResponse(Generic[T]):
    """
    Response wrapper for paginated data.
    
    Includes pagination metadata and navigation information.
    """
    
    def __init__(
        self,
        items: List[T],
        total: int,
        limit: int,
        offset: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize paginated response.
        
        Args:
            items: List of items for current page
            total: Total number of items available
            limit: Maximum items per page
            offset: Number of items skipped
            metadata: Additional metadata
        """
        self.items = items
        self.total = total
        self.limit = limit
        self.offset = offset
        self.metadata = metadata or {}
        
        # Calculate pagination info
        self.page = (offset // limit) + 1 if limit > 0 else 1
        self.total_pages = (total + limit - 1) // limit if limit > 0 else 1
        self.has_next = offset + limit < total
        self.has_previous = offset > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary with items and pagination info
        """
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "limit": self.limit,
                "offset": self.offset,
                "page": self.page,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_previous": self.has_previous
            },
            "metadata": self.metadata
        }


def success_response(
    data: Any,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Optional success message
        metadata: Optional metadata
    
    Returns:
        Formatted success response
    
    Example:
        >>> success_response({"nodes": [{"id": 1, "name": "Alice"}]}, message="Query successful")
        {
            'status': 'success',
            'message': 'Query successful',
            'data': {'nodes': [{'id': 1, 'name': 'Alice'}]},
            'timestamp': '2024-01-01T12:00:00Z'
        }
    """
    response = AgentResponse(
        status=ResponseStatus.SUCCESS,
        data=data,
        message=message,
        metadata=metadata
    )
    return response.to_dict()


def error_response(
    error: Dict[str, Any],
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an error response.
    
    Args:
        error: Error information dictionary
        message: Optional error message
        metadata: Optional metadata
    
    Returns:
        Formatted error response
    
    Example:
        >>> error_response(
        ...     {"code": "3001", "message": "Query failed"},
        ...     message="Graph operation failed"
        ... )
        {
            'status': 'error',
            'message': 'Graph operation failed',
            'error': {'code': '3001', 'message': 'Query failed'},
            'timestamp': '2024-01-01T12:00:00Z'
        }
    """
    response = AgentResponse(
        status=ResponseStatus.ERROR,
        error=error,
        message=message,
        metadata=metadata
    )
    return response.to_dict()


def paginated_response(
    items: List[Any],
    total: int,
    limit: int,
    offset: int,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a paginated response.
    
    Args:
        items: List of items for current page
        total: Total number of items
        limit: Items per page
        offset: Number of items skipped
        message: Optional message
        metadata: Optional metadata
    
    Returns:
        Formatted paginated response
    
    Example:
        >>> paginated_response(
        ...     items=[{"id": 1}, {"id": 2}],
        ...     total=100,
        ...     limit=10,
        ...     offset=0
        ... )
        {
            'status': 'success',
            'data': {
                'items': [{'id': 1}, {'id': 2}],
                'pagination': {
                    'total': 100,
                    'limit': 10,
                    'offset': 0,
                    'page': 1,
                    'total_pages': 10,
                    'has_next': True,
                    'has_previous': False
                }
            },
            'timestamp': '2024-01-01T12:00:00Z'
        }
    """
    paginated = PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        metadata=metadata
    )
    
    response = AgentResponse(
        status=ResponseStatus.SUCCESS,
        data=paginated.to_dict(),
        message=message
    )
    
    return response.to_dict()


def partial_response(
    data: Any,
    warnings: List[str],
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a partial success response with warnings.
    
    Used when operation completed but with some issues.
    
    Args:
        data: Response data
        warnings: List of warning messages
        message: Optional message
        metadata: Optional metadata
    
    Returns:
        Formatted partial response
    
    Example:
        >>> partial_response(
        ...     data={"created": 5, "failed": 2},
        ...     warnings=["2 items could not be created"],
        ...     message="Bulk import partially completed"
        ... )
        {
            'status': 'partial',
            'message': 'Bulk import partially completed',
            'data': {'created': 5, 'failed': 2},
            'metadata': {'warnings': ['2 items could not be created']},
            'timestamp': '2024-01-01T12:00:00Z'
        }
    """
    if metadata is None:
        metadata = {}
    metadata["warnings"] = warnings
    
    response = AgentResponse(
        status=ResponseStatus.PARTIAL,
        data=data,
        message=message,
        metadata=metadata
    )
    
    return response.to_dict()


def format_node_response(node_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a single node for response.
    
    Args:
        node_data: Raw node data from graph
    
    Returns:
        Formatted node data
    """
    return {
        "id": node_data.get("id"),
        "label": node_data.get("label"),
        "properties": node_data.get("properties", {}),
        "created_at": node_data.get("created_at"),
        "updated_at": node_data.get("updated_at")
    }


def format_relationship_response(rel_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a single relationship for response.
    
    Args:
        rel_data: Raw relationship data from graph
    
    Returns:
        Formatted relationship data
    """
    return {
        "id": rel_data.get("id"),
        "type": rel_data.get("type"),
        "from": rel_data.get("from_node"),
        "to": rel_data.get("to_node"),
        "properties": rel_data.get("properties", {}),
        "created_at": rel_data.get("created_at")
    }


def format_graph_response(
    nodes: List[Dict[str, Any]],
    relationships: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Format a graph structure response.
    
    Args:
        nodes: List of nodes
        relationships: Optional list of relationships
    
    Returns:
        Formatted graph data
    """
    formatted = {
        "nodes": [format_node_response(node) for node in nodes],
        "node_count": len(nodes)
    }
    
    if relationships is not None:
        formatted["relationships"] = [
            format_relationship_response(rel) for rel in relationships
        ]
        formatted["relationship_count"] = len(relationships)
    
    return formatted


def add_performance_metadata(
    response: Dict[str, Any],
    execution_time_ms: float,
    additional_metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add performance metadata to response.
    
    Args:
        response: Base response dictionary
        execution_time_ms: Execution time in milliseconds
        additional_metrics: Optional additional performance metrics
    
    Returns:
        Response with performance metadata
    
    Example:
        >>> resp = success_response({"data": "value"})
        >>> add_performance_metadata(resp, 125.5, {"db_queries": 3})
        {..., 'metadata': {'execution_time_ms': 125.5, 'db_queries': 3}}
    """
    if "metadata" not in response:
        response["metadata"] = {}
    
    response["metadata"]["execution_time_ms"] = execution_time_ms
    
    if additional_metrics:
        response["metadata"].update(additional_metrics)
    
    return response

