"""
Unit tests for community_detection tool.

These tests verify the community detection algorithms (Label Propagation,
Connected Components, Modularity Clustering) work correctly with mock Neo4j data.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.tools.graph_analysis import community_detection
from src.utils.errors import ValidationError, GraphQueryError, ToolExecutionError


class TestCommunityDetectionValidation:
    """Test input validation for community_detection."""
    
    def test_invalid_algorithm(self):
        """Test that invalid algorithm raises ValidationError."""
        with pytest.raises(ToolExecutionError) as exc_info:
            community_detection(algorithm="invalid_algo")
        
        assert "Invalid algorithm" in str(exc_info.value)
    
    def test_invalid_node_type(self):
        """Test that invalid node type raises ValidationError."""
        with pytest.raises(ToolExecutionError) as exc_info:
            community_detection(algorithm="label_propagation", node_type="InvalidType")
        
        assert "Invalid node type" in str(exc_info.value)
    
    def test_invalid_min_community_size(self):
        """Test that invalid min_community_size raises ValidationError."""
        with pytest.raises(ToolExecutionError) as exc_info:
            community_detection(algorithm="label_propagation", min_community_size=0)
        
        assert "min_community_size must be an integer >= 1" in str(exc_info.value)
    
    def test_valid_algorithms(self):
        """Test that all valid algorithms are accepted."""
        valid_algos = ["label_propagation", "connected_components", "modularity_clustering"]
        
        for algo in valid_algos:
            with patch('src.tools.graph_analysis.create_session') as mock_session:
                # Mock empty result
                mock_record = {"communities": []}
                mock_result = Mock()
                mock_result.single.return_value = mock_record
                mock_session_obj = MagicMock()
                mock_session_obj.__enter__.return_value.run.return_value = mock_result
                mock_session.return_value = mock_session_obj
                
                result = community_detection(algorithm=algo)
                
                assert result["algorithm"] == algo


class TestCommunityDetectionLabelPropagation:
    """Test label propagation community detection algorithm."""
    
    def test_label_propagation_basic(self):
        """Test basic label propagation community detection."""
        # Mock Neo4j response with two communities
        mock_communities = [
            {
                "nodes": [
                    {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                    {"id": 2, "labels": ["Person"], "properties": {"name": "Bob"}},
                    {"id": 3, "labels": ["Person"], "properties": {"name": "Charlie"}}
                ],
                "size": 3,
                "central_node": {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                "density": 0.667
            },
            {
                "nodes": [
                    {"id": 4, "labels": ["Person"], "properties": {"name": "David"}},
                    {"id": 5, "labels": ["Person"], "properties": {"name": "Eve"}}
                ],
                "size": 2,
                "central_node": {"id": 4, "labels": ["Person"], "properties": {"name": "David"}},
                "density": 1.0
            }
        ]
        
        mock_record = {"communities": mock_communities}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(algorithm="label_propagation")
            
            # Verify basic structure
            assert result["algorithm"] == "label_propagation"
            assert result["node_type"] is None
            assert len(result["communities"]) == 2
            
            # Verify first community
            assert result["communities"][0]["community_id"] == 1
            assert result["communities"][0]["size"] == 3
            assert len(result["communities"][0]["nodes"]) == 3
            assert result["communities"][0]["density"] == 0.667
            
            # Verify statistics
            assert result["statistics"]["total_communities"] == 2
            assert result["statistics"]["total_nodes_analyzed"] == 5
            assert result["statistics"]["largest_community_size"] == 3
            assert result["statistics"]["smallest_community_size"] == 2
    
    def test_label_propagation_with_node_type(self):
        """Test label propagation filtered by node type."""
        mock_communities = [
            {
                "nodes": [
                    {"id": 1, "labels": ["Organization"], "properties": {"name": "Acme Corp"}},
                    {"id": 2, "labels": ["Organization"], "properties": {"name": "Tech Inc"}}
                ],
                "size": 2,
                "central_node": {"id": 1, "labels": ["Organization"], "properties": {"name": "Acme Corp"}},
                "density": 1.0
            }
        ]
        
        mock_record = {"communities": mock_communities}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(
                algorithm="label_propagation",
                node_type="Organization"
            )
            
            assert result["node_type"] == "Organization"
            assert result["communities"][0]["nodes"][0]["labels"] == ["Organization"]


class TestCommunityDetectionConnectedComponents:
    """Test connected components community detection algorithm."""
    
    def test_connected_components_basic(self):
        """Test basic connected components detection."""
        mock_communities = [
            {
                "nodes": [
                    {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                    {"id": 2, "labels": ["Person"], "properties": {"name": "Bob"}}
                ],
                "size": 2,
                "central_node": {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                "density": 1.0
            }
        ]
        
        mock_record = {"communities": mock_communities}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(algorithm="connected_components")
            
            assert result["algorithm"] == "connected_components"
            assert len(result["communities"]) == 1


class TestCommunityDetectionModularityClustering:
    """Test modularity clustering community detection algorithm."""
    
    def test_modularity_clustering_basic(self):
        """Test basic modularity clustering."""
        mock_communities = [
            {
                "nodes": [
                    {"id": 1, "labels": ["Person"], "properties": {"name": "Team A Member 1"}},
                    {"id": 2, "labels": ["Person"], "properties": {"name": "Team A Member 2"}},
                    {"id": 3, "labels": ["Person"], "properties": {"name": "Team A Member 3"}}
                ],
                "size": 3,
                "central_node": {"id": 1, "labels": ["Person"], "properties": {"name": "Team A Member 1"}},
                "density": 0.667
            }
        ]
        
        mock_record = {"communities": mock_communities}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(algorithm="modularity_clustering")
            
            assert result["algorithm"] == "modularity_clustering"
            assert result["communities"][0]["size"] == 3


class TestCommunityDetectionEdgeCases:
    """Test edge cases and error handling."""
    
    def test_no_communities_found(self):
        """Test handling when no communities are found."""
        mock_record = {"communities": []}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(algorithm="label_propagation")
            
            assert result["communities"] == []
            assert result["statistics"]["total_communities"] == 0
            assert "No communities found" in result["explanation"]
    
    def test_single_community_result(self):
        """Test with single community result."""
        mock_communities = [
            {
                "nodes": [
                    {"id": 1, "labels": ["Person"], "properties": {"name": "Only Community"}},
                    {"id": 2, "labels": ["Person"], "properties": {"name": "Member 2"}}
                ],
                "size": 2,
                "central_node": {"id": 1, "labels": ["Person"], "properties": {"name": "Only Community"}},
                "density": 1.0
            }
        ]
        
        mock_record = {"communities": mock_communities}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(algorithm="label_propagation")
            
            assert len(result["communities"]) == 1
            assert result["statistics"]["total_communities"] == 1
            assert result["statistics"]["largest_community_size"] == 2
            assert result["statistics"]["smallest_community_size"] == 2
    
    def test_neo4j_error_handling(self):
        """Test Neo4j error handling."""
        from neo4j.exceptions import Neo4jError
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.side_effect = Neo4jError("Database error")
            mock_session.return_value = mock_session_obj
            
            with pytest.raises(GraphQueryError) as exc_info:
                community_detection(algorithm="label_propagation")
            
            assert "Failed to perform" in str(exc_info.value)


class TestCommunityDetectionStatistics:
    """Test statistics calculation."""
    
    def test_modularity_score_calculation(self):
        """Test that modularity score is calculated correctly."""
        mock_communities = [
            {
                "nodes": [{"id": 1, "labels": ["Person"], "properties": {"name": "A"}}] * 3,
                "size": 3,
                "central_node": {"id": 1, "labels": ["Person"], "properties": {"name": "A"}},
                "density": 0.8
            },
            {
                "nodes": [{"id": 2, "labels": ["Person"], "properties": {"name": "B"}}] * 2,
                "size": 2,
                "central_node": {"id": 2, "labels": ["Person"], "properties": {"name": "B"}},
                "density": 0.6
            }
        ]
        
        mock_record = {"communities": mock_communities}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(algorithm="label_propagation")
            
            # Modularity should be average of densities: (0.8 + 0.6) / 2 = 0.7
            assert result["statistics"]["modularity_score"] == 0.7
    
    def test_average_community_size(self):
        """Test average community size calculation."""
        mock_communities = [
            {
                "nodes": [{"id": i, "labels": ["Person"], "properties": {"name": f"P{i}"}} for i in range(10)],
                "size": 10,
                "central_node": {"id": 1, "labels": ["Person"], "properties": {"name": "P1"}},
                "density": 0.5
            },
            {
                "nodes": [{"id": i, "labels": ["Person"], "properties": {"name": f"P{i}"}} for i in range(10, 15)],
                "size": 5,
                "central_node": {"id": 10, "labels": ["Person"], "properties": {"name": "P10"}},
                "density": 0.6
            }
        ]
        
        mock_record = {"communities": mock_communities}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(algorithm="label_propagation")
            
            # Average: (10 + 5) / 2 = 7.5
            assert result["statistics"]["average_community_size"] == 7.5


class TestCommunityDetectionExplanations:
    """Test explanation generation."""
    
    def test_explanation_content(self):
        """Test that explanation contains relevant information."""
        mock_communities = [
            {
                "nodes": [
                    {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                    {"id": 2, "labels": ["Person"], "properties": {"name": "Bob"}}
                ],
                "size": 2,
                "central_node": {"id": 1, "labels": ["Person"], "properties": {"name": "Alice"}},
                "density": 1.0
            }
        ]
        
        mock_record = {"communities": mock_communities}
        
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(algorithm="label_propagation")
            
            explanation = result["explanation"]
            assert "Alice" in explanation
            assert "Person" in explanation
            assert "label_propagation" in explanation
            assert "Modularity score" in explanation


class TestCommunityDetectionParameters:
    """Test parameter handling."""
    
    def test_min_community_size_parameter(self):
        """Test min_community_size parameter is used correctly."""
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_record = {"communities": []}
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(
                algorithm="label_propagation",
                min_community_size=5
            )
            
            # Verify the query was called with correct parameters
            call_args = mock_session_obj.__enter__.return_value.run.call_args
            assert call_args[0][1]["min_size"] == 5
    
    def test_max_communities_parameter(self):
        """Test max_communities parameter is used correctly."""
        with patch('src.tools.graph_analysis.create_session') as mock_session:
            mock_record = {"communities": []}
            mock_result = Mock()
            mock_result.single.return_value = mock_record
            mock_session_obj = MagicMock()
            mock_session_obj.__enter__.return_value.run.return_value = mock_result
            mock_session.return_value = mock_session_obj
            
            result = community_detection(
                algorithm="label_propagation",
                max_communities=10
            )
            
            # Verify the query was called with correct parameters
            call_args = mock_session_obj.__enter__.return_value.run.call_args
            assert call_args[0][1]["max_communities"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

