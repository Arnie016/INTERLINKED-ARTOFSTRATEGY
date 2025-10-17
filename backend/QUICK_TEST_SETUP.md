# Quick Test Setup Guide

## Overview

The full dependency installation (`./setup_test_env.sh`) can take a while due to complex dependency resolution in the `strands_agents/requirements.txt` file. This guide provides a faster path to test the proxy implementation.

## Fast Path: Unit Tests Only

### 1. Install Minimal Dependencies

```bash
cd backend/api

# Install only FastAPI and test dependencies
pip install fastapi pydantic pydantic-settings python-dotenv pytest pytest-asyncio httpx

# Install proxy dependencies
pip install boto3
```

### 2. Run Unit Tests (No External Dependencies)

```bash
# Run transformer tests
pytest tests/test_transformers.py -v

# Run session tests
pytest tests/test_session.py -v
```

These tests will run successfully without:
- Strands agents installed
- Neo4j running
- Anthropic API key

### 3. Expected Output

```
tests/test_transformers.py::TestRequestTransformer::test_basic_transformation PASSED
tests/test_transformers.py::TestRequestTransformer::test_transformation_with_additional_context PASSED
tests/test_transformers.py::TestResponseTransformer::test_basic_transformation PASSED
tests/test_transformers.py::TestResponseTransformer::test_transformation_without_agent_used PASSED
tests/test_transformers.py::TestResponseTransformer::test_error_transformation PASSED
tests/test_transformers.py::TestValidation::test_valid_message PASSED
tests/test_transformers.py::TestValidation::test_empty_message PASSED
tests/test_transformers.py::TestValidation::test_whitespace_only_message PASSED
tests/test_transformers.py::TestValidation::test_oversized_message PASSED
tests/test_transformers.py::TestSanitization::test_basic_sanitization PASSED
tests/test_transformers.py::TestSanitization::test_null_byte_removal PASSED
tests/test_transformers.py::TestSanitization::test_line_ending_normalization PASSED
tests/test_transformers.py::TestSanitization::test_combined_sanitization PASSED

tests/test_session.py::TestSessionManager::test_initialization PASSED
tests/test_session.py::TestSessionManager::test_extract_session_id_from_header PASSED
tests/test_session.py::TestSessionManager::test_extract_session_id_from_cookie PASSED
... (more tests)

============== XX passed in X.XXs ==============
```

## Full Setup: Integration Tests

If you want to run the full integration tests with Strands agents:

### Option 1: Use Pre-built Environment

If you have `strands-agents` already installed in your environment:

```bash
# Activate existing environment
source path/to/your/venv/bin/activate

# Run all tests
cd backend/api
pytest tests/ -v
```

### Option 2: Install from PyPI (Simpler)

Instead of installing from `strands_agents/requirements.txt`, install directly from PyPI:

```bash
cd backend/api

# Install from PyPI (much faster)
pip install strands-agents anthropic neo4j boto3 fastapi uvicorn pydantic pydantic-settings python-dotenv

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run tests
pytest tests/ -v
```

### Option 3: Skip Heavy Dependencies

If dependency resolution is slow, create a minimal requirements file:

```bash
cd backend/api

# Create minimal requirements
cat > requirements-minimal.txt << EOF
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
boto3>=1.26.0
neo4j>=5.0.0
anthropic>=0.18.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.26.0
EOF

# Install
pip install -r requirements-minimal.txt

# Then try installing strands-agents separately
pip install strands-agents
```

## What Gets Tested

### Unit Tests (Fast, No External Deps)
- ✅ Request/response transformation logic
- ✅ Message validation and sanitization
- ✅ Session ID extraction and generation
- ✅ Session cookie management
- ✅ Configuration models
- ✅ Error response formatting

### Integration Tests (Require Setup)
- 🔧 Strands agent invocation
- 🔧 Neo4j queries through agents
- 🔧 Session persistence across requests
- 🔧 End-to-end API workflows

## Manual Verification Without Tests

If you just want to verify the proxy works:

###  1. Create .env File

```bash
cd backend
cp .env.example .env

# Edit .env with your actual credentials
nano .env
```

### 2. Try Starting the Server

```bash
cd backend/api
python main_proxy.py
```

If you see errors about missing modules, install them:

```bash
# For missing strands module
pip install strands-agents

# For missing neo4j module
pip install neo4j

# For missing anthropic module
pip install anthropic
```

### 3. Test with curl

```bash
# Health check (doesn't need agents)
curl http://localhost:8000/api/health

# This will work even if agents aren't working:
{
  "status": "healthy",
  "message": "All systems operational",
  "components": {...},
  "timestamp": "2025-10-17T..."
}
```

## Troubleshooting

### Dependency Resolution is Slow

**Problem**: `pip install` hangs during dependency resolution

**Solutions**:
1. Install packages individually:
   ```bash
   pip install fastapi uvicorn pydantic
   pip install boto3 neo4j anthropic
   pip install strands-agents
   ```

2. Use `--no-deps` flag (careful!):
   ```bash
   pip install --no-deps strands-agents
   pip install anthropic boto3 neo4j pydantic fastapi
   ```

3. Skip strands-agents for now:
   - Unit tests don't need it
   - You can test transformation and session logic

### Import Errors in Tests

**Problem**: `ModuleNotFoundError: No module named 'proxy'`

**Solution**: Run tests from `backend/api` directory:
```bash
cd backend/api
pytest tests/
```

### Test Discovery Issues

**Problem**: `No tests collected`

**Solution**: Ensure pytest.ini is in place:
```bash
ls backend/api/pytest.ini
```

## Summary

For fastest verification of the proxy implementation:

1. **Quick**: Run unit tests only (no strands-agents needed)
2. **Medium**: Install from PyPI instead of requirements.txt
3. **Full**: Use the setup script but be patient with dependency resolution

The core proxy logic (transformation, session management, routing) can be tested without the full Strands agents stack!

