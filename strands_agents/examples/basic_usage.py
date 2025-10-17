"""
Basic usage examples for Strands Agents.

This script demonstrates how to use the orchestrator and specialized agents
to query and analyze the organizational graph.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents import (
    create_orchestrator_agent,
    create_graph_agent,
    create_analyzer_agent,
    process_query
)


def example_orchestrator():
    """Example using the orchestrator agent."""
    print("=" * 80)
    print("EXAMPLE 1: Using the Orchestrator Agent")
    print("=" * 80)
    
    # Create orchestrator for a regular user
    orchestrator = create_orchestrator_agent(user_role="user")
    
    # Simple query
    print("\nQuery: Who are all the people in the Engineering department?")
    response = orchestrator("Who are all the people in the Engineering department?")
    print(f"Response:\n{response}\n")
    
    # Analytical query
    print("\nQuery: Find organizational bottlenecks and suggest improvements")
    response = orchestrator("Find organizational bottlenecks and suggest improvements")
    print(f"Response:\n{response}\n")


def example_graph_agent():
    """Example using the graph agent directly."""
    print("=" * 80)
    print("EXAMPLE 2: Using the Graph Agent Directly")
    print("=" * 80)
    
    # Create graph agent
    graph_agent = create_graph_agent()
    
    # Search for people
    print("\nQuery: Find all senior engineers in the organization")
    response = graph_agent("Find all senior engineers in the organization")
    print(f"Response:\n{response}\n")
    
    # Explore relationships
    print("\nQuery: Who does Alice Johnson report to?")
    response = graph_agent("Who does Alice Johnson report to?")
    print(f"Response:\n{response}\n")


def example_analyzer_agent():
    """Example using the analyzer agent directly."""
    print("=" * 80)
    print("EXAMPLE 3: Using the Analyzer Agent Directly")
    print("=" * 80)
    
    # Create analyzer agent
    analyzer_agent = create_analyzer_agent()
    
    # Centrality analysis
    print("\nQuery: Who are the most central people in our organization?")
    response = analyzer_agent("Who are the most central people in our organization?")
    print(f"Response:\n{response}\n")
    
    # Community detection
    print("\nQuery: Detect communities in the Engineering department")
    response = analyzer_agent("Detect communities in the Engineering department")
    print(f"Response:\n{response}\n")


def example_convenience_function():
    """Example using the convenience function."""
    print("=" * 80)
    print("EXAMPLE 4: Using the Convenience Function")
    print("=" * 80)
    
    # Simple one-liner
    print("\nQuery: What processes does the Data team own?")
    response = process_query(
        "What processes does the Data team own?",
        user_role="user"
    )
    print(f"Response:\n{response}\n")


def example_custom_configuration():
    """Example with custom model configuration."""
    print("=" * 80)
    print("EXAMPLE 5: Custom Model Configuration")
    print("=" * 80)
    
    # Custom config for more detailed responses
    custom_config = {
        "temperature": 0.7,
        "max_tokens": 8192
    }
    
    orchestrator = create_orchestrator_agent(
        user_role="user",
        custom_model_config=custom_config
    )
    
    print("\nQuery: Provide a comprehensive analysis of our organizational structure")
    response = orchestrator(
        "Provide a comprehensive analysis of our organizational structure"
    )
    print(f"Response:\n{response}\n")


def main():
    """Run all examples."""
    print("\n")
    print("*" * 80)
    print("STRANDS AGENTS - BASIC USAGE EXAMPLES")
    print("*" * 80)
    print("\n")
    
    # Check environment variables
    required_vars = ["AWS_REGION"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Some examples may not work correctly.\n")
    
    # Note about tool implementation
    print("📝 NOTE: The actual Neo4j tools are not yet implemented (Tasks 3-6).")
    print("These examples will show placeholder responses from the agents.")
    print("Once tools are implemented, agents will return real data from Neo4j.\n")
    
    try:
        # Run examples
        example_orchestrator()
        example_graph_agent()
        example_analyzer_agent()
        example_convenience_function()
        example_custom_configuration()
        
        print("\n")
        print("*" * 80)
        print("ALL EXAMPLES COMPLETED")
        print("*" * 80)
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

