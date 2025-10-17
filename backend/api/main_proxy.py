#!/usr/bin/env python3
"""
FastAPI backend with Strands Agents proxy.

This is the new main entry point that uses the Strands agent proxy
while maintaining backward compatibility with the existing frontend.

Key features:
- Session management for conversation context
- Strands agent orchestration with AgentCore Memory
- Backward-compatible /api/chat endpoint
- Health monitoring and configuration endpoints
"""

import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Add strands_agents to path
strands_agents_path = Path(__file__).parent.parent.parent / "strands_agents" / "src"
sys.path.insert(0, str(strands_agents_path))

# Add parent directory to path for legacy imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Import proxy components
from proxy.models import ProxyConfig
from proxy.session import initialize_session_manager
from proxy.client import initialize_agent_client
from proxy.router import router as proxy_router

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    
    Handles startup and shutdown tasks:
    - Initialize session manager
    - Initialize agent client
    - Setup logging and monitoring
    """
    logger.info("Starting FastAPI application with Strands agent proxy")
    
    # Load configuration
    config = ProxyConfig(
        session_backend=os.getenv("PROXY_SESSION_BACKEND", "file"),
        session_storage_dir=os.getenv("PROXY_SESSION_STORAGE_DIR"),
        session_s3_bucket=os.getenv("PROXY_SESSION_S3_BUCKET"),
        session_s3_prefix=os.getenv("PROXY_SESSION_S3_PREFIX", "interlinked-aos-dev/sessions/"),
        use_agentcore_memory=os.getenv("PROXY_USE_AGENTCORE_MEMORY", "true").lower() == "true",
        memory_id=os.getenv("MEMORY_ID"),
        enable_request_logging=os.getenv("PROXY_ENABLE_REQUEST_LOGGING", "true").lower() == "true",
        enable_error_details=os.getenv("PROXY_ENABLE_ERROR_DETAILS", "true").lower() == "true",
        enable_performance_metrics=os.getenv("PROXY_ENABLE_PERFORMANCE_METRICS", "true").lower() == "true",
        agent_timeout_seconds=int(os.getenv("PROXY_AGENT_TIMEOUT_SECONDS", "60")),
        aws_region=os.getenv("AWS_REGION", "us-west-2"),
    )
    
    logger.info(f"Proxy configuration loaded: backend={config.session_backend}, use_agentcore={config.use_agentcore_memory}")
    
    # Initialize managers
    try:
        initialize_session_manager(config)
        logger.info("Session manager initialized successfully")
        
        initialize_agent_client(config)
        logger.info("Agent client initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize managers: {e}", exc_info=True)
        raise
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Initialize FastAPI app
app = FastAPI(
    title="Interlinked AOS API (Strands Proxy)",
    description="REST API for AI agent interactions with Strands Agents backend",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include proxy router
app.include_router(proxy_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Interlinked AOS API (Strands Proxy)",
        "version": "2.0.0",
        "backend": "Strands Agents with AgentCore",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "config": "/api/proxy/config",
            "docs": "/docs"
        }
    }


# Legacy endpoints for backward compatibility
# These import the old agent orchestrator for now

@app.get("/api/agents")
async def list_agents():
    """
    Get information about available agents (legacy endpoint).
    
    This provides backward compatibility but now returns info
    about the Strands orchestrator system.
    """
    return {
        "orchestrator": {
            "name": "Orchestrator Agent",
            "role": "Routes requests to specialized agents",
            "available_tools": [
                "graph_agent",
                "analyzer_agent",
                "extractor_agent",
                "admin_agent"
            ],
            "description": "Main entry point that intelligently routes to specialized agents"
        },
        "graph": {
            "name": "Graph Agent",
            "role": "Read-only graph queries",
            "available_tools": [
                "search_nodes",
                "find_related_nodes",
                "get_graph_snapshot",
                "explain_path"
            ],
            "description": "Searches and explores the organizational graph"
        },
        "analyzer": {
            "name": "Analyzer Agent",
            "role": "Advanced analytics",
            "available_tools": [
                "centrality_analysis",
                "community_detection",
                "graph_stats"
            ],
            "description": "Performs advanced graph analytics and insights"
        },
        "extractor": {
            "name": "Extractor Agent",
            "role": "Data ingestion",
            "available_tools": [
                "create_node",
                "create_relationship",
                "bulk_ingest"
            ],
            "description": "Creates and modifies graph data"
        },
        "admin": {
            "name": "Admin Agent",
            "role": "Administrative operations",
            "available_tools": [
                "reindex",
                "migrate_labels",
                "maintenance_cleanup_orphan_nodes"
            ],
            "description": "Performs privileged administrative operations"
        }
    }


@app.get("/api/graph")
async def get_graph_data():
    """
    Get Neo4j graph data for visualization (legacy endpoint).
    
    This is kept for backward compatibility with the frontend visualization.
    """
    from agents.agent_orchestrator import AgentOrchestrator
    
    try:
        orchestrator = AgentOrchestrator()
        agent = orchestrator.get_agent("extractor")
        
        # Get all nodes of different types
        all_nodes = []
        node_types = ["Person", "Department", "Process", "Project", "System"]
        
        for node_type in node_types:
            try:
                nodes_result = agent.execute_tool("list_nodes", {"node_type": node_type, "limit": 50})
                if nodes_result.get("success"):
                    for node in nodes_result.get("nodes", []):
                        all_nodes.append({
                            "id": str(node.get("id", "")),
                            "label": node.get("name", node.get("title", "Unknown")),
                            "type": node_type,
                            "properties": node
                        })
            except Exception as e:
                logger.warning(f"Could not fetch {node_type} nodes: {e}")
        
        # Get relationships
        edges = []
        try:
            relationships_result = agent.execute_tool("list_relationships", {"limit": 100})
            if relationships_result.get("success"):
                for rel in relationships_result.get("relationships", []):
                    edges.append({
                        "id": str(rel.get("id", "")),
                        "source": str(rel.get("start_node_id", "")),
                        "target": str(rel.get("end_node_id", "")),
                        "type": rel.get("type", "RELATES_TO"),
                        "properties": rel
                    })
        except Exception as e:
            logger.warning(f"Could not fetch relationships: {e}")
        
        return {"nodes": all_nodes, "edges": edges}
        
    except Exception as e:
        logger.error(f"Error in get_graph_data: {e}")
        return {"nodes": [], "edges": []}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    
    uvicorn.run(
        "main_proxy:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

