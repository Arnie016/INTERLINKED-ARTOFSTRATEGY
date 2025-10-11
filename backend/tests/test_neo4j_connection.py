#!/usr/bin/env python3
"""
Simple Neo4j connection test
Tests basic connectivity using environment variables from .env file.
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables from .env file
load_dotenv()


def test_neo4j_connection():
    """Test Neo4j connection using environment variables"""
    print("🧪 Neo4j Connection Test")
    print("=" * 50)
    
    # Get credentials from environment variables
    URI = os.getenv('NEO4J_URI')
    USERNAME = os.getenv('NEO4J_USERNAME')
    PASSWORD = os.getenv('NEO4J_PASSWORD')
    DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    # Check if required environment variables are set
    if not URI:
        print("❌ NEO4J_URI not set in environment variables")
        print("   Make sure your .env file contains: NEO4J_URI=neo4j+ssc://your-instance.databases.neo4j.io")
        return False
    
    if not USERNAME:
        print("❌ NEO4J_USERNAME not set in environment variables")
        print("   Make sure your .env file contains: NEO4J_USERNAME=neo4j")
        return False
    
    if not PASSWORD:
        print("❌ NEO4J_PASSWORD not set in environment variables")
        print("   Make sure your .env file contains: NEO4J_PASSWORD=your_password")
        return False
    
    print("✅ Environment variables found")
    print(f"   URI: {URI}")
    print(f"   Username: {USERNAME}")
    print(f"   Database: {DATABASE}")
    print(f"   Password: {'*' * len(PASSWORD) if PASSWORD else 'NOT SET'}")
    
    try:
        print("\n🔌 Attempting connection...")
        
        # Create driver and test connection
        driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
        
        # Verify connectivity
        driver.verify_connectivity()
        print("✅ Connectivity verified!")
        
        # Get server info
        server_info = driver.get_server_info()
        print(f"✅ Server: {server_info.address}")
        
        # Test a simple query
        print("\n📝 Testing basic query...")
        with driver.session(database=DATABASE) as session:
            result = session.run("RETURN 'Hello Neo4j!' as message, datetime() as timestamp")
            record = result.single()
            print(f"✅ Query result: {record['message']}")
            print(f"✅ Timestamp: {record['timestamp']}")
            
            # Test database statistics
            print("\n📊 Getting database statistics...")
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_result.single()['count']
            print(f"✅ Node count: {node_count}")
            
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()['count']
            print(f"✅ Relationship count: {rel_count}")
            
            # Test labels
            label_result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
            labels = label_result.single()['labels']
            print(f"✅ Labels: {len(labels)} ({', '.join(labels) if labels else 'None'})")
        
        # Close connection
        driver.close()
        print("\n🎉 Connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Provide helpful error messages
        if "Unable to retrieve routing information" in str(e):
            print("\n💡 Troubleshooting tips:")
            print("   - Make sure your URI uses 'neo4j+ssc://' for self-signed certificates")
            print("   - Check if the Neo4j instance is running")
            print("   - Verify the instance URI is correct")
        elif "Authentication failed" in str(e) or "Unauthorized" in str(e):
            print("\n💡 Troubleshooting tips:")
            print("   - Check your username and password in the .env file")
            print("   - Verify credentials are correct in Neo4j Aura console")
        elif "Service unavailable" in str(e):
            print("\n💡 Troubleshooting tips:")
            print("   - Check if the Neo4j instance is running")
            print("   - Wait 60-90 seconds after instance creation")
            print("   - Verify the URI is correct")
        
        return False


def main():
    """Main test function"""
    print("Neo4j Connection Test")
    print("=" * 80)
    
    success = test_neo4j_connection()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ Connection test completed successfully!")
        print("🎉 Your Neo4j connection is working perfectly!")
    else:
        print("❌ Connection test failed!")
        print("💡 Check your .env file and Neo4j instance status")
    print("=" * 80)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)