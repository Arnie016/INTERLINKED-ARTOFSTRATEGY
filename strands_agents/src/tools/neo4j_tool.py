"""
Neo4j Tool for Agents

This tool provides comprehensive access to Neo4j database operations
for agents to query nodes, relationships, and their details.
"""

import sys
import os
from typing import Dict, List, Any, Optional, Union
import logging

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.neo4j_driver import get_neo4j_driver, execute_query, execute_write_query

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jTool:
    """Tool for agents to interact with Neo4j database."""
    
    def __init__(self):
        """Initialize the Neo4j tool."""
        self.driver = get_neo4j_driver()
        logger.info("Neo4j tool initialized")
    
    def get_all_nodes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all nodes in the database with their properties.
        
        Args:
            limit: Maximum number of nodes to return (default: 100)
            
        Returns:
            List of dictionaries containing node information
        """
        try:
            query = f"""
            MATCH (n)
            RETURN n, labels(n) as labels, elementId(n) as node_id
            LIMIT {limit}
            """
            results = execute_query(query)
            
            nodes = []
            for record in results:
                node_data = dict(record['n'])
                nodes.append({
                    'id': record['node_id'],
                    'labels': record['labels'],
                    'properties': node_data
                })
            
            logger.info(f"Retrieved {len(nodes)} nodes")
            return nodes
            
        except Exception as e:
            logger.error(f"Error getting all nodes: {e}")
            return []
    
    def get_all_relationships(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all relationships in the database with their properties.
        
        Args:
            limit: Maximum number of relationships to return (default: 100)
            
        Returns:
            List of dictionaries containing relationship information
        """
        try:
            query = f"""
            MATCH (a)-[r]->(b)
            RETURN a, r, b, type(r) as relationship_type, elementId(r) as rel_id
            LIMIT {limit}
            """
            results = execute_query(query)
            
            relationships = []
            for record in results:
                rel_data = dict(record['r'])
                relationships.append({
                    'id': record['rel_id'],
                    'type': record['relationship_type'],
                    'start_node': {
                        'id': record['a'].element_id,
                        'labels': list(record['a'].labels),
                        'properties': dict(record['a'])
                    },
                    'end_node': {
                        'id': record['b'].element_id,
                        'labels': list(record['b'].labels),
                        'properties': dict(record['b'])
                    },
                    'properties': rel_data
                })
            
            logger.info(f"Retrieved {len(relationships)} relationships")
            return relationships
            
        except Exception as e:
            logger.error(f"Error getting all relationships: {e}")
            return []
    
    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all nodes with a specific label.
        
        Args:
            label: The node label to filter by
            limit: Maximum number of nodes to return (default: 100)
            
        Returns:
            List of dictionaries containing node information
        """
        try:
            query = f"""
            MATCH (n:{label})
            RETURN n, labels(n) as labels, elementId(n) as node_id
            LIMIT {limit}
            """
            results = execute_query(query)
            
            nodes = []
            for record in results:
                node_data = dict(record['n'])
                nodes.append({
                    'id': record['node_id'],
                    'labels': record['labels'],
                    'properties': node_data
                })
            
            logger.info(f"Retrieved {len(nodes)} nodes with label '{label}'")
            return nodes
            
        except Exception as e:
            logger.error(f"Error getting nodes by label '{label}': {e}")
            return []
    
    def get_relationships_by_type(self, rel_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all relationships of a specific type.
        
        Args:
            rel_type: The relationship type to filter by
            limit: Maximum number of relationships to return (default: 100)
            
        Returns:
            List of dictionaries containing relationship information
        """
        try:
            query = f"""
            MATCH (a)-[r:{rel_type}]->(b)
            RETURN a, r, b, type(r) as relationship_type, elementId(r) as rel_id
            LIMIT {limit}
            """
            results = execute_query(query)
            
            relationships = []
            for record in results:
                rel_data = dict(record['r'])
                relationships.append({
                    'id': record['rel_id'],
                    'type': record['relationship_type'],
                    'start_node': {
                        'id': record['a'].element_id,
                        'labels': list(record['a'].labels),
                        'properties': dict(record['a'])
                    },
                    'end_node': {
                        'id': record['b'].element_id,
                        'labels': list(record['b'].labels),
                        'properties': dict(record['b'])
                    },
                    'properties': rel_data
                })
            
            logger.info(f"Retrieved {len(relationships)} relationships of type '{rel_type}'")
            return relationships
            
        except Exception as e:
            logger.error(f"Error getting relationships by type '{rel_type}': {e}")
            return []
    
    def get_node_by_id(self, node_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific node by its ID.
        
        Args:
            node_id: The ID of the node to retrieve
            
        Returns:
            Dictionary containing node information or None if not found
        """
        try:
            query = """
            MATCH (n)
            WHERE elementId(n) = $node_id
            RETURN n, labels(n) as labels, elementId(n) as node_id
            """
            results = execute_query(query, {'node_id': node_id})
            
            if results:
                record = results[0]
                node_data = dict(record['n'])
                return {
                    'id': record['node_id'],
                    'labels': record['labels'],
                    'properties': node_data
                }
            
            logger.warning(f"Node with ID {node_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting node by ID {node_id}: {e}")
            return None
    
    def get_node_connections(self, node_id: int, depth: int = 1) -> Dict[str, Any]:
        """
        Get all connections (relationships) for a specific node.
        
        Args:
            node_id: The ID of the node
            depth: How many hops to traverse (default: 1)
            
        Returns:
            Dictionary containing node and its connections
        """
        try:
            query = f"""
            MATCH (n)-[r*1..{depth}]-(connected)
            WHERE elementId(n) = $node_id
            RETURN n, r, connected, labels(n) as start_labels, labels(connected) as end_labels
            """
            results = execute_query(query, {'node_id': node_id})
            
            if not results:
                logger.warning(f"No connections found for node {node_id}")
                return {'node': None, 'connections': []}
            
            # Get the main node
            main_node = results[0]['n']
            main_node_data = {
                'id': node_id,
                'labels': results[0]['start_labels'],
                'properties': dict(main_node)
            }
            
            # Get all connections
            connections = []
            for record in results:
                if record['connected'] != main_node:  # Avoid self-connections
                    connections.append({
                        'id': record['connected'].element_id,
                        'labels': record['end_labels'],
                        'properties': dict(record['connected']),
                        'relationships': [dict(rel) for rel in record['r']] if isinstance(record['r'], list) else [dict(record['r'])]
                    })
            
            logger.info(f"Retrieved {len(connections)} connections for node {node_id}")
            return {
                'node': main_node_data,
                'connections': connections
            }
            
        except Exception as e:
            logger.error(f"Error getting connections for node {node_id}: {e}")
            return {'node': None, 'connections': []}
    
    def search_nodes(self, property_name: str, property_value: Any, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for nodes by property name and value.
        
        Args:
            property_name: The property name to search by
            property_value: The property value to match
            limit: Maximum number of nodes to return (default: 100)
            
        Returns:
            List of dictionaries containing matching nodes
        """
        try:
            query = f"""
            MATCH (n)
            WHERE n.{property_name} = $property_value
            RETURN n, labels(n) as labels, elementId(n) as node_id
            LIMIT {limit}
            """
            results = execute_query(query, {'property_value': property_value})
            
            nodes = []
            for record in results:
                node_data = dict(record['n'])
                nodes.append({
                    'id': record['node_id'],
                    'labels': record['labels'],
                    'properties': node_data
                })
            
            logger.info(f"Found {len(nodes)} nodes with {property_name} = {property_value}")
            return nodes
            
        except Exception as e:
            logger.error(f"Error searching nodes by {property_name}: {e}")
            return []
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get the database schema information including all labels and relationship types.
        
        Returns:
            Dictionary containing schema information
        """
        try:
            # Get all node labels
            labels_query = """
            CALL db.labels() YIELD label
            RETURN collect(label) as labels
            """
            labels_result = execute_query(labels_query)
            labels = labels_result[0]['labels'] if labels_result else []
            
            # Get all relationship types
            rel_types_query = """
            CALL db.relationshipTypes() YIELD relationshipType
            RETURN collect(relationshipType) as relationship_types
            """
            rel_types_result = execute_query(rel_types_query)
            relationship_types = rel_types_result[0]['relationship_types'] if rel_types_result else []
            
            # Get node counts by label
            node_counts = {}
            for label in labels:
                count_query = f"MATCH (n:{label}) RETURN count(n) as count"
                count_result = execute_query(count_query)
                node_counts[label] = count_result[0]['count'] if count_result else 0
            
            # Get relationship counts by type
            rel_counts = {}
            for rel_type in relationship_types:
                count_query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                count_result = execute_query(count_query)
                rel_counts[rel_type] = count_result[0]['count'] if count_result else 0
            
            schema = {
                'labels': labels,
                'relationship_types': relationship_types,
                'node_counts': node_counts,
                'relationship_counts': rel_counts,
                'total_nodes': sum(node_counts.values()),
                'total_relationships': sum(rel_counts.values())
            }
            
            logger.info(f"Retrieved schema: {len(labels)} labels, {len(relationship_types)} relationship types")
            return schema
            
        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            return {'error': str(e)}
    
    def execute_custom_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.
        
        Args:
            query: The Cypher query to execute
            parameters: Optional parameters for the query
            
        Returns:
            List of query results
        """
        try:
            results = execute_query(query, parameters or {})
            logger.info(f"Executed custom query, returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Dictionary containing database statistics
        """
        try:
            # Get basic counts
            node_count_query = "MATCH (n) RETURN count(n) as node_count"
            rel_count_query = "MATCH ()-[r]->() RETURN count(r) as rel_count"
            
            node_count = execute_query(node_count_query)[0]['node_count']
            rel_count = execute_query(rel_count_query)[0]['rel_count']
            
            # Get schema info
            schema = self.get_database_schema()
            
            stats = {
                'total_nodes': node_count,
                'total_relationships': rel_count,
                'schema': schema,
                'database_info': self.driver.get_database_info()
            }
            
            logger.info(f"Retrieved database stats: {node_count} nodes, {rel_count} relationships")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}


# Convenience functions for direct use
def get_all_nodes(limit: int = 100) -> List[Dict[str, Any]]:
    """Get all nodes in the database."""
    tool = Neo4jTool()
    return tool.get_all_nodes(limit)


def get_all_relationships(limit: int = 100) -> List[Dict[str, Any]]:
    """Get all relationships in the database."""
    tool = Neo4jTool()
    return tool.get_all_relationships(limit)


def get_nodes_by_label(label: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get nodes by label."""
    tool = Neo4jTool()
    return tool.get_nodes_by_label(label, limit)


def get_relationships_by_type(rel_type: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get relationships by type."""
    tool = Neo4jTool()
    return tool.get_relationships_by_type(rel_type, limit)


def get_database_schema() -> Dict[str, Any]:
    """Get database schema information."""
    tool = Neo4jTool()
    return tool.get_database_schema()


def get_database_stats() -> Dict[str, Any]:
    """Get comprehensive database statistics."""
    tool = Neo4jTool()
    return tool.get_database_stats()


# Example usage
if __name__ == "__main__":
    # Test the tool
    print("🔧 Testing Neo4j Tool")
    print("=" * 40)
    
    try:
        tool = Neo4jTool()
        
        # Test database stats
        print("📊 Database Statistics:")
        stats = tool.get_database_stats()
        if 'error' not in stats:
            print(f"  Total Nodes: {stats['total_nodes']:,}")
            print(f"  Total Relationships: {stats['total_relationships']:,}")
            print(f"  Labels: {len(stats['schema']['labels'])}")
            print(f"  Relationship Types: {len(stats['schema']['relationship_types'])}")
        
        # Test getting nodes by label
        print("\n🏷️  Nodes by Label:")
        for label in stats.get('schema', {}).get('labels', [])[:3]:  # Show first 3 labels
            nodes = tool.get_nodes_by_label(label, limit=5)
            print(f"  {label}: {len(nodes)} nodes (showing first 5)")
            for node in nodes[:2]:  # Show first 2 nodes
                print(f"    - {node['properties']}")
        
        # Test getting relationships
        print("\n🔗 Relationships:")
        relationships = tool.get_all_relationships(limit=5)
        print(f"  Found {len(relationships)} relationships (showing first 5)")
        for rel in relationships[:2]:  # Show first 2 relationships
            print(f"    - {rel['start_node']['labels']} -[{rel['type']}]-> {rel['end_node']['labels']}")
        
        print("\n✅ Neo4j tool test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing Neo4j tool: {e}")
