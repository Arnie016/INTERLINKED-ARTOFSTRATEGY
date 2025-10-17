# Strands Agents for Organizational Graph Analysis

A multi-agent system built with AWS Bedrock and Strands Agents SDK for analyzing organizational graph data stored in Neo4j.

## Architecture

This project implements the **"Agents as Tools"** pattern with specialized agents orchestrated by a main coordinator.

For detailed architecture information, see:
- 📐 [Architecture Overview](docs/architecture/overview.md) - Complete architecture documentation
- 🔗 [Integration Guide](docs/architecture/integration.md) - Integration patterns and utilities

### Quick Overview

```
OrchestratorAgent (Main Entry Point)
├── GraphAgent (Read-only queries and search)
├── AnalyzerAgent (Advanced analytics and insights)
├── ExtractorAgent (Data ingestion and writes)
└── AdminAgent (Privileged admin operations)
```

## Getting Started

For detailed setup instructions, see our comprehensive guides:

- 🚀 [Quick Start Guide](docs/guides/quick-start.md) - Get up and running in minutes
- ☁️ [AWS Setup Guide](docs/guides/aws-setup.md) - Configure AWS credentials and Bedrock
- 🗄️ [Neo4j Setup Guide](docs/guides/neo4j-setup.md) - Configure Neo4j connection

### Quick Install

```bash
# Clone and navigate to project
cd strands_agents

# Run automated setup
./setup.sh

# Configure environment
cp env.template .env
# Edit .env with your credentials
```

## CLI Testing

Test the orchestrator agent via command line interface in development or production:

### Quick Test (5 minutes)
```bash
./run_cli_tests.sh --interactive
```

### Full Testing Documentation
- 🎯 [CLI Quick Start](CLI_QUICKSTART.md) - Get testing in 5 minutes
- 📋 [Complete Walkthrough](WALKTHROUGH.md) - Step-by-step guide with exact commands
- 📚 [CLI Testing Guide](docs/guides/CLI_TESTING_GUIDE.md) - Comprehensive testing scenarios
- 🛠️ [CLI Testing README](CLI_TESTING_README.md) - Documentation index

### Automated Testing
```bash
# Local testing
./run_cli_tests.sh --local

# AgentCore deployment testing
./run_cli_tests.sh --agentcore

# All tests
./run_cli_tests.sh --all
```

See [CLI Testing README](CLI_TESTING_README.md) for complete documentation.

## Usage

### Basic Usage with Orchestrator

```python
from strands_agents.src.agents import create_orchestrator_agent

# Create orchestrator for a regular user
orchestrator = create_orchestrator_agent(user_role="user")

# Ask a question
response = orchestrator("Who are the most influential people in Engineering?")
print(response)

# Complex multi-agent query
response = orchestrator(
    "Find all bottlenecks in our processes and suggest who should own each one"
)
print(response)
```

### Using Specialized Agents Directly

```python
from strands_agents.src.agents import (
    create_graph_agent,
    create_analyzer_agent,
    create_extractor_agent
)

# Graph Agent for searches
graph_agent = create_graph_agent()
response = graph_agent("Find all people in the Data department")
print(response)

# Analyzer Agent for analytics
analyzer_agent = create_analyzer_agent()
response = analyzer_agent("Detect communities in our organization")
print(response)

# Extractor Agent for data ingestion (requires appropriate role)
extractor_agent = create_extractor_agent()
response = extractor_agent(
    "Create a new person: Alice Johnson, Senior Engineer, Data team"
)
print(response)
```

### Convenience Function

```python
from strands_agents.src.agents import process_query

# Simple one-line query processing
response = process_query(
    "What processes does the Engineering department own?",
    user_role="user"
)
print(response)
```

## Configuration

Configuration is managed through environment variables and YAML files.

For detailed configuration information:
- [Configuration Module](src/config/README.md) - Configuration system details
- [Utilities Module](src/utils/README.md) - Shared utilities and helpers

### Quick Configuration

```python
from strands_agents.src.agents import create_orchestrator_agent

# Create with default configuration
orchestrator = create_orchestrator_agent(user_role="user")

# Or customize model settings
custom_config = {
    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "temperature": 0.3
}
orchestrator = create_orchestrator_agent(
    user_role="user",
    custom_model_config=custom_config
)
```

## Documentation

Comprehensive documentation is organized by topic:

### 📚 Guides (Getting Started)
- [Quick Start](docs/guides/quick-start.md) - Get up and running
- [AWS Setup](docs/guides/aws-setup.md) - Configure AWS credentials
- [Neo4j Setup](docs/guides/neo4j-setup.md) - Configure database connection

### 🏗️ Architecture (Technical Details)
- [Architecture Overview](docs/architecture/overview.md) - System architecture
- [Integration Guide](docs/architecture/integration.md) - Integration patterns

### 🔧 Implementation (Development)
- [Agent Implementation](docs/implementation/agents.md) - Agent implementation details
- [Utilities Implementation](docs/implementation/utilities.md) - Shared utilities
- [Setup Details](docs/implementation/setup.md) - Project setup summary

### 📖 Module Documentation
- [Configuration](src/config/README.md) - Configuration management
- [Utilities](src/utils/README.md) - Shared utilities and helpers
- [Testing](tests/README.md) - Testing guide and best practices

## Testing

```bash
# Run all tests
cd strands_agents
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific tests
python -m pytest tests/test_agents_basic.py -v
```

See the [Testing Guide](tests/README.md) for more details.

## License

See main project LICENSE file.

## Support

For issues or questions, please contact the development team or create an issue in the project repository.
