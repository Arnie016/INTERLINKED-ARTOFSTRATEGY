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
    """Generate comprehensive organizational data for a company using the mock data generator."""
    try:
        from tools.mock_generation import generate_mock_data
        
        # Validate company size
        if request.company_size not in ["small", "medium", "large"]:
            return SampleDataResponse(
                success=False,
                message=f"Invalid company size: {request.company_size}. Must be 'small', 'medium', or 'large'.",
                data_generated={}
            )
        
        # Get the admin agent for clearing data (has reset_graph permission)
        admin_agent = orchestrator.get_agent("admin")
        
        # Get the extractor agent for data insertion
        agent = orchestrator.get_agent("extractor")
        
        # First, clear existing data using admin agent
        print(f"Clearing existing data for {request.company_name}...")
        clear_result = admin_agent.execute_tool("reset_graph", {"confirm": True})
        
        if not clear_result.get("success"):
            return SampleDataResponse(
                success=False,
                message=f"Failed to clear existing data: {clear_result.get('error', 'Unknown error')}",
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
        
        data = result["data"]
        
        # Insert data into Neo4j
        print("Inserting data into Neo4j...")
        
        # Insert departments
        dept_nodes = {}
        for dept in data["departments"]:
            dept_result = agent.execute_tool("add_node", {
                "node_type": "Department",
                "properties": {
                    "name": dept["name"],
                    "description": dept.get("description", ""),
                    "budget": dept.get("budget", 0),
                    "head": dept.get("head", ""),
                    "location": dept.get("location", ""),
                    "size": dept.get("headcount", 0),
                    "status": dept.get("status", "active")
                }
            })
            if dept_result.get("success"):
                dept_nodes[dept["name"]] = dept_result.get("node")
        
        print(f"✓ Inserted {len(dept_nodes)} departments into Neo4j")
        
        # Insert employees
        emp_nodes = {}
        for emp in data["employees"]:
            emp_result = agent.execute_tool("add_node", {
                "node_type": "Person",
                "properties": {
                    "name": emp["name"],
                    "email": emp["email"],
                    "role": emp["role"],
                    "department": emp["department"],
                    "location": emp.get("location", ""),
                    "status": emp.get("status", "active"),
                    "skills": ",".join(emp.get("skills", [])),
                    "tenure_years": emp.get("tenure_years", 0),
                    "level": emp.get("level", "")
                }
            })
            if emp_result.get("success"):
                emp_nodes[emp["name"]] = emp_result.get("node")
        
        print(f"✓ Inserted {len(emp_nodes)} employees into Neo4j")
        
        # Insert projects
        project_nodes = {}
        for project in data["projects"]:
            project_result = agent.execute_tool("add_node", {
                "node_type": "Project",
                "properties": {
                    "name": project["name"],
                    "description": project.get("description", ""),
                    "status": project.get("status", "active"),
                    "start_date": project.get("start_date", ""),
                    "end_date": project.get("end_date", ""),
                    "budget": project.get("budget", 0),
                    "priority": project.get("priority", "medium"),
                    "department": project.get("department", ""),
                    "sponsor": project.get("sponsor", ""),
                    "manager": project.get("manager", "")
                }
            })
            if project_result.get("success"):
                project_nodes[project["name"]] = project_result.get("node")
        
        print(f"✓ Inserted {len(project_nodes)} projects into Neo4j")
        
        # Insert systems
        system_nodes = {}
        for system in data["systems"]:
            system_result = agent.execute_tool("add_node", {
                "node_type": "System",
                "properties": {
                    "name": system["name"],
                    "type": system.get("type", ""),
                    "vendor": system.get("vendor", ""),
                    "version": system.get("version", ""),
                    "status": system.get("status", "active"),
                    "criticality": system.get("criticality", "medium"),
                    "owner": system.get("owner", ""),
                    "department": system.get("department", "")
                }
            })
            if system_result.get("success"):
                system_nodes[system["name"]] = system_result.get("node")
        
        print(f"✓ Inserted {len(system_nodes)} systems into Neo4j")
        
        # Insert processes
        process_nodes = {}
        for process in data["processes"]:
            process_result = agent.execute_tool("add_node", {
                "node_type": "Process",
                "properties": {
                    "name": process["name"],
                    "description": process.get("description", ""),
                    "category": process.get("category", ""),
                    "owner": process.get("owner", ""),
                    "department": process.get("department", ""),
                    "frequency": process.get("frequency", ""),
                    "complexity": process.get("complexity", "medium"),
                    "automation_level": process.get("automation_level", "manual"),
                    "status": process.get("status", "active")
                }
            })
            if process_result.get("success"):
                process_nodes[process["name"]] = process_result.get("node")
        
        print(f"✓ Inserted {len(process_nodes)} processes into Neo4j")
        
        # Insert relationships
        relationships_created = 0
        
        # Department membership
        for rel in data["relationships"]["department_membership"]:
            if rel["from"] in emp_nodes and rel["to"] in dept_nodes:
                agent.execute_tool("add_relationship", {
                    "from_node": emp_nodes[rel["from"]],
                    "to_node": dept_nodes[rel["to"]],
                    "relationship_type": "BELONGS_TO",
                    "properties": {"allocation_percentage": rel.get("allocation_percentage", 100)}
                })
                relationships_created += 1
        
        # Reporting relationships
        for rel in data["relationships"]["reporting"]:
            if rel["from"] in emp_nodes and rel["to"] in emp_nodes:
                agent.execute_tool("add_relationship", {
                    "from_node": emp_nodes[rel["from"]],
                    "to_node": emp_nodes[rel["to"]],
                    "relationship_type": "REPORTS_TO",
                    "properties": {"relationship_type": rel.get("relationship_type", "direct")}
                })
                relationships_created += 1
        
        # Process ownership
        for rel in data["relationships"]["process_ownership"]:
            if rel["from"] in emp_nodes and rel["to"] in process_nodes:
                agent.execute_tool("add_relationship", {
                    "from_node": emp_nodes[rel["from"]],
                    "to_node": process_nodes[rel["to"]],
                    "relationship_type": "OWNS",
                    "properties": {"ownership_type": rel.get("ownership_type", "primary")}
                })
                relationships_created += 1
        
        # Process participation
        for rel in data["relationships"]["collaboration"]:
            if rel["from"] in emp_nodes and rel["to"] in process_nodes:
                agent.execute_tool("add_relationship", {
                    "from_node": emp_nodes[rel["from"]],
                    "to_node": process_nodes[rel["to"]],
                    "relationship_type": "PERFORMS",
                    "properties": {"role": rel.get("role", "participant")}
                })
                relationships_created += 1
        
        # System usage
        for rel in data["relationships"]["system_usage"]:
            if rel["from"] in emp_nodes and rel["to"] in system_nodes:
                agent.execute_tool("add_relationship", {
                    "from_node": emp_nodes[rel["from"]],
                    "to_node": system_nodes[rel["to"]],
                    "relationship_type": "USES",
                    "properties": {
                        "usage_frequency": rel.get("usage_frequency", "daily"),
                        "proficiency": rel.get("proficiency", "intermediate")
                    }
                })
                relationships_created += 1
        
        # Project assignments
        for rel in data["relationships"]["project_assignments"]:
            if rel["from"] in emp_nodes and rel["to"] in project_nodes:
                agent.execute_tool("add_relationship", {
                    "from_node": emp_nodes[rel["from"]],
                    "to_node": project_nodes[rel["to"]],
                    "relationship_type": "WORKS_ON",
                    "properties": {
                        "role": rel.get("role", "contributor"),
                        "allocation_percentage": rel.get("allocation_percentage", 50)
                    }
                })
                relationships_created += 1
        
        print(f"✓ Created {relationships_created} relationships in Neo4j")
        
        return SampleDataResponse(
            success=True,
            message=f"Successfully generated comprehensive data for {request.company_name}",
            data_generated={
                "company_name": request.company_name,
                "company_size": request.company_size,
                "departments_created": len(dept_nodes),
                "employees_created": len(emp_nodes),
                "projects_created": len(project_nodes),
                "systems_created": len(system_nodes),
                "processes_created": len(process_nodes),
                "relationships_created": relationships_created,
                "total_nodes": len(dept_nodes) + len(emp_nodes) + len(project_nodes) + len(system_nodes) + len(process_nodes),
                "files_generated": result.get("files", {}),
                "statistics": result.get("statistics", {})
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
