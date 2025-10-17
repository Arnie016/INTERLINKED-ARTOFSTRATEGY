"""
Unit Tests for Path Analysis Tools

Tests for explain_path tool with mock Neo4j interactions.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

# Import tools to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.graph_analysis import explain_path
from src.utils.errors import ValidationError, GraphQueryError, ToolExecutionError


class TestExplainPath:
    """Test suite for explain_path tool."""
    
    @patch('src.tools.graph_analysis.create_session')
    def test_explain_path_single_path(self, mock_create_session):
        """Test finding a single path between two nodes."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Mock a simple path: Person -> WORKS_AT -> Organization
        mock_record = {
            "nodes": [
                {
                    "id": 1,
                    "labels": ["Person"],
                    "properties": {"name": "Alice Johnson"}
                },
                {
                    "id": 2,
                    "labels": ["Organization"],
                    "properties": {"name": "Engineering Dept"}
                }
            ],
            "relationships": [
                {
                    "type": "WORKS_AT",
                    "properties": {},
                    "start_id": 1,
                    "end_id": 2
                }
            ],
            "path_length": 1
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = explain_path("1", "2", max_paths=3)
        
        # Assertions
        assert result["paths_found"] == 1
        assert result["shortest_path_length"] == 1
        assert len(result["paths"]) == 1
        assert result["paths"][0]["length"] == 1
        assert "Alice Johnson" in result["paths"][0]["description"]
        assert "WORKS_AT" in result["paths"][0]["description"]
        assert "Found 1 path connecting" in result["explanation"]
    
    @patch('src.tools.graph_analysis.create_session')
    def test_explain_path_multiple_paths(self, mock_create_session):
        """Test finding multiple paths between two nodes."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Mock two different paths
        mock_records = [
            {
                "nodes": [
                    {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                    {"id": 2, "labels": ["Project"], "properties": {"name": "ProjectX"}},
                    {"id": 3, "labels": ["Person"], "properties": {"name": "Bob"}}
                ],
                "relationships": [
                    {"type": "PARTICIPATES_IN", "properties": {}, "start_id": 1, "end_id": 2},
                    {"type": "PARTICIPATES_IN", "properties": {}, "start_id": 3, "end_id": 2}
                ],
                "path_length": 2
            },
            {
                "nodes": [
                    {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                    {"id": 4, "labels": ["Organization"], "properties": {"name": "Eng"}},
                    {"id": 3, "labels": ["Person"], "properties": {"name": "Bob"}}
                ],
                "relationships": [
                    {"type": "WORKS_AT", "properties": {}, "start_id": 1, "end_id": 4},
                    {"type": "WORKS_AT", "properties": {}, "start_id": 3, "end_id": 4}
                ],
                "path_length": 2
            }
        ]
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = explain_path("1", "3", max_paths=5)
        
        # Assertions
        assert result["paths_found"] == 2
        assert result["shortest_path_length"] == 2
        assert len(result["paths"]) == 2
        assert "Found 2 path(s) connecting" in result["explanation"]
        assert "Multiple routes exist" in result["explanation"]
    
    @patch('src.tools.graph_analysis.create_session')
    def test_explain_path_no_paths_found(self, mock_create_session):
        """Test when no paths exist between nodes."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Empty result - no paths found
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = explain_path("1", "999", max_paths=3)
        
        # Assertions
        assert result["paths_found"] == 0
        assert result["shortest_path_length"] is None
        assert len(result["paths"]) == 0
        assert "No paths found" in result["explanation"]
        assert "disconnected" in result["explanation"]
    
    @patch('src.tools.graph_analysis.create_session')
    def test_explain_path_with_max_depth(self, mock_create_session):
        """Test path finding with custom max depth."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Mock a 3-hop path
        mock_record = {
            "nodes": [
                {"id": 1, "labels": ["Person"], "properties": {"name": "A"}},
                {"id": 2, "labels": ["Project"], "properties": {"name": "B"}},
                {"id": 3, "labels": ["Technology"], "properties": {"name": "C"}},
                {"id": 4, "labels": ["Person"], "properties": {"name": "D"}}
            ],
            "relationships": [
                {"type": "PARTICIPATES_IN", "properties": {}, "start_id": 1, "end_id": 2},
                {"type": "USES", "properties": {}, "start_id": 2, "end_id": 3},
                {"type": "USES", "properties": {}, "start_id": 4, "end_id": 3}
            ],
            "path_length": 3
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute with custom max_depth
        result = explain_path("1", "4", max_paths=3, max_depth=5)
        
        # Verify query was called with correct max_depth parameter
        call_args = mock_session.run.call_args
        if len(call_args[0]) > 1:
            assert call_args[0][1]["max_depth"] == 5
        
        assert result["paths_found"] == 1
        assert result["shortest_path_length"] == 3
    
    def test_explain_path_invalid_start_node_id(self):
        """Test with invalid start node ID."""
        with pytest.raises(ToolExecutionError) as exc_info:
            explain_path("", "2", max_paths=3)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_explain_path_invalid_end_node_id(self):
        """Test with invalid end node ID."""
        with pytest.raises(ToolExecutionError) as exc_info:
            explain_path("1", "", max_paths=3)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_explain_path_same_node_ids(self):
        """Test with same start and end node IDs."""
        with pytest.raises(ToolExecutionError) as exc_info:
            explain_path("1", "1", max_paths=3)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_explain_path_invalid_max_paths_too_low(self):
        """Test with max_paths below minimum."""
        with pytest.raises(ToolExecutionError) as exc_info:
            explain_path("1", "2", max_paths=0)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_explain_path_invalid_max_paths_too_high(self):
        """Test with max_paths above maximum."""
        with pytest.raises(ToolExecutionError) as exc_info:
            explain_path("1", "2", max_paths=11)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_explain_path_invalid_max_depth_too_low(self):
        """Test with max_depth below minimum."""
        with pytest.raises(ToolExecutionError) as exc_info:
            explain_path("1", "2", max_paths=3, max_depth=0)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_explain_path_invalid_max_depth_too_high(self):
        """Test with max_depth above maximum."""
        with pytest.raises(ToolExecutionError) as exc_info:
            explain_path("1", "2", max_paths=3, max_depth=20)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    @patch('src.tools.graph_analysis.create_session')
    def test_explain_path_long_path(self, mock_create_session):
        """Test finding a longer path with multiple hops."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Mock a 5-hop path
        mock_record = {
            "nodes": [
                {"id": i, "labels": ["Person"], "properties": {"name": f"Node{i}"}}
                for i in range(1, 7)
            ],
            "relationships": [
                {"type": "MANAGES", "properties": {}, "start_id": i, "end_id": i+1}
                for i in range(1, 6)
            ],
            "path_length": 5
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = explain_path("1", "6", max_paths=1)
        
        # Assertions
        assert result["paths_found"] == 1
        assert result["shortest_path_length"] == 5
        assert len(result["paths"][0]["nodes"]) == 6
        assert len(result["paths"][0]["relationships"]) == 5
    
    @patch('src.tools.graph_analysis.create_session')
    def test_explain_path_nodes_with_no_name_property(self, mock_create_session):
        """Test path with nodes that don't have a name property."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Mock nodes without 'name' property
        mock_record = {
            "nodes": [
                {"id": 1, "labels": ["Person"], "properties": {"email": "alice@example.com"}},
                {"id": 2, "labels": ["Project"], "properties": {"id": "proj-123"}}
            ],
            "relationships": [
                {"type": "PARTICIPATES_IN", "properties": {}, "start_id": 1, "end_id": 2}
            ],
            "path_length": 1
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = explain_path("1", "2", max_paths=1)
        
        # Assertions - should use node ID when name is missing
        assert result["paths_found"] == 1
        assert "Node 1" in result["paths"][0]["description"]
        assert "Node 2" in result["paths"][0]["description"]
    
    @patch('src.tools.graph_analysis.create_session')
    def test_explain_path_neo4j_error(self, mock_create_session):
        """Test handling of Neo4j errors."""
        mock_session = MagicMock()
        from neo4j.exceptions import ServiceUnavailable
        mock_session.run.side_effect = ServiceUnavailable("Connection failed")
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Neo4j error gets wrapped in ToolExecutionError
        with pytest.raises(ToolExecutionError) as exc_info:
            explain_path("1", "2", max_paths=3)
        
        assert "Path finding operation failed" in str(exc_info.value)
    
    @patch('src.tools.graph_analysis.create_session')
    def test_explain_path_description_formatting(self, mock_create_session):
        """Test that path descriptions are properly formatted."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Mock a clear path for description testing
        mock_record = {
            "nodes": [
                {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                {"id": 2, "labels": ["Organization"], "properties": {"name": "Acme Corp"}},
                {"id": 3, "labels": ["Project"], "properties": {"name": "Project X"}}
            ],
            "relationships": [
                {"type": "WORKS_AT", "properties": {}, "start_id": 1, "end_id": 2},
                {"type": "OWNS", "properties": {}, "start_id": 2, "end_id": 3}
            ],
            "path_length": 2
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute
        result = explain_path("1", "3", max_paths=1)
        
        # Check description formatting
        description = result["paths"][0]["description"]
        assert "Person: Alice" in description
        assert "WORKS_AT" in description
        assert "Organization: Acme Corp" in description
        assert "OWNS" in description
        assert "Project: Project X" in description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

