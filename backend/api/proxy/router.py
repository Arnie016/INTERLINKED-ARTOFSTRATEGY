"""
FastAPI router for proxy endpoints.

Provides the /api/chat endpoint with backward compatibility
while forwarding to Strands agents.
"""

import logging
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

from .models import (
    ChatMessage,
    ChatResponse,
    HealthResponse,
    ErrorResponse,
    MetricsResponse,
    ProxyConfig,
)
from .session import get_session_manager
from .client import get_agent_client
from .transformers import (
    RequestTransformer,
    ResponseTransformer,
    validate_chat_message,
    sanitize_message,
)
from .client import (
    AgentInvocationError,
    AgentTimeoutError,
    AgentConfigurationError,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["proxy"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    chat_message: ChatMessage,
    request: Request,
    response: Response
) -> ChatResponse:
    """
    Chat with the AI agent system (proxy to Strands agents).
    
    This endpoint maintains backward compatibility with the existing frontend
    while routing requests through the new Strands agent orchestrator.
    
    Features:
    - Session management for conversation context
    - Automatic routing to specialized agents
    - Error handling and retry logic
    - Performance metrics
    
    Args:
        chat_message: User's chat message
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        Chat response from the agent
        
    Raises:
        HTTPException: On various error conditions
    """
    session_id = None
    
    try:
        # Get managers
        session_manager_instance = get_session_manager()
        agent_client = get_agent_client()
        
        # Validate message
        is_valid, error_msg = validate_chat_message(chat_message)
        if not is_valid:
            logger.warning(f"Invalid message: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Sanitize message
        chat_message.message = sanitize_message(chat_message.message)
        
        # Get or create session ID
        session_id = session_manager_instance.get_or_create_session_id(request)
        
        # Set session cookie in response
        session_manager_instance.set_session_cookie(response, session_id)
        
        logger.info(
            f"Processing chat request for session {session_id}: "
            f"agent_type={chat_message.agent_type}, "
            f"message_preview={chat_message.message[:50]}..."
        )
        
        # Create Strands session manager for this session
        strands_session_manager = session_manager_instance.create_strands_session_manager(
            session_id
        )
        
        # Transform request to Strands format
        strands_request = RequestTransformer.transform(
            chat_message=chat_message,
            session_id=session_id
        )
        
        # Invoke agent
        strands_response = agent_client.invoke_agent(
            request=strands_request,
            session_manager=strands_session_manager
        )
        
        # Transform response to frontend format
        frontend_response = ResponseTransformer.transform(
            agent_response=strands_response,
            original_agent_type=chat_message.agent_type
        )
        
        logger.info(
            f"Successfully processed chat request for session {session_id}: "
            f"response_length={len(frontend_response.response)}"
        )
        
        return frontend_response
        
    except AgentTimeoutError as e:
        logger.error(f"Agent timeout for session {session_id}: {e}")
        return ResponseTransformer.transform_error(
            error_message="The request took too long to process. Please try again.",
            session_id=session_id,
            agent_type=chat_message.agent_type
        )
        
    except AgentConfigurationError as e:
        logger.error(f"Agent configuration error for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent system is temporarily unavailable"
        )
        
    except AgentInvocationError as e:
        logger.error(f"Agent invocation error for session {session_id}: {e}")
        return ResponseTransformer.transform_error(
            error_message="I encountered an error processing your request. Please try again.",
            session_id=session_id,
            agent_type=chat_message.agent_type
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(
            f"Unexpected error processing chat for session {session_id}: {e}",
            exc_info=True
        )
        return ResponseTransformer.transform_error(
            error_message="An unexpected error occurred. Please try again.",
            session_id=session_id,
            agent_type=chat_message.agent_type if chat_message else "orchestrator"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for the proxy.
    
    Checks the status of:
    - Session manager
    - Agent client
    - Neo4j connection (via agent)
    
    Returns:
        Health status information
    """
    components = {}
    overall_status = "healthy"
    messages = []
    
    try:
        # Check session manager
        session_manager = get_session_manager()
        active_sessions = session_manager.get_active_sessions_count()
        components["session_manager"] = {
            "status": "operational",
            "backend": session_manager.config.session_backend,
            "active_sessions": active_sessions
        }
        
    except Exception as e:
        logger.error(f"Session manager health check failed: {e}")
        components["session_manager"] = {
            "status": "error",
            "error": str(e)
        }
        overall_status = "unhealthy"
        messages.append("Session manager unavailable")
    
    try:
        # Check agent client
        agent_client = get_agent_client()
        agent_health = await agent_client.health_check()
        components["strands_agent"] = agent_health
        
        if agent_health.get("status") != "ready":
            overall_status = "degraded"
            messages.append("Agent system not ready")
        
    except Exception as e:
        logger.error(f"Agent client health check failed: {e}")
        components["strands_agent"] = {
            "status": "error",
            "error": str(e)
        }
        overall_status = "unhealthy"
        messages.append("Agent client unavailable")
    
    # Build response message
    if overall_status == "healthy":
        message = "All systems operational"
    elif overall_status == "degraded":
        message = f"System degraded: {'; '.join(messages)}"
    else:
        message = f"System unhealthy: {'; '.join(messages)}"
    
    return HealthResponse(
        status=overall_status,
        message=message,
        components=components
    )


@router.get("/proxy/config")
async def get_proxy_config() -> Dict[str, Any]:
    """
    Get proxy configuration (non-sensitive details only).
    
    Returns:
        Configuration details
    """
    try:
        session_manager = get_session_manager()
        agent_client = get_agent_client()
        
        return {
            "session_backend": session_manager.config.session_backend,
            "use_agentcore_memory": agent_client.config.use_agentcore_memory,
            "aws_region": agent_client.config.aws_region,
            "active_sessions": session_manager.get_active_sessions_count(),
            "cached_agents": agent_client.get_cached_agents_count(),
            "agent_timeout_seconds": agent_client.config.agent_timeout_seconds,
        }
        
    except Exception as e:
        logger.error(f"Failed to get proxy config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve proxy configuration"
        )


@router.post("/proxy/clear-cache")
async def clear_cache(session_id: str = None) -> Dict[str, Any]:
    """
    Clear cached sessions and agents.
    
    Args:
        session_id: Optional session ID to clear, or None to clear all
        
    Returns:
        Status message
    """
    try:
        session_manager = get_session_manager()
        agent_client = get_agent_client()
        
        sessions_before = session_manager.get_active_sessions_count()
        agents_before = agent_client.get_cached_agents_count()
        
        # Clear caches
        session_manager.clear_session_cache(session_id)
        agent_client.clear_agent_cache(session_id)
        
        sessions_after = session_manager.get_active_sessions_count()
        agents_after = agent_client.get_cached_agents_count()
        
        return {
            "success": True,
            "message": f"Cleared {sessions_before - sessions_after} sessions and {agents_before - agents_after} agents",
            "session_id": session_id,
            "sessions_cleared": sessions_before - sessions_after,
            "agents_cleared": agents_before - agents_after
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


@router.get("/proxy/metrics", response_model=MetricsResponse)
async def get_metrics_endpoint() -> MetricsResponse:
    """
    Get performance and operational metrics.
    
    Provides metrics including:
    - Request count and error rate
    - Response time percentiles (p50, p95, p99)
    - Errors by type
    - Circuit breaker state (if enabled)
    
    Returns:
        MetricsResponse with current metrics
    """
    try:
        # Import here to avoid circular imports
        from .logging_config import get_metrics
        
        metrics = get_metrics()
        metrics_data = metrics.get_metrics()
        
        # Get circuit breaker state if available
        circuit_breaker_state = None
        if hasattr(router, 'circuit_breaker'):
            circuit_breaker_state = router.circuit_breaker.get_state()
        
        return MetricsResponse(
            request_count=metrics_data["request_count"],
            error_count=metrics_data["error_count"],
            error_rate=metrics_data["error_rate"],
            avg_response_time_ms=metrics_data["avg_response_time_ms"],
            p50_response_time_ms=metrics_data.get("p50_response_time_ms", 0.0),
            p95_response_time_ms=metrics_data.get("p95_response_time_ms", 0.0),
            p99_response_time_ms=metrics_data.get("p99_response_time_ms", 0.0),
            errors_by_type=metrics_data["errors_by_type"],
            circuit_breaker_state=circuit_breaker_state
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )


@router.post("/proxy/metrics/reset")
async def reset_metrics() -> Dict[str, Any]:
    """
    Reset all metrics counters.
    
    Returns:
        Success message
    """
    try:
        from .logging_config import get_metrics
        
        metrics = get_metrics()
        metrics.reset()
        
        return {
            "success": True,
            "message": "All metrics have been reset"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset metrics"
        )

