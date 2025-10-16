# Configuration Module

This module provides configuration management for Strands agents, supporting environment-specific settings and model configuration.

## Modules

### config_loader.py
Environment-based configuration loading from YAML files.

**Features:**
- Automatic environment detection
- Configuration validation
- Environment variable overrides
- Caching for performance

**Usage:**
```python
from config import get_config

config = get_config()

# Get agent configuration
orchestrator_config = config.get_agent_config("orchestrator")
model_id = orchestrator_config["model"]

# Get Neo4j configuration
neo4j_config = config.get_neo4j_config()

# Check environment
if config.is_production():
    # Use production settings
    pass
```

### constants.py
Shared constants, enums, and default values.

**Features:**
- Type-safe enums
- Centralized constants
- Error and success messages
- Cypher query patterns

**Usage:**
```python
from config import (
    NodeLabel,
    RelationshipType,
    DEFAULT_PAGE_SIZE,
    get_error_message
)

# Use enums
label = NodeLabel.PERSON.value  # "Person"
rel_type = RelationshipType.WORKS_AT.value  # "WORKS_AT"

# Use defaults
limit = DEFAULT_PAGE_SIZE  # 50

# Get messages
error_msg = get_error_message("node_not_found", node_id="123")
```

### model_config.py
Bedrock model configuration and management.

**Features:**
- Model parameter presets
- Agent-specific configurations
- Token management
- Model selection helpers

**Usage:**
```python
from config import get_model_config, AgentName, estimate_token_count

# Get model config for agent
model_config = get_model_config(AgentName.GRAPH)

# Use in Strands Agent
from strands.models import BedrockModel

model = BedrockModel(**model_config.to_dict())

# Estimate tokens
text = "This is a sample text"
token_count = estimate_token_count(text)
```

## Configuration Files

Configuration is stored in YAML files under `deployment/`:

```
deployment/
├── dev/
│   └── config.yaml      # Development configuration
├── prod/
│   └── config.yaml      # Production configuration
└── test/
    └── config.yaml      # Test configuration
```

### Configuration Structure

```yaml
environment: development
region: us-west-2

agents:
  orchestrator:
    name: interlinked-aos-dev-orchestrator
    model: anthropic.claude-3-5-sonnet-20241022-v2:0
    description: "Main orchestrator agent"
  
  graph:
    name: interlinked-aos-dev-graph-agent
    model: anthropic.claude-3-5-sonnet-20241022-v2:0
    description: "Graph operations agent"

neo4j:
  connection_mode: direct
  timeout: 30
  max_retry: 3

agentcore:
  memory:
    enabled: true
    retention_days: 7
  
  observability:
    enabled: true
    trace_model_calls: true
    log_level: INFO

security:
  secrets_provider: env
  allowed_node_labels:
    - Person
    - Organization
  allowed_relationship_types:
    - WORKS_AT
    - MANAGES

performance:
  query_timeout: 30
  max_query_complexity: 1000
```

## Environment Variables

Environment variables override YAML configuration:

```bash
# Environment selection
export ENVIRONMENT=production

# AWS Configuration
export AWS_REGION=us-west-2
export AWS_ACCOUNT_ID=123456789012

# Neo4j Configuration
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password

# Gateway Configuration
export GATEWAY_ENDPOINT=https://api.example.com

# Logging
export LOG_LEVEL=INFO

# AgentCore Identity (production)
export COGNITO_USER_POOL_ID=us-west-2_xxx
export COGNITO_CLIENT_ID=xxx
```

## Model Configuration

### Preset Configurations

```python
from config import REASONING_MODEL, FAST_MODEL, PRECISE_MODEL

# High-quality reasoning
model = BedrockModel(**REASONING_MODEL.to_dict())

# Fast responses
model = BedrockModel(**FAST_MODEL.to_dict())

# Precise outputs
model = BedrockModel(**PRECISE_MODEL.to_dict())
```

### Agent-Specific Models

```python
from config import AGENT_MODEL_CONFIGS, AgentName

# Get configuration for specific agent
graph_config = AGENT_MODEL_CONFIGS[AgentName.GRAPH]

# Orchestrator uses more deterministic settings
orchestrator_config = AGENT_MODEL_CONFIGS[AgentName.ORCHESTRATOR]
# Temperature: 0.5 for consistent routing

# Analyzer uses balanced settings
analyzer_config = AGENT_MODEL_CONFIGS[AgentName.ANALYZER]
# Temperature: 0.7 for nuanced analysis
```

### Custom Models

```python
from config import create_custom_model_config

custom_config = create_custom_model_config(
    model_id="anthropic.claude-3-opus-20240229-v1:0",
    max_tokens=8192,
    temperature=0.9,
    top_p=0.95
)
```

## Constants Usage

### Enums

```python
from config import NodeLabel, RelationshipType, OperationType

# Node labels
person_label = NodeLabel.PERSON.value  # "Person"
org_label = NodeLabel.ORGANIZATION.value  # "Organization"

# Relationship types
works_at = RelationshipType.WORKS_AT.value  # "WORKS_AT"

# Operation types
op_type = OperationType.SEARCH  # For routing
```

### Default Values

```python
from config import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DEFAULT_QUERY_TIMEOUT,
    MAX_BULK_CREATE
)

# Use in queries
limit = request.get("limit", DEFAULT_PAGE_SIZE)  # 50
timeout = DEFAULT_QUERY_TIMEOUT  # 30 seconds

# Validate bulk operations
if len(items) > MAX_BULK_CREATE:
    raise ValidationError(f"Cannot create more than {MAX_BULK_CREATE} items")
```

### Messages

```python
from config import get_error_message, get_success_message

# Error messages
error = get_error_message("node_not_found", node_id="123")
# "Node with ID '123' not found"

# Success messages
success = get_success_message("node_created")
# "Node created successfully"
```

## Loading Configuration

### Basic Loading

```python
from config import get_config

# Load configuration (auto-detects environment)
config = get_config()

# Access configuration values
region = config.region
environment = config.environment
```

### Environment-Specific Loading

```python
from config import load_config

# Load specific environment
dev_config = load_config("development")
prod_config = load_config("production")
```

### Reload Configuration

```python
from config import get_config

# Force reload (useful for tests)
config = get_config(reload=True)
```

## Best Practices

1. **Use environment variables for secrets:**
   ```python
   # Good: Use env vars for sensitive data
   neo4j_password = os.getenv("NEO4J_PASSWORD")
   
   # Bad: Don't hardcode secrets in YAML
   ```

2. **Use enums for type safety:**
   ```python
   # Good: Type-safe enum
   label = NodeLabel.PERSON.value
   
   # Bad: Magic strings
   label = "Person"
   ```

3. **Centralize default values:**
   ```python
   # Good: Use constant
   from config import DEFAULT_PAGE_SIZE
   limit = request.get("limit", DEFAULT_PAGE_SIZE)
   
   # Bad: Magic number
   limit = request.get("limit", 50)
   ```

4. **Use message templates:**
   ```python
   # Good: Centralized message
   error = get_error_message("node_not_found", node_id=node_id)
   
   # Bad: Inline string
   error = f"Node with ID '{node_id}' not found"
   ```

## Testing

```python
from config import load_config

def test_configuration_loading():
    # Load test configuration
    config = load_config("test")
    
    assert config.environment == "test"
    assert config.is_development() == False
    
    # Test agent config
    graph_config = config.get_agent_config("graph")
    assert "model" in graph_config
```

