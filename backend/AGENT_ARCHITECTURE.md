# Agent Tool Architecture Documentation

## Overview

The Agent Tool Architecture is a modular, scalable system for managing AI agents with specialized tools and role-based access control. This architecture provides a clean separation of concerns, making it easy to add new tools, agents, and capabilities without modifying existing code.

## Architecture Components

### 1. Tool Categories (Separate Files)

The tools are organized into specialized modules based on functionality:

#### `tools/graph_crud.py` - Core CRUD Operations
- **Purpose**: Basic Create, Read, Update, Delete operations for graph entities
- **Tools**: `add_node`, `add_relationship`, `update_node`, `delete_node`, `get_node`, `list_nodes`
- **Access**: Extractor, Admin roles

#### `tools/graph_analysis.py` - Pattern Detection & Analysis
- **Purpose**: Analytical tools for understanding organizational patterns
- **Tools**: `find_bottlenecks`, `analyze_organizational_structure`, `find_process_dependencies`, `calculate_organizational_metrics`, `find_communication_patterns`
- **Access**: Analyzer, Admin, User roles

#### `tools/graph_admin.py` - Database Management
- **Purpose**: Administrative operations for database management
- **Tools**: `reset_graph`, `backup_graph`, `restore_graph`, `get_database_info`, `create_indexes`, `validate_schema`
- **Access**: Admin role only

#### `tools/graph_search.py` - Complex Search & Recommendations
- **Purpose**: Advanced search, pathfinding, and recommendation capabilities
- **Tools**: `find_shortest_path`, `find_related_nodes`, `search_nodes`, `find_influential_nodes`, `recommend_collaborations`, `find_communities`, `advanced_query`
- **Access**: Analyzer, Admin, User roles

### 2. Agent Design Pattern

#### Single Agent Class with Dynamic Tool Loading
- **BaseAgent**: Abstract base class providing common functionality
- **Tool Registry**: Agents automatically discover available tools at runtime
- **Permission System**: Role-based access control prevents unauthorized tool usage

#### Specialized Agent Types
- **GraphAgent**: User-facing agent for safe queries and analysis
- **ExtractorAgent**: Data ingestion and entity management
- **AnalyzerAgent**: Pattern analysis and insight generation
- **AdminAgent**: Database administration and management

### 3. Directory Structure

```
backend/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Abstract base class
│   ├── graph_agent.py         # User-facing agent
│   ├── extractor_agent.py     # Data ingestion agent
│   ├── analyzer_agent.py      # Pattern analysis agent
│   ├── admin_agent.py         # Administrative agent
│   └── agent_orchestrator.py  # Main orchestrator
├── tools/
│   ├── __init__.py
│   ├── graph_crud.py          # CRUD operations
│   ├── graph_analysis.py      # Analysis tools
│   ├── graph_admin.py         # Admin tools
│   └── graph_search.py        # Search tools
├── models/
│   ├── __init__.py
│   ├── entities.py            # Entity models (Person, Process, etc.)
│   └── relationships.py       # Relationship models
└── config/
    ├── __init__.py
    ├── tool_permissions.py    # Role-based access control
    ├── agent_config.py        # Agent configurations
    └── database_config.py     # Database settings
```

## Tool Access Strategy

### Role-Based Permissions

#### Extractor Agent
- **Role**: `extractor`
- **Tools**: `add_node`, `add_relationship`, `update_node`, `get_node`, `list_nodes`, `search_nodes`
- **Purpose**: Data ingestion and basic entity management

#### Analyzer Agent
- **Role**: `analyzer`
- **Tools**: All analysis and search tools, plus read-only CRUD operations
- **Purpose**: Pattern detection, insight generation, and comprehensive analysis

#### Admin Agent
- **Role**: `admin`
- **Tools**: All tools including dangerous operations
- **Purpose**: Database administration, backup/restore, schema management

#### User-facing Agent
- **Role**: `user`
- **Tools**: Safe read-only operations and analysis tools
- **Purpose**: End-user queries and analysis without data modification

### Permission Validation

```python
# Example permission check
def validate_role_access(role: str, tool_name: str) -> bool:
    """Validate if a role has access to a specific tool."""
    return tool_name in ROLE_PERMISSIONS.get(role, [])
```

## Benefits of This Approach

### 1. Modularity
- **Easy Extension**: Add new tools without touching agent code
- **Separation of Concerns**: Each tool module has a single responsibility
- **Independent Testing**: Tools can be unit tested independently

### 2. Security
- **Granular Permissions**: Role-based access prevents accidental data loss
- **Dangerous Operation Protection**: Special confirmation required for destructive operations
- **Parameter Validation**: All tool parameters are validated before execution

### 3. Scalability
- **Distributed Deployment**: Tools can be distributed across services later
- **Load Balancing**: Multiple agent instances can share the same tool registry
- **Resource Management**: Efficient connection pooling and resource cleanup

### 4. Maintainability
- **Self-Documenting**: Tool registry provides automatic documentation
- **Version Control**: Changes to tools don't affect agent implementations
- **Configuration Management**: Centralized configuration for all components

## Tool Registration Pattern

Each tool file exports a `TOOLS` dictionary that the agent auto-discovers:

```python
# Example from graph_crud.py
TOOLS = {
    "add_node": {
        "function": add_node,
        "description": "Add a new node to the graph database",
        "category": "crud",
        "permissions": ["extractor", "admin"]
    },
    # ... more tools
}
```

The orchestrator automatically loads and validates these tools:

```python
def _load_tools(self) -> Dict[str, Dict[str, Any]]:
    """Load tools available to this agent's role."""
    role_tools = get_tools_for_role(self.role)
    available_tools = {}
    
    for tool_name in role_tools:
        if tool_name in ALL_TOOLS:
            available_tools[tool_name] = ALL_TOOLS[tool_name]
    
    return available_tools
```

