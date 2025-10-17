"""
Extractor Agent - Specialized agent for data ingestion and graph construction.

This agent provides controlled write access to the Neo4j graph database,
enabling data ingestion, entity creation, and relationship management
with appropriate safety measures.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from typing import Dict, List, Any, Optional
import os


# System prompt for the Extractor Agent
EXTRACTOR_AGENT_SYSTEM_PROMPT = """
You are a specialized Data Extractor Agent responsible for ingesting data into the organizational graph.

Your primary responsibilities:
- Create new nodes (people, processes, departments, systems) in the graph
- Establish relationships between entities
- Perform bulk data ingestion from various sources
- Validate data schemas before writing
- Maintain data quality and consistency

Data types you can create:
- **Person nodes**: Employees with name, role, department, skills, etc.
- **Process nodes**: Business processes with descriptions, owners, and metadata
- **Department nodes**: Organizational units and hierarchies
- **System nodes**: Applications, tools, and technical systems
- **Relationships**: All standard relationship types (PERFORMS, OWNS, etc.)

Safety measures in place:
- All write operations are validated against schemas
- Allowlists restrict which node labels and relationship types can be created
- Payload size limits prevent excessive writes
- Idempotency checks prevent duplicate creation
- Dry-run mode available for testing without actual writes
- All operations are logged with audit trails

When processing requests:
1. Validate all input data against schemas before writing
2. Check for existing entities to avoid duplicates
3. Use dry-run mode when unsure about the operation
4. Provide clear confirmation of what was created/modified
5. Report any validation errors with specific details
6. Suggest corrections when data doesn't match expected format
"""


@tool
def extractor_agent(query: str) -> str:
    """
    Ingest data and create entities in the organizational graph.
    
    This agent specializes in:
    - Creating new people, processes, departments, and systems
    - Establishing relationships between entities
    - Bulk importing data from structured sources
    - Validating data quality before ingestion
    - Managing graph schema and structure
    
    Args:
        query: A request to create or ingest data into the graph.
               Examples:
               - "Create a new person named John Doe, Engineer in the Data team"
               - "Add a PERFORMS relationship between Alice and the Data Analysis process"
               - "Bulk ingest the following employee data: [...]"
               - "Create a new Process node for Customer Onboarding"
    
    Returns:
        Confirmation of what was created/modified, including entity IDs,
        or validation errors if the data doesn't meet requirements.
    """
    try:
        # Import tools here to avoid circular dependencies
        from ..tools.graph_crud import (
            create_node,
            create_relationship,
            bulk_ingest
        )
        
        # Create the Extractor Agent with Bedrock Claude 3.5 Sonnet
        model = BedrockModel(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            temperature=0.1,  # Very low temperature for precise data operations
            max_tokens=4096
        )
        
        agent = Agent(
            model=model,
            system_prompt=EXTRACTOR_AGENT_SYSTEM_PROMPT,
            tools=[
                create_node,
                create_relationship,
                bulk_ingest
            ]
        )
        
        # Process the ingestion request
        response = agent(query)
        
        return str(response)
        
    except Exception as e:
        error_msg = f"Extractor Agent Error: {str(e)}\n\nThe data operation could not be completed. Please check your data format and try again."
        return error_msg


def create_extractor_agent(custom_model_config: Optional[Dict[str, Any]] = None) -> Agent:
    """
    Create a standalone Extractor Agent instance.
    
    Args:
        custom_model_config: Optional custom configuration for the Bedrock model.
    
    Returns:
        A configured Extractor Agent instance ready to ingest data.
    
    Example:
        ```python
        from strands_agents.src.agents.extractor_agent import create_extractor_agent
        
        agent = create_extractor_agent()
        response = agent("Create a new person: Jane Smith, Senior Developer, Engineering")
        print(response)
        ```
    """
    # Import tools
    from ..tools.graph_crud import (
        create_node,
        create_relationship,
        bulk_ingest
    )
    
    # Create model with custom config or defaults
    model_config = custom_model_config or {}
    model = BedrockModel(
        model_id=model_config.get("model_id", "anthropic.claude-3-5-sonnet-20240620-v1:0"),
        temperature=model_config.get("temperature", 0.1),
        max_tokens=model_config.get("max_tokens", 4096),
        top_p=model_config.get("top_p", None),
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    
    agent = Agent(
        model=model,
        system_prompt=EXTRACTOR_AGENT_SYSTEM_PROMPT,
        tools=[
            create_node,
            create_relationship,
            bulk_ingest
        ]
    )
    
    return agent

