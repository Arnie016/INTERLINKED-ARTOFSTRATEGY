# Utilities Module

This module provides shared utilities for all Strands agents, ensuring consistency and reducing code duplication across the agent system.

## Modules

### logging.py
Centralized logging utilities with AgentCore Observability integration.

**Features:**
- Structured JSON logging for CloudWatch
- Environment-based configuration (dev/prod)
- Performance tracking and metrics
- Session and trace ID support

**Usage:**
```python
from utils import get_logger

logger = get_logger(__name__)
logger.info("Agent initialized")
logger.log_agent_invocation("graph_agent", "Find all people", session_id="abc123")
```

### errors.py
Custom exception hierarchy for different error scenarios.

**Features:**
- Standardized error codes
- Structured error responses
- Context preservation
- User-friendly error messages

**Usage:**
```python
from utils import GraphQueryError, handle_error

try:
    # Execute query
    result = execute_query(query)
except Exception as e:
    raise GraphQueryError(
        "Query execution failed",
        query=query,
        original_error=e
    )
```

### validation.py
Input validation and schema validation utilities.

**Features:**
- Node and relationship validation
- Property type checking
- Cypher injection prevention
- Pagination parameter validation

**Usage:**
```python
from utils import validate_node_properties, validate_pagination_params

# Validate node creation
properties = validate_node_properties(
    "Person",
    {"name": "Alice", "email": "alice@example.com"}
)

# Validate pagination
params = validate_pagination_params(limit=100, offset=0)
```

### auth.py
Authentication and authorization utilities with role-based access control.

**Features:**
- Token validation
- Permission checking
- Role-based access control
- AgentCore Identity integration ready

**Usage:**
```python
from utils import create_auth_context, Permission

auth = create_auth_context(token="user-token")
auth.require_permission(Permission.WRITE_GRAPH)

if auth.is_admin():
    # Perform admin operation
    pass
```

### response.py
Standardized response formatting for all agent operations.

**Features:**
- Consistent response structure
- Pagination support
- Performance metadata
- Error formatting

**Usage:**
```python
from utils import success_response, paginated_response, add_performance_metadata

# Simple success response
response = success_response(
    data={"nodes": nodes},
    message="Query successful"
)

# Paginated response
response = paginated_response(
    items=results,
    total=1000,
    limit=50,
    offset=0
)

# Add performance tracking
response = add_performance_metadata(response, execution_time_ms=125.5)
```

### test_helpers.py
Testing utilities for agent validation.

**Features:**
- Mock Neo4j responses
- Sample graph data generators
- Request/response mocks
- Assertion helpers

**Usage:**
```python
from utils.test_helpers import create_mock_graph, create_mock_agent_request

# Generate test data
graph = create_mock_graph(num_people=5, num_orgs=2)

# Create mock request
request = create_mock_agent_request(
    query="Find all people",
    session_id="test-session"
)
```

## Integration with AgentCore

### Observability
The logging module integrates with AgentCore Observability:

```python
logger = get_logger(__name__, environment="production")
logger.log_model_call(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    input_tokens=1000,
    output_tokens=500,
    duration_ms=250
)
```

Logs are formatted for CloudWatch and include:
- Structured JSON format
- Timestamps in ISO 8601 format
- Event types for filtering
- Performance metrics

### Identity
The auth module is ready for AgentCore Identity integration:

```python
# Current: Development mode with mock tokens
auth = create_auth_context(token="user-alice")

# Future: Production with Cognito
# auth = create_auth_context(token=cognito_jwt_token)
```

### Gateway
Validation utilities prepare data for Gateway integration:

```python
from utils import validate_node_properties

# Validates against allowed node labels from config
properties = validate_node_properties("Person", data)
```

## Best Practices

1. **Always use structured logging:**
   ```python
   logger.info("Query executed", query_type="search", duration_ms=125.5)
   ```

2. **Raise specific exceptions:**
   ```python
   raise GraphQueryError("Query failed", query=cypher_query)
   ```

3. **Validate all inputs:**
   ```python
   validate_node_label(label)
   validate_node_properties(label, properties)
   ```

4. **Use standardized responses:**
   ```python
   return success_response(data, message="Operation successful")
   ```

5. **Track performance:**
   ```python
   start = time.time()
   result = perform_operation()
   duration_ms = (time.time() - start) * 1000
   logger.log_tool_execution(tool_name, duration_ms, success=True)
   ```

## Error Handling Pattern

```python
from utils import get_logger, handle_error, GraphQueryError

logger = get_logger(__name__)

try:
    result = execute_graph_query(query)
    return success_response(result)
except GraphQueryError as e:
    error_dict = handle_error(e, logger)
    return error_response(error_dict["error"])
except Exception as e:
    error_dict = handle_error(e, logger)
    return error_response(error_dict["error"])
```

## Testing Pattern

```python
from utils.test_helpers import (
    create_mock_graph,
    create_mock_agent_request,
    assert_valid_response
)

def test_agent_query():
    # Setup
    graph = create_mock_graph(num_people=5)
    request = create_mock_agent_request(query="Find all people")
    
    # Execute
    response = agent.handle_request(request)
    
    # Assert
    assert_valid_response(response)
    assert response["status"] == "success"
```