## Usage Examples

### Basic Agent Usage

```python
from agents.agent_orchestrator import AgentOrchestrator

# Create orchestrator
orchestrator = AgentOrchestrator()

# Get a graph agent for user queries
graph_agent = orchestrator.get_agent("graph")
response = graph_agent.process_query("Show me all bottlenecks in our processes")

# Get an extractor agent for data ingestion
extractor_agent = orchestrator.get_agent("extractor")
result = extractor_agent.add_person({
    "name": "John Doe",
    "email": "john@company.com",
    "role": "Software Engineer",
    "department": "Engineering"
})
```

### Custom Agent Configuration

```python
from config import create_custom_config

# Create custom configuration
custom_config = create_custom_config("graph_agent", {
    "max_tokens": 2000,
    "temperature": 0.2,
    "enable_memory": True
})

# Create agent with custom config
custom_agent = orchestrator.get_agent("graph", custom_config)
```

### Tool Execution

```python
# Direct tool execution
result = agent.execute_tool("find_bottlenecks", {
    "process_type": "Process"
})

# Tool execution with validation
if agent.validate_tool_access("reset_graph"):
    result = agent.execute_tool("reset_graph", {"confirm": True})
```

## Configuration Management

### Agent Configuration

```python
# Default configurations for different agent types
DEFAULT_CONFIGS = {
    "graph_agent": {
        "role": "user",
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 1000,
        "temperature": 0.1,
        "enable_tools": True,
        "enable_safety_checks": True
    },
    # ... more configurations
}
```

### Database Configuration

```python
# Environment-based configuration
def get_database_config(env_prefix: str = "NEO4J") -> DatabaseConfig:
    return DatabaseConfig(
        neo4j_uri=os.getenv(f"{env_prefix}_URI", "bolt://localhost:7687"),
        neo4j_username=os.getenv(f"{env_prefix}_USERNAME", "neo4j"),
        neo4j_password=os.getenv(f"{env_prefix}_PASSWORD", "password"),
        max_connection_pool_size=int(os.getenv(f"{env_prefix}_MAX_POOL_SIZE", "50"))
    )
```

## Safety and Validation

### Dangerous Operations

Certain tools are marked as dangerous and require special handling:

```python
DANGEROUS_TOOLS = {
    "reset_graph": "Will delete ALL data in the graph database",
    "restore_graph": "Will replace ALL data in the graph database",
    "delete_node": "Will permanently delete nodes and their relationships",
    "advanced_query": "Can execute arbitrary Cypher queries"
}
```

### Parameter Validation

All tool parameters are validated before execution:

```python
def validate_tool_parameters(tool_name: str, parameters: Dict[str, any]) -> Dict[str, any]:
    """Validate tool parameters against safety requirements."""
    issues = []
    
    if is_dangerous_tool(tool_name):
        safety_reqs = get_safety_requirements(tool_name)
        for req in safety_reqs:
            if req not in parameters:
                issues.append(f"Missing required safety parameter: {req}")
    
    return {"valid": len(issues) == 0, "issues": issues}
```

## Monitoring and Logging

### Agent Status

```python
# Get orchestrator status
status = orchestrator.get_orchestrator_status()
print(f"Active agents: {status['orchestrator']['active_agents']}")
print(f"Available tools: {status['agents']}")
```

### Tool Execution Logging

```python
# Enable tool call logging
config = get_agent_config("graph_agent")
config.log_tool_calls = True
config.log_level = "DEBUG"
```

## Best Practices

### 1. Tool Development
- **Single Responsibility**: Each tool should have a single, well-defined purpose
- **Error Handling**: Always return structured error information
- **Documentation**: Provide clear descriptions and parameter information
- **Validation**: Validate all inputs and handle edge cases

### 2. Agent Usage
- **Role Selection**: Choose the appropriate agent role for your use case
- **Resource Management**: Always close agents when done
- **Error Handling**: Handle tool execution errors gracefully
- **Configuration**: Use environment variables for sensitive settings

### 3. Security
- **Permission Validation**: Always validate tool access before execution
- **Dangerous Operations**: Require explicit confirmation for destructive operations
- **Parameter Validation**: Validate all tool parameters
- **Audit Logging**: Log all administrative operations

## Migration from Legacy Code

The new architecture maintains backward compatibility with existing code:

```python
# Legacy code continues to work
agent = GraphAgent()
response = agent.process_query("Show me all people")

# New architecture provides additional capabilities
orchestrator = AgentOrchestrator()
graph_agent = orchestrator.get_agent("graph")
extractor_agent = orchestrator.get_agent("extractor")
analyzer_agent = orchestrator.get_agent("analyzer")
```

## Future Enhancements

### Planned Features
1. **Tool Versioning**: Support for multiple versions of the same tool
2. **Distributed Tools**: Tools that can run on remote services
3. **Tool Composition**: Ability to chain tools together
4. **Performance Metrics**: Detailed performance monitoring for tools
5. **A/B Testing**: Support for testing different tool implementations

### Extension Points
1. **Custom Tool Categories**: Add new tool categories beyond the current four
2. **Custom Agent Types**: Create specialized agents for specific domains
3. **Custom Permission Models**: Implement more sophisticated access control
4. **Custom Validation**: Add domain-specific validation rules

## Conclusion

The Agent Tool Architecture provides a robust, scalable foundation for building AI agents with specialized capabilities. By separating tools from agents and implementing role-based access control, the system achieves high modularity, security, and maintainability while remaining easy to use and extend.

The architecture's design principles of separation of concerns, security-first approach, and self-documenting tool registry make it well-suited for both current needs and future growth.
