"""
Unit Tests for Neo4j Configuration Module

Tests configuration loading, validation, and secure credential handling.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pydantic import SecretStr, ValidationError

# Add parent directory to path (same pattern as test_agents_basic.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.neo4j_config import (
    Neo4jConnectionConfig,
    Neo4jSettings,
    get_neo4j_config,
    validate_required_env_vars,
    create_custom_config,
    is_gateway_mode_enabled,
    get_gateway_url,
    get_config_instance,
    reset_config_instance,
    load_dotenv_if_exists,
    ENVIRONMENT_PRESETS
)
from src.utils.errors import ConfigurationError


class TestNeo4jConnectionConfig:
    """Test Neo4jConnectionConfig model validation and methods."""
    
    def test_valid_configuration(self):
        """Test creating a valid configuration."""
        config = Neo4jConnectionConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password=SecretStr("password123"),
            database="neo4j"
        )
        
        assert config.uri == "bolt://localhost:7687"
        assert config.username == "neo4j"
        assert config.password.get_secret_value() == "password123"
        assert config.database == "neo4j"
        assert config.max_connection_pool_size == 50  # default
        assert config.enable_ssl is True  # default
    
    def test_invalid_uri_scheme(self):
        """Test that invalid URI schemes are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Neo4jConnectionConfig(
                uri="http://localhost:7687",
                username="neo4j",
                password=SecretStr("password123")
            )
        
        assert "Neo4j URI must start with" in str(exc_info.value)
    
    def test_valid_uri_schemes(self):
        """Test all valid URI schemes."""
        valid_schemes = [
            "bolt://localhost:7687",
            "bolt+s://localhost:7687",
            "bolt+ssc://localhost:7687",
            "neo4j://localhost:7687",
            "neo4j+s://localhost:7687",
            "neo4j+ssc://localhost:7687"
        ]
        
        for uri in valid_schemes:
            config = Neo4jConnectionConfig(
                uri=uri,
                username="neo4j",
                password=SecretStr("password123")
            )
            assert config.uri == uri
    
    def test_invalid_trust_strategy(self):
        """Test that invalid trust strategies are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Neo4jConnectionConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password=SecretStr("password123"),
                trust_strategy="INVALID_STRATEGY"
            )
        
        assert "Trust strategy must be one of" in str(exc_info.value)
    
    def test_pool_size_validation(self):
        """Test connection pool size validation."""
        # Too small
        with pytest.raises(ValidationError):
            Neo4jConnectionConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password=SecretStr("password123"),
                max_connection_pool_size=0
            )
        
        # Too large
        with pytest.raises(ValidationError):
            Neo4jConnectionConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password=SecretStr("password123"),
                max_connection_pool_size=1001
            )
        
        # Valid
        config = Neo4jConnectionConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password=SecretStr("password123"),
            max_connection_pool_size=100
        )
        assert config.max_connection_pool_size == 100
    
    def test_timeout_validation(self):
        """Test timeout parameter validation."""
        # Too small
        with pytest.raises(ValidationError):
            Neo4jConnectionConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password=SecretStr("password123"),
                connection_timeout=0
            )
        
        # Too large
        with pytest.raises(ValidationError):
            Neo4jConnectionConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password=SecretStr("password123"),
                connection_timeout=301
            )
        
        # Valid
        config = Neo4jConnectionConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password=SecretStr("password123"),
            connection_timeout=60
        )
        assert config.connection_timeout == 60
    
    def test_get_driver_config(self):
        """Test driver configuration generation."""
        config = Neo4jConnectionConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password=SecretStr("password123"),
            max_connection_pool_size=75,
            connection_timeout=45
        )
        
        driver_config = config.get_driver_config()
        
        assert driver_config["max_connection_pool_size"] == 75
        assert driver_config["connection_timeout"] == 45
        assert "max_transaction_retry_time" in driver_config
        assert "encrypted" in driver_config
    
    def test_get_driver_config_no_duplicate_encryption(self):
        """Test that encryption is not duplicated in URI."""
        config = Neo4jConnectionConfig(
            uri="neo4j+s://localhost:7687",
            username="neo4j",
            password=SecretStr("password123"),
            encrypted=True
        )
        
        driver_config = config.get_driver_config()
        
        # Should not add encrypted=True since URI already has +s
        assert "encrypted" not in driver_config
    
    def test_get_connection_string_safe(self):
        """Test safe connection string doesn't expose password."""
        config = Neo4jConnectionConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password=SecretStr("super-secret-password"),
            database="testdb"
        )
        
        safe_string = config.get_connection_string_safe()
        
        assert "bolt://localhost:7687" in safe_string
        assert "neo4j" in safe_string
        assert "testdb" in safe_string
        assert "super-secret-password" not in safe_string
        assert "password" not in safe_string.lower() or "***" in safe_string
    
    def test_password_redaction_in_json(self):
        """Test password is redacted in JSON output."""
        config = Neo4jConnectionConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password=SecretStr("super-secret-password")
        )
        
        json_output = config.json()
        
        assert "super-secret-password" not in json_output
        assert "REDACTED" in json_output


