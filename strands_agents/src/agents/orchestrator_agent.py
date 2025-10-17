"""
Orchestrator Agent - Main entry point using the "Agents as Tools" pattern.

This agent routes user queries to specialized agents based on intent detection,
integrating their responses to provide comprehensive answers to complex questions.
"""

from strands import Agent
from strands.models import BedrockModel
from typing import Dict, Any, Optional
import os

# Import specialized agent tools
from .graph_agent import graph_agent
from .analyzer_agent import analyzer_agent
from .extractor_agent import extractor_agent
from .admin_agent import admin_agent


# System prompt for the Orchestrator Agent
ORCHESTRATOR_SYSTEM_PROMPT = """
You are the Orchestrator Agent, the main entry point for users interacting with the organizational graph system.

Your role is to understand user queries and route them to the appropriate specialized agents:

**Available Specialized Agents:**

1. **Graph Agent** (graph_agent)
   - Use for: Queries about people, processes, departments, systems
   - Use for: Searching nodes, exploring relationships, finding paths
   - Use for: Read-only operations and basic graph exploration
   - Examples: "Who reports to Alice?", "What processes does Engineering own?"

2. **Analyzer Agent** (analyzer_agent)
   - Use for: Advanced analytics and pattern detection
   - Use for: Centrality analysis, community detection, statistics
   - Use for: Bottleneck identification and performance metrics
   - Examples: "Who are the key influencers?", "Find organizational bottlenecks"

3. **Extractor Agent** (extractor_agent)
   - Use for: Creating new nodes and relationships
   - Use for: Data ingestion and bulk imports
   - Use for: Write operations to the graph
   - Examples: "Add a new employee", "Create a relationship between X and Y"

4. **Admin Agent** (admin_agent)
   - Use for: Database maintenance and administrative tasks
   - Use for: Reindexing, schema migrations, cleanup operations
   - Use for: Privileged operations (requires admin role)
   - Examples: "Reindex Person nodes", "Clean up orphaned data"

**Routing Guidelines:**

- For simple information retrieval → use **graph_agent**
- For analytical questions requiring metrics → use **analyzer_agent**
- For creating or modifying data → use **extractor_agent**
- For administrative operations → use **admin_agent** (check permissions first)

**Multi-Agent Coordination:**

You can use multiple specialized agents for complex queries:
1. Break down complex questions into sub-questions
2. Route each sub-question to the appropriate agent
3. Integrate the responses into a cohesive answer
4. Ensure context flows between agent calls

**Response Guidelines:**

1. Always explain which agent(s) you're using and why
2. Provide comprehensive answers that address all aspects of the query
3. If a query is ambiguous, ask clarifying questions before routing
4. Combine results from multiple agents when needed
5. Present information in a clear, business-friendly format
6. Highlight key insights and actionable recommendations

**Safety and Permissions:**

- Verify user has appropriate permissions before using extractor or admin agents
- Warn users about destructive operations
- Recommend dry-run for admin operations
- Respect read-only constraints for regular users
"""


def create_orchestrator_agent(
    user_role: str = "user",
    custom_model_config: Optional[Dict[str, Any]] = None
) -> Agent:
    """
    Create the Orchestrator Agent with access to all specialized agents.
    
    This agent intelligently routes user queries to the appropriate
    specialized agent(s) and integrates their responses.
    
    Args:
        user_role: The role of the user ('user', 'extractor', 'admin').
                  Determines which agents are available.
        custom_model_config: Optional custom configuration for the Bedrock model.
    
    Returns:
        A configured Orchestrator Agent ready to process user queries.
    
    Example:
        ```python
        from strands_agents.src.agents.orchestrator_agent import create_orchestrator_agent
        
        # Create orchestrator for a regular user
        orchestrator = create_orchestrator_agent(user_role="user")
        
        # Process a complex query
        response = orchestrator(
            "Who are the most central people in Engineering, and what processes do they own?"
        )
        print(response)
        ```
    """
    # Determine which agent tools to include based on user role
    available_agents = [graph_agent, analyzer_agent]
    
    if user_role in ["extractor", "admin"]:
        available_agents.append(extractor_agent)
    
    if user_role == "admin":
        available_agents.append(admin_agent)
    
    # Create model with custom config or defaults
    model_config = custom_model_config or {}
    model = BedrockModel(
        model_id=model_config.get("model_id", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
        temperature=model_config.get("temperature", 0.5),  # Moderate temperature for reasoning
        max_tokens=model_config.get("max_tokens", 4096),
        top_p=model_config.get("top_p", None),
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    
    # Create the orchestrator agent with specialized agents as tools
    orchestrator = Agent(
        model=model,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=available_agents
    )
    
    return orchestrator


def process_query(
    query: str,
    user_role: str = "user",
    custom_model_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to process a query with the orchestrator.
    
    Args:
        query: The user's question or request
        user_role: The role of the user ('user', 'extractor', 'admin')
        custom_model_config: Optional custom model configuration
    
    Returns:
        The orchestrator's response as a string
    
    Example:
        ```python
        from strands_agents.src.agents.orchestrator_agent import process_query
        
        response = process_query(
            "Find all bottlenecks and suggest improvements",
            user_role="user"
        )
        print(response)
        ```
    """
    orchestrator = create_orchestrator_agent(
        user_role=user_role,
        custom_model_config=custom_model_config
    )
    
    response = orchestrator(query)
    return str(response)

