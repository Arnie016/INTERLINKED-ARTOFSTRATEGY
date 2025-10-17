"""
Test suite for graph_stats tool in graph_analysis.py

Tests cover:
- Basic metrics calculation (node count, relationship count)
- Density metrics (graph density, degree distribution)
- Connectivity metrics (components, clustering coefficient)
- Node type and relationship type filtering
- Sample size validation
- Empty graph handling
- Error scenarios
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import the function under test
from src.tools.graph_analysis import graph_stats

# Import exceptions
from src.utils.errors import ValidationError, GraphQueryError, ToolExecutionError


@pytest.fixture
def mock_neo4j_driver():
    """Create a mock Neo4j driver"""
    driver = MagicMock()
    return driver


@pytest.fixture
def mock_session():
    """Create a mock Neo4j session"""
    session = MagicMock()
    return session


def create_mock_result(data: Dict[str, Any]) -> Mock:
    """Helper to create a mock Neo4j result"""
    result = Mock()
    record = Mock()
    for key, value in data.items():
        setattr(record, key, value)
        record.__getitem__ = lambda self, k: getattr(self, k)
    result.single.return_value = record
    return result


def create_mock_result_list(data_list: List[Dict[str, Any]]) -> Mock:
    """Helper to create a mock Neo4j result with multiple records"""
    result = Mock()
    records = []
    for data in data_list:
        record = Mock()
        for key, value in data.items():
            setattr(record, key, value)
            record.__getitem__ = lambda self, k: getattr(self, k)
        records.append(record)
    result.__iter__ = lambda self: iter(records)
    return result


class TestGraphStatsBasicMetrics:
    """Test basic metrics calculation"""
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_basic_metrics_simple_graph(self, mock_get_driver):
        """Test basic metrics on a simple graph"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock basic query result
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 10,
                "total_relationships": 15,
                "all_labels": [["Person"], ["Person"], ["Organization"]],
                "all_rel_types": ["WORKS_AT", "REPORTS_TO"]
            }),
            create_mock_result_list([
                {"label": "Person", "count": 8},
                {"label": "Organization", "count": 2}
            ]),
            create_mock_result_list([
                {"rel_type": "WORKS_AT", "count": 10},
                {"rel_type": "REPORTS_TO", "count": 5}
            ]),
            create_mock_result({
                "node_count": 10,
                "density": 0.15,
                "avg_degree": 3.0,
                "median_degree": 2,
                "max_degree": 8,
                "min_degree": 1
            }),
            create_mock_result_list([
                {"degree_bucket": "1-5", "node_count": 7},
                {"degree_bucket": "6-10", "node_count": 3}
            ]),
            create_mock_result({
                "highly_connected": 2,
                "isolated": 0
            }),
            create_mock_result({
                "num_components": 1,
                "largest_size": 10
            }),
            create_mock_result({
                "sample_ids": [1, 2, 3, 4, 5]
            }),
            create_mock_result({
                "avg_clustering": 0.45
            }),
            create_mock_result_list([
                {"path_length": 2},
                {"path_length": 3},
                {"path_length": 2},
                {"path_length": 4}
            ])
        ]
        
        result = graph_stats()
        
        assert result["basic_metrics"]["total_nodes"] == 10
        assert result["basic_metrics"]["total_relationships"] == 15
        assert "Person" in result["basic_metrics"]["node_labels"]
        assert "Organization" in result["basic_metrics"]["node_labels"]
        assert result["basic_metrics"]["node_labels"]["Person"] == 8
        assert result["basic_metrics"]["node_labels"]["Organization"] == 2
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_empty_graph_handling(self, mock_get_driver):
        """Test handling of empty graph"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock empty graph results - need to provide empty list for iteration queries
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 0,
                "total_relationships": 0,
                "all_labels": [],
                "all_rel_types": []
            }),
            create_mock_result_list([]),  # label_dist_query result
            create_mock_result_list([])   # rel_dist_query result
        ]
        
        result = graph_stats()
        
        assert result["basic_metrics"]["total_nodes"] == 0
        assert result["basic_metrics"]["total_relationships"] == 0
        assert result["explanation"] == "Graph is empty. No statistics to calculate."


class TestGraphStatsDensityMetrics:
    """Test density metrics calculation"""
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_sparse_graph_density(self, mock_get_driver):
        """Test density calculation for sparse graph"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock a sparse graph (density < 0.01)
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 100,
                "total_relationships": 50,
                "all_labels": [["Person"]],
                "all_rel_types": ["KNOWS"]
            }),
            create_mock_result_list([{"label": "Person", "count": 100}]),
            create_mock_result_list([{"rel_type": "KNOWS", "count": 50}]),
            create_mock_result({
                "node_count": 100,
                "density": 0.005,  # Very sparse
                "avg_degree": 1.0,
                "median_degree": 1,
                "max_degree": 5,
                "min_degree": 0
            }),
            create_mock_result_list([
                {"degree_bucket": "0 (isolated)", "node_count": 10},
                {"degree_bucket": "1-5", "node_count": 90}
            ]),
            create_mock_result({"highly_connected": 5, "isolated": 10}),
            create_mock_result({"num_components": 5, "largest_size": 80}),
            create_mock_result({"sample_ids": list(range(100))}),
            create_mock_result({"avg_clustering": 0.1}),
            create_mock_result_list([{"path_length": 3}, {"path_length": 4}])
        ]
        
        result = graph_stats()
        
        assert result["density_metrics"]["graph_density"] == 0.005
        assert "very sparse" in result["explanation"]
        assert result["density_metrics"]["average_degree"] == 1.0
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_dense_graph_density(self, mock_get_driver):
        """Test density calculation for dense graph"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock a dense graph (density > 0.5)
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 20,
                "total_relationships": 180,
                "all_labels": [["Person"]],
                "all_rel_types": ["KNOWS"]
            }),
            create_mock_result_list([{"label": "Person", "count": 20}]),
            create_mock_result_list([{"rel_type": "KNOWS", "count": 180}]),
            create_mock_result({
                "node_count": 20,
                "density": 0.6,  # Dense
                "avg_degree": 18.0,
                "median_degree": 18,
                "max_degree": 19,
                "min_degree": 15
            }),
            create_mock_result_list([
                {"degree_bucket": "11-20", "node_count": 20}
            ]),
            create_mock_result({"highly_connected": 10, "isolated": 0}),
            create_mock_result({"num_components": 1, "largest_size": 20}),
            create_mock_result({"sample_ids": list(range(20))}),
            create_mock_result({"avg_clustering": 0.8}),
            create_mock_result_list([{"path_length": 1}, {"path_length": 2}])
        ]
        
        result = graph_stats()
        
        assert result["density_metrics"]["graph_density"] == 0.6
        assert "dense" in result["explanation"]
        assert result["density_metrics"]["average_degree"] == 18.0


class TestGraphStatsDegreeDistribution:
    """Test degree distribution calculation"""
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_degree_buckets(self, mock_get_driver):
        """Test degree distribution bucketing"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 50,
                "total_relationships": 100,
                "all_labels": [["Person"]],
                "all_rel_types": ["KNOWS"]
            }),
            create_mock_result_list([{"label": "Person", "count": 50}]),
            create_mock_result_list([{"rel_type": "KNOWS", "count": 100}]),
            create_mock_result({
                "node_count": 50,
                "density": 0.08,
                "avg_degree": 4.0,
                "median_degree": 3,
                "max_degree": 15,
                "min_degree": 0
            }),
            create_mock_result_list([
                {"degree_bucket": "0 (isolated)", "node_count": 5},
                {"degree_bucket": "1-5", "node_count": 30},
                {"degree_bucket": "6-10", "node_count": 10},
                {"degree_bucket": "11-20", "node_count": 5}
            ]),
            create_mock_result({"highly_connected": 5, "isolated": 5}),
            create_mock_result({"num_components": 2, "largest_size": 45}),
            create_mock_result({"sample_ids": list(range(50))}),
            create_mock_result({"avg_clustering": 0.35}),
            create_mock_result_list([{"path_length": 2}, {"path_length": 3}])
        ]
        
        result = graph_stats()
        
        assert "0 (isolated)" in result["degree_distribution"]["degree_buckets"]
        assert result["degree_distribution"]["degree_buckets"]["0 (isolated)"] == 5
        assert result["degree_distribution"]["isolated_nodes"] == 5
        assert result["degree_distribution"]["highly_connected_nodes"] == 5


