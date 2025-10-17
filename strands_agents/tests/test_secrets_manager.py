"""
Tests for AWS Secrets Manager Integration

This module tests the secrets_manager module functionality including:
- Secret retrieval from AWS Secrets Manager
- Caching behavior
- Error handling and fallbacks
- Secret name construction
- Integration with Neo4j configuration
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import the module to test
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.config.secrets_manager import (
    SecretsManagerClient,
    get_neo4j_credentials_from_secrets,
    get_secret_name_for_environment,
    validate_secret_structure,
    create_secret_json,
    get_secrets_client,
    reset_secrets_client,
    _secret_cache
)
from src.utils.errors import ConfigurationError


# Sample secret data for testing
SAMPLE_SECRET = {
    'uri': 'bolt+s://example.neo4j.io:7687',
    'username': 'neo4j',
    'password': 'test-password-123',
    'database': 'neo4j'
}


class TestSecretNameConstruction:
    """Test secret name construction following naming convention."""
    
    def test_production_environment(self):
        """Test secret name for production environment."""
        secret_name = get_secret_name_for_environment('production')
        assert secret_name == 'interlinked-aos-production/neo4j'
    
    def test_staging_environment(self):
        """Test secret name for staging environment."""
        secret_name = get_secret_name_for_environment('staging')
        assert secret_name == 'interlinked-aos-staging/neo4j'
    
    def test_development_environment(self):
        """Test secret name for development environment."""
        secret_name = get_secret_name_for_environment('development')
        assert secret_name == 'interlinked-aos-development/neo4j'
    
    def test_environment_alias_prod(self):
        """Test environment alias 'prod' maps to 'production'."""
        secret_name = get_secret_name_for_environment('prod')
        assert secret_name == 'interlinked-aos-production/neo4j'
    
    def test_environment_alias_dev(self):
        """Test environment alias 'dev' maps to 'development'."""
        secret_name = get_secret_name_for_environment('dev')
        assert secret_name == 'interlinked-aos-development/neo4j'
    
    def test_environment_alias_stage(self):
        """Test environment alias 'stage' maps to 'staging'."""
        secret_name = get_secret_name_for_environment('stage')
        assert secret_name == 'interlinked-aos-staging/neo4j'
    
    def test_case_insensitivity(self):
        """Test environment names are case-insensitive."""
        secret_name = get_secret_name_for_environment('PRODUCTION')
        assert secret_name == 'interlinked-aos-production/neo4j'


class TestSecretValidation:
    """Test secret structure validation."""
    
    def test_valid_secret_structure(self):
        """Test validation passes for valid secret structure."""
        assert validate_secret_structure(SAMPLE_SECRET) is True
    
    def test_missing_uri(self):
        """Test validation fails when uri is missing."""
        secret = SAMPLE_SECRET.copy()
        del secret['uri']
        assert validate_secret_structure(secret) is False
    
    def test_missing_username(self):
        """Test validation fails when username is missing."""
        secret = SAMPLE_SECRET.copy()
        del secret['username']
        assert validate_secret_structure(secret) is False
    
    def test_missing_password(self):
        """Test validation fails when password is missing."""
        secret = SAMPLE_SECRET.copy()
        del secret['password']
        assert validate_secret_structure(secret) is False
    
    def test_empty_uri(self):
        """Test validation fails when uri is empty."""
        secret = SAMPLE_SECRET.copy()
        secret['uri'] = ''
        assert validate_secret_structure(secret) is False
    
    def test_non_string_values(self):
        """Test validation fails when values are not strings."""
        secret = SAMPLE_SECRET.copy()
        secret['username'] = 12345
        assert validate_secret_structure(secret) is False


class TestSecretJsonCreation:
    """Test JSON creation for secrets."""
    
    def test_create_secret_json(self):
        """Test creating JSON string for secret."""
        json_str = create_secret_json(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password123',
            database='neo4j'
        )
        
        # Parse and validate
        secret_dict = json.loads(json_str)
        assert secret_dict['uri'] == 'bolt://localhost:7687'
        assert secret_dict['username'] == 'neo4j'
        assert secret_dict['password'] == 'password123'
        assert secret_dict['database'] == 'neo4j'
    
    def test_default_database(self):
        """Test default database value."""
        json_str = create_secret_json(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password123'
        )
        
        secret_dict = json.loads(json_str)
        assert secret_dict['database'] == 'neo4j'


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 Secrets Manager client."""
    with patch('src.config.secrets_manager.boto3') as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        yield mock_client


