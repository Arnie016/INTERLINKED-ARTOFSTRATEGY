"""
Unit tests for request/response transformation module.

Tests transformation between frontend format and Strands agent format.
"""

import pytest
from datetime import datetime

from proxy.models import (
    ChatMessage,
    ChatResponse,
    StrandsAgentRequest,
    StrandsAgentResponse
)
from proxy.transformers import (
    RequestTransformer,
    ResponseTransformer,
    validate_chat_message,
    sanitize_message
)


class TestRequestTransformation:
    """Test transformation from frontend format to Strands format."""
    
    def test_basic_request_transformation(self):
        """Test basic request transformation."""
        chat_message = ChatMessage(
            message="Who are the key people?",
            agent_type="graph"
        )
        session_id = "test-session-123"
        
        strands_request = RequestTransformer.transform(chat_message, session_id)
        
        assert isinstance(strands_request, StrandsAgentRequest)
        assert strands_request.prompt == "Who are the key people?"
        assert strands_request.session_id == session_id
        assert strands_request.metadata["original_agent_type"] == "graph"
    
    def test_request_transformation_preserves_message(self):
        """Test that message content is preserved exactly."""
        original_message = "This is a test message with special chars: !@#$%"
        chat_message = ChatMessage(
            message=original_message,
            agent_type="analyzer"
        )
        
        strands_request = RequestTransformer.transform(chat_message, "sess-123")
        
        assert strands_request.prompt == original_message
    
    def test_request_transformation_different_agent_types(self):
        """Test transformation with different agent types."""
        agent_types = ["graph", "analyzer", "extractor", "admin", "orchestrator"]
        
        for agent_type in agent_types:
            chat_message = ChatMessage(
                message="Test message",
                agent_type=agent_type
            )
            
            strands_request = RequestTransformer.transform(chat_message, "sess-123")
            
            assert strands_request.metadata["original_agent_type"] == agent_type


class TestResponseTransformation:
    """Test transformation from Strands format to frontend format."""
    
    def test_basic_response_transformation(self):
        """Test basic response transformation."""
        strands_response = StrandsAgentResponse(
            result="Found 15 people in the organization.",
            session_id="test-session-123",
            agent_used="graph_agent",
            metadata={"execution_time_ms": 1234.5}
        )
        
        chat_response = ResponseTransformer.transform(
            strands_response,
            original_agent_type="graph"
        )
        
        assert isinstance(chat_response, ChatResponse)
        assert chat_response.success is True
        assert chat_response.response == "Found 15 people in the organization."
        assert chat_response.agent_type == "graph"
        assert chat_response.session_id == "test-session-123"
        assert chat_response.timestamp is not None
    
    def test_response_transformation_preserves_content(self):
        """Test that response content is preserved exactly."""
        original_result = "This is a detailed response\nwith multiple lines\nand formatting."
        
        strands_response = StrandsAgentResponse(
            result=original_result,
            session_id="sess-123",
            agent_used="orchestrator",
            metadata={}
        )
        
        chat_response = ResponseTransformer.transform(
            strands_response,
            original_agent_type="graph"
        )
        
        assert chat_response.response == original_result
    
    def test_response_transformation_includes_timestamp(self):
        """Test that transformed response includes timestamp."""
        strands_response = StrandsAgentResponse(
            result="Test response",
            session_id="sess-123",
            agent_used="graph_agent",
            metadata={}
        )
        
        chat_response = ResponseTransformer.transform(
            strands_response,
            original_agent_type="graph"
        )
        
        assert chat_response.timestamp is not None
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(chat_response.timestamp.replace('Z', '+00:00'))
    
    def test_response_transformation_agent_type_mapping(self):
        """Test that agent type is properly mapped."""
        strands_response = StrandsAgentResponse(
            result="Test",
            session_id="sess-123",
            agent_used="orchestrator_agent",
            metadata={}
        )
        
        # Original agent type should be preserved
        chat_response = ResponseTransformer.transform(
            strands_response,
            original_agent_type="analyzer"
        )
        
        assert chat_response.agent_type == "analyzer"


