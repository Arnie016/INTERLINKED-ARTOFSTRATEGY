"""
Tool permissions configuration for role-based access control.

This module defines which tools are available to different agent roles,
ensuring proper security and access control in the Agent Tool Architecture.
"""

from typing import Dict, List, Set
from enum import Enum


class AgentRole(Enum):
    """Enumeration of available agent roles."""
    EXTRACTOR = "extractor"
    ANALYZER = "analyzer"
    ADMIN = "admin"
    USER = "user"


# Role-based tool permissions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    # Extractor Agent: Only needs basic CRUD operations for data ingestion
    AgentRole.EXTRACTOR.value: [
        # CRUD Tools
        "add_node",
        "add_relationship",
        "update_node",
        "get_node",
        "list_nodes",
        "list_relationships",
        "test_connection",
        
        # Limited search for validation
        "search_nodes",
    ],
    
    # Analyzer Agent: Needs analysis and search tools for pattern detection
    AgentRole.ANALYZER.value: [
        # Read-only CRUD
        "get_node",
        "list_nodes",
        "list_relationships",
        "test_connection",
        
        # Analysis Tools
        "find_bottlenecks",
        "analyze_organizational_structure",
        "find_process_dependencies",
        "calculate_organizational_metrics",
        "find_communication_patterns",
        
        # Search Tools
        "find_shortest_path",
        "find_related_nodes",
        "search_nodes",
        "find_influential_nodes",
        "recommend_collaborations",
        "find_communities",
        "advanced_query",
        
        # Limited admin for info
        "get_database_info",
        "validate_schema",
    ],
    
    # Admin Agent: Full access to all tools including dangerous operations
    AgentRole.ADMIN.value: [
        # All CRUD Tools
        "add_node",
        "add_relationship",
        "update_node",
        "delete_node",
        "get_node",
        "list_nodes",
        "list_relationships",
        "test_connection",
        
        # All Analysis Tools
        "find_bottlenecks",
        "analyze_organizational_structure",
        "find_process_dependencies",
        "calculate_organizational_metrics",
        "find_communication_patterns",
        
        # All Search Tools
        "find_shortest_path",
        "find_related_nodes",
        "search_nodes",
        "find_influential_nodes",
        "recommend_collaborations",
        "find_communities",
        "advanced_query",
        
        # All Admin Tools
        "reset_graph",
        "backup_graph",
        "restore_graph",
        "get_database_info",
        "create_indexes",
        "validate_schema",
    ],
    
    # User-facing Agent: Limited to safe, read-only operations
    AgentRole.USER.value: [
        # Read-only CRUD
        "get_node",
        "list_nodes",
        "list_relationships",
        
        # Safe Analysis Tools
        "find_bottlenecks",
        "analyze_organizational_structure",
        "find_process_dependencies",
        "calculate_organizational_metrics",
        "find_communication_patterns",
        
        # Safe Search Tools
        "find_shortest_path",
        "find_related_nodes",
        "search_nodes",
        "find_influential_nodes",
        "recommend_collaborations",
        "find_communities",
    ],
}


# Tool categories for easier management
TOOL_CATEGORIES = {
    "crud": [
        "add_node", "add_relationship", "update_node", "delete_node",
        "get_node", "list_nodes", "list_relationships", "test_connection"
    ],
    "analysis": [
        "find_bottlenecks", "analyze_organizational_structure",
        "find_process_dependencies", "calculate_organizational_metrics",
        "find_communication_patterns"
    ],
    "search": [
        "find_shortest_path", "find_related_nodes", "search_nodes",
        "find_influential_nodes", "recommend_collaborations",
        "find_communities", "advanced_query"
    ],
    "admin": [
        "reset_graph", "backup_graph", "restore_graph",
        "get_database_info", "create_indexes", "validate_schema"
    ]
}


# Dangerous tools that require special confirmation
DANGEROUS_TOOLS = {
    "reset_graph": "Will delete ALL data in the graph database",
    "restore_graph": "Will replace ALL data in the graph database",
    "delete_node": "Will permanently delete nodes and their relationships",
    "advanced_query": "Can execute arbitrary Cypher queries"
}


# Tools that require specific parameters for safety
SAFETY_REQUIREMENTS = {
    "reset_graph": ["confirm"],
    "restore_graph": ["confirm"],
    "delete_node": ["delete_relationships"],
    "advanced_query": ["cypher_query"]
}


