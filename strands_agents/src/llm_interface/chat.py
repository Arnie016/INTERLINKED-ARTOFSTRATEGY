"""
Simple Chat Interface for Agents

A minimal chat interface that allows you to interact with agents and their tools
directly from the IDE terminal. Just run this file and start chatting!
"""

import sys
import os
from typing import Optional

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.query_agent import main as query_agent_main
from agents.neo4j_agent import Neo4jAgent
from tools.neo4j_tool import Neo4jTool


class ChatInterface:
    """Simple chat interface for interacting with agents."""
    
    def __init__(self):
        """Initialize the chat interface."""
        self.neo4j_agent = None
        self.neo4j_tool = None
        self.running = True
        
        print("🤖 Chat Interface Initialized")
        print("Available agents:")
        print("  - Query Agent (basic Claude)")
        print("  - Neo4j Agent (organizational data)")
        print("  - Neo4j Tool (direct database access)")
        print("\nType 'help' for commands or start chatting!")
        print("=" * 50)
    
    def initialize_neo4j_agent(self):
        """Initialize Neo4j agent if not already done."""
        if self.neo4j_agent is None:
            try:
                print("🔄 Initializing Neo4j agent...")
                self.neo4j_agent = Neo4jAgent()
                print("✅ Neo4j agent ready!")
            except Exception as e:
                print(f"❌ Failed to initialize Neo4j agent: {e}")
                return False
        return True
    
    def initialize_neo4j_tool(self):
        """Initialize Neo4j tool if not already done."""
        if self.neo4j_tool is None:
            try:
                print("🔄 Initializing Neo4j tool...")
                self.neo4j_tool = Neo4jTool()
                print("✅ Neo4j tool ready!")
            except Exception as e:
                print(f"❌ Failed to initialize Neo4j tool: {e}")
                return False
        return True
    
    def show_help(self):
        """Show available commands."""
        print("\n📋 Available Commands:")
        print("  help                    - Show this help message")
        print("  quit, exit, q           - Exit the chat")
        print("  neo4j                   - Switch to Neo4j agent mode")
        print("  query                   - Switch to basic query agent mode")
        print("  tool                    - Switch to direct Neo4j tool mode")
        print("  stats                   - Show database statistics")
        print("  schema                  - Show database schema")
        print("  clear                   - Clear the screen")
        print("\n💡 Just type your question to chat with the current agent!")
        print("   Example: 'What departments exist in the organization?'")
    
    def show_stats(self):
        """Show database statistics."""
        if not self.initialize_neo4j_tool() or self.neo4j_tool is None:
            return
        
        try:
            stats = self.neo4j_tool.get_database_stats()
            if 'error' not in stats:
                print(f"\n📊 Database Statistics:")
                print(f"  Total Nodes: {stats['total_nodes']:,}")
                print(f"  Total Relationships: {stats['total_relationships']:,}")
                print(f"  Labels: {len(stats['schema']['labels'])}")
                print(f"  Relationship Types: {len(stats['schema']['relationship_types'])}")
            else:
                print(f"❌ Error getting stats: {stats['error']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_schema(self):
        """Show database schema."""
        if not self.initialize_neo4j_tool() or self.neo4j_tool is None:
            return
        
        try:
            schema = self.neo4j_tool.get_database_schema()
            if 'error' not in schema:
                print(f"\n🏷️  Database Schema:")
                print(f"  Labels: {schema['labels']}")
                print(f"  Relationship Types: {schema['relationship_types']}")
            else:
                print(f"❌ Error getting schema: {schema['error']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def chat_with_neo4j_agent(self, message: str):
        """Chat with the Neo4j agent."""
        if not self.initialize_neo4j_agent() or self.neo4j_agent is None:
            return
        
        try:
            print("🤖 Neo4j Agent: ", end="", flush=True)
            response = self.neo4j_agent.query(message)
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def chat_with_query_agent(self, message: str):
        """Chat with the basic query agent."""
        try:
            print("🤖 Query Agent: ", end="", flush=True)
            # Create a simple agent for this message
            from strands import Agent
            agent = Agent(model="apac.anthropic.claude-sonnet-4-20250514-v1:0")
            response = agent(message)
            
            # Extract the actual content from AgentResult
            if hasattr(response, 'message') and 'content' in response.message:
                content = response.message['content']
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get('text', str(content[0]))
                    print(text_content)
                else:
                    print(str(content))
            else:
                print(str(response))
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def use_neo4j_tool(self, message: str):
        """Use Neo4j tool directly."""
        if not self.initialize_neo4j_tool() or self.neo4j_tool is None:
            return
        
        try:
            # Simple command parsing for tool usage
            message_lower = message.lower().strip()
            
            if "all nodes" in message_lower or "nodes" in message_lower:
                nodes = self.neo4j_tool.get_all_nodes(limit=10)
                print(f"\n📋 Found {len(nodes)} nodes (showing first 10):")
                for node in nodes:
                    labels = ":".join(node['labels']) if node['labels'] else "No labels"
                    name = node['properties'].get('name', 'Unknown')
                    print(f"  - {labels}: {name}")
            
            elif "all relationships" in message_lower or "relationships" in message_lower:
                rels = self.neo4j_tool.get_all_relationships(limit=10)
                print(f"\n🔗 Found {len(rels)} relationships (showing first 10):")
                for rel in rels:
                    start_name = rel['start_node']['properties'].get('name', 'Unknown')
                    end_name = rel['end_node']['properties'].get('name', 'Unknown')
                    print(f"  - {start_name} -[{rel['type']}]-> {end_name}")
            
            elif "people" in message_lower or "person" in message_lower:
                people = self.neo4j_tool.get_nodes_by_label("Person", limit=10)
                print(f"\n👥 Found {len(people)} people:")
                for person in people:
                    name = person['properties'].get('name', 'Unknown')
                    role = person['properties'].get('role', 'Unknown role')
                    dept = person['properties'].get('department', 'Unknown dept')
                    print(f"  - {name} ({role}) - {dept}")
            
            elif "departments" in message_lower or "department" in message_lower:
                depts = self.neo4j_tool.get_nodes_by_label("Department", limit=10)
                print(f"\n🏢 Found {len(depts)} departments:")
                for dept in depts:
                    name = dept['properties'].get('name', 'Unknown')
                    budget = dept['properties'].get('budget', 'Unknown budget')
                    print(f"  - {name} (Budget: {budget})")
            
            else:
                print("💡 Try: 'all nodes', 'all relationships', 'people', or 'departments'")
                print("   Or use the Neo4j agent for more complex queries!")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def process_command(self, message: str):
        """Process special commands."""
        message_lower = message.lower().strip()
        
        if message_lower in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            self.running = False
            return True
        
        elif message_lower == 'help':
            self.show_help()
            return True
        
        elif message_lower == 'clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            return True
        
        elif message_lower == 'stats':
            self.show_stats()
            return True
        
        elif message_lower == 'schema':
            self.show_schema()
            return True
        
        return False
    
    def run(self):
        """Main chat loop."""
        current_mode = "neo4j"  # Default to Neo4j agent
        
        while self.running:
            try:
                # Show current mode
                mode_indicators = {
                    "neo4j": "🤖 Neo4j Agent",
                    "query": "🤖 Query Agent", 
                    "tool": "🔧 Neo4j Tool"
                }
                
                user_input = input(f"\n{mode_indicators[current_mode]} > ").strip()
                
                if not user_input:
                    continue
                
                # Check for mode switching
                if user_input.lower() == "neo4j":
                    current_mode = "neo4j"
                    print("✅ Switched to Neo4j Agent mode")
                    continue
                elif user_input.lower() == "query":
                    current_mode = "query"
                    print("✅ Switched to Query Agent mode")
                    continue
                elif user_input.lower() == "tool":
                    current_mode = "tool"
                    print("✅ Switched to Neo4j Tool mode")
                    continue
                
                # Process commands
                if self.process_command(user_input):
                    continue
                
                # Route to appropriate handler
                if current_mode == "neo4j":
                    self.chat_with_neo4j_agent(user_input)
                elif current_mode == "query":
                    self.chat_with_query_agent(user_input)
                elif current_mode == "tool":
                    self.use_neo4j_tool(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")


def main():
    """Main function to start the chat interface."""
    try:
        chat = ChatInterface()
        chat.run()
    except Exception as e:
        print(f"❌ Failed to start chat interface: {e}")


if __name__ == "__main__":
    main()
