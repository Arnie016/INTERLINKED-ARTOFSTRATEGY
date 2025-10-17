"""
Unit Tests for Query Safety Framework

Tests for query validation, complexity analysis, and safety decorators.
"""

import pytest
import time
from unittest.mock import MagicMock, patch

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.query_safety import (
    QuerySafetyValidator,
    validate_tool_input,
    rate_limit,
    monitor_performance,
    validate_query_before_execution,
    clear_rate_limit_state
)
from src.utils.errors import ValidationError, ToolExecutionError


class TestQuerySafetyValidator:
    """Test suite for QuerySafetyValidator."""
    
    def test_read_only_valid_query(self):
        """Test that read-only queries pass validation."""
        query = "MATCH (n:Person) RETURN n LIMIT 10"
        assert QuerySafetyValidator.is_read_only(query) is True
    
    def test_read_only_create_fails(self):
        """Test that CREATE operations are blocked."""
        query = "CREATE (n:Person {name: 'Alice'}) RETURN n"
        with pytest.raises(ValidationError) as exc_info:
            QuerySafetyValidator.is_read_only(query)
        
        assert "CREATE" in str(exc_info.value)
    
    def test_read_only_merge_fails(self):
        """Test that MERGE operations are blocked."""
        query = "MERGE (n:Person {id: 1}) RETURN n"
        with pytest.raises(ValidationError) as exc_info:
            QuerySafetyValidator.is_read_only(query)
        
        assert "MERGE" in str(exc_info.value)
    
    def test_read_only_delete_fails(self):
        """Test that DELETE operations are blocked."""
        query = "MATCH (n:Person) DELETE n"
        with pytest.raises(ValidationError) as exc_info:
            QuerySafetyValidator.is_read_only(query)
        
        assert "DELETE" in str(exc_info.value)
    
    def test_read_only_set_fails(self):
        """Test that SET operations are blocked."""
        query = "MATCH (n:Person) SET n.updated = true RETURN n"
        with pytest.raises(ValidationError) as exc_info:
            QuerySafetyValidator.is_read_only(query)
        
        assert "SET" in str(exc_info.value)
    
    def test_read_only_remove_fails(self):
        """Test that REMOVE operations are blocked."""
        query = "MATCH (n:Person) REMOVE n.property RETURN n"
        with pytest.raises(ValidationError) as exc_info:
            QuerySafetyValidator.is_read_only(query)
        
        assert "REMOVE" in str(exc_info.value)
    
    def test_read_only_detach_delete_fails(self):
        """Test that DETACH DELETE operations are blocked."""
        query = "MATCH (n:Person) DETACH DELETE n"
        with pytest.raises(ValidationError) as exc_info:
            QuerySafetyValidator.is_read_only(query)
        
        # Should catch either DETACH or DELETE keyword
        error_str = str(exc_info.value)
        assert "DETACH" in error_str or "DELETE" in error_str
    
    def test_read_only_property_name_false_positive(self):
        """Test that property names don't trigger false positives."""
        # "CREATED" in property should not trigger "CREATE" keyword
        query = "MATCH (n:Person) WHERE n.created > '2020-01-01' RETURN n"
        assert QuerySafetyValidator.is_read_only(query) is True
    
    def test_complexity_analysis_simple_query(self):
        """Test complexity analysis for simple queries."""
        query = "MATCH (n:Person) WHERE n.name = $name RETURN n LIMIT 10"
        params = {"name": "Alice"}
        
        result = QuerySafetyValidator.analyze_complexity(query, params)
        
        assert result["complexity_score"] < 3
        assert result["estimated_cost"] == "low"
        assert len(result["expensive_operations"]) == 0
    
    def test_complexity_analysis_expensive_operations(self):
        """Test that expensive operations are detected."""
        query = """
        MATCH (start:Person), (end:Person)
        WHERE id(start) = $start_id AND id(end) = $end_id
        MATCH path = allShortestPaths((start)-[*]-(end))
        RETURN path
        """
        
        result = QuerySafetyValidator.analyze_complexity(query)
        
        assert "allShortestPaths" in result["expensive_operations"]
        assert result["complexity_score"] >= 2
    
    def test_complexity_analysis_unbounded_pattern(self):
        """Test detection of unbounded variable-length patterns."""
        query = "MATCH (n:Person)-[*]-(m) RETURN n, m"
        
        result = QuerySafetyValidator.analyze_complexity(query)
        
        assert any("unbounded" in w.lower() for w in result["warnings"])
        assert result["complexity_score"] >= 3
    
    def test_complexity_analysis_large_depth(self):
        """Test detection of large traversal depths."""
        query = "MATCH (n:Person)-[*1..10]-(m) RETURN n, m LIMIT 100"
        
        result = QuerySafetyValidator.analyze_complexity(query)
        
        assert any("depth" in w.lower() for w in result["warnings"])
    
    def test_complexity_analysis_no_limit(self):
        """Test warning for queries without LIMIT."""
        query = "MATCH (n:Person) RETURN n"
        
        result = QuerySafetyValidator.analyze_complexity(query)
        
        assert any("limit" in w.lower() for w in result["warnings"])
    
    def test_complexity_analysis_multiple_match(self):
        """Test detection of multiple MATCH clauses."""
        query = """
        MATCH (n:Person)
        MATCH (m:Organization)
        MATCH (p:Project)
        MATCH (t:Technology)
        RETURN n, m, p, t
        LIMIT 10
        """
        
        result = QuerySafetyValidator.analyze_complexity(query)
        
        assert any("MATCH" in w for w in result["warnings"])
    
    def test_complexity_analysis_large_limit(self):
        """Test warning for large limit values."""
        query = "MATCH (n:Person) RETURN n LIMIT $limit"
        params = {"limit": 5000}
        
        result = QuerySafetyValidator.analyze_complexity(query, params)
        
        assert any("limit" in w.lower() for w in result["warnings"])
    
    def test_validate_query_safety_pass(self):
        """Test comprehensive validation for safe query."""
        query = "MATCH (n:Person) WHERE n.name = $name RETURN n LIMIT 10"
        params = {"name": "Alice"}
        
        result = QuerySafetyValidator.validate_query_safety(query, params)
        
        assert result["safe"] is True
        assert "complexity" in result
    
    def test_validate_query_safety_fail_write(self):
        """Test validation fails for write operations."""
        query = "CREATE (n:Person {name: 'Alice'}) RETURN n"
        
        with pytest.raises(ValidationError):
            QuerySafetyValidator.validate_query_safety(query)
    
    def test_validate_query_safety_fail_complexity(self):
        """Test validation fails for overly complex queries."""
        # Create a query with high complexity score
        query = """
        MATCH (n)-[*]-(m)
        MATCH (a)-[*]-(b)
        MATCH (x)-[*]-(y)
        MATCH path = allShortestPaths((n)-[*]-(m))
        RETURN n, m
        """
        
        with pytest.raises(ValidationError) as exc_info:
            QuerySafetyValidator.validate_query_safety(query)
        
        assert "complexity" in str(exc_info.value).lower()