class TestGraphStatsConnectivityMetrics:
    """Test connectivity metrics calculation"""
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_connected_components(self, mock_get_driver):
        """Test connected components detection"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 30,
                "total_relationships": 40,
                "all_labels": [["Person"]],
                "all_rel_types": ["KNOWS"]
            }),
            create_mock_result_list([{"label": "Person", "count": 30}]),
            create_mock_result_list([{"rel_type": "KNOWS", "count": 40}]),
            create_mock_result({
                "node_count": 30,
                "density": 0.1,
                "avg_degree": 2.7,
                "median_degree": 2,
                "max_degree": 10,
                "min_degree": 0
            }),
            create_mock_result_list([
                {"degree_bucket": "0 (isolated)", "node_count": 3},
                {"degree_bucket": "1-5", "node_count": 25},
                {"degree_bucket": "6-10", "node_count": 2}
            ]),
            create_mock_result({"highly_connected": 3, "isolated": 3}),
            create_mock_result({"num_components": 4, "largest_size": 20}),
            create_mock_result({"sample_ids": list(range(30))}),
            create_mock_result({"avg_clustering": 0.3}),
            create_mock_result_list([{"path_length": 3}, {"path_length": 4}])
        ]
        
        result = graph_stats()
        
        assert result["connectivity_metrics"]["connected_components"] == 4
        assert result["connectivity_metrics"]["largest_component_size"] == 20
        assert "fragmented" in result["explanation"]
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_clustering_coefficient_high(self, mock_get_driver):
        """Test high clustering coefficient"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 25,
                "total_relationships": 50,
                "all_labels": [["Person"]],
                "all_rel_types": ["KNOWS"]
            }),
            create_mock_result_list([{"label": "Person", "count": 25}]),
            create_mock_result_list([{"rel_type": "KNOWS", "count": 50}]),
            create_mock_result({
                "node_count": 25,
                "density": 0.2,
                "avg_degree": 4.0,
                "median_degree": 4,
                "max_degree": 8,
                "min_degree": 2
            }),
            create_mock_result_list([{"degree_bucket": "1-5", "node_count": 20}, {"degree_bucket": "6-10", "node_count": 5}]),
            create_mock_result({"highly_connected": 3, "isolated": 0}),
            create_mock_result({"num_components": 1, "largest_size": 25}),
            create_mock_result({"sample_ids": list(range(25))}),
            create_mock_result({"avg_clustering": 0.75}),  # High clustering
            create_mock_result_list([{"path_length": 2}, {"path_length": 3}])
        ]
        
        result = graph_stats()
        
        assert result["connectivity_metrics"]["average_clustering_coefficient"] == 0.75
        assert "high" in result["explanation"]
        assert "strong local community structure" in result["explanation"]


