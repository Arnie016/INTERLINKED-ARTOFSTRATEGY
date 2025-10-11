# Agent Tool Architecture Tests

This directory contains test files for the Agent Tool Architecture.

## Test Files

### `test_architecture.py`
Tests the core architecture components:
- Tool imports and registry
- Agent imports and configurations
- Role-based permissions
- Model validation
- Tool categories

**Run:** `python test_architecture.py`

### `test_neo4j_connection.py`
Tests Neo4j database connectivity:
- Connection establishment
- Basic query execution
- Environment variable configuration

**Run:** `python test_neo4j_connection.py`

### `run_tests.py`
Test runner that executes all tests:
- Runs all test files
- Provides summary results
- Handles test failures gracefully

**Run:** `python run_tests.py`

## Running Tests

### Individual Tests
```bash
# From the tests directory
python test_architecture.py
python test_neo4j_connection.py

# From the backend directory
python tests/test_architecture.py
python tests/test_neo4j_connection.py
```

### All Tests (Recommended)
```bash
# From the tests directory
python run_tests.py

# From the backend directory
python tests/run_tests.py
```

## Requirements

- Python 3.8+
- Neo4j database (for connection tests)
- Environment variables in `.env` file:
  - `NEO4J_URI`
  - `NEO4J_USERNAME`
  - `NEO4J_PASSWORD`

## Test Results

The architecture test should show:
- ✅ 24 tools across 4 categories
- ✅ 4 agent types with different roles
- ✅ 4 roles with appropriate permissions
- ✅ Model validation working correctly

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the correct directory:
- Tests should be run from the `tests/` directory
- Or use the full path from the `backend/` directory

### Database Connection Errors
For Neo4j connection tests:
- Ensure Neo4j is running
- Check environment variables in `.env` file
- Verify network connectivity to Neo4j instance
