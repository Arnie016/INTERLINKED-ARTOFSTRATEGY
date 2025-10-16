"""
Data Loading Orchestrator - Coordinates the complete data loading workflow.

This orchestrator handles the initial graph loading process, ensuring that only
the data_loader_agent is used for loading generated data into Neo4j, while
keeping the extractor_agent separate for LLM-driven updates.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from .data_loader_agent import DataLoaderAgent
    from ...config.agent_config import AgentConfig
    from ...config.database_config import DatabaseConfig
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from agents.data_agents.data_loader_agent import DataLoaderAgent
    from config.agent_config import AgentConfig
    from config.database_config import DatabaseConfig


class DataLoadingOrchestrator:
    """
    Orchestrates the complete data loading workflow for initial graph setup.
    
    This class ensures that only the data_loader_agent is used for loading
    generated data files, providing a clean separation between initial data
    loading and LLM-driven updates.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize the Data Loading Orchestrator.
        
        Args:
            config: Optional agent configuration
            db_config: Optional database configuration
        """
        if config is None:
            try:
                from ...config.agent_config import get_agent_config
            except ImportError:
                from config.agent_config import get_agent_config
            config = get_agent_config("extractor_agent")
        
        if db_config is None:
            try:
                from ...config.database_config import get_database_config
            except ImportError:
                from config.database_config import get_database_config
            db_config = get_database_config()
        
        self.data_loader_agent = DataLoaderAgent(config, db_config)
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    
    def initialize_graph_with_data(self, company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize the Neo4j graph with generated data files.
        
        This is the main method for initial graph loading. It:
        1. Resets the graph to ensure a clean state
        2. Loads entities from the latest data files
        3. Creates relationships from the latest data files
        4. Creates additional implicit relationships
        5. Verifies the final state
        
        Args:
            company_name: Optional company name to filter data files
        
        Returns:
            Dict containing the complete loading results
        """
        try:
            print(f"🚀 Starting graph initialization for company: {company_name or 'latest'}")
            start_time = datetime.now()
            
            # Step 1: Reset the graph
            print("🧹 Step 1: Resetting Neo4j graph...")
            reset_result = self.data_loader_agent.reset_graph({})
            if not reset_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to reset graph: {reset_result.get('error')}",
                    "step": "reset",
                    "reset_result": reset_result
                }
            print(f"✅ Graph reset successful: {reset_result.get('message')}")
            
            # Step 2: Load data files
            print("📁 Step 2: Loading data files...")
            load_result = self.data_loader_agent.load_data_files({"company_name": company_name})
            if not load_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to load data files: {load_result.get('error')}",
                    "step": "load_data",
                    "reset_result": reset_result,
                    "load_result": load_result
                }
            print(f"✅ Data loading successful: {load_result.get('nodes_created', 0)} nodes, {load_result.get('relationships_created', 0)} relationships")
            
            # Step 3: Verify final state
            print("🔍 Step 3: Verifying final graph state...")
            status_result = self.data_loader_agent.check_database_status({})
            if not status_result.get("success"):
                print(f"⚠️ Warning: Could not verify final state: {status_result.get('error')}")
            else:
                print(f"✅ Final verification: {status_result.get('message')}")
            
            # Calculate timing
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "message": "Graph initialization completed successfully",
                "summary": {
                    "nodes_created": load_result.get("nodes_created", 0),
                    "relationships_created": load_result.get("relationships_created", 0),
                    "additional_relationships": load_result.get("additional_relationships", 0),
                    "files_loaded": load_result.get("loaded_files", []),
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
    
    def load_specific_company_data(self, company_name: str) -> Dict[str, Any]:
        """
        Load data for a specific company.
        
        Args:
            company_name: Name of the company to load data for
        
        Returns:
            Dict containing loading results
        """
        return self.initialize_graph_with_data(company_name)
    
    def get_available_data_files(self) -> Dict[str, Any]:
        """
        Get information about available data files.
        
        Returns:
            Dict containing information about available data files
        """
        try:
            if not os.path.exists(self.data_dir):
                return {
                    "success": False,
                    "error": f"Data directory does not exist: {self.data_dir}",
                    "files": []
                }
            
            # Get all JSON files
            json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
            
            # Group files by company and timestamp
            companies = {}
            for filename in json_files:
                # Parse filename: CompanyName_Type_YYYY-MM-DD_HHMMSS.json
                parts = filename.split('_')
                if len(parts) >= 4:
                    company_name = '_'.join(parts[:-3])  # Everything before the last 3 parts
                    file_type = parts[-3]  # Entities, Relationships, etc.
                    timestamp = f"{parts[-2]}_{parts[-1].replace('.json', '')}"
                    
                    if company_name not in companies:
                        companies[company_name] = {}
                    
                    if timestamp not in companies[company_name]:
                        companies[company_name][timestamp] = {}
                    
                    companies[company_name][timestamp][file_type] = {
                        "filename": filename,
                        "filepath": os.path.join(self.data_dir, filename),
                        "modified": os.path.getmtime(os.path.join(self.data_dir, filename))
                    }
            
            return {
                "success": True,
                "data_directory": self.data_dir,
                "companies": companies,
                "total_files": len(json_files)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get available data files: {str(e)}",
                "files": []
            }
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get current graph statistics.
        
        Returns:
            Dict containing graph statistics
        """
        return self.data_loader_agent.check_database_status({})
    
    def reset_graph_only(self) -> Dict[str, Any]:
        """
        Reset the graph without loading any data.
        
        Returns:
            Dict containing reset results
        """
        return self.data_loader_agent.reset_graph({})
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about orchestrator capabilities.
        
        Returns:
            Dict containing capability information
        """
        return {
            "name": "Data Loading Orchestrator",
            "description": "Coordinates the complete data loading workflow for initial graph setup",
            "capabilities": [
                "Graph initialization with data files",
                "Company-specific data loading",
                "Data file discovery and management",
                "Graph statistics and monitoring",
                "Clean graph reset functionality"
            ],
            "data_directory": self.data_dir,
            "data_loader_agent": self.data_loader_agent.get_capabilities()
        }
