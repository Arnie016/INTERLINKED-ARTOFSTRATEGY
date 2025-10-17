"""
Integration tests for FastAPI proxy with Strands agents.

Tests the full request/response flow including:
- Session management with Strands session managers
- Agent invocation with real/mocked agents
- Request/response transformation
- Error handling
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from proxy.models import ProxyConfig, ChatMessage, ChatResponse
from proxy.session import SessionManager, initialize_session_manager
from proxy.client import StrandsAgentClient, initialize_agent_client


@pytest.fixture
def temp_session_dir():
    """Create temporary directory for file-based sessions."""
    temp_dir = tempfile.mkdtemp(prefix="test_sessions_")
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def proxy_config(temp_session_dir):
    """Create test proxy configuration."""
    return ProxyConfig(
        session_backend="file",
        session_storage_dir=temp_session_dir,
        use_agentcore_memory=False,
        aws_region="us-west-2",
        agent_timeout_seconds=30,
        enable_error_details=True
    )


@pytest.fixture
def session_manager(proxy_config):
    """Create and initialize session manager for tests."""
    initialize_session_manager(proxy_config)
    from proxy.session import get_session_manager
    return get_session_manager()


@pytest.fixture
def agent_client(proxy_config):
    """Create and initialize agent client for tests."""
    initialize_agent_client(proxy_config)
    from proxy.client import get_agent_client
    return get_agent_client()


@pytest.fixture
def test_client(proxy_config, session_manager, agent_client):
    """Create FastAPI test client."""
    from proxy import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router.router)
    
    return TestClient(app)


@pytest.fixture
def mock_strands_agent():
    """Mock Strands Agent that returns predictable responses."""
    mock_agent = Mock()
    
    def agent_call(prompt: str):
        """Mock agent callable."""
        # Return different responses based on prompt content
        if "error" in prompt.lower():
            raise Exception("Mock agent error")
        elif "timeout" in prompt.lower():
            raise TimeoutError("Mock timeout")
        else:
            return f"Mock agent response to: {prompt[:50]}..."
    
    mock_agent.side_effect = agent_call
    return mock_agent


class TestSessionManagement:
    """Test session management integration."""
    
    @pytest.mark.unit
    def test_session_id_generation(self, session_manager):
        """Test session ID generation."""
        from fastapi import Request
        
        # Create mock request without session
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.cookies = {}
        
        session_id = session_manager.get_or_create_session_id(mock_request)
        
        assert session_id is not None
        assert session_id.startswith("sess-")
        assert len(session_id) > 10
    
    @pytest.mark.unit
    def test_session_id_extraction_from_header(self, session_manager):
        """Test extracting session ID from request header."""
        from fastapi import Request
        
        expected_session_id = "sess-test-header"
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Session-ID": expected_session_id}
        mock_request.cookies = {}
        
        session_id = session_manager.get_or_create_session_id(mock_request)
        
        assert session_id == expected_session_id
    
    @pytest.mark.unit
    def test_session_id_extraction_from_cookie(self, session_manager):
        """Test extracting session ID from cookie."""
        from fastapi import Request
        
        expected_session_id = "sess-test-cookie"
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.cookies = {"session_id": expected_session_id}
        
        session_id = session_manager.get_or_create_session_id(mock_request)
        
        assert session_id == expected_session_id
    
    @pytest.mark.unit
    def test_file_session_manager_creation(self, session_manager, temp_session_dir):
        """Test creation of file-based Strands session manager."""
        session_id = "test-file-session"
        
        strands_manager = session_manager.create_strands_session_manager(session_id)
        
        assert strands_manager is not None
        assert strands_manager.session_id == session_id
        
        # Verify session directory was created
        session_file = Path(temp_session_dir) / f"{session_id}.json"
        assert session_file.parent.exists()
    
    @pytest.mark.unit
    def test_session_manager_caching(self, session_manager):
        """Test that session managers are cached."""
        session_id = "test-cache-session"
        
        # Create first manager
        manager1 = session_manager.create_strands_session_manager(session_id)
        
        # Get same session again
        manager2 = session_manager.create_strands_session_manager(session_id)
        
        # Should be the same instance
        assert manager1 is manager2
        assert session_manager.get_active_sessions_count() == 1
    
    @pytest.mark.unit
    def test_clear_session_cache(self, session_manager):
        """Test clearing session cache."""
        # Create multiple sessions
        session_manager.create_strands_session_manager("session-1")
        session_manager.create_strands_session_manager("session-2")
        
        assert session_manager.get_active_sessions_count() == 2
        
        # Clear specific session
        session_manager.clear_session_cache("session-1")
        assert session_manager.get_active_sessions_count() == 1
        
        # Clear all
        session_manager.clear_session_cache()
        assert session_manager.get_active_sessions_count() == 0


class TestAgentInvocation:
    """Test agent invocation integration."""
    
    @pytest.mark.unit
    @patch('proxy.client.Agent')
    def test_agent_creation(self, mock_agent_class, agent_client, session_manager):
        """Test agent creation with session manager."""
        session_id = "test-agent-session"
        strands_manager = session_manager.create_strands_session_manager(session_id)
        
        # Mock the agent creation
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        agent = agent_client.create_agent(
            session_manager=strands_manager,
            use_agentcore=False
        )
        
        assert agent is not None
    
    @pytest.mark.unit
    def test_agent_caching(self, agent_client, session_manager):
        """Test that agents are cached per session."""
        session_id = "test-agent-cache"
        strands_manager = session_manager.create_strands_session_manager(session_id)
        
        with patch('proxy.client.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Create first agent
            agent1 = agent_client._get_or_create_agent(session_id, strands_manager)
            
            # Get same agent
            agent2 = agent_client._get_or_create_agent(session_id, strands_manager)
            
            # Should be cached
            assert agent1 is agent2
            assert agent_client.get_cached_agents_count() == 1
    
    @pytest.mark.unit
    def test_clear_agent_cache(self, agent_client, session_manager):
        """Test clearing agent cache."""
        with patch('proxy.client.Agent'):
            # Create multiple agents
            agent_client._get_or_create_agent(
                "session-1",
                session_manager.create_strands_session_manager("session-1")
            )
            agent_client._get_or_create_agent(
                "session-2",
                session_manager.create_strands_session_manager("session-2")
            )
            
            assert agent_client.get_cached_agents_count() == 2
            
            # Clear specific agent
            agent_client.clear_agent_cache("session-1")
            assert agent_client.get_cached_agents_count() == 1
            
            # Clear all
            agent_client.clear_agent_cache()
            assert agent_client.get_cached_agents_count() == 0


class TestEndToEndFlow:
    """Test complete end-to-end request/response flow."""
    
    @pytest.mark.integration
    @patch('proxy.client.StrandsAgentClient._get_or_create_agent')
    def test_chat_endpoint_success(
        self,
        mock_get_agent,
        test_client,
        mock_strands_agent
    ):
        """Test successful chat request through the proxy."""
        # Setup mock agent
        mock_get_agent.return_value = mock_strands_agent
        
        # Make chat request
        response = test_client.post(
            "/api/chat",
            json={
                "message": "Who are the key people?",
                "agent_type": "graph"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "response" in data
        assert data["agent_type"] == "graph"
        assert "session_id" in data
        assert "timestamp" in data
        
        # Verify session cookie was set
        assert "session_id" in response.cookies
    
    @pytest.mark.integration
    @patch('proxy.client.StrandsAgentClient._get_or_create_agent')
    def test_chat_endpoint_maintains_session(
        self,
        mock_get_agent,
        test_client,
        mock_strands_agent
    ):
        """Test that session is maintained across multiple requests."""
        mock_get_agent.return_value = mock_strands_agent
        
        # First request
        response1 = test_client.post(
            "/api/chat",
            json={"message": "First message", "agent_type": "graph"}
        )
        
        session_id_1 = response1.json()["session_id"]
        cookie_1 = response1.cookies["session_id"]
        
        # Second request with session cookie
        response2 = test_client.post(
            "/api/chat",
            json={"message": "Second message", "agent_type": "graph"},
            cookies={"session_id": cookie_1}
        )
        
        session_id_2 = response2.json()["session_id"]
        
        # Should maintain same session
        assert session_id_1 == session_id_2
    
    @pytest.mark.integration
    @patch('proxy.client.StrandsAgentClient._get_or_create_agent')
    def test_chat_endpoint_with_session_header(
        self,
        mock_get_agent,
        test_client,
        mock_strands_agent
    ):
        """Test chat request with X-Session-ID header."""
        mock_get_agent.return_value = mock_strands_agent
        
        custom_session_id = "custom-session-123"
        
        response = test_client.post(
            "/api/chat",
            json={"message": "Test message", "agent_type": "graph"},
            headers={"X-Session-ID": custom_session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == custom_session_id
    
    @pytest.mark.integration
    def test_chat_endpoint_validation_empty_message(self, test_client):
        """Test validation rejects empty messages."""
        response = test_client.post(
            "/api/chat",
            json={"message": "", "agent_type": "graph"}
        )
        
        assert response.status_code == 400
    
    @pytest.mark.integration
    def test_chat_endpoint_validation_too_long(self, test_client):
        """Test validation rejects messages that are too long."""
        long_message = "x" * 50000  # Exceeds 10000 char limit
        
        response = test_client.post(
            "/api/chat",
            json={"message": long_message, "agent_type": "graph"}
        )
        
        assert response.status_code == 400
    
    @pytest.mark.integration
    @patch('proxy.client.StrandsAgentClient._get_or_create_agent')
    def test_chat_endpoint_agent_timeout(
        self,
        mock_get_agent,
        test_client
    ):
        """Test handling of agent timeout."""
        # Mock agent that raises TimeoutError
        mock_agent = Mock()
        mock_agent.side_effect = TimeoutError("Timeout")
        mock_get_agent.return_value = mock_agent
        
        response = test_client.post(
            "/api/chat",
            json={"message": "Test timeout", "agent_type": "graph"}
        )
        
        # Should return 200 with error in response (not HTTP error)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "took too long" in data["response"].lower()
    
    @pytest.mark.integration
    @patch('proxy.client.StrandsAgentClient._get_or_create_agent')
    def test_chat_endpoint_agent_error(
        self,
        mock_get_agent,
        test_client
    ):
        """Test handling of agent invocation error."""
        # Mock agent that raises exception
        mock_agent = Mock()
        mock_agent.side_effect = Exception("Agent error")
        mock_get_agent.return_value = mock_agent
        
        response = test_client.post(
            "/api/chat",
            json={"message": "Test error", "agent_type": "graph"}
        )
        
        # Should return 200 with error in response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data["response"].lower()


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @pytest.mark.unit
    def test_health_endpoint(self, test_client):
        """Test health check returns status."""
        response = test_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "message" in data
        assert "components" in data
        
        # Should have session_manager and strands_agent components
        components = data["components"]
        assert "session_manager" in components
        assert "strands_agent" in components


class TestProxyConfigEndpoint:
    """Test proxy configuration endpoint."""
    
    @pytest.mark.unit
    def test_config_endpoint(self, test_client):
        """Test configuration endpoint returns settings."""
        response = test_client.get("/api/proxy/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_backend" in data
        assert "use_agentcore_memory" in data
        assert "aws_region" in data
        assert "active_sessions" in data
        assert "cached_agents" in data


class TestCacheClearEndpoint:
    """Test cache clearing endpoint."""
    
    @pytest.mark.unit
    @patch('proxy.client.StrandsAgentClient._get_or_create_agent')
    def test_clear_all_cache(self, mock_get_agent, test_client, session_manager):
        """Test clearing all cached sessions and agents."""
        # Create some cached sessions/agents
        with patch('proxy.client.Agent'):
            session_manager.create_strands_session_manager("session-1")
            session_manager.create_strands_session_manager("session-2")
        
        # Clear cache
        response = test_client.post("/api/proxy/clear-cache")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "sessions_cleared" in data
        assert "agents_cleared" in data
    
    @pytest.mark.unit
    @patch('proxy.client.StrandsAgentClient._get_or_create_agent')
    def test_clear_specific_session_cache(
        self,
        mock_get_agent,
        test_client,
        session_manager
    ):
        """Test clearing cache for specific session."""
        session_id = "session-to-clear"
        
        # Create cached session
        with patch('proxy.client.Agent'):
            session_manager.create_strands_session_manager(session_id)
        
        # Clear specific session
        response = test_client.post(
            f"/api/proxy/clear-cache?session_id={session_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == session_id


class TestRequestResponseTransformation:
    """Test request and response transformation."""
    
    @pytest.mark.unit
    def test_request_transformation(self):
        """Test transformation from frontend format to Strands format."""
        from proxy.transformers import RequestTransformer
        from proxy.models import ChatMessage
        
        chat_message = ChatMessage(
            message="Who are the key people?",
            agent_type="graph"
        )
        session_id = "test-session"
        
        strands_request = RequestTransformer.transform(chat_message, session_id)
        
        assert strands_request.prompt == "Who are the key people?"
        assert strands_request.session_id == session_id
        assert strands_request.metadata["original_agent_type"] == "graph"
    
    @pytest.mark.unit
    def test_response_transformation(self):
        """Test transformation from Strands format to frontend format."""
        from proxy.transformers import ResponseTransformer
        from proxy.models import StrandsAgentResponse
        
        strands_response = StrandsAgentResponse(
            result="Found 15 people...",
            session_id="test-session",
            agent_used="orchestrator",
            metadata={"execution_time_ms": 1234.5}
        )
        
        frontend_response = ResponseTransformer.transform(
            strands_response,
            original_agent_type="graph"
        )
        
        assert frontend_response.success is True
        assert frontend_response.response == "Found 15 people..."
        assert frontend_response.agent_type == "graph"
        assert frontend_response.session_id == "test-session"
        assert frontend_response.timestamp is not None
    
    @pytest.mark.unit
    def test_error_response_transformation(self):
        """Test transformation of error responses."""
        from proxy.transformers import ResponseTransformer
        
        error_response = ResponseTransformer.transform_error(
            error_message="Something went wrong",
            session_id="test-session",
            agent_type="graph"
        )
        
        assert error_response.success is False
        assert error_response.response == "Something went wrong"
        assert error_response.agent_type == "graph"
        assert error_response.session_id == "test-session"
    
    @pytest.mark.unit
    def test_message_sanitization(self):
        """Test message sanitization."""
        from proxy.transformers import sanitize_message
        
        # Test HTML stripping
        dirty_message = "<script>alert('xss')</script>Hello"
        clean = sanitize_message(dirty_message)
        assert "<script>" not in clean
        assert "Hello" in clean
        
        # Test whitespace normalization
        message_with_spaces = "Hello    world  \n\n  test"
        clean = sanitize_message(message_with_spaces)
        assert "  " not in clean  # No double spaces
        assert clean.strip() == clean  # No leading/trailing whitespace


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
