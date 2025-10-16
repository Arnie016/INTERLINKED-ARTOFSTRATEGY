"""
Analyzer Agent - Specialized agent for pattern analysis and insights.

This agent focuses on analyzing organizational patterns, finding insights,
and generating recommendations based on graph data analysis.
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


class AnalyzerAgent(BaseAgent):
    """
    Pattern analysis and insights agent.
    
    This agent specializes in analyzing organizational patterns,
    finding insights, and generating actionable recommendations.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize the Analyzer Agent.
        
        Args:
            config: Optional agent configuration (uses default if not provided)
            db_config: Optional database configuration (uses default if not provided)
        """
        if config is None:
            try:
                from ..config import get_agent_config
            except ImportError:
                from config import get_agent_config
            config = get_agent_config("analyzer_agent")
        
        if db_config is None:
            try:
                from ..config import get_database_config
            except ImportError:
                from config import get_database_config
            db_config = get_database_config()
        
        super().__init__(config, db_config)
    
    def process_query(self, query: str) -> str:
        """
        Process an analysis query.
        
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
        You are an organizational analysis agent specializing in pattern detection and insights.
        Your role is to analyze the organizational graph data and provide actionable insights about:
        - Organizational structure and hierarchy
        - Process efficiency and bottlenecks
        - Communication patterns and collaboration
        - Resource allocation and utilization
        - Performance metrics and KPIs
        - Risk identification and mitigation
        
        Available tools:
        {tools_context}
        
        Analysis request: {query}
        
        {f"Previous conversation context:\n{memory_context}\n" if memory_context else ""}
        
        Instructions:
        1. Use multiple analysis tools to gather comprehensive data
        2. Look for patterns, trends, and anomalies in the data
        3. Provide specific, actionable recommendations
        4. Quantify findings with metrics and statistics
        5. Identify both opportunities and risks
        6. Consider the business impact of your findings
        7. Use visual descriptions when helpful (charts, graphs, etc.)
        
        Analysis approach:
        - Start with high-level metrics and structure analysis
        - Drill down into specific areas of interest
        - Compare different departments, teams, or processes
        - Look for correlations and dependencies
        - Identify outliers and exceptions
        - Provide both current state and improvement recommendations
        """
        
        return prompt
    
    def analyze_organizational_health(self) -> str:
        """Perform comprehensive organizational health analysis."""
        query = "Perform a comprehensive organizational health analysis including structure, processes, communication, and performance metrics. Identify key strengths, weaknesses, and improvement opportunities."
        return self.process_query(query)
    
    def find_operational_bottlenecks(self) -> str:
        """Find and analyze operational bottlenecks."""
        query = "Identify all operational bottlenecks in our organization, analyze their impact, and provide specific recommendations for resolution."
        return self.process_query(query)
    
    def analyze_communication_patterns(self) -> str:
        """Analyze communication patterns and collaboration effectiveness."""
        query = "Analyze communication patterns and collaboration effectiveness across the organization. Identify silos, communication gaps, and opportunities for improved collaboration."
        return self.process_query(query)
    
    def assess_resource_utilization(self) -> str:
        """Assess resource utilization and allocation efficiency."""
        query = "Assess resource utilization and allocation efficiency across departments and processes. Identify underutilized resources and optimization opportunities."
        return self.process_query(query)
    
    def identify_risk_factors(self) -> str:
        """Identify organizational risk factors and dependencies."""
        query = "Identify organizational risk factors, critical dependencies, and potential points of failure. Provide risk mitigation strategies."
        return self.process_query(query)
    
    def analyze_performance_metrics(self) -> str:
        """Analyze key performance metrics and trends."""
        query = "Analyze key performance metrics and trends across the organization. Identify areas of high performance and areas needing improvement."
        return self.process_query(query)
    
    def compare_departments(self, department_names: Optional[List[str]] = None) -> str:
        """Compare performance and structure across departments."""
        if department_names:
            dept_list = ", ".join(department_names)
            query = f"Compare the performance, structure, and efficiency of the following departments: {dept_list}. Identify best practices and improvement opportunities."
        else:
            query = "Compare performance and structure across all departments. Identify best practices, performance variations, and improvement opportunities."
        return self.process_query(query)
    
    def analyze_process_efficiency(self) -> str:
        """Analyze process efficiency and optimization opportunities."""
        query = "Analyze the efficiency of all business processes, identify optimization opportunities, and recommend process improvements."
        return self.process_query(query)
    
    def find_skill_gaps_and_training_needs(self) -> str:
        """Identify skill gaps and training needs."""
        query = "Analyze the organization to identify skill gaps, training needs, and development opportunities. Provide recommendations for addressing these gaps."
        return self.process_query(query)
    
    def analyze_system_dependencies(self) -> str:
        """Analyze system dependencies and integration points."""
        query = "Analyze system dependencies, integration points, and technical architecture. Identify potential issues and optimization opportunities."
        return self.process_query(query)
    
    def generate_insights_report(self, report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate structured insights report.
        
        Args:
            report_type: Type of report (comprehensive, bottlenecks, communication, performance)
        
        Returns:
            Dict containing structured insights data
        """
        report_data = {
            "report_type": report_type,
            "timestamp": self._get_timestamp(),
            "agent": self.name,
            "insights": {}
        }
        
        try:
            if report_type == "comprehensive":
                # Get multiple analysis results
                report_data["insights"] = {
                    "organizational_metrics": self.execute_tool("calculate_organizational_metrics", {}),
                    "bottlenecks": self.execute_tool("find_bottlenecks", {}),
                    "structure_analysis": self.execute_tool("analyze_organizational_structure", {}),
                    "process_dependencies": self.execute_tool("find_process_dependencies", {}),
                    "communication_patterns": self.execute_tool("find_communication_patterns", {})
                }
            elif report_type == "bottlenecks":
                report_data["insights"] = self.execute_tool("find_bottlenecks", {})
            elif report_type == "communication":
                report_data["insights"] = self.execute_tool("find_communication_patterns", {})
            elif report_type == "performance":
                report_data["insights"] = self.execute_tool("calculate_organizational_metrics", {})
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            report_data["success"] = True
            
        except Exception as e:
            report_data["success"] = False
            report_data["error"] = str(e)
        
        return report_data
    
    def find_anomalies(self) -> str:
        """Find anomalies and outliers in organizational data."""
        query = "Identify anomalies, outliers, and unusual patterns in our organizational data. Analyze what these might indicate and their potential impact."
        return self.process_query(query)
    
    def analyze_trends(self, time_period: Optional[str] = None) -> str:
        """Analyze trends over time (if temporal data is available)."""
        if time_period:
            query = f"Analyze trends and changes over the {time_period} period. Identify patterns, growth areas, and areas of concern."
        else:
            query = "Analyze trends and patterns in our organizational data. Identify growth areas, declining areas, and areas requiring attention."
        return self.process_query(query)
    
    def benchmark_against_best_practices(self) -> str:
        """Benchmark organizational practices against industry best practices."""
        query = "Benchmark our organizational practices, structure, and processes against industry best practices. Identify gaps and improvement opportunities."
        return self.process_query(query)
    
    def predict_future_scenarios(self, scenario_type: str = "growth") -> str:
        """Predict future scenarios based on current data patterns."""
        query = f"Based on current organizational data and patterns, predict potential future scenarios for {scenario_type}. Identify risks and opportunities."
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
                "Organizational health analysis",
                "Bottleneck identification and analysis",
                "Communication pattern analysis",
                "Resource utilization assessment",
                "Risk factor identification",
                "Performance metrics analysis",
                "Department comparison",
                "Process efficiency analysis",
                "Skill gap identification",
                "System dependency analysis",
                "Anomaly detection",
                "Trend analysis",
                "Best practice benchmarking",
                "Future scenario prediction"
            ],
            "model": f"{self.config.model_provider}:{self.config.model_id}",
            "memory_enabled": self.config.enable_memory,
            "max_memory_size": self.config.max_memory_size
        }
