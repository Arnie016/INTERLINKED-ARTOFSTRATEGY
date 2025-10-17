"""
Admin Agent - Specialized agent for privileged database operations.

This agent provides administrative capabilities for database maintenance,
schema management, and privileged operations with strict access controls
and safety measures.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from typing import Dict, List, Any, Optional
import os


# System prompt for the Admin Agent
ADMIN_AGENT_SYSTEM_PROMPT = """
You are a specialized Administrative Agent with privileged access to database operations.

Your primary responsibilities:
- Perform database maintenance operations (reindexing, cleanup)
- Migrate and transform graph schema (label migrations, property updates)
- Clean up orphaned nodes and optimize database structure
- Execute administrative queries with proper safeguards
- Monitor database health and performance

Administrative capabilities:
- **Reindexing**: Create and rebuild indexes for better query performance
- **Label Migration**: Safely migrate nodes from old to new labels
- **Maintenance Cleanup**: Remove orphaned nodes and optimize structure
- **Schema Management**: Manage constraints, indexes, and graph schema
- **Backup Operations**: Coordinate backup and restore procedures

CRITICAL SAFETY MEASURES:
- ALL destructive operations require explicit confirmation
- Dry-run mode is MANDATORY before actual execution
- All operations have size limits and execution timeouts
- Comprehensive audit logging for all admin actions
- Rollback capabilities for supported operations
- Role-based access control (admin role required)

When processing requests:
1. ALWAYS use dry-run first to preview the operation
2. Clearly communicate what the operation will do
3. Request explicit confirmation for destructive actions
4. Provide detailed progress reporting for long operations
5. Offer rollback options when applicable
6. Document all operations in audit logs
7. Validate that the user has admin privileges
8. Set conservative limits on batch operations
"""


@tool
def admin_agent(query: str) -> str:
    """
    Perform privileged administrative operations on the graph database.
    
    This agent specializes in:
    - Database reindexing and optimization
    - Label and schema migrations
    - Maintenance cleanup (orphan removal, optimization)
    - Administrative queries and operations
    - Database health monitoring
    
    **WARNING**: This agent can perform destructive operations.
    Admin role is required to use this agent.
    
    Args:
        query: An administrative request.
               Examples:
               - "Reindex the Person nodes on the 'name' property"
               - "Migrate all 'Employee' labels to 'Person'"
               - "Clean up orphaned nodes in the database"
               - "Show database statistics and health"
    
    Returns:
        Results of the administrative operation, including dry-run previews,
        execution status, and detailed operation logs.
    """
    try:
        # Import tools here to avoid circular dependencies
        from ..tools.graph_admin import (
            reindex,
            migrate_labels,
            maintenance_cleanup_orphan_nodes
        )
        
        # Create the Admin Agent with Bedrock Claude 3.5 Sonnet
        model = BedrockModel(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            temperature=0.0,  # Zero temperature for maximum precision in admin tasks
            max_tokens=4096
        )
        
        agent = Agent(
            model=model,
            system_prompt=ADMIN_AGENT_SYSTEM_PROMPT,
            tools=[
                reindex,
                migrate_labels,
                maintenance_cleanup_orphan_nodes
            ]
        )
        
        # Process the admin request
        response = agent(query)
        
        return str(response)
        
    except Exception as e:
        error_msg = f"Admin Agent Error: {str(e)}\n\nThe administrative operation could not be completed. Please check permissions and parameters."
        return error_msg


def create_admin_agent(custom_model_config: Optional[Dict[str, Any]] = None) -> Agent:
    """
    Create a standalone Admin Agent instance.
    
    **WARNING**: This agent has privileged access. Ensure proper
    authentication and authorization before use.
    
    Args:
        custom_model_config: Optional custom configuration for the Bedrock model.
    
    Returns:
        A configured Admin Agent instance ready to perform administrative operations.
    
    Example:
        ```python
        from strands_agents.src.agents.admin_agent import create_admin_agent
        
        # Only create if user has admin role
        if user.has_role("admin"):
            agent = create_admin_agent()
            response = agent("Show database health metrics")
            print(response)
        ```
    """
    # Import tools
    from ..tools.graph_admin import (
        reindex,
        migrate_labels,
        maintenance_cleanup_orphan_nodes
    )
    
    # Create model with custom config or defaults
    model_config = custom_model_config or {}
    model = BedrockModel(
        model_id=model_config.get("model_id", "anthropic.claude-3-5-sonnet-20240620-v1:0"),
        temperature=model_config.get("temperature", 0.0),
        max_tokens=model_config.get("max_tokens", 4096),
        top_p=model_config.get("top_p", None),
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    
    agent = Agent(
        model=model,
        system_prompt=ADMIN_AGENT_SYSTEM_PROMPT,
        tools=[
            reindex,
            migrate_labels,
            maintenance_cleanup_orphan_nodes
        ]
    )
    
    return agent

