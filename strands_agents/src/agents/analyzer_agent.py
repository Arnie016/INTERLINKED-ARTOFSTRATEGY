"""
Analyzer Agent - Specialized agent for graph analytics and insights.

This agent provides advanced analytical capabilities for understanding
organizational patterns, detecting bottlenecks, and generating insights
from the graph data.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from typing import Dict, List, Any, Optional
import os


# System prompt for the Analyzer Agent
ANALYZER_AGENT_SYSTEM_PROMPT = """
You are a specialized Analytics Agent focused on organizational analysis and insights.

Your primary responsibilities:
- Perform centrality analysis to identify key people and processes
- Detect communities and organizational clusters
- Calculate graph statistics and metrics
- Identify bottlenecks and inefficiencies
- Generate actionable insights and recommendations

Analysis capabilities:
- **Centrality Analysis**: PageRank, betweenness, closeness, eigenvector centrality
- **Community Detection**: Louvain, label propagation, modularity maximization
- **Graph Statistics**: Node/edge counts, density, diameter, clustering coefficient
- **Pattern Detection**: Identify organizational patterns, silos, and collaboration gaps
- **Performance Metrics**: Calculate KPIs and efficiency indicators

Safety constraints:
- You have READ-ONLY access to the graph
- All computations have timeout limits to prevent long-running operations
- Results are cached to improve performance

When responding:
1. Use appropriate analytical algorithms for the question
2. Provide both quantitative metrics and qualitative insights
3. Explain findings in business terms, not just technical metrics
4. Prioritize actionable recommendations over raw data
5. Visualize results when helpful (describe charts/graphs)
6. Compare metrics across different parts of the organization
"""


@tool
def analyzer_agent(query: str) -> str:
    """
    Perform advanced analytics on the organizational graph.
    
    This agent specializes in:
    - Centrality analysis (identifying key players and critical processes)
    - Community detection (finding teams and organizational clusters)
    - Graph statistics (measuring organizational complexity and connectivity)
    - Bottleneck identification (finding inefficiencies and constraints)
    - Performance analysis (calculating metrics and KPIs)
    
    Args:
        query: An analytical question about the organization.
               Examples:
               - "Who are the most central people in our organization?"
               - "Find communities in our Engineering department"
               - "What are the key organizational metrics?"
               - "Identify bottlenecks in our processes"
               - "Which processes have the most dependencies?"
    
    Returns:
        Detailed analytical insights with metrics, patterns, and recommendations.
    """
    try:
        # Import tools here to avoid circular dependencies
        from ..tools.graph_analysis import (
            centrality_analysis,
            community_detection,
            graph_stats,
            find_bottlenecks
        )
        
        # Create the Analyzer Agent with Bedrock Claude 3.5 Sonnet
        model = BedrockModel(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            temperature=0.2,  # Even lower temperature for analytical precision
            max_tokens=4096
        )
        
        agent = Agent(
            model=model,
            system_prompt=ANALYZER_AGENT_SYSTEM_PROMPT,
            tools=[
                centrality_analysis,
                community_detection,
                graph_stats,
                find_bottlenecks
            ]
        )
        
        # Process the analytical query
        response = agent(query)
        
        return str(response)
        
    except Exception as e:
        error_msg = f"Analyzer Agent Error: {str(e)}\n\nThe analysis could not be completed. Please try a different analytical approach or contact support."
        return error_msg


def create_analyzer_agent(custom_model_config: Optional[Dict[str, Any]] = None) -> Agent:
    """
    Create a standalone Analyzer Agent instance.
    
    Args:
        custom_model_config: Optional custom configuration for the Bedrock model.
    
    Returns:
        A configured Analyzer Agent instance ready to perform analytics.
    
    Example:
        ```python
        from strands_agents.src.agents.analyzer_agent import create_analyzer_agent
        
        agent = create_analyzer_agent()
        response = agent("Analyze our organizational structure and identify key influencers")
        print(response)
        ```
    """
    # Import tools
    from ..tools.graph_analysis import (
        centrality_analysis,
        community_detection,
        graph_stats,
        find_bottlenecks
    )
    
    # Create model with custom config or defaults
    model_config = custom_model_config or {}
    model = BedrockModel(
        model_id=model_config.get("model_id", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
        temperature=model_config.get("temperature", 0.2),
        max_tokens=model_config.get("max_tokens", 4096),
        top_p=model_config.get("top_p", None),
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    
    agent = Agent(
        model=model,
        system_prompt=ANALYZER_AGENT_SYSTEM_PROMPT,
        tools=[
            centrality_analysis,
            community_detection,
            graph_stats,
            find_bottlenecks
        ]
    )
    
    return agent

