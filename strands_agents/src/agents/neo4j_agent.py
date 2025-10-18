"""
Neo4j Agent

A generic agent that can interact with any Neo4j database to answer questions
about organizational graph data. The agent dynamically adapts to different
organizational structures and data schemas.
"""

import sys
import os
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strands import Agent
from tools.neo4j_tool import Neo4jTool


class Neo4jAgent:
    """Generic agent that can query and analyze any Neo4j organizational graph data."""
    
    def __init__(self, model: str = "apac.anthropic.claude-sonnet-4-20250514-v1:0"):
        """Initialize the Neo4j agent."""
        self.agent = Agent(model=model)
        self.neo4j_tool = Neo4jTool()
    
    def query(self, question: str) -> str:
        """
        Answer a question about the organizational data.
        
        Args:
            question: The question to answer
            
        Returns:
            The agent's response
        """
        try:
            # First, gather relevant data from Neo4j based on the question
            context_data = self._gather_context(question)
            
            # Create a comprehensive prompt with the data
            system_prompt = f"""
            You are an organizational data analyst with access to a graph database containing organizational information.

            Current database context:
            {context_data}

            Based on the available data, answer the user's question with specific, data-driven information.
            If the data doesn't contain enough information to answer the question completely, say so clearly.
            Focus on the actual data available rather than making assumptions about organizational structure.
            """
            
            # Set the system prompt
            self.agent.system_prompt = system_prompt
            
            # Get response from agent
            response = self.agent(question)
            
            # Extract the actual content from AgentResult
            if hasattr(response, 'message') and 'content' in response.message:
                content = response.message['content']
                if isinstance(content, list) and len(content) > 0:
                    return content[0].get('text', str(content[0]))
                else:
                    return str(content)
            else:
                return str(response)
                
        except Exception as e:
            return f"Error processing query: {e}"
    
    def _gather_context(self, question: str) -> str:
        """Gather relevant context data from Neo4j based on the question."""
        try:
            context_parts = []
            question_lower = question.lower()
            
            # Get database stats
            stats = self.neo4j_tool.get_database_stats()
            if 'error' not in stats:
                context_parts.append(f"Database contains {stats['total_nodes']} nodes and {stats['total_relationships']} relationships.")
            
            # Get schema information
            schema = self.neo4j_tool.get_database_schema()
            if 'error' not in schema:
                context_parts.append(f"Available node types: {', '.join(schema['labels'])}")
                context_parts.append(f"Available relationship types: {', '.join(schema['relationship_types'])}")
            
            # Dynamically gather data based on available node types and question keywords
            available_labels = schema.get('labels', []) if 'error' not in schema else []
            
            # For each available label, check if it's relevant to the question
            for label in available_labels:
                if self._is_label_relevant_to_question(label, question_lower):
                    nodes = self.neo4j_tool.get_nodes_by_label(label, limit=10)
                    if nodes:
                        context_parts.append(self._format_nodes_for_context(label, nodes))
            
            return "\n\n".join(context_parts) if context_parts else "No relevant data found."
            
        except Exception as e:
            return f"Error gathering context: {e}"
    
    def _is_label_relevant_to_question(self, label: str, question_lower: str) -> bool:
        """Determine if a node label is relevant to the question."""
        # Common organizational entity keywords
        relevance_keywords = {
            'person': ['person', 'people', 'employee', 'staff', 'worker', 'individual', 'member', 'user'],
            'department': ['department', 'dept', 'team', 'division', 'unit', 'group', 'organization'],
            'project': ['project', 'initiative', 'program', 'task', 'assignment', 'work'],
            'role': ['role', 'position', 'job', 'title', 'function', 'responsibility'],
            'skill': ['skill', 'competency', 'expertise', 'ability', 'capability'],
            'system': ['system', 'tool', 'platform', 'application', 'software', 'technology'],
            'process': ['process', 'workflow', 'procedure', 'method', 'practice'],
            'location': ['location', 'office', 'site', 'building', 'place', 'address'],
            'budget': ['budget', 'cost', 'expense', 'financial', 'money', 'funding'],
            'status': ['status', 'state', 'condition', 'phase', 'stage']
        }
        
        # Check if the label name or any of its keywords appear in the question
        label_lower = label.lower()
        for category, keywords in relevance_keywords.items():
            if (category in label_lower or 
                any(keyword in label_lower for keyword in keywords) or
                any(keyword in question_lower for keyword in keywords)):
                return True
        
        return False
    
    def _format_nodes_for_context(self, label: str, nodes: List[Dict[str, Any]]) -> str:
        """Format nodes for context display in a generic way."""
        try:
            formatted_items = []
            
            for node in nodes:
                properties = node.get('properties', {})
                
                # Try to find common identifying properties
                name = (properties.get('name') or 
                       properties.get('title') or 
                       properties.get('label') or 
                       properties.get('id') or 
                       'Unknown')
                
                # Try to find common descriptive properties
                description_parts = []
                for key, value in properties.items():
                    if key.lower() in ['role', 'type', 'status', 'department', 'budget', 'location']:
                        if value and str(value).strip():
                            description_parts.append(f"{key}: {value}")
                
                description = f" ({', '.join(description_parts)})" if description_parts else ""
                formatted_items.append(f"- {name}{description}")
            
            return f"{label} entities:\n" + "\n".join(formatted_items)
            
        except Exception as e:
            return f"Error formatting {label} nodes: {e}"


def main():
    """Test the Neo4j agent."""
    print("🤖 Neo4j Agent Test")
    print("=" * 40)
    
    try:
        # Create agent
        agent = Neo4jAgent()
        
        # Test questions
        test_questions = [
            "What types of entities exist in this database?",
            "What are the main organizational units?",
            "What projects or initiatives are tracked?",
            "Who are the key individuals in the organization?",
            "What is the overall structure of the data?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. Question: {question}")
            print("-" * 50)
            response = agent.query(question)
            print(f"Answer: {response}")
            
            if i < len(test_questions):
                input("\nPress Enter to continue to next question...")
        
        print("\n✅ Neo4j agent test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
