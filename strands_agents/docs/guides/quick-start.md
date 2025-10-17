# Quick Start Guide

This guide will help you get the Strands Agents project up and running quickly.

## Prerequisites

Before starting, ensure you have:

- ✅ Python 3.11 or higher
- ✅ AWS CLI v2 installed and configured
- ✅ AWS account with Bedrock access
- ✅ Neo4j instance (local or Aura)

## 1. Initial Setup

Clone the repository and navigate to the Strands agents directory:

```bash
cd strands_agents
```

## 2. Run Setup Script

The setup script will handle most of the initial configuration:

```bash
./setup.sh
```

This script will:
- ✅ Verify Python and AWS CLI versions
- ✅ Check AWS credentials
- ✅ Create a virtual environment
- ✅ Install dependencies
- ✅ Create a `.env` file from template
- ✅ Verify Bedrock access

## 3. Configure Environment

Edit the `.env` file with your specific configuration:

```bash
# Open in your preferred editor
nano .env
# or
code .env
```

**Required configuration:**

```bash
# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_DATABASE=neo4j

# AWS Configuration
AWS_REGION=us-west-2
AWS_PROFILE=default  # or your specific profile
```

## 4. Verify Installation

Activate the virtual environment:

```bash
source venv/bin/activate
```

Test Python imports:

```bash
python3 -c "import boto3; import neo4j; print('✓ All imports successful')"
```

Verify AWS connectivity:

```bash
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-west-2 --query "modelSummaries[?contains(modelId, 'claude')].modelId" --output table
```

## 5. Project Structure

Your project should now have this structure:

```
strands_agents/
├── src/
│   ├── agents/           # Agent definitions (to be created)
│   ├── tools/            # Tool implementations (to be created)
│   ├── utils/            # Shared utilities (to be created)
│   └── config/           # Configuration modules (to be created)
├── tests/                # Test files
├── docs/                 # Documentation
├── deployment/           # Deployment configurations
│   ├── dev/
│   └── prod/
├── venv/                 # Virtual environment
├── .env                  # Your configuration (not in git)
├── .env.example          # Configuration template
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## 6. Next Steps

Now that your environment is set up, you're ready to:

### Development Phase

1. **Create Agent Definitions** (Task 1, Subtask 2)
   - Implement the five agent classes
   - Add tool annotations
   - Configure agent schemas

2. **Implement Tools** (Tasks 3-6)
   - Graph read-only tools
   - Analytics tools
   - Write tools with safeguards
   - Admin tools

3. **Set up Orchestration** (Task 7)
   - Implement agent-as-tools pattern
   - Configure routing logic

### Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

### Development Server

Start the FastAPI development proxy:

```bash
uvicorn src.api.main:app --reload --port 8000
```

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Install new dependencies
pip install package-name
pip freeze > requirements.txt

# Run tests
pytest tests/ -v

# Format code (if using black)
black src/

# Type checking (if using mypy)
mypy src/

# AWS commands
aws bedrock list-foundation-models --region us-west-2
aws secretsmanager get-secret-value --secret-id interlinked-aos-dev
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Remove and recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### AWS Credentials

```bash
# Verify credentials
aws sts get-caller-identity

# Configure new profile
aws configure --profile interlinked-dev

# Use specific profile
export AWS_PROFILE=interlinked-dev
```

### Neo4j Connection

```bash
# Test Neo4j connection
python3 -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)
driver.verify_connectivity()
print('✓ Neo4j connection successful')
driver.close()
"
```

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

## Getting Help

- 📖 **Documentation**: Check the [docs/](./docs/) directory
- 🐛 **Issues**: Review existing issues or create a new one
- 💬 **Questions**: Reach out to the team

## Useful Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents Documentation](https://github.com/anthropics/strands-agents)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## What's Next?

After completing this quick start, you should:

1. ✅ Have a working development environment
2. ✅ Be able to run tests
3. ✅ Have AWS and Neo4j connectivity
4. ✅ Be ready to implement agents

Proceed to implement **Task 1, Subtask 2**: "Implement agent definition files with schemas and capabilities"

See the task details in `.taskmaster/tasks/tasks.json` or the PRD document.
