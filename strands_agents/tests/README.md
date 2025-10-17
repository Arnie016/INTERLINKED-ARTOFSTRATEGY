# Testing Guide for Strands Agents

## Current Testing Capabilities

### ✅ Tests We CAN Run Now (No AWS/Neo4j Required)

These tests verify the agent architecture without requiring external services:

1. **Agent Instantiation** - Verify all agents can be created
2. **Configuration Handling** - Test custom model configs
3. **Role-Based Access** - Verify orchestrator provides correct agents per role  
4. **Tool Registration** - Confirm all tools are properly defined
5. **Type Hints** - Validate function signatures and types
6. **Package Exports** - Ensure all modules export correctly

### ❌ Tests We CANNOT Run Yet

These require implementation of tasks 2-6:

1. **End-to-End Execution** - Requires AWS Bedrock credentials
2. **Neo4j Integration** - Tools are currently placeholders
3. **Actual Graph Queries** - Needs task 3 implementation
4. **Data Modifications** - Needs task 5 implementation
5. **Live Model Responses** - Would incur AWS costs

## Running the Tests

### Prerequisites

```bash
# Install dependencies (from strands_agents directory)
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov
```

### Run All Basic Tests

```bash
# From strands_agents directory
cd /Users/stefn/Interlinked/AWS\ Hackathon/INTERLINKED-ARTOFSTRATEGY/strands_agents

# Run all tests
python -m pytest tests/test_agents_basic.py -v

# Run with coverage
python -m pytest tests/test_agents_basic.py --cov=src --cov-report=html

# Run specific test class
python -m pytest tests/test_agents_basic.py::TestAgentInstantiation -v

# Run specific test
python -m pytest tests/test_agents_basic.py::TestAgentInstantiation::test_graph_agent_creation -v
```

### Expected Output

```
============================= test session starts ==============================
collected 30 items

tests/test_agents_basic.py::TestAgentInstantiation::test_graph_agent_creation PASSED
tests/test_agents_basic.py::TestAgentInstantiation::test_analyzer_agent_creation PASSED
tests/test_agents_basic.py::TestAgentInstantiation::test_extractor_agent_creation PASSED
tests/test_agents_basic.py::TestAgentInstantiation::test_admin_agent_creation PASSED
tests/test_agents_basic.py::TestAgentInstantiation::test_orchestrator_creation_user_role PASSED
tests/test_agents_basic.py::TestAgentInstantiation::test_orchestrator_creation_extractor_role PASSED
tests/test_agents_basic.py::TestAgentInstantiation::test_orchestrator_creation_admin_role PASSED
tests/test_agents_basic.py::TestCustomConfiguration::test_custom_temperature PASSED
tests/test_agents_basic.py::TestCustomConfiguration::test_custom_max_tokens PASSED
tests/test_agents_basic.py::TestCustomConfiguration::test_multiple_custom_params PASSED
tests/test_agents_basic.py::TestToolDefinitions::test_graph_search_tools_exist PASSED
tests/test_agents_basic.py::TestToolDefinitions::test_graph_analysis_tools_exist PASSED
tests/test_agents_basic.py::TestToolDefinitions::test_graph_crud_tools_exist PASSED
tests/test_agents_basic.py::TestToolDefinitions::test_graph_admin_tools_exist PASSED
tests/test_agents_basic.py::TestToolPlaceholders::test_search_nodes_placeholder PASSED
tests/test_agents_basic.py::TestToolPlaceholders::test_find_related_nodes_placeholder PASSED
tests/test_agents_basic.py::TestToolPlaceholders::test_create_node_placeholder PASSED
tests/test_agents_basic.py::TestTypeHints::test_search_nodes_signature PASSED
tests/test_agents_basic.py::TestTypeHints::test_create_node_signature PASSED
tests/test_agents_basic.py::TestAgentTools::test_graph_agent_tool_exists PASSED
tests/test_agents_basic.py::TestAgentTools::test_analyzer_agent_tool_exists PASSED
tests/test_agents_basic.py::TestAgentTools::test_extractor_agent_tool_exists PASSED
tests/test_agents_basic.py::TestAgentTools::test_admin_agent_tool_exists PASSED
tests/test_agents_basic.py::TestPackageExports::test_agents_package_exports PASSED

============================== 30 tests PASSED in 2.35s ==============================
```

## Test Organization

### Test Classes

1. **TestAgentInstantiation** - Agent creation tests
2. **TestCustomConfiguration** - Custom config tests
3. **TestToolDefinitions** - Tool existence tests
4. **TestToolPlaceholders** - Placeholder response tests
5. **TestTypeHints** - Type annotation tests
6. **TestAgentTools** - Agent tool wrapper tests
7. **TestPackageExports** - Package export tests

## What These Tests Validate

### ✅ Architecture Correctness
- All 5 agents (orchestrator + 4 specialized) can be instantiated
- Each agent has the correct temperature setting
- Orchestrator provides correct tools based on user role

### ✅ Configuration System
- Custom model parameters are applied correctly
- Multiple custom parameters work together
- Default configurations are correct

### ✅ Tool System
- All 13 tools are properly defined
- Tool signatures have correct type hints
- Placeholder tools return expected structure

### ✅ Code Quality
- Functions are callable
- Documentation exists
- Type annotations are present
- Package exports are correct

## Limitations

⚠️ **These tests do NOT validate:**
- Actual LLM responses (requires AWS Bedrock)
- Neo4j database operations (tools are placeholders)
- Error handling for real failures (no real operations yet)
- Performance under load
- Memory usage during operation

## Future Testing (After Tasks 2-6)

Once tools are implemented, we'll add:

### Integration Tests
- Neo4j connection and query tests
- AWS Bedrock model invocation tests
- End-to-end workflow tests

### Performance Tests
- Query response time tests
- Connection pool efficiency tests
- Concurrent operation tests

### Security Tests
- Role-based access enforcement
- Input validation tests
- Injection attack prevention

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the correct directory:

```bash
cd /Users/stefn/Interlinked/AWS\ Hackathon/INTERLINKED-ARTOFSTRATEGY/strands_agents
python -m pytest tests/test_agents_basic.py -v
```

### Missing Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

### Strands Package Not Found

The tests are designed to run even if `strands-agents` package is not installed, but you may see warnings. Install it with:

```bash
pip install strands-agents
```

## Next Steps

After implementing tasks 2-6, we'll create:
- `test_neo4j_integration.py` - Neo4j connection and query tests
- `test_graph_operations.py` - Actual graph operation tests
- `test_agent_workflows.py` - End-to-end workflow tests
- `test_security.py` - Security and access control tests

