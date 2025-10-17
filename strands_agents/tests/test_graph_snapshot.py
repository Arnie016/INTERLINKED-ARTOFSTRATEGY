"""
Unit Tests for Graph Snapshot Tool

Tests for get_graph_snapshot tool with mock Neo4j interactions.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

# Import tools to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.graph_analysis import get_graph_snapshot
from src.utils.errors import ValidationError, GraphQueryError, ToolExecutionError


class TestGetGraphSnapshot:
    """Test suite for get_graph_snapshot tool."""
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_basic(self, mock_create_session):
        """Test basic graph snapshot functionality."""
        mock_session = MagicMock()
        
        # Mock center node query result
        center_result = MagicMock()
        center_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Alice Johnson"}
        }
        center_result.single.return_value = center_record
        
        # Mock subgraph query result
        subgraph_result = MagicMock()
        subgraph_record = {
            "all_nodes": [
                {"id": 1, "labels": ["Person"], "properties": {"name": "Alice Johnson"}},
                {"id": 2, "labels": ["Organization"], "properties": {"name": "Acme Corp"}}
            ],
            "all_relationships": [
                {
                    "id": 10,
                    "type": "WORKS_AT",
                    "properties": {},
                    "start_id": 1,
                    "end_id": 2
                }
            ]
        }
        subgraph_result.single.return_value = subgraph_record
        
        # Configure mock to return different results for each query
        mock_session.run.side_effect = [center_result, subgraph_result]
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = get_graph_snapshot("1", max_nodes=50)
        
        # Assertions
        assert result["center_node"]["id"] == "1"
        assert result["metadata"]["node_count"] == 2
        assert result["metadata"]["relationship_count"] == 1
        assert len(result["nodes"]) == 2
        assert len(result["relationships"]) == 1
        assert "visualization_hints" in result
        assert result["visualization_hints"]["center_node_id"] == "1"
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_with_filters(self, mock_create_session):
        """Test graph snapshot with node and relationship type filters."""
        mock_session = MagicMock()
        
        center_result = MagicMock()
        center_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Alice"}
        }
        center_result.single.return_value = center_record
        
        subgraph_result = MagicMock()
        subgraph_record = {
            "all_nodes": [
                {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                {"id": 2, "labels": ["Person"], "properties": {"name": "Bob"}}
            ],
            "all_relationships": [
                {"id": 10, "type": "MANAGES", "properties": {}, "start_id": 1, "end_id": 2}
            ]
        }
        subgraph_result.single.return_value = subgraph_record
        
        mock_session.run.side_effect = [center_result, subgraph_result]
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute with filters
        result = get_graph_snapshot(
            "1",
            max_nodes=50,
            node_types=["Person"],
            relationship_types=["MANAGES"]
        )
        
        # Verify query was built with filters
        call_args = mock_session.run.call_args_list
        # Second call should be the subgraph query with filters
        subgraph_query = call_args[1][0][0]
        assert "MANAGES" in subgraph_query
        assert "n:Person" in subgraph_query
        
        assert result["metadata"]["node_count"] == 2
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_isolated_node(self, mock_create_session):
        """Test snapshot of an isolated node with no relationships."""
        mock_session = MagicMock()
        
        center_result = MagicMock()
        center_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Isolated"}
        }
        center_result.single.return_value = center_record
        
        # Subgraph query returns None/empty (no neighbors)
        subgraph_result = MagicMock()
        subgraph_result.single.return_value = {"all_nodes": None, "all_relationships": []}
        
        mock_session.run.side_effect = [center_result, subgraph_result]
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = get_graph_snapshot("1", max_nodes=50)
        
        # Should still return center node
        assert result["center_node"]["id"] == "1"
        assert result["metadata"]["node_count"] == 1
        assert result["metadata"]["relationship_count"] == 0
        assert len(result["nodes"]) == 1
        assert len(result["relationships"]) == 0
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_custom_depth(self, mock_create_session):
        """Test snapshot with custom depth parameter."""
        mock_session = MagicMock()
        
        center_result = MagicMock()
        center_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Center"}
        }
        center_result.single.return_value = center_record
        
        # Mock a deeper graph
        subgraph_result = MagicMock()
        subgraph_record = {
            "all_nodes": [
                {"id": i, "labels": ["Person"], "properties": {"name": f"Node{i}"}}
                for i in range(1, 6)
            ],
            "all_relationships": [
                {"id": i+10, "type": "MANAGES", "properties": {}, "start_id": i, "end_id": i+1}
                for i in range(1, 5)
            ]
        }
        subgraph_result.single.return_value = subgraph_record
        
        mock_session.run.side_effect = [center_result, subgraph_result]
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute with custom depth
        result = get_graph_snapshot("1", max_nodes=50, depth=3)
        
        # Verify query used depth parameter
        call_args = mock_session.run.call_args_list
        subgraph_query = call_args[1][0][0]
        assert "*1..3" in subgraph_query
        
        assert result["metadata"]["node_count"] == 5
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_large_graph_hints(self, mock_create_session):
        """Test visualization hints for different graph sizes."""
        mock_session = MagicMock()
        
        center_result = MagicMock()
        center_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Center"}
        }
        center_result.single.return_value = center_record
        
        # Mock a large graph (>50 nodes)
        subgraph_result = MagicMock()
        subgraph_record = {
            "all_nodes": [
                {"id": i, "labels": ["Person"], "properties": {"name": f"Node{i}"}}
                for i in range(1, 61)
            ],
            "all_relationships": [
                {"id": i+100, "type": "RELATES_TO", "properties": {}, "start_id": 1, "end_id": i}
                for i in range(2, 61)
            ]
        }
        subgraph_result.single.return_value = subgraph_record
        
        mock_session.run.side_effect = [center_result, subgraph_result]
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = get_graph_snapshot("1", max_nodes=100)
        
        # Check visualization hints for large graph
        assert result["metadata"]["node_count"] == 60
        assert result["visualization_hints"]["layout_type"] == "circular"
        assert result["visualization_hints"]["suggested_zoom"] == "fit"
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_small_graph_hints(self, mock_create_session):
        """Test visualization hints for small graphs."""
        mock_session = MagicMock()
        
        center_result = MagicMock()
        center_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Center"}
        }
        center_result.single.return_value = center_record
        
        # Mock a small graph (<10 nodes)
        subgraph_result = MagicMock()
        subgraph_record = {
            "all_nodes": [
                {"id": i, "labels": ["Person"], "properties": {"name": f"Node{i}"}}
                for i in range(1, 6)
            ],
            "all_relationships": [
                {"id": i+10, "type": "RELATES_TO", "properties": {}, "start_id": 1, "end_id": i}
                for i in range(2, 6)
            ]
        }
        subgraph_result.single.return_value = subgraph_record
        
        mock_session.run.side_effect = [center_result, subgraph_result]
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = get_graph_snapshot("1", max_nodes=50)
        
        # Check visualization hints for small graph
        assert result["metadata"]["node_count"] == 5
        assert result["visualization_hints"]["layout_type"] == "force"
        assert result["visualization_hints"]["suggested_zoom"] == "default"
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_truncation(self, mock_create_session):
        """Test that truncation flag is set when max_nodes is reached."""
        mock_session = MagicMock()
        
        center_result = MagicMock()
        center_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Center"}
        }
        center_result.single.return_value = center_record
        
        # Return exactly max_nodes
        subgraph_result = MagicMock()
        subgraph_record = {
            "all_nodes": [
                {"id": i, "labels": ["Person"], "properties": {"name": f"Node{i}"}}
                for i in range(1, 51)  # 50 nodes
            ],
            "all_relationships": []
        }
        subgraph_result.single.return_value = subgraph_record
        
        mock_session.run.side_effect = [center_result, subgraph_result]
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute with max_nodes=50
        result = get_graph_snapshot("1", max_nodes=50)
        
        # Truncation should be true
        assert result["metadata"]["truncated"] is True
    
    def test_get_graph_snapshot_invalid_center_node_id(self):
        """Test with invalid center node ID."""
        with pytest.raises(ToolExecutionError) as exc_info:
            get_graph_snapshot("", max_nodes=50)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_get_graph_snapshot_invalid_max_nodes_too_high(self):
        """Test with max_nodes exceeding maximum."""
        with pytest.raises(ToolExecutionError) as exc_info:
            get_graph_snapshot("1", max_nodes=300)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_get_graph_snapshot_invalid_depth_too_low(self):
        """Test with depth below minimum."""
        with pytest.raises(ToolExecutionError) as exc_info:
            get_graph_snapshot("1", max_nodes=50, depth=0)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_get_graph_snapshot_invalid_depth_too_high(self):
        """Test with depth above maximum."""
        with pytest.raises(ToolExecutionError) as exc_info:
            get_graph_snapshot("1", max_nodes=50, depth=5)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_get_graph_snapshot_invalid_node_type(self):
        """Test with invalid node type filter."""
        with pytest.raises(ToolExecutionError) as exc_info:
            get_graph_snapshot("1", max_nodes=50, node_types=["InvalidType"])
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_get_graph_snapshot_invalid_relationship_type(self):
        """Test with invalid relationship type filter."""
        with pytest.raises(ToolExecutionError) as exc_info:
            get_graph_snapshot("1", max_nodes=50, relationship_types=["INVALID_REL"])
        
        assert "Invalid parameters" in str(exc_info.value)
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_center_node_not_found(self, mock_create_session):
        """Test when center node doesn't exist."""
        mock_session = MagicMock()
        
        # Center node query returns None
        center_result = MagicMock()
        center_result.single.return_value = None
        
        mock_session.run.return_value = center_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Should raise GraphQueryError wrapped in ToolExecutionError
        with pytest.raises(ToolExecutionError) as exc_info:
            get_graph_snapshot("999", max_nodes=50)
        
        assert "Graph snapshot operation failed" in str(exc_info.value)
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_neo4j_error(self, mock_create_session):
        """Test handling of Neo4j errors."""
        mock_session = MagicMock()
        from neo4j.exceptions import ServiceUnavailable
        mock_session.run.side_effect = ServiceUnavailable("Connection failed")
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Neo4j error gets wrapped in ToolExecutionError
        with pytest.raises(ToolExecutionError) as exc_info:
            get_graph_snapshot("1", max_nodes=50)
        
        assert "Graph snapshot operation failed" in str(exc_info.value)
    
    @patch('src.tools.graph_analysis.create_session')
    def test_get_graph_snapshot_relationship_properties(self, mock_create_session):
        """Test that relationship properties are properly included."""
        mock_session = MagicMock()
        
        center_result = MagicMock()
        center_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Alice"}
        }
        center_result.single.return_value = center_record
        
        subgraph_result = MagicMock()
        subgraph_record = {
            "all_nodes": [
                {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                {"id": 2, "labels": ["Person"], "properties": {"name": "Bob"}}
            ],
            "all_relationships": [
                {
                    "id": 10,
                    "type": "MANAGES",
                    "properties": {"since": "2020-01-01", "level": "senior"},
                    "start_id": 1,
                    "end_id": 2
                }
            ]
        }
        subgraph_result.single.return_value = subgraph_record
        
        mock_session.run.side_effect = [center_result, subgraph_result]
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = get_graph_snapshot("1", max_nodes=50)
        
        # Check relationship properties are included
        assert len(result["relationships"]) == 1
        rel = result["relationships"][0]
        assert rel["type"] == "MANAGES"
        assert "since" in rel["properties"]
        assert rel["properties"]["since"] == "2020-01-01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

