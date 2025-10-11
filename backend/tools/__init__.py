"""
Tools package for the Agent Tool Architecture.

This package contains modular tools organized by functionality:
- graph_crud.py: Core CRUD operations (add/delete nodes, relationships)
- graph_analysis.py: Pattern detection, bottleneck analysis, metrics
- graph_admin.py: Reset DB, backup, schema management
- graph_search.py: Complex search, pathfinding, recommendations

Each tool file exports a TOOLS dictionary for dynamic discovery.
"""

try:
    from .graph_crud import TOOLS as CRUD_TOOLS
    from .graph_analysis import TOOLS as ANALYSIS_TOOLS
    from .graph_admin import TOOLS as ADMIN_TOOLS
    from .graph_search import TOOLS as SEARCH_TOOLS
except ImportError:
    # Handle direct execution
    from graph_crud import TOOLS as CRUD_TOOLS
    from graph_analysis import TOOLS as ANALYSIS_TOOLS
    from graph_admin import TOOLS as ADMIN_TOOLS
    from graph_search import TOOLS as SEARCH_TOOLS

# Registry of all available tools
ALL_TOOLS = {
    **CRUD_TOOLS,
    **ANALYSIS_TOOLS,
    **ADMIN_TOOLS,
    **SEARCH_TOOLS
}

def get_tools_by_category(category: str = None):
    """Get tools filtered by category or all tools if no category specified."""
    if category is None:
        return ALL_TOOLS
    
    category_map = {
        'crud': CRUD_TOOLS,
        'analysis': ANALYSIS_TOOLS,
        'admin': ADMIN_TOOLS,
        'search': SEARCH_TOOLS
    }
    
    return category_map.get(category, {})

def get_tools_for_role(role: str):
    """Get tools available for a specific role based on permissions."""
    try:
        from ..config.tool_permissions import ROLE_PERMISSIONS
    except ImportError:
        from config.tool_permissions import ROLE_PERMISSIONS
    
    allowed_tools = ROLE_PERMISSIONS.get(role, [])
    return {name: tool for name, tool in ALL_TOOLS.items() if name in allowed_tools}
