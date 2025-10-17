# FastAPI Proxy Testing Guide

Comprehensive guide for testing the FastAPI proxy implementation that maintains backward compatibility while integrating with Strands Agents.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing New Tests](#writing-new-tests)
- [Troubleshooting](#troubleshooting)

## Overview

The test suite validates:
- **Session Management**: Session ID generation, extraction, and Strands session manager creation
- **Agent Invocation**: Agent creation, caching, and invocation with proper error handling
- **Request/Response Transformation**: Bidirectional transformation between frontend and Strands formats
- **API Endpoints**: Full end-to-end testing of `/api/chat`, `/api/health`, and other endpoints
- **Error Handling**: Proper error responses for various failure scenarios

## Test Structure

```
backend/api/tests/
├── conftest.py              # Shared pytest fixtures and configuration
├── test_session.py          # Session management unit tests
├── test_transformers.py     # Request/response transformation tests
├── test_integration.py      # End-to-end integration tests
└── __init__.py
```

### Test Files

**`conftest.py`**
- Shared fixtures for test environment setup
- Mock session IDs and sample data
- Environment variable configuration

**`test_session.py`**
- Session ID generation and extraction
- File-based and S3-based session manager creation
- Session caching and cleanup

**`test_transformers.py`**
- Frontend to Strands request transformation
- Strands to frontend response transformation
- Message validation and sanitization

**`test_integration.py`**
- Complete request/response flow
- Agent invocation with mocked agents
- Error handling scenarios
- Health check and configuration endpoints

## Setup

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Install proxy dependencies
pip install -r backend/api/requirements.txt
```

### Environment Variables

Set required environment variables for testing:

```bash
# Required for tests
export PROXY_SESSION_BACKEND=file
export PROXY_USE_AGENTCORE_MEMORY=false
export AWS_REGION=us-west-2

# Neo4j (can be mock values for unit tests)
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password

# Anthropic API key (can be test value for unit tests)
export ANTHROPIC_API_KEY=test-key
```

## Running Tests

### Run All Tests

```bash
cd backend/api
pytest tests/ -v
```

### Run Specific Test File

```bash
# Session tests only
pytest tests/test_session.py -v

# Transformer tests only
pytest tests/test_transformers.py -v

# Integration tests only
pytest tests/test_integration.py -v
```

### Run by Test Markers

```bash
# Unit tests only (no external dependencies)
pytest tests/ -v -m unit

# Integration tests only
pytest tests/ -v -m integration

# Tests requiring Neo4j
pytest tests/ -v -m neo4j

# Tests requiring AgentCore
pytest tests/ -v -m agentcore
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=proxy --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Run Specific Test Class or Method

```bash
# Run specific test class
pytest tests/test_session.py::TestSessionIDGeneration -v

# Run specific test method
pytest tests/test_session.py::TestSessionIDGeneration::test_generate_session_id_default_prefix -v
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Unit tests don't require external services and use mocks:

```python
@pytest.mark.unit
def test_session_id_generation(session_manager):
    """Test session ID generation without external dependencies."""
    session_id = session_manager.generate_session_id()
    assert session_id.startswith("sess-")
```

**Characteristics:**
- Fast execution (< 1 second per test)
- No Neo4j or AWS services required
- Use mocks for external dependencies
- Run on every commit

### Integration Tests (`@pytest.mark.integration`)

Integration tests validate end-to-end flows:

```python
@pytest.mark.integration
def test_chat_endpoint_success(test_client, mock_strands_agent):
    """Test complete chat request flow."""
    response = test_client.post("/api/chat", json={
        "message": "Test message",
        "agent_type": "graph"
    })
    assert response.status_code == 200
```

**Characteristics:**
- Slower execution (1-5 seconds per test)
- May require mocked Strands agents
- Test full request/response pipeline
- Run before deployment

### Service-Specific Tests

**Neo4j Tests (`@pytest.mark.neo4j`)**
- Require running Neo4j instance
- Test actual database operations
- Skip if Neo4j not available

**AgentCore Tests (`@pytest.mark.agentcore`)**
- Require AWS credentials
- Test AgentCore Memory integration
- Skip if AgentCore not configured

## Writing New Tests

### Test Naming Conventions

```python
# Test files
test_*.py                    # All test files start with 'test_'

# Test classes
class TestFeatureName:       # Group related tests

# Test methods
def test_specific_behavior(): # Describe what is being tested
```

### Using Fixtures

```python
@pytest.fixture
def custom_fixture():
    """Provide test data or setup."""
    # Setup
    data = {"key": "value"}
    yield data
    # Teardown (optional)

def test_with_fixture(custom_fixture):
    """Test using custom fixture."""
    assert custom_fixture["key"] == "value"
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

@patch('proxy.client.Agent')
def test_with_mocked_agent(mock_agent_class):
    """Test with mocked Strands Agent."""
    mock_agent = Mock()
    mock_agent.return_value = "Mock response"
    mock_agent_class.return_value = mock_agent
    
    # Test code that uses Agent
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await some_async_function()
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_inputs(input, expected):
    """Test function with multiple inputs."""
    result = transform(input)
    assert result == expected
```

## Common Test Patterns

### Testing API Endpoints

```python
def test_api_endpoint(test_client):
    """Test FastAPI endpoint."""
    response = test_client.post("/api/chat", json={
        "message": "Test",
        "agent_type": "graph"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### Testing Session Management

```python
def test_session_persistence(test_client):
    """Test that sessions persist across requests."""
    # First request
    response1 = test_client.post("/api/chat", json={
        "message": "First message",
        "agent_type": "graph"
    })
    
    session_id = response1.json()["session_id"]
    cookie = response1.cookies["session_id"]
    
    # Second request with same session
    response2 = test_client.post(
        "/api/chat",
        json={"message": "Second message", "agent_type": "graph"},
        cookies={"session_id": cookie}
    )
    
    assert response2.json()["session_id"] == session_id
```

### Testing Error Handling

```python
def test_error_response(test_client, mock_strands_agent):
    """Test error handling."""
    # Mock agent to raise error
    mock_strands_agent.side_effect = Exception("Test error")
    
    response = test_client.post("/api/chat", json={
        "message": "Test",
        "agent_type": "graph"
    })
    
    data = response.json()
    assert data["success"] is False
    assert "error" in data["response"].lower()
```

### Testing Validation

```python
@pytest.mark.parametrize("invalid_message", [
    "",                    # Empty
    "   ",                 # Whitespace only
    "x" * 10001,          # Too long
])
def test_message_validation(test_client, invalid_message):
    """Test message validation rejects invalid inputs."""
    response = test_client.post("/api/chat", json={
        "message": invalid_message,
        "agent_type": "graph"
    })
    
    assert response.status_code == 400
```

## Troubleshooting

### Common Issues

**1. Import Errors**

```
ModuleNotFoundError: No module named 'proxy'
```

**Solution:** Ensure you're running tests from the correct directory:
```bash
cd backend/api
pytest tests/ -v
```

**2. Fixture Not Found**

```
fixture 'session_manager' not found
```

**Solution:** Check that `conftest.py` is in the tests directory and fixtures are properly defined.

**3. Async Tests Failing**

```
RuntimeError: Event loop is closed
```

**Solution:** Ensure `pytest-asyncio` is installed and `asyncio_mode = auto` is set in `pytest.ini`.

**4. Mock Not Working**

```
AttributeError: Mock object has no attribute 'xxx'
```

**Solution:** Properly configure mock spec:
```python
mock_obj = Mock(spec=RealClass)
```

### Debugging Tests

**Run with verbose output:**
```bash
pytest tests/ -vv
```

**Show print statements:**
```bash
pytest tests/ -v -s
```

**Run specific test with debugging:**
```bash
pytest tests/test_session.py::test_name -v -s --pdb
```

**Check test collection:**
```bash
pytest tests/ --collect-only
```

## Best Practices

### DO

✅ Use descriptive test names that explain what is being tested
✅ Keep tests focused on a single behavior
✅ Use fixtures for common setup
✅ Mock external dependencies (Neo4j, AWS, etc.)
✅ Clean up resources in fixtures (use `yield`)
✅ Use appropriate test markers (`unit`, `integration`, etc.)
✅ Test both success and failure scenarios
✅ Verify error messages and status codes

### DON'T

❌ Don't test implementation details
❌ Don't make real API calls to external services
❌ Don't share state between tests
❌ Don't use `sleep()` for timing (use proper async/await)
❌ Don't skip cleanup in fixtures
❌ Don't hardcode secrets or credentials

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend/api
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run unit tests
        env:
          PROXY_SESSION_BACKEND: file
          PROXY_USE_AGENTCORE_MEMORY: false
          AWS_REGION: us-west-2
          NEO4J_URI: bolt://localhost:7687
          NEO4J_USERNAME: neo4j
          NEO4J_PASSWORD: password
          ANTHROPIC_API_KEY: test-key
        run: |
          cd backend/api
          pytest tests/ -v -m unit --cov=proxy
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Coverage Goals

- **Overall Coverage**: > 80%
- **Critical Paths**: > 95%
  - Session management
  - Request/response transformation
  - Error handling
- **Edge Cases**: Well tested
  - Invalid inputs
  - Timeout scenarios
  - Concurrent requests

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Strands Agents Testing](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/testing/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Contributing

When adding new features to the proxy:

1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add new tests for new functionality
4. Maintain test coverage above 80%
5. Update this guide if adding new test patterns

## Questions?

For questions about testing:
- Check existing tests for patterns
- Refer to Strands Agents documentation
- Review FastAPI testing guide