@pytest.fixture
def clear_cache():
    """Clear secret cache before each test."""
    _secret_cache.clear()
    yield
    _secret_cache.clear()


class TestSecretsManagerClient:
    """Test SecretsManagerClient class."""
    
    def test_initialization(self, mock_boto3_client):
        """Test client initialization."""
        client = SecretsManagerClient(region_name='us-west-2')
        
        assert client.region_name == 'us-west-2'
        assert client.cache_ttl == 300
        assert client.enable_fallback is True
    
    def test_custom_cache_ttl(self, mock_boto3_client):
        """Test client with custom cache TTL."""
        client = SecretsManagerClient(cache_ttl=600)
        assert client.cache_ttl == 600
    
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    def test_get_secret_success(self, mock_boto3_client, clear_cache):
        """Test successful secret retrieval."""
        # Mock AWS response
        mock_boto3_client.get_secret_value.return_value = {
            'SecretString': json.dumps(SAMPLE_SECRET)
        }
        
        client = SecretsManagerClient()
        secret = client.get_secret('test-secret')
        
        assert secret == SAMPLE_SECRET
        mock_boto3_client.get_secret_value.assert_called_once_with(
            SecretId='test-secret'
        )
    
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    def test_get_secret_with_cache(self, mock_boto3_client, clear_cache):
        """Test secret retrieval uses cache."""
        # Mock AWS response
        mock_boto3_client.get_secret_value.return_value = {
            'SecretString': json.dumps(SAMPLE_SECRET)
        }
        
        client = SecretsManagerClient()
        
        # First call
        secret1 = client.get_secret('test-secret', use_cache=True)
        assert secret1 == SAMPLE_SECRET
        
        # Second call should use cache
        secret2 = client.get_secret('test-secret', use_cache=True)
        assert secret2 == SAMPLE_SECRET
        
        # Should only call AWS once
        assert mock_boto3_client.get_secret_value.call_count == 1
    
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    def test_get_secret_without_cache(self, mock_boto3_client, clear_cache):
        """Test secret retrieval bypasses cache when requested."""
        # Mock AWS response
        mock_boto3_client.get_secret_value.return_value = {
            'SecretString': json.dumps(SAMPLE_SECRET)
        }
        
        client = SecretsManagerClient()
        
        # Both calls should hit AWS
        secret1 = client.get_secret('test-secret', use_cache=False)
        secret2 = client.get_secret('test-secret', use_cache=False)
        
        assert mock_boto3_client.get_secret_value.call_count == 2
    
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password',
        'NEO4J_DATABASE': 'testdb'
    })
    def test_fallback_to_environment(self, mock_boto3_client, clear_cache):
        """Test fallback to environment variables when AWS fails."""
        # Mock AWS failure
        from botocore.exceptions import ClientError
        mock_boto3_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'GetSecretValue'
        )
        
        client = SecretsManagerClient(enable_fallback=True)
        secret = client.get_secret('test-secret')
        
        # Should get values from environment
        assert secret['uri'] == 'bolt://localhost:7687'
        assert secret['username'] == 'neo4j'
        assert secret['password'] == 'password'
        assert secret['database'] == 'testdb'
    
    def test_fallback_disabled_raises_error(self, mock_boto3_client, clear_cache):
        """Test error raised when fallback is disabled."""
        # Mock AWS failure
        from botocore.exceptions import ClientError
        mock_boto3_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'GetSecretValue'
        )
        
        client = SecretsManagerClient(enable_fallback=False)
        
        with pytest.raises(ConfigurationError):
            client.get_secret('test-secret')
    
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    def test_clear_cache_specific_secret(self, mock_boto3_client, clear_cache):
        """Test clearing specific secret from cache."""
        # Mock AWS response
        mock_boto3_client.get_secret_value.return_value = {
            'SecretString': json.dumps(SAMPLE_SECRET)
        }
        
        client = SecretsManagerClient()
        
        # Cache a secret
        client.get_secret('test-secret')
        assert 'test-secret' in _secret_cache
        
        # Clear it
        client.clear_cache('test-secret')
        assert 'test-secret' not in _secret_cache
    
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    def test_clear_all_cache(self, mock_boto3_client, clear_cache):
        """Test clearing all cached secrets."""
        # Mock AWS response
        mock_boto3_client.get_secret_value.return_value = {
            'SecretString': json.dumps(SAMPLE_SECRET)
        }
        
        client = SecretsManagerClient()
        
        # Cache multiple secrets
        client.get_secret('secret-1')
        client.get_secret('secret-2')
        assert len(_secret_cache) == 2
        
        # Clear all
        client.clear_cache()
        assert len(_secret_cache) == 0
    
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    def test_refresh_secret(self, mock_boto3_client, clear_cache):
        """Test forcing refresh of a cached secret."""
        # Mock AWS response
        mock_boto3_client.get_secret_value.return_value = {
            'SecretString': json.dumps(SAMPLE_SECRET)
        }
        
        client = SecretsManagerClient()
        
        # Cache a secret
        client.get_secret('test-secret')
        assert mock_boto3_client.get_secret_value.call_count == 1
        
        # Refresh it (should clear cache and fetch again)
        client.refresh_secret('test-secret')
        assert mock_boto3_client.get_secret_value.call_count == 2


