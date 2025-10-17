"""
Graph Admin Tools - Administrative and maintenance operations.

These tools provide privileged database operations for maintenance,
optimization, and schema management with strict safety controls.

All admin operations require:
- Admin role authorization
- Explicit confirmation for destructive operations  
- Dry-run mode by default
- Comprehensive audit logging
- Safety interlocks and size limits
"""

from strands import tool
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from src.config import create_session
from src.utils import (
    AuthContext,
    get_logger,
    require_admin_role,
    Permission,
    ValidationError,
    GraphQueryError,
    GraphOperationError,
    ToolExecutionError,
    get_user_context_for_logging
)
from src.config.constants import (
    MAX_BULK_DELETE,
    get_success_message,
    get_error_message
)

logger = get_logger(__name__)

# Admin-specific constants
MAX_REINDEX_NODES = 100000  # Maximum nodes for reindexing
MAX_MIGRATION_NODES = 10000  # Maximum nodes for label migration
MAX_ORPHAN_CLEANUP = 1000   # Maximum orphans to delete in one operation
BATCH_SIZE = 100            # Batch size for bulk operations
OPERATION_TIMEOUT = 300     # 5 minutes max per operation


@tool
def reindex(
    label: str,
    property: str,
    dry_run: bool = True,
    confirm: bool = False,
    auth: Optional[AuthContext] = None
) -> Dict[str, Any]:
    """
    Create or rebuild an index on a node label and property.
    
    Indexing improves query performance for frequently accessed properties.
    
    Args:
        label: The node label to index (e.g., "Person")
        property: The property to index (e.g., "name", "email")
        dry_run: If True, shows what would be done without executing (default: True)
        confirm: Explicit confirmation required for execution (must be True if dry_run=False)
        auth: Authentication context (required, must have admin role)
    
    Returns:
        A dictionary containing:
        - "success": Whether operation succeeded
        - "dry_run": Whether this was a dry run
        - "label": The label that was/would be indexed
        - "property": The property that was/would be indexed
        - "affected_nodes": Number of nodes affected
        - "execution_time_ms": Estimated or actual execution time
        - "index_name": Name of the index created
        - "already_exists": Whether index already existed
    
    Examples:
        - reindex("Person", "name", dry_run=True, auth=admin_auth)  # Preview
        - reindex("Person", "email", dry_run=False, confirm=True, auth=admin_auth)  # Execute
    
    Safety measures:
        - Admin role required
        - Dry-run mode mandatory by default
        - Explicit confirmation required for execution
        - Size limits on indexable node sets
        - Execution time monitoring
        - Detailed audit logging
    
    Raises:
        AuthenticationError: If auth context is missing
        AuthorizationError: If user is not admin
        ValidationError: If label or property is invalid
        GraphOperationError: If operation fails
    """
    start_time = time.time()
    operation_context = {
        "operation": "reindex",
        "label": label,
        "property": property,
        "dry_run": dry_run,
        "confirm": confirm,
        "user": get_user_context_for_logging(auth) if auth else None
    }
    
    try:
        # RBAC check - admin role required
        if not auth:
            raise ValidationError(
                "Authentication required for admin operations",
                field="auth",
                details=operation_context
            )
        
        require_admin_role(lambda **kwargs: None)(auth=auth)
        auth.require_permission(Permission.REINDEX)
        
        # Log admin operation
        logger.info(f"Admin reindex operation initiated by {auth.username}", extra=operation_context)
        
        # Validation
        if not label or not label.strip():
            raise ValidationError("Label is required", field="label")
        
        if not property or not property.strip():
            raise ValidationError("Property name is required", field="property")
        
        # Safety check: require confirmation for actual execution
        if not dry_run and not confirm:
            raise ValidationError(
                "Explicit confirmation required for index creation. Set confirm=True to proceed.",
                field="confirm",
                details={"dry_run": dry_run, "confirm": confirm}
            )
        
        # Query to check node count and if property exists
        with create_session() as session:
            # Check if label exists and count nodes
            count_query = f"""
            MATCH (n:{label})
            RETURN count(n) as node_count,
                   count(n.{property}) as property_count
            """
            
            try:
                result = session.run(count_query).single()
                node_count = result["node_count"] if result else 0
                property_count = result["property_count"] if result else 0
            except Exception as e:
                raise GraphQueryError(
                    f"Failed to query nodes for label '{label}': {str(e)}",
                    query=count_query,
                    details={"label": label, "property": property}
                ) from e
            
            # Safety interlock: check node count
            if node_count > MAX_REINDEX_NODES:
                raise GraphOperationError(
                    f"Cannot reindex {node_count} nodes (exceeds maximum of {MAX_REINDEX_NODES})",
                    operation="reindex",
                    details={
                        "node_count": node_count,
                        "max_allowed": MAX_REINDEX_NODES,
                        "label": label
                    }
                )
            
            # Generate index name
            index_name = f"index_{label}_{property}".lower().replace(" ", "_")
            
            # Check if index already exists
            check_index_query = "SHOW INDEXES"
            existing_indexes = list(session.run(check_index_query))
            index_exists = any(
                idx.get("name") == index_name or 
                (idx.get("labelsOrTypes") == [label] and property in idx.get("properties", []))
                for idx in existing_indexes
            )
            
            if dry_run:
                # Dry run - show what would happen
                execution_time_ms = (time.time() - start_time) * 1000
                
                result = {
                    "success": True,
                    "dry_run": True,
                    "label": label,
                    "property": property,
                    "affected_nodes": node_count,
                    "nodes_with_property": property_count,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "index_name": index_name,
                    "already_exists": index_exists,
                    "estimated_creation_time_ms": round(node_count * 0.1, 2),  # Rough estimate
                    "preview": {
                        "action": "CREATE INDEX" if not index_exists else "INDEX ALREADY EXISTS",
                        "index_name": index_name,
                        "index_for": f"{label}({property})",
                        "affected_nodes": node_count,
                        "nodes_missing_property": node_count - property_count
                    }
                }
                
                logger.info(f"Reindex dry run completed", extra={**operation_context, **result})
                return result
            
            else:
                # Actual execution
                if index_exists:
                    # Index already exists
                    execution_time_ms = (time.time() - start_time) * 1000
                    
                    result = {
                        "success": True,
                        "dry_run": False,
                        "label": label,
                        "property": property,
                        "affected_nodes": node_count,
                        "execution_time_ms": round(execution_time_ms, 2),
                        "index_name": index_name,
                        "already_exists": True,
                        "message": f"Index '{index_name}' already exists for {label}({property})"
                    }
                    
                    logger.info(f"Index already exists", extra={**operation_context, **result})
                    return result
                
                # Create the index
                create_index_query = f"""
                CREATE INDEX {index_name} IF NOT EXISTS
                FOR (n:{label})
                ON (n.{property})
                """
                
                try:
                    session.run(create_index_query)
                    execution_time_ms = (time.time() - start_time) * 1000
                    
                    result = {
                        "success": True,
                        "dry_run": False,
                        "label": label,
                        "property": property,
                        "affected_nodes": node_count,
                        "execution_time_ms": round(execution_time_ms, 2),
                        "index_name": index_name,
                        "already_exists": False,
                        "message": get_success_message("reindex_started")
                    }
                    
                    logger.info(
                        f"Index created successfully by {auth.username}",
                        extra={**operation_context, **result}
                    )
                    
                    return result
                    
                except Exception as e:
                    raise GraphOperationError(
                        f"Failed to create index: {str(e)}",
                        operation="create_index",
                        details={"query": create_index_query}
                    ) from e
    
    except (ValidationError, GraphQueryError, GraphOperationError) as e:
        logger.error(f"Reindex operation failed: {str(e)}", extra=operation_context)
        raise ToolExecutionError(
            f"Reindex operation failed: {str(e)}",
            tool_name="reindex",
            details=operation_context
        ) from e
    
    except Exception as e:
        logger.error(f"Unexpected error in reindex: {str(e)}", extra=operation_context, exc_info=True)
        raise ToolExecutionError(
            f"Unexpected error in reindex operation: {str(e)}",
            tool_name="reindex",
            details=operation_context
        ) from e


