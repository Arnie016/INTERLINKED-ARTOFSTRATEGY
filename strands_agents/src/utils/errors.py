"""
Custom Exception Classes and Error Handlers

Provides a hierarchy of custom exceptions for different error scenarios
in the agent system, with support for structured error responses.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(Enum):
    """Standard error codes for agent operations."""
    
    # General errors (1xxx)
    INTERNAL_ERROR = "1000"
    CONFIGURATION_ERROR = "1001"
    VALIDATION_ERROR = "1002"
    
    # Authentication/Authorization errors (2xxx)
    AUTHENTICATION_FAILED = "2000"
    UNAUTHORIZED = "2001"
    PERMISSION_DENIED = "2002"
    
    # Graph operation errors (3xxx)
    GRAPH_CONNECTION_FAILED = "3000"
    GRAPH_QUERY_FAILED = "3001"
    NODE_NOT_FOUND = "3002"
    RELATIONSHIP_NOT_FOUND = "3003"
    INVALID_GRAPH_SCHEMA = "3004"
    GRAPH_WRITE_FAILED = "3005"
    
    # Tool execution errors (4xxx)
    TOOL_EXECUTION_FAILED = "4000"
    TOOL_NOT_FOUND = "4001"
    TOOL_TIMEOUT = "4002"
    
    # Model errors (5xxx)
    MODEL_INVOCATION_FAILED = "5000"
    MODEL_RATE_LIMIT_EXCEEDED = "5001"
    MODEL_CONTEXT_LIMIT_EXCEEDED = "5002"
    
    # Data errors (6xxx)
    INVALID_INPUT = "6000"
    MISSING_REQUIRED_FIELD = "6001"
    INVALID_DATA_FORMAT = "6002"


class AgentError(Exception):
    """
    Base exception class for all agent-related errors.
    
    Provides structured error information including error codes,
    user-friendly messages, and additional context.
    """
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize agent error.
        
        Args:
            message: Human-readable error message
            error_code: Standard error code from ErrorCode enum
            details: Additional context about the error
            original_error: Original exception if this is a wrapped error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for API responses.
        
        Returns:
            Dictionary with error information
        """
        error_dict = {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "type": self.__class__.__name__
            }
        }
        
        if self.details:
            error_dict["error"]["details"] = self.details
        
        if self.original_error:
            error_dict["error"]["original_error"] = str(self.original_error)
        
        return error_dict
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"[{self.error_code.value}] {self.message}"


class ConfigurationError(AgentError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message,
            ErrorCode.CONFIGURATION_ERROR,
            details,
            original_error
        )


class ValidationError(AgentError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if details is None:
            details = {}
        if field:
            details["field"] = field
        
        super().__init__(
            message,
            ErrorCode.VALIDATION_ERROR,
            details,
            original_error
        )


class AuthenticationError(AgentError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message,
            ErrorCode.AUTHENTICATION_FAILED,
            details,
            original_error
        )


class AuthorizationError(AgentError):
    """Raised when user lacks required permissions."""
    
    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if details is None:
            details = {}
        if required_permission:
            details["required_permission"] = required_permission
        
        super().__init__(
            message,
            ErrorCode.PERMISSION_DENIED,
            details,
            original_error
        )


class ConnectionError(AgentError):
    """Raised when connection to external service fails."""
    
    def __init__(
        self,
        message: str = "Connection failed",
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message,
            ErrorCode.GRAPH_CONNECTION_FAILED,
            details,
            original_error
        )


class GraphConnectionError(AgentError):
    """Raised when connection to graph database fails."""
    
    def __init__(
        self,
        message: str = "Failed to connect to graph database",
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message,
            ErrorCode.GRAPH_CONNECTION_FAILED,
            details,
            original_error
        )


class GraphQueryError(AgentError):
    """Raised when graph query execution fails."""
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if details is None:
            details = {}
        if query:
            details["query"] = query
        
        super().__init__(
            message,
            ErrorCode.GRAPH_QUERY_FAILED,
            details,
            original_error
        )


class GraphSchemaError(AgentError):
    """Raised when graph schema validation fails."""
    
    def __init__(
        self,
        message: str,
        schema_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if details is None:
            details = {}
        if schema_type:
            details["schema_type"] = schema_type
        
        super().__init__(
            message,
            ErrorCode.INVALID_GRAPH_SCHEMA,
            details,
            original_error
        )


class GraphWriteError(AgentError):
    """Raised when graph write operation fails."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if details is None:
            details = {}
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message,
            ErrorCode.GRAPH_WRITE_FAILED,
            details,
            original_error
        )


class ToolExecutionError(AgentError):
    """Raised when tool execution fails."""
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if details is None:
            details = {}
        if tool_name:
            details["tool_name"] = tool_name
        
        super().__init__(
            message,
            ErrorCode.TOOL_EXECUTION_FAILED,
            details,
            original_error
        )


class ModelError(AgentError):
    """Raised when model invocation fails."""
    
    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if details is None:
            details = {}
        if model_id:
            details["model_id"] = model_id
        
        super().__init__(
            message,
            ErrorCode.MODEL_INVOCATION_FAILED,
            details,
            original_error
        )


class RateLimitError(AgentError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if details is None:
            details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message,
            ErrorCode.MODEL_RATE_LIMIT_EXCEEDED,
            details,
            original_error
        )


def handle_error(error: Exception, logger=None) -> Dict[str, Any]:
    """
    Handle and format errors for API responses.
    
    Args:
        error: Exception to handle
        logger: Optional logger to log the error
    
    Returns:
        Dictionary containing error information
    
    Example:
        >>> try:
        ...     raise GraphQueryError("Query failed", query="MATCH (n) RETURN n")
        ... except Exception as e:
        ...     error_response = handle_error(e, logger)
    """
    if isinstance(error, AgentError):
        # Already a structured agent error
        error_dict = error.to_dict()
    else:
        # Wrap generic exception
        wrapped_error = AgentError(
            message=str(error),
            error_code=ErrorCode.INTERNAL_ERROR,
            original_error=error
        )
        error_dict = wrapped_error.to_dict()
    
    # Log error if logger provided
    if logger:
        logger.error(
            f"Error occurred: {error}",
            error_code=error_dict["error"]["code"],
            error_type=error_dict["error"]["type"]
        )
    
    return error_dict

