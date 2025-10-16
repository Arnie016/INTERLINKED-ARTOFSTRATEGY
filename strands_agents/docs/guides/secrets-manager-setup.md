# AWS Secrets Manager Setup Guide

This guide explains how to set up and use AWS Secrets Manager for secure credential management in production environments.

## Overview

The Strands Agents project supports two credential management strategies:

1. **Development**: `.env` files for local development
2. **Production/Staging**: AWS Secrets Manager for secure, centralized credential management

The system automatically detects the environment and uses the appropriate strategy.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Secret Structure](#secret-structure)
- [Creating Secrets](#creating-secrets)
- [Configuration](#configuration)
- [Usage](#usage)
- [Caching](#caching)
- [Fallback Mechanism](#fallback-mechanism)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### AWS Credentials

Ensure your AWS credentials are configured:

```bash
# Option 1: AWS CLI configuration
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
```

### Required Permissions

Your IAM user or role needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-west-2:*:secret:interlinked-aos-*"
    }
  ]
}
```

### Python Dependencies

Install boto3 if not already installed:

```bash
pip install boto3
```

## Secret Structure

Secrets must follow this JSON structure:

```json
{
  "uri": "bolt+s://your-neo4j-instance.databases.neo4j.io:7687",
  "username": "neo4j",
  "password": "your-secure-password",
  "database": "neo4j"
}
```

### Required Fields

- `uri`: Neo4j connection URI (bolt://, bolt+s://, neo4j://, or neo4j+s://)
- `username`: Neo4j username
- `password`: Neo4j password

### Optional Fields

- `database`: Neo4j database name (defaults to "neo4j" if not provided)

## Creating Secrets

### Naming Convention

Secrets follow the naming pattern: `interlinked-aos-<environment>/neo4j`

Examples:
- Development: `interlinked-aos-development/neo4j`
- Staging: `interlinked-aos-staging/neo4j`
- Production: `interlinked-aos-production/neo4j`

### Method 1: AWS CLI

```bash
# Create secret for production
aws secretsmanager create-secret \
  --name interlinked-aos-production/neo4j \
  --description "Neo4j credentials for production environment" \
  --secret-string '{
    "uri": "bolt+s://prod.neo4j.io:7687",
    "username": "neo4j",
    "password": "your-secure-password",
    "database": "neo4j"
  }' \
  --region us-west-2

# Create secret for staging
aws secretsmanager create-secret \
  --name interlinked-aos-staging/neo4j \
  --description "Neo4j credentials for staging environment" \
  --secret-string '{
    "uri": "bolt+s://staging.neo4j.io:7687",
    "username": "neo4j",
    "password": "your-secure-password",
    "database": "neo4j"
  }' \
  --region us-west-2
```

### Method 2: AWS Console

1. Navigate to AWS Secrets Manager
2. Click "Store a new secret"
3. Select "Other type of secret"
4. Add the key-value pairs (uri, username, password, database)
5. Name the secret following the convention: `interlinked-aos-<environment>/neo4j`
6. Complete the wizard

### Method 3: Python Helper

Use the provided helper function:

```python
from src.config.secrets_manager import create_secret_json

# Generate JSON for the secret
secret_json = create_secret_json(
    uri="bolt+s://prod.neo4j.io:7687",
    username="neo4j",
    password="your-secure-password",
    database="neo4j"
)

# Upload using boto3
import boto3
client = boto3.client('secretsmanager', region_name='us-west-2')

client.create_secret(
    Name='interlinked-aos-production/neo4j',
    SecretString=secret_json,
    Description='Neo4j credentials for production'
)
```

## Configuration

### Environment Detection

The system automatically detects the environment:

```python
# Uses ENVIRONMENT env var, defaults to 'development'
config = get_neo4j_config()

# Explicitly specify environment
config = get_neo4j_config(environment='production')
```

### Environment Variable

Set the `ENVIRONMENT` variable to control which secret is loaded:

```bash
export ENVIRONMENT=production  # Uses interlinked-aos-production/neo4j
export ENVIRONMENT=staging     # Uses interlinked-aos-staging/neo4j
export ENVIRONMENT=development # Uses .env file
```

### Force Secrets Manager Usage

Override auto-detection:

```python
# Force Secrets Manager even in development
config = get_neo4j_config(
    environment='development',
    use_secrets_manager=True
)

# Force .env file even in production (not recommended)
config = get_neo4j_config(
    environment='production',
    use_secrets_manager=False
)
```

## Usage

### Basic Usage

```python
from src.config import get_neo4j_config
from neo4j import GraphDatabase

# Get configuration (auto-detects environment)
config = get_neo4j_config()

# Create Neo4j driver
driver = GraphDatabase.driver(
    config.uri,
    auth=(config.username, config.password.get_secret_value()),
    **config.get_driver_config()
)
```

### Direct Credentials Retrieval

```python
from src.config.secrets_manager import get_neo4j_credentials_from_secrets

# Get credentials for specific environment
credentials = get_neo4j_credentials_from_secrets(
    environment='production',
    region_name='us-west-2'
)

# Access credentials
uri = credentials['uri']
username = credentials['username']
password = credentials['password']
database = credentials['database']
```

### Using the Client Directly

```python
from src.config.secrets_manager import SecretsManagerClient

# Initialize client
client = SecretsManagerClient(
    region_name='us-west-2',
    cache_ttl=300,  # 5 minutes
    enable_fallback=True
)

# Retrieve secret
secret = client.get_secret('interlinked-aos-production/neo4j')

# Force refresh (bypass cache)
secret = client.refresh_secret('interlinked-aos-production/neo4j')
```

## Caching

### Cache Behavior

- Secrets are cached for 5 minutes (300 seconds) by default
- Cache reduces API calls to AWS Secrets Manager
- Cache is in-memory and cleared on application restart

### Custom Cache TTL

```python
from src.config.secrets_manager import SecretsManagerClient

# Custom cache duration (10 minutes)
client = SecretsManagerClient(cache_ttl=600)
```

### Disable Caching

```python
# Bypass cache for a single request
secret = client.get_secret('secret-name', use_cache=False)
```

### Clear Cache

```python
# Clear specific secret
client.clear_cache('interlinked-aos-production/neo4j')

# Clear all cached secrets
client.clear_cache()
```

## Fallback Mechanism

### Automatic Fallback

If AWS Secrets Manager fails, the system automatically falls back to environment variables:

```python
# Enable fallback (default)
credentials = get_neo4j_credentials_from_secrets(
    environment='production',
    enable_fallback=True
)
```

### Disable Fallback

For strict production environments:

```python
# Raise error if Secrets Manager fails
credentials = get_neo4j_credentials_from_secrets(
    environment='production',
    enable_fallback=False
)
```

### Fallback Order

1. AWS Secrets Manager
2. Environment variables (if fallback enabled):
   - `NEO4J_URI`
   - `NEO4J_USERNAME`
   - `NEO4J_PASSWORD`
   - `NEO4J_DATABASE`

## Best Practices

### 1. Secret Rotation

Enable automatic rotation in AWS Secrets Manager:

```bash
aws secretsmanager rotate-secret \
  --secret-id interlinked-aos-production/neo4j \
  --rotation-lambda-arn arn:aws:lambda:us-west-2:123456789012:function:SecretsManagerRotation \
  --rotation-rules AutomaticallyAfterDays=30
```

### 2. Separate Secrets per Environment

Always maintain separate secrets for each environment:

- ✅ `interlinked-aos-development/neo4j`
- ✅ `interlinked-aos-staging/neo4j`
- ✅ `interlinked-aos-production/neo4j`
- ❌ Don't reuse production secrets in other environments

### 3. Use IAM Roles

When deploying to AWS (Lambda, ECS, etc.):

```python
# IAM role is automatically used, no credentials needed
credentials = get_neo4j_credentials_from_secrets(
    environment='production'
)
```

### 4. Enable CloudWatch Logging

Monitor secret access:

```bash
aws secretsmanager put-resource-policy \
  --secret-id interlinked-aos-production/neo4j \
  --resource-policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "cloudwatch.amazonaws.com"},
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "*"
    }]
  }'
