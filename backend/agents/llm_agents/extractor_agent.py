"""
Extractor Agent - Specialized agent for data ingestion and extraction.

This agent is designed for adding and updating organizational data,
with access to CRUD operations and validation tools.
"""

from typing import Dict, List, Any, Optional
import json

try:
    from .base_agent import BaseAgent
    from ...config import AgentConfig, DatabaseConfig
    from ...models import validate_entity_data, validate_relationship_data
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from agents.llm_agents.base_agent import BaseAgent
    from config import AgentConfig, DatabaseConfig
    from models import validate_entity_data, validate_relationship_data


class ExtractorAgent(BaseAgent):
    """
    Data extraction and ingestion agent.
    
    This agent specializes in adding and updating organizational data
    with proper validation and error handling.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize the Extractor Agent.
        
        Args:
            config: Optional agent configuration (uses default if not provided)
            db_config: Optional database configuration (uses default if not provided)
        """
        if config is None:
            try:
                from ..config import get_agent_config
            except ImportError:
                from config import get_agent_config
            config = get_agent_config("extractor_agent")
        
        if db_config is None:
            try:
                from ..config import get_database_config
            except ImportError:
                from config import get_database_config
            db_config = get_database_config()
        
        super().__init__(config, db_config)
    
    def process_query(self, query: str) -> str:
        """
        Process a data extraction or ingestion query.
        
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
        You are a data extraction and ingestion agent with access to a Neo4j graph database.
        Your role is to add, update, and manage organizational data including:
        - People (Person nodes)
        - Processes (Process nodes)
        - Departments (Department nodes)
        - Projects (Project nodes)
        - Systems (System nodes)
        - Relationships between these entities
        
        Available tools:
        {tools_context}
        
        User request: {query}
        
        {f"Previous conversation context:\n{memory_context}\n" if memory_context else ""}
        
        Instructions:
        1. Validate all data before adding to the database
        2. Use appropriate entity types and relationship types
        3. Ensure data consistency and avoid duplicates
        4. Provide clear feedback on what was added or updated
        5. Handle errors gracefully and suggest corrections
        6. Use search tools to check for existing data before adding new entries
        
        Common operations:
        - Add person: Use add_node with node_type="Person" and proper properties
        - Add process: Use add_node with node_type="Process" and proper properties
        - Add relationship: Use add_relationship with proper node references
        - Update data: Use update_node with match_properties and update_properties
        - Search existing: Use search_nodes to find existing data
        
        Entity validation rules:
        - Person: Must have name, optional email, role, department
        - Process: Must have name, optional description, category, owner
        - Department: Must have name, optional head, location
        - Project: Must have name, optional status, start_date, end_date
        - System: Must have name, optional type, vendor, version
        """
        
        return prompt
    
    def add_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a person to the graph database with validation.
        
        Args:
            person_data: Dictionary containing person information
        
        Returns:
            Dict containing operation result
        """
        # Validate person data
        validation_result = validate_entity_data("Person", person_data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": f"Person data validation failed: {validation_result['error']}"
            }
        
        # Check for existing person
        if "name" in person_data:
            search_result = self.execute_tool("search_nodes", {
                "search_term": person_data["name"],
                "node_types": ["Person"],
                "limit": 5
            })
            
            if search_result.get("success") and search_result.get("count", 0) > 0:
                return {
                    "success": False,
                    "error": f"Person with name '{person_data['name']}' already exists",
                    "existing_people": search_result.get("matching_nodes", [])
                }
        
        # Add person
        result = self.execute_tool("add_node", {
            "node_type": "Person",
            "properties": validation_result["data"]
        })
        
        return result
    
    def add_process(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a process to the graph database with validation.
        
        Args:
            process_data: Dictionary containing process information
        
        Returns:
            Dict containing operation result
        """
        # Validate process data
        validation_result = validate_entity_data("Process", process_data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": f"Process data validation failed: {validation_result['error']}"
            }
        
        # Check for existing process
        if "name" in process_data:
            search_result = self.execute_tool("search_nodes", {
                "search_term": process_data["name"],
                "node_types": ["Process"],
                "limit": 5
            })
            
            if search_result.get("success") and search_result.get("count", 0) > 0:
                return {
                    "success": False,
                    "error": f"Process with name '{process_data['name']}' already exists",
                    "existing_processes": search_result.get("matching_nodes", [])
                }
        
        # Add process
        result = self.execute_tool("add_node", {
            "node_type": "Process",
            "properties": validation_result["data"]
        })
        
        return result
    
    def add_department(self, department_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a department to the graph database with validation.
        
        Args:
            department_data: Dictionary containing department information
        
        Returns:
            Dict containing operation result
        """
        # Validate department data
        validation_result = validate_entity_data("Department", department_data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": f"Department data validation failed: {validation_result['error']}"
            }
        
        # Check for existing department
        if "name" in department_data:
            search_result = self.execute_tool("search_nodes", {
                "search_term": department_data["name"],
                "node_types": ["Department"],
                "limit": 5
            })
            
            if search_result.get("success") and search_result.get("count", 0) > 0:
                return {
                    "success": False,
                    "error": f"Department with name '{department_data['name']}' already exists",
                    "existing_departments": search_result.get("matching_nodes", [])
                }
        
        # Add department
        result = self.execute_tool("add_node", {
            "node_type": "Department",
            "properties": validation_result["data"]
        })
        
        return result
    
    def add_relationship(self, from_node: Dict[str, Any], to_node: Dict[str, Any], 
                        relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a relationship between nodes with validation.
        
        Args:
            from_node: Source node specification
            to_node: Target node specification
            relationship_type: Type of relationship
            properties: Optional relationship properties
        
        Returns:
            Dict containing operation result
        """
        # Validate relationship data
        if properties:
            validation_result = validate_relationship_data(relationship_type, properties)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Relationship data validation failed: {validation_result['error']}"
                }
            properties = validation_result["data"]
        
        # Add relationship
        result = self.execute_tool("add_relationship", {
            "from_node": from_node,
            "to_node": to_node,
            "relationship_type": relationship_type,
            "properties": properties
        })
        
        return result
    
    def update_person(self, match_properties: Dict[str, Any], update_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update person properties."""
        return self.execute_tool("update_node", {
            "node_type": "Person",
            "match_properties": match_properties,
            "update_properties": update_properties
        })
    
    def update_process(self, match_properties: Dict[str, Any], update_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update process properties."""
        return self.execute_tool("update_node", {
            "node_type": "Process",
            "match_properties": match_properties,
            "update_properties": update_properties
        })
    
    def update_department(self, match_properties: Dict[str, Any], update_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update department properties."""
        return self.execute_tool("update_node", {
            "node_type": "Department",
            "match_properties": match_properties,
            "update_properties": update_properties
        })
    
    def bulk_import_data(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Import multiple entities and relationships in bulk.
        
        Args:
            data: Dictionary with entity types as keys and lists of entity data as values
        
        Returns:
            Dict containing import results
        """
        results = {
            "success": True,
            "imported": {},
            "errors": [],
            "total_imported": 0
        }
        
        # Process each entity type
        for entity_type, entities in data.items():
            if entity_type not in ["Person", "Process", "Department", "Project", "System"]:
                results["errors"].append(f"Unknown entity type: {entity_type}")
                continue
            
            imported_count = 0
            entity_errors = []
            
            for entity_data in entities:
                try:
                    # Validate entity data
                    validation_result = validate_entity_data(entity_type, entity_data)
                    if not validation_result["valid"]:
                        entity_errors.append(f"Validation failed for {entity_type}: {validation_result['error']}")
                        continue
                    
                    # Add entity
                    result = self.execute_tool("add_node", {
                        "node_type": entity_type,
                        "properties": validation_result["data"]
                    })
                    
                    if result.get("success"):
                        imported_count += 1
                    else:
                        entity_errors.append(f"Failed to add {entity_type}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    entity_errors.append(f"Exception adding {entity_type}: {str(e)}")
            
            results["imported"][entity_type] = {
                "count": imported_count,
                "errors": entity_errors
            }
            results["total_imported"] += imported_count
            
            if entity_errors:
                results["errors"].extend(entity_errors)
        
        if results["errors"]:
            results["success"] = False
        
        return results
    
    def validate_data_consistency(self) -> Dict[str, Any]:
        """
        Validate data consistency in the graph database.
        
        Returns:
            Dict containing validation results
        """
        issues = []
        
        try:
            # Check for people without departments
            people_result = self.execute_tool("list_nodes", {
                "node_type": "Person",
                "limit": 1000
            })
            
            if people_result.get("success"):
                for person in people_result.get("nodes", []):
                    if not person.get("properties", {}).get("department"):
                        issues.append(f"Person '{person.get('properties', {}).get('name', 'Unknown')}' has no department")
            
            # Check for processes without owners
            processes_result = self.execute_tool("list_nodes", {
                "node_type": "Process",
                "limit": 1000
            })
            
            if processes_result.get("success"):
                for process in processes_result.get("nodes", []):
                    if not process.get("properties", {}).get("owner"):
                        issues.append(f"Process '{process.get('properties', {}).get('name', 'Unknown')}' has no owner")
            
            # Check for departments without heads
            departments_result = self.execute_tool("list_nodes", {
                "node_type": "Department",
                "limit": 1000
            })
            
            if departments_result.get("success"):
                for dept in departments_result.get("nodes", []):
                    if not dept.get("properties", {}).get("head"):
                        issues.append(f"Department '{dept.get('properties', {}).get('name', 'Unknown')}' has no head")
            
        except Exception as e:
            issues.append(f"Error during validation: {str(e)}")
        
        return {
            "success": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues)
        }
    
    def get_import_statistics(self) -> Dict[str, Any]:
        """Get statistics about imported data."""
        stats = {}
        
        entity_types = ["Person", "Process", "Department", "Project", "System"]
        
        for entity_type in entity_types:
            result = self.execute_tool("list_nodes", {
                "node_type": entity_type,
                "limit": 10000
            })
            
            if result.get("success"):
                stats[entity_type] = result.get("count", 0)
            else:
                stats[entity_type] = 0
        
        return {
            "success": True,
            "statistics": stats,
            "total_entities": sum(stats.values())
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            "name": self.name,
            "role": self.role,
            "available_tools": self.get_available_tools(),
            "capabilities": [
                "Data ingestion and validation",
                "Entity creation (Person, Process, Department, Project, System)",
                "Relationship management",
                "Bulk data import",
                "Data consistency validation",
                "Entity updates and modifications"
            ],
            "model": f"{self.config.model_provider}:{self.config.model_id}",
            "memory_enabled": self.config.enable_memory,
            "max_memory_size": self.config.max_memory_size
        }