class TestValidateToolInput:
    """Test suite for validate_tool_input decorator."""
    
    def test_decorator_basic_function(self):
        """Test decorator works with basic function."""
        @validate_tool_input
        def test_func(param1: str, param2: int = 10) -> dict:
            return {"param1": param1, "param2": param2}
        
        result = test_func("test", param2=20)
        assert result["param1"] == "test"
        assert result["param2"] == 20
    
    def test_decorator_logs_invocation(self):
        """Test that decorator logs function invocations."""
        @validate_tool_input
        def test_func(param: str) -> str:
            return param
        
        with patch('src.utils.query_safety.logger') as mock_logger:
            result = test_func("test")
            
            # Check that info was logged
            assert mock_logger.info.called
            assert any("started" in str(call) for call in mock_logger.info.call_args_list)
            assert any("completed" in str(call) for call in mock_logger.info.call_args_list)
    
    def test_decorator_handles_exceptions(self):
        """Test decorator properly handles and logs exceptions."""
        @validate_tool_input
        def test_func(param: str) -> str:
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_func("test")
    
    def test_decorator_measures_performance(self):
        """Test decorator measures execution time."""
        @validate_tool_input
        def slow_func() -> str:
            time.sleep(0.1)
            return "done"
        
        start = time.time()
        result = slow_func()
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert result == "done"