class TestGraphStatsFiltering:
    """Test node type and relationship type filtering"""
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_node_type_filtering(self, mock_get_driver):
        """Test filtering by node type"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 50,
                "total_relationships": 80,
                "all_labels": [["Person"]],
                "all_rel_types": ["KNOWS"]
            }),
            create_mock_result_list([{"label": "Person", "count": 50}]),
            create_mock_result_list([{"rel_type": "KNOWS", "count": 80}]),
            create_mock_result({
                "node_count": 50,
                "density": 0.065,
                "avg_degree": 3.2,
                "median_degree": 3,
                "max_degree": 10,
                "min_degree": 1
            }),
            create_mock_result_list([{"degree_bucket": "1-5", "node_count": 45}, {"degree_bucket": "6-10", "node_count": 5}]),
            create_mock_result({"highly_connected": 5, "isolated": 0}),
            create_mock_result({"num_components": 1, "largest_size": 50}),
            create_mock_result({"sample_ids": list(range(50))}),
            create_mock_result({"avg_clustering": 0.4}),
            create_mock_result_list([{"path_length": 2}, {"path_length": 3}])
        ]
        
        result = graph_stats(node_type="Person")
        
        assert result["basic_metrics"]["total_nodes"] == 50
        # Verify the filtering was applied (we can't directly test the Cypher query, 
        # but we can verify the result is consistent with Person-only filtering)
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_relationship_type_filtering(self, mock_get_driver):
        """Test filtering by relationship type"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 60,
                "total_relationships": 40,
                "all_labels": [["Person"], ["Organization"]],
                "all_rel_types": ["WORKS_AT"]
            }),
            create_mock_result_list([{"label": "Person", "count": 50}, {"label": "Organization", "count": 10}]),
            create_mock_result_list([{"rel_type": "WORKS_AT", "count": 40}]),
            create_mock_result({
                "node_count": 60,
                "density": 0.02,
                "avg_degree": 1.3,
                "median_degree": 1,
                "max_degree": 10,
                "min_degree": 0
            }),
            create_mock_result_list([{"degree_bucket": "0 (isolated)", "node_count": 20}, {"degree_bucket": "1-5", "node_count": 40}]),
            create_mock_result({"highly_connected": 6, "isolated": 20}),
            create_mock_result({"num_components": 3, "largest_size": 50}),
            create_mock_result({"sample_ids": list(range(60))}),
            create_mock_result({"avg_clustering": 0.1}),
            create_mock_result_list([{"path_length": 1}, {"path_length": 2}])
        ]
        
        result = graph_stats(relationship_type="WORKS_AT")
        
        assert "WORKS_AT" in result["basic_metrics"]["relationship_types"]


