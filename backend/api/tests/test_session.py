"""
Unit tests for session management module.

Tests session ID generation, extraction, and Strands session manager creation.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request, Response

from proxy.models import ProxyConfig
from proxy.session import SessionManager


@pytest.fixture
def temp_session_dir():
    """Create temporary directory for file-based sessions."""
    temp_dir = tempfile.mkdtemp(prefix="test_sessions_")
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def file_config(temp_session_dir):
    """Create config for file-based session management."""
    return ProxyConfig(
        session_backend="file",
        session_storage_dir=temp_session_dir,
        use_agentcore_memory=False,
        aws_region="us-west-2"
    )


@pytest.fixture
def s3_config():
    """Create config for S3-based session management."""
    return ProxyConfig(
        session_backend="s3",
        session_s3_bucket="test-bucket",
        session_s3_prefix="sessions/",
        use_agentcore_memory=False,
        aws_region="us-west-2"
    )


@pytest.fixture
def session_manager(file_config):
    """Create session manager with file backend."""
    return SessionManager(file_config)


class TestSessionIDGeneration:
    """Test session ID generation."""
    
    def test_generate_session_id_default_prefix(self, session_manager):
        """Test generating session ID with default prefix."""
        session_id = session_manager.generate_session_id()
        
        assert session_id is not None
        assert session_id.startswith("sess-")
        assert len(session_id) > 10  # prefix + UUID portion
    
    def test_generate_session_id_custom_prefix(self, session_manager):
        """Test generating session ID with custom prefix."""
        session_id = session_manager.generate_session_id(prefix="custom")
        
        assert session_id.startswith("custom-")
    
    def test_generate_unique_session_ids(self, session_manager):
        """Test that generated session IDs are unique."""
        ids = {session_manager.generate_session_id() for _ in range(100)}
        
        # All should be unique
        assert len(ids) == 100


class TestSessionIDExtraction:
    """Test extracting session ID from requests."""
    
    def test_extract_from_header(self, session_manager):
        """Test extracting session ID from X-Session-ID header."""
        expected_id = "sess-from-header"
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Session-ID": expected_id}
        mock_request.cookies = {}
        
        session_id = session_manager.extract_session_id(mock_request)
        
        assert session_id == expected_id
    
    def test_extract_from_cookie(self, session_manager):
        """Test extracting session ID from cookie."""
        expected_id = "sess-from-cookie"
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.cookies = {"session_id": expected_id}
        
        session_id = session_manager.extract_session_id(mock_request)
        
        assert session_id == expected_id
    
    def test_header_takes_precedence_over_cookie(self, session_manager):
        """Test that header takes precedence over cookie."""
        header_id = "sess-from-header"
        cookie_id = "sess-from-cookie"
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Session-ID": header_id}
        mock_request.cookies = {"session_id": cookie_id}
        
        session_id = session_manager.extract_session_id(mock_request)
        
        assert session_id == header_id
    
    def test_extract_returns_none_when_not_found(self, session_manager):
        """Test that None is returned when session ID not found."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.cookies = {}
        
        session_id = session_manager.extract_session_id(mock_request)
        
        assert session_id is None


