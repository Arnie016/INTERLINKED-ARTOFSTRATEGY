"""
Graph Search Tools - Complex search, pathfinding, and recommendation queries.

This module provides advanced search and query capabilities for finding
patterns, paths, and recommendations within the organizational graph.
"""

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
import json


def find_shortest_path(driver: GraphDatabase, start_node: Dict[str, Any], 
                      end_node: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
    """
    Find the shortest path between two nodes in the graph.
    
    Args:
        driver: Neo4j driver instance
        start_node: Dictionary with 'type' and 'properties' to identify start node
        end_node: Dictionary with 'type' and 'properties' to identify end node
        max_depth: Maximum path length to search
    
    Returns:
        Dict containing path information or error details
    """
    try:
        with driver.session() as session:
            # Build match conditions
            start_conditions = " AND ".join([f"start.{k} = $start_{k}" for k in start_node['properties'].keys()])
            end_conditions = " AND ".join([f"end.{k} = $end_{k}" for k in end_node['properties'].keys()])
            
            query = f"""
            MATCH (start:{start_node['type']}), (end:{end_node['type']})
            WHERE {start_conditions} AND {end_conditions}
            MATCH path = shortestPath((start)-[*1..{max_depth}]-(end))
            RETURN path, length(path) as path_length
            """
            
            # Prepare parameters
            params = {}
            for k, v in start_node['properties'].items():
                params[f"start_{k}"] = v
            for k, v in end_node['properties'].items():
                params[f"end_{k}"] = v
            
            result = session.run(query, params)
            record = result.single()
            
            if record:
                path = record["path"]
                path_length = record["path_length"]
                
                # Extract path details
                nodes = []
                relationships = []
                
                for node in path.nodes:
                    nodes.append({
                        "id": node.id,
                        "labels": list(node.labels),
                        "properties": dict(node)
                    })
                
                for rel in path.relationships:
                    relationships.append({
                        "id": rel.id,
                        "type": rel.type,
                        "properties": dict(rel),
                        "start_node_id": rel.start_node.id,
                        "end_node_id": rel.end_node.id
                    })
                
                return {
                    "success": True,
                    "path_length": path_length,
                    "nodes": nodes,
                    "relationships": relationships,
                    "message": f"Found path with {path_length} relationships"
                }
            else:
                return {
                    "success": False,
                    "error": "No path found between the specified nodes"
                }
                
    except Exception as e:
        return {"success": False, "error": f"Error finding shortest path: {str(e)}"}


def find_related_nodes(driver: GraphDatabase, node: Dict[str, Any], 
                      relationship_types: Optional[List[str]] = None,
                      max_depth: int = 2, limit: int = 50) -> Dict[str, Any]:
    """
    Find nodes related to a given node through various relationship types.
    
    Args:
        driver: Neo4j driver instance
        node: Dictionary with 'type' and 'properties' to identify the node
        relationship_types: Optional list of relationship types to follow
        max_depth: Maximum depth to traverse
        limit: Maximum number of related nodes to return
    
    Returns:
        Dict containing related nodes and their relationships
    """
    try:
        with driver.session() as session:
            # Build match conditions
            conditions = " AND ".join([f"n.{k} = ${k}" for k in node['properties'].keys()])
            
            # Build relationship pattern - use simple direct relationships for now
            if relationship_types:
                rel_pattern = "|".join(relationship_types)
                rel_clause = f"-[r:{rel_pattern}]->"
            else:
                rel_clause = f"-[r]->"
            
            query = f"""
            MATCH (n:{node['type']}){rel_clause}(related)
            WHERE {conditions}
            RETURN DISTINCT related, labels(related) as labels, 
                   collect(DISTINCT type(r)) as relationship_types
            LIMIT $limit
            """
            
            result = session.run(query, {**node['properties'], "limit": limit})
            
            related_nodes = []
            for record in result:
                related_node = record["related"]
                related_nodes.append({
                    "id": related_node.id,
                    "labels": record["labels"],
                    "properties": dict(related_node),
                    "relationship_types": record["relationship_types"]
                })
            
            return {
                "success": True,
                "related_nodes": related_nodes,
                "count": len(related_nodes),
                "message": f"Found {len(related_nodes)} related nodes"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error finding related nodes: {str(e)}"}


def search_nodes(driver: GraphDatabase, search_term: str, 
                node_types: Optional[List[str]] = None,
                properties: Optional[List[str]] = None,
                limit: int = 20) -> Dict[str, Any]:
    """
    Search for nodes by name or other properties using fuzzy matching.
    
    Args:
        driver: Neo4j driver instance
        search_term: Term to search for
        node_types: Optional list of node types to search in
        properties: Optional list of properties to search in
        limit: Maximum number of results to return
    
    Returns:
        Dict containing matching nodes
    """
    try:
        with driver.session() as session:
            # Default properties to search if none specified
            if not properties:
                properties = ["name", "description", "title", "role"]
            
            # Build node type filter
            if node_types:
                type_filter = f"AND labels(n) IN {node_types}"
            else:
                type_filter = ""
            
            # Build property search conditions
            property_conditions = []
            for prop in properties:
                property_conditions.append(f"n.{prop} CONTAINS $search_term")
            
            conditions = " OR ".join(property_conditions)
            
            query = f"""
            MATCH (n)
            WHERE ({conditions}) {type_filter}
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
            
            result = session.run(query, {"search_term": search_term, "limit": limit})
            
            matching_nodes = []
            for record in result:
                node = record["n"]
                matching_nodes.append({
                    "id": node.id,
                    "labels": record["labels"],
                    "properties": dict(node)
                })
            
            return {
                "success": True,
                "matching_nodes": matching_nodes,
                "count": len(matching_nodes),
                "search_term": search_term,
                "message": f"Found {len(matching_nodes)} nodes matching '{search_term}'"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error searching nodes: {str(e)}"}


def find_influential_nodes(driver: GraphDatabase, node_type: str = "Person",
                          metric: str = "betweenness", limit: int = 10) -> Dict[str, Any]:
    """
    Find the most influential nodes using centrality metrics.
    
    Args:
        driver: Neo4j driver instance
        node_type: Type of nodes to analyze
        metric: Centrality metric to use ('degree', 'betweenness', 'closeness')
        limit: Maximum number of results to return
    
    Returns:
        Dict containing influential nodes with their scores
    """
    try:
        with driver.session() as session:
            if metric == "degree":
                # Degree centrality - nodes with most connections
                query = f"""
                MATCH (n:{node_type})
                OPTIONAL MATCH (n)-[r]-(connected)
                WITH n, count(r) as degree
                RETURN n, degree
                ORDER BY degree DESC
                LIMIT $limit
                """
                
            elif metric == "betweenness":
                # Betweenness centrality - nodes that are bridges between others
                # Note: This is a simplified version. For large graphs, consider using APOC
                query = f"""
                MATCH (n:{node_type})
                OPTIONAL MATCH (a:{node_type})-[r1*1..2]-(n)-[r2*1..2]-(b:{node_type})
                WHERE a <> b AND a <> n AND b <> n
                WITH n, count(DISTINCT [a, b]) as betweenness
                RETURN n, betweenness
                ORDER BY betweenness DESC
                LIMIT $limit
                """
                
            elif metric == "closeness":
                # Closeness centrality - nodes closest to all other nodes
                query = f"""
                MATCH (n:{node_type})
                OPTIONAL MATCH (n)-[r*1..3]-(other:{node_type})
                WHERE other <> n
                WITH n, avg(length(r)) as avg_distance, count(other) as reachable
                WHERE reachable > 0
                WITH n, 1.0 / avg_distance as closeness, reachable
                RETURN n, closeness, reachable
                ORDER BY closeness DESC
                LIMIT $limit
                """
                
            else:
                return {"success": False, "error": f"Unknown metric: {metric}"}
            
            result = session.run(query, {"limit": limit})
            
            influential_nodes = []
            for record in result:
                node = record["n"]
                score = record[metric] if metric in record else record.get("closeness", 0)
                
                node_data = {
                    "id": node.id,
                    "properties": dict(node),
                    "centrality_score": score
                }
                
                if metric == "closeness":
                    node_data["reachable_nodes"] = record.get("reachable", 0)
                
                influential_nodes.append(node_data)
            
            return {
                "success": True,
                "influential_nodes": influential_nodes,
                "metric": metric,
                "count": len(influential_nodes),
                "message": f"Found {len(influential_nodes)} most influential {node_type} nodes by {metric} centrality"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error finding influential nodes: {str(e)}"}


def recommend_collaborations(driver: GraphDatabase, person_name: str,
                           max_recommendations: int = 5) -> Dict[str, Any]:
    """
    Recommend potential collaborations for a person based on shared connections and interests.
    
    Args:
        driver: Neo4j driver instance
        person_name: Name of the person to get recommendations for
        max_recommendations: Maximum number of recommendations to return
    
    Returns:
        Dict containing collaboration recommendations
    """
    try:
        with driver.session() as session:
            # Find people with shared connections (collaborative filtering)
            query = """
            MATCH (p:Person {name: $person_name})
            MATCH (p)-[:COLLABORATES_WITH]->(shared)-[:COLLABORATES_WITH]->(recommended:Person)
            WHERE recommended <> p AND NOT (p)-[:COLLABORATES_WITH]->(recommended)
            WITH recommended, count(shared) as shared_connections,
                 collect(shared.name) as mutual_connections
            ORDER BY shared_connections DESC
            LIMIT $limit
            RETURN recommended, shared_connections, mutual_connections
            """
            
            result = session.run(query, {
                "person_name": person_name,
                "limit": max_recommendations
            })
            
            recommendations = []
            for record in result:
                recommended_person = record["recommended"]
                recommendations.append({
                    "id": recommended_person.id,
                    "name": recommended_person["name"],
                    "role": recommended_person.get("role", ""),
                    "department": recommended_person.get("department", ""),
                    "shared_connections": record["shared_connections"],
                    "mutual_connections": record["mutual_connections"],
                    "reason": f"Shares {record['shared_connections']} mutual connections"
                })
            
            return {
                "success": True,
                "recommendations": recommendations,
                "count": len(recommendations),
                "person": person_name,
                "message": f"Found {len(recommendations)} collaboration recommendations for {person_name}"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error generating recommendations: {str(e)}"}


def find_communities(driver: GraphDatabase, node_type: str = "Person",
                    min_community_size: int = 3) -> Dict[str, Any]:
    """
    Find communities (clusters) of closely connected nodes.
    
    Args:
        driver: Neo4j driver instance
        node_type: Type of nodes to analyze
        min_community_size: Minimum size for a community to be included
    
    Returns:
        Dict containing identified communities
    """
    try:
        with driver.session() as session:
            # Simple community detection using connected components
            # For more sophisticated algorithms, consider using APOC or GDS
            query = f"""
            MATCH (n:{node_type})
            WHERE NOT n:Processed
            WITH n
            MATCH path = (n)-[*1..3]-(connected:{node_type})
            WHERE NOT connected:Processed
            WITH n, collect(DISTINCT connected) as community
            WHERE size(community) >= $min_size
            SET n:Processed
            WITH n, community
            UNWIND community as member
            SET member:Processed
            RETURN n, community, size(community) as community_size
            ORDER BY community_size DESC
            """
            
            result = session.run(query, {"min_size": min_community_size})
            
            communities = []
            for record in result:
                center_node = record["n"]
                community_members = record["community"]
                
                community_data = {
                    "center_node": {
                        "id": center_node.id,
                        "properties": dict(center_node)
                    },
                    "members": [
                        {
                            "id": member.id,
                            "properties": dict(member)
                        }
                        for member in community_members
                    ],
                    "size": record["community_size"]
                }
                communities.append(community_data)
            
            # Clean up processed labels
            session.run(f"MATCH (n:{node_type}:Processed) REMOVE n:Processed")
            
            return {
                "success": True,
                "communities": communities,
                "count": len(communities),
                "min_community_size": min_community_size,
                "message": f"Found {len(communities)} communities with at least {min_community_size} members"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error finding communities: {str(e)}"}


def advanced_query(driver: GraphDatabase, cypher_query: str, 
                  parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a custom Cypher query with parameters.
    
    Args:
        driver: Neo4j driver instance
        cypher_query: Custom Cypher query to execute
        parameters: Optional parameters for the query
    
    Returns:
        Dict containing query results or error information
    """
    try:
        with driver.session() as session:
            params = parameters or {}
            result = session.run(cypher_query, params)
            
            # Convert results to list of dictionaries
            records = []
            for record in result:
                record_dict = {}
                for key in record.keys():
                    value = record[key]
                    # Convert Neo4j objects to Python dictionaries
                    if hasattr(value, 'id') and hasattr(value, 'labels'):
                        # Node
                        record_dict[key] = {
                            "id": value.id,
                            "labels": list(value.labels),
                            "properties": dict(value)
                        }
                    elif hasattr(value, 'id') and hasattr(value, 'type'):
                        # Relationship
                        record_dict[key] = {
                            "id": value.id,
                            "type": value.type,
                            "properties": dict(value),
                            "start_node_id": value.start_node.id,
                            "end_node_id": value.end_node.id
                        }
                    else:
                        # Primitive value
                        record_dict[key] = value
                
                records.append(record_dict)
            
            return {
                "success": True,
                "results": records,
                "count": len(records),
                "query": cypher_query,
                "message": f"Query executed successfully, returned {len(records)} records"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error executing query: {str(e)}"}


# Tool registry for this module
TOOLS = {
    "find_shortest_path": {
        "function": find_shortest_path,
        "description": "Find the shortest path between two nodes in the graph",
        "category": "search",
        "permissions": ["analyzer", "admin", "user"]
    },
    "find_related_nodes": {
        "function": find_related_nodes,
        "description": "Find nodes related to a given node through various relationship types",
        "category": "search",
        "permissions": ["analyzer", "admin", "user"]
    },
    "search_nodes": {
        "function": search_nodes,
        "description": "Search for nodes by name or other properties using fuzzy matching",
        "category": "search",
        "permissions": ["analyzer", "admin", "user"]
    },
    "find_influential_nodes": {
        "function": find_influential_nodes,
        "description": "Find the most influential nodes using centrality metrics",
        "category": "search",
        "permissions": ["analyzer", "admin", "user"]
    },
    "recommend_collaborations": {
        "function": recommend_collaborations,
        "description": "Recommend potential collaborations for a person based on shared connections",
        "category": "search",
        "permissions": ["analyzer", "admin", "user"]
    },
    "find_communities": {
        "function": find_communities,
        "description": "Find communities (clusters) of closely connected nodes",
        "category": "search",
        "permissions": ["analyzer", "admin", "user"]
    },
    "advanced_query": {
        "function": advanced_query,
        "description": "Execute a custom Cypher query with parameters",
        "category": "search",
        "permissions": ["admin", "analyzer"]
    }
}