```

### 5. Use Encryption

Always use SSL/TLS for Neo4j connections in production:

```json
{
  "uri": "bolt+s://prod.neo4j.io:7687",  // Note the +s for SSL
  "username": "neo4j",
  "password": "password",
  "database": "neo4j"
}
```

## Troubleshooting

### Error: "boto3 is required"

**Solution**: Install boto3

```bash
pip install boto3
```

### Error: "Secret not found"

**Possible causes**:
1. Secret doesn't exist in AWS Secrets Manager
2. Wrong region specified
3. Incorrect secret name

**Solution**:

```bash
# List all secrets
aws secretsmanager list-secrets --region us-west-2

# Verify secret exists
aws secretsmanager describe-secret \
  --secret-id interlinked-aos-production/neo4j \
  --region us-west-2
```

### Error: "AccessDeniedException"

**Cause**: Insufficient IAM permissions

**Solution**: Ensure your IAM user/role has the required permissions (see [Prerequisites](#required-permissions))

### Error: "Missing required keys"

**Cause**: Secret structure is invalid

**Solution**: Verify secret contains uri, username, and password:

```bash
aws secretsmanager get-secret-value \
  --secret-id interlinked-aos-production/neo4j \
  --region us-west-2 \
  --query 'SecretString' \
  --output text
