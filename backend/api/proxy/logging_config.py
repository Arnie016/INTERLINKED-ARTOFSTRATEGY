"""
Structured logging configuration for FastAPI proxy.

Provides request tracing, correlation IDs, and integration with
AgentCore Observability for production monitoring.
"""

import logging
import sys
import json
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime
from contextvars import ContextVar
from functools import wraps

# Context variables for request correlation
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
session_id_ctx: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs logs in JSON format with contextual information
    including request IDs, session IDs, and timestamps.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request/session context if available
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id
        
        session_id = session_id_ctx.get()
        if session_id:
            log_data["session_id"] = session_id
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add source location
        log_data["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName
        }
        
        return json.dumps(log_data)


class ContextLogger:
    """
    Logger wrapper that adds contextual information to all log calls.
    
    Automatically includes request IDs, session IDs, and custom fields
    in all log entries.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize context logger.
        
        Args:
            logger: Base Python logger to wrap
        """
        self.logger = logger
    
    def _log(self, level: int, message: str, **extra_fields):
        """
        Log message with extra fields.
        
        Args:
            level: Log level (logging.INFO, logging.ERROR, etc.)
            message: Log message
            **extra_fields: Additional fields to include in log
        """
        # Create log record with extra fields
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",  # pathname
            0,   # lineno
            message,
            (),  # args
            None  # exc_info
        )
        record.extra_fields = extra_fields
        self.logger.handle(record)
    
    def info(self, message: str, **extra_fields):
        """Log info message with extra fields."""
        self._log(logging.INFO, message, **extra_fields)
    
    def warning(self, message: str, **extra_fields):
        """Log warning message with extra fields."""
        self._log(logging.WARNING, message, **extra_fields)
    
    def error(self, message: str, **extra_fields):
        """Log error message with extra fields."""
        self._log(logging.ERROR, message, **extra_fields)
    
    def debug(self, message: str, **extra_fields):
        """Log debug message with extra fields."""
        self._log(logging.DEBUG, message, **extra_fields)


def configure_logging(
    log_level: str = "INFO",
    use_json: bool = True,
    include_source: bool = True
) -> None:
    """
    Configure application-wide logging.
    
    Sets up structured logging with JSON formatting for production
    or human-readable format for development.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        use_json: Whether to use JSON formatting (True for production)
        include_source: Whether to include source file information
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if use_json:
        # Use JSON formatter for production
        formatter = StructuredFormatter()
    else:
        # Use simple formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set log levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)


def get_context_logger(name: str) -> ContextLogger:
    """
    Get context-aware logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        ContextLogger instance
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger)


def set_request_context(request_id: Optional[str] = None, session_id: Optional[str] = None):
    """
    Set request context for logging.
    
    Should be called at the beginning of each request to establish
    correlation IDs for all subsequent log entries.
    
    Args:
        request_id: Request ID (generated if not provided)
        session_id: Session ID (optional)
        
    Returns:
        Tuple of (request_id, session_id)
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    request_id_ctx.set(request_id)
    
    if session_id:
        session_id_ctx.set(session_id)
    
    return request_id, session_id


def clear_request_context():
    """Clear request context after request completes."""
    request_id_ctx.set(None)
    session_id_ctx.set(None)


def log_request_timing(logger: ContextLogger):
    """
    Decorator to log request timing information.
    
    Measures execution time and logs entry/exit points with timing data.
    
    Args:
        logger: ContextLogger instance
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            logger.info(
                f"Starting {func.__name__}",
                operation=func.__name__,
                arguments=str(kwargs.keys())
            )
            
            try:
                result = await func(*args, **kwargs)
                
                execution_time_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"Completed {func.__name__}",
                    operation=func.__name__,
                    execution_time_ms=round(execution_time_ms, 2),
                    success=True
                )
                
                return result
                
            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Failed {func.__name__}: {str(e)}",
                    operation=func.__name__,
                    execution_time_ms=round(execution_time_ms, 2),
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            logger.info(
                f"Starting {func.__name__}",
                operation=func.__name__,
                arguments=str(kwargs.keys())
            )
            
            try:
                result = func(*args, **kwargs)
                
                execution_time_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"Completed {func.__name__}",
                    operation=func.__name__,
                    execution_time_ms=round(execution_time_ms, 2),
                    success=True
                )
                
                return result
                
            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Failed {func.__name__}: {str(e)}",
                    operation=func.__name__,
                    execution_time_ms=round(execution_time_ms, 2),
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RequestMetrics:
    """
    Track request metrics for monitoring.
    
    Collects timing, error rate, and throughput metrics
    that can be exported to monitoring systems.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.request_count = 0
        self.error_count = 0
        self.total_response_time_ms = 0.0
        self.response_times = []
        self.errors_by_type = {}
    
    def record_request(
        self,
        response_time_ms: float,
        success: bool,
        error_type: Optional[str] = None
    ):
        """
        Record request metrics.
        
        Args:
            response_time_ms: Request response time in milliseconds
            success: Whether request succeeded
            error_type: Type of error if request failed
        """
        self.request_count += 1
        self.total_response_time_ms += response_time_ms
        self.response_times.append(response_time_ms)
        
        if not success:
            self.error_count += 1
            if error_type:
                self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics summary.
        
        Returns:
            Dictionary of metrics
        """
        if self.request_count == 0:
            return {
                "request_count": 0,
                "error_count": 0,
                "error_rate": 0.0,
                "avg_response_time_ms": 0.0
            }
        
        # Calculate percentiles
        sorted_times = sorted(self.response_times)
        p50_idx = int(len(sorted_times) * 0.5)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)
        
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count,
            "avg_response_time_ms": self.total_response_time_ms / self.request_count,
            "p50_response_time_ms": sorted_times[p50_idx] if sorted_times else 0.0,
            "p95_response_time_ms": sorted_times[p95_idx] if sorted_times else 0.0,
            "p99_response_time_ms": sorted_times[p99_idx] if sorted_times else 0.0,
            "errors_by_type": self.errors_by_type
        }
    
    def reset(self):
        """Reset all metrics."""
        self.request_count = 0
        self.error_count = 0
        self.total_response_time_ms = 0.0
        self.response_times = []
        self.errors_by_type = {}


# Global metrics instance
_metrics = RequestMetrics()


def get_metrics() -> RequestMetrics:
    """
    Get global metrics instance.
    
    Returns:
        RequestMetrics instance
    """
    return _metrics