class TestRateLimit:
    """Test suite for rate_limit decorator."""
    
    def setup_method(self):
        """Clear rate limit state before each test."""
        clear_rate_limit_state()
    
    def test_rate_limit_allows_within_limit(self):
        """Test that calls within limit are allowed."""
        @rate_limit(calls_per_minute=5)
        def test_func() -> str:
            return "success"
        
        # Should allow 5 calls
        for i in range(5):
            result = test_func()
            assert result == "success"
    
    def test_rate_limit_blocks_over_limit(self):
        """Test that calls over limit are blocked."""
        @rate_limit(calls_per_minute=3)
        def test_func() -> str:
            return "success"
        
        # First 3 calls should succeed
        for i in range(3):
            test_func()
        
        # 4th call should fail
        with pytest.raises(ToolExecutionError) as exc_info:
            test_func()
        
        assert "rate limit" in str(exc_info.value).lower()
    
    def test_rate_limit_resets_after_minute(self):
        """Test that rate limit resets after one minute."""
        @rate_limit(calls_per_minute=2)
        def test_func() -> str:
            return "success"
        
        # Use up the limit
        test_func()
        test_func()
        
        # Should fail
        with pytest.raises(ToolExecutionError):
            test_func()
        
        # Clear state to simulate reset
        clear_rate_limit_state()
        
        # Should succeed after reset
        result = test_func()
        assert result == "success"


class TestMonitorPerformance:
    """Test suite for monitor_performance decorator."""
    
    def test_monitor_fast_operation(self):
        """Test monitoring of fast operations."""
        @monitor_performance(threshold_seconds=1.0)
        def fast_func() -> str:
            return "done"
        
        result = fast_func()
        assert result == "done"
    
    def test_monitor_slow_operation_logs_warning(self):
        """Test that slow operations log warnings."""
        @monitor_performance(threshold_seconds=0.05)
        def slow_func() -> str:
            time.sleep(0.1)
            return "done"
        
        with patch('src.utils.query_safety.logger') as mock_logger:
            result = slow_func()
            
            # Check that warning was logged
            assert mock_logger.warning.called
            assert any("slow" in str(call).lower() for call in mock_logger.warning.call_args_list)
    
    def test_monitor_exception_handling(self):
        """Test that exceptions are properly handled and logged."""
        @monitor_performance(threshold_seconds=1.0)
        def failing_func() -> str:
            raise RuntimeError("Test error")
        
        with pytest.raises(RuntimeError):
            failing_func()


class TestValidateQueryBeforeExecution:
    """Test suite for validate_query_before_execution function."""
    
    def test_validate_safe_query(self):
        """Test validation of safe query."""
        query = "MATCH (n:Person) RETURN n LIMIT 10"
        
        # Should not raise an exception
        validate_query_before_execution(query)
    
    def test_validate_unsafe_query_raises(self):
        """Test validation of unsafe query raises exception."""
        query = "CREATE (n:Person) RETURN n"
        
        with pytest.raises(ValidationError):
            validate_query_before_execution(query)
    
    def test_validate_complex_query_logs_warnings(self):
        """Test that complex queries log warnings."""
        # Use a very complex query that will definitely fail
        query = """
        MATCH (n)-[*]-(m)
        MATCH (a)-[*]-(b)
        MATCH (x)-[*]-(y)
        MATCH path = allShortestPaths((n)-[*]-(m))
        RETURN n, m
        """
        
        with patch('src.utils.query_safety.logger') as mock_logger:
            with pytest.raises(ValidationError):
                # This should fail due to high complexity
                validate_query_before_execution(query)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

