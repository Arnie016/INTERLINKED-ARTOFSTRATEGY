"""
Neo4j Driver Module

Production-ready Neo4j driver that loads credentials from .env file.
This module provides a singleton driver instance for the application.
"""

import os
from typing import Optional, Dict, Any
from neo4j import GraphDatabase, Driver
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Neo4jDriver:
    """Singleton Neo4j driver for the application."""
    
    _instance: Optional['Neo4jDriver'] = None
    _driver: Optional[Driver] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jDriver, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.uri = os.getenv('NEO4J_URI')
            self.username = os.getenv('NEO4J_USERNAME')
            self.password = os.getenv('NEO4J_PASSWORD')
            self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
            self.aura_instance_id = os.getenv('AURA_INSTANCEID')
            self.aura_instance_name = os.getenv('AURA_INSTANCENAME')
            
            if not all([self.uri, self.username, self.password]):
                raise ValueError(
                    "Missing required Neo4j credentials. Check your .env file for:\n"
                    "- NEO4J_URI\n"
                    "- NEO4J_USERNAME\n"
                    "- NEO4J_PASSWORD"
                )
            
            logger.info(f"Neo4j driver initialized for {self.aura_instance_name} ({self.aura_instance_id})")
    
    def get_driver(self) -> Driver:
        """Get or create Neo4j driver instance."""
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password)
                )
                logger.info(f"Connected to Neo4j Aura instance: {self.aura_instance_name}")
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
                    "username": self.username,
                    "aura_instance_id": self.aura_instance_id,
                    "aura_instance_name": self.aura_instance_name
                }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def execute_query(self, query: str, parameters: Optional[Dict] = None) -> Any:
        """Execute a Cypher query and return results."""
        try:
            driver = self.get_driver()
            with driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return list(result)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_write_query(self, query: str, parameters: Optional[Dict] = None) -> Any:
        """Execute a write Cypher query and return results."""
        try:
            driver = self.get_driver()
            with driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return list(result)
        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global driver instance
neo4j_driver = Neo4jDriver()


# Convenience functions
def get_neo4j_driver() -> Neo4jDriver:
    """Get the global Neo4j driver instance."""
    return neo4j_driver


def get_database_session():
    """Get a Neo4j database session."""
    driver = neo4j_driver.get_driver()
    return driver.session(database=neo4j_driver.database)


def execute_query(query: str, parameters: Optional[Dict] = None) -> Any:
    """Execute a Cypher query using the global driver."""
    return neo4j_driver.execute_query(query, parameters)


def execute_write_query(query: str, parameters: Optional[Dict] = None) -> Any:
    """Execute a write Cypher query using the global driver."""
    return neo4j_driver.execute_write_query(query, parameters)


# Example usage
if __name__ == "__main__":
    # Test the driver
    try:
        driver = get_neo4j_driver()
        print("🔗 Testing Neo4j Driver")
        print("=" * 40)
        
        if driver.test_connection():
            print("✅ Connection successful!")
            
            # Get database info
            info = driver.get_database_info()
            if "error" not in info:
                print(f"Database: {info.get('database_name', 'unknown')}")
                print(f"Aura Instance: {info.get('aura_instance_name', 'unknown')} ({info.get('aura_instance_id', 'unknown')})")
                print(f"Nodes: {info.get('node_count', 0):,}")
                print(f"Relationships: {info.get('relationship_count', 0):,}")
                
                # Test a simple query
                print("\n🔍 Testing query execution...")
                results = execute_query("MATCH (n) RETURN labels(n) as labels, count(n) as count LIMIT 5")
                if results:
                    print("Sample node types:")
                    for record in results:
                        labels = record["labels"]
                        count = record["count"]
                        label_str = ":".join(labels) if labels else "No labels"
                        print(f"  {label_str}: {count:,} nodes")
                else:
                    print("No nodes found in database")
            else:
                print(f"❌ Error getting database info: {info['error']}")
        else:
            print("❌ Connection failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your .env file contains valid Neo4j credentials")
