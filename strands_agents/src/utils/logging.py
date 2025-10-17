"""
Logging Utilities for Strands Agents

Provides centralized logging configuration with support for:
- Structured logging format
- Multiple severity levels
- AgentCore Observability integration
- CloudWatch compatibility
- Development and production modes
"""

import logging
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in structured JSON format
    for CloudWatch and observability dashboards.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class AgentLogger:
    """
    Centralized logger for agent operations with AgentCore observability integration.
    
    Features:
    - Environment-based configuration (dev/prod)
    - Structured logging for CloudWatch
    - Consistent formatting across all agents
    - Performance tracking
    - Session and trace ID support
    """
    
    def __init__(
        self,
        name: str,
        level: Optional[str] = None,
        environment: Optional[str] = None,
        enable_structured: bool = True
    ):
        """
        Initialize logger for an agent.
        
        Args:
            name: Logger name (typically agent name)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            environment: Environment name (development, production)
            enable_structured: Whether to use structured JSON logging
        """
        self.logger = logging.getLogger(name)
        
        # Determine log level
        if level is None:
            level = os.getenv("LOG_LEVEL", "INFO")
        
        # Determine environment
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        
        self.environment = environment
        self.enable_structured = enable_structured and (environment == "production")
        
        # Set log level
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Configure handler
        handler = logging.StreamHandler(sys.stdout)
        
        if self.enable_structured:
            # Use structured formatter for production
            formatter = StructuredFormatter()
        else:
            # Use readable formatter for development
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str, **extra_fields):
        """Log debug message with optional extra fields."""
        self._log(logging.DEBUG, message, extra_fields)
    
    def info(self, message: str, **extra_fields):
        """Log info message with optional extra fields."""
        self._log(logging.INFO, message, extra_fields)
    
    def warning(self, message: str, **extra_fields):
        """Log warning message with optional extra fields."""
        self._log(logging.WARNING, message, extra_fields)
    
    def error(self, message: str, **extra_fields):
        """Log error message with optional extra fields."""
        self._log(logging.ERROR, message, extra_fields)
    
    def critical(self, message: str, **extra_fields):
        """Log critical message with optional extra fields."""
        self._log(logging.CRITICAL, message, extra_fields)
    
    def _log(self, level: int, message: str, extra_fields: Dict[str, Any]):
        """Internal method to log with extra fields."""
        if extra_fields:
            # Create a new LogRecord with extra fields
            extra = {"extra_fields": extra_fields}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)
    
    def log_agent_invocation(
        self,
        agent_name: str,
        query: str,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """
        Log agent invocation with observability metadata.
        
        Args:
            agent_name: Name of the agent being invoked
            query: User query or input
            session_id: Optional session identifier
            trace_id: Optional trace identifier for distributed tracing
        """
        extra = {
            "agent_name": agent_name,
            "query_length": len(query),
            "event_type": "agent_invocation"
        }
        
        if session_id:
            extra["session_id"] = session_id
        if trace_id:
            extra["trace_id"] = trace_id
        
        self.info(f"Agent invoked: {agent_name}", **extra)
    
    def log_tool_execution(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Log tool execution with performance metrics.
        
        Args:
            tool_name: Name of the tool executed
            duration_ms: Execution duration in milliseconds
            success: Whether execution was successful
            error: Optional error message if failed
        """
        extra = {
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "event_type": "tool_execution"
        }
        
        if error:
            extra["error"] = error
            self.error(f"Tool execution failed: {tool_name}", **extra)
        else:
            self.info(f"Tool executed: {tool_name}", **extra)
    
    def log_model_call(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float
    ):
        """
        Log model invocation with token usage.
        
        Args:
            model_id: Bedrock model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Call duration in milliseconds
        """
        extra = {
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "duration_ms": duration_ms,
            "event_type": "model_call"
        }
        
        self.info(f"Model called: {model_id}", **extra)


def get_logger(
    name: str,
    level: Optional[str] = None,
    environment: Optional[str] = None
) -> AgentLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (typically module or agent name)
        level: Optional log level override
        environment: Optional environment override
    
    Returns:
        AgentLogger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Agent initialized")
        >>> logger.log_agent_invocation("graph_agent", "Find all people")
    """
    return AgentLogger(name, level, environment)

