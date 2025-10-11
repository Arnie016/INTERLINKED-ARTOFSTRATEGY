#!/usr/bin/env python3
"""
Test the Graph Agent with sample data
"""

import time
from graph_agent import GraphAgent
from setup_sample_data import setup_sample_data

def test_with_sample_data():
    """Test agent with actual organizational data"""
    
    
    print("\n🧪 Testing Graph Agent with Data")
    print("=" * 50)
    
    agent = GraphAgent()
    
    try:
        # Test direct Neo4j queries first
        print("\n1️⃣ Testing direct graph queries...")
        
        queries = [
            ("Count all people", "MATCH (p:Person) RETURN count(p) as people_count"),
            ("List all processes", "MATCH (proc:Process) RETURN proc.name as process_name"),
            ("Find who performs what", "MATCH (p:Person)-[:PERFORMS]->(proc:Process) RETURN p.name as person, proc.name as process")
        ]
        
        for desc, query in queries:
            print(f"\n   {desc}:")
            results = agent.query_neo4j(query)
            print(f"   Results: {results}")
        
        # Test simple agent queries (without full LLM to avoid throttling)
        print("\n2️⃣ Testing basic agent functionality...")
        
        # Simple response without tools
        response = agent.call_bedrock("What is organizational analysis?")
        print(f"✅ Basic response: {response[:100]}...")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        agent.close()

if __name__ == "__main__":
    test_with_sample_data()