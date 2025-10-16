#!/usr/bin/env python3
"""
Simple connection test for the standalone data loader.
Tests basic connectivity using the StandaloneDataLoader class.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_agents.standalone_data_loader import StandaloneDataLoader

def test_standalone_connection():
    """Test connection using the standalone data loader"""
    print("🧪 Standalone Data Loader Connection Test")
    print("=" * 60)
    
    try:
        print("📋 Initializing StandaloneDataLoader...")
        loader = StandaloneDataLoader()
        print("✅ StandaloneDataLoader initialized successfully")
        
        print("\n🔍 Testing database status...")
        status_result = loader.check_database_status()
        
        if status_result.get("success"):
            print("✅ Connection successful!")
            print(f"   Status: {status_result.get('status')}")
            print(f"   Message: {status_result.get('message')}")
            print(f"   Node count: {status_result.get('node_count', 0)}")
            print(f"   Relationship count: {status_result.get('relationship_count', 0)}")
            
            # Test a simple query
            print("\n📝 Testing basic query...")
            database = os.getenv('NEO4J_DATABASE', 'neo4j')
            with loader.driver.session(database=database) as session:
                result = session.run("RETURN 'Hello from StandaloneDataLoader!' as message, datetime() as timestamp")
                record = result.single()
                print(f"✅ Query result: {record['message']}")
                print(f"✅ Timestamp: {record['timestamp']}")
            
            # Close connection
            loader.close()
            print("\n🔌 Connection closed successfully")
            return True
        else:
            print(f"❌ Connection failed: {status_result.get('error')}")
            loader.close()
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
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
    print("Standalone Data Loader Connection Test")
    print("=" * 80)
    
    success = test_standalone_connection()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ Connection test completed successfully!")
        print("🎉 Your StandaloneDataLoader is working perfectly with Neo4j Aura!")
    else:
        print("❌ Connection test failed!")
        print("💡 Check your .env file and Neo4j instance status")
    print("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
