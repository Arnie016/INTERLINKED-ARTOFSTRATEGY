"""
AWS Secrets Manager Integration Module

This module provides secure credential retrieval from AWS Secrets Manager for production
deployments. It implements caching, error handling, and fallback mechanisms to ensure
reliable access to Neo4j credentials.

Features:
- Secret retrieval from AWS Secrets Manager
- LRU cache with configurable TTL to minimize API calls
- Environment-aware secret path construction (interlinked-aos-<env>)
- Graceful fallback to environment variables
- Secure secret handling in memory
- Automatic secret rotation support
- Comprehensive error handling
"""

import json
import os
import time
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache
from datetime import datetime, timedelta

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception
    PartialCredentialsError = Exception

try:
    from .constants import Environment
    from ..utils.errors import ConfigurationError
    from ..utils.logging import get_logger
except ImportError:
    from constants import Environment
    from utils.errors import ConfigurationError
    from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Cache configuration
DEFAULT_CACHE_TTL = 300  # 5 minutes
_secret_cache: Dict[str, Tuple[Dict[str, Any], float]] = {}


class SecretsManagerClient:
    """
    AWS Secrets Manager client wrapper with caching and error handling.
    
    This class provides a high-level interface for retrieving secrets from
    AWS Secrets Manager with built-in caching, fallbacks, and error handling.
    """
    
    def __init__(
        self,
        region_name: str = "us-west-2",
        cache_ttl: int = DEFAULT_CACHE_TTL,
        enable_fallback: bool = True
    ):
        """
        Initialize Secrets Manager client.
        
        Args:
            region_name: AWS region name (default: us-west-2)
            cache_ttl: Cache time-to-live in seconds (default: 300)
            enable_fallback: Whether to fallback to environment variables (default: True)
        
        Raises:
            ConfigurationError: If boto3 is not available
        """
        if not BOTO3_AVAILABLE:
            raise ConfigurationError(
                "boto3 is required for AWS Secrets Manager integration. "
                "Install it with: pip install boto3"
            )
        
        self.region_name = region_name
        self.cache_ttl = cache_ttl
        self.enable_fallback = enable_fallback
        
        # Initialize AWS client
        try:
            self.client = boto3.client(
                'secretsmanager',
                region_name=region_name
            )
            logger.info(f"Initialized Secrets Manager client for region: {region_name}")
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"AWS credentials not configured: {str(e)}")
            if not enable_fallback:
                raise ConfigurationError(
                    "AWS credentials not configured and fallback disabled"
                ) from e
            self.client = None
    
    def get_secret(
        self,
        secret_name: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name or ARN of the secret
            use_cache: Whether to use cached values (default: True)
        
        Returns:
            Dict containing secret key-value pairs
        
        Raises:
            ConfigurationError: If secret retrieval fails and fallback is disabled
        """
        # Check cache first
        if use_cache and secret_name in _secret_cache:
            cached_value, cached_time = _secret_cache[secret_name]
            if time.time() - cached_time < self.cache_ttl:
                logger.debug(f"Retrieved secret from cache: {secret_name}")
                return cached_value
            else:
                logger.debug(f"Cache expired for secret: {secret_name}")
                del _secret_cache[secret_name]
        
        # Try to retrieve from AWS Secrets Manager
        if self.client is not None:
            try:
                logger.info(f"Retrieving secret from AWS Secrets Manager: {secret_name}")
                response = self.client.get_secret_value(SecretId=secret_name)
                
                # Parse secret string
                if 'SecretString' in response:
                    secret_dict = json.loads(response['SecretString'])
                else:
                    # Binary secrets not supported for Neo4j config
                    logger.error(f"Binary secret not supported: {secret_name}")
                    raise ConfigurationError(
                        f"Secret {secret_name} contains binary data, expected JSON string"
                    )
                
                # Update cache
                if use_cache:
                    _secret_cache[secret_name] = (secret_dict, time.time())
                    logger.debug(f"Cached secret: {secret_name}")
                
                return secret_dict
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                logger.error(
                    f"Failed to retrieve secret {secret_name}: {error_code}",
                    extra={"error_code": error_code}
                )
                
                # Handle specific error cases
                if error_code == 'ResourceNotFoundException':
                    logger.warning(f"Secret not found: {secret_name}")
                elif error_code == 'InvalidRequestException':
                    logger.warning(f"Invalid request for secret: {secret_name}")
                elif error_code == 'InvalidParameterException':
                    logger.warning(f"Invalid parameter for secret: {secret_name}")
                elif error_code == 'DecryptionFailure':
                    logger.error(f"Failed to decrypt secret: {secret_name}")
                elif error_code == 'InternalServiceError':
                    logger.error(f"AWS service error retrieving secret: {secret_name}")
                
                if not self.enable_fallback:
                    raise ConfigurationError(
                        f"Failed to retrieve secret {secret_name}: {error_code}"
                    ) from e
        
        # Fallback to environment variables
        if self.enable_fallback:
            logger.info(f"Attempting fallback to environment variables for: {secret_name}")
            return self._get_secret_from_env(secret_name)
        
        raise ConfigurationError(
            f"Failed to retrieve secret {secret_name} and fallback is disabled"
        )
    
    def _get_secret_from_env(self, secret_name: str) -> Dict[str, Any]:
        """
        Fallback to environment variables if AWS Secrets Manager is unavailable.
        
        Args:
            secret_name: Secret name (used for logging only)
        
        Returns:
            Dict containing Neo4j credentials from environment variables
        
        Raises:
            ConfigurationError: If required environment variables are missing
        """
        logger.warning(
            f"Using environment variable fallback for secret: {secret_name}"
        )
        
        # Load required Neo4j credentials from environment
        neo4j_uri = os.getenv('NEO4J_URI')
        neo4j_username = os.getenv('NEO4J_USERNAME')
        neo4j_password = os.getenv('NEO4J_PASSWORD')
        neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        # Validate required variables are set
        if not all([neo4j_uri, neo4j_username, neo4j_password]):
            missing = []
            if not neo4j_uri:
                missing.append('NEO4J_URI')
            if not neo4j_username:
                missing.append('NEO4J_USERNAME')
            if not neo4j_password:
                missing.append('NEO4J_PASSWORD')
            
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        return {
            'uri': neo4j_uri,
            'username': neo4j_username,
            'password': neo4j_password,
            'database': neo4j_database
        }
    
    def clear_cache(self, secret_name: Optional[str] = None) -> None:
        """
        Clear cached secrets.
        
        Args:
            secret_name: Specific secret to clear, or None to clear all
        """
        if secret_name is None:
            _secret_cache.clear()
            logger.info("Cleared all cached secrets")
        elif secret_name in _secret_cache:
            del _secret_cache[secret_name]
            logger.info(f"Cleared cached secret: {secret_name}")
    
    def refresh_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Force refresh of a secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name or ARN of the secret
        
        Returns:
            Dict containing refreshed secret key-value pairs
        """
        self.clear_cache(secret_name)
        return self.get_secret(secret_name, use_cache=True)


def get_secret_name_for_environment(environment: str) -> str:
    """
    Construct secret name following the naming convention.
    
    Format: interlinked-aos-<env>/neo4j
    
    Args:
        environment: Environment name (development, staging, production)
    
    Returns:
        Secret name string
    
    Example:
        >>> get_secret_name_for_environment("production")
        'interlinked-aos-production/neo4j'
    """
    # Normalize environment name
    env_normalized = environment.lower().strip()
    
    # Map common aliases
    env_mapping = {
        'dev': 'development',
        'develop': 'development',
        'prod': 'production',
        'stage': 'staging',
        'stg': 'staging'
    }
    
    env_name = env_mapping.get(env_normalized, env_normalized)
    
    # Construct secret name
    secret_name = f"interlinked-aos-{env_name}/neo4j"
    
    logger.debug(f"Constructed secret name: {secret_name} for environment: {environment}")
    
    return secret_name


def get_neo4j_credentials_from_secrets(
    environment: Optional[str] = None,
    region_name: str = "us-west-2",
    cache_ttl: int = DEFAULT_CACHE_TTL,
    enable_fallback: bool = True
) -> Dict[str, Any]:
    """
    Retrieve Neo4j credentials from AWS Secrets Manager.
    
    This is the primary function for retrieving production credentials.
    It handles environment detection, secret retrieval, caching, and fallback.
    
    Args:
        environment: Target environment (development/staging/production).
                    If None, uses ENVIRONMENT env var or defaults to 'production'
        region_name: AWS region name (default: us-west-2)
        cache_ttl: Cache time-to-live in seconds (default: 300)
        enable_fallback: Whether to fallback to environment variables (default: True)
    
    Returns:
        Dict containing Neo4j credentials:
            - uri: Neo4j connection URI
            - username: Neo4j username
            - password: Neo4j password
            - database: Neo4j database name
    
    Raises:
        ConfigurationError: If credentials cannot be retrieved
    
    Example:
        >>> credentials = get_neo4j_credentials_from_secrets(environment="production")
        >>> driver = GraphDatabase.driver(
        ...     credentials['uri'],
        ...     auth=(credentials['username'], credentials['password'])
        ... )
    """
    # Detect environment
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'production')
    
    logger.info(
        f"Retrieving Neo4j credentials for environment: {environment}",
        extra={"environment": environment, "region": region_name}
    )
    
    # Get secret name
    secret_name = get_secret_name_for_environment(environment)
    
    # Initialize Secrets Manager client
    client = SecretsManagerClient(
        region_name=region_name,
        cache_ttl=cache_ttl,
        enable_fallback=enable_fallback
    )
    
    # Retrieve credentials
    credentials = client.get_secret(secret_name)
    
    # Validate credential structure
    required_keys = ['uri', 'username', 'password']
    missing_keys = [key for key in required_keys if key not in credentials]
    
    if missing_keys:
        raise ConfigurationError(
            f"Secret {secret_name} missing required keys: {', '.join(missing_keys)}"
        )
    
    # Ensure database is present (with default)
    if 'database' not in credentials:
        credentials['database'] = 'neo4j'
        logger.debug("Using default database name: neo4j")
    
    logger.info(
        f"Successfully retrieved Neo4j credentials",
        extra={
            "environment": environment,
            "uri": credentials['uri'],
            "database": credentials['database']
        }
    )
    
    return credentials