class TestNeo4jSettings:
    """Test Neo4jSettings environment variable loading."""
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://testhost:7687",
        "NEO4J_USERNAME": "testuser",
        "NEO4J_PASSWORD": "testpass",
        "NEO4J_DATABASE": "testdb"
    }, clear=True)
    def test_load_from_environment(self):
        """Test loading settings from environment variables."""
        settings = Neo4jSettings()
        
        assert settings.neo4j_uri == "bolt://testhost:7687"
        assert settings.neo4j_username == "testuser"
        assert settings.neo4j_password.get_secret_value() == "testpass"
        assert settings.neo4j_database == "testdb"
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://testhost:7687",
        "NEO4J_USERNAME": "testuser",
        "NEO4J_PASSWORD": "testpass"
    }, clear=True)
    def test_default_values(self):
        """Test default values are applied when not in environment."""
        settings = Neo4jSettings()
        
        assert settings.neo4j_database == "neo4j"  # default
        assert settings.neo4j_max_pool_size == 50  # default
        assert settings.neo4j_enable_ssl is True  # default
        assert settings.use_gateway is False  # default
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://testhost:7687",
        "NEO4J_USERNAME": "testuser",
        "NEO4J_PASSWORD": "testpass",
        "NEO4J_MAX_POOL_SIZE": "100",
        "NEO4J_ENABLE_SSL": "false",
        "NEO4J_USE_GATEWAY": "true",
        "NEO4J_GATEWAY_URL": "https://gateway.example.com"
    }, clear=True)
    def test_optional_environment_variables(self):
        """Test loading optional environment variables."""
        settings = Neo4jSettings()
        
        assert settings.neo4j_max_pool_size == 100
        assert settings.neo4j_enable_ssl is False
        assert settings.use_gateway is True
        assert settings.gateway_url == "https://gateway.example.com"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_required_variables(self):
        """Test that missing required variables raise error."""
        with pytest.raises(ValidationError) as exc_info:
            Neo4jSettings()
        
        error_str = str(exc_info.value)
        assert "neo4j_uri" in error_str or "NEO4J_URI" in error_str