@tool
def migrate_labels(
    old_label: str,
    new_label: str,
    dry_run: bool = True,
    confirm: bool = False,
    auth: Optional[AuthContext] = None
) -> Dict[str, Any]:
    """
    Migrate nodes from one label to another.
    
    This operation changes the label on existing nodes, useful for
    schema evolution and refactoring.
    
    Args:
        old_label: Current label to migrate from
        new_label: New label to migrate to
        dry_run: If True, previews changes without executing (default: True)
        confirm: Explicit confirmation required for execution (must be True if dry_run=False)
        auth: Authentication context (required, must have admin role)
    
    Returns:
        A dictionary containing:
        - "success": Whether operation succeeded
        - "dry_run": Whether this was a dry run
        - "old_label": The original label
        - "new_label": The target label
        - "affected_nodes": Number of nodes affected
        - "execution_time_ms": Actual execution time
        - "preview": Preview of changes if dry_run=True
        - "rollback_available": Whether rollback is possible
        - "batches_processed": Number of batches (if executed)
    
    Examples:
        - migrate_labels("Employee", "Person", dry_run=True, auth=admin_auth)  # Preview
        - migrate_labels("Employee", "Person", dry_run=False, confirm=True, auth=admin_auth)  # Execute
    
    Safety measures:
        - Admin role required
        - Dry-run mode mandatory by default
        - Explicit confirmation required for execution
        - Transaction-based with rollback capability
        - Batch processing for large datasets
        - Size limits on migration operations
        - Detailed preview before execution
        - Comprehensive audit trail
    
    Raises:
        AuthenticationError: If auth context is missing
        AuthorizationError: If user is not admin
        ValidationError: If labels are invalid
        GraphOperationError: If migration fails
    """
    start_time = time.time()
    operation_context = {
        "operation": "migrate_labels",
        "old_label": old_label,
        "new_label": new_label,
        "dry_run": dry_run,
        "confirm": confirm,
        "user": get_user_context_for_logging(auth) if auth else None
    }
    
    try:
        # RBAC check - admin role required
        if not auth:
            raise ValidationError(
                "Authentication required for admin operations",
                field="auth",
                details=operation_context
            )
        
        require_admin_role(lambda **kwargs: None)(auth=auth)
        auth.require_permission(Permission.MANAGE_SCHEMA)
        
        # Log admin operation
        logger.info(f"Admin label migration initiated by {auth.username}", extra=operation_context)
        
        # Validation
        if not old_label or not old_label.strip():
            raise ValidationError("Old label is required", field="old_label")
        
        if not new_label or not new_label.strip():
            raise ValidationError("New label is required", field="new_label")
        
        if old_label == new_label:
            raise ValidationError(
                "Old label and new label must be different",
                field="new_label",
                details={"old_label": old_label, "new_label": new_label}
            )
        
        # Safety check: require confirmation for actual execution
        if not dry_run and not confirm:
            raise ValidationError(
                "Explicit confirmation required for label migration. Set confirm=True to proceed.",
                field="confirm",
                details={"dry_run": dry_run, "confirm": confirm}
            )
        
        with create_session() as session:
            # Count nodes with old label
            count_query = f"MATCH (n:{old_label}) RETURN count(n) as count"
            
            try:
                result = session.run(count_query).single()
                node_count = result["count"] if result else 0
            except Exception as e:
                raise GraphQueryError(
                    f"Failed to count nodes with label '{old_label}': {str(e)}",
                    query=count_query
                ) from e
            
            if node_count == 0:
                return {
                    "success": True,
                    "dry_run": dry_run,
                    "old_label": old_label,
                    "new_label": new_label,
                    "affected_nodes": 0,
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                    "message": f"No nodes found with label '{old_label}'"
                }
            
            # Safety interlock: check node count
            if node_count > MAX_MIGRATION_NODES:
                raise GraphOperationError(
                    f"Cannot migrate {node_count} nodes (exceeds maximum of {MAX_MIGRATION_NODES})",
                    operation="migrate_labels",
                    details={
                        "node_count": node_count,
                        "max_allowed": MAX_MIGRATION_NODES,
                        "old_label": old_label
                    }
                )
            
            # Get sample nodes for preview
            sample_query = f"""
            MATCH (n:{old_label})
            RETURN n
            LIMIT 5
            """
            
            sample_nodes = []
            for record in session.run(sample_query):
                node = record["n"]
                sample_nodes.append({
                    "id": node.id,
                    "labels": list(node.labels),
                    "properties": dict(node)
                })
            
            if dry_run:
                # Dry run - show preview
                execution_time_ms = (time.time() - start_time) * 1000
                num_batches = (node_count + BATCH_SIZE - 1) // BATCH_SIZE
                
                result = {
                    "success": True,
                    "dry_run": True,
                    "old_label": old_label,
                    "new_label": new_label,
                    "affected_nodes": node_count,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "estimated_batches": num_batches,
                    "estimated_execution_time_ms": round(node_count * 10, 2),  # Rough estimate
                    "rollback_available": True,  # Transaction-based
                    "preview": {
                        "action": "REMOVE old label, SET new label",
                        "affected_nodes": node_count,
                        "sample_nodes": sample_nodes,
                        "migration_steps": [
                            f"1. Remove label '{old_label}' from {node_count} nodes",
                            f"2. Add label '{new_label}' to {node_count} nodes",
                            f"3. Process in {num_batches} batches of {BATCH_SIZE} nodes"
                        ]
                    }
                }
                
                logger.info(f"Label migration dry run completed", extra={**operation_context, **result})
                return result
            
            else:
                # Actual execution - transaction-based for rollback capability
                migrated_count = 0
                batches_processed = 0
                
                try:
                    tx = session.begin_transaction()
                    
                    # Process in batches
                    while migrated_count < node_count:
                        batch_query = f"""
                        MATCH (n:{old_label})
                        WITH n LIMIT {BATCH_SIZE}
                        REMOVE n:{old_label}
                        SET n:{new_label}
                        RETURN count(n) as batch_count
                        """
                        
                        batch_result = tx.run(batch_query).single()
                        batch_count = batch_result["batch_count"] if batch_result else 0
                        
                        migrated_count += batch_count
                        batches_processed += 1
                        
                        logger.info(
                            f"Processed batch {batches_processed}: {batch_count} nodes",
                            extra={**operation_context, "batch": batches_processed, "migrated": migrated_count}
                        )
                        
                        # Safety check: timeout
                        if (time.time() - start_time) > OPERATION_TIMEOUT:
                            tx.rollback()
                            raise GraphOperationError(
                                f"Migration operation timed out after {OPERATION_TIMEOUT} seconds",
                                operation="migrate_labels",
                                details={"migrated_count": migrated_count, "total": node_count}
                            )
                        
                        # Break if no more nodes processed
                        if batch_count == 0:
                            break
                    
                    # Commit transaction
                    tx.commit()
                    execution_time_ms = (time.time() - start_time) * 1000
                    
                    result = {
                        "success": True,
                        "dry_run": False,
                        "old_label": old_label,
                        "new_label": new_label,
                        "affected_nodes": migrated_count,
                        "execution_time_ms": round(execution_time_ms, 2),
                        "batches_processed": batches_processed,
                        "rollback_available": False,  # Already committed
                        "message": f"Successfully migrated {migrated_count} nodes from '{old_label}' to '{new_label}'"
                    }
                    
                    logger.info(
                        f"Label migration completed successfully by {auth.username}",
                        extra={**operation_context, **result}
                    )
                    
                    return result
                    
                except Exception as e:
                    # Rollback on error
                    try:
                        tx.rollback()
                        logger.warning(f"Transaction rolled back due to error", extra=operation_context)
                    except:
                        pass
                    
                    raise GraphOperationError(
                        f"Label migration failed: {str(e)}",
                        operation="migrate_labels",
                        details={"migrated_before_error": migrated_count, "total": node_count}
                    ) from e
    
    except (ValidationError, GraphQueryError, GraphOperationError) as e:
        logger.error(f"Label migration failed: {str(e)}", extra=operation_context)
        raise ToolExecutionError(
            f"Label migration failed: {str(e)}",
            tool_name="migrate_labels",
            details=operation_context
        ) from e
    
    except Exception as e:
        logger.error(f"Unexpected error in migrate_labels: {str(e)}", extra=operation_context, exc_info=True)
        raise ToolExecutionError(
            f"Unexpected error in label migration: {str(e)}",
            tool_name="migrate_labels",
            details=operation_context
        ) from e


