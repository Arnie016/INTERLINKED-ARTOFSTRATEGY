"""
Standalone Data Loader Agent - Direct Neo4j integration without base agent dependency.

This agent handles data loading operations directly with Neo4j, providing a clean
separation from the LLM-based agents and avoiding the complexity of the base agent.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StandaloneDataLoader:
    """
    Standalone data loader that directly connects to Neo4j.
    
    This class provides all the functionality needed for loading generated data
    into Neo4j without depending on the base agent architecture.
    """
    
    def __init__(self):
        """Initialize the standalone data loader with direct Neo4j connection."""
        self.driver = None
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        self._connect_to_neo4j()
    
    def _connect_to_neo4j(self):
        """Establish connection to Neo4j using environment variables."""
        try:
            # Get Neo4j connection details from environment
            uri = os.getenv('NEO4J_URI')
            username = os.getenv('NEO4J_USERNAME')
            password = os.getenv('NEO4J_PASSWORD')
            database = os.getenv('NEO4J_DATABASE', 'neo4j')
            
            if not all([uri, username, password]):
                raise ValueError("Missing Neo4j connection details in environment variables")
            
            logger.info(f"Connecting to Neo4j at {uri}")
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # Test connection
            with self.driver.session(database=database) as session:
                session.run("RETURN 1")
            
            logger.info("✅ Successfully connected to Neo4j")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def reset_graph(self) -> Dict[str, Any]:
        """Reset the Neo4j graph by clearing all data."""
        try:
            database = os.getenv('NEO4J_DATABASE', 'neo4j')
            with self.driver.session(database=database) as session:
                # Delete all relationships first
                rel_result = session.run("MATCH ()-[r]->() DELETE r")
                rel_count = rel_result.consume().counters.relationships_deleted
                
                # Delete all nodes
                node_result = session.run("MATCH (n) DELETE n")
                node_count = node_result.consume().counters.nodes_deleted
                
                logger.info(f"Graph reset: deleted {node_count} nodes and {rel_count} relationships")
                
                return {
                    "success": True,
                    "message": f"Graph reset successfully. Deleted {node_count} nodes and {rel_count} relationships.",
                    "nodes_deleted": node_count,
                    "relationships_deleted": rel_count
                }
                
        except Exception as e:
            logger.error(f"Failed to reset graph: {e}")
            return {
                "success": False,
                "error": f"Failed to reset graph: {str(e)}"
            }
    
    def check_database_status(self) -> Dict[str, Any]:
        """Check the status of the Neo4j database connection."""
        try:
            database = os.getenv('NEO4J_DATABASE', 'neo4j')
            with self.driver.session(database=database) as session:
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
    
    def find_latest_data_files(self, company_name: Optional[str] = None) -> Dict[str, str]:
        """Find the latest generated data files."""
        try:
            logger.info(f"Looking for data files in: {self.data_dir}")
            if not os.path.exists(self.data_dir):
                logger.error(f"Data directory does not exist: {self.data_dir}")
                return {}
            
            # Get all JSON files in the data directory
            json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
            logger.info(f"Found {len(json_files)} JSON files: {json_files}")
            
            if company_name:
                # Filter by company name
                company_clean = company_name.replace(' ', '_')
                company_files = [f for f in json_files if company_clean in f]
                logger.info(f"Filtering for company '{company_clean}': {company_files}")
            else:
                # Get the most recent files
                company_files = json_files
                logger.info(f"Using all files (no company filter): {company_files}")
            
            if not company_files:
                logger.error("No matching files found")
                return {}
            
            # Sort by modification time (newest first)
            company_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.data_dir, x)), reverse=True)
            logger.info(f"Files sorted by modification time: {company_files}")
            
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
                        logger.info(f"Latest timestamp: {latest_timestamp}")
                    
                    if timestamp_part == latest_timestamp:
                        latest_files[file_type] = os.path.join(self.data_dir, filename)
                        logger.info(f"Added {file_type} file: {filename}")
            
            logger.info(f"Final files to load: {list(latest_files.keys())}")
            return latest_files
            
        except Exception as e:
            logger.error(f"Error finding data files: {e}")
            return {}
    
    def load_entities_file(self, file_path: str) -> Dict[str, Any]:
        """Load entities from a JSON file into Neo4j."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            nodes_created = 0
            errors = []
            database = os.getenv('NEO4J_DATABASE', 'neo4j')
            
            with self.driver.session(database=database) as session:
                # Load employees (Person nodes)
                for employee in data.get("employees", []):
                    try:
                        # Check for existing employee
                        existing_query = "MATCH (n:Person {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=employee.get('name'))
                        if existing_result.single():
                            logger.info(f"Employee already exists: {employee.get('name')}")
                            continue
                            
                        query = "CREATE (n:Person $props) RETURN n"
                        result = session.run(query, props=employee)
                        record = result.single()
                        if record:
                            nodes_created += 1
                            logger.info(f"Created employee node: {employee.get('name')}")
                        else:
                            errors.append(f"Failed to create employee node: {employee.get('name')}")
                    except Exception as e:
                        errors.append(f"Employee {employee.get('name', 'unknown')}: {str(e)}")
                
                # Load departments
                for department in data.get("departments", []):
                    try:
                        # Check for existing department
                        existing_query = "MATCH (n:Department {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=department.get('name'))
                        if existing_result.single():
                            logger.info(f"Department already exists: {department.get('name')}")
                            continue
                            
                        query = "CREATE (n:Department $props) RETURN n"
                        result = session.run(query, props=department)
                        record = result.single()
                        if record:
                            nodes_created += 1
                            logger.info(f"Created department node: {department.get('name')}")
                        else:
                            errors.append(f"Failed to create department node: {department.get('name')}")
                    except Exception as e:
                        errors.append(f"Department {department.get('name', 'unknown')}: {str(e)}")
                
                # Load projects
                for project in data.get("projects", []):
                    try:
                        # Check for existing project
                        existing_query = "MATCH (n:Project {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=project.get('name'))
                        if existing_result.single():
                            logger.info(f"Project already exists: {project.get('name')}")
                            continue
                            
                        query = "CREATE (n:Project $props) RETURN n"
                        result = session.run(query, props=project)
                        record = result.single()
                        if record:
                            nodes_created += 1
                            logger.info(f"Created project node: {project.get('name')}")
                        else:
                            errors.append(f"Failed to create project node: {project.get('name')}")
                    except Exception as e:
                        errors.append(f"Project {project.get('name', 'unknown')}: {str(e)}")
                
                # Load systems
                for system in data.get("systems", []):
                    try:
                        # Check for existing system
                        existing_query = "MATCH (n:System {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=system.get('name'))
                        if existing_result.single():
                            logger.info(f"System already exists: {system.get('name')}")
                            continue
                            
                        query = "CREATE (n:System $props) RETURN n"
                        result = session.run(query, props=system)
                        record = result.single()
                        if record:
                            nodes_created += 1
                            logger.info(f"Created system node: {system.get('name')}")
                        else:
                            errors.append(f"Failed to create system node: {system.get('name')}")
                    except Exception as e:
                        errors.append(f"System {system.get('name', 'unknown')}: {str(e)}")
                
                # Load processes
                for process in data.get("processes", []):
                    try:
                        # Check for existing process
                        existing_query = "MATCH (n:Process {name: $name}) RETURN n"
                        existing_result = session.run(existing_query, name=process.get('name'))
                        if existing_result.single():
                            logger.info(f"Process already exists: {process.get('name')}")
                            continue
                            
                        query = "CREATE (n:Process $props) RETURN n"
                        result = session.run(query, props=process)
                        record = result.single()
                        if record:
                            nodes_created += 1
                            logger.info(f"Created process node: {process.get('name')}")
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
    
    def load_relationships_file(self, file_path: str) -> Dict[str, Any]:
        """Load relationships from a JSON file into Neo4j."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            relationships_created = 0
            errors = []
            database = os.getenv('NEO4J_DATABASE', 'neo4j')
            
            with self.driver.session(database=database) as session:
                # Load all relationship categories
                for category, relationships in data.items():
                    logger.info(f"Loading {category} relationships: {len(relationships)} relationships")
                    
                    for rel in relationships:
                        try:
                            from_name = rel.get("from")
                            to_name = rel.get("to")
                            rel_type = rel.get("type", "RELATES_TO")
                            
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
                                logger.info(f"Relationship already exists: {from_name} -[{rel_type}]-> {to_name}")
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
                                logger.info(f"Created relationship: {from_name} -[{rel_type}]-> {to_name}")
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
    
    def create_additional_relationships(self) -> Dict[str, Any]:
        """Create additional relationships that might be missing from the data files."""
        try:
            relationships_created = 0
            errors = []
            database = os.getenv('NEO4J_DATABASE', 'neo4j')
            
            with self.driver.session(database=database) as session:
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
                    logger.info(f"Created department head relationship: {record['person_name']} -> {record['dept_name']}")
                
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
                    logger.info(f"Created project-department relationship: {record['project_name']} -> {record['dept_name']}")
                
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
                    logger.info(f"Created process-department relationship: {record['process_name']} -> {record['dept_name']}")
            
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
    
    def load_data_files(self, company_name: Optional[str] = None) -> Dict[str, Any]:
        """Load data files into Neo4j."""
        try:
            # Find the latest data files
            files = self.find_latest_data_files(company_name)
            if not files:
                return {
                    "success": False,
                    "error": f"No data files found for company: {company_name or 'any'}"
                }
            
            nodes_created = 0
            relationships_created = 0
            loaded_files = []
            errors = []
            
            # Load entities first
            if "Entities" in files:
                entities_file = files["Entities"]
                result = self.load_entities_file(entities_file)
                if result.get("success"):
                    nodes_created += result.get("nodes_created", 0)
                    loaded_files.append(entities_file)
                else:
                    errors.append(f"Failed to load entities: {result.get('error')}")
            
            # Load relationships
            if "Relationships" in files:
                relationships_file = files["Relationships"]
                result = self.load_relationships_file(relationships_file)
                if result.get("success"):
                    relationships_created += result.get("relationships_created", 0)
                    loaded_files.append(relationships_file)
                else:
                    errors.append(f"Failed to load relationships: {result.get('error')}")
            
            # Create additional relationships
            additional_rel_result = self.create_additional_relationships()
            if additional_rel_result.get("success"):
                relationships_created += additional_rel_result.get("relationships_created", 0)
            
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
                "error": f"Failed to load data files: {str(e)}"
            }
    
    def initialize_graph_with_data(self, company_name: Optional[str] = None) -> Dict[str, Any]:
        """Initialize the Neo4j graph with generated data files."""
        try:
            logger.info(f"Starting graph initialization for company: {company_name or 'latest'}")
            start_time = datetime.now()
            
            # Step 1: Reset the graph
            logger.info("Step 1: Resetting Neo4j graph...")
            reset_result = self.reset_graph()
            if not reset_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to reset graph: {reset_result.get('error')}",
                    "step": "reset",
                    "reset_result": reset_result
                }
            logger.info(f"Graph reset successful: {reset_result.get('message')}")
            
            # Step 2: Load data files
            logger.info("Step 2: Loading data files...")
            load_result = self.load_data_files(company_name)
            if not load_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to load data files: {load_result.get('error')}",
                    "step": "load_data",
                    "reset_result": reset_result,
                    "load_result": load_result
                }
            logger.info(f"Data loading successful: {load_result.get('nodes_created', 0)} nodes, {load_result.get('relationships_created', 0)} relationships")
            
            # Step 3: Verify final state
            logger.info("Step 3: Verifying final graph state...")
            status_result = self.check_database_status()
            if not status_result.get("success"):
                logger.warning(f"Could not verify final state: {status_result.get('error')}")
            else:
                logger.info(f"Final verification: {status_result.get('message')}")
            
            # Calculate timing
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "message": "Graph initialization completed successfully",
                "summary": {
                    "nodes_created": load_result.get("nodes_created", 0),
                    "relationships_created": load_result.get("relationships_created", 0),
                    "files_loaded": load_result.get("files_loaded", []),
                    "final_node_count": status_result.get("node_count", 0),
                    "final_relationship_count": status_result.get("relationship_count", 0),
                    "duration_seconds": duration
                },
                "reset_result": reset_result,
                "load_result": load_result,
                "final_status": status_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Graph initialization failed: {str(e)}",
                "step": "unknown"
            }
