"""
Authentication and Authorization Utilities

Provides utilities for:
- Token validation
- Permission checking
- AgentCore Identity integration
- Role-based access control
"""

from typing import Optional, Dict, Any, List, Set
from enum import Enum
from .errors import AuthenticationError, AuthorizationError


class Role(Enum):
    """User roles with different permission levels."""
    
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class Permission(Enum):
    """Granular permissions for different operations."""
    
    # Read permissions
    READ_GRAPH = "read:graph"
    READ_ANALYTICS = "read:analytics"
    
    # Write permissions
    WRITE_GRAPH = "write:graph"
    CREATE_NODE = "create:node"
    UPDATE_NODE = "update:node"
    DELETE_NODE = "delete:node"
    CREATE_RELATIONSHIP = "create:relationship"
    DELETE_RELATIONSHIP = "delete:relationship"
    
    # Admin permissions
    ADMIN_OPERATIONS = "admin:operations"
    MANAGE_SCHEMA = "admin:schema"
    BULK_IMPORT = "admin:bulk_import"
    REINDEX = "admin:reindex"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.READONLY: {
        Permission.READ_GRAPH,
        Permission.READ_ANALYTICS
    },
    Role.USER: {
        Permission.READ_GRAPH,
        Permission.READ_ANALYTICS,
        Permission.WRITE_GRAPH,
        Permission.CREATE_NODE,
        Permission.UPDATE_NODE,
        Permission.CREATE_RELATIONSHIP
    },
    Role.ADMIN: set(Permission)  # All permissions
}


class AuthContext:
    """
    Authentication context containing user identity and permissions.
    
    This class represents the authenticated user's session and their
    authorized permissions for operations.
    """
    
    def __init__(
        self,
        user_id: str,
        username: Optional[str] = None,
        role: Role = Role.USER,
        custom_permissions: Optional[Set[Permission]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authentication context.
        
        Args:
            user_id: Unique user identifier
            username: Optional username
            role: User role (admin, user, readonly)
            custom_permissions: Optional custom permissions beyond role
            metadata: Additional metadata (session_id, ip_address, etc.)
        """
        self.user_id = user_id
        self.username = username or user_id
        self.role = role
        self.metadata = metadata or {}
        
        # Build permission set
        self.permissions = ROLE_PERMISSIONS.get(role, set())
        if custom_permissions:
            self.permissions.update(custom_permissions)
    
    def has_permission(self, permission: Permission) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            permission: Permission to check
        
        Returns:
            True if user has permission
        """
        return permission in self.permissions
    
    def require_permission(self, permission: Permission):
        """
        Require a specific permission, raise error if not authorized.
        
        Args:
            permission: Required permission
        
        Raises:
            AuthorizationError: If user lacks permission
        """
        if not self.has_permission(permission):
            raise AuthorizationError(
                f"User {self.username} lacks required permission",
                required_permission=permission.value,
                details={
                    "user_id": self.user_id,
                    "user_role": self.role.value,
                    "required_permission": permission.value
                }
            )
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == Role.ADMIN
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role.value,
            "permissions": [p.value for p in self.permissions]
        }


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate authentication token.
    
    Args:
        token: JWT or session token
    
    Returns:
        Dictionary with token claims
    
    Raises:
        AuthenticationError: If token is invalid
    
    Note:
        This is a placeholder implementation. In production, integrate
        with AWS Cognito or AgentCore Identity for real token validation.
    
    Example:
        >>> claims = validate_token("valid-token-123")
        >>> claims['user_id']
        'user-123'
    """
    if not token:
        raise AuthenticationError("Token is required")
    
    # TODO: Implement real token validation with AWS Cognito
    # For now, return mock claims for development
    if token.startswith("admin-"):
        return {
            "user_id": "admin-user",
            "username": "admin",
            "role": "admin",
            "exp": 9999999999
        }
    elif token.startswith("user-"):
        return {
            "user_id": token,
            "username": token.replace("user-", ""),
            "role": "user",
            "exp": 9999999999
        }
    else:
        raise AuthenticationError(
            "Invalid token format",
            details={"token_prefix": token[:10] if len(token) > 10 else token}
        )


def create_auth_context(token: Optional[str] = None) -> AuthContext:
    """
    Create authentication context from token.
    
    Args:
        token: Optional authentication token
    
    Returns:
        AuthContext instance
    
    Raises:
        AuthenticationError: If token is invalid
    
    Example:
        >>> auth = create_auth_context("user-alice")
        >>> auth.username
        'alice'
    """
    if not token:
        # Default to readonly for unauthenticated requests
        return AuthContext(
            user_id="anonymous",
            username="anonymous",
            role=Role.READONLY
        )
    
    # Validate token and extract claims
    claims = validate_token(token)
    
    # Map role string to enum
    role_str = claims.get("role", "user")
    try:
        role = Role(role_str)
    except ValueError:
        role = Role.USER
    
    return AuthContext(
        user_id=claims["user_id"],
        username=claims.get("username"),
        role=role,
        metadata={
            "token_exp": claims.get("exp"),
            "token_iat": claims.get("iat")
        }
    )


def require_admin(auth: AuthContext):
    """
    Require admin role, raise error if not admin.
    
    Args:
        auth: Authentication context
    
    Raises:
        AuthorizationError: If user is not admin
    """
    if not auth.is_admin():
        raise AuthorizationError(
            "Admin role required for this operation",
            details={
                "user_id": auth.user_id,
                "user_role": auth.role.value
            }
        )


def check_write_permission(auth: AuthContext, operation: str = "write"):
    """
    Check if user has write permissions.
    
    Args:
        auth: Authentication context
        operation: Specific write operation (create, update, delete)
    
    Raises:
        AuthorizationError: If user lacks write permission
    """
    permission_map = {
        "write": Permission.WRITE_GRAPH,
        "create": Permission.CREATE_NODE,
        "update": Permission.UPDATE_NODE,
        "delete": Permission.DELETE_NODE
    }
    
    required_permission = permission_map.get(operation, Permission.WRITE_GRAPH)
    auth.require_permission(required_permission)


def check_read_permission(auth: AuthContext, resource: str = "graph"):
    """
    Check if user has read permissions.
    
    Args:
        auth: Authentication context
        resource: Resource being read (graph, analytics)
    
    Raises:
        AuthorizationError: If user lacks read permission
    """
    permission_map = {
        "graph": Permission.READ_GRAPH,
        "analytics": Permission.READ_ANALYTICS
    }
    
    required_permission = permission_map.get(resource, Permission.READ_GRAPH)
    auth.require_permission(required_permission)


def get_user_context_for_logging(auth: Optional[AuthContext]) -> Dict[str, Any]:
    """
    Extract user context for logging purposes.
    
    Args:
        auth: Optional authentication context
    
    Returns:
        Dictionary with user context
    
    Example:
        >>> auth = AuthContext("user-123", role=Role.USER)
        >>> get_user_context_for_logging(auth)
        {'user_id': 'user-123', 'role': 'user'}
    """
    if not auth:
        return {"user_id": "anonymous", "role": "readonly"}
    
    return {
        "user_id": auth.user_id,
        "username": auth.username,
        "role": auth.role.value
    }