@tool
def maintenance_cleanup_orphan_nodes(
    dry_run: bool = True,
    confirm: bool = False,
    max_delete: int = MAX_ORPHAN_CLEANUP,
    auth: Optional[AuthContext] = None
) -> Dict[str, Any]:
    """
    Clean up orphaned nodes (nodes with no relationships).
    
    Orphaned nodes can accumulate over time and may indicate data quality
    issues or incomplete deletions.
    
    Args:
        dry_run: If True, identifies orphans without deleting (default: True)
        confirm: Explicit confirmation required for deletion (must be True if dry_run=False)
        max_delete: Maximum number of orphans to delete (default: 1000)
        auth: Authentication context (required, must have admin role)
    
    Returns:
        A dictionary containing:
        - "success": Whether operation succeeded
        - "dry_run": Whether this was a dry run
        - "orphaned_nodes_found": Number of orphans identified
        - "orphaned_nodes_deleted": Number actually deleted (0 if dry_run)
        - "execution_time_ms": Actual execution time
        - "orphan_details": Details about orphaned nodes by label
        - "recommendations": Suggestions about the orphans
        - "batches_processed": Number of batches (if executed)
    
    Examples:
        - maintenance_cleanup_orphan_nodes(dry_run=True, auth=admin_auth)  # Identify
        - maintenance_cleanup_orphan_nodes(dry_run=False, confirm=True, auth=admin_auth)  # Delete
    
    Safety measures:
        - Admin role required
        - Dry-run mode mandatory by default
        - Explicit confirmation required for deletion
        - Batch processing for large numbers
        - Size limits on deletion operations
        - Detailed reporting before deletion
        - Comprehensive audit logging
    
    Raises:
        AuthenticationError: If auth context is missing
        AuthorizationError: If user is not admin
        ValidationError: If max_delete is invalid
        GraphOperationError: If cleanup fails
    """
    start_time = time.time()
    operation_context = {
        "operation": "maintenance_cleanup_orphan_nodes",
        "dry_run": dry_run,
        "confirm": confirm,
        "max_delete": max_delete,
        "user": get_user_context_for_logging(auth) if auth else None
    }
    
    try:
        # RBAC check - admin role required
        if not auth:
            raise ValidationError(
                "Authentication required for admin operations",
                field="auth",
                details=operation_context
            )
        
        require_admin_role(lambda **kwargs: None)(auth=auth)
        auth.require_permission(Permission.ADMIN_OPERATIONS)
        
        # Log admin operation
        logger.info(f"Admin orphan cleanup initiated by {auth.username}", extra=operation_context)
        
        # Validation
        if max_delete <= 0 or max_delete > MAX_ORPHAN_CLEANUP:
            raise ValidationError(
                f"max_delete must be between 1 and {MAX_ORPHAN_CLEANUP}",
                field="max_delete",
                details={"max_delete": max_delete, "max_allowed": MAX_ORPHAN_CLEANUP}
            )
        
        # Safety check: require confirmation for actual deletion
        if not dry_run and not confirm:
            raise ValidationError(
                "Explicit confirmation required for orphan deletion. Set confirm=True to proceed.",
                field="confirm",
                details={"dry_run": dry_run, "confirm": confirm}
            )
        
        with create_session() as session:
            # Find orphan nodes (nodes with no relationships)
            orphan_query = """
            MATCH (n)
            WHERE NOT (n)--()
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            try:
                orphan_stats = []
                total_orphans = 0
                
                for record in session.run(orphan_query):
                    labels = record["labels"]
                    count = record["count"]
                    label_str = ":".join(labels) if labels else "NO_LABEL"
                    
                    orphan_stats.append({
                        "labels": label_str,
                        "count": count
                    })
                    total_orphans += count
                
            except Exception as e:
                raise GraphQueryError(
                    f"Failed to query orphan nodes: {str(e)}",
                    query=orphan_query
                ) from e
            
            if total_orphans == 0:
                return {
                    "success": True,
                    "dry_run": dry_run,
                    "orphaned_nodes_found": 0,
                    "orphaned_nodes_deleted": 0,
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                    "orphan_details": [],
                    "message": "No orphaned nodes found"
                }
            
            # Get sample orphan nodes for recommendations
            sample_query = """
            MATCH (n)
            WHERE NOT (n)--()
            RETURN n
            LIMIT 10
            """
            
            sample_orphans = []
            for record in session.run(sample_query):
                node = record["n"]
                sample_orphans.append({
                    "id": node.id,
                    "labels": list(node.labels),
                    "properties": dict(node)
                })
            
            # Generate recommendations
            recommendations = []
            if total_orphans < 10:
                recommendations.append("Small number of orphans - may be recent deletions or data entry errors")
            elif total_orphans > 100:
                recommendations.append("Large number of orphans detected - investigate data quality processes")
            
            if any(stat["labels"] == "NO_LABEL" for stat in orphan_stats):
                recommendations.append("Found nodes without labels - consider adding labels or removing")
            
            recommendations.append("Review sample orphans to understand why they exist before deletion")
            
            if dry_run:
                # Dry run - show what would be deleted
                execution_time_ms = (time.time() - start_time) * 1000
                nodes_to_delete = min(total_orphans, max_delete)
                num_batches = (nodes_to_delete + BATCH_SIZE - 1) // BATCH_SIZE
                
                result = {
                    "success": True,
                    "dry_run": True,
                    "orphaned_nodes_found": total_orphans,
                    "orphaned_nodes_to_delete": nodes_to_delete,
                    "orphaned_nodes_deleted": 0,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "estimated_batches": num_batches,
                    "estimated_deletion_time_ms": round(nodes_to_delete * 5, 2),
                    "orphan_details": orphan_stats,
                    "sample_orphans": sample_orphans,
                    "recommendations": recommendations,
                    "preview": {
                        "action": "DELETE orphaned nodes",
                        "total_orphans": total_orphans,
                        "will_delete": nodes_to_delete,
                        "will_remain": max(0, total_orphans - max_delete)
                    }
                }
                
                logger.info(f"Orphan cleanup dry run completed", extra={**operation_context, **result})
                return result
            
            else:
                # Actual deletion - process in batches
                deleted_count = 0
                batches_processed = 0
                nodes_to_delete = min(total_orphans, max_delete)
                
                try:
                    while deleted_count < nodes_to_delete:
                        batch_query = """
                        MATCH (n)
                        WHERE NOT (n)--()
                        WITH n LIMIT $batch_size
                        DELETE n
                        RETURN count(n) as batch_count
                        """
                        
                        batch_result = session.run(
                            batch_query,
                            batch_size=min(BATCH_SIZE, nodes_to_delete - deleted_count)
                        ).single()
                        
                        batch_count = batch_result["batch_count"] if batch_result else 0
                        deleted_count += batch_count
                        batches_processed += 1
                        
                        logger.info(
                            f"Deleted batch {batches_processed}: {batch_count} orphans",
                            extra={**operation_context, "batch": batches_processed, "deleted": deleted_count}
                        )
                        
                        # Safety check: timeout
                        if (time.time() - start_time) > OPERATION_TIMEOUT:
                            raise GraphOperationError(
                                f"Cleanup operation timed out after {OPERATION_TIMEOUT} seconds",
                                operation="cleanup_orphans",
                                details={"deleted_count": deleted_count, "total": total_orphans}
                            )
                        
                        # Break if no more nodes deleted
                        if batch_count == 0:
                            break
                    
                    execution_time_ms = (time.time() - start_time) * 1000
                    
                    result = {
                        "success": True,
                        "dry_run": False,
                        "orphaned_nodes_found": total_orphans,
                        "orphaned_nodes_deleted": deleted_count,
                        "orphaned_nodes_remaining": total_orphans - deleted_count,
                        "execution_time_ms": round(execution_time_ms, 2),
                        "batches_processed": batches_processed,
                        "orphan_details": orphan_stats,
                        "message": f"Successfully deleted {deleted_count} orphaned nodes"
                    }
                    
                    logger.info(
                        f"Orphan cleanup completed successfully by {auth.username}",
                        extra={**operation_context, **result}
                    )
                    
                    return result
                    
                except Exception as e:
                    raise GraphOperationError(
                        f"Orphan cleanup failed: {str(e)}",
                        operation="cleanup_orphans",
                        details={"deleted_before_error": deleted_count, "total": total_orphans}
                    ) from e
    
    except (ValidationError, GraphQueryError, GraphOperationError) as e:
        logger.error(f"Orphan cleanup failed: {str(e)}", extra=operation_context)
        raise ToolExecutionError(
            f"Orphan cleanup failed: {str(e)}",
            tool_name="maintenance_cleanup_orphan_nodes",
            details=operation_context
        ) from e
    
    except Exception as e:
        logger.error(f"Unexpected error in orphan cleanup: {str(e)}", extra=operation_context, exc_info=True)
        raise ToolExecutionError(
            f"Unexpected error in orphan cleanup: {str(e)}",
            tool_name="maintenance_cleanup_orphan_nodes",
            details=operation_context
        ) from e
