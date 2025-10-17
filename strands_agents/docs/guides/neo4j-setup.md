# Neo4j Configuration Guide

This guide explains how to configure Neo4j database connections for the Strands Agents project in both local development and production environments.

## Overview

The Neo4j configuration module (`src/config/neo4j_config.py`) provides:

- **Environment variable loading** from `.env` files (development)
- **AWS Secrets Manager integration** (production - to be implemented in task 2.2)
- **Secure credential handling** with no exposure in logs
- **Connection pooling** configuration
- **Environment-specific presets** (development, test, production)
- **Gateway mode toggle** for AgentCore Gateway access

## Quick Start - Local Development

### 1. Create Environment File

Create a `.env` file in the project root (`strands_agents/.env`):

```bash
# Required: Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password-here
NEO4J_DATABASE=neo4j

# Optional: Connection Pool Settings
NEO4J_MAX_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30

# Optional: Feature Flags
NEO4J_ENABLE_SSL=true
NEO4J_ENABLE_QUERY_LOGGING=false
NEO4J_ENABLE_METRICS=true

# Optional: Gateway Mode (for production)
NEO4J_USE_GATEWAY=false
NEO4J_GATEWAY_URL=

# Environment
ENVIRONMENT=development
```

### 2. Neo4j Aura Cloud Setup

If using Neo4j Aura (recommended for production):

```bash
NEO4J_URI=neo4j+s://your-instance-id.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-generated-password
NEO4J_DATABASE=neo4j
```

### 3. Local Neo4j Instance

If running Neo4j locally:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

## Usage in Code

### Basic Configuration Loading

```python
from src.config import get_neo4j_config

# Load configuration from environment
config = get_neo4j_config()

# Access configuration values
print(config.uri)  # bolt://localhost:7687
print(config.username)  # neo4j
print(config.database)  # neo4j
# Password is protected
password = config.password.get_secret_value()
```

### Creating Neo4j Driver

```python
from neo4j import GraphDatabase
from src.config import get_neo4j_config

# Get configuration
config = get_neo4j_config()

# Create driver with configuration
driver = GraphDatabase.driver(
    config.uri,
    auth=(config.username, config.password.get_secret_value()),
    **config.get_driver_config()
)

# Use driver
with driver.session(database=config.database) as session:
    result = session.run("RETURN 'Hello Neo4j!' as message")
    print(result.single()['message'])

driver.close()
```

### Environment-Specific Configuration

The module automatically applies environment-specific presets:

```python
# Development environment
config = get_neo4j_config(environment="development")
# - max_connection_pool_size: 10
# - connection_timeout: 15 seconds
# - enable_query_logging: True

# Test environment
config = get_neo4j_config(environment="test")
# - max_connection_pool_size: 25
# - connection_timeout: 20 seconds
# - enable_query_logging: True

# Production environment
config = get_neo4j_config(environment="production")
# - max_connection_pool_size: 50
# - connection_timeout: 30 seconds
# - enable_query_logging: False (for performance)
```

### Custom Configuration

```python
from src.config import create_custom_config

# Create custom configuration with overrides
config = create_custom_config({
    "max_connection_pool_size": 100,
    "enable_query_logging": True,
    "connection_timeout": 60
})
```

### Singleton Instance (Recommended)

For better performance, use the singleton instance pattern:

```python
from src.config import get_config_instance

# First call loads and caches configuration
config = get_config_instance()

# Subsequent calls return cached instance
config = get_config_instance()

# Reset cache if needed (e.g., in tests)
from src.config import reset_config_instance
reset_config_instance()
```

## Configuration Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j database URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `your-password` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_DATABASE` | `neo4j` | Database name |
| `NEO4J_MAX_POOL_SIZE` | `50` | Maximum connection pool size (1-1000) |
| `NEO4J_CONNECTION_TIMEOUT` | `30` | Connection timeout in seconds (1-300) |
| `NEO4J_ENABLE_SSL` | `true` | Enable SSL/TLS connections |
| `NEO4J_ENABLE_QUERY_LOGGING` | `false` | Enable query logging |
| `NEO4J_ENABLE_METRICS` | `true` | Enable metrics collection |
| `NEO4J_USE_GATEWAY` | `false` | Use AgentCore Gateway instead of direct connection |
| `NEO4J_GATEWAY_URL` | `None` | Gateway URL (required if USE_GATEWAY=true) |
| `ENVIRONMENT` | `development` | Environment name (development/test/production) |

### Valid URI Schemes

The configuration validates URI schemes to ensure proper Neo4j connection:

- `bolt://` - Unencrypted Bolt protocol
- `bolt+s://` - Bolt with TLS encryption
- `bolt+ssc://` - Bolt with self-signed certificate
- `neo4j://` - Neo4j protocol (routes through cluster)
- `neo4j+s://` - Neo4j with TLS encryption
- `neo4j+ssc://` - Neo4j with self-signed certificate

**Recommended:**
- Development: `bolt://` (local) or `neo4j+s://` (Aura)
- Production: `neo4j+s://` (Aura) or `bolt+s://` (hosted)