```

### Error: "AWS credentials not configured"

**Solution**: Configure AWS credentials:

```bash
aws configure
# OR
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

### Cache Issues

If you've updated a secret but still seeing old values:

```python
from src.config.secrets_manager import get_secrets_client

client = get_secrets_client()
client.clear_cache('interlinked-aos-production/neo4j')
```

## Example: Complete Setup

### 1. Create the Secret

```bash
aws secretsmanager create-secret \
  --name interlinked-aos-production/neo4j \
  --secret-string '{
    "uri": "bolt+s://prod.neo4j.io:7687",
    "username": "neo4j",
    "password": "super-secure-password-123",
    "database": "neo4j"
  }' \
  --region us-west-2
```

### 2. Configure Application

```bash
export ENVIRONMENT=production
export AWS_DEFAULT_REGION=us-west-2
```

### 3. Use in Code

```python
from src.config import get_neo4j_config
from neo4j import GraphDatabase

# Automatically loads from Secrets Manager in production
config = get_neo4j_config()

# Create driver
driver = GraphDatabase.driver(
    config.uri,
    auth=(config.username, config.password.get_secret_value()),
    **config.get_driver_config()
)

# Use driver
with driver.session(database=config.database) as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    print(f"Node count: {result.single()['count']}")

driver.close()
```

## Related Documentation

- [Neo4j Configuration Guide](./neo4j-setup.md)
- [AWS Setup Guide](./aws-setup.md)
- [Environment Configuration](../implementation/setup.md)
- [Configuration Module Reference](../../src/config/README.md)

## Security Notes

⚠️ **Important Security Considerations**:

1. **Never commit secrets to version control**
2. **Use different credentials for each environment**
3. **Enable MFA for AWS console access**
4. **Regularly rotate secrets**
5. **Monitor secret access via CloudWatch**
6. **Use least-privilege IAM policies**
7. **Enable encryption in transit (bolt+s://)**
8. **Consider using AWS KMS for secret encryption**

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review AWS Secrets Manager logs in CloudWatch
3. Verify IAM permissions
4. Check the application logs for detailed error messages

