"""
FastAPI middleware for request tracking, logging, and error handling.

Provides request/response logging, timing, correlation IDs, and
error handling with proper status code mapping.
"""

import time
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import (
    set_request_context,
    clear_request_context,
    get_context_logger,
    get_metrics
)
from .models import ErrorResponse

logger = get_context_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging and timing.
    
    Logs all incoming requests and outgoing responses with:
    - Request method, path, and headers
    - Response status code and timing
    - Correlation IDs for tracing
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through logging middleware.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint
            
        Returns:
            Response with added headers and logging
        """
        start_time = time.time()
        
        # Generate correlation ID
        request_id = request.headers.get("X-Request-ID")
        request_id, _ = set_request_context(request_id=request_id)
        
        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=str(request.url.query),
            client_host=request.client.host if request.client else "unknown"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate timing
            process_time_ms = (time.time() - start_time) * 1000
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time_ms=round(process_time_ms, 2)
            )
            
            # Record metrics
            metrics = get_metrics()
            metrics.record_request(
                response_time_ms=process_time_ms,
                success=(200 <= response.status_code < 400),
                error_type=None if (200 <= response.status_code < 400) else f"HTTP_{response.status_code}"
            )
            
            return response
            
        except Exception as e:
            # Calculate timing
            process_time_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {type(e).__name__}: {str(e)}",
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__,
                error_message=str(e),
                process_time_ms=round(process_time_ms, 2)
            )
            
            # Record metrics
            metrics = get_metrics()
            metrics.record_request(
                response_time_ms=process_time_ms,
                success=False,
                error_type=type(e).__name__
            )
            
            # Re-raise to be handled by error handler
            raise
            
        finally:
            # Clear request context
            clear_request_context()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for global error handling.
    
    Catches unhandled exceptions and converts them to appropriate
    HTTP responses with proper status codes and error messages.
    """
    
    def __init__(self, app, enable_error_details: bool = False):
        """
        Initialize error handling middleware.
        
        Args:
            app: FastAPI application
            enable_error_details: Whether to include detailed error info in responses
        """
        super().__init__(app)
        self.enable_error_details = enable_error_details
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through error handling middleware.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint
            
        Returns:
            Response or error response
        """
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            return self._handle_exception(request, e)
    
    def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handle exception and return appropriate error response.
        
        Args:
            request: FastAPI request
            exc: Exception that occurred
            
        Returns:
            JSONResponse with error details
        """
        # Import here to avoid circular imports
        from .client import (
            AgentTimeoutError,
            AgentInvocationError,
            AgentConfigurationError
        )
        
        # Map exception types to status codes
        if isinstance(exc, AgentTimeoutError):
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
            error_message = "The request took too long to process. Please try again."
            error_type = "TIMEOUT"
            
        elif isinstance(exc, AgentConfigurationError):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            error_message = "Agent system is temporarily unavailable. Please try again later."
            error_type = "SERVICE_UNAVAILABLE"
            
        elif isinstance(exc, AgentInvocationError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_message = "An error occurred while processing your request. Please try again."
            error_type = "AGENT_ERROR"
            
        elif isinstance(exc, ValueError):
            status_code = status.HTTP_400_BAD_REQUEST
            error_message = str(exc)
            error_type = "VALIDATION_ERROR"
            
        else:
            # Generic internal server error
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_message = "An unexpected error occurred. Please try again."
            error_type = "INTERNAL_ERROR"
        
        # Build error response
        error_response = ErrorResponse(
            error=error_type,
            message=error_message,
            path=str(request.url.path)
        )
        
        # Add detailed error info if enabled
        if self.enable_error_details:
            error_response.detail = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc()
            }
        
        # Log error
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=str(request.url.path),
            status_code=status_code
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict(exclude_none=True)
        )


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """
    Circuit breaker middleware for resilience.
    
    Tracks error rates and temporarily blocks requests if error
    rate exceeds threshold, allowing the system to recover.
    """
    
    def __init__(
        self,
        app,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker middleware.
        
        Args:
            app: FastAPI application
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Number of test calls in half-open state
        """
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through circuit breaker.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint
            
        Returns:
            Response or circuit breaker error
        """
        # Check circuit state
        if self.state == "OPEN":
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                # Circuit is still open
                logger.warning("Circuit breaker is OPEN - rejecting request")
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "error": "SERVICE_UNAVAILABLE",
                        "message": "System is temporarily unavailable due to high error rate. Please try again later.",
                        "circuit_state": "OPEN"
                    }
                )
        
        try:
            # Allow request through
            response = await call_next(request)
            
            # Check if successful
            if 200 <= response.status_code < 400:
                # Success - handle based on state
                if self.state == "HALF_OPEN":
                    self.half_open_calls += 1
                    if self.half_open_calls >= self.half_open_max_calls:
                        # Recovery successful
                        self.state = "CLOSED"
                        self.failure_count = 0
                        logger.info("Circuit breaker recovered - entering CLOSED state")
                
                elif self.state == "CLOSED":
                    # Reset failure count on success
                    self.failure_count = max(0, self.failure_count - 1)
            
            else:
                # Non-success status code
                self._record_failure()
            
            return response
            
        except Exception as e:
            # Exception occurred
            self._record_failure()
            raise
    
    def _record_failure(self):
        """Record a failure and update circuit state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "HALF_OPEN":
            # Failure during recovery - reopen circuit
            self.state = "OPEN"
            logger.warning("Circuit breaker reopened due to failure during recovery")
        
        elif self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            # Threshold exceeded - open circuit
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened due to {self.failure_count} failures",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )
    
    def get_state(self) -> dict:
        """
        Get current circuit breaker state.
        
        Returns:
            Dictionary with circuit breaker state
        """
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "time_until_half_open": max(
                0,
                self.recovery_timeout - (time.time() - self.last_failure_time)
            ) if self.state == "OPEN" else 0
        }

