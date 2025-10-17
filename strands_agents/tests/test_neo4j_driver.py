"""
Tests for Neo4j Driver Factory

This module tests the neo4j_driver module functionality including:
- Driver factory initialization and singleton pattern
- Connection management and pooling
- Retry logic with exponential backoff
- Connection validation and health checks
- Resource cleanup and context managers
- Metrics collection
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import Any

# Import the module to test
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.config.neo4j_driver import (
    Neo4jDriverFactory,
    ConnectionMode,
    ConnectionState,
    get_driver,
    create_session,
    validate_connection,
    close_driver,
    get_connection_metrics
)
from src.config.neo4j_config import Neo4jConnectionConfig
from src.utils.errors import ConnectionError as CustomConnectionError, ConfigurationError


# Mock Neo4j driver and related classes
@pytest.fixture
def mock_neo4j_driver():
    """Mock neo4j GraphDatabase and Driver."""
    with patch('src.config.neo4j_driver.GraphDatabase') as mock_gd, \
         patch('src.config.neo4j_driver.NEO4J_AVAILABLE', True):
        
        # Create mock driver
        mock_driver = MagicMock()
        mock_driver.verify_connectivity = MagicMock()
        mock_driver.close = MagicMock()
        
        # Create mock session
        mock_session = MagicMock()
        mock_result = MagicMock()
        # Configure mock to return actual values when accessed like a dict
        mock_single = MagicMock()
        mock_single.__getitem__ = lambda self, key: 1 if key == "num" else 42
        mock_result.single.return_value = mock_single
        mock_session.run.return_value = mock_result
        mock_session.close = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver.session.return_value.__exit__.return_value = None
        
        # Configure GraphDatabase.driver to return our mock
        mock_gd.driver.return_value = mock_driver
        
        yield {
            "graphdb": mock_gd,
            "driver": mock_driver,
            "session": mock_session
        }


@pytest.fixture
def sample_config():
    """Sample Neo4j configuration for testing."""
    return Neo4jConnectionConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="test-password",
        database="neo4j",
        max_connection_pool_size=10,
        connection_timeout=30
    )


@pytest.fixture
def reset_factory():
    """Reset factory singleton before and after tests."""
    Neo4jDriverFactory.reset_instance()
    yield
    Neo4jDriverFactory.reset_instance()


class TestNeo4jDriverFactoryInitialization:
    """Test driver factory initialization."""
    
    def test_factory_requires_neo4j_package(self, reset_factory):
        """Test that factory requires neo4j package."""
        with patch('src.config.neo4j_driver.NEO4J_AVAILABLE', False):
            with pytest.raises(ConfigurationError) as exc_info:
                Neo4jDriverFactory()
            assert "neo4j driver package is required" in str(exc_info.value)
    
    def test_factory_initialization_with_config(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test factory initializes with provided config."""
        factory = Neo4jDriverFactory(config=sample_config)
        
        assert factory._config == sample_config
        assert factory._connection_mode == ConnectionMode.DIRECT
        assert factory._connection_state == ConnectionState.DISCONNECTED
        assert factory._driver is None
    
    def test_factory_initialization_default_config(self, mock_neo4j_driver, reset_factory):
        """Test factory initializes with default config."""
        with patch('src.config.neo4j_driver.get_neo4j_config') as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            
            factory = Neo4jDriverFactory()
            
            assert factory._config == mock_config
            mock_get_config.assert_called_once()
    
    def test_factory_initialization_gateway_mode(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test factory initialization in gateway mode."""
        factory = Neo4jDriverFactory(
            config=sample_config,
            connection_mode=ConnectionMode.GATEWAY
        )
        
        assert factory._connection_mode == ConnectionMode.GATEWAY


class TestSingletonPattern:
    """Test singleton pattern implementation."""
    
    def test_get_instance_creates_singleton(self, mock_neo4j_driver, reset_factory):
        """Test get_instance creates and returns singleton."""
        factory1 = Neo4jDriverFactory.get_instance()
        factory2 = Neo4jDriverFactory.get_instance()
        
        assert factory1 is factory2
    
    def test_get_instance_with_config(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test get_instance with custom config."""
        factory = Neo4jDriverFactory.get_instance(config=sample_config)
        
        assert factory._config == sample_config
    
    def test_force_new_instance(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test forcing creation of new instance."""
        factory1 = Neo4jDriverFactory.get_instance()
        factory2 = Neo4jDriverFactory.get_instance(force_new=True)
        
        assert factory1 is not factory2
    
    def test_reset_instance(self, mock_neo4j_driver, reset_factory):
        """Test resetting singleton instance."""
        factory1 = Neo4jDriverFactory.get_instance()
        Neo4jDriverFactory.reset_instance()
        factory2 = Neo4jDriverFactory.get_instance()
        
        assert factory1 is not factory2


class TestDriverCreation:
    """Test Neo4j driver creation and management."""
    
    def test_get_driver_creates_connection(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test get_driver creates connection."""
        factory = Neo4jDriverFactory(config=sample_config)
        driver = factory.get_driver()
        
        assert driver is not None
        assert factory._connection_state == ConnectionState.CONNECTED
        mock_neo4j_driver["graphdb"].driver.assert_called_once()
    
    def test_get_driver_reuses_existing_connection(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test get_driver reuses existing connection."""
        factory = Neo4jDriverFactory(config=sample_config)
        
        driver1 = factory.get_driver()
        driver2 = factory.get_driver()
        
        assert driver1 is driver2
        # Should only call GraphDatabase.driver once
        assert mock_neo4j_driver["graphdb"].driver.call_count == 1
    
    def test_get_driver_reconnects_on_health_check_failure(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test get_driver reconnects if health check fails."""
        factory = Neo4jDriverFactory(config=sample_config)
        
        # First call succeeds
        driver1 = factory.get_driver()
        
        # Make verify_connectivity fail for existing driver
        mock_neo4j_driver["driver"].verify_connectivity.side_effect = Exception("Connection lost")
        
        # Create new mock driver for reconnection
        new_mock_driver = MagicMock()
        new_mock_driver.verify_connectivity = MagicMock()
        mock_neo4j_driver["graphdb"].driver.return_value = new_mock_driver
        
        # Second call should reconnect
        driver2 = factory.get_driver()
        
        assert driver2 is new_mock_driver
        assert mock_neo4j_driver["graphdb"].driver.call_count == 2
    
    def test_get_driver_with_database_override(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test get_driver with database override."""
        factory = Neo4jDriverFactory(config=sample_config)
        driver = factory.get_driver(database="custom_db")
        
        assert driver is not None


class TestConnectionRetry:
    """Test connection retry logic with exponential backoff."""
    
    def test_retry_on_service_unavailable(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test retry logic when service is unavailable."""
        from neo4j.exceptions import ServiceUnavailable
        
        factory = Neo4jDriverFactory(config=sample_config)
        
        # Fail first 2 attempts, succeed on third
        mock_neo4j_driver["driver"].verify_connectivity.side_effect = [
            ServiceUnavailable("Connection failed"),
            ServiceUnavailable("Connection failed"),
            None  # Success on attempt 3 (index 2), so reconnections = 2
        ]
        
        driver = factory.get_driver()
        
        assert driver is not None
        assert factory._connection_state == ConnectionState.CONNECTED
        # Reconnections is tracked as attempt - 1 when attempt > 0 succeeds
        # Attempt 3 (index 2) succeeds, so reconnections = 2
        assert factory._metrics["reconnections"] >= 1
    
    def test_retry_exhausted_raises_error(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test that exhausted retries raise error."""
        from neo4j.exceptions import ServiceUnavailable
        
        factory = Neo4jDriverFactory(config=sample_config)
        
        # Always fail
        mock_neo4j_driver["driver"].verify_connectivity.side_effect = ServiceUnavailable("Connection failed")
        
        with pytest.raises(CustomConnectionError) as exc_info:
            factory.get_driver()
        
        assert "Failed to connect" in str(exc_info.value)
        assert factory._connection_state == ConnectionState.ERROR
        assert factory._metrics["failed_connections"] >= 3
    
    def test_retry_with_exponential_backoff(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test exponential backoff timing."""
        from neo4j.exceptions import ServiceUnavailable
        
        factory = Neo4jDriverFactory(config=sample_config)
        
        # Mock time.sleep to track backoff
        with patch('src.config.neo4j_driver.time.sleep') as mock_sleep:
            mock_neo4j_driver["driver"].verify_connectivity.side_effect = [
                ServiceUnavailable("Fail"),
                ServiceUnavailable("Fail"),
                None  # Success
            ]
            
            factory.get_driver()
            
            # Check that backoff increases
            calls = mock_sleep.call_args_list
            assert len(calls) == 2
            # First backoff: 1.0 * 2^0 = 1.0
            assert calls[0][0][0] == 1.0
            # Second backoff: 1.0 * 2^1 = 2.0
            assert calls[1][0][0] == 2.0


class TestConnectionValidation:
    """Test connection validation and health checks."""
    
    def test_validate_connection_success(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test successful connection validation."""
        factory = Neo4jDriverFactory(config=sample_config)
        
        result = factory.validate_connection()
        
        assert result is True
        mock_neo4j_driver["session"].run.assert_called_once_with("RETURN 1 as num")
    
    def test_validate_connection_failure(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test connection validation failure."""
        factory = Neo4jDriverFactory(config=sample_config)
        
        # Make query fail
        mock_neo4j_driver["session"].run.side_effect = Exception("Query failed")
        
        with pytest.raises(CustomConnectionError) as exc_info:
            factory.validate_connection()
        
        assert "validation failed" in str(exc_info.value).lower()
        assert factory._connection_state == ConnectionState.ERROR


class TestResourceManagement:
    """Test resource cleanup and context managers."""
    
    def test_close_releases_resources(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test close properly releases resources."""
        factory = Neo4jDriverFactory(config=sample_config)
        driver = factory.get_driver()
        
        factory.close()
        
        assert factory._driver is None
        assert factory._connection_state == ConnectionState.DISCONNECTED
        mock_neo4j_driver["driver"].close.assert_called_once()
    
    def test_context_manager_cleanup(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test context manager properly cleans up."""
        with Neo4jDriverFactory(config=sample_config) as factory:
            driver = factory.get_driver()
            assert driver is not None
        
        # After context exit, driver should be closed
        assert factory._driver is None
    
    def test_session_context_manager(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test session context manager."""
        factory = Neo4jDriverFactory(config=sample_config)
        
        with factory.session() as session:
            result = session.run("RETURN 1 as num")
            # Just verify we can call these methods
            result.single()
            assert session is not None


class TestMetricsCollection:
    """Test connection metrics and monitoring."""
    
    def test_metrics_track_connections(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test metrics track connection attempts."""
        factory = Neo4jDriverFactory(config=sample_config)
        
        factory.get_driver()
        
        metrics = factory.get_metrics()
        assert metrics["total_connections"] == 1
        assert metrics["failed_connections"] == 0
        assert metrics["connection_state"] == ConnectionState.CONNECTED.value
        assert metrics["connection_mode"] == ConnectionMode.DIRECT.value
    
    def test_metrics_track_failures(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test metrics track failed connections."""
        from neo4j.exceptions import ServiceUnavailable
        
        factory = Neo4jDriverFactory(config=sample_config)
        
        mock_neo4j_driver["driver"].verify_connectivity.side_effect = ServiceUnavailable("Fail")
        
        with pytest.raises(CustomConnectionError):
            factory.get_driver()
        
        metrics = factory.get_metrics()
        assert metrics["failed_connections"] >= 3
        assert metrics["last_error"] is not None
    
    def test_metrics_track_reconnections(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test metrics track reconnections."""
        from neo4j.exceptions import ServiceUnavailable
        
        factory = Neo4jDriverFactory(config=sample_config)
        
        # Fail first attempt, succeed on second
        mock_neo4j_driver["driver"].verify_connectivity.side_effect = [
            ServiceUnavailable("Fail"),
            None  # Success
        ]
        
        factory.get_driver()
        
        metrics = factory.get_metrics()
        assert metrics["reconnections"] == 1


class TestGatewayMode:
    """Test gateway mode (placeholder tests)."""
    
    def test_gateway_mode_not_implemented(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test gateway mode raises NotImplementedError."""
        factory = Neo4jDriverFactory(
            config=sample_config,
            connection_mode=ConnectionMode.GATEWAY
        )
        
        with pytest.raises(NotImplementedError) as exc_info:
            factory.get_driver()
        
        assert "Gateway mode is not yet implemented" in str(exc_info.value)


class TestConvenienceFunctions:
    """Test module-level convenience functions."""
    
    def test_get_driver_convenience_function(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test get_driver convenience function."""
        driver = get_driver(config=sample_config)
        
        assert driver is not None
    
    def test_create_session_convenience_function(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test create_session convenience function."""
        with create_session(config=sample_config) as session:
            result = session.run("RETURN 1 as num")
            # Just verify we can call these methods
            result.single()
    
    def test_validate_connection_convenience_function(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test validate_connection convenience function."""
        result = validate_connection(config=sample_config)
        
        assert result is True
    
    def test_close_driver_convenience_function(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test close_driver convenience function."""
        get_driver(config=sample_config)
        close_driver()
        
        factory = Neo4jDriverFactory.get_instance()
        assert factory._driver is None
    
    def test_get_connection_metrics_convenience_function(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test get_connection_metrics convenience function."""
        get_driver(config=sample_config)
        metrics = get_connection_metrics()
        
        assert "total_connections" in metrics
        assert metrics["total_connections"] == 1


class TestThreadSafety:
    """Test thread safety of driver factory."""
    
    def test_concurrent_get_instance(self, mock_neo4j_driver, reset_factory):
        """Test concurrent get_instance calls return same instance."""
        import threading
        
        instances = []
        
        def get_factory():
            factory = Neo4jDriverFactory.get_instance()
            instances.append(factory)
        
        threads = [threading.Thread(target=get_factory) for _ in range(10)]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All instances should be the same
        assert all(instance is instances[0] for instance in instances)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_auth_error_handling(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test handling of authentication errors."""
        from neo4j.exceptions import AuthError
        
        factory = Neo4jDriverFactory(config=sample_config)
        
        mock_neo4j_driver["driver"].verify_connectivity.side_effect = AuthError("Auth failed")
        
        with pytest.raises(CustomConnectionError) as exc_info:
            factory.get_driver()
        
        assert "Failed to connect" in str(exc_info.value)
    
    def test_configuration_error_handling(self, mock_neo4j_driver, sample_config, reset_factory):
        """Test handling of configuration errors."""
        from neo4j.exceptions import ConfigurationError as Neo4jConfigError
        
        factory = Neo4jDriverFactory(config=sample_config)
        
        mock_neo4j_driver["driver"].verify_connectivity.side_effect = Neo4jConfigError("Config invalid")
        
        with pytest.raises(CustomConnectionError):
            factory.get_driver()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

