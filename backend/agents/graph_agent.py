"""
Graph Agent - Main orchestrator for user-facing graph queries.

This agent provides a user-friendly interface for querying and analyzing
the organizational graph, with access to safe read-only and analysis tools.
"""

from typing import Dict, List, Any, Optional
import json

try:
    from .base_agent import BaseAgent
    from ..config import AgentConfig, DatabaseConfig
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.base_agent import BaseAgent
    from config import AgentConfig, DatabaseConfig


class GraphAgent(BaseAgent):
    """
    Main graph query agent for user interactions.
    
    This agent provides a safe, user-friendly interface for querying
    the organizational graph with access to analysis and search tools.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize the Graph Agent.
        
        Args:
            config: Optional agent configuration (uses default if not provided)
            db_config: Optional database configuration (uses default if not provided)
        """
        if config is None:
            try:
                from ..config import get_agent_config
            except ImportError:
                from config import get_agent_config
            config = get_agent_config("graph_agent")
        
        if db_config is None:
            try:
                from ..config import get_database_config
            except ImportError:
                from config import get_database_config
            db_config = get_database_config()
        
        super().__init__(config, db_config)
    
    def process_query(self, query: str) -> str:
        """
        Process a user query about the organizational graph.
        
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
        You are an organizational analysis agent with access to a Neo4j graph database containing:
        - People (nodes with properties like name, role, department)
        - Processes (nodes representing business processes)
        - Departments (organizational units)
        - Systems (applications and tools)
        - Relationships like PERFORMS, OWNS, DEPENDS_ON, REPORTS_TO, COLLABORATES_WITH, USES, SUPPORTS
        
        Available tools:
        {tools_context}
        
        User question: {query}
        
        {f"Previous conversation context:\n{memory_context}\n" if memory_context else ""}
        
        Instructions:
        1. If you need to query the graph database to answer the question, use the appropriate tools
        2. Provide clear, actionable insights based on the data
        3. If no relevant data is found, explain what you searched for and suggest alternatives
        4. Use multiple tools if needed to provide a comprehensive answer
        5. Always explain your findings in business terms that are easy to understand
        
        Common query patterns:
        - Find people: Use search_nodes with node_types=["Person"]
        - Find processes: Use search_nodes with node_types=["Process"]
        - Find bottlenecks: Use find_bottlenecks
        - Analyze structure: Use analyze_organizational_structure
        - Find dependencies: Use find_process_dependencies
        - Calculate metrics: Use calculate_organizational_metrics
        - Find patterns: Use find_communication_patterns
        - Search relationships: Use find_related_nodes
        - Find paths: Use find_shortest_path
        - Get recommendations: Use recommend_collaborations
        """
        
        return prompt
    
    def get_organizational_overview(self) -> str:
        """Get a high-level overview of the organization."""
        query = "Provide an overview of our organization including key metrics, structure, and any issues you find"
        return self.process_query(query)
    
    def find_bottlenecks(self) -> str:
        """Find and analyze organizational bottlenecks."""
        query = "Find all bottlenecks in our processes and organizational structure, and provide recommendations for improvement"
        return self.process_query(query)
    
    def analyze_team_structure(self, team_name: Optional[str] = None) -> str:
        """Analyze team structure and relationships."""
        if team_name:
            query = f"Analyze the structure and relationships of the {team_name} team"
        else:
            query = "Analyze the overall team structure and reporting relationships in our organization"
        return self.process_query(query)
    
    def find_collaboration_opportunities(self) -> str:
        """Find potential collaboration opportunities."""
        query = "Find collaboration opportunities and recommend people who should work together based on their roles, departments, and existing relationships"
        return self.process_query(query)
    
    def get_process_analysis(self) -> str:
        """Get comprehensive process analysis."""
        query = "Analyze all our business processes, their dependencies, and identify areas for improvement"
        return self.process_query(query)
    
    def search_people(self, search_term: str) -> str:
        """Search for people in the organization."""
        query = f"Search for people matching '{search_term}' and provide information about their roles, departments, and relationships"
        return self.process_query(query)
    
    def search_processes(self, search_term: str) -> str:
        """Search for processes in the organization."""
        query = f"Search for processes matching '{search_term}' and provide information about their owners, dependencies, and performance"
        return self.process_query(query)
    
    def get_department_analysis(self, department_name: Optional[str] = None) -> str:
        """Analyze department structure and performance."""
        if department_name:
            query = f"Analyze the {department_name} department including its people, processes, and performance metrics"
        else:
            query = "Analyze all departments in our organization and provide insights about their structure and performance"
        return self.process_query(query)
    
    def find_skill_gaps(self) -> str:
        """Find skill gaps and training opportunities."""
        query = "Analyze our organization to identify skill gaps and recommend training or hiring opportunities"
        return self.process_query(query)
    
    def get_system_usage_analysis(self) -> str:
        """Analyze system usage and dependencies."""
        query = "Analyze how our systems are being used, their dependencies, and identify any issues or optimization opportunities"
        return self.process_query(query)
    
    def export_analysis_report(self, report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Export analysis report as structured data.
        
        Args:
            report_type: Type of report (comprehensive, bottlenecks, structure, metrics)
        
        Returns:
            Dict containing structured analysis data
        """
        report_data = {
            "report_type": report_type,
            "timestamp": self._get_timestamp(),
            "agent": self.name,
            "data": {}
        }
        
        try:
            if report_type == "comprehensive":
                # Get multiple analysis results
                report_data["data"] = {
                    "metrics": self.execute_tool("calculate_organizational_metrics", {}),
                    "bottlenecks": self.execute_tool("find_bottlenecks", {}),
                    "structure": self.execute_tool("analyze_organizational_structure", {}),
                    "dependencies": self.execute_tool("find_process_dependencies", {}),
                    "communication": self.execute_tool("find_communication_patterns", {})
                }
            elif report_type == "bottlenecks":
                report_data["data"] = self.execute_tool("find_bottlenecks", {})
            elif report_type == "structure":
                report_data["data"] = self.execute_tool("analyze_organizational_structure", {})
            elif report_type == "metrics":
                report_data["data"] = self.execute_tool("calculate_organizational_metrics", {})
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            report_data["success"] = True
            
        except Exception as e:
            report_data["success"] = False
            report_data["error"] = str(e)
        
        return report_data
    
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
                "Organizational analysis",
                "Process bottleneck detection",
                "Team structure analysis",
                "Collaboration recommendations",
                "System usage analysis",
                "Skill gap identification",
                "Report generation"
            ],
            "model": f"{self.config.model_provider}:{self.config.model_id}",
            "memory_enabled": self.config.enable_memory,
            "max_memory_size": self.config.max_memory_size
        }
