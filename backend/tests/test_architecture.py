#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly without database connection.
This script validates the Agent Tool Architecture implementation.
"""

import os
import sys

# Add the parent directory (backend) to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all the imports to make sure they work."""
    print("Testing imports...")
    
    try:
        # Test tools imports
        print("1. Testing tools imports...")
        from tools import get_tools_for_role, ALL_TOOLS
        print(f"   ✅ Tools imported successfully. Found {len(ALL_TOOLS)} tools.")
        
        # Test config imports
        print("2. Testing config imports...")
        from config import get_agent_config, get_database_config
        print("   ✅ Config imported successfully.")
        
        # Test models imports
        print("3. Testing models imports...")
        from models import Person, Process, Department, validate_entity_data
        print("   ✅ Models imported successfully.")
        
        # Test agents imports
        print("4. Testing agents imports...")
        from agents.llm_agents.base_agent import BaseAgent
        from agents.llm_agents.graph_agent import GraphAgent
        from agents.llm_agents.extractor_agent import ExtractorAgent
        from agents.llm_agents.analyzer_agent import AnalyzerAgent
        from agents.llm_agents.admin_agent import AdminAgent
        from agents.llm_agents.agent_orchestrator import AgentOrchestrator
        print("   ✅ Agents imported successfully.")
        
        # Test tool categories
        print("5. Testing tool categories...")
        from tools import get_tools_by_category
        crud_tools = get_tools_by_category("crud")
        analysis_tools = get_tools_by_category("analysis")
        admin_tools = get_tools_by_category("admin")
        search_tools = get_tools_by_category("search")
        print(f"   ✅ CRUD tools: {len(crud_tools)}")
        print(f"   ✅ Analysis tools: {len(analysis_tools)}")
        print(f"   ✅ Admin tools: {len(admin_tools)}")
        print(f"   ✅ Search tools: {len(search_tools)}")
        
        # Test role permissions
        print("6. Testing role permissions...")
        from config import ROLE_PERMISSIONS
        print(f"   ✅ Available roles: {list(ROLE_PERMISSIONS.keys())}")
        for role, tools in ROLE_PERMISSIONS.items():
            print(f"      {role}: {len(tools)} tools")
        
        # Test agent configurations
        print("7. Testing agent configurations...")
        graph_config = get_agent_config("graph_agent")
        extractor_config = get_agent_config("extractor_agent")
        analyzer_config = get_agent_config("analyzer_agent")
        admin_config = get_agent_config("admin_agent")
        print(f"   ✅ Graph agent: {graph_config.name} ({graph_config.role})")
        print(f"   ✅ Extractor agent: {extractor_config.name} ({extractor_config.role})")
        print(f"   ✅ Analyzer agent: {analyzer_config.name} ({analyzer_config.role})")
        print(f"   ✅ Admin agent: {admin_config.name} ({admin_config.role})")
        
        # Test model validation
        print("8. Testing model validation...")
        person_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "role": "Engineer",
            "department": "Engineering"
        }
        validation_result = validate_entity_data("Person", person_data)
        print(f"   ✅ Person validation: {validation_result['valid']}")
        
        print("\n🎉 All tests passed! The Agent Tool Architecture imports are working correctly.")
        print("\n📊 Summary:")
        print(f"   - Total tools: {len(ALL_TOOLS)}")
        print(f"   - Available roles: {len(ROLE_PERMISSIONS)}")
        print(f"   - Agent types: 4 (graph, extractor, analyzer, admin)")
        print(f"   - Tool categories: 4 (crud, analysis, admin, search)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