class TestErrorResponseTransformation:
    """Test transformation of error responses."""
    
    def test_error_response_basic(self):
        """Test basic error response transformation."""
        error_response = ResponseTransformer.transform_error(
            error_message="Something went wrong",
            session_id="sess-123",
            agent_type="graph"
        )
        
        assert isinstance(error_response, ChatResponse)
        assert error_response.success is False
        assert error_response.response == "Something went wrong"
        assert error_response.agent_type == "graph"
        assert error_response.session_id == "sess-123"
        assert error_response.timestamp is not None
    
    def test_error_response_with_none_session(self):
        """Test error response with None session ID."""
        error_response = ResponseTransformer.transform_error(
            error_message="Error occurred",
            session_id=None,
            agent_type="graph"
        )
        
        assert error_response.success is False
        assert error_response.session_id is None
    
    def test_error_response_preserves_error_message(self):
        """Test that error message is preserved exactly."""
        error_msg = "Detailed error: timeout after 30 seconds"
        
        error_response = ResponseTransformer.transform_error(
            error_message=error_msg,
            session_id="sess-123",
            agent_type="graph"
        )
        
        assert error_response.response == error_msg


class TestMessageValidation:
    """Test message validation logic."""
    
    def test_valid_message(self):
        """Test validation of valid message."""
        chat_message = ChatMessage(
            message="This is a valid message",
            agent_type="graph"
        )
        
        is_valid, error_msg = validate_chat_message(chat_message)
        
        assert is_valid is True
        assert error_msg is None
    
    def test_empty_message_invalid(self):
        """Test that empty message is invalid."""
        chat_message = ChatMessage(
            message="",
            agent_type="graph"
        )
        
        is_valid, error_msg = validate_chat_message(chat_message)
        
        assert is_valid is False
        assert "empty" in error_msg.lower()
    
    def test_whitespace_only_message_invalid(self):
        """Test that whitespace-only message is invalid."""
        chat_message = ChatMessage(
            message="   \n\t  ",
            agent_type="graph"
        )
        
        is_valid, error_msg = validate_chat_message(chat_message)
        
        assert is_valid is False
        assert "empty" in error_msg.lower()
    
    def test_too_long_message_invalid(self):
        """Test that message exceeding max length is invalid."""
        # Create message longer than 10000 characters
        long_message = "x" * 10001
        
        chat_message = ChatMessage(
            message=long_message,
            agent_type="graph"
        )
        
        is_valid, error_msg = validate_chat_message(chat_message)
        
        assert is_valid is False
        assert "long" in error_msg.lower() or "exceeds" in error_msg.lower()
    
    def test_max_length_message_valid(self):
        """Test that message at exactly max length is valid."""
        max_length_message = "x" * 10000
        
        chat_message = ChatMessage(
            message=max_length_message,
            agent_type="graph"
        )
        
        is_valid, error_msg = validate_chat_message(chat_message)
        
        assert is_valid is True
    
    def test_valid_message_with_special_characters(self):
        """Test validation accepts special characters."""
        chat_message = ChatMessage(
            message="Message with special chars: !@#$%^&*()",
            agent_type="graph"
        )
        
        is_valid, error_msg = validate_chat_message(chat_message)
        
        assert is_valid is True
    
    def test_valid_message_with_unicode(self):
        """Test validation accepts unicode characters."""
        chat_message = ChatMessage(
            message="Message with unicode: 你好 مرحبا שלום",
            agent_type="graph"
        )
        
        is_valid, error_msg = validate_chat_message(chat_message)
        
        assert is_valid is True


