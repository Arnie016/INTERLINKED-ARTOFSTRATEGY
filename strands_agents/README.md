# Interlinked - Strands Agents Implementation

This directory contains the Strands Agents implementation for the Interlinked Art of Strategy platform, deployed on AWS Bedrock AgentCore Runtime.

## Architecture

The implementation follows the "Agents as Tools" pattern with:

- **OrchestratorAgent**: Main entry point that routes user prompts to specialized agents
- **GraphAgent**: Handles read/search operations on the Neo4j graph
- **AnalyzerAgent**: Performs analytics operations on graph data
- **ExtractorAgent**: Manages data ingestion with controlled write operations
- **AdminAgent**: Handles privileged administrative operations

## Project Structure

```
strands_agents/
├── src/
│   ├── agents/           # Agent definitions
│   │   ├── orchestrator_agent.py
│   │   ├── graph_agent.py
│   │   ├── analyzer_agent.py
│   │   ├── extractor_agent.py
│   │   └── admin_agent.py
│   ├── tools/            # Tool implementations
│   ├── utils/            # Shared utilities
│   └── config/           # Configuration modules
├── tests/                # Test files
├── docs/                 # Documentation
├── deployment/           # Deployment configurations
│   ├── dev/              # Development environment
│   └── prod/             # Production environment
└── requirements.txt      # Python dependencies
```

## Setup

### Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate credentials
- Access to AWS Bedrock AgentCore
- Neo4j instance (local or Aura)

### Installation

1. Create and activate a virtual environment:
```bash
cd strands_agents
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp ../.env.example .env
# Edit .env with your configuration
```

### Development

Run the FastAPI proxy for development:
```bash
uvicorn src.api.main:app --reload --port 8000
```

### Deployment

Deploy to AWS Bedrock AgentCore Runtime:
```bash
# Coming soon - deployment scripts will be added
```

## Configuration

### Environment Variables (Development)

- `NEO4J_URI`: Neo4j connection URI
- `NEO4J_USERNAME`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `NEO4J_DATABASE`: Neo4j database name
- `AWS_REGION`: AWS region (default: us-west-2)
- `AWS_PROFILE`: AWS profile to use

### AWS Secrets Manager (Production)

Secrets are stored following the naming convention: `interlinked-aos-<env>`

## Testing

Run tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Documentation

See the [docs](./docs/) directory for detailed documentation on:
- Agent definitions and capabilities
- Tool implementations
- Security and access control
- Deployment procedures
- Operational runbooks

## License

Proprietary - See LICENSE in root directory
