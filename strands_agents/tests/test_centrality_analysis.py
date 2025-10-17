"""
Unit tests for centrality_analysis tool.

These tests verify the centrality analysis algorithms (PageRank, Degree,
Betweenness, Closeness) work correctly with mock Neo4j data.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from src.tools.graph_analysis import centrality_analysis
from src.utils.errors import ValidationError, GraphQueryError, ToolExecutionError


class TestCentralityAnalysisValidation:
    """Test input validation for centrality_analysis."""
    
    def test_invalid_algorithm(self):
        """Test that invalid algorithm raises ValidationError."""
        with pytest.raises(ToolExecutionError) as exc_info:
            centrality_analysis(algorithm="invalid_algo")
        
        assert "Invalid algorithm" in str(exc_info.value)
    
    def test_invalid_node_type(self):
        """Test that invalid node type raises ValidationError."""
        with pytest.raises(ToolExecutionError) as exc_info:
            centrality_analysis(algorithm="degree", node_type="InvalidType")
        
        assert "Invalid node type" in str(exc_info.value)
    
    def test_limit_validation_too_high(self):
        """Test that limit exceeding max raises ValidationError."""
        with pytest.raises(ToolExecutionError) as exc_info:
            centrality_analysis(algorithm="degree", limit=100)
        
        assert "Limit cannot exceed" in str(exc_info.value)
    
    def test_valid_algorithms(self):
        """Test that all valid algorithms are accepted."""
        valid_algos = ["pagerank", "degree", "betweenness", "closeness"]
        
        for algo in valid_algos:
            with patch('src.tools.graph_analysis.create_session') as mock_session:
                # Mock empty result
                mock_record = {"top_nodes": [], "total_count": 0}
                mock_result = Mock()
                mock_result.single.return_value = mock_record
                mock_session_obj = MagicMock()
                mock_session_obj.__enter__.return_value.run.return_value = mock_result
                mock_session.return_value = mock_session_obj
                
                result = centrality_analysis(algorithm=algo)
                
                assert result["algorithm"] == algo


class TestCentralityAnalysisDegree:
    """Test degree centrality algorithm."""
    
    def test_degree_centrality_basic(self):
        """Test basic degree centrality calculation."""
        # Mock Neo4j response for degree centrality
        mock_nodes = [
            {
                "id": 1,
                "labels": ["Person"],
                "properties": {"name": "Alice", "email": "alice@example.com"},
                "centrality_score": 15
            },
            {
                "id": 2,
                "labels": ["Person"],
                "properties": {"name": "Bob", "email": "bob@example.com"},
                "centrality_score": 10
            },
            {
                "id": 3,
                "labels": ["Person"],
                "properties": {"name": "Charlie", "email": "charlie@example.com"},
                "centrality_score": 8
            }
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 3,
            "mean_centrality": 11.0,
            "max_centrality": 15,
            "min_centrality": 8
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="degree", limit=3)
            
            # Verify basic structure
            assert result["algorithm"] == "degree"
            assert result["node_type"] is None
            assert len(result["top_nodes"]) == 3
            
            # Verify top node
            assert result["top_nodes"][0]["id"] == "1"
            assert result["top_nodes"][0]["labels"] == ["Person"]
            assert result["top_nodes"][0]["properties"]["name"] == "Alice"
            assert result["top_nodes"][0]["centrality_score"] == 15.0
            assert result["top_nodes"][0]["rank"] == 1
            
            # Verify statistics
            assert result["statistics"]["total_analyzed"] == 3
            assert result["statistics"]["mean_centrality"] == 11.0
            assert result["statistics"]["max_centrality"] == 15.0
            assert result["statistics"]["min_centrality"] == 8.0
            assert result["statistics"]["median_centrality"] == 10.0  # Middle value
    
    def test_degree_centrality_with_node_type(self):
        """Test degree centrality filtered by node type."""
        mock_nodes = [
            {
                "id": 1,
                "labels": ["Organization"],
                "properties": {"name": "Acme Corp"},
                "centrality_score": 25
            }
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 1,
            "mean_centrality": 25.0,
            "max_centrality": 25,
            "min_centrality": 25
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(
                algorithm="degree",
                node_type="Organization",
                limit=10
            )
            
            assert result["node_type"] == "Organization"
            assert result["top_nodes"][0]["labels"] == ["Organization"]


class TestCentralityAnalysisPageRank:
    """Test PageRank centrality algorithm."""
    
    def test_pagerank_basic(self):
        """Test basic PageRank calculation."""
        mock_nodes = [
            {
                "id": 1,
                "labels": ["Person"],
                "properties": {"name": "Alice"},
                "centrality_score": 2.55
            },
            {
                "id": 2,
                "labels": ["Person"],
                "properties": {"name": "Bob"},
                "centrality_score": 1.85
            }
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 2,
            "mean_centrality": 2.2,
            "max_centrality": 2.55,
            "min_centrality": 1.85
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="pagerank")
            
            assert result["algorithm"] == "pagerank"
            assert len(result["top_nodes"]) == 2
            assert result["top_nodes"][0]["centrality_score"] == 2.55


class TestCentralityAnalysisBetweenness:
    """Test betweenness centrality algorithm."""
    
    def test_betweenness_basic(self):
        """Test basic betweenness centrality calculation."""
        mock_nodes = [
            {
                "id": 5,
                "labels": ["Person"],
                "properties": {"name": "Bridge Node"},
                "centrality_score": 42
            }
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 1,
            "mean_centrality": 42.0,
            "max_centrality": 42,
            "min_centrality": 42
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="betweenness", limit=5)
            
            assert result["algorithm"] == "betweenness"
            assert "bridging connections" in result["explanation"]


class TestCentralityAnalysisCloseness:
    """Test closeness centrality algorithm."""
    
    def test_closeness_basic(self):
        """Test basic closeness centrality calculation."""
        mock_nodes = [
            {
                "id": 10,
                "labels": ["Person"],
                "properties": {"name": "Central Node"},
                "centrality_score": 0.85
            }
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 1,
            "mean_centrality": 0.85,
            "max_centrality": 0.85,
            "min_centrality": 0.85
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="closeness", limit=10)
            
            assert result["algorithm"] == "closeness"
            assert "proximity" in result["explanation"]


class TestCentralityAnalysisEdgeCases:
    """Test edge cases and error handling."""
    
    def test_no_nodes_found(self):
        """Test handling when no nodes are found."""
        mock_record = {
            "top_nodes": [],
            "total_count": 0
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="degree")
            
            assert result["top_nodes"] == []
            assert result["statistics"]["total_analyzed"] == 0
            assert "No nodes found" in result["explanation"]
    
    def test_single_node_result(self):
        """Test with single node result."""
        mock_nodes = [
            {
                "id": 1,
                "labels": ["Person"],
                "properties": {"name": "Only Node"},
                "centrality_score": 5
            }
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 1,
            "mean_centrality": 5.0,
            "max_centrality": 5,
            "min_centrality": 5
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="degree")
            
            assert len(result["top_nodes"]) == 1
            assert result["statistics"]["median_centrality"] == 5.0
    
    def test_neo4j_error_handling(self):
        """Test Neo4j error handling."""
        from neo4j.exceptions import Neo4jError
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.side_effect = Neo4jError("Database error")
            mock_session.return_value = mock_session_obj
            
            with pytest.raises(GraphQueryError) as exc_info:
                centrality_analysis(algorithm="degree")
            
            assert "Failed to perform" in str(exc_info.value)


class TestCentralityAnalysisExplanations:
    """Test explanation generation."""
    
    def test_explanation_content(self):
        """Test that explanation contains relevant information."""
        mock_nodes = [
            {
                "id": 1,
                "labels": ["Person"],
                "properties": {"name": "Alice"},
                "centrality_score": 10
            }
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 1,
            "mean_centrality": 10.0,
            "max_centrality": 10,
            "min_centrality": 10
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="degree")
            
            explanation = result["explanation"]
            assert "Alice" in explanation
            assert "Person" in explanation
            assert "10" in explanation or "10.0" in explanation
    
    def test_algorithm_descriptions(self):
        """Test that each algorithm has appropriate description."""
        algorithms = {
            "degree": "number of direct connections",
            "pagerank": "overall importance and influence",
            "betweenness": "bridging connections",
            "closeness": "proximity"
        }
        
        for algo, expected_text in algorithms.items():
            mock_nodes = [
                {
                    "id": 1,
                    "labels": ["Person"],
                    "properties": {"name": "Test"},
                    "centrality_score": 5
                }
            ]
            
            mock_record = {
                "top_nodes": mock_nodes,
                "total_count": 1,
                "mean_centrality": 5.0,
                "max_centrality": 5,
                "min_centrality": 5
            }
            
            with patch('src.tools.graph_analysis.create_session') as mock_session:
                mock_result = Mock()
                mock_result.single.return_value = mock_record
                mock_session_obj = MagicMock()
                mock_session_obj.__enter__.return_value.run.return_value = mock_result
                mock_session.return_value = mock_session_obj
                
                result = centrality_analysis(algorithm=algo)
                
                assert expected_text in result["explanation"]


class TestCentralityAnalysisMedianCalculation:
    """Test median centrality calculation."""
    
    def test_median_odd_number_of_nodes(self):
        """Test median with odd number of nodes."""
        mock_nodes = [
            {"id": 1, "labels": ["Person"], "properties": {"name": "A"}, "centrality_score": 10},
            {"id": 2, "labels": ["Person"], "properties": {"name": "B"}, "centrality_score": 20},
            {"id": 3, "labels": ["Person"], "properties": {"name": "C"}, "centrality_score": 30}
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 3,
            "mean_centrality": 20.0,
            "max_centrality": 30,
            "min_centrality": 10
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="degree")
            
            assert result["statistics"]["median_centrality"] == 20.0
    
    def test_median_even_number_of_nodes(self):
        """Test median with even number of nodes."""
        mock_nodes = [
            {"id": 1, "labels": ["Person"], "properties": {"name": "A"}, "centrality_score": 10},
            {"id": 2, "labels": ["Person"], "properties": {"name": "B"}, "centrality_score": 20},
            {"id": 3, "labels": ["Person"], "properties": {"name": "C"}, "centrality_score": 30},
            {"id": 4, "labels": ["Person"], "properties": {"name": "D"}, "centrality_score": 40}
        ]
        
        mock_record = {
            "top_nodes": mock_nodes,
            "total_count": 4,
            "mean_centrality": 25.0,
            "max_centrality": 40,
            "min_centrality": 10
        }
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = centrality_analysis(algorithm="degree")
            
            # Median of [10, 20, 30, 40] = (20 + 30) / 2 = 25
            assert result["statistics"]["median_centrality"] == 25.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