class TestMessageSanitization:
    """Test message sanitization logic."""
    
    def test_sanitize_strips_html(self):
        """Test that HTML tags are stripped."""
        dirty_message = "<script>alert('xss')</script>Hello World"
        
        clean = sanitize_message(dirty_message)
        
        assert "<script>" not in clean
        assert "</script>" not in clean
        assert "Hello World" in clean
    
    def test_sanitize_normalizes_whitespace(self):
        """Test that whitespace is normalized."""
        message_with_spaces = "Hello    world  \n\n  test"
        
        clean = sanitize_message(message_with_spaces)
        
        # Should not have multiple spaces
        assert "  " not in clean
        # Should not have leading/trailing whitespace
        assert clean == clean.strip()
    
    def test_sanitize_removes_leading_trailing_whitespace(self):
        """Test that leading and trailing whitespace is removed."""
        message = "   Hello World   "
        
        clean = sanitize_message(message)
        
        assert clean == "Hello World"
    
    def test_sanitize_preserves_valid_content(self):
        """Test that valid content is preserved."""
        message = "This is a normal message with punctuation!"
        
        clean = sanitize_message(message)
        
        assert clean == message
    
    def test_sanitize_handles_empty_string(self):
        """Test sanitization of empty string."""
        clean = sanitize_message("")
        
        assert clean == ""
    
    def test_sanitize_handles_only_whitespace(self):
        """Test sanitization of whitespace-only string."""
        clean = sanitize_message("   \n\t  ")
        
        assert clean == ""
    
    def test_sanitize_preserves_newlines_in_content(self):
        """Test that meaningful newlines are preserved."""
        message = "Line 1\nLine 2\nLine 3"
        
        clean = sanitize_message(message)
        
        # Should preserve line structure
        assert "Line 1" in clean
        assert "Line 2" in clean
        assert "Line 3" in clean
    
    def test_sanitize_removes_dangerous_html(self):
        """Test removal of various dangerous HTML elements."""
        dangerous_inputs = [
            "<img src=x onerror='alert(1)'>",
            "<iframe src='http://evil.com'>",
            "<object data='http://evil.com'>",
            "<embed src='http://evil.com'>",
        ]
        
        for dangerous in dangerous_inputs:
            clean = sanitize_message(dangerous)
            
            # Should not contain any tags
            assert "<" not in clean
            assert ">" not in clean
    
    def test_sanitize_handles_unicode(self):
        """Test that unicode characters are preserved."""
        message = "Hello 你好 مرحبا שלום"
        
        clean = sanitize_message(message)
        
        assert "你好" in clean
        assert "مرحبا" in clean
        assert "שלום" in clean


class TestEdgeCases:
    """Test edge cases in transformation."""
    
    def test_transformation_with_very_long_response(self):
        """Test transformation handles very long responses."""
        long_result = "x" * 50000  # 50k characters
        
        strands_response = StrandsAgentResponse(
            result=long_result,
            session_id="sess-123",
            agent_used="graph_agent",
            metadata={}
        )
        
        chat_response = ResponseTransformer.transform(
            strands_response,
            original_agent_type="graph"
        )
        
        assert chat_response.response == long_result
    
    def test_transformation_with_special_session_ids(self):
        """Test transformation handles special session ID formats."""
        special_session_ids = [
            "sess-with-dashes-123",
            "sess_with_underscores_456",
            "SESS-UPPERCASE-789",
            "sess.with.dots.012",
        ]
        
        for session_id in special_session_ids:
            strands_response = StrandsAgentResponse(
                result="Test",
                session_id=session_id,
                agent_used="orchestrator",
                metadata={}
            )
            
            chat_response = ResponseTransformer.transform(
                strands_response,
                original_agent_type="graph"
            )
            
            assert chat_response.session_id == session_id
    
    def test_transformation_with_empty_metadata(self):
        """Test transformation with empty metadata."""
        strands_response = StrandsAgentResponse(
            result="Test response",
            session_id="sess-123",
            agent_used="graph_agent",
            metadata={}
        )
        
        chat_response = ResponseTransformer.transform(
            strands_response,
            original_agent_type="graph"
        )
        
        assert chat_response is not None
        assert chat_response.success is True
    
    def test_request_transformation_with_multiline_message(self):
        """Test request transformation preserves multiline messages."""
        multiline_message = """This is line 1
This is line 2
This is line 3"""
        
        chat_message = ChatMessage(
            message=multiline_message,
            agent_type="graph"
        )
        
        strands_request = RequestTransformer.transform(chat_message, "sess-123")
        
        assert strands_request.prompt == multiline_message
        assert "\n" in strands_request.prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
