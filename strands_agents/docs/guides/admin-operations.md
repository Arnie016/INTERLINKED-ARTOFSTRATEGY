# Admin Operations Guide

## Overview

This guide documents the administrative tools and operations available for maintaining and managing the Neo4j graph database. All admin operations require elevated privileges and include comprehensive safety measures, audit logging, and dry-run capabilities.

## Table of Contents

1. [Role-Based Access Control](#role-based-access-control)
2. [Admin Tools](#admin-tools)
   - [Reindex Operations](#reindex-operations)
   - [Label Migration](#label-migration)
   - [Orphan Node Cleanup](#orphan-node-cleanup)
3. [Safety Measures](#safety-measures)
4. [Audit Logging](#audit-logging)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Role-Based Access Control

### Overview

All administrative operations are protected by a comprehensive Role-Based Access Control (RBAC) system that ensures only authorized users can perform privileged operations.

### Authentication Requirements

Every admin operation requires:
- **Valid Authentication Context**: User must be authenticated with a valid token
- **Admin Role**: User must have the `admin` role assigned
- **Specific Permissions**: Each operation checks for specific permissions (e.g., `REINDEX`, `MANAGE_SCHEMA`, `ADMIN_OPERATIONS`)

### RBAC Decorators

Two decorators are available for protecting admin operations:

#### `@require_admin_role`

Convenience decorator for operations requiring admin privileges:

```python
from src.utils import require_admin_role, AuthContext

@require_admin_role
def sensitive_operation(auth: AuthContext, **kwargs):
    """Admin-only operation."""
    return {"success": True}
```

#### `@require_role_decorator(role, permissions)`

Flexible decorator factory for custom role/permission requirements:

```python
from src.utils import require_role_decorator, Role, Permission

@require_role_decorator(Role.ADMIN, [Permission.MANAGE_SCHEMA])
def schema_operation(auth: AuthContext, **kwargs):
    """Operation requiring admin role and schema management permission."""
    return {"success": True}
```

### Authorization Flow

1. Decorator extracts `auth` from function kwargs
2. Validates auth context exists (raises `AuthenticationError` if missing)
3. Checks role requirement (admin role has access to all operations)
4. Validates specific permissions if provided
5. Executes function if all checks pass
6. Logs authorization failures with detailed context

### Error Handling

- **AuthenticationError**: Raised when auth context is missing
- **AuthorizationError**: Raised when user lacks required role or permissions
- All errors include detailed context for debugging and audit purposes

---

## Admin Tools

### Reindex Operations

#### Purpose

Create or rebuild indexes on node labels and properties to improve query performance.

#### Function Signature

```python
def reindex(
    label: str,
    property: str,
    dry_run: bool = True,
    confirm: bool = False,
    auth: Optional[AuthContext] = None
) -> Dict[str, Any]
```

#### Parameters

- **label** (str, required): The node label to index (e.g., "Person")
- **property** (str, required): The property to index (e.g., "name", "email")
- **dry_run** (bool, default: True): If True, shows preview without executing
- **confirm** (bool, default: False): Explicit confirmation for execution
- **auth** (AuthContext, required): Authentication context with admin role

#### Safety Features

- **Size Limit**: Maximum 100,000 nodes per reindex operation
- **Dry-Run Default**: Operations default to dry-run mode
- **Explicit Confirmation**: Requires both `dry_run=False` and `confirm=True` for execution
- **Duplicate Detection**: Checks if index already exists
- **Execution Monitoring**: Tracks and reports execution time

#### Usage Examples

**Preview (Dry Run):**
```python
from src.utils import AuthContext, Role
from src.tools.graph_admin import reindex

# Create admin auth context
admin_auth = AuthContext(
    user_id="admin-123",
    username="alice",
    role=Role.ADMIN
)

# Preview index creation
result = reindex(
    label="Person",
    property="email",
    dry_run=True,
    auth=admin_auth
)

print(f"Would affect {result['affected_nodes']} nodes")
print(f"Estimated time: {result['estimated_creation_time_ms']}ms")
```

**Execute:**
```python
# Create index (requires confirmation)
result = reindex(
    label="Person",
    property="email",
    dry_run=False,
    confirm=True,
    auth=admin_auth
)

print(f"Index '{result['index_name']}' created successfully")
print(f"Execution time: {result['execution_time_ms']}ms")
```

#### Response Format

**Dry Run Response:**
```json
{
    "success": true,
    "dry_run": true,
    "label": "Person",
    "property": "email",
    "affected_nodes": 15000,
    "nodes_with_property": 14950,
    "execution_time_ms": 45.23,
    "index_name": "index_person_email",
    "already_exists": false,
    "estimated_creation_time_ms": 1500.0,
    "preview": {
        "action": "CREATE INDEX",
        "index_name": "index_person_email",
        "index_for": "Person(email)",
        "affected_nodes": 15000,
        "nodes_missing_property": 50
    }
}
```

**Execution Response:**
```json
{
    "success": true,
    "dry_run": false,
    "label": "Person",
    "property": "email",
    "affected_nodes": 15000,
    "execution_time_ms": 1234.56,
    "index_name": "index_person_email",
    "already_exists": false,
    "message": "Reindexing operation started"
}
```

#### Error Scenarios

- **Label/Property Missing**: Validation error if label or property is empty
- **Node Count Exceeded**: Operation blocked if nodes > 100,000
- **Missing Confirmation**: Validation error if `dry_run=False` but `confirm=False`
- **Unauthorized**: Authorization error if user is not admin

---

### Label Migration

#### Purpose

Migrate nodes from one label to another, useful for schema evolution and refactoring.

#### Function Signature

```python
def migrate_labels(
    old_label: str,
    new_label: str,
    dry_run: bool = True,
    confirm: bool = False,
    auth: Optional[AuthContext] = None
) -> Dict[str, Any]
```

#### Parameters

- **old_label** (str, required): Current label to migrate from
- **new_label** (str, required): New label to migrate to
- **dry_run** (bool, default: True): If True, previews changes without executing
- **confirm** (bool, default: False): Explicit confirmation for execution
- **auth** (AuthContext, required): Authentication context with admin role

#### Safety Features

- **Size Limit**: Maximum 10,000 nodes per migration operation
- **Transaction-Based**: All operations in a transaction with rollback on error
- **Batch Processing**: Processes nodes in batches of 100 for efficiency
- **Operation Timeout**: 300-second maximum execution time
- **Label Validation**: Prevents migration between identical labels
- **Sample Preview**: Shows sample nodes before migration
- **Progress Tracking**: Logs progress after each batch

#### Usage Examples

**Preview (Dry Run):**
```python
from src.utils import AuthContext, Role
from src.tools.graph_admin import migrate_labels

admin_auth = AuthContext(
    user_id="admin-123",
    username="alice",
    role=Role.ADMIN
)

# Preview migration
result = migrate_labels(
    old_label="Employee",
    new_label="Person",
    dry_run=True,
    auth=admin_auth
)

print(f"Would migrate {result['affected_nodes']} nodes")
print(f"Sample nodes: {result['preview']['sample_nodes']}")
```

**Execute:**
```python
# Execute migration (requires confirmation)
result = migrate_labels(
    old_label="Employee",
    new_label="Person",
    dry_run=False,
    confirm=True,
    auth=admin_auth
)

print(f"Migrated {result['affected_nodes']} nodes")
print(f"Processed in {result['batches_processed']} batches")
print(f"Execution time: {result['execution_time_ms']}ms")
```

#### Response Format

**Dry Run Response:**
```json
{
    "success": true,
    "dry_run": true,
    "old_label": "Employee",
    "new_label": "Person",
    "affected_nodes": 5000,
    "execution_time_ms": 234.56,
    "estimated_batches": 50,
    "estimated_execution_time_ms": 50000.0,
    "rollback_available": true,
    "preview": {
        "action": "REMOVE old label, SET new label",
        "affected_nodes": 5000,
        "sample_nodes": [
            {
                "id": 123,
                "labels": ["Employee"],
                "properties": {"name": "John Doe", "department": "Engineering"}
            }
        ],
        "migration_steps": [
            "1. Remove label 'Employee' from 5000 nodes",
            "2. Add label 'Person' to 5000 nodes",
            "3. Process in 50 batches of 100 nodes"
        ]
    }
}
```

**Execution Response:**
```json
{
    "success": true,
    "dry_run": false,
    "old_label": "Employee",
    "new_label": "Person",
    "affected_nodes": 5000,
    "execution_time_ms": 45678.90,
    "batches_processed": 50,
    "rollback_available": false,
    "message": "Successfully migrated 5000 nodes from 'Employee' to 'Person'"
}
```

#### Error Scenarios

- **Invalid Labels**: Validation error if labels are empty or identical
- **Node Count Exceeded**: Operation blocked if nodes > 10,000
- **Timeout**: Operation rolled back if execution exceeds 300 seconds
- **Transaction Error**: Automatic rollback with detailed error message
- **Missing Confirmation**: Validation error if execution requested without confirmation

---

### Orphan Node Cleanup

#### Purpose

Identify and remove orphaned nodes (nodes with no relationships) to maintain database health and reduce storage.

#### Function Signature

```python
def maintenance_cleanup_orphan_nodes(
    dry_run: bool = True,
    confirm: bool = False,
    max_delete: int = 1000,
    auth: Optional[AuthContext] = None
) -> Dict[str, Any]
```

#### Parameters

- **dry_run** (bool, default: True): If True, identifies orphans without deleting
- **confirm** (bool, default: False): Explicit confirmation for deletion
- **max_delete** (int, default: 1000): Maximum number of orphans to delete
- **auth** (AuthContext, required): Authentication context with admin role

#### Safety Features

- **Size Limit**: Configurable maximum deletion (default: 1,000 nodes)
- **Batch Processing**: Deletes nodes in batches of 100
- **Operation Timeout**: 300-second maximum execution time
- **Statistics by Label**: Provides breakdown of orphans by label
- **Recommendations**: Intelligent suggestions based on orphan patterns
- **Sample Review**: Shows sample orphans for review before deletion
- **Progress Tracking**: Logs progress after each batch

#### Usage Examples

**Identify Orphans (Dry Run):**
```python
from src.utils import AuthContext, Role
from src.tools.graph_admin import maintenance_cleanup_orphan_nodes

admin_auth = AuthContext(
    user_id="admin-123",
    username="alice",
    role=Role.ADMIN
)

# Identify orphans
result = maintenance_cleanup_orphan_nodes(
    dry_run=True,
    auth=admin_auth
)

print(f"Found {result['orphaned_nodes_found']} orphaned nodes")
print("Breakdown by label:")
for detail in result['orphan_details']:
    print(f"  {detail['labels']}: {detail['count']} nodes")

print("\nRecommendations:")
for rec in result['recommendations']:
    print(f"  - {rec}")
```

**Delete Orphans:**
```python
# Delete orphans (requires confirmation)
result = maintenance_cleanup_orphan_nodes(
    dry_run=False,
    confirm=True,
    max_delete=500,  # Custom limit
    auth=admin_auth
)

print(f"Deleted {result['orphaned_nodes_deleted']} orphaned nodes")
print(f"Remaining: {result['orphaned_nodes_remaining']}")
print(f"Processed in {result['batches_processed']} batches")
```

#### Response Format

**Dry Run Response:**
```json
{
    "success": true,
    "dry_run": true,
    "orphaned_nodes_found": 1250,
    "orphaned_nodes_to_delete": 1000,
    "orphaned_nodes_deleted": 0,
    "execution_time_ms": 456.78,
    "estimated_batches": 10,
    "estimated_deletion_time_ms": 5000.0,
    "orphan_details": [
        {"labels": "Resource", "count": 800},
        {"labels": "Technology", "count": 350},
        {"labels": "NO_LABEL", "count": 100}
    ],
    "sample_orphans": [
        {
            "id": 456,
            "labels": ["Resource"],
            "properties": {"name": "Old Resource", "status": "inactive"}
        }
    ],
    "recommendations": [
        "Large number of orphans detected - investigate data quality processes",
        "Found nodes without labels - consider adding labels or removing",
        "Review sample orphans to understand why they exist before deletion"
    ],
    "preview": {
        "action": "DELETE orphaned nodes",
        "total_orphans": 1250,
        "will_delete": 1000,
        "will_remain": 250
    }
}
```

**Execution Response:**
```json
{
    "success": true,
    "dry_run": false,
    "orphaned_nodes_found": 1250,
    "orphaned_nodes_deleted": 1000,
    "orphaned_nodes_remaining": 250,
    "execution_time_ms": 4567.89,
    "batches_processed": 10,
    "orphan_details": [
        {"labels": "Resource", "count": 800},
        {"labels": "Technology", "count": 350},
        {"labels": "NO_LABEL", "count": 100}
    ],
    "message": "Successfully deleted 1000 orphaned nodes"
}
```

#### Error Scenarios

- **Invalid max_delete**: Validation error if value < 1 or > 1000
- **Timeout**: Operation stopped if execution exceeds 300 seconds
- **Missing Confirmation**: Validation error if deletion requested without confirmation
- **Deletion Error**: Detailed error with count of nodes deleted before failure

---

## Safety Measures

### Universal Safety Features

All admin operations implement comprehensive safety measures:

#### 1. Authentication & Authorization

- **Required Auth Context**: All operations require authenticated user
- **Admin Role Required**: Only users with admin role can execute
- **Permission Checks**: Each operation validates specific permissions
- **Detailed Error Messages**: Authorization failures include full context

#### 2. Dry-Run Mode

- **Default to Dry-Run**: All destructive operations default to `dry_run=True`
- **Preview Output**: Shows what would happen without making changes
- **Execution Estimates**: Provides time and resource estimates
- **Sample Data**: Includes sample records for review

#### 3. Explicit Confirmation

- **Double-Check Required**: Must set both `dry_run=False` and `confirm=True`
- **Prevents Accidents**: Reduces risk of unintended destructive operations
- **Validation Errors**: Clear error if confirmation missing

#### 4. Size Limits

Each operation has appropriate size limits:
- **Reindex**: 100,000 nodes maximum
- **Label Migration**: 10,000 nodes maximum
- **Orphan Cleanup**: 1,000 nodes default (configurable)

#### 5. Batch Processing

- **Efficient Handling**: Large operations processed in batches
- **Batch Size**: 100 nodes per batch (optimal for Neo4j)
- **Progress Tracking**: Per-batch logging
- **Interruptible**: Operations can be stopped between batches

#### 6. Timeout Protection

- **Maximum Duration**: 300 seconds (5 minutes) per operation
- **Automatic Termination**: Operations stopped if timeout exceeded
- **Graceful Handling**: Rollback or partial results on timeout
- **Progress Saved**: Records work completed before timeout

#### 7. Transaction Safety

- **ACID Compliance**: Label migration uses transactions
- **Automatic Rollback**: Failed operations rolled back automatically
- **Data Consistency**: Database always left in consistent state
- **Error Recovery**: Detailed error messages for debugging

#### 8. Validation

- **Input Validation**: All parameters validated before execution
- **Type Checking**: Proper type validation with error messages
- **Business Logic**: Label validation, node existence checks, etc.
- **Early Failure**: Validation errors raised before any database operations

---

## Audit Logging

### Overview

All admin operations include comprehensive audit logging for accountability, compliance, and troubleshooting.

### Logged Information

Each admin operation logs:

#### Operation Context
- **Operation Type**: reindex, migrate_labels, cleanup_orphans
- **User Information**: user_id, username, role
- **Timestamp**: Automatic ISO 8601 timestamp
- **Parameters**: All operation parameters
- **Dry-Run Status**: Whether this was a preview or execution
- **Confirmation Status**: Whether explicit confirmation was provided

#### Execution Details
- **Affected Resources**: Node counts, labels, properties
- **Execution Metrics**: Time, batches processed
- **Success/Failure**: Operation outcome
- **Error Details**: Full context if operation failed

#### Progress Tracking
- **Batch Progress**: Logged after each batch
- **Intermediate Counts**: Running totals
- **Performance Metrics**: Per-batch timing

### Log Levels

- **INFO**: Operation initiation, success, progress
- **WARNING**: Timeout approaching, rollback executed
- **ERROR**: Operation failures, validation errors

### Example Log Entries

**Operation Initiation:**
```
INFO: Admin reindex operation initiated by alice
  extra: {
    "operation": "reindex",
    "user": {"user_id": "admin-123", "username": "alice", "role": "admin"},
    "label": "Person",
    "property": "email",
    "dry_run": false,
    "confirm": true
  }
```

**Batch Progress:**
```
INFO: Processed batch 5: 100 nodes
  extra: {
    "operation": "migrate_labels",
    "batch": 5,
    "migrated": 500,
    "old_label": "Employee",
    "new_label": "Person"
  }
```

**Operation Success:**
```
INFO: Index created successfully by alice
  extra: {
    "operation": "reindex",
    "affected_nodes": 15000,
    "execution_time_ms": 2341.5,
    "index_name": "index_person_email"
  }
```

**Operation Failure:**
```
ERROR: Label migration failed: Transaction timeout
  extra: {
    "operation": "migrate_labels",
    "migrated_before_error": 800,
    "total": 5000,
    "old_label": "Employee",
    "new_label": "Person"
  }
  exc_info: <traceback>
```

### Integration with AgentCore Observability

- **Structured Logging**: CloudWatch-compatible JSON format
- **Extra Context**: All logs include operation context
- **Exception Info**: Full tracebacks for errors
- **Metrics**: Performance metrics automatically captured
- **Tracing**: Integration with X-Ray for distributed tracing

### Compliance & Security

- **PII Protection**: No sensitive data logged (tokens excluded)
- **User Context Sanitized**: Via `get_user_context_for_logging()`
- **SIEM Compatible**: Structured format for security tools
- **Complete Accountability**: Who, what, when, why, how, result
- **Retention Policies**: Configured via CloudWatch settings

### Querying Audit Logs

**CloudWatch Insights Queries:**

Find all admin operations by user:
```
fields @timestamp, operation, affected_nodes, execution_time_ms
| filter user.username = "alice"
| sort @timestamp desc
```

Find failed operations:
```
fields @timestamp, operation, @message
| filter success = false
| sort @timestamp desc
```

Performance analysis:
```
fields operation, avg(execution_time_ms) as avg_time, max(execution_time_ms) as max_time
| stats count() by operation
```

---

## Best Practices

### General Guidelines

1. **Always Start with Dry-Run**
   - Never execute destructive operations without previewing first
   - Review dry-run output carefully before confirming execution
   - Validate affected node counts match expectations

2. **Use Appropriate Batch Sizes**
   - Default batch size (100) is optimal for most operations
   - Larger batches risk timeouts
   - Smaller batches increase overhead

3. **Monitor Execution Time**
   - Review estimated execution time in dry-run
   - Large operations may need to be split
   - Consider off-peak hours for long operations

4. **Review Audit Logs**
   - Check logs after significant operations
   - Monitor for unexpected patterns
   - Use logs for performance tuning

5. **Test in Development First**
   - Always test admin operations in dev environment
   - Validate on representative data sets
   - Confirm rollback procedures work

### Specific Recommendations

#### Reindex Operations

- **Timing**: Run during low-traffic periods
- **Frequency**: Only when query performance degrades
- **Monitoring**: Track query performance before and after
- **Validation**: Verify index is being used in query plans

#### Label Migration

- **Planning**: Document migration plan before execution
- **Validation**: Verify no dependent code uses old label
- **Testing**: Test in staging with production-like data
- **Rollback**: Keep rollback procedure documented
- **Communication**: Notify team before major migrations

#### Orphan Cleanup

- **Investigation**: Always review orphans before deletion
- **Root Cause**: Identify why orphans exist
- **Incremental**: Delete in small batches first
- **Verification**: Check application logs for related errors
- **Prevention**: Fix data quality issues causing orphans

### Error Recovery

1. **Operation Failed Mid-Execution**
   - Review audit logs for partial progress
   - For label migration, transaction auto-rollback occurs
   - For orphan cleanup, check deleted vs remaining counts
   - Re-run with updated parameters if needed

2. **Timeout Occurred**
   - Review batch progress in logs
   - Split operation into smaller chunks
   - Increase timeout if appropriate
   - Consider off-peak timing

3. **Permission Denied**
   - Verify user has admin role
   - Check specific permissions required
   - Review auth token validity
   - Contact administrator if needed

---

## Troubleshooting

### Common Issues

#### "Authentication required for admin operations"

**Cause**: Missing auth context parameter

**Solution**:
```python
# Incorrect
result = reindex("Person", "email")

# Correct
admin_auth = AuthContext(user_id="admin-123", role=Role.ADMIN)
result = reindex("Person", "email", auth=admin_auth)
```

#### "Admin role required for this operation"

**Cause**: User does not have admin role

**Solution**:
- Verify user role assignment
- Request admin access from administrator
- Check token contains correct role claim

#### "Explicit confirmation required"

**Cause**: Attempting execution without confirmation

**Solution**:
```python
# Incorrect
result = reindex("Person", "email", dry_run=False)

# Correct
result = reindex("Person", "email", dry_run=False, confirm=True)
```

#### "Cannot reindex X nodes (exceeds maximum of 100000)"

**Cause**: Node count exceeds safety limit

**Solution**:
- Split operation by filtering criteria
- Create separate indexes for subsets
- Contact administrator to increase limit if justified

#### "Migration operation timed out after 300 seconds"

**Cause**: Operation exceeded maximum execution time

**Solution**:
- Reduce batch size in operation
- Split migration into smaller label subsets
- Run during off-peak hours
- Check for Neo4j performance issues

#### "Transaction rolled back due to error"

**Cause**: Error occurred during label migration

**Solution**:
- Review detailed error in logs
- Check database connectivity
- Verify label names are correct
- Ensure sufficient resources available

### Debugging Tips

1. **Enable Detailed Logging**
   ```python
   import logging
   logging.getLogger("src.tools.graph_admin").setLevel(logging.DEBUG)
   ```

2. **Check CloudWatch Logs**
   - Filter by operation name
   - Review execution metrics
   - Check for error patterns

3. **Test with Small Dataset**
   - Use dry-run first
   - Test with subset of data
   - Verify behavior before scaling

4. **Monitor Neo4j Performance**
   - Check database metrics
   - Review query execution plans
   - Verify sufficient resources

5. **Review Sample Data**
   - Always check sample output in dry-run
   - Verify data matches expectations
   - Look for anomalies

### Getting Help

If you encounter issues not covered in this guide:

1. **Review Audit Logs**: Check CloudWatch for detailed error context
2. **Check Neo4j Logs**: Database-level errors may provide additional context
3. **Test in Development**: Reproduce issue in dev environment
4. **Document Scenario**: Include operation parameters, error messages, and logs
5. **Contact Support**: Provide full context from above steps

---

## Appendix

### Configuration Constants

```python
# Admin-specific constants
MAX_REINDEX_NODES = 100000      # Maximum nodes for reindexing
MAX_MIGRATION_NODES = 10000     # Maximum nodes for label migration
MAX_ORPHAN_CLEANUP = 1000       # Maximum orphans to delete in one operation
BATCH_SIZE = 100                # Batch size for bulk operations
OPERATION_TIMEOUT = 300         # 5 minutes max per operation
```

### Required Permissions

```python
from src.utils import Permission

# Permission for reindex operations
Permission.REINDEX = "admin:reindex"

# Permission for label migration
Permission.MANAGE_SCHEMA = "admin:schema"

# Permission for general admin operations
Permission.ADMIN_OPERATIONS = "admin:operations"
```

### Error Types

```python
from src.utils import (
    ValidationError,        # Invalid parameters
    AuthenticationError,    # Missing or invalid auth
    AuthorizationError,     # Insufficient permissions
    GraphQueryError,        # Database query failed
    GraphOperationError,    # Operation-specific error
    ToolExecutionError      # General tool failure
)
```

---

## Version History

- **v1.0.0** (2025-10-17): Initial release of admin operations
  - Reindex operations
  - Label migration with transaction support
  - Orphan node cleanup
  - Comprehensive RBAC and audit logging