class TestIntegrationWithNeo4jConfig:
    """Test integration with Neo4j configuration."""
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    @patch('src.config.secrets_manager.boto3')
    def test_get_credentials_production(self, mock_boto3, clear_cache):
        """Test getting credentials for production environment."""
        # Mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(SAMPLE_SECRET)
        }
        
        credentials = get_neo4j_credentials_from_secrets(environment='production')
        
        assert credentials == SAMPLE_SECRET
        mock_client.get_secret_value.assert_called_once()
    
    @patch.dict(os.environ, {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    @patch('src.config.secrets_manager.boto3')
    def test_get_credentials_with_fallback(self, mock_boto3, clear_cache):
        """Test credentials fallback to environment variables."""
        # Mock boto3 client failure
        from botocore.exceptions import ClientError
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'GetSecretValue'
        )
        
        credentials = get_neo4j_credentials_from_secrets(
            environment='production',
            enable_fallback=True
        )
        
        # Should get from environment
        assert credentials['uri'] == 'bolt://localhost:7687'
        assert credentials['username'] == 'neo4j'
        assert credentials['password'] == 'password'
    
    @patch('src.config.secrets_manager.boto3')
    def test_missing_required_keys_raises_error(self, mock_boto3, clear_cache):
        """Test error raised when secret missing required keys."""
        # Mock incomplete secret
        incomplete_secret = {'uri': 'bolt://localhost:7687'}
        
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(incomplete_secret)
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            get_neo4j_credentials_from_secrets(
                environment='production',
                enable_fallback=False
            )
        
        assert 'missing required keys' in str(exc_info.value).lower()


class TestGlobalClientSingleton:
    """Test global client singleton pattern."""
    
    @patch('src.config.secrets_manager.boto3')
    def test_singleton_client(self, mock_boto3):
        """Test global client is reused."""
        # Reset before test
        reset_secrets_client()
        
        client1 = get_secrets_client()
        client2 = get_secrets_client()
        
        # Should be the same instance
        assert client1 is client2
    
    @patch('src.config.secrets_manager.boto3')
    def test_reset_singleton(self, mock_boto3):
        """Test resetting global client."""
        # Get a client
        client1 = get_secrets_client()
        
        # Reset
        reset_secrets_client()
        
        # Get new client
        client2 = get_secrets_client()
        
        # Should be different instances
        assert client1 is not client2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