class TestGetOrCreateSessionID:
    """Test getting existing or creating new session ID."""
    
    def test_returns_existing_session_id(self, session_manager):
        """Test returning existing session ID from request."""
        existing_id = "sess-existing"
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Session-ID": existing_id}
        mock_request.cookies = {}
        
        session_id = session_manager.get_or_create_session_id(mock_request)
        
        assert session_id == existing_id
    
    def test_creates_new_session_id_when_not_found(self, session_manager):
        """Test creating new session ID when not in request."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.cookies = {}
        
        session_id = session_manager.get_or_create_session_id(mock_request)
        
        assert session_id is not None
        assert session_id.startswith("sess-")


class TestSessionCookie:
    """Test session cookie setting."""
    
    def test_set_session_cookie(self, session_manager):
        """Test setting session cookie in response."""
        session_id = "sess-test-cookie"
        mock_response = Mock(spec=Response)
        
        session_manager.set_session_cookie(mock_response, session_id)
        
        mock_response.set_cookie.assert_called_once()
        call_args = mock_response.set_cookie.call_args
        
        assert call_args[1]["key"] == "session_id"
        assert call_args[1]["value"] == session_id
        assert call_args[1]["httponly"] is True
    
    def test_set_session_cookie_custom_max_age(self, session_manager):
        """Test setting cookie with custom max age."""
        session_id = "sess-test"
        mock_response = Mock(spec=Response)
        custom_max_age = 3600  # 1 hour
        
        session_manager.set_session_cookie(
            mock_response,
            session_id,
            max_age=custom_max_age
        )
        
        call_args = mock_response.set_cookie.call_args
        assert call_args[1]["max_age"] == custom_max_age


class TestFileSessionManager:
    """Test file-based Strands session manager creation."""
    
    def test_create_file_session_manager(self, session_manager, temp_session_dir):
        """Test creating file-based session manager."""
        session_id = "test-file-session"
        
        strands_manager = session_manager.create_strands_session_manager(session_id)
        
        assert strands_manager is not None
        assert strands_manager.session_id == session_id
        
        # Verify it's using the correct storage directory
        assert temp_session_dir in str(strands_manager.storage_dir)
    
    def test_file_session_manager_creates_directory(
        self,
        session_manager,
        temp_session_dir
    ):
        """Test that session manager creates storage directory."""
        session_id = "test-create-dir"
        
        # Remove directory if it exists
        if os.path.exists(temp_session_dir):
            shutil.rmtree(temp_session_dir)
        
        strands_manager = session_manager.create_strands_session_manager(session_id)
        
        # Directory should be created
        assert os.path.exists(temp_session_dir)
    
    def test_file_session_manager_caching(self, session_manager):
        """Test that session managers are cached."""
        session_id = "test-cache"
        
        # Create first time
        manager1 = session_manager.create_strands_session_manager(session_id)
        
        # Get second time (should be cached)
        manager2 = session_manager.create_strands_session_manager(session_id)
        
        # Should be the same instance
        assert manager1 is manager2


class TestS3SessionManager:
    """Test S3-based Strands session manager creation."""
    
    @patch('proxy.session.boto3.Session')
    @patch('proxy.session.S3SessionManager')
    def test_create_s3_session_manager(
        self,
        mock_s3_manager_class,
        mock_boto_session,
        s3_config
    ):
        """Test creating S3-based session manager."""
        session_manager = SessionManager(s3_config)
        session_id = "test-s3-session"
        
        # Mock the S3 session manager
        mock_manager = Mock()
        mock_s3_manager_class.return_value = mock_manager
        
        strands_manager = session_manager.create_strands_session_manager(session_id)
        
        # Verify S3SessionManager was called with correct params
        mock_s3_manager_class.assert_called_once_with(
            session_id=session_id,
            bucket="test-bucket",
            prefix="sessions/",
            boto_session=mock_boto_session.return_value
        )
        
        assert strands_manager is mock_manager
    
    def test_s3_session_manager_requires_bucket(self):
        """Test that S3 backend requires bucket configuration."""
        config = ProxyConfig(
            session_backend="s3",
            session_s3_bucket=None,  # Missing bucket
            aws_region="us-west-2"
        )
        
        session_manager = SessionManager(config)
        
        with pytest.raises(ValueError, match="requires session_s3_bucket"):
            session_manager.create_strands_session_manager("test-session")


class TestInvalidSessionBackend:
    """Test handling of invalid session backend configuration."""
    
    def test_invalid_backend_raises_error(self):
        """Test that invalid backend configuration raises error."""
        config = ProxyConfig(
            session_backend="invalid",
            aws_region="us-west-2"
        )
        
        session_manager = SessionManager(config)
        
        with pytest.raises(ValueError, match="Invalid session backend"):
            session_manager.create_strands_session_manager("test-session")


class TestSessionCacheManagement:
    """Test session manager cache operations."""
    
    def test_get_active_sessions_count(self, session_manager):
        """Test getting count of active sessions."""
        assert session_manager.get_active_sessions_count() == 0
        
        # Create some sessions
        session_manager.create_strands_session_manager("session-1")
        session_manager.create_strands_session_manager("session-2")
        
        assert session_manager.get_active_sessions_count() == 2
    
    def test_clear_specific_session(self, session_manager):
        """Test clearing specific session from cache."""
        # Create sessions
        session_manager.create_strands_session_manager("session-1")
        session_manager.create_strands_session_manager("session-2")
        session_manager.create_strands_session_manager("session-3")
        
        assert session_manager.get_active_sessions_count() == 3
        
        # Clear one session
        session_manager.clear_session_cache("session-2")
        
        assert session_manager.get_active_sessions_count() == 2
        
        # Verify the specific session was cleared (next call creates new)
        manager = session_manager.create_strands_session_manager("session-2")
        assert manager is not None
    
    def test_clear_all_sessions(self, session_manager):
        """Test clearing all sessions from cache."""
        # Create multiple sessions
        for i in range(5):
            session_manager.create_strands_session_manager(f"session-{i}")
        
        assert session_manager.get_active_sessions_count() == 5
        
        # Clear all
        session_manager.clear_session_cache()
        
        assert session_manager.get_active_sessions_count() == 0
    
    def test_clear_nonexistent_session(self, session_manager):
        """Test clearing a session that doesn't exist (should not error)."""
        session_manager.create_strands_session_manager("session-1")
        
        # Try to clear nonexistent session (should not raise error)
        session_manager.clear_session_cache("nonexistent-session")
        
        # Existing session should still be there
        assert session_manager.get_active_sessions_count() == 1


class TestGlobalSessionManager:
    """Test global session manager initialization."""
    
    def test_initialize_global_session_manager(self, file_config):
        """Test initializing global session manager."""
        from proxy.session import initialize_session_manager, get_session_manager
        
        initialize_session_manager(file_config)
        
        manager = get_session_manager()
        assert manager is not None
        assert isinstance(manager, SessionManager)
    
    def test_get_session_manager_before_init_raises_error(self):
        """Test that getting manager before init raises error."""
        from proxy import session
        
        # Reset global
        session._session_manager = None
        
        with pytest.raises(RuntimeError, match="not initialized"):
            session.get_session_manager()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
