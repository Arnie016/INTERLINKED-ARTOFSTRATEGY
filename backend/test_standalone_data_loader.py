#!/usr/bin/env python3
"""
Test script for the standalone data loader with Neo4j Aura connection.
Tests the StandaloneDataLoader with direct Neo4j integration.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_agents.standalone_data_loader import StandaloneDataLoader

def test_neo4j_connection():
    """Test the Neo4j Aura connection using the standalone data loader."""
    print("🧪 Testing Neo4j Aura Connection with Standalone Data Loader")
    print("=" * 70)
    
    try:
        # Initialize standalone data loader
        print("📋 Step 1: Initializing StandaloneDataLoader...")
        loader = StandaloneDataLoader()
        print("✅ StandaloneDataLoader initialized successfully")
        
        # Test database status
        print("\n🔍 Step 2: Testing database status...")
        status_result = loader.check_database_status()
        if status_result.get("success"):
            print(f"✅ Database status: {status_result.get('message')}")
            print(f"   📊 Current nodes: {status_result.get('node_count', 0)}")
            print(f"   🔗 Current relationships: {status_result.get('relationship_count', 0)}")
        else:
            print(f"❌ Database status check failed: {status_result.get('error')}")
            return False
        
        # Test graph reset
        print("\n🧹 Step 3: Testing graph reset...")
        reset_result = loader.reset_graph()
        if reset_result.get("success"):
            print(f"✅ Graph reset successful: {reset_result.get('message')}")
        else:
            print(f"❌ Graph reset failed: {status_result.get('error')}")
            return False
        
        # Test data file discovery
        print("\n📁 Step 4: Testing data file discovery...")
        # Try without company filter first to see what's available
        files = loader.find_latest_data_files()
        if files:
            print(f"✅ Found {len(files)} data files (no company filter):")
            for file_type, file_path in files.items():
                print(f"   📄 {file_type}: {os.path.basename(file_path)}")
        else:
            print("❌ No data files found at all")
            return False
        
        # Test data loading without company filter
        print("\n🚀 Step 5: Testing data loading...")
        load_result = loader.load_data_files()
        if load_result.get("success"):
            print(f"✅ Data loading successful: {load_result.get('message')}")
            print(f"   📊 Nodes created: {load_result.get('nodes_created', 0)}")
            print(f"   🔗 Relationships created: {load_result.get('relationships_created', 0)}")
            print(f"   📁 Files loaded: {len(load_result.get('files_loaded', []))}")
        else:
            print(f"❌ Data loading failed: {load_result.get('error')}")
            return False
        
        # Test final status
        print("\n📈 Step 6: Testing final database status...")
        final_status = loader.check_database_status()
        if final_status.get("success"):
            print(f"✅ Final status: {final_status.get('message')}")
        else:
            print(f"⚠️ Could not get final status: {final_status.get('error')}")
        
        # Close connection
        loader.close()
        print("\n🔌 Connection closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_workflow():
    """Test the complete workflow with graph initialization."""
    print("\n🧪 Testing Complete Workflow")
    print("=" * 50)
    
    try:
        # Initialize standalone data loader
        loader = StandaloneDataLoader()
        
        # Test complete workflow
        print("🚀 Testing complete graph initialization workflow...")
        init_result = loader.initialize_graph_with_data()
        
        if init_result.get("success"):
            summary = init_result.get("summary", {})
            print("✅ Complete workflow successful!")
            print(f"   📊 Nodes created: {summary.get('nodes_created', 0)}")
            print(f"   🔗 Relationships created: {summary.get('relationships_created', 0)}")
            print(f"   📁 Files loaded: {len(summary.get('files_loaded', []))}")
            print(f"   ⏱️ Duration: {summary.get('duration_seconds', 0):.2f} seconds")
            print(f"   📈 Final nodes: {summary.get('final_node_count', 0)}")
            print(f"   📈 Final relationships: {summary.get('final_relationship_count', 0)}")
            
            # Close connection
            loader.close()
            return True
        else:
            print(f"❌ Complete workflow failed: {init_result.get('error')}")
            loader.close()
            return False
            
    except Exception as e:
        print(f"❌ Complete workflow test failed with exception: {str(e)}")
        return False

def test_environment_variables():
    """Test if required environment variables are set."""
    print("🔧 Testing Environment Variables")
    print("=" * 40)
    
    required_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']
    optional_vars = ['NEO4J_DATABASE']
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'NEO4J_PASSWORD':
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: NOT SET (using default: neo4j)")
    
    return all_good

if __name__ == "__main__":
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Environment variables
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n❌ Environment variables test failed!")
        print("💡 Please check your .env file and ensure all required variables are set.")
        exit(1)
    
    # Test 2: Basic connection and operations
    success1 = test_neo4j_connection()
    
    # Test 3: Complete workflow
    success2 = test_complete_workflow()
    
    print(f"\n📋 Test Results:")
    print(f"   Environment Variables: {'✅ PASSED' if env_ok else '❌ FAILED'}")
    print(f"   Basic Connection Test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"   Complete Workflow Test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if env_ok and success1 and success2:
        print("\n🎉 All tests passed! Standalone data loader is working correctly with Neo4j Aura!")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