def validate_secret_structure(secret_dict: Dict[str, Any]) -> bool:
    """
    Validate that a secret dictionary has the required structure for Neo4j.
    
    Args:
        secret_dict: Dictionary to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = ['uri', 'username', 'password']
    
    for key in required_keys:
        if key not in secret_dict:
            logger.error(f"Secret missing required key: {key}")
            return False
        
        if not isinstance(secret_dict[key], str):
            logger.error(f"Secret key {key} must be a string")
            return False
        
        if not secret_dict[key].strip():
            logger.error(f"Secret key {key} cannot be empty")
            return False
    
    return True


def create_secret_json(
    uri: str,
    username: str,
    password: str,
    database: str = "neo4j"
) -> str:
    """
    Create JSON string for storing Neo4j credentials in Secrets Manager.
    
    This utility function helps create properly formatted secrets for upload.
    
    Args:
        uri: Neo4j connection URI
        username: Neo4j username
        password: Neo4j password
        database: Neo4j database name (default: neo4j)
    
    Returns:
        JSON string ready for Secrets Manager
    
    Example:
        >>> secret_json = create_secret_json(
        ...     uri="bolt+s://example.neo4j.io:7687",
        ...     username="neo4j",
        ...     password="secure-password",
        ...     database="neo4j"
        ... )
        >>> # Upload to Secrets Manager
        >>> client.create_secret(
        ...     Name="interlinked-aos-production/neo4j",
        ...     SecretString=secret_json
        ... )
    """
    secret_dict = {
        'uri': uri,
        'username': username,
        'password': password,
        'database': database
    }
    
    return json.dumps(secret_dict, indent=2)


# Global client instance for reuse
_global_client: Optional[SecretsManagerClient] = None


def get_secrets_client(
    region_name: str = "us-west-2",
    cache_ttl: int = DEFAULT_CACHE_TTL
) -> SecretsManagerClient:
    """
    Get or create global Secrets Manager client instance.
    
    Implements singleton pattern for client reuse.
    
    Args:
        region_name: AWS region name (default: us-west-2)
        cache_ttl: Cache time-to-live in seconds (default: 300)
    
    Returns:
        SecretsManagerClient instance
    """
    global _global_client
    
    if _global_client is None:
        _global_client = SecretsManagerClient(
            region_name=region_name,
            cache_ttl=cache_ttl
        )
    
    return _global_client


def reset_secrets_client() -> None:
    """
    Reset global Secrets Manager client instance.
    
    Useful for testing or when configuration needs to change.
    """
    global _global_client
    _global_client = None
    _secret_cache.clear()
    logger.debug("Reset global secrets client and cleared cache")