class TestGraphStatsValidation:
    """Test parameter validation"""
    
    def test_invalid_sample_size_too_small(self):
        """Test validation rejects sample_size < 10"""
        with pytest.raises(ToolExecutionError) as exc_info:
            graph_stats(sample_size=5)
        
        assert "Invalid sample_size" in str(exc_info.value)
    
    def test_invalid_sample_size_too_large(self):
        """Test validation rejects sample_size > 5000"""
        with pytest.raises(ToolExecutionError) as exc_info:
            graph_stats(sample_size=10000)
        
        assert "Invalid sample_size" in str(exc_info.value)
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_valid_sample_size_boundary(self, mock_get_driver):
        """Test valid sample sizes at boundaries"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 100,
                "total_relationships": 150,
                "all_labels": [["Person"]],
                "all_rel_types": ["KNOWS"]
            }),
            create_mock_result_list([{"label": "Person", "count": 100}]),
            create_mock_result_list([{"rel_type": "KNOWS", "count": 150}]),
            create_mock_result({
                "node_count": 100,
                "density": 0.03,
                "avg_degree": 3.0,
                "median_degree": 3,
                "max_degree": 10,
                "min_degree": 1
            }),
            create_mock_result_list([{"degree_bucket": "1-5", "node_count": 90}, {"degree_bucket": "6-10", "node_count": 10}]),
            create_mock_result({"highly_connected": 10, "isolated": 0}),
            create_mock_result({"num_components": 1, "largest_size": 100}),
            create_mock_result({"sample_ids": list(range(10))}),
            create_mock_result({"avg_clustering": 0.4}),
            create_mock_result_list([{"path_length": 2}, {"path_length": 3}])
        ]
        
        # Should not raise any exception
        result = graph_stats(sample_size=10)
        assert result is not None


class TestGraphStatsErrorHandling:
    """Test error handling"""
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_neo4j_error_handling(self, mock_get_driver):
        """Test handling of Neo4j errors"""
        from neo4j.exceptions import Neo4jError
        
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Simulate Neo4j error
        mock_session.run.side_effect = Neo4jError("Database connection failed")
        
        with pytest.raises(GraphQueryError) as exc_info:
            graph_stats()
        
        assert "Failed to calculate graph statistics" in str(exc_info.value)
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_unexpected_error_handling(self, mock_get_driver):
        """Test handling of unexpected errors"""
        # Simulate unexpected error
        mock_get_driver.side_effect = Exception("Unexpected error")
        
        with pytest.raises(ToolExecutionError) as exc_info:
            graph_stats()
        
        assert "Graph statistics operation failed" in str(exc_info.value)


class TestGraphStatsExplanationGeneration:
    """Test explanation generation"""
    
    @patch('src.tools.graph_analysis.get_driver')
    def test_explanation_describes_graph_structure(self, mock_get_driver):
        """Test that explanation provides meaningful description"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_get_driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_session.run.side_effect = [
            create_mock_result({
                "total_nodes": 100,
                "total_relationships": 200,
                "all_labels": [["Person"]],
                "all_rel_types": ["KNOWS"]
            }),
            create_mock_result_list([{"label": "Person", "count": 100}]),
            create_mock_result_list([{"rel_type": "KNOWS", "count": 200}]),
            create_mock_result({
                "node_count": 100,
                "density": 0.04,
                "avg_degree": 4.0,
                "median_degree": 4,
                "max_degree": 15,
                "min_degree": 1
            }),
            create_mock_result_list([{"degree_bucket": "1-5", "node_count": 80}, {"degree_bucket": "6-10", "node_count": 15}, {"degree_bucket": "11-20", "node_count": 5}]),
            create_mock_result({"highly_connected": 10, "isolated": 0}),
            create_mock_result({"num_components": 1, "largest_size": 100}),
            create_mock_result({"sample_ids": list(range(100))}),
            create_mock_result({"avg_clustering": 0.5}),
            create_mock_result_list([{"path_length": 2}, {"path_length": 3}, {"path_length": 4}])
        ]
        
        result = graph_stats()
        explanation = result["explanation"]
        
        # Check that explanation contains key information
        assert "100" in explanation  # node count
        assert "200" in explanation  # relationship count
        assert "density" in explanation.lower()
        assert "clustering" in explanation.lower()
        assert "connected" in explanation.lower()
        
        # Verify it's human-readable
        assert len(explanation) > 50  # Should be a substantial description
        assert explanation.endswith(".")  # Should be complete sentences