def get_tools_for_role(role: str) -> List[str]:
    """
    Get list of tools available for a specific role.
    
    Args:
        role: Agent role (extractor, analyzer, admin, user)
    
    Returns:
        List of tool names available to the role
    """
    return ROLE_PERMISSIONS.get(role, [])


def validate_role_access(role: str, tool_name: str) -> bool:
    """
    Validate if a role has access to a specific tool.
    
    Args:
        role: Agent role
        tool_name: Name of the tool
    
    Returns:
        True if role has access, False otherwise
    """
    if role not in ROLE_PERMISSIONS:
        return False
    
    return tool_name in ROLE_PERMISSIONS[role]


def get_role_capabilities(role: str) -> Dict[str, List[str]]:
    """
    Get capabilities organized by category for a specific role.
    
    Args:
        role: Agent role
    
    Returns:
        Dict with tool categories and available tools
    """
    available_tools = get_tools_for_role(role)
    capabilities = {}
    
    for category, tools in TOOL_CATEGORIES.items():
        category_tools = [tool for tool in tools if tool in available_tools]
        if category_tools:
            capabilities[category] = category_tools
    
    return capabilities


def is_dangerous_tool(tool_name: str) -> bool:
    """
    Check if a tool is considered dangerous and requires special handling.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        True if tool is dangerous, False otherwise
    """
    return tool_name in DANGEROUS_TOOLS


def get_safety_requirements(tool_name: str) -> List[str]:
    """
    Get safety requirements for a specific tool.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        List of required parameters for safety
    """
    return SAFETY_REQUIREMENTS.get(tool_name, [])


def get_tool_danger_description(tool_name: str) -> str:
    """
    Get description of why a tool is considered dangerous.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        Description of the danger
    """
    return DANGEROUS_TOOLS.get(tool_name, "")


def get_all_roles() -> List[str]:
    """
    Get list of all available roles.
    
    Returns:
        List of role names
    """
    return [role.value for role in AgentRole]


def get_role_description(role: str) -> str:
    """
    Get description of what a role is designed for.
    
    Args:
        role: Agent role
    
    Returns:
        Description of the role
    """
    descriptions = {
        AgentRole.EXTRACTOR.value: "Data ingestion agent - can add and update nodes and relationships",
        AgentRole.ANALYZER.value: "Analysis agent - can analyze patterns and search the graph",
        AgentRole.ADMIN.value: "Administrative agent - full access including dangerous operations",
        AgentRole.USER.value: "User-facing agent - safe, read-only operations for end users"
    }
    
    return descriptions.get(role, "Unknown role")


def validate_tool_parameters(tool_name: str, parameters: Dict[str, any]) -> Dict[str, any]:
    """
    Validate tool parameters against safety requirements.
    
    Args:
        tool_name: Name of the tool
        parameters: Parameters passed to the tool
    
    Returns:
        Dict with validation result and any issues
    """
    issues = []
    
    # Check for dangerous tools
    if is_dangerous_tool(tool_name):
        safety_reqs = get_safety_requirements(tool_name)
        for req in safety_reqs:
            if req not in parameters:
                issues.append(f"Missing required safety parameter: {req}")
            elif req == "confirm" and not parameters[req]:
                issues.append(f"Tool {tool_name} requires explicit confirmation")
    
    # Special validations for specific tools
    if tool_name == "delete_node" and not parameters.get("delete_relationships", False):
        issues.append("delete_node requires delete_relationships parameter for safety")
    
    if tool_name == "advanced_query" and not parameters.get("cypher_query"):
        issues.append("advanced_query requires cypher_query parameter")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "is_dangerous": is_dangerous_tool(tool_name)
    }


# Role hierarchy for inheritance (higher roles inherit lower role permissions)
ROLE_HIERARCHY = {
    AgentRole.ADMIN.value: [AgentRole.ANALYZER.value, AgentRole.EXTRACTOR.value, AgentRole.USER.value],
    AgentRole.ANALYZER.value: [AgentRole.USER.value],
    AgentRole.EXTRACTOR.value: [AgentRole.USER.value],
    AgentRole.USER.value: []
}


def get_effective_permissions(role: str) -> List[str]:
    """
    Get effective permissions for a role including inherited permissions.
    
    Args:
        role: Agent role
    
    Returns:
        List of all tool names the role can access (including inherited)
    """
    if role not in ROLE_HIERARCHY:
        return get_tools_for_role(role)
    
    permissions = set(get_tools_for_role(role))
    
    # Add inherited permissions
    for inherited_role in ROLE_HIERARCHY[role]:
        permissions.update(get_tools_for_role(inherited_role))
    
    return list(permissions)
