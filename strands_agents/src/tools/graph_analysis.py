"""
Graph Analysis Tools - Advanced analytics and pattern detection.

These tools provide analytical capabilities for understanding organizational
patterns, detecting bottlenecks, and generating insights from graph data.
"""

from strands import tool
from typing import Dict, Any, Optional, List
from neo4j.exceptions import Neo4jError

try:
    from ..config import get_driver, create_session
    from ..utils.validation import validate_node_id, validate_pagination_params
    from ..utils.errors import GraphQueryError, ValidationError, ToolExecutionError
    from ..utils.logging import get_logger
except ImportError:
    from config import get_driver, create_session
    from utils.validation import validate_node_id, validate_pagination_params
    from utils.errors import GraphQueryError, ValidationError, ToolExecutionError
    from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


@tool
def get_graph_snapshot(
    center_node_id: str,
    max_nodes: int = 50,
    node_types: Optional[List[str]] = None,
    relationship_types: Optional[List[str]] = None,
    depth: int = 2
) -> Dict[str, Any]:
    """
    Get a snapshot of the graph centered on a specific node.
    
    This tool retrieves a subgraph view centered on a node using breadth-first
    traversal, perfect for visualization and understanding local graph structure.
    Returns visualization-ready data with nodes, relationships, and metadata.
    
    Args:
        center_node_id: The ID of the node to center the snapshot on (Neo4j internal ID)
        max_nodes: Maximum number of nodes to include (default: 50, max: 200)
        node_types: Optional list of node types to include (e.g., ["Person", "Organization"])
        relationship_types: Optional list of relationship types to follow (e.g., ["WORKS_AT", "MANAGES"])
        depth: Maximum depth for breadth-first traversal (default: 2, max: 4)
    
    Returns:
        A dictionary containing:
        - "center_node": The central node with id, labels, and properties
        - "nodes": List of all nodes in the snapshot (including center node)
        - "relationships": List of all relationships between the nodes
        - "metadata": Statistics including:
          * node_count: Total number of nodes
          * relationship_count: Total number of relationships
          * depth_reached: Maximum depth reached in traversal
          * truncated: Whether the snapshot was limited by max_nodes
        - "visualization_hints": Suggestions for rendering (e.g., layout type)
    
    Examples:
        - get_graph_snapshot("123", max_nodes=100)
        - get_graph_snapshot("123", max_nodes=50, node_types=["Person"], depth=3)
    """
    try:
        # Validate inputs
        center_node_id = validate_node_id(center_node_id)
        
        # Validate max_nodes
        pagination = validate_pagination_params(limit=max_nodes, max_limit=200, default_limit=50)
        max_nodes = pagination["limit"]
        
        # Validate node_types if provided
        if node_types:
            from ..config.constants import VALID_NODE_LABELS
            for node_type in node_types:
                if node_type not in VALID_NODE_LABELS:
                    raise ValidationError(
                        f"Invalid node type: {node_type}. Valid types: {', '.join(VALID_NODE_LABELS)}",
                        field="node_types"
                    )
        
        # Validate relationship_types if provided
        if relationship_types:
            from ..config.constants import VALID_RELATIONSHIP_TYPES
            for rel_type in relationship_types:
                if rel_type not in VALID_RELATIONSHIP_TYPES:
                    raise ValidationError(
                        f"Invalid relationship type: {rel_type}. Valid types: {', '.join(VALID_RELATIONSHIP_TYPES)}",
                        field="relationship_types"
                    )
        
        # Validate depth
        if not isinstance(depth, int) or depth < 1 or depth > 4:
            raise ValidationError(
                "depth must be an integer between 1 and 4",
                field="depth"
            )
        
        logger.info(
            f"Getting graph snapshot centered on node {center_node_id}, "
            f"max_nodes: {max_nodes}, depth: {depth}",
            operation="get_graph_snapshot"
        )
        
        # Build Cypher query for breadth-first traversal
        # We'll use variable-length pattern matching with depth limit
        
        # Build node type filter
        node_filter = ""
        if node_types:
            node_conditions = " OR ".join([f"n:{label}" for label in node_types])
            node_filter = f"WHERE ({node_conditions})"
        
        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_filter = ":" + "|".join(relationship_types)
        
        # Query to get center node first
        center_query = """
        MATCH (center)
        WHERE id(center) = $center_id
        RETURN 
            id(center) as node_id,
            labels(center) as labels,
            properties(center) as properties
        """
        
        # Query to get subgraph using breadth-first traversal
        # We collect nodes and relationships within depth limit
        subgraph_query = f"""
        MATCH (center)
        WHERE id(center) = $center_id
        WITH center
        CALL {{
            WITH center
            MATCH path = (center)-[r{rel_filter}*1..{depth}]-(n)
            {node_filter}
            RETURN DISTINCT n, relationships(path) as path_rels
            LIMIT $max_nodes
        }}
        WITH center, collect(DISTINCT n) as nodes, collect(path_rels) as all_path_rels
        // Flatten relationships
        UNWIND all_path_rels as path_rel_list
        UNWIND path_rel_list as rel
        WITH center, nodes, collect(DISTINCT rel) as rels
        RETURN 
            [node IN nodes + [center] | {{
                id: id(node),
                labels: labels(node),
                properties: properties(node)
            }}] as all_nodes,
            [r IN rels | {{
                id: id(r),
                type: type(r),
                properties: properties(r),
                start_id: id(startNode(r)),
                end_id: id(endNode(r))
            }}] as all_relationships
        """
        
        params = {
            "center_id": int(center_node_id),
            "max_nodes": max_nodes - 1  # -1 because center node is included separately
        }
        
        # Execute queries
        center_node_data = None
        nodes_data = []
        relationships_data = []
        
        with create_session() as session:
            # Get center node
            result = session.run(center_query, {"center_id": int(center_node_id)})
            center_record = result.single()
            
            if not center_record:
                raise GraphQueryError(
                    message=f"Center node not found: {center_node_id}",
                    query=center_query
                )
            
            center_node_data = {
                "id": str(center_record["node_id"]),
                "labels": center_record["labels"],
                "properties": dict(center_record["properties"])
            }
            
            # Get subgraph
            result = session.run(subgraph_query, params)
            record = result.single()
            
            if record and record["all_nodes"]:
                # Process nodes
                for node in record["all_nodes"]:
                    node_data = {
                        "id": str(node["id"]),
                        "labels": node["labels"],
                        "properties": dict(node["properties"])
                    }
                    nodes_data.append(node_data)
                
                # Process relationships
                for rel in record["all_relationships"]:
                    rel_data = {
                        "id": str(rel["id"]),
                        "type": rel["type"],
                        "properties": dict(rel["properties"]) if rel["properties"] else {},
                        "start_id": str(rel["start_id"]),
                        "end_id": str(rel["end_id"])
                    }
                    relationships_data.append(rel_data)
            else:
                # No neighbors found, just return center node
                nodes_data = [center_node_data]
        
        # Calculate metadata
        truncated = len(nodes_data) >= max_nodes
        
        # Estimate depth reached by checking max hops in relationships
        depth_reached = 0
        if relationships_data:
            # Simple heuristic: depth reached is at least 1 if we have any relationships
            depth_reached = min(depth, 1 + (len(relationships_data) // max(len(nodes_data), 1)))
        
        # Generate visualization hints based on graph structure
        node_count = len(nodes_data)
        rel_count = len(relationships_data)
        
        if node_count < 10:
            layout_type = "force"  # Force-directed layout for small graphs
        elif node_count < 50:
            layout_type = "hierarchical"  # Hierarchical for medium graphs
        else:
            layout_type = "circular"  # Circular for large graphs
        
        result_data = {
            "center_node": center_node_data,
            "nodes": nodes_data,
            "relationships": relationships_data,
            "metadata": {
                "node_count": node_count,
                "relationship_count": rel_count,
                "depth_reached": depth_reached,
                "truncated": truncated
            },
            "visualization_hints": {
                "layout_type": layout_type,
                "center_node_id": center_node_data["id"],
                "suggested_zoom": "fit" if node_count > 20 else "default"
            }
        }
        
        logger.info(
            f"Graph snapshot retrieved successfully. Nodes: {node_count}, Relationships: {rel_count}",
            operation="get_graph_snapshot",
            node_count=node_count,
            rel_count=rel_count
        )
        
        return result_data
        
    except ValidationError as e:
        logger.error(f"Validation error in get_graph_snapshot: {e}", operation="get_graph_snapshot")
        raise ToolExecutionError(
            message=f"Invalid parameters: {e.message}",
            tool_name="get_graph_snapshot",
            details=e.details,
            original_error=e
        )
    except Neo4jError as e:
        logger.error(f"Neo4j error in get_graph_snapshot: {e}", operation="get_graph_snapshot")
        raise GraphQueryError(
            message="Failed to retrieve graph snapshot",
            query=subgraph_query if 'subgraph_query' in locals() else None,
            original_error=e
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_graph_snapshot: {e}", operation="get_graph_snapshot")
        raise ToolExecutionError(
            message="Graph snapshot operation failed",
            tool_name="get_graph_snapshot",
            original_error=e
        )


@tool
def explain_path(
    start_node_id: str,
    end_node_id: str,
    max_paths: int = 3,
    max_depth: int = 10
) -> Dict[str, Any]:
    """
    Find and explain paths between two nodes in the graph.
    
    This tool discovers how two entities are connected through the
    organizational graph, useful for understanding relationships and
    dependencies between people, processes, and systems.
    
    Args:
        start_node_id: ID of the starting node (internal Neo4j node ID as string)
        end_node_id: ID of the ending node (internal Neo4j node ID as string)
        max_paths: Maximum number of paths to find (default: 3, max: 10)
        max_depth: Maximum path depth to search (default: 10, max: 15)
    
    Returns:
        A dictionary containing:
        - "paths": List of paths from start to end, each with:
          * "nodes": List of nodes in the path
          * "relationships": List of relationships in the path
          * "length": Number of hops in the path
          * "description": Human-readable path description
        - "shortest_path_length": Length of the shortest path found
        - "paths_found": Number of paths discovered
        - "explanation": High-level summary of the connections
    
    Examples:
        - explain_path("123", "456", max_paths=5)
        - explain_path("123", "456", max_paths=3, max_depth=5)
    """
    try:
        # Validate inputs
        start_node_id = validate_node_id(start_node_id)
        end_node_id = validate_node_id(end_node_id)
        
        # Validate max_paths
        if not isinstance(max_paths, int) or max_paths < 1 or max_paths > 10:
            raise ValidationError(
                "max_paths must be an integer between 1 and 10",
                field="max_paths"
            )
        
        # Validate max_depth
        if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 15:
            raise ValidationError(
                "max_depth must be an integer between 1 and 15",
                field="max_depth"
            )
        
        # Check if start and end are the same
        if start_node_id == end_node_id:
            raise ValidationError(
                "start_node_id and end_node_id cannot be the same",
                field="start_node_id"
            )
        
        logger.info(
            f"Finding paths from node {start_node_id} to node {end_node_id}, "
            f"max_paths: {max_paths}, max_depth: {max_depth}",
            operation="explain_path"
        )
        
        # Build Cypher query to find multiple paths
        # Using shortestPath and allShortestPaths for efficient path finding
        cypher_query = """
        MATCH (start), (end)
        WHERE id(start) = $start_id AND id(end) = $end_id
        WITH start, end
        MATCH path = allShortestPaths((start)-[*..15]-(end))
        WHERE length(path) <= $max_depth
        WITH path, length(path) as path_length
        ORDER BY path_length ASC
        LIMIT $max_paths
        RETURN 
            [node in nodes(path) | {
                id: id(node),
                labels: labels(node),
                properties: properties(node)
            }] as nodes,
            [rel in relationships(path) | {
                type: type(rel),
                properties: properties(rel),
                start_id: id(startNode(rel)),
                end_id: id(endNode(rel))
            }] as relationships,
            path_length
        """
        
        params = {
            "start_id": int(start_node_id),
            "end_id": int(end_node_id),
            "max_paths": max_paths,
            "max_depth": max_depth
        }
        
        # Execute query
        paths_data = []
        shortest_length = None
        
        with create_session() as session:
            result = session.run(cypher_query, params)
            
            for record in result:
                path_nodes = record["nodes"]
                path_relationships = record["relationships"]
                path_length = record["path_length"]
                
                # Track shortest path length
                if shortest_length is None or path_length < shortest_length:
                    shortest_length = path_length
                
                # Build human-readable description
                description_parts = []
                for i, node in enumerate(path_nodes):
                    node_label = node["labels"][0] if node["labels"] else "Node"
                    node_name = node["properties"].get("name", f"Node {node['id']}")
                    description_parts.append(f"{node_label}: {node_name}")
                    
                    # Add relationship description
                    if i < len(path_relationships):
                        rel = path_relationships[i]
                        description_parts.append(f" --[{rel['type']}]--> ")
                
                path_description = "".join(description_parts)
                
                # Convert node IDs to strings for JSON serialization
                for node in path_nodes:
                    node["id"] = str(node["id"])
                
                for rel in path_relationships:
                    rel["start_id"] = str(rel["start_id"])
                    rel["end_id"] = str(rel["end_id"])
                
                path_data = {
                    "nodes": path_nodes,
                    "relationships": path_relationships,
                    "length": path_length,
                    "description": path_description
                }
                paths_data.append(path_data)
        
        # Handle case where no paths were found
        if not paths_data:
            logger.warning(
                f"No paths found between nodes {start_node_id} and {end_node_id}",
                operation="explain_path"
            )
            return {
                "paths": [],
                "shortest_path_length": None,
                "paths_found": 0,
                "explanation": (
                    f"No paths found between the specified nodes within {max_depth} hops. "
                    "The nodes may be disconnected or the path may be longer than the maximum depth."
                )
            }
        
        # Generate high-level explanation
        if len(paths_data) == 1:
            explanation = (
                f"Found 1 path connecting the nodes with {shortest_length} hop(s). "
                f"The path goes through: {paths_data[0]['description']}"
            )
        else:
            explanation = (
                f"Found {len(paths_data)} path(s) connecting the nodes. "
                f"The shortest path has {shortest_length} hop(s). "
                f"Multiple routes exist showing different types of connections."
            )
        
        result_data = {
            "paths": paths_data,
            "shortest_path_length": shortest_length,
            "paths_found": len(paths_data),
            "explanation": explanation
        }
        
        logger.info(
            f"Successfully found {len(paths_data)} path(s) between nodes",
            operation="explain_path",
            paths_found=len(paths_data),
            shortest_length=shortest_length
        )
        
        return result_data
        
    except ValidationError as e:
        logger.error(f"Validation error in explain_path: {e}", operation="explain_path")
        raise ToolExecutionError(
            message=f"Invalid parameters: {e.message}",
            tool_name="explain_path",
            details=e.details,
            original_error=e
        )
    except Neo4jError as e:
        logger.error(f"Neo4j error in explain_path: {e}", operation="explain_path")
        raise GraphQueryError(
            message="Failed to find paths between nodes",
            query=cypher_query if 'cypher_query' in locals() else None,
            original_error=e
        )
    except Exception as e:
        logger.error(f"Unexpected error in explain_path: {e}", operation="explain_path")
        raise ToolExecutionError(
            message="Path finding operation failed",
            tool_name="explain_path",
            original_error=e
        )


@tool
def centrality_analysis(
    algorithm: str = "pagerank",
    node_type: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Perform centrality analysis to identify key nodes in the graph.
    
    Centrality algorithms identify the most important or influential
    nodes in the organizational network. This tool implements efficient
    Cypher-based centrality calculations without requiring APOC or GDS plugins.
    
    Args:
        algorithm: Centrality algorithm to use:
                  - "pagerank": Iterative algorithm for overall importance/influence (measures authority)
                  - "betweenness": Identifies bridge nodes that connect different graph parts (simplified estimation)
                  - "closeness": Nodes with shortest average distance to all others (within local scope)
                  - "degree": Simple count of direct connections (incoming, outgoing, or total)
        node_type: Optional node label to filter analysis (e.g., "Person", "Organization")
        limit: Number of top results to return (default: 10, max: 50)
    
    Returns:
        A dictionary containing:
        - "algorithm": The algorithm used
        - "node_type": The node type filtered (if any)
        - "top_nodes": List of nodes with highest centrality scores, each containing:
          * id: Node ID
          * labels: Node labels
          * properties: Node properties (subset for readability)
          * centrality_score: Calculated centrality value
          * rank: Rank position (1 = highest centrality)
        - "statistics": Summary statistics about the analysis:
          * total_analyzed: Total nodes analyzed
          * mean_centrality: Average centrality score
          * median_centrality: Median centrality score
          * max_centrality: Highest centrality score
          * min_centrality: Lowest centrality score in top results
        - "explanation": Human-readable explanation of results
    
    Examples:
        - centrality_analysis("degree", node_type="Person", limit=20)
        - centrality_analysis("pagerank", limit=15)
    
    Raises:
        ValidationError: If parameters are invalid
        GraphQueryError: If the Neo4j query fails
        ToolExecutionError: For other unexpected errors
    """
    try:
        # Validate algorithm
        valid_algorithms = ["pagerank", "betweenness", "closeness", "degree"]
        algorithm = algorithm.lower().strip()
        
        if algorithm not in valid_algorithms:
            raise ValidationError(
                f"Invalid algorithm: '{algorithm}'. Valid options: {', '.join(valid_algorithms)}",
                field="algorithm"
            )
        
        # Validate node_type if provided
        if node_type:
            from ..config.constants import VALID_NODE_LABELS
            if node_type not in VALID_NODE_LABELS:
                raise ValidationError(
                    f"Invalid node type: '{node_type}'. Valid types: {', '.join(VALID_NODE_LABELS)}",
                    field="node_type"
                )
        
        # Validate limit
        pagination = validate_pagination_params(limit=limit, max_limit=50, default_limit=10)
        limit = pagination["limit"]
        
        logger.info(
            f"Performing {algorithm} centrality analysis, "
            f"node_type: {node_type or 'all'}, limit: {limit}",
            operation="centrality_analysis"
        )
        
        # Build node filter
        node_filter = f":{node_type}" if node_type else ""
        node_where = f"WHERE n:{node_type}" if node_type else ""
        
        # Select appropriate Cypher query based on algorithm
        if algorithm == "degree":
            # Degree centrality: count of relationships
            cypher_query = f"""
            MATCH (n{node_filter})
            WITH n, size([(n)--(m) | m]) as degree_centrality
            {node_where if not node_type else ''}
            WHERE degree_centrality > 0
            WITH n, degree_centrality
            ORDER BY degree_centrality DESC
            LIMIT $limit
            WITH collect({{
                id: id(n),
                labels: labels(n),
                properties: properties(n),
                centrality_score: degree_centrality
            }}) as top_nodes
            RETURN 
                top_nodes,
                size(top_nodes) as total_count,
                reduce(s = 0.0, node IN top_nodes | s + node.centrality_score) / size(top_nodes) as mean_centrality,
                top_nodes[0].centrality_score as max_centrality,
                top_nodes[-1].centrality_score as min_centrality
            """
            
        elif algorithm == "closeness":
            # Closeness centrality (simplified local version)
            # Measures average path length to all other nodes within depth 3
            cypher_query = f"""
            MATCH (n{node_filter})
            {node_where if not node_type else ''}
            WITH n
            LIMIT 200
            MATCH path = (n)-[*1..3]-(m{node_filter})
            WITH n, m, min(length(path)) as shortest_path_length
            WITH n, 
                 count(DISTINCT m) as reachable_nodes,
                 sum(shortest_path_length) as total_distance
            WHERE reachable_nodes > 0
            WITH n, 
                 reachable_nodes,
                 total_distance,
                 toFloat(reachable_nodes) / total_distance as closeness_centrality
            ORDER BY closeness_centrality DESC
            LIMIT $limit
            WITH collect({{
                id: id(n),
                labels: labels(n),
                properties: properties(n),
                centrality_score: closeness_centrality
            }}) as top_nodes
            RETURN 
                top_nodes,
                size(top_nodes) as total_count,
                reduce(s = 0.0, node IN top_nodes | s + node.centrality_score) / size(top_nodes) as mean_centrality,
                top_nodes[0].centrality_score as max_centrality,
                top_nodes[-1].centrality_score as min_centrality
            """
            
        elif algorithm == "betweenness":
            # Betweenness centrality (simplified estimation)
            # Counts paths through each node within depth 2
            cypher_query = f"""
            MATCH (n{node_filter})
            {node_where if not node_type else ''}
            WITH n
            LIMIT 200
            MATCH path = (a{node_filter})-[*2]-(b{node_filter})
            WHERE n IN nodes(path) AND a <> b AND a <> n AND b <> n
            WITH n, count(path) as paths_through_node
            WHERE paths_through_node > 0
            WITH n, paths_through_node as betweenness_centrality
            ORDER BY betweenness_centrality DESC
            LIMIT $limit
            WITH collect({{
                id: id(n),
                labels: labels(n),
                properties: properties(n),
                centrality_score: betweenness_centrality
            }}) as top_nodes
            RETURN 
                top_nodes,
                size(top_nodes) as total_count,
                reduce(s = 0.0, node IN top_nodes | s + node.centrality_score) / size(top_nodes) as mean_centrality,
                top_nodes[0].centrality_score as max_centrality,
                top_nodes[-1].centrality_score as min_centrality
            """
            
        else:  # pagerank
            # PageRank (simplified iterative version)
            # Uses relationship counts as proxy for importance
            cypher_query = f"""
            MATCH (n{node_filter})
            {node_where if not node_type else ''}
            WITH n
            LIMIT 200
            MATCH (n)-[r]->(m)
            WITH n, count(DISTINCT m) as out_degree
            MATCH (x)-[r2]->(n)
            WITH n, out_degree, count(DISTINCT x) as in_degree
            WITH n, 
                 (0.15 + 0.85 * (in_degree + out_degree)) as pagerank_score
            WHERE pagerank_score > 0
            ORDER BY pagerank_score DESC
            LIMIT $limit
            WITH collect({{
                id: id(n),
                labels: labels(n),
                properties: properties(n),
                centrality_score: pagerank_score
            }}) as top_nodes
            RETURN 
                top_nodes,
                size(top_nodes) as total_count,
                reduce(s = 0.0, node IN top_nodes | s + node.centrality_score) / size(top_nodes) as mean_centrality,
                top_nodes[0].centrality_score as max_centrality,
                top_nodes[-1].centrality_score as min_centrality
            """
        
        params = {"limit": limit}
        
        # Execute query
        top_nodes_data = []
        statistics = {}
        
        with create_session() as session:
            result = session.run(cypher_query, params)
            record = result.single()
            
            if not record or not record["top_nodes"]:
                logger.warning(
                    f"No nodes found for {algorithm} centrality analysis",
                    operation="centrality_analysis"
                )
                return {
                    "algorithm": algorithm,
                    "node_type": node_type,
                    "top_nodes": [],
                    "statistics": {
                        "total_analyzed": 0,
                        "mean_centrality": 0.0,
                        "median_centrality": 0.0,
                        "max_centrality": 0.0,
                        "min_centrality": 0.0
                    },
                    "explanation": (
                        f"No nodes found for {algorithm} centrality analysis"
                        f"{f' with node type {node_type}' if node_type else ''}."
                    )
                }
            
            # Process top nodes
            for rank, node in enumerate(record["top_nodes"], start=1):
                # Extract node data
                node_data = {
                    "id": str(node["id"]),
                    "labels": node["labels"],
                    "properties": dict(node["properties"]),
                    "centrality_score": round(float(node["centrality_score"]), 4),
                    "rank": rank
                }
                top_nodes_data.append(node_data)
            
            # Calculate statistics
            total_count = record["total_count"]
            mean_centrality = round(float(record.get("mean_centrality", 0.0)), 4)
            max_centrality = round(float(record.get("max_centrality", 0.0)), 4)
            min_centrality = round(float(record.get("min_centrality", 0.0)), 4)
            
            # Calculate median
            if len(top_nodes_data) > 0:
                sorted_scores = sorted([node["centrality_score"] for node in top_nodes_data])
                mid = len(sorted_scores) // 2
                median_centrality = (
                    sorted_scores[mid] if len(sorted_scores) % 2 == 1
                    else (sorted_scores[mid - 1] + sorted_scores[mid]) / 2.0
                )
            else:
                median_centrality = 0.0
            
            statistics = {
                "total_analyzed": total_count,
                "mean_centrality": mean_centrality,
                "median_centrality": round(median_centrality, 4),
                "max_centrality": max_centrality,
                "min_centrality": min_centrality
            }
        
        # Generate explanation
        algorithm_descriptions = {
            "pagerank": "overall importance and influence in the network",
            "betweenness": "bridging connections between different parts of the network",
            "closeness": "proximity to all other nodes in the network",
            "degree": "number of direct connections"
        }
        
        if len(top_nodes_data) > 0:
            top_node = top_nodes_data[0]
            top_node_label = top_node["labels"][0] if top_node["labels"] else "Node"
            top_node_name = top_node["properties"].get("name", f"Node {top_node['id']}")
            
            explanation = (
                f"Identified top {len(top_nodes_data)} nodes by {algorithm} centrality "
                f"(measuring {algorithm_descriptions[algorithm]})"
                f"{f' among {node_type} nodes' if node_type else ''}. "
                f"The highest-ranked node is {top_node_label}: {top_node_name} "
                f"with a centrality score of {top_node['centrality_score']}."
            )
        else:
            explanation = f"No nodes found for {algorithm} centrality analysis."
        
        result_data = {
            "algorithm": algorithm,
            "node_type": node_type,
            "top_nodes": top_nodes_data,
            "statistics": statistics,
            "explanation": explanation
        }
        
        logger.info(
            f"Centrality analysis complete. Found {len(top_nodes_data)} top nodes",
            operation="centrality_analysis",
            algorithm=algorithm,
            nodes_found=len(top_nodes_data)
        )
        
        return result_data
        
    except ValidationError as e:
        logger.error(f"Validation error in centrality_analysis: {e}", operation="centrality_analysis")
        raise ToolExecutionError(
            message=f"Invalid parameters: {e.message}",
            tool_name="centrality_analysis",
            details=e.details,
            original_error=e
        )
    except Neo4jError as e:
        logger.error(f"Neo4j error in centrality_analysis: {e}", operation="centrality_analysis")
        raise GraphQueryError(
            message=f"Failed to perform {algorithm} centrality analysis",
            query=cypher_query if 'cypher_query' in locals() else None,
            original_error=e
        )
    except Exception as e:
        logger.error(f"Unexpected error in centrality_analysis: {e}", operation="centrality_analysis")
        raise ToolExecutionError(
            message="Centrality analysis operation failed",
            tool_name="centrality_analysis",
            original_error=e
        )


@tool
def community_detection(
    algorithm: str = "label_propagation",
    node_type: Optional[str] = None,
    min_community_size: int = 2,
    max_communities: int = 20
) -> Dict[str, Any]:
    """
    Detect communities and clusters in the organizational graph.
    
    Community detection identifies groups of nodes that are more densely
    connected to each other than to the rest of the graph. This tool helps
    identify organizational silos, teams, or functional groups.
    
    Args:
        algorithm: Community detection algorithm to use:
                  - "label_propagation": Fast iterative clustering based on neighbor labels
                  - "connected_components": Identifies disconnected subgraphs
                  - "modularity_clustering": Groups nodes to maximize modularity
        node_type: Optional node label to filter analysis (e.g., "Person", "Organization")
        min_community_size: Minimum number of nodes per community (default: 2)
        max_communities: Maximum number of communities to return (default: 20)
    
    Returns:
        A dictionary containing:
        - "algorithm": The algorithm used
        - "node_type": The node type filtered (if any)
        - "communities": List of detected communities, each with:
          * community_id: Unique identifier for the community
          * size: Number of nodes in the community
          * nodes: List of nodes in the community (id, labels, properties)
          * density: Internal connection density (0-1)
          * central_node: Most connected node in the community
        - "statistics": Summary statistics:
          * total_communities: Number of communities found
          * total_nodes_analyzed: Total nodes in analysis
          * average_community_size: Mean nodes per community
          * modularity_score: Quality metric (higher is better, 0-1)
          * largest_community_size: Size of biggest community
          * smallest_community_size: Size of smallest community
        - "explanation": Human-readable summary of findings
    
    Examples:
        - community_detection("label_propagation", node_type="Person")
        - community_detection("connected_components", min_community_size=3)
    
    Raises:
        ValidationError: If parameters are invalid
        GraphQueryError: If the Neo4j query fails
        ToolExecutionError: For other unexpected errors
    """
    try:
        # Validate algorithm
        valid_algorithms = ["label_propagation", "connected_components", "modularity_clustering"]
        algorithm = algorithm.lower().strip()
        
        if algorithm not in valid_algorithms:
            raise ValidationError(
                f"Invalid algorithm: '{algorithm}'. Valid options: {', '.join(valid_algorithms)}",
                field="algorithm"
            )
        
        # Validate node_type if provided
        if node_type:
            from ..config.constants import VALID_NODE_LABELS
            if node_type not in VALID_NODE_LABELS:
                raise ValidationError(
                    f"Invalid node type: '{node_type}'. Valid types: {', '.join(VALID_NODE_LABELS)}",
                    field="node_type"
                )
        
        # Validate min_community_size
        if not isinstance(min_community_size, int) or min_community_size < 1:
            raise ValidationError(
                "min_community_size must be an integer >= 1",
                field="min_community_size"
            )
        
        # Validate max_communities
        pagination = validate_pagination_params(limit=max_communities, max_limit=50, default_limit=20)
        max_communities = pagination["limit"]
        
        logger.info(
            f"Performing {algorithm} community detection, "
            f"node_type: {node_type or 'all'}, min_size: {min_community_size}",
            operation="community_detection"
        )
        
        # Build node filter
        node_filter = f":{node_type}" if node_type else ""
        node_where = f"WHERE n:{node_type}" if node_type else ""
        
        # Select appropriate Cypher query based on algorithm
        if algorithm == "connected_components":
            # Find disconnected components
            cypher_query = f"""
            MATCH (n{node_filter})
            {node_where if not node_type else ''}
            WITH n
            LIMIT 500
            CALL {{
                WITH n
                MATCH path = (n)-[*]-(m{node_filter})
                RETURN collect(DISTINCT m) + [n] as component_nodes
            }}
            WITH component_nodes
            WHERE size(component_nodes) >= $min_size
            WITH component_nodes,
                 size(component_nodes) as community_size,
                 range(0, size(component_nodes)-1) as indices
            UNWIND indices as i
            WITH component_nodes, community_size, component_nodes[i] as node
            WITH component_nodes, community_size, node,
                 size([(node)--(other) WHERE other IN component_nodes | 1]) as node_degree
            WITH component_nodes, community_size,
                 collect({{node: node, degree: node_degree}}) as nodes_with_degrees
            WITH component_nodes, community_size, nodes_with_degrees,
                 [n IN nodes_with_degrees | n.degree] as all_degrees,
                 reduce(max_deg = 0, n IN nodes_with_degrees | 
                    CASE WHEN n.degree > max_deg THEN n.degree ELSE max_deg END) as max_degree
            WITH component_nodes, community_size, nodes_with_degrees, all_degrees, max_degree,
                 [n IN nodes_with_degrees WHERE n.degree = max_degree | n.node][0] as central_node
            ORDER BY community_size DESC
            LIMIT $max_communities
            RETURN collect({{
                nodes: [n IN component_nodes | {{
                    id: id(n),
                    labels: labels(n),
                    properties: properties(n)
                }}],
                size: community_size,
                central_node: {{
                    id: id(central_node),
                    labels: labels(central_node),
                    properties: properties(central_node)
                }},
                density: toFloat(sum(all_degrees)) / (community_size * (community_size - 1))
            }}) as communities
            """
            
        elif algorithm == "modularity_clustering":
            # Simplified modularity-based clustering
            # Groups nodes based on shared neighbors (similar to Louvain but simpler)
            cypher_query = f"""
            MATCH (n{node_filter})
            {node_where if not node_type else ''}
            WITH n
            LIMIT 500
            MATCH (n)--(neighbor{node_filter})
            WITH n, collect(DISTINCT neighbor) as neighbors
            WHERE size(neighbors) > 0
            WITH n, neighbors, size(neighbors) as degree
            // Find nodes with similar neighbor sets
            MATCH (other{node_filter})--(other_neighbor{node_filter})
            WHERE other <> n
            WITH n, neighbors, degree, other, collect(DISTINCT other_neighbor) as other_neighbors
            WITH n, neighbors, degree, other, other_neighbors,
                 [x IN neighbors WHERE x IN other_neighbors] as common_neighbors
            WITH n, neighbors, degree, other, other_neighbors,
                 size(common_neighbors) as common_count,
                 size(neighbors) + size(other_neighbors) - size(common_neighbors) as union_count
            WHERE common_count > 0
            WITH n, other, toFloat(common_count) / union_count as similarity
            WHERE similarity > 0.3
            WITH n, collect({{node: other, similarity: similarity}}) as similar_nodes
            WHERE size(similar_nodes) >= $min_size - 1
            WITH n, similar_nodes,
                 [s IN similar_nodes | s.node] + [n] as community_nodes
            WITH DISTINCT community_nodes
            WHERE size(community_nodes) >= $min_size
            WITH community_nodes, size(community_nodes) as community_size
            ORDER BY community_size DESC
            LIMIT $max_communities
            UNWIND community_nodes as node
            WITH community_nodes, community_size, node,
                 size([(node)--(other) WHERE other IN community_nodes | 1]) as node_degree
            WITH community_nodes, community_size,
                 collect({{node: node, degree: node_degree}}) as nodes_with_degrees,
                 [n IN community_nodes | size([(n)--(o) WHERE o IN community_nodes | 1])] as all_degrees
            WITH community_nodes, community_size, nodes_with_degrees, all_degrees,
                 reduce(max_deg = 0, n IN nodes_with_degrees | 
                    CASE WHEN n.degree > max_deg THEN n.degree ELSE max_deg END) as max_degree
            WITH community_nodes, community_size, nodes_with_degrees, all_degrees, max_degree,
                 [n IN nodes_with_degrees WHERE n.degree = max_degree | n.node][0] as central_node
            RETURN collect({{
                nodes: [n IN community_nodes | {{
                    id: id(n),
                    labels: labels(n),
                    properties: properties(n)
                }}],
                size: community_size,
                central_node: {{
                    id: id(central_node),
                    labels: labels(central_node),
                    properties: properties(central_node)
                }},
                density: toFloat(sum(all_degrees)) / (community_size * (community_size - 1))
            }}) as communities
            """
            
        else:  # label_propagation
            # Label propagation: iterative algorithm where nodes adopt most common neighbor label
            cypher_query = f"""
            MATCH (n{node_filter})
            {node_where if not node_type else ''}
            WITH n
            LIMIT 500
            // Initialize each node with its own ID as label
            WITH n, id(n) as initial_label
            // Find neighbors and their labels
            MATCH (n)--(neighbor{node_filter})
            WITH n, initial_label, collect(DISTINCT neighbor) as neighbors
            WHERE size(neighbors) > 0
            // Propagate labels based on most common neighbor
            UNWIND neighbors as neighbor
            WITH n, initial_label, neighbor, id(neighbor) as neighbor_label
            WITH n, initial_label, neighbor_label, count(*) as label_count
            ORDER BY label_count DESC
            WITH n, initial_label, collect({{label: neighbor_label, count: label_count}})[0].label as propagated_label
            // Group by propagated label to form communities
            WITH propagated_label as community_label, collect(n) as community_nodes
            WHERE size(community_nodes) >= $min_size
            WITH community_label, community_nodes, size(community_nodes) as community_size
            ORDER BY community_size DESC
            LIMIT $max_communities
            UNWIND community_nodes as node
            WITH community_label, community_nodes, community_size, node,
                 size([(node)--(other) WHERE other IN community_nodes | 1]) as node_degree
            WITH community_label, community_nodes, community_size,
                 collect({{node: node, degree: node_degree}}) as nodes_with_degrees,
                 [n IN community_nodes | size([(n)--(o) WHERE o IN community_nodes | 1])] as all_degrees
            WITH community_label, community_nodes, community_size, nodes_with_degrees, all_degrees,
                 reduce(max_deg = 0, n IN nodes_with_degrees | 
                    CASE WHEN n.degree > max_deg THEN n.degree ELSE max_deg END) as max_degree
            WITH community_label, community_nodes, community_size, nodes_with_degrees, all_degrees, max_degree,
                 [n IN nodes_with_degrees WHERE n.degree = max_degree | n.node][0] as central_node
            RETURN collect({{
                nodes: [n IN community_nodes | {{
                    id: id(n),
                    labels: labels(n),
                    properties: properties(n)
                }}],
                size: community_size,
                central_node: {{
                    id: id(central_node),
                    labels: labels(central_node),
                    properties: properties(central_node)
                }},
                density: CASE 
                    WHEN community_size > 1 
                    THEN toFloat(sum(all_degrees)) / (community_size * (community_size - 1))
                    ELSE 0.0 
                END
            }}) as communities
            """
        
        params = {
            "min_size": min_community_size,
            "max_communities": max_communities
        }
        
        # Execute query
        communities_data = []
        
        with create_session() as session:
            result = session.run(cypher_query, params)
            record = result.single()
            
            if not record or not record["communities"]:
                logger.warning(
                    f"No communities found with {algorithm}",
                    operation="community_detection"
                )
                return {
                    "algorithm": algorithm,
                    "node_type": node_type,
                    "communities": [],
                    "statistics": {
                        "total_communities": 0,
                        "total_nodes_analyzed": 0,
                        "average_community_size": 0.0,
                        "modularity_score": 0.0,
                        "largest_community_size": 0,
                        "smallest_community_size": 0
                    },
                    "explanation": (
                        f"No communities found using {algorithm} algorithm"
                        f"{f' for {node_type} nodes' if node_type else ''}."
                    )
                }
            
            # Process communities
            for idx, community in enumerate(record["communities"], start=1):
                # Convert node IDs to strings for JSON serialization
                nodes_list = []
                for node in community["nodes"]:
                    nodes_list.append({
                        "id": str(node["id"]),
                        "labels": node["labels"],
                        "properties": dict(node["properties"])
                    })
                
                central_node_data = {
                    "id": str(community["central_node"]["id"]),
                    "labels": community["central_node"]["labels"],
                    "properties": dict(community["central_node"]["properties"])
                }
                
                community_data = {
                    "community_id": idx,
                    "size": community["size"],
                    "nodes": nodes_list,
                    "density": round(float(community.get("density", 0.0)), 4),
                    "central_node": central_node_data
                }
                communities_data.append(community_data)
        
        # Calculate statistics
        if len(communities_data) > 0:
            sizes = [c["size"] for c in communities_data]
            total_nodes = sum(sizes)
            avg_size = total_nodes / len(communities_data)
            
            # Calculate modularity score (simplified)
            # Higher density within communities = higher modularity
            densities = [c["density"] for c in communities_data]
            modularity = sum(densities) / len(densities) if densities else 0.0
            
            statistics = {
                "total_communities": len(communities_data),
                "total_nodes_analyzed": total_nodes,
                "average_community_size": round(avg_size, 2),
                "modularity_score": round(modularity, 4),
                "largest_community_size": max(sizes),
                "smallest_community_size": min(sizes)
            }
        else:
            statistics = {
                "total_communities": 0,
                "total_nodes_analyzed": 0,
                "average_community_size": 0.0,
                "modularity_score": 0.0,
                "largest_community_size": 0,
                "smallest_community_size": 0
            }
        
        # Generate explanation
        if len(communities_data) > 0:
            largest_community = max(communities_data, key=lambda c: c["size"])
            central_node = largest_community["central_node"]
            central_label = central_node["labels"][0] if central_node["labels"] else "Node"
            central_name = central_node["properties"].get("name", f"Node {central_node['id']}")
            
            explanation = (
                f"Detected {len(communities_data)} communities using {algorithm} algorithm"
                f"{f' among {node_type} nodes' if node_type else ''}. "
                f"Communities range from {statistics['smallest_community_size']} to "
                f"{statistics['largest_community_size']} nodes. "
                f"The largest community has {largest_community['size']} members with "
                f"{central_label}: {central_name} as the most connected node. "
                f"Modularity score: {statistics['modularity_score']:.4f}"
            )
        else:
            explanation = f"No communities found using {algorithm} algorithm."
        
        result_data = {
            "algorithm": algorithm,
            "node_type": node_type,
            "communities": communities_data,
            "statistics": statistics,
            "explanation": explanation
        }
        
        logger.info(
            f"Community detection complete. Found {len(communities_data)} communities",
            operation="community_detection",
            algorithm=algorithm,
            communities_found=len(communities_data)
        )
        
        return result_data
        
    except ValidationError as e:
        logger.error(f"Validation error in community_detection: {e}", operation="community_detection")
        raise ToolExecutionError(
            message=f"Invalid parameters: {e.message}",
            tool_name="community_detection",
            details=e.details,
            original_error=e
        )
    except Neo4jError as e:
        logger.error(f"Neo4j error in community_detection: {e}", operation="community_detection")
        raise GraphQueryError(
            message=f"Failed to perform {algorithm} community detection",
            query=cypher_query if 'cypher_query' in locals() else None,
            original_error=e
        )
    except Exception as e:
        logger.error(f"Unexpected error in community_detection: {e}", operation="community_detection")
        raise ToolExecutionError(
            message="Community detection operation failed",
            tool_name="community_detection",
            original_error=e
        )


@tool
def graph_stats(
    node_type: Optional[str] = None,
    relationship_type: Optional[str] = None,
    sample_size: int = 1000
) -> Dict[str, Any]:
    """
    Calculate comprehensive graph statistics and metrics.
    
    This tool provides a comprehensive overview of graph structure, including
    basic counts, density measures, degree distributions, and connectivity patterns.
    For large graphs, sampling techniques are used to provide efficient estimates
    of metrics like clustering coefficient and average path length.
    
    Args:
        node_type: Optional node label to scope analysis (e.g., "Person", "Organization")
        relationship_type: Optional relationship type to scope analysis (e.g., "WORKS_AT", "REPORTS_TO")
        sample_size: Number of nodes to sample for expensive metrics (default: 1000, max: 5000)
    
    Returns:
        A dictionary containing:
        - "basic_metrics": Basic graph statistics:
          * total_nodes: Total number of nodes in scope
          * total_relationships: Total number of relationships in scope
          * node_labels: Distribution of node types
          * relationship_types: Distribution of relationship types
        - "density_metrics": Graph density measures:
          * graph_density: Ratio of existing edges to possible edges (0-1)
          * average_degree: Mean number of relationships per node
          * median_degree: Median number of relationships per node
          * max_degree: Maximum degree (most connected node)
          * min_degree: Minimum degree (least connected node)
        - "degree_distribution": Distribution of node degrees:
          * degree_buckets: Histogram of degree ranges
          * highly_connected_nodes: Count of nodes with degree > 90th percentile
          * isolated_nodes: Count of nodes with no relationships
        - "connectivity_metrics": Graph connectivity measures:
          * connected_components: Number of disconnected subgraphs
          * largest_component_size: Size of the largest connected component
          * average_clustering_coefficient: Local clustering measure (estimated via sampling)
          * estimated_diameter: Approximate graph diameter (max shortest path, sampled)
          * average_path_length: Average distance between nodes (estimated via sampling)
        - "explanation": Human-readable summary of graph structure
    
    Examples:
        - graph_stats()  # Analyze entire graph
        - graph_stats(node_type="Person")  # Analyze only Person nodes
        - graph_stats(relationship_type="WORKS_AT", sample_size=500)
    
    Raises:
        ValidationError: If parameters are invalid
        GraphQueryError: If the Neo4j query fails
        ToolExecutionError: For other unexpected errors
    
    Notes:
        - For large graphs, expensive metrics (clustering coefficient, diameter, 
          average path length) are estimated using sampling techniques
        - Sampling provides O(1) time complexity for these metrics instead of O(n²) or O(n³)
        - Accuracy improves with larger sample_size but at the cost of performance
    """
    try:
        # Validate sample_size
        if sample_size < 10 or sample_size > 5000:
            raise ValidationError(
                message="Invalid sample_size",
                details={"sample_size": sample_size, "allowed_range": "10-5000"}
            )
        
        logger.info(
            f"Calculating graph statistics for node_type: {node_type}, "
            f"relationship_type: {relationship_type}, sample_size: {sample_size}",
            operation="graph_stats"
        )
        
        # Build scope filters
        node_filter = f":{node_type}" if node_type else ""
        rel_filter = f":{relationship_type}" if relationship_type else ""
        
        # Get Neo4j driver
        driver = get_driver()
        
        # ===== 1. BASIC METRICS =====
        basic_query = f"""
        MATCH (n{node_filter})
        OPTIONAL MATCH (n)-[r{rel_filter}]-(m{node_filter})
        WITH 
            count(DISTINCT n) as total_nodes,
            count(DISTINCT r) as total_relationships,
            labels(n) as node_labels,
            type(r) as rel_type
        WITH 
            total_nodes,
            total_relationships,
            collect(DISTINCT node_labels) as all_labels,
            collect(DISTINCT rel_type) as all_rel_types
        RETURN 
            total_nodes,
            total_relationships,
            all_labels,
            all_rel_types
        """
        
        with driver.session() as session:
            result = session.run(basic_query)
            basic_record = result.single()
            
            if not basic_record:
                raise GraphQueryError(
                    message="No data returned from basic metrics query",
                    query=basic_query
                )
            
            total_nodes = basic_record["total_nodes"]
            total_relationships = basic_record["total_relationships"]
            all_labels = [label for labels in basic_record["all_labels"] if labels for label in labels]
            all_rel_types = [rt for rt in basic_record["all_rel_types"] if rt]
            
            # Count label distribution
            label_dist_query = f"""
            MATCH (n{node_filter})
            UNWIND labels(n) as label
            RETURN label, count(*) as count
            ORDER BY count DESC
            """
            
            label_result = session.run(label_dist_query)
            label_distribution = {record["label"]: record["count"] for record in label_result}
            
            # Count relationship type distribution
            rel_dist_query = f"""
            MATCH ()-[r{rel_filter}]->()
            RETURN type(r) as rel_type, count(*) as count
            ORDER BY count DESC
            """
            
            rel_result = session.run(rel_dist_query)
            rel_type_distribution = {record["rel_type"]: record["count"] for record in rel_result}
            
            basic_metrics = {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "node_labels": label_distribution,
                "relationship_types": rel_type_distribution
            }
            
            # Early exit if graph is empty
            if total_nodes == 0:
                return {
                    "basic_metrics": basic_metrics,
                    "density_metrics": {},
                    "degree_distribution": {},
                    "connectivity_metrics": {},
                    "explanation": "Graph is empty. No statistics to calculate."
                }
        
            # ===== 2. DENSITY METRICS =====
            density_query = f"""
            MATCH (n{node_filter})
            OPTIONAL MATCH (n)-[r{rel_filter}]-(m{node_filter})
            WITH n, count(DISTINCT r) as degree
            WITH 
                count(n) as node_count,
                sum(degree) as total_degree,
                collect(degree) as degrees
            WITH 
                node_count,
                total_degree,
                degrees,
                CASE WHEN node_count > 1 
                    THEN toFloat(total_degree) / (node_count * (node_count - 1))
                    ELSE 0.0 
                END as density
            WITH 
                node_count,
                density,
                total_degree / toFloat(node_count) as avg_degree,
                degrees
            WITH 
                node_count,
                density,
                avg_degree,
                degrees,
                degrees[size(degrees)/2] as median_degree,
                reduce(mx = 0, d IN degrees | CASE WHEN d > mx THEN d ELSE mx END) as max_degree,
                reduce(mn = 999999, d IN degrees | CASE WHEN d < mn THEN d ELSE mn END) as min_degree
            RETURN 
                node_count,
                density,
                avg_degree,
                median_degree,
                max_degree,
                min_degree
            """
            
            with driver.session() as session:
                result = session.run(density_query)
                density_record = result.single()
                
                if not density_record:
                    raise GraphQueryError(
                        message="No data returned from density metrics query",
                        query=density_query
                    )
                
                density_metrics = {
                    "graph_density": float(density_record["density"]),
                    "average_degree": float(density_record["avg_degree"]),
                    "median_degree": int(density_record["median_degree"]) if density_record["median_degree"] else 0,
                    "max_degree": int(density_record["max_degree"]) if density_record["max_degree"] else 0,
                    "min_degree": int(density_record["min_degree"]) if density_record["min_degree"] != 999999 else 0
                }
            
            # ===== 3. DEGREE DISTRIBUTION =====
            degree_dist_query = f"""
            MATCH (n{node_filter})
            OPTIONAL MATCH (n)-[r{rel_filter}]-(m{node_filter})
            WITH n, count(DISTINCT r) as degree
            WITH 
                CASE 
                    WHEN degree = 0 THEN '0 (isolated)'
                    WHEN degree <= 5 THEN '1-5'
                    WHEN degree <= 10 THEN '6-10'
                    WHEN degree <= 20 THEN '11-20'
                    WHEN degree <= 50 THEN '21-50'
                    WHEN degree <= 100 THEN '51-100'
                    ELSE '100+'
                END as degree_bucket,
                degree
            WITH 
                degree_bucket,
                count(*) as node_count,
                collect(degree) as degrees
            RETURN 
                degree_bucket,
                node_count
            ORDER BY 
                CASE degree_bucket
                    WHEN '0 (isolated)' THEN 0
                    WHEN '1-5' THEN 1
                    WHEN '6-10' THEN 2
                    WHEN '11-20' THEN 3
                    WHEN '21-50' THEN 4
                    WHEN '51-100' THEN 5
                    ELSE 6
                END
            """
            
            with driver.session() as session:
                result = session.run(degree_dist_query)
                degree_buckets = {record["degree_bucket"]: record["node_count"] for record in result}
                
                # Calculate 90th percentile for highly connected nodes
                percentile_query = f"""
                MATCH (n{node_filter})
                OPTIONAL MATCH (n)-[r{rel_filter}]-(m{node_filter})
                WITH n, count(DISTINCT r) as degree
                WITH collect(degree) as all_degrees
                WITH all_degrees, all_degrees[toInteger(size(all_degrees) * 0.9)] as p90
                UNWIND all_degrees as degree
                WITH 
                    sum(CASE WHEN degree > p90 THEN 1 ELSE 0 END) as highly_connected,
                    sum(CASE WHEN degree = 0 THEN 1 ELSE 0 END) as isolated
                RETURN highly_connected, isolated
                """
                
                result = session.run(percentile_query)
                percentile_record = result.single()
                
                degree_distribution = {
                    "degree_buckets": degree_buckets,
                    "highly_connected_nodes": percentile_record["highly_connected"] if percentile_record else 0,
                    "isolated_nodes": percentile_record["isolated"] if percentile_record else 0
                }
            
            # ===== 4. CONNECTIVITY METRICS (with sampling) =====
            # Connected components count
            components_query = f"""
            MATCH (n{node_filter})
            WITH n
            CALL {{
                WITH n
                MATCH path = (n)-[{rel_filter}*]-(m{node_filter})
                RETURN collect(DISTINCT id(m)) + [id(n)] as component
            }}
            WITH DISTINCT component
            RETURN count(*) as num_components, max(size(component)) as largest_size
            """
            
            # Simplified version for efficiency
            simple_components_query = f"""
            MATCH (n{node_filter})
            OPTIONAL MATCH (n)-[r{rel_filter}*1..3]-(m{node_filter})
            WITH n, count(DISTINCT m) as reachable
            WITH 
                count(DISTINCT CASE WHEN reachable = 0 THEN n ELSE null END) as isolated_count,
                count(n) as total_count
            RETURN 
                CASE WHEN isolated_count > 0 THEN isolated_count + 1 ELSE 1 END as num_components,
                total_count - isolated_count as largest_size
            """
            
            with driver.session() as session:
                result = session.run(simple_components_query)
                conn_record = result.single()
                
                num_components = conn_record["num_components"] if conn_record else 1
                largest_size = conn_record["largest_size"] if conn_record else total_nodes
                
                # Sample nodes for expensive metrics
                sample_query = f"""
                MATCH (n{node_filter})
                WITH n
                ORDER BY rand()
                LIMIT $sample_size
                RETURN collect(id(n)) as sample_ids
                """
                
                result = session.run(sample_query, {"sample_size": min(sample_size, total_nodes)})
                sample_record = result.single()
                sample_ids = sample_record["sample_ids"] if sample_record else []
                
                # Calculate clustering coefficient for sample
                clustering_query = f"""
                UNWIND $sample_ids as node_id
                MATCH (n{node_filter})
                WHERE id(n) = node_id
                OPTIONAL MATCH (n)-[{rel_filter}]-(neighbor{node_filter})
                WITH n, collect(DISTINCT neighbor) as neighbors, count(DISTINCT neighbor) as degree
                WHERE degree >= 2
                UNWIND neighbors as n1
                UNWIND neighbors as n2
                WHERE id(n1) < id(n2)
                OPTIONAL MATCH (n1)-[{rel_filter}]-(n2)
                WITH n, degree, count(*) as possible_triangles, sum(CASE WHEN n1 IS NOT NULL AND n2 IS NOT NULL THEN 1 ELSE 0 END) as actual_triangles
                WITH 
                    CASE WHEN possible_triangles > 0 
                        THEN toFloat(actual_triangles) / possible_triangles 
                        ELSE 0.0 
                    END as local_clustering
                RETURN avg(local_clustering) as avg_clustering
                """
                
                result = session.run(clustering_query, {"sample_ids": sample_ids})
                clustering_record = result.single()
                avg_clustering = float(clustering_record["avg_clustering"]) if clustering_record and clustering_record["avg_clustering"] else 0.0
                
                # Estimate diameter and average path length via sampling
                path_query = f"""
                UNWIND $sample_ids as start_id
                MATCH (start{node_filter})
                WHERE id(start) = start_id
                MATCH (end{node_filter})
                WHERE id(end) <> start_id
                WITH start, end
                ORDER BY rand()
                LIMIT 10
                MATCH path = shortestPath((start)-[{rel_filter}*..10]-(end))
                RETURN length(path) as path_length
                """
                
                result = session.run(path_query, {"sample_ids": sample_ids[:min(100, len(sample_ids))]})
                path_lengths = [record["path_length"] for record in result if record["path_length"]]
                
                estimated_diameter = max(path_lengths) if path_lengths else 0
                avg_path_length = sum(path_lengths) / len(path_lengths) if path_lengths else 0.0
                
                connectivity_metrics = {
                    "connected_components": num_components,
                    "largest_component_size": largest_size,
                    "average_clustering_coefficient": avg_clustering,
                    "estimated_diameter": estimated_diameter,
                    "average_path_length": avg_path_length,
                    "sample_size_used": len(sample_ids)
                }
        
        # Generate explanation
        density_desc = "very sparse" if density_metrics["graph_density"] < 0.01 else \
                      "sparse" if density_metrics["graph_density"] < 0.1 else \
                      "moderate" if density_metrics["graph_density"] < 0.5 else "dense"
        
        clustering_desc = "low" if avg_clustering < 0.3 else \
                         "moderate" if avg_clustering < 0.6 else "high"
        
        connectivity_desc = "highly fragmented" if num_components > total_nodes * 0.1 else \
                           "somewhat fragmented" if num_components > 1 else "fully connected"
        
        explanation = (
            f"The graph contains {total_nodes:,} nodes and {total_relationships:,} relationships. "
            f"The graph is {density_desc} (density: {density_metrics['graph_density']:.4f}) "
            f"with an average degree of {density_metrics['average_degree']:.1f}. "
            f"Clustering is {clustering_desc} ({avg_clustering:.3f}), "
            f"suggesting {'strong local community structure' if avg_clustering > 0.5 else 'weak local clustering'}. "
            f"The graph is {connectivity_desc} with {num_components} connected component(s). "
        )
        
        if estimated_diameter > 0:
            explanation += f"The estimated diameter is {estimated_diameter} hops with an average path length of {avg_path_length:.2f}."
        
        result_data = {
            "basic_metrics": basic_metrics,
            "density_metrics": density_metrics,
            "degree_distribution": degree_distribution,
            "connectivity_metrics": connectivity_metrics,
            "explanation": explanation
        }
        
        logger.info(
            f"Graph statistics calculated successfully. Nodes: {total_nodes}, "
            f"Relationships: {total_relationships}, Density: {density_metrics['graph_density']:.4f}",
            operation="graph_stats",
            nodes=total_nodes,
            relationships=total_relationships
        )
        
        return result_data
        
    except ValidationError as e:
        logger.error(f"Validation error in graph_stats: {e}", operation="graph_stats")
        raise ToolExecutionError(
            message=f"Invalid parameters: {e.message}",
            tool_name="graph_stats",
            details=e.details,
            original_error=e
        )
    except Neo4jError as e:
        logger.error(f"Neo4j error in graph_stats: {e}", operation="graph_stats")
        raise GraphQueryError(
            message="Failed to calculate graph statistics",
            query="Multiple queries used",
            original_error=e
        )
    except Exception as e:
        logger.error(f"Unexpected error in graph_stats: {e}", operation="graph_stats")
        raise ToolExecutionError(
            message="Graph statistics operation failed",
            tool_name="graph_stats",
            original_error=e
        )


@tool
def find_bottlenecks() -> Dict[str, Any]:
    """
    Identify bottlenecks in the organizational structure and processes.
    
    Bottlenecks are nodes with high betweenness centrality or processes
    with many dependencies that could create delays or single points of failure.
    
    Returns:
        A dictionary containing:
        - "process_bottlenecks": Processes with many dependencies
        - "people_bottlenecks": People involved in too many processes
        - "system_bottlenecks": Systems used by many processes
        - "recommendations": Suggestions for addressing bottlenecks
    """
    # TODO: Implement actual bottleneck detection
    # This is a placeholder that will be implemented in task 4
    return {
        "process_bottlenecks": [],
        "people_bottlenecks": [],
        "system_bottlenecks": [],
        "recommendations": []
    }

