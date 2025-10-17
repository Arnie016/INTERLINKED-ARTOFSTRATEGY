# Utilities Integration Guide

This guide shows how to integrate the shared utilities and configuration modules into existing Strands agents.

## Quick Start

### 1. Update Imports in Agent Files

**Before:**
```python
from strands import Agent
from strands.models import BedrockModel
```

**After:**
```python
from strands import Agent
from strands.models import BedrockModel
from config import get_config, get_model_config, AgentName
from utils import get_logger, success_response, error_response, handle_error
```

### 2. Initialize Logger

Add at the top of each agent file:

```python
# Get logger for this module
logger = get_logger(__name__)
```

### 3. Use Configuration for Model Setup

**Before:**
```python
model = BedrockModel(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"
)
```

**After:**
```python
# Get model configuration for this agent
model_config = get_model_config(AgentName.GRAPH)
model = BedrockModel(**model_config.to_dict())

logger.info(
    "Agent initialized",
    agent_name=AgentName.GRAPH.value,
    model_id=model_config.model_id
)
```

### 4. Add Validation to Tools

**Before:**
```python
@tool
def search_nodes(label: str, properties: dict) -> dict:
    # Direct Neo4j query
    result = driver.execute_query(query)
    return result
```

**After:**
```python
from utils import (
    validate_node_label,
    validate_node_properties,
    GraphQueryError,
    success_response,
    error_response
)

@tool
def search_nodes(label: str, properties: dict) -> dict:
    """Search for nodes by label and properties."""
    try:
        # Validate inputs
        label = validate_node_label(label)
        properties = validate_node_properties(label, properties, check_required=False)
        
        # Log operation
        logger.info(
            "Searching nodes",
            label=label,
            property_count=len(properties)
        )
        
        # Execute query
        result = driver.execute_query(query)
        
        # Log success
        logger.info(
            "Search completed",
            nodes_found=len(result)
        )
        
        # Return formatted response
        return success_response(
            data={"nodes": result},
            message=f"Found {len(result)} nodes"
        )
        
    except GraphQueryError as e:
        error_dict = handle_error(e, logger)
        return error_response(error_dict["error"])
    except Exception as e:
        error_dict = handle_error(e, logger)
        return error_response(error_dict["error"])
```

### 5. Use Response Formatters

**Before:**
```python
return {"status": "success", "data": nodes}
```

**After:**
```python
from utils import success_response, format_node_response

# Format individual nodes
formatted_nodes = [format_node_response(node) for node in nodes]

# Return standardized response
return success_response(
    data={"nodes": formatted_nodes},
    message=f"Found {len(nodes)} nodes"
)
```

### 6. Add Pagination

**Before:**
```python
def list_all_people():
    result = driver.execute_query("MATCH (p:Person) RETURN p")
    return result
```

**After:**
```python
from utils import validate_pagination_params, paginated_response

def list_all_people(limit: int = None, offset: int = None):
    # Validate pagination parameters
    params = validate_pagination_params(limit, offset)
    
    # Execute paginated query
    query = """
        MATCH (p:Person)
        RETURN p
        SKIP $offset
        LIMIT $limit
    """
    
    result = driver.execute_query(query, offset=params["offset"], limit=params["limit"])
    
    # Get total count
    total = driver.execute_query("MATCH (p:Person) RETURN count(p) as count")[0]["count"]
    
    # Return paginated response
    return paginated_response(
        items=result,
        total=total,
        limit=params["limit"],
        offset=params["offset"]
    )
```

### 7. Add Authentication (Optional)

For tools that require authentication:

```python
from utils import create_auth_context, check_write_permission, AuthorizationError

@tool
def create_node(label: str, properties: dict, auth_token: str = None) -> dict:
    """Create a new node (requires write permission)."""
    try:
        # Create auth context
        auth = create_auth_context(auth_token)
        
        # Check permission
        check_write_permission(auth, operation="create")
        
        # Validate and create node
        label = validate_node_label(label)
        properties = validate_node_properties(label, properties)
        
        # Log with user context
        logger.info(
            "Creating node",
            label=label,
            user_id=auth.user_id
        )
        
        # Execute creation
        result = driver.execute_query(query)
        
        return success_response(
            data={"node": result},
            message="Node created successfully"
        )
        
    except AuthorizationError as e:
        return error_response(e.to_dict()["error"])
```

## Complete Agent Example

Here's a complete example of an updated agent tool:

