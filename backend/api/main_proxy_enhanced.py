"""
Enhanced FastAPI proxy application with comprehensive logging and monitoring.

This is the production-ready version of the proxy with:
- Structured logging with correlation IDs
- Request/response timing and tracing
- Error handling middleware
- Circuit breaker for resilience
- Performance metrics collection
- Health monitoring
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from proxy import (
    ProxyConfig,
    initialize_session_manager,
    initialize_agent_client,
    router,
    configure_logging,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    CircuitBreakerMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks:
    - Configure logging
    - Initialize session manager
    - Initialize agent client
    - Setup monitoring
    """
    # Startup
    print("=" * 70)
    print("FastAPI Proxy Starting...")
    print("=" * 70)
    
    # Configure logging
    log_level = os.getenv("PROXY_LOG_LEVEL", "INFO")
    use_json = os.getenv("PROXY_LOG_FORMAT", "json") == "json"
    
    configure_logging(
        log_level=log_level,
        use_json=use_json
    )
    
    print(f"✓ Logging configured (level={log_level}, format={'json' if use_json else 'text'})")
    
    # Load configuration from environment
    config = ProxyConfig(
        session_backend=os.getenv("PROXY_SESSION_BACKEND", "file"),
        session_storage_dir=os.getenv("PROXY_SESSION_STORAGE_DIR"),
        session_s3_bucket=os.getenv("PROXY_SESSION_S3_BUCKET"),
        session_s3_prefix=os.getenv("PROXY_SESSION_S3_PREFIX", "sessions/"),
        use_agentcore_memory=os.getenv("PROXY_USE_AGENTCORE_MEMORY", "true").lower() == "true",
        memory_id=os.getenv("MEMORY_ID"),
        enable_error_details=os.getenv("PROXY_ENABLE_ERROR_DETAILS", "false").lower() == "true",
        agent_timeout_seconds=int(os.getenv("PROXY_AGENT_TIMEOUT_SECONDS", "60")),
        aws_region=os.getenv("AWS_REGION", "us-west-2")
    )
    
    print(f"✓ Configuration loaded (backend={config.session_backend}, agentcore={config.use_agentcore_memory})")
    
    # Initialize managers
    initialize_session_manager(config)
    print("✓ Session manager initialized")
    
    initialize_agent_client(config)
    print("✓ Agent client initialized")
    
    print("=" * 70)
    print("FastAPI Proxy Ready!")
    print("=" * 70)
    print(f"\nEndpoints:")
    print(f"  POST /api/chat           - Main chat endpoint")
    print(f"  GET  /api/health         - Health check")
    print(f"  GET  /api/proxy/config   - Configuration")
    print(f"  GET  /api/proxy/metrics  - Performance metrics")
    print(f"  POST /api/proxy/clear-cache - Clear caches")
    print(f"  GET  /docs               - API documentation")
    print("=" * 70)
    print()
    
    yield
    
    # Shutdown
    print("\n" + "=" * 70)
    print("FastAPI Proxy Shutting Down...")
    print("=" * 70)


# Create FastAPI application
app = FastAPI(
    title="Interlinked AOS Proxy API",
    description="FastAPI proxy maintaining backward compatibility while integrating with Strands Agents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware in order (outer to inner)
# 1. Request logging (outermost - logs all requests)
app.add_middleware(RequestLoggingMiddleware)

# 2. Circuit breaker (protects against cascading failures)
enable_circuit_breaker = os.getenv("PROXY_ENABLE_CIRCUIT_BREAKER", "false").lower() == "true"
if enable_circuit_breaker:
    circuit_breaker = CircuitBreakerMiddleware(
        app=app,
        failure_threshold=int(os.getenv("PROXY_CIRCUIT_BREAKER_THRESHOLD", "5")),
        recovery_timeout=int(os.getenv("PROXY_CIRCUIT_BREAKER_TIMEOUT", "60"))
    )
    app.add_middleware(
        CircuitBreakerMiddleware,
        failure_threshold=int(os.getenv("PROXY_CIRCUIT_BREAKER_THRESHOLD", "5")),
        recovery_timeout=int(os.getenv("PROXY_CIRCUIT_BREAKER_TIMEOUT", "60"))
    )
    # Store reference for metrics endpoint
    router.circuit_breaker = circuit_breaker

# 3. Error handling (innermost - catches all unhandled errors)
enable_error_details = os.getenv("PROXY_ENABLE_ERROR_DETAILS", "false").lower() == "true"
app.add_middleware(
    ErrorHandlingMiddleware,
    enable_error_details=enable_error_details
)

# Include router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint - provides API information."""
    return {
        "name": "Interlinked AOS Proxy API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "metrics": "/api/proxy/metrics",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "main_proxy_enhanced:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("PROXY_LOG_LEVEL", "info").lower()
    )

