"""
Pytest configuration and shared fixtures for proxy tests.
"""

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add paths for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

strands_agents_path = backend_path.parent / "strands_agents" / "src"
sys.path.insert(0, str(strands_agents_path))

# Set test environment variables
os.environ["PROXY_SESSION_BACKEND"] = "file"
os.environ["PROXY_USE_AGENTCORE_MEMORY"] = "false"
os.environ["PROXY_ENABLE_ERROR_DETAILS"] = "true"
os.environ["AWS_REGION"] = "us-west-2"
os.environ["NEO4J_URI"] = os.getenv("NEO4J_URI", "bolt://localhost:7687")
os.environ["NEO4J_USERNAME"] = os.getenv("NEO4J_USERNAME", "neo4j")
os.environ["NEO4J_PASSWORD"] = os.getenv("NEO4J_PASSWORD", "password")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture
def test_env():
    """Test environment configuration."""
    return {
        "session_backend": "file",
        "use_agentcore_memory": False,
        "aws_region": "us-west-2",
    }


@pytest.fixture
def mock_session_id():
    """Mock session ID for testing."""
    return "sess-test-12345"


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "message": "Who are the key people in the organization?",
        "agent_type": "graph"
    }


@pytest.fixture
def sample_chat_response():
    """Sample expected chat response."""
    return {
        "success": True,
        "response": "Found 15 people in the organization...",
        "agent_type": "graph",
        "timestamp": "2025-10-17T10:30:00Z",
        "session_id": "sess-test-12345"
    }

