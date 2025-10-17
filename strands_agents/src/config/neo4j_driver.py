"""
Neo4j Driver Factory Module for Strands Agents

This module provides a factory class for managing Neo4j driver instances with
connection pooling, validation, automatic reconnection, and resource management.

Features:
- Singleton pattern for driver reuse across application
- Connection pooling with configurable settings
- Health check validation
- Automatic retry with exponential backoff
- Support for both direct Neo4j and Gateway access modes
- Resource management with context manager support
- Connection monitoring and metrics collection
- Thread-safe operations
"""

import time
import threading
from typing import Dict, Any, Optional
from contextlib import contextmanager
from enum import Enum

try:
    from neo4j import GraphDatabase, Driver, Session
    from neo4j.exceptions import ServiceUnavailable, AuthError, ConfigurationError as Neo4jConfigError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
    Driver = None
    Session = None
    ServiceUnavailable = Exception
    AuthError = Exception
    Neo4jConfigError = Exception

try:
    from .neo4j_config import Neo4jConnectionConfig, get_neo4j_config
    from .secrets_manager import get_neo4j_credentials_from_secrets
    from ..utils.errors import ConfigurationError, ConnectionError as CustomConnectionError
    from ..utils.logging import get_logger
except ImportError:
    from neo4j_config import Neo4jConnectionConfig, get_neo4j_config
    from secrets_manager import get_neo4j_credentials_from_secrets
    from utils.errors import ConfigurationError, ConnectionError as CustomConnectionError
    from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class ConnectionMode(Enum):
    """Connection mode enumeration."""
    DIRECT = "direct"
    GATEWAY = "gateway"


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class Neo4jDriverFactory:
    """
    Factory class for managing Neo4j driver instances.
    
    This class implements a singleton pattern to ensure only one driver instance
    exists per application. It provides connection pooling, validation, automatic
    reconnection, and resource management capabilities.
    
    Example:
        >>> factory = Neo4jDriverFactory.get_instance()
        >>> driver = factory.get_driver()
        >>> with driver.session() as session:
        ...     result = session.run("RETURN 1 as num")
        ...     print(result.single()["num"])
        >>> factory.close()
    """
    
    _instance: Optional['Neo4jDriverFactory'] = None
    _lock = threading.Lock()
    
    def __init__(
        self,
        config: Optional[Neo4jConnectionConfig] = None,
        connection_mode: ConnectionMode = ConnectionMode.DIRECT
    ):
        """
        Initialize the Neo4j driver factory.
        
        Args:
            config: Neo4j connection configuration
            connection_mode: Connection mode (direct or gateway)
        
        Raises:
            ConfigurationError: If neo4j package is not available or config is invalid
        """
        if not NEO4J_AVAILABLE:
            raise ConfigurationError(
                "neo4j driver package is required. Install it with: pip install neo4j"
            )
        
        self._config = config or get_neo4j_config()
        self._connection_mode = connection_mode
        self._driver: Optional[Driver] = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._metrics: Dict[str, Any] = {
            "total_connections": 0,
            "failed_connections": 0,
            "reconnections": 0,
            "last_connection_time": None,
            "last_error": None
        }
        self._connection_lock = threading.Lock()
        
        logger.info(
            f"Initialized Neo4j driver factory in {connection_mode.value} mode",
            extra={"connection_mode": connection_mode.value}
        )
    
    @classmethod
    def get_instance(
        cls,
        config: Optional[Neo4jConnectionConfig] = None,
        connection_mode: ConnectionMode = ConnectionMode.DIRECT,
        force_new: bool = False
    ) -> 'Neo4jDriverFactory':
        """
        Get or create the Neo4jDriverFactory singleton instance.
        
        Args:
            config: Neo4j connection configuration (optional)
            connection_mode: Connection mode (direct or gateway)
            force_new: Force creation of new instance (useful for testing)
        
        Returns:
            Neo4jDriverFactory instance
        
        Example:
            >>> factory = Neo4jDriverFactory.get_instance()
            >>> # Or with custom config
            >>> factory = Neo4jDriverFactory.get_instance(
            ...     config=my_config,
            ...     connection_mode=ConnectionMode.GATEWAY
            ... )
        """
        with cls._lock:
            if cls._instance is None or force_new:
                if force_new and cls._instance is not None:
                    cls._instance.close()
                cls._instance = cls(config=config, connection_mode=connection_mode)
                logger.info("Created new Neo4jDriverFactory singleton instance")
            return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance (useful for testing).
        
        This will close the existing driver and clear the instance.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None
                logger.info("Reset Neo4jDriverFactory singleton instance")
    
    def get_driver(self, database: Optional[str] = None) -> Driver:
        """
        Get a configured Neo4j driver instance.
        
        Creates a new driver if one doesn't exist, or returns the existing driver.
        Implements connection pooling and automatic reconnection.
        
        Args:
            database: Optional database name override
        
        Returns:
            neo4j.Driver instance
        
        Raises:
            CustomConnectionError: If connection cannot be established
        
        Example:
            >>> factory = Neo4jDriverFactory.get_instance()
            >>> driver = factory.get_driver()
            >>> with driver.session(database="neo4j") as session:
            ...     result = session.run("RETURN 1")
        """
        with self._connection_lock:
            # Return existing driver if available and connected
            if self._driver is not None and self._connection_state == ConnectionState.CONNECTED:
                try:
                    # Quick health check
                    self._driver.verify_connectivity()
                    return self._driver
                except Exception as e:
                    logger.warning(f"Existing driver failed health check: {str(e)}")
                    self._connection_state = ConnectionState.ERROR
                    self._driver = None
            
            # Create new driver with retry logic
            self._driver = self._connect_with_retry()
            return self._driver
    
    def _connect_with_retry(
        self,
        max_retries: int = 3,
        initial_backoff: float = 1.0
    ) -> Driver:
        """
        Attempt to connect with exponential backoff retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
        
        Returns:
            neo4j.Driver instance
        
        Raises:
            CustomConnectionError: If all retries fail
        """
        self._connection_state = ConnectionState.CONNECTING
        backoff = initial_backoff
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Attempting Neo4j connection (attempt {attempt + 1}/{max_retries})",
                    extra={"attempt": attempt + 1, "max_retries": max_retries}
                )
                
                # Create driver based on connection mode
                if self._connection_mode == ConnectionMode.DIRECT:
                    driver = self._create_direct_driver()
                else:
                    driver = self._create_gateway_driver()
                
                # Verify connectivity
                driver.verify_connectivity()
                
                # Update state and metrics
                self._connection_state = ConnectionState.CONNECTED
                self._metrics["total_connections"] += 1
                self._metrics["last_connection_time"] = time.time()
                
                if attempt > 0:
                    self._metrics["reconnections"] += 1
                
                logger.info(
                    "Successfully connected to Neo4j",
                    extra={
                        "connection_mode": self._connection_mode.value,
                        "uri": self._config.uri,
                        "database": self._config.database
                    }
                )
                
                return driver
                
            except (ServiceUnavailable, AuthError, Neo4jConfigError) as e:
                last_exception = e
                self._metrics["failed_connections"] += 1
                self._metrics["last_error"] = str(e)
                
                logger.warning(
                    f"Connection attempt {attempt + 1} failed: {str(e)}",
                    extra={
                        "attempt": attempt + 1,
                        "error_type": type(e).__name__,
                        "will_retry": attempt < max_retries - 1
                    }
                )
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
        
        # All retries failed
        self._connection_state = ConnectionState.ERROR
        error_msg = f"Failed to connect to Neo4j after {max_retries} attempts"
        
        if last_exception:
            error_msg += f": {str(last_exception)}"
        
        logger.error(error_msg)
        raise CustomConnectionError(error_msg) from last_exception
    
    def _create_direct_driver(self) -> Driver:
        """
        Create a Neo4j driver for direct database access.
        
        Returns:
            neo4j.Driver instance
        """
        # Get driver configuration
        driver_config = self._config.get_driver_config()
        
        # Create driver
        driver = GraphDatabase.driver(
            self._config.uri,
            auth=(
                self._config.username,
                self._config.password.get_secret_value()
            ),
            **driver_config
        )
        
        logger.debug(
            "Created direct Neo4j driver",
            extra={
                "uri": self._config.uri,
                "pool_size": driver_config.get("max_connection_pool_size")
            }
        )
        
        return driver
    
    def _create_gateway_driver(self) -> Driver:
        """
        Create a Neo4j driver for Gateway access.
        
        This is a placeholder for future Gateway implementation.
        
        Returns:
            neo4j.Driver instance
        
        Raises:
            NotImplementedError: Gateway mode not yet implemented
        """
        raise NotImplementedError(
            "Gateway mode is not yet implemented. "
            "Use ConnectionMode.DIRECT for now."
        )
    
    def validate_connection(self, timeout: int = 5) -> bool:
        """
        Validate the Neo4j connection with a health check.
        
        Args:
            timeout: Timeout in seconds for the health check
        
        Returns:
            bool: True if connection is valid
        
        Raises:
            CustomConnectionError: If validation fails
        
        Example:
            >>> factory = Neo4jDriverFactory.get_instance()
            >>> if factory.validate_connection():
            ...     print("Connection is healthy")
        """
        try:
            driver = self.get_driver()
            
            # Perform a simple query to validate
            with driver.session(database=self._config.database) as session:
                result = session.run("RETURN 1 as num")
                value = result.single()["num"]
                
                if value != 1:
                    raise CustomConnectionError("Health check query returned unexpected value")
            
            logger.info("Neo4j connection validation successful")
            return True
            
        except Exception as e:
            self._connection_state = ConnectionState.ERROR
            error_msg = f"Connection validation failed: {str(e)}"
            logger.error(error_msg)
            raise CustomConnectionError(error_msg) from e
    
    def close(self) -> None:
        """
        Close the driver and release all resources.
        
        This should be called when the application is shutting down to ensure
        proper cleanup of connection pools and resources.
        
        Example:
            >>> factory = Neo4jDriverFactory.get_instance()
            >>> # ... use driver ...
            >>> factory.close()
        """
        with self._connection_lock:
            if self._driver is not None:
                try:
                    self._driver.close()
                    logger.info("Closed Neo4j driver and released resources")
                except Exception as e:
                    logger.error(f"Error closing Neo4j driver: {str(e)}")
                finally:
                    self._driver = None
                    self._connection_state = ConnectionState.DISCONNECTED
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get connection metrics and statistics.
        
        Returns:
            dict: Connection metrics including:
                - total_connections: Total number of successful connections
                - failed_connections: Total number of failed connection attempts
                - reconnections: Number of reconnections after initial connection
                - last_connection_time: Timestamp of last successful connection
                - last_error: Last error message (if any)
                - connection_state: Current connection state
                - connection_mode: Current connection mode
        
        Example:
            >>> factory = Neo4jDriverFactory.get_instance()
            >>> metrics = factory.get_metrics()
            >>> print(f"Total connections: {metrics['total_connections']}")
        """
        metrics = self._metrics.copy()
        metrics["connection_state"] = self._connection_state.value
        metrics["connection_mode"] = self._connection_mode.value
        metrics["uri"] = self._config.uri
        metrics["database"] = self._config.database
        return metrics
    
    def get_connection_state(self) -> ConnectionState:
        """
        Get the current connection state.
        
        Returns:
            ConnectionState: Current connection state
        """
        return self._connection_state
    
    @contextmanager
    def session(self, database: Optional[str] = None, **kwargs) -> Session:
        """
        Context manager for Neo4j sessions.
        
        Provides a convenient way to work with sessions using context managers.
        Automatically closes the session when done.
        
        Args:
            database: Optional database name override
            **kwargs: Additional session configuration
        
        Yields:
            neo4j.Session instance
        
        Example:
            >>> factory = Neo4jDriverFactory.get_instance()
            >>> with factory.session() as session:
            ...     result = session.run("MATCH (n) RETURN count(n) as count")
            ...     print(result.single()["count"])
        """
        driver = self.get_driver()
        db = database or self._config.database
        
        session = driver.session(database=db, **kwargs)
        try:
            yield session
        finally:
            session.close()
    
    def __enter__(self) -> 'Neo4jDriverFactory':
        """
        Context manager entry.
        
        Returns:
            Neo4jDriverFactory instance
        
        Example:
            >>> with Neo4jDriverFactory.get_instance() as factory:
            ...     driver = factory.get_driver()
            ...     # ... use driver ...
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit with resource cleanup.
        
        Ensures the driver is properly closed when exiting the context.
        """
        self.close()
    
    def __repr__(self) -> str:
        """String representation of the factory."""
        return (
            f"Neo4jDriverFactory("
            f"mode={self._connection_mode.value}, "
            f"state={self._connection_state.value}, "
            f"uri={self._config.uri})"
        )


# Convenience functions

def get_driver(
    config: Optional[Neo4jConnectionConfig] = None,
    connection_mode: ConnectionMode = ConnectionMode.DIRECT
) -> Driver:
    """
    Convenience function to get a Neo4j driver instance.
    
    This is a shorthand for Neo4jDriverFactory.get_instance().get_driver()
    
    Args:
        config: Optional Neo4j connection configuration
        connection_mode: Connection mode (direct or gateway)
    
    Returns:
        neo4j.Driver instance
    
    Example:
        >>> from src.config.neo4j_driver import get_driver
        >>> driver = get_driver()
        >>> with driver.session() as session:
        ...     result = session.run("RETURN 1")
    """
    factory = Neo4jDriverFactory.get_instance(config=config, connection_mode=connection_mode)
    return factory.get_driver()


def create_session(
    database: Optional[str] = None,
    config: Optional[Neo4jConnectionConfig] = None,
    **kwargs
):
    """
    Convenience function to create a Neo4j session context manager.
    
    Args:
        database: Optional database name
        config: Optional Neo4j connection configuration
        **kwargs: Additional session configuration
    
    Returns:
        Context manager for neo4j.Session
    
    Example:
        >>> from src.config.neo4j_driver import create_session
        >>> with create_session() as session:
        ...     result = session.run("MATCH (n) RETURN count(n) as count")
        ...     print(result.single()["count"])
    """
    factory = Neo4jDriverFactory.get_instance(config=config)
    return factory.session(database=database, **kwargs)


def validate_connection(
    config: Optional[Neo4jConnectionConfig] = None,
    timeout: int = 5
) -> bool:
    """
    Convenience function to validate Neo4j connection.
    
    Args:
        config: Optional Neo4j connection configuration
        timeout: Timeout in seconds
    
    Returns:
        bool: True if connection is valid
    
    Example:
        >>> from src.config.neo4j_driver import validate_connection
        >>> if validate_connection():
        ...     print("Neo4j connection is healthy")
    """
    factory = Neo4jDriverFactory.get_instance(config=config)
    return factory.validate_connection(timeout=timeout)


def close_driver() -> None:
    """
    Convenience function to close the Neo4j driver.
    
    This should be called when the application is shutting down.
    
    Example:
        >>> from src.config.neo4j_driver import close_driver
        >>> close_driver()
    """
    factory = Neo4jDriverFactory.get_instance()
    factory.close()


def get_connection_metrics() -> Dict[str, Any]:
    """
    Convenience function to get connection metrics.
    
    Returns:
        dict: Connection metrics
    
    Example:
        >>> from src.config.neo4j_driver import get_connection_metrics
        >>> metrics = get_connection_metrics()
        >>> print(f"Total connections: {metrics['total_connections']}")
    """
    factory = Neo4jDriverFactory.get_instance()
    return factory.get_metrics()

