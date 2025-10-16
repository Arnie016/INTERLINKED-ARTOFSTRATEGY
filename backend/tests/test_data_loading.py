#!/usr/bin/env python3
"""
Test script for the data loading workflow.
Tests the DataLoadingOrchestrator with the existing sample data.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_agents.data_loading_orchestrator import DataLoadingOrchestrator

def test_data_loading():
    """Test the complete data loading workflow."""
    print("🧪 Testing Data Loading Workflow")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        print("📋 Step 1: Initializing DataLoadingOrchestrator...")
        orchestrator = DataLoadingOrchestrator()
        print("✅ Orchestrator initialized successfully")
        
        # Check available data files
        print("\n📁 Step 2: Checking available data files...")
        files_result = orchestrator.get_available_data_files()
        if files_result.get("success"):
            print(f"✅ Found {files_result.get('total_files', 0)} data files")
            companies = files_result.get("companies", {})
            for company, timestamps in companies.items():
                print(f"   📊 Company: {company}")
                for timestamp, file_types in timestamps.items():
                    print(f"      🕐 {timestamp}: {list(file_types.keys())}")
        else:
            print(f"❌ Failed to get data files: {files_result.get('error')}")
            return False
        
        # Test graph initialization with Test Company data
        print("\n🚀 Step 3: Testing graph initialization with Test Company data...")
        init_result = orchestrator.initialize_graph_with_data("Test Company")
        
        if init_result.get("success"):
            summary = init_result.get("summary", {})
            print("✅ Graph initialization successful!")
            print(f"   📊 Nodes created: {summary.get('nodes_created', 0)}")
            print(f"   🔗 Relationships created: {summary.get('relationships_created', 0)}")
            print(f"   ➕ Additional relationships: {summary.get('additional_relationships', 0)}")
            print(f"   📁 Files loaded: {len(summary.get('files_loaded', []))}")
            print(f"   ⏱️ Duration: {summary.get('duration_seconds', 0):.2f} seconds")
            
            # Check final graph statistics
            print("\n📈 Step 4: Checking final graph statistics...")
            stats_result = orchestrator.get_graph_statistics()
            if stats_result.get("success"):
                print(f"✅ Final graph state:")
                print(f"   📊 Total nodes: {stats_result.get('node_count', 0)}")
                print(f"   🔗 Total relationships: {stats_result.get('relationship_count', 0)}")
            else:
                print(f"⚠️ Could not get final statistics: {stats_result.get('error')}")
            
            return True
        else:
            print(f"❌ Graph initialization failed: {init_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_data_loading_without_company():
    """Test loading data without specifying a company (should load latest)."""
    print("\n🧪 Testing Data Loading Without Company Filter")
    print("=" * 50)
    
    try:
        orchestrator = DataLoadingOrchestrator()
        
        print("🚀 Loading latest data files...")
        init_result = orchestrator.initialize_graph_with_data()
        
        if init_result.get("success"):
            summary = init_result.get("summary", {})
            print("✅ Latest data loading successful!")
            print(f"   📊 Nodes created: {summary.get('nodes_created', 0)}")
            print(f"   🔗 Relationships created: {summary.get('relationships_created', 0)}")
            return True
        else:
            print(f"❌ Latest data loading failed: {init_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Load specific company data
    success1 = test_data_loading()
    
    # Test 2: Load latest data
    success2 = test_data_loading_without_company()
    
    print(f"\n📋 Test Results:")
    print(f"   Test 1 (Specific Company): {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"   Test 2 (Latest Data): {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Data loading workflow is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
