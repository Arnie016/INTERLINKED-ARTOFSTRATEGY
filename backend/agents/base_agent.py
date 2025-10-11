"""
Base Agent class for the Agent Tool Architecture.

This module provides the foundational agent class that all specialized agents
inherit from, implementing the tool registry system and common functionality.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
from datetime import datetime

import boto3
from neo4j import GraphDatabase

try:
    from ..tools import get_tools_for_role, ALL_TOOLS
    from ..config import AgentConfig, DatabaseConfig, validate_role_access, validate_tool_parameters
    from ..models import validate_entity_data, validate_relationship_data
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools import get_tools_for_role, ALL_TOOLS
    from config import AgentConfig, DatabaseConfig, validate_role_access, validate_tool_parameters
    from models import validate_entity_data, validate_relationship_data


class BaseAgent(ABC):
    """
    Base class for all agents in the Agent Tool Architecture.
    
    This class provides common functionality including:
    - Tool registry and discovery
    - Role-based access control
    - Database connection management
    - Model interaction
    - Safety and validation
    """
    
    def __init__(self, config: AgentConfig, db_config: DatabaseConfig):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration
            db_config: Database configuration
        """
        self.config = config
        self.db_config = db_config
        self.role = config.role
        self.name = config.name
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Initialize database connection
        self.driver = self._setup_database()
        
        # Initialize model client
        self.model_client = self._setup_model_client()
        
        # Initialize tool registry
        self.available_tools = self._load_tools()
        
        # Initialize conversation memory if enabled
        self.memory = [] if config.enable_memory else None
        
        self.logger.info(f"Initialized {self.name} with role: {self.role}")
        self.logger.info(f"Available tools: {list(self.available_tools.keys())}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent."""
        logger = logging.getLogger(f"{self.__class__.__name__}.{self.name}")
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_database(self) -> GraphDatabase:
        """Setup Neo4j database connection."""
        try:
            # Build driver configuration
            driver_config = {
                "auth": (self.db_config.neo4j_username, self.db_config.neo4j_password),
                "max_connection_pool_size": self.db_config.max_connection_pool_size,
                "connection_timeout": self.db_config.connection_timeout,
                "max_transaction_retry_time": self.db_config.max_transaction_retry_time,
            }
            
            # Only add SSL configuration if URI doesn't already specify it
            # URI schemes like neo4j+ssc://, neo4j+s:// already include SSL settings
            uri = self.db_config.neo4j_uri.lower()
            if self.db_config.enable_ssl and not any(scheme in uri for scheme in ['+ssc', '+s']):
                driver_config["encrypted"] = True
            
            driver = GraphDatabase.driver(self.db_config.neo4j_uri, **driver_config)
            
            # Test connection
            with driver.session() as session:
                session.run("RETURN 1")
            
            self.logger.info("Database connection established successfully")
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def _setup_model_client(self):
        """Setup model client based on configuration."""
        if self.config.model_provider == "bedrock":
            return boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.config.model_provider}")
    
    def _load_tools(self) -> Dict[str, Dict[str, Any]]:
        """Load tools available to this agent's role."""
        role_tools = get_tools_for_role(self.role)
        available_tools = {}
        
        for tool_name in role_tools:
            if tool_name in ALL_TOOLS:
                available_tools[tool_name] = ALL_TOOLS[tool_name]
            else:
                self.logger.warning(f"Tool {tool_name} not found in registry")
        
        return available_tools
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.available_tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        return self.available_tools.get(tool_name)
    
    def validate_tool_access(self, tool_name: str) -> bool:
        """Validate if this agent has access to a specific tool."""
        return validate_role_access(self.role, tool_name)
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
        
        Returns:
            Dict containing tool execution result
        """
        # Validate tool access
        if not self.validate_tool_access(tool_name):
            return {
                "success": False,
                "error": f"Agent role '{self.role}' does not have access to tool '{tool_name}'"
            }
        
        # Get tool information
        tool_info = self.get_tool_info(tool_name)
        if not tool_info:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        # Validate parameters
        validation_result = validate_tool_parameters(tool_name, parameters)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": f"Tool parameter validation failed: {validation_result['issues']}"
            }
        
        # Log tool execution
        if self.config.log_tool_calls:
            self.logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
        
        try:
            # Execute the tool
            tool_function = tool_info["function"]
            result = tool_function(self.driver, **parameters)
            
            # Log result
            if self.config.log_tool_calls:
                self.logger.info(f"Tool {tool_name} executed successfully")
            
            return result
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def call_model(self, prompt: str, tools: Optional[List[Dict]] = None) -> str:
        """
        Call the configured model with optional tool use.
        
        Args:
            prompt: Input prompt
            tools: Optional list of tools to make available
        
        Returns:
            Model response
        """
        try:
            if self.config.model_provider == "bedrock":
                return self._call_bedrock(prompt, tools)
            else:
                raise ValueError(f"Unsupported model provider: {self.config.model_provider}")
                
        except Exception as e:
            error_msg = f"Model call failed: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def _call_bedrock(self, prompt: str, tools: Optional[List[Dict]] = None) -> str:
        """Call Bedrock model."""
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
        }
        
        # Add tools if provided
        if tools and self.config.enable_tools:
            request_body["toolConfig"] = {
                "tools": tools,
                "toolChoice": {"auto": {}}
            }
        
        try:
            response = self.model_client.converse(
                modelId=self.config.model_id,
                **request_body
            )
            
            # Handle tool use in response
            output_message = response['output']['message']
            
            if 'toolUse' in output_message.get('content', [{}])[0]:
                # Process tool use
                tool_use = output_message['content'][0]['toolUse']
                return self._handle_tool_use(tool_use, prompt)
            else:
                # Regular text response
                return output_message['content'][0]['text']
                
        except Exception as e:
            raise Exception(f"Bedrock API call failed: {str(e)}")
    
    def _handle_tool_use(self, tool_use: Dict, original_prompt: str) -> str:
        """Handle tool use requests from the model."""
        tool_name = tool_use['name']
        tool_input = tool_use['input']
        
        # Execute the tool
        result = self.execute_tool(tool_name, tool_input)
        
        # Send results back to model for interpretation
        follow_up_prompt = f"""
        Original question: {original_prompt}
        
        Tool executed: {tool_name}
        Tool input: {json.dumps(tool_input, indent=2)}
        Tool result: {json.dumps(result, indent=2)}
        
        Please interpret these results and provide a helpful response to the user's question.
        """
        
        return self.call_model(follow_up_prompt)
    
    def get_tools_for_model(self) -> List[Dict]:
        """Get tools formatted for model consumption."""
        tools = []
        
        for tool_name, tool_info in self.available_tools.items():
            # Get function signature for input schema
            import inspect
            sig = inspect.signature(tool_info["function"])
            
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == "driver":  # Skip driver parameter
                    continue
                
                # Determine parameter type
                param_type = "string"
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}"
                }
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            tool_spec = {
                "toolSpec": {
                    "name": tool_name,
                    "description": tool_info["description"],
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": properties,
                            "required": required
                        }
                    }
                }
            }
            
            tools.append(tool_spec)
        
        return tools
    
    def add_to_memory(self, message: str, role: str = "user"):
        """Add message to conversation memory."""
        if self.memory is not None:
            self.memory.append({
                "role": role,
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Trim memory if it exceeds max size
            if len(self.memory) > self.config.max_memory_size:
                self.memory = self.memory[-self.config.max_memory_size:]
    
    def get_memory_context(self) -> str:
        """Get conversation memory as context string."""
        if not self.memory:
            return ""
        
        context_parts = []
        for msg in self.memory[-5:]:  # Last 5 messages
            context_parts.append(f"{msg['role']}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def clear_memory(self):
        """Clear conversation memory."""
        if self.memory is not None:
            self.memory.clear()
    
    @abstractmethod
    def process_query(self, query: str) -> str:
        """
        Process a user query. Must be implemented by subclasses.
        
        Args:
            query: User query string
        
        Returns:
            Response string
        """
        pass
    
    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.close()
            self.logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
