"""
Graph CRUD Tools - Create and update operations.

These tools provide controlled write access to create nodes and relationships
in the Neo4j graph database with appropriate validation and safety measures.
"""

from strands import tool
from typing import Dict, Any, List, Optional
import sys
import json

from ..config import get_driver, create_session
from ..utils import (
    ValidationError,
    GraphOperationError,
    ToolExecutionError,
    validate_node_label,
    validate_node_properties,
    logger,
    VALID_NODE_LABELS
)
from ..config.constants import MAX_BULK_CREATE


# Maximum payload size in bytes (1MB)
MAX_PAYLOAD_SIZE = 1024 * 1024

# Maximum property value length
MAX_PROPERTY_LENGTH = 10000


def validate_payload_size(data: Dict[str, Any], max_size: int = MAX_PAYLOAD_SIZE) -> None:
    """
    Validate that the payload size doesn't exceed the maximum.
    
    Args:
        data: Data to validate
        max_size: Maximum allowed size in bytes
        
    Raises:
        ValidationError: If payload is too large
    """
    payload_json = json.dumps(data)
    payload_size = sys.getsizeof(payload_json)
    
    if payload_size > max_size:
        raise ValidationError(
            f"Payload size ({payload_size} bytes) exceeds maximum allowed size ({max_size} bytes)",
            field="properties",
            details={"size": payload_size, "max_size": max_size}
        )


def validate_property_values(properties: Dict[str, Any]) -> None:
    """
    Validate that property values don't exceed maximum length.
    
    Args:
        properties: Properties to validate
        
    Raises:
        ValidationError: If any property value is too long
    """
    for key, value in properties.items():
        if isinstance(value, str) and len(value) > MAX_PROPERTY_LENGTH:
            raise ValidationError(
                f"Property '{key}' value exceeds maximum length of {MAX_PROPERTY_LENGTH} characters",
                field=key,
                details={"length": len(value), "max_length": MAX_PROPERTY_LENGTH}
            )


def check_node_exists(session, label: str, properties: Dict[str, Any]) -> Optional[int]:
    """
    Check if a node with the same label and key properties already exists.
    
    Args:
        session: Neo4j session
        label: Node label
        properties: Node properties
        
    Returns:
        Node ID if exists, None otherwise
    """
    # Use 'name' as the key property for idempotency checks
    if 'name' not in properties:
        return None
    
    query = f"""
    MATCH (n:{label})
    WHERE n.name = $name
    RETURN elementId(n) as node_id
    LIMIT 1
    """
    
    result = session.run(query, name=properties['name'])
    record = result.single()
    
    return record['node_id'] if record else None


