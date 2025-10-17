"""
Unit Tests for Graph Search Tools

Tests for search_nodes and find_related_nodes tools with mock Neo4j interactions.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from typing import List, Dict, Any

# Import tools to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.graph_search import search_nodes, find_related_nodes
from src.utils.errors import ValidationError, GraphQueryError, ToolExecutionError


class TestSearchNodes:
    """Test suite for search_nodes tool."""
    
    @patch('src.tools.graph_search.create_session')
    def test_search_nodes_basic(self, mock_create_session):
        """Test basic node search functionality."""
        # Mock Neo4j session and result
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Mock return values
        mock_record = {
            "node_id": 1,
            "labels": ["Person"],
            "properties": {"name": "Alice Johnson", "role": "Engineer"}
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute search
        results = search_nodes("Alice", limit=10)
        
        # Assertions
        assert len(results) == 1
        assert results[0]["id"] == "1"
        assert results[0]["labels"] == ["Person"]
        assert results[0]["properties"]["name"] == "Alice Johnson"
        
        # Verify session was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "MATCH (n)" in call_args[0][0]
        # Check that parameters were passed (second positional arg or named arg)
        if len(call_args[0]) > 1:
            assert call_args[0][1]["query"] == "alice"
        else:
            assert call_args.kwargs["query"] == "alice"
    
    @patch('src.tools.graph_search.create_session')
    def test_search_nodes_with_node_types(self, mock_create_session):
        """Test node search with node type filtering."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        mock_record = {
            "node_id": 2,
            "labels": ["Organization"],
            "properties": {"name": "Engineering Dept"}
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute search with node type filter
        results = search_nodes("engineering", node_types=["Organization"], limit=10)
        
        # Assertions
        assert len(results) == 1
        assert "Organization" in results[0]["labels"]
        
        # Verify query includes label filter
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "n:Organization" in query
    
    @patch('src.tools.graph_search.create_session')
    def test_search_nodes_empty_results(self, mock_create_session):
        """Test node search with no results."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute search
        results = search_nodes("nonexistent", limit=10)
        
        # Assertions
        assert len(results) == 0
    
    @patch('src.tools.graph_search.create_session')
    def test_search_nodes_limit_enforcement(self, mock_create_session):
        """Test that limit parameter is properly enforced."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Create 5 mock records
        mock_records = [
            {"node_id": i, "labels": ["Person"], "properties": {"name": f"Person {i}"}}
            for i in range(5)
        ]
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute search with limit
        results = search_nodes("Person", limit=5)
        
        # Verify limit was passed to query
        call_args = mock_session.run.call_args
        # Check that parameters were passed (second positional arg or named arg)
        if len(call_args[0]) > 1:
            assert call_args[0][1]["limit"] == 5
        else:
            assert "limit" in call_args.kwargs or len(call_args[0]) > 1
    
    def test_search_nodes_invalid_query_empty(self):
        """Test search with empty query string."""
        with pytest.raises(ToolExecutionError) as exc_info:
            search_nodes("", limit=10)
        
        assert "Invalid search parameters" in str(exc_info.value)
    
    def test_search_nodes_invalid_query_too_long(self):
        """Test search with overly long query string."""
        long_query = "x" * 501  # Exceeds max length of 500
        
        with pytest.raises(ToolExecutionError) as exc_info:
            search_nodes(long_query, limit=10)
        
        assert "Invalid search parameters" in str(exc_info.value)
    
    def test_search_nodes_invalid_node_type(self):
        """Test search with invalid node type."""
        with pytest.raises(ToolExecutionError) as exc_info:
            search_nodes("test", node_types=["InvalidType"], limit=10)
        
        assert "Invalid search parameters" in str(exc_info.value)
    
    def test_search_nodes_invalid_limit_too_high(self):
        """Test search with limit exceeding maximum."""
        with pytest.raises(ToolExecutionError) as exc_info:
            search_nodes("test", limit=100)
        
        assert "Invalid search parameters" in str(exc_info.value)
    
    def test_search_nodes_invalid_limit_negative(self):
        """Test search with negative limit."""
        with pytest.raises(ToolExecutionError) as exc_info:
            search_nodes("test", limit=-1)
        
        assert "Invalid search parameters" in str(exc_info.value)
    
    @patch('src.tools.graph_search.create_session')
    def test_search_nodes_neo4j_error(self, mock_create_session):
        """Test handling of Neo4j errors."""
        mock_session = MagicMock()
        from neo4j.exceptions import ServiceUnavailable
        mock_session.run.side_effect = ServiceUnavailable("Connection failed")
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Neo4j error gets wrapped in ToolExecutionError
        with pytest.raises(ToolExecutionError) as exc_info:
            search_nodes("test", limit=10)
        
        assert "Search operation failed" in str(exc_info.value)


