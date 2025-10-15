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
from agents.agent_orchestrator import AgentOrchestrator

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
    departments: int = 5
    people_per_department: int = 8
    processes_per_department: int = 3

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
        # Use extractor agent to get graph data
        agent = orchestrator.get_agent("extractor")
        
        # Get all nodes of different types
        all_nodes = []
        node_types = ["Person", "Department", "Process", "Project"]
        
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
                print(f"Warning: Could not fetch {node_type} nodes: {e}")
        
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
            print(f"Warning: Could not fetch relationships: {e}")
        
        return GraphData(nodes=all_nodes, edges=edges)
        
    except Exception as e:
        print(f"Error in get_graph_data: {e}")
        # Return empty graph data instead of raising exception
        return GraphData(nodes=[], edges=[])

@app.post("/api/generate-sample-data", response_model=SampleDataResponse)
async def generate_sample_data(request: SampleDataRequest):
    """Generate sample organizational data for a company."""
    try:
        # Get the extractor agent for data generation
        agent = orchestrator.get_agent("extractor")
        
        # First, clear existing data
        print(f"Clearing existing data for {request.company_name}...")
        clear_result = agent.execute_tool("reset_graph", {"confirm": True})
        
        if not clear_result.get("success"):
            return SampleDataResponse(
                success=False,
                message=f"Failed to clear existing data: {clear_result.get('error', 'Unknown error')}",
                data_generated={}
            )
        
        # Generate sample data using the agent
        print(f"Generating sample data for {request.company_name}...")
        
        # Create departments
        departments = []
        for i in range(request.departments):
            dept_name = f"{request.company_name} Department {i+1}"
            dept_result = agent.execute_tool("add_node", {
                "node_type": "Department",
                "properties": {
                    "name": dept_name,
                    "company": request.company_name,
                    "department_id": f"dept_{i+1}",
                    "budget": 100000 + (i * 50000),
                    "headcount": request.people_per_department
                }
            })
            if dept_result.get("success"):
                departments.append(dept_result.get("node"))
        
        # Create people for each department
        people = []
        for dept_idx, dept in enumerate(departments):
            for person_idx in range(request.people_per_department):
                person_name = f"Person {person_idx+1} from {dept['name']}"
                person_result = agent.execute_tool("add_node", {
                    "node_type": "Person",
                    "properties": {
                        "name": person_name,
                        "email": f"person{person_idx+1}.dept{dept_idx+1}@{request.company_name.lower().replace(' ', '')}.com",
                        "role": f"Role {person_idx+1}",
                        "department": dept['name'],
                        "employee_id": f"emp_{dept_idx+1}_{person_idx+1}",
                        "salary": 50000 + (person_idx * 10000)
                    }
                })
                if person_result.get("success"):
                    people.append(person_result.get("node"))
                    
                    # Create relationship between person and department
                    agent.execute_tool("add_relationship", {
                        "from_node": person_result.get("node"),
                        "to_node": dept,
                        "relationship_type": "WORKS_IN",
                        "properties": {"since": "2024-01-01"}
                    })
        
        # Create processes for each department
        processes = []
        for dept_idx, dept in enumerate(departments):
            for process_idx in range(request.processes_per_department):
                process_name = f"Process {process_idx+1} in {dept['name']}"
                process_result = agent.execute_tool("add_node", {
                    "node_type": "Process",
                    "properties": {
                        "name": process_name,
                        "department": dept['name'],
                        "process_id": f"proc_{dept_idx+1}_{process_idx+1}",
                        "status": "active",
                        "priority": "medium"
                    }
                })
                if process_result.get("success"):
                    processes.append(process_result.get("node"))
                    
                    # Create relationship between process and department
                    agent.execute_tool("add_relationship", {
                        "from_node": process_result.get("node"),
                        "to_node": dept,
                        "relationship_type": "OWNED_BY",
                        "properties": {"created": "2024-01-01"}
                    })
        
        # Create some inter-department relationships
        for i in range(min(3, len(departments) - 1)):
            if i + 1 < len(departments):
                agent.execute_tool("add_relationship", {
                    "from_node": departments[i],
                    "to_node": departments[i + 1],
                    "relationship_type": "DEPENDS_ON",
                    "properties": {"dependency_type": "data_flow"}
                })
        
        return SampleDataResponse(
            success=True,
            message=f"Successfully generated sample data for {request.company_name}",
            data_generated={
                "company_name": request.company_name,
                "departments_created": len(departments),
                "people_created": len(people),
                "processes_created": len(processes),
                "total_nodes": len(departments) + len(people) + len(processes)
            }
        )
        
    except Exception as e:
        print(f"Error generating sample data: {e}")
        return SampleDataResponse(
            success=False,
            message=f"Failed to generate sample data: {str(e)}",
            data_generated={}
        )

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