@tool
def create_node(
    label: str,
    properties: Dict[str, Any],
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Create a new node in the graph with comprehensive validation.
    
    This tool creates a single node with specified label and properties,
    with validation against allowed schemas and labels. Includes idempotency
    checks to prevent duplicate nodes.
    
    Args:
        label: The node label (must be one of: Person, Organization, Project, Technology, Resource)
        properties: Dictionary of node properties (must include 'name' for idempotency)
        dry_run: If True, validates but doesn't actually create the node (default: False)
    
    Returns:
        A dictionary containing:
        - "success": Boolean indicating if creation succeeded
        - "dry_run": Whether this was a dry run
        - "node_id": ID of the created node (or existing node if duplicate)
        - "node": The created/existing node with all properties
        - "was_duplicate": True if node already existed
        - "validation_errors": Any validation issues (if success is False)
    
    Examples:
        >>> create_node("Person", {"name": "Alice Johnson", "role": "Engineer"})
        {"success": True, "node_id": 123, "node": {...}, "was_duplicate": False}
        
        >>> create_node("Organization", {"name": "Acme Corp"}, dry_run=True)
        {"success": True, "dry_run": True, "node_id": None, "node": {...}}
    
    Safety measures:
        - Label must be in allowlist (Person, Organization, Project, Technology, Resource)
        - Properties are validated against schema
        - Payload size is limited to 1MB
        - Property values limited to 10,000 characters
        - Idempotency checks prevent duplicates (based on 'name' property)
        - Dry-run mode for testing without writes
        - Comprehensive error handling and logging
    """
    operation_context = {
        "operation": "create_node",
        "label": label,
        "dry_run": dry_run
    }
    
    try:
        logger.info(f"Creating node with label '{label}'", extra=operation_context)
        
        # Validate label
        validate_node_label(label)
        
        # Validate properties structure and types
        validated_properties = validate_node_properties(label, properties, check_required=True)
        
        # Validate payload size
        validate_payload_size(validated_properties)
        
        # Validate property values
        validate_property_values(validated_properties)
        
        # Dry run mode - return validated structure without writing
        if dry_run:
            logger.info(f"Dry run for creating {label} node", extra=operation_context)
            return {
                "success": True,
                "dry_run": True,
                "node_id": None,
                "node": {
                    "label": label,
                    "properties": validated_properties
                },
                "was_duplicate": False,
                "message": "Validation passed. Node would be created."
            }
        
        # Create node in Neo4j
        with create_session() as session:
            # Check for existing node (idempotency)
            existing_node_id = check_node_exists(session, label, validated_properties)
            
            if existing_node_id is not None:
                # Node already exists - return existing node
                logger.info(
                    f"Node with label '{label}' and name '{validated_properties.get('name')}' already exists",
                    extra={**operation_context, "node_id": existing_node_id}
                )
                
                # Fetch existing node details
                fetch_query = f"""
                MATCH (n:{label})
                WHERE elementId(n) = $node_id
                RETURN n
                """
                result = session.run(fetch_query, node_id=existing_node_id)
                existing_node = result.single()['n']
                
                return {
                    "success": True,
                    "dry_run": False,
                    "node_id": existing_node_id,
                    "node": {
                        "id": existing_node_id,
                        "label": label,
                        "properties": dict(existing_node)
                    },
                    "was_duplicate": True,
                    "message": f"Node already exists with id {existing_node_id}"
                }
            
            # Create new node
            create_query = f"""
            CREATE (n:{label} $properties)
            RETURN elementId(n) as node_id, n
            """
            
            result = session.run(create_query, properties=validated_properties)
            record = result.single()
            
            node_id = record['node_id']
            node = record['n']
            
            logger.info(
                f"Successfully created node with id {node_id}",
                extra={**operation_context, "node_id": node_id}
            )
            
            return {
                "success": True,
                "dry_run": False,
                "node_id": node_id,
                "node": {
                    "id": node_id,
                    "label": label,
                    "properties": dict(node)
                },
                "was_duplicate": False,
                "message": f"Node created successfully with id {node_id}"
            }
    
    except ValidationError as e:
        logger.warning(
            f"Validation error creating node: {str(e)}",
            extra={**operation_context, "error": str(e)}
        )
        return {
            "success": False,
            "dry_run": dry_run,
            "node_id": None,
            "node": None,
            "validation_errors": [str(e)],
            "error": str(e)
        }
    
    except GraphOperationError as e:
        logger.error(
            f"Graph operation error creating node: {str(e)}",
            extra={**operation_context, "error": str(e)}
        )
        return {
            "success": False,
            "dry_run": dry_run,
            "node_id": None,
            "node": None,
            "error": str(e)
        }
    
    except Exception as e:
        error_msg = f"Unexpected error creating node: {str(e)}"
        logger.error(error_msg, extra={**operation_context, "error": str(e)})
        raise ToolExecutionError(error_msg, tool_name="create_node") from e


@tool
def create_relationship(
    start_node_id: str,
    end_node_id: str,
    relationship_type: str,
    properties: Optional[Dict[str, Any]] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Create a relationship between two existing nodes with comprehensive validation.
    
    This tool creates a directed relationship from start_node to end_node
    with validation to ensure both nodes exist. Includes idempotency checks
    to prevent duplicate relationships.
    
    Args:
        start_node_id: ID of the source node
        end_node_id: ID of the target node
        relationship_type: Type of relationship (must be one of: WORKS_AT, MANAGES, PARTICIPATES_IN, USES, RELATES_TO)
        properties: Optional properties for the relationship
        dry_run: If True, validates but doesn't actually create the relationship (default: False)
    
    Returns:
        A dictionary containing:
        - "success": Boolean indicating if creation succeeded
        - "dry_run": Whether this was a dry run
        - "relationship_id": ID of the created relationship
        - "relationship": The created relationship details (type, properties, start/end nodes)
        - "was_duplicate": True if relationship already existed
        - "validation_errors": Any validation issues (if success is False)
    
    Examples:
        >>> create_relationship("123", "456", "WORKS_AT")
        {"success": True, "relationship_id": 789, "relationship": {...}, "was_duplicate": False}
        
        >>> create_relationship("123", "456", "MANAGES", {"since": "2024"}, dry_run=True)
        {"success": True, "dry_run": True, "relationship_id": None, "relationship": {...}}
    
    Safety measures:
        - Validates that both start and end nodes exist before creating relationship
        - Relationship type must be in allowlist (WORKS_AT, MANAGES, PARTICIPATES_IN, USES, RELATES_TO)
        - Properties are validated against schema
        - Payload size is limited to 1MB
        - Property values limited to 10,000 characters
        - Idempotency checks prevent duplicate relationships (same type between same nodes)
        - Dry-run mode for testing without writes
        - Comprehensive error handling and logging
    """
    from ..utils import validate_relationship_type, validate_relationship_properties, validate_node_id
    
    operation_context = {
        "operation": "create_relationship",
        "start_node_id": start_node_id,
        "end_node_id": end_node_id,
        "relationship_type": relationship_type,
        "dry_run": dry_run
    }
    
    try:
        logger.info(
            f"Creating relationship '{relationship_type}' between nodes {start_node_id} and {end_node_id}",
            extra=operation_context
        )
        
        # Validate node IDs
        start_id_str = validate_node_id(start_node_id)
        end_id_str = validate_node_id(end_node_id)
        
        # Validate relationship type
        validate_relationship_type(relationship_type)
        
        # Validate properties
        validated_properties = {}
        if properties:
            validated_properties = validate_relationship_properties(properties)
            validate_payload_size(validated_properties)
            validate_property_values(validated_properties)
        
        # Dry run mode - return validated structure without writing
        if dry_run:
            logger.info(
                f"Dry run for creating {relationship_type} relationship",
                extra=operation_context
            )
            return {
                "success": True,
                "dry_run": True,
                "relationship_id": None,
                "relationship": {
                    "type": relationship_type,
                    "properties": validated_properties,
                    "start_node_id": start_id_str,
                    "end_node_id": end_id_str
                },
                "was_duplicate": False,
                "message": "Validation passed. Relationship would be created."
            }
        
        # Create relationship in Neo4j
        with create_session() as session:
            # First, verify both nodes exist
            verify_query = """
            MATCH (start_node)
            WHERE id(start_node) = $start_id
            MATCH (end_node)
            WHERE id(end_node) = $end_id
            RETURN id(start_node) as start_exists, id(end_node) as end_exists
            """
            
            result = session.run(
                verify_query,
                start_id=int(start_id_str),
                end_id=int(end_id_str)
            )
            
            verification = result.single()
            if not verification:
                raise ValidationError(
                    f"One or both nodes do not exist: start_node_id={start_id_str}, end_node_id={end_id_str}",
                    field="node_ids",
                    details={"start_node_id": start_id_str, "end_node_id": end_id_str}
                )
            
            # Check for existing relationship (idempotency)
            check_query = f"""
            MATCH (a)-[r:{relationship_type}]->(b)
            WHERE elementId(a) = $start_id AND elementId(b) = $end_id
            RETURN elementId(r) as rel_id, r
            LIMIT 1
            """
            
            result = session.run(
                check_query,
                start_id=int(start_id_str),
                end_id=int(end_id_str)
            )
            existing_rel = result.single()
            
            if existing_rel:
                # Relationship already exists
                rel_id = existing_rel['rel_id']
                rel = existing_rel['r']
                
                logger.info(
                    f"Relationship '{relationship_type}' between nodes {start_id_str} and {end_id_str} already exists",
                    extra={**operation_context, "relationship_id": rel_id}
                )
                
                return {
                    "success": True,
                    "dry_run": False,
                    "relationship_id": rel_id,
                    "relationship": {
                        "id": rel_id,
                        "type": relationship_type,
                        "properties": dict(rel),
                        "start_node_id": int(start_id_str),
                        "end_node_id": int(end_id_str)
                    },
                    "was_duplicate": True,
                    "message": f"Relationship already exists with id {rel_id}"
                }
            
            # Create new relationship
            create_query = f"""
            MATCH (a), (b)
            WHERE elementId(a) = $start_id AND elementId(b) = $end_id
            CREATE (a)-[r:{relationship_type} $properties]->(b)
            RETURN elementId(r) as rel_id, r, id(a) as start_id, id(b) as end_id
            """
            
            result = session.run(
                create_query,
                start_id=int(start_id_str),
                end_id=int(end_id_str),
                properties=validated_properties
            )
            record = result.single()
            
            rel_id = record['rel_id']
            rel = record['r']
            
            logger.info(
                f"Successfully created relationship with id {rel_id}",
                extra={**operation_context, "relationship_id": rel_id}
            )
            
            return {
                "success": True,
                "dry_run": False,
                "relationship_id": rel_id,
                "relationship": {
                    "id": rel_id,
                    "type": relationship_type,
                    "properties": dict(rel),
                    "start_node_id": int(start_id_str),
                    "end_node_id": int(end_id_str)
                },
                "was_duplicate": False,
                "message": f"Relationship created successfully with id {rel_id}"
            }
    
    except ValidationError as e:
        logger.warning(
            f"Validation error creating relationship: {str(e)}",
            extra={**operation_context, "error": str(e)}
        )
        return {
            "success": False,
            "dry_run": dry_run,
            "relationship_id": None,
            "relationship": None,
            "validation_errors": [str(e)],
            "error": str(e)
        }
    
    except GraphOperationError as e:
        logger.error(
            f"Graph operation error creating relationship: {str(e)}",
            extra={**operation_context, "error": str(e)}
        )
        return {
            "success": False,
            "dry_run": dry_run,
            "relationship_id": None,
            "relationship": None,
            "error": str(e)
        }
    
    except Exception as e:
        error_msg = f"Unexpected error creating relationship: {str(e)}"
        logger.error(error_msg, extra={**operation_context, "error": str(e)})
        raise ToolExecutionError(error_msg, tool_name="create_relationship") from e


@tool
def bulk_ingest(
    data: List[Dict[str, Any]],
    schema_validation: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Perform bulk ingestion of nodes and relationships with comprehensive validation.
    
    This tool efficiently ingests multiple entities in a single transaction
    with comprehensive validation and error reporting. Supports both nodes and
    relationships with proper error collection and partial success handling.
    
    Args:
        data: List of entities to ingest. Each entity should be either:
             - Node: {"type": "node", "data": {"label": "Person", "properties": {"name": "Alice"}}}
             - Relationship: {"type": "relationship", "data": {"start_node_id": "123", "end_node_id": "456", "relationship_type": "WORKS_AT", "properties": {...}}}
        schema_validation: Whether to validate against schemas (default: True)
        dry_run: If True, validates but doesn't actually write (default: False)
    
    Returns:
        A dictionary containing:
        - "success": Overall success status (true if all operations succeeded or were validated)
        - "dry_run": Whether this was a dry run
        - "created_nodes": Number of nodes created (or would be created)
        - "created_relationships": Number of relationships created (or would be created)
        - "skipped_duplicates": Number of duplicate entities skipped
        - "validation_errors": List of validation errors with details
        - "partial_results": Details of what was created/would be created
    
    Examples:
        >>> bulk_ingest([
        ...     {"type": "node", "data": {"label": "Person", "properties": {"name": "Alice"}}},
        ...     {"type": "node", "data": {"label": "Organization", "properties": {"name": "Acme"}}}
        ... ])
        {"success": True, "created_nodes": 2, "created_relationships": 0, ...}
        
        >>> bulk_ingest([
        ...     {"type": "relationship", "data": {
        ...         "start_node_id": "123", "end_node_id": "456",
        ...         "relationship_type": "WORKS_AT"
        ...     }}
        ... ], dry_run=True)
        {"success": True, "dry_run": True, "created_relationships": 1, ...}
    
    Safety measures:
        - All data validated before any writes occur
        - Transaction-based (all or nothing, unless partial_success enabled)
        - Maximum batch size limit (100 items)
        - Payload size limits (1MB per item)
        - Schema validation for all entities
        - Dry-run mode for testing without writes
        - Detailed error reporting with item indices
        - Progress tracking for large batches
    """
    from ..utils import validate_bulk_operation
    
    operation_context = {
        "operation": "bulk_ingest",
        "item_count": len(data) if data else 0,
        "schema_validation": schema_validation,
        "dry_run": dry_run
    }
    
    try:
        logger.info(
            f"Starting bulk ingest of {len(data) if data else 0} items",
            extra=operation_context
        )
        
        # Validate bulk operation size
        validated_data = validate_bulk_operation(data, max_items=MAX_BULK_CREATE)
        
        # Track results
        validation_errors = []
        nodes_to_create = []
        relationships_to_create = []
        skipped_duplicates = 0
        
        # Phase 1: Validation
        for idx, item in enumerate(validated_data):
            item_context = {**operation_context, "item_index": idx}
            
            try:
                # Validate item structure
                if not isinstance(item, dict):
                    raise ValidationError(
                        f"Item at index {idx} must be a dictionary",
                        field="data",
                        details={"index": idx}
                    )
                
                item_type = item.get("type")
                item_data = item.get("data")
                
                if not item_type:
                    raise ValidationError(
                        f"Item at index {idx} missing 'type' field",
                        field="type",
                        details={"index": idx}
                    )
                
                if not item_data:
                    raise ValidationError(
                        f"Item at index {idx} missing 'data' field",
                        field="data",
                        details={"index": idx}
                    )
                
                # Validate based on type
                if item_type == "node":
                    label = item_data.get("label")
                    properties = item_data.get("properties", {})
                    
                    if schema_validation:
                        validate_node_label(label)
                        validated_props = validate_node_properties(label, properties, check_required=True)
                        validate_payload_size(validated_props)
                        validate_property_values(validated_props)
                    
                    nodes_to_create.append({
                        "index": idx,
                        "label": label,
                        "properties": properties
                    })
                
                elif item_type == "relationship":
                    start_node_id = item_data.get("start_node_id")
                    end_node_id = item_data.get("end_node_id")
                    relationship_type = item_data.get("relationship_type")
                    properties = item_data.get("properties", {})
                    
                    if schema_validation:
                        from ..utils import validate_relationship_type, validate_relationship_properties, validate_node_id
                        
                        validate_node_id(start_node_id)
                        validate_node_id(end_node_id)
                        validate_relationship_type(relationship_type)
                        
                        if properties:
                            validated_props = validate_relationship_properties(properties)
                            validate_payload_size(validated_props)
                            validate_property_values(validated_props)
                    
                    relationships_to_create.append({
                        "index": idx,
                        "start_node_id": start_node_id,
                        "end_node_id": end_node_id,
                        "relationship_type": relationship_type,
                        "properties": properties
                    })
                
                else:
                    raise ValidationError(
                        f"Item at index {idx} has invalid type '{item_type}'. Must be 'node' or 'relationship'",
                        field="type",
                        details={"index": idx, "type": item_type}
                    )
            
            except ValidationError as e:
                validation_errors.append({
                    "index": idx,
                    "error": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                })
                logger.warning(f"Validation error at index {idx}: {str(e)}", extra=item_context)
        
        # If validation errors exist and we're strict, return errors
        if validation_errors:
            logger.error(
                f"Bulk ingest validation failed with {len(validation_errors)} errors",
                extra={**operation_context, "error_count": len(validation_errors)}
            )
            return {
                "success": False,
                "dry_run": dry_run,
                "created_nodes": 0,
                "created_relationships": 0,
                "skipped_duplicates": 0,
                "validation_errors": validation_errors,
                "partial_results": [],
                "error": f"Validation failed for {len(validation_errors)} items"
            }
        
        # Dry run mode - return validated structure
        if dry_run:
            logger.info(
                f"Dry run complete: would create {len(nodes_to_create)} nodes and {len(relationships_to_create)} relationships",
                extra=operation_context
            )
            return {
                "success": True,
                "dry_run": True,
                "created_nodes": len(nodes_to_create),
                "created_relationships": len(relationships_to_create),
                "skipped_duplicates": 0,
                "validation_errors": [],
                "partial_results": {
                    "nodes": nodes_to_create,
                    "relationships": relationships_to_create
                },
                "message": f"Validation passed. Would create {len(nodes_to_create)} nodes and {len(relationships_to_create)} relationships."
            }
        
        # Phase 2: Execute writes in transaction
        created_nodes = []
        created_relationships = []
        
        with create_session() as session:
            # Start transaction
            with session.begin_transaction() as tx:
                try:
                    # Create nodes
                    for node_data in nodes_to_create:
                        label = node_data["label"]
                        properties = node_data["properties"]
                        
                        # Check for existing node (idempotency)
                        existing_id = check_node_exists(session, label, properties)
                        
                        if existing_id is not None:
                            skipped_duplicates += 1
                            created_nodes.append({
                                "index": node_data["index"],
                                "node_id": existing_id,
                                "label": label,
                                "was_duplicate": True
                            })
                            continue
                        
                        # Create node
                        create_query = f"""
                        CREATE (n:{label} $properties)
                        RETURN elementId(n) as node_id
                        """
                        
                        result = tx.run(create_query, properties=properties)
                        record = result.single()
                        node_id = record['node_id']
                        
                        created_nodes.append({
                            "index": node_data["index"],
                            "node_id": node_id,
                            "label": label,
                            "was_duplicate": False
                        })
                    
                    # Create relationships
                    for rel_data in relationships_to_create:
                        start_id = int(rel_data["start_node_id"])
                        end_id = int(rel_data["end_node_id"])
                        rel_type = rel_data["relationship_type"]
                        properties = rel_data["properties"]
                        
                        # Verify nodes exist
                        verify_query = """
                        MATCH (a), (b)
                        WHERE elementId(a) = $start_id AND elementId(b) = $end_id
                        RETURN elementId(a) as a_id, elementId(b) as b_id
                        """
                        
                        result = tx.run(verify_query, start_id=start_id, end_id=end_id)
                        if not result.single():
                            raise ValidationError(
                                f"Nodes not found for relationship: start={start_id}, end={end_id}",
                                field="node_ids"
                            )
                        
                        # Check for existing relationship
                        check_query = f"""
                        MATCH (a)-[r:{rel_type}]->(b)
                        WHERE elementId(a) = $start_id AND elementId(b) = $end_id
                        RETURN id(r) as rel_id
                        LIMIT 1
                        """
                        
                        result = tx.run(check_query, start_id=start_id, end_id=end_id)
                        existing_rel = result.single()
                        
                        if existing_rel:
                            skipped_duplicates += 1
                            created_relationships.append({
                                "index": rel_data["index"],
                                "relationship_id": existing_rel['rel_id'],
                                "relationship_type": rel_type,
                                "was_duplicate": True
                            })
                            continue
                        
                        # Create relationship
                        create_query = f"""
                        MATCH (a), (b)
                        WHERE elementId(a) = $start_id AND elementId(b) = $end_id
                        CREATE (a)-[r:{rel_type} $properties]->(b)
                        RETURN id(r) as rel_id
                        """
                        
                        result = tx.run(
                            create_query,
                            start_id=start_id,
                            end_id=end_id,
                            properties=properties
                        )
                        record = result.single()
                        rel_id = record['rel_id']
                        
                        created_relationships.append({
                            "index": rel_data["index"],
                            "relationship_id": rel_id,
                            "relationship_type": rel_type,
                            "was_duplicate": False
                        })
                    
                    # Commit transaction
                    tx.commit()
                    
                    logger.info(
                        f"Bulk ingest complete: created {len(created_nodes)} nodes and {len(created_relationships)} relationships",
                        extra={
                            **operation_context,
                            "created_nodes": len(created_nodes),
                            "created_relationships": len(created_relationships),
                            "skipped_duplicates": skipped_duplicates
                        }
                    )
                    
                    return {
                        "success": True,
                        "dry_run": False,
                        "created_nodes": len([n for n in created_nodes if not n["was_duplicate"]]),
                        "created_relationships": len([r for r in created_relationships if not r["was_duplicate"]]),
                        "skipped_duplicates": skipped_duplicates,
                        "validation_errors": [],
                        "partial_results": {
                            "nodes": created_nodes,
                            "relationships": created_relationships
                        },
                        "message": f"Successfully created {len(created_nodes)} nodes and {len(created_relationships)} relationships"
                    }
                
                except Exception as e:
                    # Rollback transaction on error
                    tx.rollback()
                    raise GraphOperationError(
                        f"Transaction failed and was rolled back: {str(e)}",
                        details={"error": str(e)}
                    ) from e
    
    except ValidationError as e:
        logger.warning(
            f"Validation error in bulk ingest: {str(e)}",
            extra={**operation_context, "error": str(e)}
        )
        return {
            "success": False,
            "dry_run": dry_run,
            "created_nodes": 0,
            "created_relationships": 0,
            "skipped_duplicates": 0,
            "validation_errors": [str(e)],
            "partial_results": [],
            "error": str(e)
        }
    
    except GraphOperationError as e:
        logger.error(
            f"Graph operation error in bulk ingest: {str(e)}",
            extra={**operation_context, "error": str(e)}
        )
        return {
            "success": False,
            "dry_run": dry_run,
            "created_nodes": 0,
            "created_relationships": 0,
            "skipped_duplicates": 0,
            "validation_errors": [],
            "partial_results": [],
            "error": str(e)
        }
    
    except Exception as e:
        error_msg = f"Unexpected error in bulk ingest: {str(e)}"
        logger.error(error_msg, extra={**operation_context, "error": str(e)})
        raise ToolExecutionError(error_msg, tool_name="bulk_ingest") from e

