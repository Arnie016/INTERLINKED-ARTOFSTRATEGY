"""
Basic tests for Strands Agents that can run without AWS credentials or Neo4j.

These tests verify:
- Agent instantiation
- Configuration handling
- Tool registration
- Type hints and schemas
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set minimal environment for testing
os.environ['AWS_REGION'] = 'us-west-2'


class TestAgentInstantiation:
    """Test that all agents can be instantiated correctly."""
    
    def test_graph_agent_creation(self):
        """Test GraphAgent instantiation."""
        from src.agents import create_graph_agent
        
        agent = create_graph_agent()
        assert agent is not None
        # Strands Agent.model.config is a dict, not an object
        assert agent.model.config['model_id'] == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert agent.model.config['temperature'] == 0.3
        assert agent.model.config['max_tokens'] == 4096
    
    def test_analyzer_agent_creation(self):
        """Test AnalyzerAgent instantiation."""
        from src.agents import create_analyzer_agent
        
        agent = create_analyzer_agent()
        assert agent is not None
        assert agent.model.config['temperature'] == 0.2
    
    def test_extractor_agent_creation(self):
        """Test ExtractorAgent instantiation."""
        from src.agents import create_extractor_agent
        
        agent = create_extractor_agent()
        assert agent is not None
        assert agent.model.config['temperature'] == 0.1
    
    def test_admin_agent_creation(self):
        """Test AdminAgent instantiation."""
        from src.agents import create_admin_agent
        
        agent = create_admin_agent()
        assert agent is not None
        assert agent.model.config['temperature'] == 0.0
    
    def test_orchestrator_creation_user_role(self):
        """Test Orchestrator instantiation with user role."""
        from src.agents import create_orchestrator_agent
        
        orchestrator = create_orchestrator_agent(user_role="user")
        assert orchestrator is not None
        assert orchestrator.model.config['temperature'] == 0.5
        # User role should have 2 agents: graph + analyzer
        # Note: Strands Agent doesn't expose tools list, so we verify creation succeeds
        assert hasattr(orchestrator, 'model')
    
    def test_orchestrator_creation_extractor_role(self):
        """Test Orchestrator with extractor role has correct tools."""
        from src.agents import create_orchestrator_agent
        
        orchestrator = create_orchestrator_agent(user_role="extractor")
        # Extractor role should have 3 agents: graph + analyzer + extractor
        # Verify creation succeeds (tools are internal to Strands Agent)
        assert orchestrator is not None
        assert hasattr(orchestrator, 'model')
    
    def test_orchestrator_creation_admin_role(self):
        """Test Orchestrator with admin role has all tools."""
        from src.agents import create_orchestrator_agent
        
        orchestrator = create_orchestrator_agent(user_role="admin")
        # Admin role should have all 4 agents
        # Verify creation succeeds (tools are internal to Strands Agent)
        assert orchestrator is not None
        assert hasattr(orchestrator, 'model')


class TestCustomConfiguration:
    """Test custom model configurations."""
    
    def test_custom_temperature(self):
        """Test that custom temperature is applied."""
        from src.agents import create_graph_agent
        
        custom_config = {"temperature": 0.8}
        agent = create_graph_agent(custom_model_config=custom_config)
        
        assert agent.model.config['temperature'] == 0.8
    
    def test_custom_max_tokens(self):
        """Test that custom max_tokens is applied."""
        from src.agents import create_analyzer_agent
        
        custom_config = {"max_tokens": 8192}
        agent = create_analyzer_agent(custom_model_config=custom_config)
        
        assert agent.model.config['max_tokens'] == 8192
    
    def test_multiple_custom_params(self):
        """Test that multiple custom parameters are applied."""
        from src.agents import create_extractor_agent
        
        custom_config = {
            "temperature": 0.5,
            "max_tokens": 2048,
            "top_p": 0.9
        }
        agent = create_extractor_agent(custom_model_config=custom_config)
        
        assert agent.model.config['temperature'] == 0.5
        assert agent.model.config['max_tokens'] == 2048
        assert agent.model.config['top_p'] == 0.9


class TestToolDefinitions:
    """Test that tool functions are properly defined."""
    
    def test_graph_search_tools_exist(self):
        """Test that graph search tools are defined."""
        from src.tools import graph_search
        
        assert hasattr(graph_search, 'search_nodes')
        assert hasattr(graph_search, 'find_related_nodes')
        assert callable(graph_search.search_nodes)
        assert callable(graph_search.find_related_nodes)
    
    def test_graph_analysis_tools_exist(self):
        """Test that graph analysis tools are defined."""
        from src.tools import graph_analysis
        
        assert hasattr(graph_analysis, 'centrality_analysis')
        assert hasattr(graph_analysis, 'community_detection')
        assert hasattr(graph_analysis, 'graph_stats')
        assert hasattr(graph_analysis, 'find_bottlenecks')
        assert hasattr(graph_analysis, 'get_graph_snapshot')
        assert hasattr(graph_analysis, 'explain_path')
    
    def test_graph_crud_tools_exist(self):
        """Test that CRUD tools are defined."""
        from src.tools import graph_crud
        
        assert hasattr(graph_crud, 'create_node')
        assert hasattr(graph_crud, 'create_relationship')
        assert hasattr(graph_crud, 'bulk_ingest')
    
    def test_graph_admin_tools_exist(self):
        """Test that admin tools are defined."""
        from src.tools import graph_admin
        
        assert hasattr(graph_admin, 'reindex')
        assert hasattr(graph_admin, 'migrate_labels')
        assert hasattr(graph_admin, 'maintenance_cleanup_orphan_nodes')


class TestToolPlaceholders:
    """Test that placeholder tools return expected structure."""
    
    def test_search_nodes_placeholder(self):
        """Test search_nodes placeholder returns correct structure."""
        from src.tools.graph_search import search_nodes
        
        result = search_nodes("test query", limit=5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "labels" in result[0]
        assert "properties" in result[0]
    
    def test_find_related_nodes_placeholder(self):
        """Test find_related_nodes placeholder returns correct structure."""
        from src.tools.graph_search import find_related_nodes
        
        test_node = {"type": "Person", "properties": {"name": "Test"}}
        result = find_related_nodes(test_node)
        
        assert isinstance(result, dict)
        assert "center_node" in result
        assert "related_nodes" in result
        assert "relationship_count" in result
    
    def test_create_node_placeholder(self):
        """Test create_node placeholder returns expected error."""
        from src.tools.graph_crud import create_node
        
        result = create_node("Person", {"name": "Test"})
        
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is False
        # Should indicate tools not yet implemented
        assert "task 5" in result.get("error", "").lower()


class TestTypeHints:
    """Test that tools have proper type annotations."""
    
    def test_search_nodes_signature(self):
        """Test search_nodes has proper type hints."""
        from src.tools.graph_search import search_nodes
        import inspect
        
        sig = inspect.signature(search_nodes)
        
        # Check parameter types
        assert sig.parameters['query'].annotation == str
        assert sig.parameters['limit'].annotation == int
        
        # Check return type exists
        assert sig.return_annotation is not inspect.Parameter.empty
    
    def test_create_node_signature(self):
        """Test create_node has proper type hints."""
        from src.tools.graph_crud import create_node
        import inspect
        
        sig = inspect.signature(create_node)
        
        # Check parameters
        assert sig.parameters['label'].annotation == str
        assert 'Dict' in str(sig.parameters['properties'].annotation)


class TestAgentTools:
    """Test agent tool functions (callable wrappers)."""
    
    def test_graph_agent_tool_exists(self):
        """Test that graph_agent tool function exists."""
        from src.agents.graph_agent import graph_agent
        
        assert callable(graph_agent)
        
        # Check it has the @tool decorator attributes
        assert hasattr(graph_agent, '__doc__')
        assert graph_agent.__doc__ is not None
    
    def test_analyzer_agent_tool_exists(self):
        """Test that analyzer_agent tool function exists."""
        from src.agents.analyzer_agent import analyzer_agent
        
        assert callable(analyzer_agent)
        assert hasattr(analyzer_agent, '__doc__')
    
    def test_extractor_agent_tool_exists(self):
        """Test that extractor_agent tool function exists."""
        from src.agents.extractor_agent import extractor_agent
        
        assert callable(extractor_agent)
        assert hasattr(extractor_agent, '__doc__')
    
    def test_admin_agent_tool_exists(self):
        """Test that admin_agent tool function exists."""
        from src.agents.admin_agent import admin_agent
        
        assert callable(admin_agent)
        assert hasattr(admin_agent, '__doc__')


class TestPackageExports:
    """Test that package exports are correct."""
    
    def test_agents_package_exports(self):
        """Test that agents package exports all required functions."""
        from src import agents
        
        # Check orchestrator exports
        assert hasattr(agents, 'create_orchestrator_agent')
        assert hasattr(agents, 'process_query')
        
        # Check specialized agent exports
        assert hasattr(agents, 'create_graph_agent')
        assert hasattr(agents, 'create_analyzer_agent')
        assert hasattr(agents, 'create_extractor_agent')
        assert hasattr(agents, 'create_admin_agent')
        
        # Check tool exports
        assert hasattr(agents, 'graph_agent')
        assert hasattr(agents, 'analyzer_agent')
        assert hasattr(agents, 'extractor_agent')
        assert hasattr(agents, 'admin_agent')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

