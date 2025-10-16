"""
Admin Agent - Specialized agent for database administration and management.

This agent has full access to all tools including dangerous operations
like database reset, backup, and restore. Use with extreme caution.
"""

from typing import Dict, List, Any, Optional
import json

try:
    from .base_agent import BaseAgent
    from ...config import AgentConfig, DatabaseConfig
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from agents.llm_agents.base_agent import BaseAgent
    from config import AgentConfig, DatabaseConfig


class AdminAgent(BaseAgent):
    """
    Database administration and management agent.
    
    This agent has full access to all tools including dangerous operations.
    It should only be used by authorized administrators.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize the Admin Agent.
        
        Args:
            config: Optional agent configuration (uses default if not provided)
            db_config: Optional database configuration (uses default if not provided)
        """
        if config is None:
            try:
                from ..config import get_agent_config
            except ImportError:
                from config import get_agent_config
            config = get_agent_config("admin_agent")
        
        if db_config is None:
            try:
                from ..config import get_database_config
            except ImportError:
                from config import get_database_config
            db_config = get_database_config()
        
        super().__init__(config, db_config)
    
    def process_query(self, query: str) -> str:
        """
        Process an administrative query.
        
        Args:
            query: User query string
        
        Returns:
            Response string
        """
        # Add query to memory
        self.add_to_memory(query, "user")
        
        # Get memory context
        memory_context = self.get_memory_context()
        
        # Prepare enhanced prompt with context
        enhanced_prompt = self._create_enhanced_prompt(query, memory_context)
        
        # Get available tools for the model
        tools = self.get_tools_for_model()
        
        # Call model with tools
        response = self.call_model(enhanced_prompt, tools)
        
        # Add response to memory
        self.add_to_memory(response, "assistant")
        
        return response
    
    def _create_enhanced_prompt(self, query: str, memory_context: str) -> str:
        """Create enhanced prompt with context and instructions."""
        
        # Get available tools for context
        available_tools = self.get_available_tools()
        tool_descriptions = []
        
        for tool_name in available_tools:
            tool_info = self.get_tool_info(tool_name)
            if tool_info:
                tool_descriptions.append(f"- {tool_name}: {tool_info['description']}")
        
        tools_context = "\n".join(tool_descriptions)
        
        prompt = f"""
        You are an administrative agent with full access to the Neo4j graph database.
        Your role is to manage and maintain the database including:
        - Database administration and maintenance
        - Data backup and restore operations
        - Schema management and validation
        - Performance optimization
        - Security and access control
        - Data integrity and consistency
        - System monitoring and diagnostics
        
        Available tools:
        {tools_context}
        
        Administrative request: {query}
        
        {f"Previous conversation context:\n{memory_context}\n" if memory_context else ""}
        
        Instructions:
        1. Use appropriate tools for the requested operation
        2. Always confirm dangerous operations before executing
        3. Provide detailed feedback on all operations
        4. Monitor system health and performance
        5. Ensure data integrity and consistency
        6. Document all administrative actions
        7. Handle errors gracefully and provide recovery options
        
        DANGER: You have access to destructive operations like reset_graph and restore_graph.
        Always require explicit confirmation for these operations and warn users about data loss.
        """
        
        return prompt
    
    def get_database_status(self) -> str:
        """Get comprehensive database status and health information."""
        query = "Provide a comprehensive status report of the database including health, performance, and any issues that need attention."
        return self.process_query(query)
    
    def backup_database(self, backup_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Optional path to save backup file
        
        Returns:
            Dict containing backup result
        """
        return self.execute_tool("backup_graph", {"backup_path": backup_path})
    
    def restore_database(self, backup_data: Dict[str, Any], confirm: bool = False) -> Dict[str, Any]:
        """
        Restore database from backup data.
        
        Args:
            backup_data: Backup data dictionary
            confirm: Must be True to actually perform the restore
        
        Returns:
            Dict containing restore result
        """
        if not confirm:
            return {
                "success": False,
                "error": "Restore operation requires explicit confirmation. Set confirm=True to proceed.",
                "warning": "This will replace ALL data in the graph database!"
            }
        
        return self.execute_tool("restore_graph", {
            "backup_data": backup_data,
            "confirm": confirm
        })
    
    def reset_database(self, confirm: bool = False) -> Dict[str, Any]:
        """
        Reset the entire database (DANGEROUS).
        
        Args:
            confirm: Must be True to actually perform the reset
        
        Returns:
            Dict containing reset result
        """
        if not confirm:
            return {
                "success": False,
                "error": "Reset operation requires explicit confirmation. Set confirm=True to proceed.",
                "warning": "This will delete ALL data in the graph database!"
            }
        
        return self.execute_tool("reset_graph", {"confirm": confirm})
    
    def validate_database_schema(self) -> Dict[str, Any]:
        """Validate database schema and identify issues."""
        return self.execute_tool("validate_schema", {})
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get detailed database information."""
        return self.execute_tool("get_database_info", {})
    
    def create_database_indexes(self, indexes: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Create indexes on specified node properties.
        
        Args:
            indexes: List of index specifications with 'label' and 'property' keys
        
        Returns:
            Dict containing index creation results
        """
        return self.execute_tool("create_indexes", {"indexes": indexes})
    
    def optimize_database_performance(self) -> str:
        """Analyze and optimize database performance."""
        query = "Analyze database performance and provide recommendations for optimization including indexes, query optimization, and resource allocation."
        return self.process_query(query)
    
    def monitor_database_health(self) -> str:
        """Monitor database health and identify potential issues."""
        query = "Monitor database health, identify potential issues, and provide recommendations for maintaining optimal performance."
        return self.process_query(query)
    
    def cleanup_orphaned_data(self) -> str:
        """Clean up orphaned data and relationships."""
        query = "Identify and clean up orphaned data, broken relationships, and inconsistent references in the database."
        return self.process_query(query)
    
    def audit_database_access(self) -> str:
        """Audit database access and security."""
        query = "Audit database access patterns, security settings, and provide recommendations for improving security and access control."
        return self.process_query(query)
    
    def migrate_database_schema(self, migration_plan: Dict[str, Any]) -> str:
        """Migrate database schema according to a migration plan."""
        query = f"Execute database schema migration according to the following plan: {json.dumps(migration_plan, indent=2)}"
        return self.process_query(query)
    
    def generate_database_report(self, report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate comprehensive database report.
        
        Args:
            report_type: Type of report (comprehensive, health, performance, security)
        
        Returns:
            Dict containing database report data
        """
        report_data = {
            "report_type": report_type,
            "timestamp": self._get_timestamp(),
            "agent": self.name,
            "database_info": {}
        }
        
        try:
            if report_type == "comprehensive":
                # Get multiple database information
                report_data["database_info"] = {
                    "basic_info": self.execute_tool("get_database_info", {}),
                    "schema_validation": self.execute_tool("validate_schema", {}),
                    "organizational_metrics": self.execute_tool("calculate_organizational_metrics", {}),
                    "bottlenecks": self.execute_tool("find_bottlenecks", {})
                }
            elif report_type == "health":
                report_data["database_info"] = {
                    "basic_info": self.execute_tool("get_database_info", {}),
                    "schema_validation": self.execute_tool("validate_schema", {})
                }
            elif report_type == "performance":
                report_data["database_info"] = self.execute_tool("get_database_info", {})
            elif report_type == "security":
                report_data["database_info"] = {
                    "basic_info": self.execute_tool("get_database_info", {}),
                    "schema_validation": self.execute_tool("validate_schema", {})
                }
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            report_data["success"] = True
            
        except Exception as e:
            report_data["success"] = False
            report_data["error"] = str(e)
        
        return report_data
    
    def emergency_recovery(self, recovery_type: str = "backup_restore") -> str:
        """
        Perform emergency recovery operations.
        
        Args:
            recovery_type: Type of recovery (backup_restore, schema_repair, data_repair)
        
        Returns:
            Recovery operation result
        """
        if recovery_type == "backup_restore":
            query = "Perform emergency backup and restore operations to recover from data corruption or loss."
        elif recovery_type == "schema_repair":
            query = "Perform emergency schema repair operations to fix corrupted or inconsistent schema."
        elif recovery_type == "data_repair":
            query = "Perform emergency data repair operations to fix corrupted or inconsistent data."
        else:
            return f"Unknown recovery type: {recovery_type}"
        
        return self.process_query(query)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            "name": self.name,
            "role": self.role,
            "available_tools": self.get_available_tools(),
            "capabilities": [
                "Database administration and maintenance",
                "Data backup and restore operations",
                "Schema management and validation",
                "Performance optimization",
                "Security and access control",
                "Data integrity and consistency",
                "System monitoring and diagnostics",
                "Emergency recovery operations",
                "Database migration and upgrades",
                "Index creation and optimization",
                "Orphaned data cleanup",
                "Access auditing and security",
                "Comprehensive reporting"
            ],
            "model": f"{self.config.model_provider}:{self.config.model_id}",
            "memory_enabled": self.config.enable_memory,
            "max_memory_size": self.config.max_memory_size,
            "warning": "This agent has access to destructive operations. Use with extreme caution."
        }
