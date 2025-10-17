"""
Pydantic models for API request/response validation.

Defines the data models for:
- Incoming requests from frontend
- Outgoing responses to frontend
- Internal Strands agent formats
- Configuration settings
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Available agent types (for backward compatibility)."""
    GRAPH = "graph"
    ANALYZER = "analyzer"
    EXTRACTOR = "extractor"
    ADMIN = "admin"
    ORCHESTRATOR = "orchestrator"  # New default for Strands


# Frontend API Models (existing contract)

class ChatMessage(BaseModel):
    """
    Chat message from frontend (existing contract).
    
    This matches the current frontend API contract for backward compatibility.
    """
    message: str = Field(..., description="User's message content", min_length=1)
    agent_type: str = Field(
        default="orchestrator",
        description="Type of agent to use (for backward compatibility, now routes through orchestrator)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Who are the key people in the organization?",
                "agent_type": "graph"
            }
        }


class ChatResponse(BaseModel):
    """
    Chat response to frontend (existing contract).
    
    This maintains the current frontend API contract for backward compatibility.
    """
    success: bool = Field(..., description="Whether the request was successful")
    response: str = Field(..., description="Agent's response message")
    agent_type: str = Field(..., description="Type of agent that handled the request")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the response")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "Found 15 people in the organization...",
                "agent_type": "graph",
                "timestamp": "2025-10-17T10:30:00Z",
                "session_id": "user-123-abc"
            }
        }


# Internal Strands Agent Models

class StrandsAgentRequest(BaseModel):
    """
    Internal request format for Strands agents.
    
    This is the format used when invoking the Strands orchestrator agent.
    """
    prompt: str = Field(..., description="User's prompt/message")
    session_id: str = Field(..., description="Session ID for conversation context")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for the agent"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Who are the key people in the organization?",
                "session_id": "user-123-abc",
                "context": {}
            }
        }


class StrandsAgentResponse(BaseModel):
    """
    Internal response format from Strands agents.
    
    This represents the response structure from the Strands orchestrator.
    """
    result: str = Field(..., description="Agent's response")
    session_id: str = Field(..., description="Session ID")
    agent_used: Optional[str] = Field(None, description="Which specialized agent was used")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "result": "Found 15 people in the organization...",
                "session_id": "user-123-abc",
                "agent_used": "graph_agent",
                "metadata": {"execution_time_ms": 245}
            }
        }


# Configuration Models

class ProxyConfig(BaseModel):
    """
    Configuration settings for the proxy.
    
    Controls behavior of the FastAPI proxy including session management,
    feature flags, and deployment modes.
    """
    # Session Management
    session_backend: str = Field(
        default="file",
        description="Session backend: 'file' for local dev, 's3' for production"
    )
    session_storage_dir: Optional[str] = Field(
        default=None,
        description="Directory for file-based session storage (defaults to temp)"
    )
    session_s3_bucket: Optional[str] = Field(
        default=None,
        description="S3 bucket name for session storage in production"
    )
    session_s3_prefix: str = Field(
        default="interlinked-aos-dev/sessions/",
        description="S3 key prefix for session storage"
    )
    
    # Agent Configuration
    use_agentcore_memory: bool = Field(
        default=True,
        description="Whether to use AgentCore Memory for conversation persistence"
    )
    memory_id: Optional[str] = Field(
        default=None,
        description="AgentCore Memory ID (from environment or config)"
    )
    
    # Feature Flags
    enable_request_logging: bool = Field(
        default=True,
        description="Enable detailed request logging"
    )
    enable_error_details: bool = Field(
        default=True,
        description="Include detailed error information in responses (dev mode)"
    )
    enable_performance_metrics: bool = Field(
        default=True,
        description="Track and log performance metrics"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Max requests per time window"
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate limit time window in seconds"
    )
    
    # Timeouts
    agent_timeout_seconds: int = Field(
        default=60,
        description="Timeout for agent invocation in seconds"
    )
    
    # AWS Configuration
    aws_region: str = Field(
        default="us-west-2",
        description="AWS region for Bedrock and other services"
    )
    
    class Config:
        env_prefix = "PROXY_"  # Environment variables: PROXY_SESSION_BACKEND, etc.
        
        json_schema_extra = {
            "example": {
                "session_backend": "s3",
                "session_s3_bucket": "interlinked-aos-sessions",
                "use_agentcore_memory": True,
                "memory_id": "mem-abc123",
                "aws_region": "us-west-2"
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response model for API errors.
    
    Provides structured error information to the frontend.
    """
    success: bool = Field(default=False, description="Always False for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    detail: Optional[Dict[str, Any]] = Field(None, description="Additional error details (dev mode)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "AGENT_TIMEOUT",
                "message": "The request took too long to process",
                "path": "/api/chat",
                "detail": {"timeout_seconds": 60},
                "timestamp": "2025-10-17T10:30:00.000Z"
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response model.
    
    Provides status information about the proxy and its dependencies.
    """
    status: str = Field(..., description="Overall health status: 'healthy', 'degraded', or 'unhealthy'")
    message: str = Field(..., description="Human-readable status message")
    components: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Status of individual components"
    )
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "All systems operational",
                "components": {
                    "neo4j": {"status": "connected", "latency_ms": 15},
                    "strands_agent": {"status": "ready"},
                    "session_manager": {"status": "operational", "backend": "s3"}
                },
                "timestamp": "2025-10-17T10:30:00.000Z"
            }
        }


class MetricsResponse(BaseModel):
    """
    Metrics response model for monitoring endpoint.
    
    Provides performance and operational metrics.
    """
    request_count: int = Field(..., description="Total number of requests processed")
    error_count: int = Field(..., description="Total number of errors")
    error_rate: float = Field(..., description="Error rate (0.0-1.0)")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    p50_response_time_ms: float = Field(..., description="50th percentile response time")
    p95_response_time_ms: float = Field(..., description="95th percentile response time")
    p99_response_time_ms: float = Field(..., description="99th percentile response time")
    errors_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Error counts by error type"
    )
    circuit_breaker_state: Optional[Dict[str, Any]] = Field(
        None,
        description="Circuit breaker state if enabled"
    )
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_count": 1000,
                "error_count": 5,
                "error_rate": 0.005,
                "avg_response_time_ms": 245.3,
                "p50_response_time_ms": 210.0,
                "p95_response_time_ms": 450.0,
                "p99_response_time_ms": 850.0,
                "errors_by_type": {
                    "AgentTimeoutError": 3,
                    "ValidationError": 2
                },
                "circuit_breaker_state": {
                    "state": "CLOSED",
                    "failure_count": 0
                },
                "timestamp": "2025-10-17T10:30:00.000Z"
            }
        }

