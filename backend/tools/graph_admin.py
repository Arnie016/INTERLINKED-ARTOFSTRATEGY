"""
Graph Admin Tools - Database management, backup, and schema operations.

This module provides administrative tools for managing the Neo4j database,
including reset operations, backups, and schema management. These tools
should only be available to admin users.
"""

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
import json
import os
from datetime import datetime


def reset_graph(driver: GraphDatabase, confirm: bool = False) -> Dict[str, Any]:
    """
    Reset the entire graph database (DANGEROUS - use with caution).
    
    Args:
        driver: Neo4j driver instance
        confirm: Must be True to actually perform the reset
    
    Returns:
        Dict containing reset result or error information
    """
    if not confirm:
        return {
            "success": False,
            "error": "Reset operation requires explicit confirmation. Set confirm=True to proceed.",
            "warning": "This will delete ALL data in the graph database!"
        }
    
    try:
        with driver.session() as session:
            # Delete all nodes and relationships
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted_count")
            record = result.single()
            deleted_count = record["deleted_count"] if record else 0
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Successfully reset graph database. Deleted {deleted_count} nodes."
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error resetting graph: {str(e)}"}


def backup_graph(driver: GraphDatabase, backup_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a backup of the graph database by exporting all data to JSON.
    
    Args:
        driver: Neo4j driver instance
        backup_path: Optional path to save backup file
    
    Returns:
        Dict containing backup result or error information
    """
    try:
        with driver.session() as session:
            # Export all nodes
            nodes_query = """
            MATCH (n)
            RETURN labels(n) as labels, properties(n) as properties, id(n) as id
            """
            
            # Export all relationships
            relationships_query = """
            MATCH (a)-[r]->(b)
            RETURN type(r) as type, properties(r) as properties, 
                   id(a) as start_node_id, id(b) as end_node_id,
                   labels(a) as start_labels, labels(b) as end_labels,
                   properties(a) as start_properties, properties(b) as end_properties
            """
            
            nodes_result = session.run(nodes_query)
            relationships_result = session.run(relationships_query)
            
            # Collect data
            nodes = [dict(record) for record in nodes_result]
            relationships = [dict(record) for record in relationships_result]
            
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "nodes": nodes,
                "relationships": relationships,
                "node_count": len(nodes),
                "relationship_count": len(relationships)
            }
            
            # Save to file if path provided
            if backup_path:
                with open(backup_path, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                
                return {
                    "success": True,
                    "backup_path": backup_path,
                    "node_count": len(nodes),
                    "relationship_count": len(relationships),
                    "message": f"Backup saved to {backup_path}"
                }
            else:
                return {
                    "success": True,
                    "backup_data": backup_data,
                    "node_count": len(nodes),
                    "relationship_count": len(relationships),
                    "message": "Backup data generated successfully"
                }
            
    except Exception as e:
        return {"success": False, "error": f"Error creating backup: {str(e)}"}


def restore_graph(driver: GraphDatabase, backup_data: Dict[str, Any], 
                  confirm: bool = False) -> Dict[str, Any]:
    """
    Restore graph database from backup data.
    
    Args:
        driver: Neo4j driver instance
        backup_data: Backup data dictionary
        confirm: Must be True to actually perform the restore
    
    Returns:
        Dict containing restore result or error information
    """
    if not confirm:
        return {
            "success": False,
            "error": "Restore operation requires explicit confirmation. Set confirm=True to proceed.",
            "warning": "This will replace ALL data in the graph database!"
        }
    
    try:
        with driver.session() as session:
            # Clear existing data first
            session.run("MATCH (n) DETACH DELETE n")
            
            # Restore nodes
            nodes = backup_data.get("nodes", [])
            relationships = backup_data.get("relationships", [])
            
            # Create node mapping for relationship restoration
            node_id_mapping = {}
            
            for node_data in nodes:
                node_id = node_data["id"]
                labels = node_data["labels"]
                properties = node_data["properties"]
                
                # Create node with labels and properties
                label_str = ":".join(labels) if labels else ""
                query = f"CREATE (n:{label_str} $props) RETURN id(n) as new_id"
                result = session.run(query, {"props": properties})
                record = result.single()
                
                if record:
                    new_id = record["new_id"]
                    node_id_mapping[node_id] = new_id
            
            # Restore relationships
            for rel_data in relationships:
                start_old_id = rel_data["start_node_id"]
                end_old_id = rel_data["end_node_id"]
                rel_type = rel_data["type"]
                rel_properties = rel_data["properties"]
                
                # Get new node IDs
                start_new_id = node_id_mapping.get(start_old_id)
                end_new_id = node_id_mapping.get(end_old_id)
                
                if start_new_id is not None and end_new_id is not None:
                    # Create relationship
                    if rel_properties:
                        query = """
                        MATCH (a), (b)
                        WHERE id(a) = $start_id AND id(b) = $end_id
                        CREATE (a)-[r:%s $props]->(b)
                        """ % rel_type
                        session.run(query, {
                            "start_id": start_new_id,
                            "end_id": end_new_id,
                            "props": rel_properties
                        })
                    else:
                        query = """
                        MATCH (a), (b)
                        WHERE id(a) = $start_id AND id(b) = $end_id
                        CREATE (a)-[r:%s]->(b)
                        """ % rel_type
                        session.run(query, {
                            "start_id": start_new_id,
                            "end_id": end_new_id
                        })
            
            return {
                "success": True,
                "restored_nodes": len(nodes),
                "restored_relationships": len(relationships),
                "message": f"Successfully restored {len(nodes)} nodes and {len(relationships)} relationships"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error restoring graph: {str(e)}"}


def get_database_info(driver: GraphDatabase) -> Dict[str, Any]:
    """
    Get information about the current database state.
    
    Args:
        driver: Neo4j driver instance
    
    Returns:
        Dict containing database information
    """
    try:
        with driver.session() as session:
            # Get basic counts
            counts_query = """
            MATCH (n) 
            WITH labels(n) as node_labels, count(n) as count
            UNWIND node_labels as label
            WITH label, sum(count) as total_count
            RETURN label, total_count
            ORDER BY total_count DESC
            """
            
            # Get relationship counts
            rel_counts_query = """
            MATCH ()-[r]->()
            WITH type(r) as rel_type, count(r) as count
            RETURN rel_type, count
            ORDER BY count DESC
            """
            
            # Get database size info
            size_query = """
            CALL apoc.meta.stats() YIELD nodeCount, relCount, labelCount, relTypeCount
            RETURN nodeCount, relCount, labelCount, relTypeCount
            """
            
            counts_result = session.run(counts_query)
            rel_counts_result = session.run(rel_counts_query)
            
            # Try to get size info (may fail if APOC not available)
            try:
                size_result = session.run(size_query)
                size_info = size_result.single()
            except:
                size_info = None
            
            node_counts = [dict(record) for record in counts_result]
            relationship_counts = [dict(record) for record in rel_counts_result]
            
            total_nodes = sum(count["total_count"] for count in node_counts)
            total_relationships = sum(count["count"] for count in relationship_counts)
            
            return {
                "success": True,
                "node_counts_by_label": node_counts,
                "relationship_counts_by_type": relationship_counts,
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "unique_labels": len(node_counts),
                "unique_relationship_types": len(relationship_counts),
                "size_info": dict(size_info) if size_info else None
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error getting database info: {str(e)}"}


def create_indexes(driver: GraphDatabase, indexes: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Create indexes on specified node properties for better query performance.
    
    Args:
        driver: Neo4j driver instance
        indexes: List of index specifications with 'label' and 'property' keys
    
    Returns:
        Dict containing index creation results
    """
    try:
        with driver.session() as session:
            created_indexes = []
            failed_indexes = []
            
            for index_spec in indexes:
                label = index_spec.get("label")
                property_name = index_spec.get("property")
                
                if not label or not property_name:
                    failed_indexes.append({
                        "spec": index_spec,
                        "error": "Missing label or property"
                    })
                    continue
                
                try:
                    # Create index
                    query = f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{property_name})"
                    session.run(query)
                    created_indexes.append(f"{label}.{property_name}")
                except Exception as e:
                    failed_indexes.append({
                        "spec": index_spec,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "created_indexes": created_indexes,
                "failed_indexes": failed_indexes,
                "message": f"Created {len(created_indexes)} indexes, {len(failed_indexes)} failed"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error creating indexes: {str(e)}"}


def validate_schema(driver: GraphDatabase) -> Dict[str, Any]:
    """
    Validate the current database schema and identify potential issues.
    
    Args:
        driver: Neo4j driver instance
    
    Returns:
        Dict containing schema validation results
    """
    try:
        with driver.session() as session:
            # Check for nodes without required properties
            orphaned_nodes_query = """
            MATCH (n)
            WHERE n.name IS NULL OR n.name = ""
            RETURN labels(n) as labels, count(n) as count
            """
            
            # Check for relationships without proper nodes
            invalid_relationships_query = """
            MATCH (a)-[r]->(b)
            WHERE a.name IS NULL OR b.name IS NULL
            RETURN type(r) as rel_type, count(r) as count
            """
            
            # Check for duplicate names within same label
            duplicate_names_query = """
            MATCH (n)
            WITH labels(n) as node_labels, n.name as name, count(n) as count
            WHERE count > 1
            UNWIND node_labels as label
            RETURN label, name, count
            """
            
            orphaned_result = session.run(orphaned_nodes_query)
            invalid_rels_result = session.run(invalid_relationships_query)
            duplicates_result = session.run(duplicate_names_query)
            
            orphaned_nodes = [dict(record) for record in orphaned_result]
            invalid_relationships = [dict(record) for record in invalid_rels_result]
            duplicate_names = [dict(record) for record in duplicates_result]
            
            issues = []
            if orphaned_nodes:
                issues.append(f"Found {sum(n['count'] for n in orphaned_nodes)} nodes without names")
            if invalid_relationships:
                issues.append(f"Found {sum(r['count'] for r in invalid_relationships)} invalid relationships")
            if duplicate_names:
                issues.append(f"Found {len(duplicate_names)} duplicate names")
            
            return {
                "success": True,
                "orphaned_nodes": orphaned_nodes,
                "invalid_relationships": invalid_relationships,
                "duplicate_names": duplicate_names,
                "issues": issues,
                "is_valid": len(issues) == 0,
                "message": "Schema validation completed" if len(issues) == 0 else f"Found {len(issues)} schema issues"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error validating schema: {str(e)}"}


# Tool registry for this module
TOOLS = {
    "reset_graph": {
        "function": reset_graph,
        "description": "Reset the entire graph database (DANGEROUS - use with caution)",
        "category": "admin",
        "permissions": ["admin"]
    },
    "backup_graph": {
        "function": backup_graph,
        "description": "Create a backup of the graph database by exporting all data to JSON",
        "category": "admin",
        "permissions": ["admin"]
    },
    "restore_graph": {
        "function": restore_graph,
        "description": "Restore graph database from backup data",
        "category": "admin",
        "permissions": ["admin"]
    },
    "get_database_info": {
        "function": get_database_info,
        "description": "Get information about the current database state",
        "category": "admin",
        "permissions": ["admin", "analyzer"]
    },
    "create_indexes": {
        "function": create_indexes,
        "description": "Create indexes on specified node properties for better query performance",
        "category": "admin",
        "permissions": ["admin"]
    },
    "validate_schema": {
        "function": validate_schema,
        "description": "Validate the current database schema and identify potential issues",
        "category": "admin",
        "permissions": ["admin", "analyzer"]
    }
}
