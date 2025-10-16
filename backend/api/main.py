#!/usr/bin/env python3
"""
FastAPI backend for Agent Tool Architecture.
Provides REST API endpoints for agent interactions and graph data.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from agents.llm_agents.agent_orchestrator import AgentOrchestrator

# Load environment variables from backend directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Initialize FastAPI app
app = FastAPI(
    title="Agent Tool Architecture API",
    description="REST API for interacting with AI agents and Neo4j graph database",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent orchestrator
orchestrator = AgentOrchestrator()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    agent_type: str = "graph"

class ChatResponse(BaseModel):
    success: bool
    response: str
    agent_type: str
    timestamp: str

class GraphData(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class AgentInfo(BaseModel):
    name: str
    role: str
    available_tools: List[str]
    description: str

class SampleDataRequest(BaseModel):
    company_name: str
    company_size: str = "medium"  # small, medium, large
    generate_files: bool = True  # Whether to save files to disk

class SampleDataResponse(BaseModel):
    success: bool
    message: str
    data_generated: Dict[str, Any]

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Agent Tool Architecture API",
        "version": "1.0.0",
        "endpoints": {
            "agents": "/api/agents",
            "chat": "/api/chat",
            "graph": "/api/graph",
            "health": "/api/health",
            "generate_sample_data": "/api/generate-sample-data"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Neo4j connection
        agent = orchestrator.get_agent("extractor")
        test_result = agent.execute_tool("test_connection", {})
        
        neo4j_status = "connected" if test_result.get("success") else "disconnected"
        
        return {
            "status": "healthy", 
            "message": "API is running",
            "neo4j_status": neo4j_status,
            "neo4j_message": test_result.get("message", "Connection test completed")
        }
    except Exception as e:
        return {
            "status": "healthy", 
            "message": "API is running",
            "neo4j_status": "error",
            "neo4j_message": f"Neo4j connection error: {str(e)}"
        }

@app.get("/api/agents", response_model=Dict[str, AgentInfo])
async def list_agents():
    """Get information about all available agents."""
    try:
        agents_info = {}
        
        for agent_type in ["graph", "extractor", "analyzer", "admin"]:
            try:
                agent = orchestrator.get_agent(agent_type)
                agents_info[agent_type] = AgentInfo(
                    name=agent.name,
                    role=agent.role,
                    available_tools=agent.get_available_tools(),
                    description=f"{agent.name} - {agent.role} role with {len(agent.get_available_tools())} tools"
                )
            except Exception as e:
                agents_info[agent_type] = AgentInfo(
                    name=f"{agent_type.title()} Agent",
                    role="unknown",
                    available_tools=[],
                    description=f"Error loading {agent_type} agent: {str(e)}"
                )
        
        return agents_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(chat_message: ChatMessage):
    """Chat with a specific agent."""
    try:
        from datetime import datetime
        
        # Get the specified agent
        agent = orchestrator.get_agent(chat_message.agent_type)
        
        # Process the message
        response = agent.process_query(chat_message.message)
        
        return ChatResponse(
            success=True,
            response=response,
            agent_type=chat_message.agent_type,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process message with {chat_message.agent_type} agent: {str(e)}"
        )

@app.get("/api/graph", response_model=GraphData)
async def get_graph_data():
    """Get Neo4j graph data for visualization."""
    try:
        from config.database_config import get_database_config
        from neo4j import GraphDatabase
        
        # Get database configuration
        db_config = get_database_config()
        
        # Create Neo4j driver
        driver = GraphDatabase.driver(
            db_config.neo4j_uri,
            auth=(db_config.neo4j_username, db_config.neo4j_password)
        )
        
        all_nodes = []
        edges = []
        
        with driver.session() as session:
            # Get all nodes
            nodes_query = """
            MATCH (n)
            RETURN n, labels(n) as node_labels
            LIMIT 1000
            """
            nodes_result = session.run(nodes_query)
            
            for record in nodes_result:
                node = record["n"]
                node_labels = record["node_labels"]
                node_type = node_labels[0] if node_labels else "Unknown"
                
                # Get node properties
                node_props = dict(node)
                
                all_nodes.append({
                    "id": str(node.id),
                    "label": node_props.get("name", node_props.get("title", f"{node_type}_{node.id}")),
                    "type": node_type,
                    "properties": node_props
                })
            
            # Get all relationships
            relationships_query = """
            MATCH (a)-[r]->(b)
            RETURN a, r, b, type(r) as rel_type
            LIMIT 1000
            """
            relationships_result = session.run(relationships_query)
            
            for record in relationships_result:
                start_node = record["a"]
                end_node = record["b"]
                relationship = record["r"]
                rel_type = record["rel_type"]
                
                # Get relationship properties
                rel_props = dict(relationship)
                
                edges.append({
                    "id": f"{start_node.id}_{rel_type}_{end_node.id}",
                    "source": str(start_node.id),
                    "target": str(end_node.id),
                    "type": rel_type,
                    "properties": rel_props
                })
        
        driver.close()
        
        print(f"Retrieved {len(all_nodes)} nodes and {len(edges)} relationships from Neo4j")
        return GraphData(nodes=all_nodes, edges=edges)
        
    except Exception as e:
        print(f"Error in get_graph_data: {e}")
        import traceback
        traceback.print_exc()
        # Return empty graph data instead of raising exception
        return GraphData(nodes=[], edges=[])

@app.post("/api/generate-sample-data", response_model=SampleDataResponse)
async def generate_sample_data(request: SampleDataRequest):
    """Generate comprehensive organizational data for a company using the mock data generator and data loading orchestrator."""
    try:
        from tools.mock_generation import generate_mock_data
        from agents.data_agents.standalone_data_loader import StandaloneDataLoader
        
        # Validate company size
        if request.company_size not in ["small", "medium", "large"]:
            return SampleDataResponse(
                success=False,
                message=f"Invalid company size: {request.company_size}. Must be 'small', 'medium', or 'large'.",
                data_generated={}
            )
        
        # Generate comprehensive mock data
        print(f"Generating comprehensive organizational data for {request.company_name} ({request.company_size})...")
        
        # Always generate files (or pass None for default directory)
        result = generate_mock_data(request.company_name, request.company_size, None)
        
        if not result.get("success"):
            return SampleDataResponse(
                success=False,
                message="Failed to generate mock data",
                data_generated={}
            )
        
        # Initialize standalone data loader
        data_loader = StandaloneDataLoader()
        
        # Use standalone data loader to initialize graph with data
        print("Initializing graph with generated data using StandaloneDataLoader...")
        try:
            load_result = data_loader.initialize_graph_with_data(request.company_name)
        finally:
            # Always close the data loader connection
            data_loader.close()
        
        if not load_result.get("success"):
            return SampleDataResponse(
                success=False,
                message=f"Failed to load data into Neo4j: {load_result.get('error', 'Unknown error')}",
                data_generated={}
            )
        
        return SampleDataResponse(
            success=True,
            message=f"Successfully generated and loaded data for {request.company_name}",
            data_generated={
                "company_name": request.company_name,
                "company_size": request.company_size,
                "nodes_created": load_result.get("summary", {}).get("nodes_created", 0),
                "relationships_created": load_result.get("summary", {}).get("relationships_created", 0),
                "additional_relationships": load_result.get("summary", {}).get("additional_relationships", 0),
                "files_loaded": load_result.get("summary", {}).get("files_loaded", []),
                "final_status": load_result.get("final_status", {}),
                "files_generated": result.get("files", {}),
                "statistics": result.get("statistics", {}),
                "duration_seconds": load_result.get("summary", {}).get("duration_seconds", 0)
            }
        )
        
    except Exception as e:
        import traceback
        print(f"Error generating sample data: {e}")
        print(traceback.format_exc())
        return SampleDataResponse(
            success=False,
            message=f"Failed to generate sample data: {str(e)}",
            data_generated={}
        )

@app.post("/api/load-existing-data")
async def load_existing_data(request: SampleDataRequest):
    """Load existing data files into Neo4j without generating new data."""
    try:
        from agents.data_agents.data_loading_orchestrator import DataLoadingOrchestrator
        
        # Initialize data loading orchestrator
        orchestrator = DataLoadingOrchestrator()
        
        # Load existing data files
        print(f"Loading existing data files for {request.company_name}...")
        load_result = orchestrator.initialize_graph_with_data(request.company_name)
        
        if not load_result.get("success"):
            return SampleDataResponse(
                success=False,
                message=f"Failed to load existing data: {load_result.get('error', 'Unknown error')}",
                data_generated={}
            )
        
        return SampleDataResponse(
            success=True,
            message=f"Successfully loaded existing data for {request.company_name}",
            data_generated={
                "company_name": request.company_name,
                "nodes_created": load_result.get("summary", {}).get("nodes_created", 0),
                "relationships_created": load_result.get("summary", {}).get("relationships_created", 0),
                "additional_relationships": load_result.get("summary", {}).get("additional_relationships", 0),
                "files_loaded": load_result.get("summary", {}).get("files_loaded", []),
                "final_status": load_result.get("final_status", {}),
                "duration_seconds": load_result.get("summary", {}).get("duration_seconds", 0)
            }
        )
        
    except Exception as e:
        import traceback
        print(f"Error loading existing data: {e}")
        print(traceback.format_exc())
        return SampleDataResponse(
            success=False,
            message=f"Failed to load existing data: {str(e)}",
            data_generated={}
        )

@app.get("/api/available-data-files")
async def get_available_data_files():
    """Get information about available data files."""
    try:
        from agents.data_agents.data_loading_orchestrator import DataLoadingOrchestrator
        
        orchestrator = DataLoadingOrchestrator()
        result = orchestrator.get_available_data_files()
        
        return {
            "success": result.get("success", False),
            "data": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get available data files: {str(e)}"
        }

@app.get("/api/graph/cypher")
async def execute_cypher_query(query: str):
    """Execute a custom Cypher query."""
    try:
        agent = orchestrator.get_agent("extractor")
        result = agent.execute_tool("advanced_query", {"cypher_query": query})
        
        return {"success": result.get("success", False), "data": result.get("results", [])}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")

@app.get("/api/agents/{agent_type}/tools")
async def get_agent_tools(agent_type: str):
    """Get available tools for a specific agent."""
    try:
        agent = orchestrator.get_agent(agent_type)
        tools = agent.get_available_tools()
        
        return {
            "agent_type": agent_type,
            "tools": tools,
            "tool_count": len(tools)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tools for {agent_type}: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
