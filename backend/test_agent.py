#!/usr/bin/env python3
"""
Test script for the Graph Agent
"""

from graph_agent import GraphAgent


def test_basic_functionality():
    """Test basic agent functionality"""
    print("🧪 Testing Graph Agent")
    print("=" * 50)
    
    agent = GraphAgent()
    
    try:
        # Test 1: Simple query without graph access
        print("\n1️⃣ Testing basic Bedrock response...")
        response = agent.call_bedrock("Hello, can you introduce yourself?")
        print(f"✅ Response: {response}")
        
        # Test 2: Neo4j connection test
        print("\n2️⃣ Testing Neo4j connection...")
        results = agent.query_neo4j("RETURN 'Hello Neo4j!' as message")
        print(f"✅ Neo4j test: {results}")
        
        # Test 3: Full agent query
        print("\n3️⃣ Testing full agent query...")
        response = agent.process_query("How many nodes are in the graph?")
        print(f"✅ Agent response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        agent.close()


if __name__ == "__main__":
    test_basic_functionality()