"""
FastAPI proxy package for maintaining backward compatibility
while integrating with Strands Agents.

This package provides:
- Session management (file and S3)
- Request/response transformation
- Strands agent invocation
- API routing
- Structured logging and monitoring
- Error handling middleware
"""

from .models import (
    ChatMessage,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
    ProxyConfig
)
from .session import SessionManager, initialize_session_manager, get_session_manager
from .client import StrandsAgentClient, initialize_agent_client, get_agent_client
from .router import router
from .logging_config import (
    configure_logging,
    get_context_logger,
    set_request_context,
    clear_request_context,
    get_metrics
)
from .middleware import (
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    CircuitBreakerMiddleware
)

__all__ = [
    "ChatMessage",
    "ChatResponse",
    "ErrorResponse",
    "HealthResponse",
    "MetricsResponse",
    "ProxyConfig",
    "SessionManager",
    "initialize_session_manager",
    "get_session_manager",
    "StrandsAgentClient",
    "initialize_agent_client",
    "get_agent_client",
    "router",
    "configure_logging",
    "get_context_logger",
    "set_request_context",
    "clear_request_context",
    "get_metrics",
    "RequestLoggingMiddleware",
    "ErrorHandlingMiddleware",
    "CircuitBreakerMiddleware",
]
