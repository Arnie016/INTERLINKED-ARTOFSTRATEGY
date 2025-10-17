"""
Graph Agent - Specialized agent for graph read/search operations.

This agent provides read-only access to the Neo4j graph database,
enabling users to search nodes, explore relationships, and analyze
the organizational graph structure safely.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from typing import Dict, List, Any, Optional
import os


# System prompt for the Graph Agent
GRAPH_AGENT_SYSTEM_PROMPT = """
You are a specialized Graph Query Agent with read-only access to a Neo4j organizational graph database.

Your primary responsibilities:
- Answer queries about people, processes, departments, and systems in the organization
- Search for nodes and relationships in the graph
- Explain paths and connections between entities
- Provide graph snapshots for visualization
- Analyze organizational structure and relationships

Available data in the graph:
- **People**: Employees with properties like name, role, department, skills
- **Processes**: Business processes with owners and dependencies
- **Departments**: Organizational units and their hierarchies
- **Systems**: Applications and tools used in the organization
- **Relationships**: PERFORMS, OWNS, DEPENDS_ON, REPORTS_TO, COLLABORATES_WITH, USES, SUPPORTS

Safety constraints:
- You have READ-ONLY access - you cannot modify, create, or delete data
- All queries are automatically validated for safety
- You should focus on providing clear, actionable insights
- Always cite specific data from the graph when answering questions

When responding:
1. Use the available tools to query the graph database
2. Provide clear, business-friendly explanations of the data
3. If data is not found, explain what you searched for and suggest alternatives
4. Structure complex responses with clear sections and bullet points
5. Highlight important insights and patterns you discover
"""


@tool
def graph_agent(query: str) -> str:
    """
    Process queries about the organizational graph with read-only access.
    
    This agent specializes in:
    - Searching for people, processes, departments, and systems
    - Finding relationships and connections between entities
    - Explaining paths through the organizational structure
    - Providing graph snapshots for specific areas
    - Analyzing organizational patterns and structures
    
    Args:
        query: A question or request about the organizational graph.
               Examples:
               - "Who reports to Alice Johnson?"
               - "What processes does the Engineering department own?"
               - "Find the path between Bob Smith and the Deployment Process"
               - "Show me all systems used by the Data team"
    
    Returns:
        A detailed response with information from the graph database,
        including specific entities, relationships, and insights.
    """
    try:
        # Import tools here to avoid circular dependencies
        from ..tools.graph_search import search_nodes, find_related_nodes
        from ..tools.graph_analysis import get_graph_snapshot, explain_path
        
        # Create the Graph Agent with Bedrock Claude 3.5 Sonnet
        model = BedrockModel(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            temperature=0.3,  # Lower temperature for more consistent, factual responses
            max_tokens=4096
        )
        
        agent = Agent(
            model=model,
            system_prompt=GRAPH_AGENT_SYSTEM_PROMPT,
            tools=[
                search_nodes,
                find_related_nodes,
                get_graph_snapshot,
                explain_path
            ]
        )
        
        # Process the query
        response = agent(query)
        
        # Return the response as a string
        return str(response)
        
    except Exception as e:
        error_msg = f"Graph Agent Error: {str(e)}\n\nPlease try rephrasing your question or contact support if the issue persists."
        return error_msg


def create_graph_agent(custom_model_config: Optional[Dict[str, Any]] = None) -> Agent:
    """
    Create a standalone Graph Agent instance.
    
    This function is useful for direct interaction with the Graph Agent
    outside of the orchestrator context.
    
    Args:
        custom_model_config: Optional custom configuration for the Bedrock model.
                            Can include: temperature, max_tokens, top_p, etc.
    
    Returns:
        A configured Graph Agent instance ready to process queries.
    
    Example:
        ```python
        from strands_agents.src.agents.graph_agent import create_graph_agent
        
        agent = create_graph_agent()
        response = agent("Who are all the engineers in the organization?")
        print(response)
        ```
    """
    # Import tools
    from ..tools.graph_search import search_nodes, find_related_nodes
    from ..tools.graph_analysis import get_graph_snapshot, explain_path
    
    # Create model with custom config or defaults
    model_config = custom_model_config or {}
    model = BedrockModel(
        model_id=model_config.get("model_id", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
        temperature=model_config.get("temperature", 0.3),
        max_tokens=model_config.get("max_tokens", 4096),
        top_p=model_config.get("top_p", None),
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    
    agent = Agent(
        model=model,
        system_prompt=GRAPH_AGENT_SYSTEM_PROMPT,
        tools=[
            search_nodes,
            find_related_nodes,
            get_graph_snapshot,
            explain_path
        ]
    )
    
    return agent