### SSL/TLS Trust Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `TRUST_SYSTEM_CA_SIGNED_CERTIFICATES` | Default, trust system CAs | Production with valid certificates |
| `TRUST_ALL_CERTIFICATES` | Trust all certificates | Development only (insecure) |
| `TRUST_CUSTOM_CA_SIGNED_CERTIFICATES` | Trust custom CA | Custom certificate authority |

## Gateway Mode

Gateway mode allows routing Neo4j requests through AgentCore Gateway for enhanced security and access control.

### Enable Gateway Mode

```bash
# In .env file
NEO4J_USE_GATEWAY=true
NEO4J_GATEWAY_URL=https://your-gateway-endpoint.amazonaws.com
```

### Check Gateway Mode in Code

```python
from src.config import is_gateway_mode_enabled, get_gateway_url

if is_gateway_mode_enabled():
    gateway_url = get_gateway_url()
    print(f"Using Gateway at: {gateway_url}")
else:
    print("Using direct Neo4j connection")
```

## Security Best Practices

### 1. Never Commit Credentials

Add `.env` to `.gitignore`:

```gitignore
# Environment files
.env
.env.local
.env.*.local
```

### 2. Use SecretStr for Passwords

The configuration automatically uses Pydantic's `SecretStr` to protect passwords:

```python
config = get_neo4j_config()

# WRONG: This won't work
# print(config.password)  # Prints: SecretStr('**********')

# CORRECT: Use get_secret_value()
password = config.password.get_secret_value()
```

### 3. Safe Logging

Use the safe connection string for logging:

```python
config = get_neo4j_config()

# Safe for logging (no password)
safe_string = config.get_connection_string_safe()
logger.info(f"Connecting to: {safe_string}")
# Output: "bolt://localhost:7687 (user: neo4j, database: neo4j)"
```

### 4. Validate Environment Variables

Before running, validate that all required variables are set:

```python
from src.config import validate_required_env_vars

validation = validate_required_env_vars()

if not all(validation.values()):
    missing = [k for k, v in validation.items() if not v]
    raise ConfigurationError(f"Missing required variables: {missing}")
```

## Testing

The configuration module includes comprehensive unit tests:

```bash
# Run all configuration tests
cd strands_agents
source venv/bin/activate
python -m pytest tests/test_neo4j_config.py -v

# Run specific test class
python -m pytest tests/test_neo4j_config.py::TestNeo4jConnectionConfig -v

# Run with coverage
python -m pytest tests/test_neo4j_config.py --cov=src/config/neo4j_config --cov-report=html
```

### Test Neo4j Connection

Test your configuration with the Neo4j connection test:

```bash
cd strands_agents
source venv/bin/activate
python backend/tests/test_neo4j_connection.py
```

## Troubleshooting

### Connection Failed

**Error:** `Unable to retrieve routing information`

- Check that your URI is correct
- Verify the Neo4j instance is running
- Use `neo4j+s://` or `neo4j+ssc://` for Aura
- Wait 60-90 seconds after creating a new Aura instance

**Error:** `Authentication failed`

- Verify username and password in `.env`
- Check credentials in Neo4j console
- Ensure password doesn't contain special characters that need escaping

**Error:** `Service unavailable`

- Check if Neo4j instance is running
- Verify network connectivity
- Check firewall rules (port 7687 for Bolt)

### Configuration Not Loading

**Issue:** Environment variables not loading

```python
# Debug: Check if .env file exists
from pathlib import Path
env_path = Path.cwd() / ".env"
print(f"Env file exists: {env_path.exists()}")

# Debug: Check environment variables
import os
print(f"NEO4J_URI: {os.getenv('NEO4J_URI')}")

# Force reload
from src.config import load_dotenv_if_exists
loaded = load_dotenv_if_exists()
print(f"Env file loaded: {loaded}")
```

### Validation Errors

**Error:** `Neo4j URI must start with bolt://...`

- Check URI format in `.env`
- Use one of the valid schemes (bolt://, neo4j://, etc.)

**Error:** `Connection pool size must be between 1 and 1000`

- Check `NEO4J_MAX_POOL_SIZE` value
- Ensure it's a number between 1-1000

## Production Deployment

### AWS Secrets Manager (Coming in Task 2.2)

For production, credentials will be stored in AWS Secrets Manager:

```bash
# Secret name pattern
interlinked-aos-{environment}

# Example: Development
interlinked-aos-dev

# Example: Production
interlinked-aos-prod
```

The configuration module will automatically:
1. Detect production environment
2. Retrieve credentials from Secrets Manager
3. Cache credentials to minimize API calls
4. Handle secret rotation automatically

### Environment Variables in Production

Set environment variables in your deployment:

```bash
# AWS ECS/Fargate
ENVIRONMENT=production
AWS_REGION=us-west-2
AWS_SECRET_NAME=interlinked-aos-prod

# Gateway mode for production
NEO4J_USE_GATEWAY=true
NEO4J_GATEWAY_URL=https://your-gateway.amazonaws.com
```

## Related Documentation

- [Strands Agents README](../README.md) - Main project documentation
- [Configuration README](../src/config/README.md) - Configuration module details
- [Utilities README](../src/utils/README.md) - Utility functions
- [Testing README](../tests/README_TESTING.md) - Testing guide

## Support

For issues or questions:
1. Check this documentation
2. Review test files for examples
3. Check AWS Bedrock AgentCore documentation
4. Review Strands Agents documentation

