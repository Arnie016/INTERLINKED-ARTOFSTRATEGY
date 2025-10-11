#!/usr/bin/env python3
"""
Graph Query Agent using Bedrock AgentCore and Nova
Connects to Neo4j and responds to user queries about organizational data.
"""

import os
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import boto3
from neo4j import GraphDatabase
from pydantic import BaseModel

# Load environment variables
load_dotenv()


class GraphQueryTool(BaseModel):
    """Tool for querying Neo4j graph database"""
    name: str = "query_graph"
    description: str = "Query the organizational graph database to find relationships, people, processes, and inefficiencies"


class GraphAgent:
    """Agent that combines Bedrock Nova with Neo4j graph queries"""
    
    def __init__(self):
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Initialize Neo4j driver
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )
        
        # Bedrock model configuration
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"  # Using Claude 3 Haiku for reliability
        
    def query_neo4j(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute Cypher query against Neo4j"""
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(cypher_query)
                return [record.data() for record in result]
        except Exception as e:
            return [{"error": f"Query failed: {str(e)}"}]
    
    def call_bedrock(self, prompt: str, tools: Optional[List[Dict]] = None) -> str:
        """Call Bedrock Claude with optional tool use"""
        
        # Prepare the request body
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 1000,
                "temperature": 0.1
            }
        }
        
        # Add tools if provided
        if tools:
            request_body["toolConfig"] = {
                "tools": tools,
                "toolChoice": {"auto": {}}
            }
        
        try:
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
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
            return f"Error calling Bedrock: {str(e)}"
    
    def _handle_tool_use(self, tool_use: Dict, original_prompt: str) -> str:
        """Handle tool use requests from Nova"""
        tool_name = tool_use['name']
        tool_input = tool_use['input']
        
        if tool_name == "query_graph":
            # Execute the Cypher query
            cypher_query = tool_input.get('query', '')
            results = self.query_neo4j(cypher_query)
            
            # Send results back to Claude for interpretation
            follow_up_prompt = f"""
            Original question: {original_prompt}
            
            Graph query executed: {cypher_query}
            Results: {json.dumps(results, indent=2)}
            
            Please interpret these results and provide a helpful response to the user's question.
            """
            
            return self.call_bedrock(follow_up_prompt)
        
        return f"Unknown tool: {tool_name}"
    
    def process_query(self, user_query: str) -> str:
        """Main method to process user queries"""
        
        # Define available tools
        tools = [
            {
                "toolSpec": {
                    "name": "query_graph",
                    "description": "Query the Neo4j graph database to find organizational data, relationships, people, processes, and inefficiencies",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Cypher query to execute against the Neo4j database"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            }
        ]
        
        # Enhanced prompt with graph context
        enhanced_prompt = f"""
        You are an organizational analysis agent with access to a Neo4j graph database containing:
        - People (nodes with properties like name, role, department)
        - Processes (nodes representing business processes)
        - Relationships like PERFORMS, OWNS, DEPENDS_ON, REPORTS_TO
        
        User question: {user_query}
        
        If you need to query the graph database to answer this question, use the query_graph tool with appropriate Cypher queries.
        
        Common query patterns:
        - Find people: MATCH (p:Person) WHERE p.name CONTAINS 'Alice' RETURN p
        - Find processes: MATCH (proc:Process) RETURN proc.name, proc.description
        - Find relationships: MATCH (p:Person)-[r:PERFORMS]->(proc:Process) RETURN p.name, proc.name
        - Find bottlenecks: MATCH (proc:Process) WHERE NOT (proc)<-[:PERFORMS]-(:Person) RETURN proc.name
        """
        
        return self.call_bedrock(enhanced_prompt, tools)
    
    def close(self):
        """Clean up connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()


def main():
    """Test the agent"""
    agent = GraphAgent()
    
    try:
        # Test queries
        test_queries = [
            "Show me all people in the organization",
            "What processes are unassigned?",
            "Who reports to Alice?",
            "Find any bottlenecks in our processes"
        ]
        
        for query in test_queries:
            print(f"\n🤔 User: {query}")
            print("🤖 Agent:", agent.process_query(query))
            print("-" * 50)
            
    finally:
        agent.close()


if __name__ == "__main__":
    main()