```python
"""
Graph Search Tool - Updated with shared utilities
"""

from strands import tool
from config import get_config
from utils import (
    get_logger,
    validate_node_label,
    validate_search_query,
    validate_pagination_params,
    GraphQueryError,
    success_response,
    error_response,
    paginated_response,
    handle_error,
    format_node_response
)

# Initialize logger
logger = get_logger(__name__)

# Load configuration
config = get_config()
neo4j_config = config.get_neo4j_config()


@tool
def search_nodes(
    label: str,
    search_term: str,
    limit: int = None,
    offset: int = None
) -> dict:
    """
    Search for nodes by label and text search.
    
    Args:
        label: Node label to search (Person, Organization, etc.)
        search_term: Text to search for in node properties
        limit: Maximum results to return
        offset: Number of results to skip
    
    Returns:
        Paginated response with matching nodes
    """
    try:
        # Validate inputs
        label = validate_node_label(label)
        search_term = validate_search_query(search_term)
        params = validate_pagination_params(limit, offset)
        
        # Log operation start
        logger.info(
            "Searching nodes",
            label=label,
            search_term_length=len(search_term),
            limit=params["limit"],
            offset=params["offset"]
        )
        
        # Build and execute query
        query = f"""
            MATCH (n:{label})
            WHERE n.name CONTAINS $search_term
               OR n.description CONTAINS $search_term
            RETURN n
            SKIP $offset
            LIMIT $limit
        """
        
        import time
        start = time.time()
        
        # Execute query (placeholder - will use real Neo4j driver)
        result = []  # driver.execute_query(query, search_term=search_term, ...)
        
        # Calculate execution time
        duration_ms = (time.time() - start) * 1000
        
        # Get total count
        count_query = f"""
            MATCH (n:{label})
            WHERE n.name CONTAINS $search_term
               OR n.description CONTAINS $search_term
            RETURN count(n) as total
        """
        total = 0  # driver.execute_query(count_query)[0]["total"]
        
        # Format nodes
        formatted_nodes = [format_node_response(node) for node in result]
        
        # Log success with metrics
        logger.info(
            "Search completed successfully",
            nodes_found=len(result),
            total_available=total,
            execution_time_ms=duration_ms
        )
        
        # Return paginated response
        response = paginated_response(
            items=formatted_nodes,
            total=total,
            limit=params["limit"],
            offset=params["offset"],
            message=f"Found {len(result)} of {total} nodes"
        )
        
        # Add performance metadata
        if "metadata" not in response:
            response["metadata"] = {}
        response["metadata"]["execution_time_ms"] = duration_ms
        
        return response
        
    except GraphQueryError as e:
        error_dict = handle_error(e, logger)
        return error_response(
            error_dict["error"],
            message="Graph query failed"
        )
    except Exception as e:
        error_dict = handle_error(e, logger)
        return error_response(
            error_dict["error"],
            message="Unexpected error during search"
        )
```

## Testing with Utilities

Update tests to use test helpers:

```python
from utils.test_helpers import (
    create_mock_graph,
    create_mock_agent_request,
    assert_valid_response,
    assert_valid_node
)

def test_search_nodes():
    # Create test data
    graph = create_mock_graph(num_people=10)
    
    # Create mock request
    request = create_mock_agent_request(
        query="Find people named Alice"
    )
    
    # Execute search
    response = search_nodes(
        label="Person",
        search_term="Alice",
        limit=10,
        offset=0
    )
    
    # Validate response structure
    assert_valid_response(response)
    assert response["status"] == "success"
    
    # Validate nodes
    for node in response["data"]["items"]:
        assert_valid_node(node)
```

## Configuration Loading Example

Load agent-specific configuration:

```python
from config import get_config, AgentName

# Load global config
config = get_config()

# Get agent-specific config
graph_agent_config = config.get_agent_config("graph")

print(f"Agent Name: {graph_agent_config['name']}")
print(f"Model: {graph_agent_config['model']}")
print(f"Description: {graph_agent_config['description']}")

# Get Neo4j config
neo4j_config = config.get_neo4j_config()
print(f"Connection Mode: {neo4j_config['connection_mode']}")
print(f"Timeout: {neo4j_config['timeout']}")

# Check environment
if config.is_production():
    print("Running in production mode")
else:
    print("Running in development mode")
```

## Migration Checklist

Use this checklist when updating an agent:

- [ ] Add logger initialization at module level
- [ ] Replace hardcoded model config with `get_model_config()`
- [ ] Add input validation to all tool functions
- [ ] Use structured error handling with custom exceptions
- [ ] Replace ad-hoc responses with `success_response()` / `error_response()`
- [ ] Add pagination support where appropriate
- [ ] Use constants instead of magic strings
- [ ] Add performance logging with execution times
- [ ] Update tests to use test helpers
- [ ] Add authentication checks for write operations (if applicable)

## Benefits After Integration

1. **Consistent error handling** across all agents
2. **Structured logging** for CloudWatch observability
3. **Input validation** prevents invalid data
4. **Standardized responses** for easier client integration
5. **Configuration management** supports multiple environments
6. **Type safety** with enums and type hints
7. **Performance tracking** with execution metrics
8. **Security** with input sanitization and auth checks
9. **Testing** made easier with mock helpers
10. **Maintainability** with centralized utilities

## Support

For questions or issues with integration:

1. Check the comprehensive READMEs in `src/utils/` and `src/config/`
2. Review the examples in `examples/basic_usage.py`
3. Look at test examples in `tests/test_agents_basic.py`
4. Refer to the implementation summary in `UTILITIES_IMPLEMENTATION_SUMMARY.md`