class TestFindRelatedNodes:
    """Test suite for find_related_nodes tool."""
    
    @patch('src.tools.graph_search.create_session')
    def test_find_related_nodes_basic(self, mock_create_session):
        """Test basic related nodes functionality."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Mock center node and related node
        mock_records = [
            {
                "center_id": 1,
                "center_labels": ["Person"],
                "center_properties": {"name": "Alice"},
                "related_id": 2,
                "related_labels": ["Organization"],
                "related_properties": {"name": "Engineering"},
                "relationship_type": "WORKS_AT",
                "relationship_properties": {},
                "is_outgoing": True
            }
        ]
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute find related
        node = {"type": "Person", "properties": {"name": "Alice"}}
        results = find_related_nodes(node, limit=20)
        
        # Assertions
        assert results["center_node"]["id"] == "1"
        assert len(results["related_nodes"]) == 1
        assert results["related_nodes"][0]["node"]["id"] == "2"
        assert results["related_nodes"][0]["relationship"]["type"] == "WORKS_AT"
        assert results["relationship_count"] == 1
    
    @patch('src.tools.graph_search.create_session')
    def test_find_related_nodes_with_relationship_types(self, mock_create_session):
        """Test finding related nodes with specific relationship types."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        mock_records = [
            {
                "center_id": 1,
                "center_labels": ["Person"],
                "center_properties": {"name": "Alice"},
                "related_id": 2,
                "related_labels": ["Person"],
                "related_properties": {"name": "Bob"},
                "relationship_type": "MANAGES",
                "relationship_properties": {},
                "is_outgoing": True
            }
        ]
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute find related with relationship type filter
        node = {"type": "Person", "properties": {"name": "Alice"}}
        results = find_related_nodes(
            node,
            relationship_types=["MANAGES"],
            limit=20
        )
        
        # Verify query includes relationship type filter
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "MANAGES" in query
    
    @patch('src.tools.graph_search.create_session')
    def test_find_related_nodes_direction_outgoing(self, mock_create_session):
        """Test finding related nodes with outgoing direction."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        mock_records = [
            {
                "center_id": 1,
                "center_labels": ["Person"],
                "center_properties": {"name": "Alice"},
                "related_id": 2,
                "related_labels": ["Project"],
                "related_properties": {"name": "Project X"},
                "relationship_type": "PARTICIPATES_IN",
                "relationship_properties": {},
                "is_outgoing": True
            }
        ]
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute find related with outgoing direction
        node = {"type": "Person", "properties": {"name": "Alice"}}
        results = find_related_nodes(node, direction="outgoing", limit=20)
        
        # Verify direction in query
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "-[r]->" in query
    
    @patch('src.tools.graph_search.create_session')
    def test_find_related_nodes_direction_incoming(self, mock_create_session):
        """Test finding related nodes with incoming direction."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        mock_records = [
            {
                "center_id": 1,
                "center_labels": ["Person"],
                "center_properties": {"name": "Bob"},
                "related_id": 2,
                "related_labels": ["Person"],
                "related_properties": {"name": "Alice"},
                "relationship_type": "MANAGES",
                "relationship_properties": {},
                "is_outgoing": False
            }
        ]
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute find related with incoming direction
        node = {"type": "Person", "properties": {"name": "Bob"}}
        results = find_related_nodes(node, direction="incoming", limit=20)
        
        # Verify direction in query
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "<-[r]-" in query
    
    @patch('src.tools.graph_search.create_session')
    def test_find_related_nodes_no_results(self, mock_create_session):
        """Test finding related nodes when center node exists but has no relationships."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        
        # Empty result - center node not found
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        # Execute find related
        node = {"type": "Person", "properties": {"name": "NonExistent"}}
        
        # GraphQueryError gets wrapped in ToolExecutionError
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, limit=20)
        
        assert "Find related nodes operation failed" in str(exc_info.value)
    
    def test_find_related_nodes_invalid_node_dict(self):
        """Test with invalid node parameter (not a dict)."""
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes("invalid", limit=20)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_find_related_nodes_missing_type(self):
        """Test with node missing 'type' field."""
        node = {"properties": {"name": "Alice"}}
        
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, limit=20)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_find_related_nodes_missing_properties(self):
        """Test with node missing 'properties' field."""
        node = {"type": "Person"}
        
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, limit=20)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_find_related_nodes_invalid_node_type(self):
        """Test with invalid node type."""
        node = {"type": "InvalidType", "properties": {"name": "Alice"}}
        
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, limit=20)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_find_related_nodes_invalid_relationship_type(self):
        """Test with invalid relationship type."""
        node = {"type": "Person", "properties": {"name": "Alice"}}
        
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(
                node,
                relationship_types=["INVALID_REL"],
                limit=20
            )
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_find_related_nodes_invalid_direction(self):
        """Test with invalid direction parameter."""
        node = {"type": "Person", "properties": {"name": "Alice"}}
        
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, direction="invalid", limit=20)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_find_related_nodes_invalid_depth_too_low(self):
        """Test with depth below minimum."""
        node = {"type": "Person", "properties": {"name": "Alice"}}
        
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, depth=0, limit=20)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_find_related_nodes_invalid_depth_too_high(self):
        """Test with depth above maximum."""
        node = {"type": "Person", "properties": {"name": "Alice"}}
        
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, depth=4, limit=20)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    def test_find_related_nodes_invalid_limit_too_high(self):
        """Test with limit exceeding maximum."""
        node = {"type": "Person", "properties": {"name": "Alice"}}
        
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, limit=200)
        
        assert "Invalid parameters" in str(exc_info.value)
    
    @patch('src.tools.graph_search.create_session')
    def test_find_related_nodes_neo4j_error(self, mock_create_session):
        """Test handling of Neo4j errors."""
        mock_session = MagicMock()
        from neo4j.exceptions import ServiceUnavailable
        mock_session.run.side_effect = ServiceUnavailable("Connection failed")
        mock_create_session.return_value.__enter__.return_value = mock_session
        
        node = {"type": "Person", "properties": {"name": "Alice"}}
        
        # Neo4j error gets wrapped in ToolExecutionError
        with pytest.raises(ToolExecutionError) as exc_info:
            find_related_nodes(node, limit=20)
        
        assert "Find related nodes operation failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

