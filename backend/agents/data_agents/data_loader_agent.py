"""
Data Loader Agent - Dedicated agent for loading generated data into Neo4j.

This agent is completely separate from the data generation process and is only called
after sample data has been generated. Its sole responsibility is to reset the graph
and load the generated data files into Neo4j with proper validation and relationship creation.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from ..llm_agents.base_agent import BaseAgent
    from ...config.agent_config import AgentConfig
    from ...config.database_config import DatabaseConfig
    from ...models import validate_entity_data, validate_relationship_data
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from agents.llm_agents.base_agent import BaseAgent
    from config.agent_config import AgentConfig
    from config.database_config import DatabaseConfig
    from models import validate_entity_data, validate_relationship_data


class DataLoaderAgent(BaseAgent):
    """
    Dedicated agent for loading generated data into Neo4j.
    
    This agent is completely separate from data generation and is only called
    after sample data has been generated. It handles:
    - Resetting the Neo4j graph
    - Loading entities from generated files
    - Creating relationships from generated files
    - Providing status updates on the loading process
    """
    
    def __init__(self, config: AgentConfig, db_config: DatabaseConfig):
        super().__init__(config, db_config)
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and loading settings."""
        return {
            "role": self.role,
            "name": self.name,
            "description": "Dedicated agent for loading generated data into Neo4j",
            "available_tools": self.get_available_tools(),
            "specializations": [
                "Neo4j graph reset",
                "Data file loading",
                "Entity insertion",
                "Relationship creation",
                "Database status monitoring"
            ],
            "data_directory": self.data_dir
        }
    
    def process_query(self, query: str) -> str:
        """
        Process a data loading query.
        
        Args:
            query: User query string
        
        Returns:
            Response string
        """
        # For data loader agent, we don't use LLM processing
        # Instead, we provide information about available loading operations
        return f"""
        Data Loader Agent - Neo4j Loading Operations Available:
        
        This agent is specialized for loading generated data into Neo4j:
        - reset_and_load_data: Reset graph and load latest generated data
        - load_data_files: Load specific data files into Neo4j
        - reset_graph: Clear all data from Neo4j
        - check_database_status: Verify Neo4j connection and status
        
        Query: {query}
        
        Note: This agent is only called after data generation is complete.
        It handles the Neo4j operations separately from data generation.
        """
    
    def reset_and_load_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reset the Neo4j graph and load the latest generated data.
        
        Args:
            parameters: Dict containing optional company_name to load specific data
        
        Returns:
            Dict containing results of the reset and load operation
        """
        try:
            company_name = parameters.get("company_name")
            print(f"🔄 Starting reset and load operation for company: {company_name or 'latest'}")
            
            # Step 1: Reset the graph
            print("🧹 Step 1: Resetting Neo4j graph...")
            reset_result = self._reset_graph()
            if not reset_result.get("success"):
                print(f"❌ Graph reset failed: {reset_result.get('error')}")
                return {
                    "success": False,
                    "error": f"Failed to reset graph: {reset_result.get('error')}",
                    "reset_result": reset_result
                }
            print(f"✅ Graph reset successful: {reset_result.get('message')}")
            
            # Step 2: Find and load the latest data files
            print("📁 Step 2: Finding and loading latest data files...")
            load_result = self._load_latest_data_files(company_name)
            if not load_result.get("success"):
                print(f"❌ Data loading failed: {load_result.get('error')}")
                return {
                    "success": False,
                    "error": f"Failed to load data: {load_result.get('error')}",
                    "reset_result": reset_result,
                    "load_result": load_result
                }
            print(f"✅ Data loading successful: {load_result.get('nodes_created', 0)} nodes, {load_result.get('relationships_created', 0)} relationships")
            
            return {
                "success": True,
                "message": "Successfully reset graph and loaded data into Neo4j",
                "reset_result": reset_result,
                "load_result": load_result,
                "summary": {
                    "nodes_created": load_result.get("nodes_created", 0),
                    "relationships_created": load_result.get("relationships_created", 0),
                    "files_loaded": load_result.get("files_loaded", [])
                }
            }
            
        except Exception as e:
            print(f"❌ Reset and load operation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Reset and load operation failed: {str(e)}"
            }
    
    def load_data_files(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load specific data files into Neo4j.
        
        Args:
            parameters: Dict containing file paths or company name
        
        Returns:
            Dict containing results of the load operation
        """
        try:
            company_name = parameters.get("company_name")
            file_paths = parameters.get("file_paths", {})
            
            if company_name:
                return self._load_latest_data_files(company_name)
            elif file_paths:
                return self._load_specific_files(file_paths)
            else:
                return {
                    "success": False,
                    "error": "Must provide either company_name or file_paths"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Load data files operation failed: {str(e)}"
            }
    
    def reset_graph(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clear all data from the Neo4j graph.
        
        Args:
            parameters: Dict containing optional confirmation
        
        Returns:
            Dict containing results of the reset operation
        """
        return self._reset_graph()
    
    
    def check_database_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the status of the Neo4j database connection.
        
        Args:
            parameters: Dict (unused)
        
        Returns:
            Dict containing database status information
        """
        try:
            with self.driver.session() as session:
                # Test basic connection
                result = session.run("RETURN 1 as test")
                record = result.single()
                
                if record and record["test"] == 1:
                    # Get database statistics
                    node_count_result = session.run("MATCH (n) RETURN count(n) as count")
                    node_count = node_count_result.single()["count"]
                    
                    rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                    rel_count = rel_count_result.single()["count"]
                    
                    return {
                        "success": True,
                        "status": "connected",
                        "node_count": node_count,
                        "relationship_count": rel_count,
                        "message": f"Database connected. {node_count} nodes, {rel_count} relationships."
                    }
                else:
                    return {
                        "success": False,
                        "status": "connection_failed",
                        "error": "Database connection test failed"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "status": "connection_error",
                "error": f"Database connection error: {str(e)}"
            }
    
    def _reset_graph(self) -> Dict[str, Any]:
        """Reset the Neo4j graph by clearing all data."""
        try:
            with self.driver.session() as session:
                # Delete all relationships first
                rel_result = session.run("MATCH ()-[r]->() DELETE r")
                rel_count = rel_result.consume().counters.relationships_deleted
                
                # Delete all nodes
                node_result = session.run("MATCH (n) DELETE n")
                node_count = node_result.consume().counters.nodes_deleted
                
                return {
                    "success": True,
                    "message": f"Graph reset successfully. Deleted {node_count} nodes and {rel_count} relationships.",
                    "nodes_deleted": node_count,
                    "relationships_deleted": rel_count
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to reset graph: {str(e)}"
            }
    
    def _load_latest_data_files(self, company_name: Optional[str] = None) -> Dict[str, Any]:
        """Load the latest generated data files."""
        try:
            # Find the latest data files
            files = self._find_latest_data_files(company_name)
            if not files:
                return {
                    "success": False,
                    "error": f"No data files found for company: {company_name or 'any'}"
                }
            
            return self._load_specific_files(files)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load latest data files: {str(e)}"
            }
    
    def _find_latest_data_files(self, company_name: Optional[str] = None) -> Dict[str, str]:
        """Find the latest generated data files."""
        try:
            print(f"🔍 Looking for data files in: {self.data_dir}")
            if not os.path.exists(self.data_dir):
                print(f"❌ Data directory does not exist: {self.data_dir}")
                return {}
            
            # Get all JSON files in the data directory
            json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
            print(f"📄 Found {len(json_files)} JSON files: {json_files}")
            
            if company_name:
                # Filter by company name
                company_clean = company_name.replace(' ', '_')
                company_files = [f for f in json_files if company_clean in f]
                print(f"🏢 Filtering for company '{company_clean}': {company_files}")
            else:
                # Get the most recent files
                company_files = json_files
                print(f"📅 Using all files (no company filter): {company_files}")
            
            if not company_files:
                print("❌ No matching files found")
                return {}
            
            # Sort by modification time (newest first)
            company_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.data_dir, x)), reverse=True)
            print(f"⏰ Files sorted by modification time: {company_files}")
            
            # Find the latest set of files (same timestamp)
            latest_timestamp = None
            latest_files = {}
            
            for filename in company_files:
                # Extract timestamp from filename (format: CompanyName_Type_YYYY-MM-DD_HHMMSS.json)
                parts = filename.split('_')
                if len(parts) >= 4:
                    # For "Test_Company_Entities_2025-10-16_154849.json"
                    # parts[0] = "Test", parts[1] = "Company", parts[2] = "Entities", parts[3] = "2025-10-16", parts[4] = "154849.json"
                    timestamp_part = f"{parts[-2]}_{parts[-1].replace('.json', '')}"
                    file_type = parts[-3]  # "Entities", "Relationships", etc.
                    
                    if latest_timestamp is None:
                        latest_timestamp = timestamp_part
                        print(f"🕐 Latest timestamp: {latest_timestamp}")
                    
                    if timestamp_part == latest_timestamp:
                        latest_files[file_type] = os.path.join(self.data_dir, filename)
                        print(f"✅ Added {file_type} file: {filename}")
            
            print(f"📋 Final files to load: {list(latest_files.keys())}")
            return latest_files
            
        except Exception as e:
            print(f"❌ Error finding data files: {e}")
            return {}
    
    def _load_specific_files(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Load specific data files into Neo4j."""
        try:
            nodes_created = 0
            relationships_created = 0
            loaded_files = []
            errors = []
            
            # Load entities first
            if "Entities" in files:
                entities_file = files["Entities"]
                result = self._load_entities_file(entities_file)
                if result.get("success"):
                    nodes_created += result.get("nodes_created", 0)
                    loaded_files.append(entities_file)
                else:
                    errors.append(f"Failed to load entities: {result.get('error')}")
            
            # Load relationships
            if "Relationships" in files:
                relationships_file = files["Relationships"]
                result = self._load_relationships_file(relationships_file)
                if result.get("success"):
                    relationships_created += result.get("relationships_created", 0)
                    loaded_files.append(relationships_file)
                else:
                    errors.append(f"Failed to load relationships: {result.get('error')}")
            
            return {
                "success": len(errors) == 0,
                "nodes_created": nodes_created,
                "relationships_created": relationships_created,
                "files_loaded": loaded_files,
                "errors": errors,
                "message": f"Loaded {nodes_created} nodes and {relationships_created} relationships from {len(loaded_files)} files"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load specific files: {str(e)}"
            }
    
    def _load_entities_file(self, file_path: str) -> Dict[str, Any]:
        """Load entities from a JSON file into Neo4j with validation."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            nodes_created = 0
            errors = []
            
            with self.driver.session() as session:
                # Load employees (Person nodes)
                for employee in data.get("employees", []):
                    try:
                        # Validate employee data
                        validation_result = validate_entity_data("Person", employee)
                        if not validation_result["valid"]:
                            errors.append(f"Employee validation failed: {validation_result['error']}")
                            continue
                            
                        # Check for existing employee
                        existing_query = "MATCH (n:Person {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=employee.get('name'))
                        if existing_result.single():
                            print(f"⚠️ Employee already exists: {employee.get('name')}")
                            continue
                            
                        query = "CREATE (n:Person $props) RETURN n"
                        result = session.run(query, props=validation_result["data"])
                        record = result.single()
                        if record:
                            nodes_created += 1
                            print(f"✅ Created employee node: {employee.get('name')}")
                        else:
                            errors.append(f"Failed to create employee node: {employee.get('name')}")
                    except Exception as e:
                        errors.append(f"Employee {employee.get('name', 'unknown')}: {str(e)}")
                
                # Load departments
                for department in data.get("departments", []):
                    try:
                        # Validate department data
                        validation_result = validate_entity_data("Department", department)
                        if not validation_result["valid"]:
                            errors.append(f"Department validation failed: {validation_result['error']}")
                            continue
                            
                        # Check for existing department
                        existing_query = "MATCH (n:Department {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=department.get('name'))
                        if existing_result.single():
                            print(f"⚠️ Department already exists: {department.get('name')}")
                            continue
                            
                        query = "CREATE (n:Department $props) RETURN n"
                        result = session.run(query, props=validation_result["data"])
                        record = result.single()
                        if record:
                            nodes_created += 1
                            print(f"✅ Created department node: {department.get('name')}")
                        else:
                            errors.append(f"Failed to create department node: {department.get('name')}")
                    except Exception as e:
                        errors.append(f"Department {department.get('name', 'unknown')}: {str(e)}")
                
                # Load projects
                for project in data.get("projects", []):
                    try:
                        # Validate project data
                        validation_result = validate_entity_data("Project", project)
                        if not validation_result["valid"]:
                            errors.append(f"Project validation failed: {validation_result['error']}")
                            continue
                            
                        # Check for existing project
                        existing_query = "MATCH (n:Project {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=project.get('name'))
                        if existing_result.single():
                            print(f"⚠️ Project already exists: {project.get('name')}")
                            continue
                            
                        query = "CREATE (n:Project $props) RETURN n"
                        result = session.run(query, props=validation_result["data"])
                        record = result.single()
                        if record:
                            nodes_created += 1
                            print(f"✅ Created project node: {project.get('name')}")
                        else:
                            errors.append(f"Failed to create project node: {project.get('name')}")
                    except Exception as e:
                        errors.append(f"Project {project.get('name', 'unknown')}: {str(e)}")
                
                # Load systems
                for system in data.get("systems", []):
                    try:
                        # Validate system data
                        validation_result = validate_entity_data("System", system)
                        if not validation_result["valid"]:
                            errors.append(f"System validation failed: {validation_result['error']}")
                            continue
                            
                        # Check for existing system
                        existing_query = "MATCH (n:System {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=system.get('name'))
                        if existing_result.single():
                            print(f"⚠️ System already exists: {system.get('name')}")
                            continue
                            
                        query = "CREATE (n:System $props) RETURN n"
                        result = session.run(query, props=validation_result["data"])
                        record = result.single()
                        if record:
                            nodes_created += 1
                            print(f"✅ Created system node: {system.get('name')}")
                        else:
                            errors.append(f"Failed to create system node: {system.get('name')}")
                    except Exception as e:
                        errors.append(f"System {system.get('name', 'unknown')}: {str(e)}")
                
                # Load processes
                for process in data.get("processes", []):
                    try:
                        # Validate process data
                        validation_result = validate_entity_data("Process", process)
                        if not validation_result["valid"]:
                            errors.append(f"Process validation failed: {validation_result['error']}")
                            continue
                            
                        # Check for existing process
                        existing_query = "MATCH (n:Process {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=process.get('name'))
                        if existing_result.single():
                            print(f"⚠️ Process already exists: {process.get('name')}")
                            continue
                            
                        query = "CREATE (n:Process $props) RETURN n"
                        result = session.run(query, props=validation_result["data"])
                        record = result.single()
                        if record:
                            nodes_created += 1
                            print(f"✅ Created process node: {process.get('name')}")
                        else:
                            errors.append(f"Failed to create process node: {process.get('name')}")
                    except Exception as e:
                        errors.append(f"Process {process.get('name', 'unknown')}: {str(e)}")
            
            return {
                "success": len(errors) == 0,
                "nodes_created": nodes_created,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load entities file: {str(e)}"
            }
    
    def _load_relationships_file(self, file_path: str) -> Dict[str, Any]:
        """Load relationships from a JSON file into Neo4j with validation."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            relationships_created = 0
            errors = []
            
            with self.driver.session() as session:
                # Load all relationship categories
                # The relationship file has categories directly as keys (reports_to, works_with, etc.)
                for category, relationships in data.items():
                    print(f"📋 Loading {category} relationships: {len(relationships)} relationships")
                    
                    for rel in relationships:
                        try:
                            from_name = rel.get("from")
                            to_name = rel.get("to")
                            rel_type = rel.get("type", "RELATES_TO")
                            
                            # Validate relationship data
                            validation_result = validate_relationship_data(rel_type, rel)
                            if not validation_result["valid"]:
                                errors.append(f"Relationship validation failed: {validation_result['error']}")
                                continue
                            
                            # Extract properties (everything except from, to, type)
                            properties = {k: v for k, v in rel.items() if k not in ["from", "to", "type"]}
                            
                            # Check if both nodes exist before creating relationship
                            check_query = """
                            MATCH (from), (to)
                            WHERE from.name = $from_name AND to.name = $to_name
                            RETURN from, to
                            """
                            check_result = session.run(check_query, from_name=from_name, to_name=to_name)
                            existing_nodes = check_result.single()
                            
                            if not existing_nodes:
                                # Check which nodes are missing
                                missing_check = """
                                MATCH (n)
                                WHERE n.name = $from_name OR n.name = $to_name
                                RETURN n.name as node_name
                                """
                                missing_result = session.run(missing_check, from_name=from_name, to_name=to_name)
                                existing_node_names = [record["node_name"] for record in missing_result]
                                
                                missing_nodes = []
                                if from_name not in existing_node_names:
                                    missing_nodes.append(from_name)
                                if to_name not in existing_node_names:
                                    missing_nodes.append(to_name)
                                
                                errors.append(f"Relationship {from_name} -> {to_name}: missing nodes {missing_nodes}")
                                continue
                            
                            # Check if relationship already exists
                            existing_rel_query = f"""
                            MATCH (from)-[r:{rel_type}]->(to)
                            WHERE from.name = $from_name AND to.name = $to_name
                            RETURN r
                            """
                            existing_rel_result = session.run(existing_rel_query, from_name=from_name, to_name=to_name)
                            if existing_rel_result.single():
                                print(f"⚠️ Relationship already exists: {from_name} -[{rel_type}]-> {to_name}")
                                continue
                            
                            # Create the relationship
                            if properties:
                                query = f"""
                                MATCH (from), (to)
                                WHERE from.name = $from_name AND to.name = $to_name
                                CREATE (from)-[r:{rel_type} $props]->(to)
                                RETURN r
                                """
                                result = session.run(query, 
                                                   from_name=from_name, 
                                                   to_name=to_name, 
                                                   props=properties)
                            else:
                                query = f"""
                                MATCH (from), (to)
                                WHERE from.name = $from_name AND to.name = $to_name
                                CREATE (from)-[r:{rel_type}]->(to)
                                RETURN r
                                """
                                result = session.run(query, 
                                                   from_name=from_name, 
                                                   to_name=to_name)
                            
                            record = result.single()
                            if record:
                                relationships_created += 1
                                print(f"✅ Created relationship: {from_name} -[{rel_type}]-> {to_name}")
                            else:
                                errors.append(f"Failed to create relationship: {from_name} -> {to_name}")
                                
                        except Exception as e:
                            errors.append(f"Relationship {from_name} -> {to_name}: {str(e)}")
            
            return {
                "success": len(errors) == 0,
                "relationships_created": relationships_created,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load relationships file: {str(e)}"
            }
    
    def _create_additional_relationships(self) -> Dict[str, Any]:
        """
        Create additional relationships that might be missing from the data files.
        This includes department head relationships and other implicit relationships.
        """
        try:
            relationships_created = 0
            errors = []
            
            with self.driver.session() as session:
                # Create department head relationships
                dept_head_query = """
                MATCH (dept:Department), (person:Person)
                WHERE dept.head = person.name
                AND NOT EXISTS((person)-[:HEADS]->(dept))
                CREATE (person)-[:HEADS]->(dept)
                RETURN person.name as person_name, dept.name as dept_name
                """
                dept_head_result = session.run(dept_head_query)
                for record in dept_head_result:
                    relationships_created += 1
                    print(f"✅ Created department head relationship: {record['person_name']} -> {record['dept_name']}")
                
                # Create project department relationships
                project_dept_query = """
                MATCH (project:Project), (dept:Department)
                WHERE project.department = dept.name
                AND NOT EXISTS((project)-[:BELONGS_TO]->(dept))
                CREATE (project)-[:BELONGS_TO]->(dept)
                RETURN project.name as project_name, dept.name as dept_name
                """
                project_dept_result = session.run(project_dept_query)
                for record in project_dept_result:
                    relationships_created += 1
                    print(f"✅ Created project-department relationship: {record['project_name']} -> {record['dept_name']}")
                
                # Create process department relationships
                process_dept_query = """
                MATCH (process:Process), (dept:Department)
                WHERE process.department = dept.name
                AND NOT EXISTS((process)-[:BELONGS_TO]->(dept))
                CREATE (process)-[:BELONGS_TO]->(dept)
                RETURN process.name as process_name, dept.name as dept_name
                """
                process_dept_result = session.run(process_dept_query)
                for record in process_dept_result:
                    relationships_created += 1
                    print(f"✅ Created process-department relationship: {record['process_name']} -> {record['dept_name']}")
            
            return {
                "success": True,
                "relationships_created": relationships_created,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create additional relationships: {str(e)}",
                "relationships_created": 0
            }
    
    def _load_data_files_manually(self, company_name: str) -> Dict[str, Any]:
        """
        Manually load data files into Neo4j (called from API endpoint).
        """
        try:
            # Find the latest data files for the company
            files = self._find_latest_data_files(company_name)
            
            if not files:
                return {
                    "success": False,
                    "error": f"No data files found for company: {company_name}",
                    "nodes_created": 0,
                    "relationships_created": 0
                }
            
            # Load the data files
            result = self._load_specific_files(files)
            
            if result.get("success"):
                # Create additional relationships
                additional_rel_result = self._create_additional_relationships()
                if additional_rel_result.get("success"):
                    result["relationships_created"] += additional_rel_result.get("relationships_created", 0)
                    result["additional_relationships"] = additional_rel_result.get("relationships_created", 0)
                
                return {
                    "success": True,
                    "message": f"Successfully loaded data from {len(result.get('loaded_files', []))} files",
                    "nodes_created": result.get('nodes_created', 0),
                    "relationships_created": result.get('relationships_created', 0),
                    "loaded_files": result.get('loaded_files', []),
                    "errors": result.get('errors', [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to load data files: {result.get('error', 'Unknown error')}",
                    "nodes_created": result.get('nodes_created', 0),
                    "relationships_created": result.get('relationships_created', 0),
                    "errors": result.get('errors', [])
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error loading data files: {str(e)}",
                "nodes_created": 0,
                "relationships_created": 0
            }