class TestGetNeo4jConfig:
    """Test get_neo4j_config function."""
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://testhost:7687",
        "NEO4J_USERNAME": "testuser",
        "NEO4J_PASSWORD": "testpass",
        "NEO4J_DATABASE": "testdb"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_get_config_success(self, mock_load_dotenv):
        """Test successful configuration loading."""
        mock_load_dotenv.return_value = False
        
        config = get_neo4j_config()
        
        assert isinstance(config, Neo4jConnectionConfig)
        assert config.uri == "bolt://testhost:7687"
        assert config.username == "testuser"
        assert config.database == "testdb"
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://testhost:7687",
        "NEO4J_USERNAME": "testuser",
        "NEO4J_PASSWORD": "testpass",
        "ENVIRONMENT": "production"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_environment_presets_applied(self, mock_load_dotenv):
        """Test that environment-specific presets are applied."""
        mock_load_dotenv.return_value = False
        
        config = get_neo4j_config(environment="production")
        
        # Production preset values
        assert config.max_connection_pool_size == 50
        assert config.connection_timeout == 30
        assert config.enable_query_logging is False
        assert config.enable_metrics is True
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://testhost:7687",
        "NEO4J_USERNAME": "testuser",
        "NEO4J_PASSWORD": "testpass"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_development_environment_presets(self, mock_load_dotenv):
        """Test development environment presets."""
        mock_load_dotenv.return_value = False
        
        config = get_neo4j_config(environment="development")
        
        # Development preset values
        assert config.max_connection_pool_size == 10
        assert config.connection_timeout == 15
        assert config.enable_query_logging is True
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_missing_env_vars_raises_error(self, mock_load_dotenv):
        """Test that missing environment variables raise ConfigurationError."""
        mock_load_dotenv.return_value = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            get_neo4j_config()
        
        assert "Failed to load Neo4j configuration" in str(exc_info.value)
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://testhost:7687",
        "NEO4J_USERNAME": "testuser",
        "NEO4J_PASSWORD": "testpass"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_use_dotenv_parameter(self, mock_load_dotenv):
        """Test use_dotenv parameter controls .env loading."""
        mock_load_dotenv.return_value = False
        
        # With use_dotenv=True (default)
        get_neo4j_config(use_dotenv=True)
        assert mock_load_dotenv.called
        
        mock_load_dotenv.reset_mock()
        
        # With use_dotenv=False
        get_neo4j_config(use_dotenv=False)
        assert not mock_load_dotenv.called


class TestValidateRequiredEnvVars:
    """Test validate_required_env_vars function."""
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
    }, clear=True)
    def test_all_required_vars_present(self):
        """Test validation when all required variables are present."""
        validation = validate_required_env_vars()
        
        assert validation["NEO4J_URI"] is True
        assert validation["NEO4J_USERNAME"] is True
        assert validation["NEO4J_PASSWORD"] is True
        assert all(validation.values())
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j"
    }, clear=True)
    def test_missing_password(self):
        """Test validation when password is missing."""
        validation = validate_required_env_vars()
        
        assert validation["NEO4J_URI"] is True
        assert validation["NEO4J_USERNAME"] is True
        assert validation["NEO4J_PASSWORD"] is False
        assert not all(validation.values())
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
    }, clear=True)
    def test_empty_string_treated_as_missing(self):
        """Test that empty strings are treated as missing."""
        validation = validate_required_env_vars()
        
        assert validation["NEO4J_URI"] is False
    
    @patch.dict(os.environ, {}, clear=True)
    def test_all_vars_missing(self):
        """Test validation when all variables are missing."""
        validation = validate_required_env_vars()
        
        assert all(not v for v in validation.values())


class TestCreateCustomConfig:
    """Test create_custom_config function."""
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_create_with_overrides(self, mock_load_dotenv):
        """Test creating custom config with overrides."""
        mock_load_dotenv.return_value = False
        
        overrides = {
            "max_connection_pool_size": 100,
            "enable_query_logging": True,
            "connection_timeout": 60
        }
        
        config = create_custom_config(overrides)
        
        assert config.max_connection_pool_size == 100
        assert config.enable_query_logging is True
        assert config.connection_timeout == 60
        # Base config values should still be present
        assert config.uri == "bolt://localhost:7687"
        assert config.username == "neo4j"
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_password_override_ignored(self, mock_load_dotenv):
        """Test that password overrides are ignored for security."""
        mock_load_dotenv.return_value = False
        
        base_config = get_neo4j_config()
        original_password = base_config.password.get_secret_value()
        
        overrides = {
            "password": SecretStr("should-be-ignored"),
            "max_connection_pool_size": 100
        }
        
        config = create_custom_config(overrides)
        
        # Password should remain unchanged
        assert config.password.get_secret_value() == original_password
        # Other override should work
        assert config.max_connection_pool_size == 100


