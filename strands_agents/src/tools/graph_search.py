"""
Graph Search Tools - Read-only search and retrieval operations.

These tools provide safe, read-only access to search and retrieve
nodes and relationships from the Neo4j graph database.
"""

from strands import tool
from typing import List, Dict, Any, Optional
from neo4j.exceptions import Neo4jError

try:
    from ..config import get_driver, create_session
    from ..utils.validation import validate_search_query, validate_pagination_params, validate_node_label
    from ..utils.errors import GraphQueryError, ValidationError, ToolExecutionError
    from ..utils.logging import get_logger
    from ..config.constants import VALID_NODE_LABELS, VALID_RELATIONSHIP_TYPES
except ImportError:
    from config import get_driver, create_session
    from utils.validation import validate_search_query, validate_pagination_params, validate_node_label
    from utils.errors import GraphQueryError, ValidationError, ToolExecutionError
    from utils.logging import get_logger
    from config.constants import VALID_NODE_LABELS, VALID_RELATIONSHIP_TYPES

# Initialize logger
logger = get_logger(__name__)


@tool
def search_nodes(
    query: str,
    node_types: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for nodes in the graph by text query.
    
    This tool searches across node properties (name, description, role, etc.)
    to find matching entities in the organizational graph.
    
    Args:
        query: The search term or phrase to look for
        node_types: Optional list of node types to filter by
                   (e.g., ["Person", "Organization", "Project"])
        limit: Maximum number of results to return (default: 10, max: 50)
    
    Returns:
        A list of matching nodes with their properties and labels.
        Each node includes: id, labels, and all properties.
    
    Examples:
        - search_nodes("engineering", node_types=["Person"])
        - search_nodes("deployment", node_types=["Project"])
        - search_nodes("alice johnson")
    """
    try:
        # Validate inputs
        query = validate_search_query(query, min_length=1, max_length=500)
        pagination = validate_pagination_params(limit=limit, max_limit=50, default_limit=10)
        limit = pagination["limit"]
        
        # Validate node types if provided
        if node_types:
            for node_type in node_types:
                if node_type not in VALID_NODE_LABELS:
                    raise ValidationError(
                        f"Invalid node type: {node_type}. Valid types: {', '.join(VALID_NODE_LABELS)}",
                        field="node_types"
                    )
        
        logger.info(
            f"Searching nodes with query: '{query[:50]}...' node_types: {node_types}, limit: {limit}",
            operation="search_nodes"
        )
        
        # Build Cypher query with parameterization for safety
        where_clauses = []
        params = {"query": query.lower(), "limit": limit}
        
        # Add full-text search conditions
        where_clauses.append(
            "(toLower(n.name) CONTAINS $query OR "
            "toLower(n.description) CONTAINS $query OR "
            "toLower(n.role) CONTAINS $query OR "
            "toLower(n.title) CONTAINS $query)"
        )
        
        # Build label filter if node_types provided
        if node_types:
            label_conditions = " OR ".join([f"n:{label}" for label in node_types])
            where_clauses.append(f"({label_conditions})")
        
        where_clause = " AND ".join(where_clauses)
        
        cypher_query = f"""
        MATCH (n)
        WHERE {where_clause}
        RETURN 
            id(n) as node_id,
            labels(n) as labels,
            properties(n) as properties
        LIMIT $limit
        """
        
        # Execute query
        results = []
        with create_session() as session:
            result = session.run(cypher_query, params)
            
            for record in result:
                node_data = {
                    "id": str(record["node_id"]),
                    "labels": record["labels"],
                    "properties": dict(record["properties"])
                }
                results.append(node_data)
        
        logger.info(
            f"Search completed successfully. Found {len(results)} nodes",
            operation="search_nodes",
            result_count=len(results)
        )
        
        return results
        
    except ValidationError as e:
        logger.error(f"Validation error in search_nodes: {e}", operation="search_nodes")
        raise ToolExecutionError(
            message=f"Invalid search parameters: {e.message}",
            tool_name="search_nodes",
            details=e.details,
            original_error=e
        )
    except Neo4jError as e:
        logger.error(f"Neo4j error in search_nodes: {e}", operation="search_nodes")
        raise GraphQueryError(
            message="Failed to execute search query",
            query=cypher_query if 'cypher_query' in locals() else None,
            original_error=e
        )
    except Exception as e:
        logger.error(f"Unexpected error in search_nodes: {e}", operation="search_nodes")
        raise ToolExecutionError(
            message="Search operation failed",
            tool_name="search_nodes",
            original_error=e
        )


@tool
def find_related_nodes(
    node: Dict[str, Any],
    relationship_types: Optional[List[str]] = None,
    direction: str = "both",
    depth: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Find nodes related to a given node through specified relationships.
    
    This tool traverses the graph to find entities connected to the
    starting node through various relationship types.
    
    Args:
        node: The starting node specified as {"type": "Person", "properties": {"name": "Alice"}}
        relationship_types: Optional list of relationship types to follow
                          (e.g., ["WORKS_AT", "MANAGES", "PARTICIPATES_IN"])
                          If None, follows all relationship types.
        direction: Direction to traverse ("outgoing", "incoming", "both")
        depth: How many hops away to search (1-3, default: 1)
        limit: Maximum number of related nodes to return (default: 20, max: 100)
    
    Returns:
        A dictionary containing:
        - "center_node": The starting node
        - "related_nodes": List of connected nodes with their relationships
        - "relationship_count": Total number of relationships found
    
    Examples:
        - find_related_nodes({"type": "Person", "properties": {"name": "Alice"}}, ["MANAGES"])
        - find_related_nodes({"type": "Project", "properties": {"name": "Deploy"}}, ["USES"])
    """
    try:
        # Validate inputs
        if not node or not isinstance(node, dict):
            raise ValidationError("Node parameter must be a dictionary", field="node")
        
        if "type" not in node or "properties" not in node:
            raise ValidationError(
                "Node must have 'type' and 'properties' fields",
                field="node"
            )
        
        node_type = node["type"]
        node_props = node["properties"]
        
        # Validate node type
        if node_type not in VALID_NODE_LABELS:
            raise ValidationError(
                f"Invalid node type: {node_type}. Valid types: {', '.join(VALID_NODE_LABELS)}",
                field="node.type"
            )
        
        # Validate relationship types if provided
        if relationship_types:
            for rel_type in relationship_types:
                if rel_type not in VALID_RELATIONSHIP_TYPES:
                    raise ValidationError(
                        f"Invalid relationship type: {rel_type}. Valid types: {', '.join(VALID_RELATIONSHIP_TYPES)}",
                        field="relationship_types"
                    )
        
        # Validate direction
        valid_directions = ["outgoing", "incoming", "both"]
        if direction not in valid_directions:
            raise ValidationError(
                f"Invalid direction: {direction}. Valid: {', '.join(valid_directions)}",
                field="direction"
            )
        
        # Validate depth
        if not isinstance(depth, int) or depth < 1 or depth > 3:
            raise ValidationError("Depth must be an integer between 1 and 3", field="depth")
        
        # Validate limit
        pagination = validate_pagination_params(limit=limit, max_limit=100, default_limit=20)
        limit = pagination["limit"]
        
        logger.info(
            f"Finding related nodes for {node_type} with props: {node_props}, "
            f"rel_types: {relationship_types}, direction: {direction}, depth: {depth}",
            operation="find_related_nodes"
        )
        
        # Build query to find center node first
        where_conditions = []
        params = {"limit": limit}
        
        for idx, (key, value) in enumerate(node_props.items()):
            param_name = f"prop_{idx}"
            where_conditions.append(f"n.{key} = ${param_name}")
            params[param_name] = value
        
        where_clause = " AND ".join(where_conditions)
        
        # Build relationship pattern based on direction
        if direction == "outgoing":
            rel_pattern = "-[r]->"
        elif direction == "incoming":
            rel_pattern = "<-[r]-"
        else:  # both
            rel_pattern = "-[r]-"
        
        # Add relationship type filter if specified
        if relationship_types:
            rel_type_filter = ":" + "|".join(relationship_types)
        else:
            rel_type_filter = ""
        
        # Build path pattern based on depth
        path_pattern = f"(n){rel_pattern * depth}(m)"
        
        cypher_query = f"""
        MATCH (n:{node_type})
        WHERE {where_clause}
        WITH n
        LIMIT 1
        MATCH path = (n){rel_pattern}{rel_type_filter}(m)
        WHERE m <> n
        RETURN 
            id(n) as center_id,
            labels(n) as center_labels,
            properties(n) as center_properties,
            id(m) as related_id,
            labels(m) as related_labels,
            properties(m) as related_properties,
            type(r) as relationship_type,
            properties(r) as relationship_properties,
            startNode(r) = n as is_outgoing
        LIMIT $limit
        """
        
        # Execute query
        center_node_data = None
        related_nodes_data = []
        
        with create_session() as session:
            result = session.run(cypher_query, params)
            
            for record in result:
                # Store center node (same for all records)
                if center_node_data is None:
                    center_node_data = {
                        "id": str(record["center_id"]),
                        "labels": record["center_labels"],
                        "properties": dict(record["center_properties"])
                    }
                
                # Add related node
                related_node_entry = {
                    "node": {
                        "id": str(record["related_id"]),
                        "labels": record["related_labels"],
                        "properties": dict(record["related_properties"])
                    },
                    "relationship": {
                        "type": record["relationship_type"],
                        "direction": "outgoing" if record["is_outgoing"] else "incoming",
                        "properties": dict(record["relationship_properties"]) if record["relationship_properties"] else {}
                    }
                }
                related_nodes_data.append(related_node_entry)
        
        # Handle case where center node was not found
        if center_node_data is None:
            raise GraphQueryError(
                message=f"Center node not found: {node_type} with properties {node_props}",
                query=cypher_query
            )
        
        result_data = {
            "center_node": center_node_data,
            "related_nodes": related_nodes_data,
            "relationship_count": len(related_nodes_data)
        }
        
        logger.info(
            f"Found {len(related_nodes_data)} related nodes",
            operation="find_related_nodes",
            result_count=len(related_nodes_data)
        )
        
        return result_data
        
    except ValidationError as e:
        logger.error(f"Validation error in find_related_nodes: {e}", operation="find_related_nodes")
        raise ToolExecutionError(
            message=f"Invalid parameters: {e.message}",
            tool_name="find_related_nodes",
            details=e.details,
            original_error=e
        )
    except Neo4jError as e:
        logger.error(f"Neo4j error in find_related_nodes: {e}", operation="find_related_nodes")
        raise GraphQueryError(
            message="Failed to find related nodes",
            query=cypher_query if 'cypher_query' in locals() else None,
            original_error=e
        )
    except Exception as e:
        logger.error(f"Unexpected error in find_related_nodes: {e}", operation="find_related_nodes")
        raise ToolExecutionError(
            message="Find related nodes operation failed",
            tool_name="find_related_nodes",
            original_error=e
        )

