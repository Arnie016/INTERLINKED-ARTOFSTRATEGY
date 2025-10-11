"""
Graph CRUD Tools - Core Create/Read/Update/Delete operations for Neo4j graph database.

This module provides fundamental operations for managing nodes and relationships
in the organizational graph. These tools are essential for data ingestion and
basic graph manipulation.
"""

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
import json


def add_node(driver: GraphDatabase, node_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new node to the graph database.
    
    Args:
        driver: Neo4j driver instance
        node_type: Type/label of the node (e.g., 'Person', 'Process', 'Department')
        properties: Dictionary of node properties
    
    Returns:
        Dict containing the created node data or error information
    """
    try:
        with driver.session() as session:
            # Create parameterized query for safety
            query = f"CREATE (n:{node_type} $props) RETURN n"
            result = session.run(query, props=properties)
            record = result.single()
            
            if record:
                node = record['n']
                return {
                    "success": True,
                    "node": dict(node),
                    "node_id": node.id,
                    "message": f"Successfully created {node_type} node"
                }
            else:
                return {"success": False, "error": "Failed to create node"}
                
    except Exception as e:
        return {"success": False, "error": f"Error creating node: {str(e)}"}


def add_relationship(driver: GraphDatabase, from_node: Dict[str, Any], 
                    to_node: Dict[str, Any], relationship_type: str, 
                    properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add a relationship between two nodes.
    
    Args:
        driver: Neo4j driver instance
        from_node: Dictionary with 'type' and 'properties' to identify source node
        to_node: Dictionary with 'type' and 'properties' to identify target node
        relationship_type: Type of relationship (e.g., 'PERFORMS', 'REPORTS_TO')
        properties: Optional relationship properties
    
    Returns:
        Dict containing the created relationship data or error information
    """
    try:
        with driver.session() as session:
            # Build match conditions for both nodes
            from_conditions = " AND ".join([f"n1.{k} = ${k}" for k in from_node['properties'].keys()])
            to_conditions = " AND ".join([f"n2.{k} = ${k}" for k in to_node['properties'].keys()])
            
            # Create relationship with optional properties
            if properties:
                query = f"""
                MATCH (n1:{from_node['type']}), (n2:{to_node['type']})
                WHERE {from_conditions} AND {to_conditions}
                CREATE (n1)-[r:{relationship_type} $rel_props]->(n2)
                RETURN r
                """
                params = {**from_node['properties'], **to_node['properties'], 'rel_props': properties}
            else:
                query = f"""
                MATCH (n1:{from_node['type']}), (n2:{to_node['type']})
                WHERE {from_conditions} AND {to_conditions}
                CREATE (n1)-[r:{relationship_type}]->(n2)
                RETURN r
                """
                params = {**from_node['properties'], **to_node['properties']}
            
            result = session.run(query, params)
            record = result.single()
            
            if record:
                rel = record['r']
                return {
                    "success": True,
                    "relationship": dict(rel),
                    "relationship_id": rel.id,
                    "message": f"Successfully created {relationship_type} relationship"
                }
            else:
                return {"success": False, "error": "Failed to create relationship - nodes not found"}
                
    except Exception as e:
        return {"success": False, "error": f"Error creating relationship: {str(e)}"}


def update_node(driver: GraphDatabase, node_type: str, 
                match_properties: Dict[str, Any], update_properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update properties of an existing node.
    
    Args:
        driver: Neo4j driver instance
        node_type: Type/label of the node to update
        match_properties: Properties to identify the node
        update_properties: New properties to set
    
    Returns:
        Dict containing the updated node data or error information
    """
    try:
        with driver.session() as session:
            # Build match conditions
            conditions = " AND ".join([f"n.{k} = ${k}" for k in match_properties.keys()])
            
            # Build SET clause
            set_clauses = ", ".join([f"n.{k} = $update_{k}" for k in update_properties.keys()])
            
            query = f"""
            MATCH (n:{node_type})
            WHERE {conditions}
            SET {set_clauses}
            RETURN n
            """
            
            # Prepare parameters
            params = match_properties.copy()
            for k, v in update_properties.items():
                params[f"update_{k}"] = v
            
            result = session.run(query, params)
            record = result.single()
            
            if record:
                node = record['n']
                return {
                    "success": True,
                    "node": dict(node),
                    "message": f"Successfully updated {node_type} node"
                }
            else:
                return {"success": False, "error": "Node not found"}
                
    except Exception as e:
        return {"success": False, "error": f"Error updating node: {str(e)}"}


def delete_node(driver: GraphDatabase, node_type: str, 
                match_properties: Dict[str, Any], delete_relationships: bool = True) -> Dict[str, Any]:
    """
    Delete a node from the graph database.
    
    Args:
        driver: Neo4j driver instance
        node_type: Type/label of the node to delete
        match_properties: Properties to identify the node
        delete_relationships: Whether to delete relationships first (default: True)
    
    Returns:
        Dict containing deletion result or error information
    """
    try:
        with driver.session() as session:
            # Build match conditions
            conditions = " AND ".join([f"n.{k} = ${k}" for k in match_properties.keys()])
            
            if delete_relationships:
                # Delete node and all its relationships
                query = f"""
                MATCH (n:{node_type})
                WHERE {conditions}
                DETACH DELETE n
                RETURN count(n) as deleted_count
                """
            else:
                # Only delete if no relationships exist
                query = f"""
                MATCH (n:{node_type})
                WHERE {conditions} AND NOT (n)--()
                DELETE n
                RETURN count(n) as deleted_count
                """
            
            result = session.run(query, match_properties)
            record = result.single()
            
            deleted_count = record['deleted_count'] if record else 0
            
            if deleted_count > 0:
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "message": f"Successfully deleted {deleted_count} {node_type} node(s)"
                }
            else:
                return {"success": False, "error": "Node not found or has relationships"}
                
    except Exception as e:
        return {"success": False, "error": f"Error deleting node: {str(e)}"}


def get_node(driver: GraphDatabase, node_type: str, 
             match_properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve a specific node from the graph database.
    
    Args:
        driver: Neo4j driver instance
        node_type: Type/label of the node to retrieve
        match_properties: Properties to identify the node
    
    Returns:
        Dict containing the node data or error information
    """
    try:
        with driver.session() as session:
            # Build match conditions
            conditions = " AND ".join([f"n.{k} = ${k}" for k in match_properties.keys()])
            
            query = f"""
            MATCH (n:{node_type})
            WHERE {conditions}
            RETURN n
            """
            
            result = session.run(query, match_properties)
            record = result.single()
            
            if record:
                node = record['n']
                return {
                    "success": True,
                    "node": dict(node),
                    "node_id": node.id
                }
            else:
                return {"success": False, "error": "Node not found"}
                
    except Exception as e:
        return {"success": False, "error": f"Error retrieving node: {str(e)}"}


def list_nodes(driver: GraphDatabase, node_type: str, 
               limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """
    List nodes of a specific type with pagination.
    
    Args:
        driver: Neo4j driver instance
        node_type: Type/label of nodes to retrieve
        limit: Maximum number of nodes to return
        offset: Number of nodes to skip
    
    Returns:
        Dict containing list of nodes or error information
    """
    try:
        with driver.session() as session:
            query = f"""
            MATCH (n:{node_type})
            RETURN n
            SKIP $offset
            LIMIT $limit
            """
            
            result = session.run(query, {"offset": offset, "limit": limit})
            nodes = [dict(record['n']) for record in result]
            
            return {
                "success": True,
                "nodes": nodes,
                "count": len(nodes),
                "offset": offset,
                "limit": limit
            }
                
    except Exception as e:
        return {"success": False, "error": f"Error listing nodes: {str(e)}"}


# Tool registry for this module
TOOLS = {
    "add_node": {
        "function": add_node,
        "description": "Add a new node to the graph database",
        "category": "crud",
        "permissions": ["extractor", "admin"]
    },
    "add_relationship": {
        "function": add_relationship,
        "description": "Add a relationship between two nodes",
        "category": "crud",
        "permissions": ["extractor", "admin"]
    },
    "update_node": {
        "function": update_node,
        "description": "Update properties of an existing node",
        "category": "crud",
        "permissions": ["extractor", "admin"]
    },
    "delete_node": {
        "function": delete_node,
        "description": "Delete a node from the graph database",
        "category": "crud",
        "permissions": ["admin"]
    },
    "get_node": {
        "function": get_node,
        "description": "Retrieve a specific node from the graph database",
        "category": "crud",
        "permissions": ["extractor", "analyzer", "admin", "user"]
    },
    "list_nodes": {
        "function": list_nodes,
        "description": "List nodes of a specific type with pagination",
        "category": "crud",
        "permissions": ["extractor", "analyzer", "admin", "user"]
    }
}