class TestGatewayMode:
    """Test Gateway mode functions."""
    
    @patch.dict(os.environ, {
        "NEO4J_USE_GATEWAY": "true",
        "NEO4J_GATEWAY_URL": "https://gateway.example.com"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_gateway_mode_enabled(self, mock_load_dotenv):
        """Test Gateway mode detection when enabled."""
        mock_load_dotenv.return_value = False
        
        assert is_gateway_mode_enabled() is True
        assert get_gateway_url() == "https://gateway.example.com"
    
    @patch.dict(os.environ, {
        "NEO4J_USE_GATEWAY": "false"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_gateway_mode_disabled(self, mock_load_dotenv):
        """Test Gateway mode detection when disabled."""
        mock_load_dotenv.return_value = False
        
        assert is_gateway_mode_enabled() is False
        assert get_gateway_url() is None
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_gateway_mode_default(self, mock_load_dotenv):
        """Test Gateway mode defaults to False."""
        mock_load_dotenv.return_value = False
        
        assert is_gateway_mode_enabled() is False
    
    @patch.dict(os.environ, {
        "NEO4J_USE_GATEWAY": "true"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_gateway_url_missing_warning(self, mock_load_dotenv):
        """Test warning when Gateway mode enabled but URL missing."""
        mock_load_dotenv.return_value = False
        
        assert is_gateway_mode_enabled() is True
        url = get_gateway_url()
        assert url is None


class TestConfigInstance:
    """Test singleton configuration instance functions."""
    
    def setup_method(self):
        """Reset config instance before each test."""
        reset_config_instance()
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_singleton_instance(self, mock_load_dotenv):
        """Test singleton instance caching."""
        mock_load_dotenv.return_value = False
        
        # First call should create instance
        config1 = get_config_instance()
        # Second call should return same instance
        config2 = get_config_instance()
        
        assert config1 is config2
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_reset_instance(self, mock_load_dotenv):
        """Test resetting singleton instance."""
        mock_load_dotenv.return_value = False
        
        config1 = get_config_instance()
        reset_config_instance()
        config2 = get_config_instance()
        
        # Should be different instances after reset
        assert config1 is not config2
        # But should have same values
        assert config1.uri == config2.uri


class TestEnvironmentPresets:
    """Test environment-specific presets."""
    
    def test_presets_structure(self):
        """Test that environment presets have expected structure."""
        assert "development" in ENVIRONMENT_PRESETS
        assert "test" in ENVIRONMENT_PRESETS
        assert "production" in ENVIRONMENT_PRESETS
        
        for env, preset in ENVIRONMENT_PRESETS.items():
            assert "max_connection_pool_size" in preset
            assert "connection_timeout" in preset
            assert "enable_query_logging" in preset
            assert "enable_metrics" in preset
    
    def test_preset_values(self):
        """Test specific preset values."""
        dev_preset = ENVIRONMENT_PRESETS["development"]
        prod_preset = ENVIRONMENT_PRESETS["production"]
        
        # Development should have smaller pool and shorter timeout
        assert dev_preset["max_connection_pool_size"] < prod_preset["max_connection_pool_size"]
        
        # Development should have query logging enabled
        assert dev_preset["enable_query_logging"] is True
        # Production should have it disabled
        assert prod_preset["enable_query_logging"] is False


class TestSecurityFeatures:
    """Test security features and credential handling."""
    
    @patch.dict(os.environ, {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "super-secret-password"
    }, clear=True)
    @patch('src.config.neo4j_config.load_dotenv_if_exists')
    def test_password_not_in_logs(self, mock_load_dotenv):
        """Test that password doesn't appear in log output."""
        mock_load_dotenv.return_value = False
        
        config = get_neo4j_config()
        
        # Get safe connection string
        safe_string = config.get_connection_string_safe()
        
        # Password should not be in safe string
        assert "super-secret-password" not in safe_string
    
    def test_secret_str_protection(self):
        """Test SecretStr protects password in various scenarios."""
        config = Neo4jConnectionConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password=SecretStr("my-secret")
        )
        
        # String representation should not contain password
        assert "my-secret" not in str(config)
        assert "my-secret" not in repr(config)
        
        # Dict export should redact password
        config_dict = config.dict()
        assert isinstance(config_dict["password"], SecretStr)
        
        # JSON export should redact password
        json_str = config.json()
        assert "my-secret" not in json_str

