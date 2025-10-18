"""
Neo4j Configuration Module

Simple configuration for connecting to Neo4j database.
Supports both local and cloud Neo4j instances.
"""

import os
from typing import Optional, Dict, Any
from neo4j import GraphDatabase, Driver
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jConfig:
    """Neo4j configuration and connection management."""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j"
    ):
        """
        Initialize Neo4j configuration.
        
        Args:
            uri: Neo4j connection URI (defaults to environment variable or local)
            username: Username (defaults to environment variable or 'neo4j')
            password: Password (defaults to environment variable)
            database: Database name (defaults to 'neo4j')
        """
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        self.database = database
        
        if not self.password:
            raise ValueError(
                "Neo4j password is required. Set NEO4J_PASSWORD environment variable "
                "or pass password parameter."
            )
        
        self._driver: Optional[Driver] = None
    
    def get_driver(self) -> Driver:
        """Get or create Neo4j driver instance."""
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password)
                )
                logger.info(f"Connected to Neo4j at {self.uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
        
        return self._driver
    
    def close(self):
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
    
    def test_connection(self) -> bool:
        """Test the Neo4j connection."""
        try:
            driver = self.get_driver()
            with driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                logger.info("Neo4j connection test successful")
                return test_value == 1
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the Neo4j database."""
        try:
            driver = self.get_driver()
            with driver.session(database=self.database) as session:
                # Get database info
                result = session.run("CALL db.info()")
                db_info = result.single()
                
                # Get node and relationship counts
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                
                return {
                    "database_name": db_info.get("name", "unknown"),
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "uri": self.uri,
                    "username": self.username
                }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for quick setup
def create_neo4j_config(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    database: str = "neo4j"
) -> Neo4jConfig:
    """
    Create a Neo4j configuration instance.
    
    Args:
        uri: Neo4j connection URI
        username: Username
        password: Password
        database: Database name
    
    Returns:
        Neo4jConfig instance
    """
    return Neo4jConfig(uri, username, password, database)


# Example usage
if __name__ == "__main__":
    # Test the configuration
    try:
        with create_neo4j_config() as config:
            print("Testing Neo4j connection...")
            
            if config.test_connection():
                print("✅ Connection successful!")
                
                # Get database info
                info = config.get_database_info()
                print(f"Database: {info.get('database_name', 'unknown')}")
                print(f"Nodes: {info.get('node_count', 0)}")
                print(f"Relationships: {info.get('relationship_count', 0)}")
            else:
                print("❌ Connection failed!")
                
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Neo4j running (local or cloud)")
        print("2. NEO4J_PASSWORD environment variable set")
        print("3. NEO4J_URI set if not using localhost:7687")
        print("4. NEO4J_USERNAME set if not using 'neo4j'")
