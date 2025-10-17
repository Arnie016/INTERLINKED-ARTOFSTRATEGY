"""
Query Safety and Validation Framework

This module provides safety measures for Neo4j query execution including:
- Read-only enforcement
- Query complexity analysis
- Performance monitoring
- Rate limiting
"""

import re
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from collections import defaultdict
from threading import Lock

try:
    from .errors import ValidationError, GraphQueryError, ToolExecutionError
    from .logging import get_logger
except ImportError:
    from errors import ValidationError, GraphQueryError, ToolExecutionError
    from logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Rate limiting state
_rate_limit_state = defaultdict(lambda: {"count": 0, "reset_time": time.time()})
_rate_limit_lock = Lock()


class QuerySafetyValidator:
    """
    Validator for ensuring query safety and read-only operations.
    """
    
    # Dangerous Cypher keywords that indicate write operations
    WRITE_KEYWORDS = [
        "CREATE", "MERGE", "DELETE", "REMOVE", "SET",
        "DETACH", "DROP", "ALTER", "GRANT", "REVOKE"
    ]
    
    # Expensive operations that should be limited
    EXPENSIVE_OPERATIONS = [
        "shortestPath", "allShortestPaths",
        "dijkstra", "aStar"
    ]
    
    @staticmethod
    def is_read_only(query: str) -> bool:
        """
        Check if a Cypher query is read-only.
        
        Args:
            query: The Cypher query to validate
            
        Returns:
            bool: True if query is read-only, False otherwise
            
        Raises:
            ValidationError: If query contains write operations
        """
        # Normalize query for checking
        query_upper = query.upper()
        
        # Check for write keywords
        for keyword in QuerySafetyValidator.WRITE_KEYWORDS:
            # Use word boundaries to avoid false positives (e.g., "CREATED" in property names)
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, query_upper):
                raise ValidationError(
                    f"Query contains forbidden write operation: {keyword}",
                    field="query",
                    details={"keyword": keyword, "query_preview": query[:100]}
                )
        
        return True
    
    @staticmethod
    def analyze_complexity(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze query complexity to prevent expensive operations.
        
        Args:
            query: The Cypher query to analyze
            params: Query parameters
            
        Returns:
            Dict containing complexity metrics:
            - complexity_score: Integer score (0-10, higher is more complex)
            - expensive_operations: List of expensive operations found
            - estimated_cost: Rough estimate of query cost
            - warnings: List of potential performance issues
        """
        query_upper = query.upper()
        complexity_score = 0
        expensive_ops = []
        warnings = []
        
        # Check for expensive path-finding operations
        for op in QuerySafetyValidator.EXPENSIVE_OPERATIONS:
            if op.upper() in query_upper:
                expensive_ops.append(op)
                complexity_score += 2
        
        # Check for unbounded variable-length patterns
        # Pattern like [*] or [*..] without upper bound
        unbounded_pattern = r'\[\*(?:\.\.)?\]'
        if re.search(unbounded_pattern, query):
            warnings.append("Unbounded variable-length pattern detected")
            complexity_score += 3
        
        # Check for large depth in variable-length patterns
        # Pattern like [*1..10]
        depth_pattern = r'\[\*\d+\.\.(\d+)\]'
        matches = re.findall(depth_pattern, query)
        for depth_str in matches:
            depth = int(depth_str)
            if depth > 5:
                warnings.append(f"Large traversal depth detected: {depth}")
                complexity_score += 1
        
        # Check for multiple MATCH clauses (could be expensive with cross-products)
        match_count = len(re.findall(r'\bMATCH\b', query_upper))
        if match_count > 3:
            warnings.append(f"Multiple MATCH clauses: {match_count}")
            complexity_score += 1
        
        # Check if LIMIT is used (good practice)
        if 'LIMIT' not in query_upper:
            warnings.append("No LIMIT clause found - results may be unbounded")
            complexity_score += 1
        
        # Check for OPTIONAL MATCH (can be expensive)
        if 'OPTIONAL MATCH' in query_upper:
            complexity_score += 1
        
        # Analyze parameters for potential issues
        if params:
            limit_value = params.get("limit", params.get("max_nodes", None))
            if limit_value and limit_value > 1000:
                warnings.append(f"Large limit value: {limit_value}")
                complexity_score += 1
        
        # Calculate estimated cost (simplified heuristic)
        estimated_cost = "low" if complexity_score < 3 else "medium" if complexity_score < 6 else "high"
        
        return {
            "complexity_score": min(complexity_score, 10),  # Cap at 10
            "expensive_operations": expensive_ops,
            "estimated_cost": estimated_cost,
            "warnings": warnings
        }
    
    @staticmethod
    def validate_query_safety(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Comprehensive query safety validation.
        
        Args:
            query: The Cypher query to validate
            params: Query parameters
            
        Returns:
            Dict with validation results
            
        Raises:
            ValidationError: If query fails safety checks
        """
        # Check read-only
        QuerySafetyValidator.is_read_only(query)
        
        # Analyze complexity
        complexity = QuerySafetyValidator.analyze_complexity(query, params)
        
        # Block queries that are too complex
        if complexity["complexity_score"] >= 8:
            raise ValidationError(
                f"Query complexity too high: {complexity['complexity_score']}/10",
                field="query",
                details=complexity
            )
        
        return {
            "safe": True,
            "complexity": complexity
        }


def validate_tool_input(func: Callable) -> Callable:
    """
    Decorator for validating tool inputs and ensuring type safety.
    
    This decorator:
    - Validates required parameters are present
    - Checks parameter types match function annotations
    - Logs tool invocations
    - Adds performance timing
    
    Usage:
        @validate_tool_input
        @tool
        def my_tool(param1: str, param2: int = 10) -> Dict:
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        tool_name = func.__name__
        
        logger.info(f"Tool invocation started: {tool_name}", operation=tool_name)
        
        try:
            # Get function signature for validation
            import inspect
            sig = inspect.signature(func)
            
            # Bind arguments to get actual parameter values
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate types (basic validation)
            for param_name, param_value in bound_args.arguments.items():
                param_obj = sig.parameters[param_name]
                
                # Skip if no annotation
                if param_obj.annotation == inspect.Parameter.empty:
                    continue
                
                # Get expected type (handle Optional types)
                expected_type = param_obj.annotation
                
                # Basic type checking (doesn't handle complex generics perfectly)
                if hasattr(expected_type, '__origin__'):
                    # Handle Optional, List, Dict, etc.
                    pass  # Complex generic validation would go here
                elif not isinstance(param_value, expected_type):
                    if param_value is not None:  # Allow None for optional params
                        logger.warning(
                            f"Type mismatch for parameter '{param_name}': "
                            f"expected {expected_type}, got {type(param_value)}",
                            operation=tool_name
                        )
            
            # Execute the tool
            result = func(*args, **kwargs)
            
            # Log success with timing
            elapsed_time = time.time() - start_time
            logger.info(
                f"Tool invocation completed: {tool_name}, elapsed: {elapsed_time:.3f}s",
                operation=tool_name,
                elapsed_time=elapsed_time
            )
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Tool invocation failed: {tool_name}, error: {e}, elapsed: {elapsed_time:.3f}s",
                operation=tool_name,
                elapsed_time=elapsed_time
            )
            raise
    
    return wrapper


def rate_limit(calls_per_minute: int = 60, per_user: bool = False):
    """
    Decorator for rate limiting tool calls.
    
    Args:
        calls_per_minute: Maximum number of calls allowed per minute
        per_user: If True, rate limit per user (requires user_id in kwargs)
        
    Usage:
        @rate_limit(calls_per_minute=30)
        @tool
        def my_tool(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tool_name = func.__name__
            
            # Determine rate limit key
            if per_user:
                user_id = kwargs.get("user_id", "anonymous")
                limit_key = f"{tool_name}:{user_id}"
            else:
                limit_key = tool_name
            
            current_time = time.time()
            
            with _rate_limit_lock:
                state = _rate_limit_state[limit_key]
                
                # Reset counter if minute has passed
                if current_time - state["reset_time"] >= 60:
                    state["count"] = 0
                    state["reset_time"] = current_time
                
                # Check rate limit
                if state["count"] >= calls_per_minute:
                    seconds_until_reset = 60 - (current_time - state["reset_time"])
                    raise ToolExecutionError(
                        message=f"Rate limit exceeded for {tool_name}",
                        tool_name=tool_name,
                        details={
                            "calls_per_minute": calls_per_minute,
                            "retry_after_seconds": int(seconds_until_reset)
                        }
                    )
                
                # Increment counter
                state["count"] += 1
            
            # Execute the function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def monitor_performance(threshold_seconds: float = 5.0):
    """
    Decorator for monitoring tool performance and logging slow operations.
    
    Args:
        threshold_seconds: Threshold in seconds for logging warnings
        
    Usage:
        @monitor_performance(threshold_seconds=2.0)
        @tool
        def my_tool(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tool_name = func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                # Log if operation took longer than threshold
                if elapsed_time > threshold_seconds:
                    logger.warning(
                        f"Slow operation detected: {tool_name} took {elapsed_time:.3f}s "
                        f"(threshold: {threshold_seconds}s)",
                        operation=tool_name,
                        elapsed_time=elapsed_time,
                        threshold=threshold_seconds
                    )
                
                return result
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(
                    f"Operation failed after {elapsed_time:.3f}s: {tool_name}",
                    operation=tool_name,
                    elapsed_time=elapsed_time
                )
                raise
        
        return wrapper
    return decorator


def validate_query_before_execution(query: str, params: Optional[Dict[str, Any]] = None):
    """
    Validate query safety before execution (for use in tools).
    
    Args:
        query: Cypher query to validate
        params: Query parameters
        
    Raises:
        ValidationError: If query fails safety checks
    """
    try:
        validation_result = QuerySafetyValidator.validate_query_safety(query, params)
        
        # Log complexity warnings
        complexity = validation_result["complexity"]
        if complexity["warnings"]:
            logger.warning(
                f"Query complexity warnings: {', '.join(complexity['warnings'])}",
                operation="query_validation",
                complexity_score=complexity["complexity_score"]
            )
        
    except ValidationError as e:
        logger.error(f"Query validation failed: {e.message}", operation="query_validation")
        raise


# Utility function to clear rate limit state (for testing)
def clear_rate_limit_state():
    """Clear all rate limit state. Use only for testing."""
    global _rate_limit_state
    with _rate_limit_lock:
        _rate_limit_state.clear()

