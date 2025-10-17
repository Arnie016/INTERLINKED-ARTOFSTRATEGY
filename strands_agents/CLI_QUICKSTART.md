# CLI Testing Quick Start

**Fast track guide to test the orchestrator agent via command line in 5 minutes.**

## 🚀 Quick Setup (Local Testing)

```bash
# 1. Navigate to project
cd strands_agents

# 2. Run setup
./setup.sh

# 3. Activate environment
source venv/bin/activate

# 4. Configure .env (edit with your credentials)
nano .env  # Add NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, AWS_REGION

# 5. Test connection
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(f'AWS Region: {os.getenv(\"AWS_REGION\")}')"
```

## 💬 Interactive CLI Test

Create and run a simple test script:

```bash
# Create test script
cat > quick_test.py << 'EOF'
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.agents import create_orchestrator_agent
from dotenv import load_dotenv

load_dotenv()
orchestrator = create_orchestrator_agent(user_role="user")

print("🤖 Orchestrator Ready! Type your query:")
while True:
    query = input("\nYou: ").strip()
    if query.lower() in ['exit', 'quit']: break
    if not query: continue
    print(f"\nOrchestrator: {orchestrator(query)}")
EOF

# Run it
python3 quick_test.py
```

## 🧪 Test Queries

Try these queries:

```
Who are all the people in Engineering?
Find the most influential people
What processes does the Data team own?
Detect communities in our organization
```

## ☁️ AgentCore Deployment (Production)

```bash
# 1. Install AgentCore CLI
pip install bedrock-agentcore

# 2. Create memory
python3 examples/setup_agentcore_memory.py
# Copy the MEMORY_ID output

# 3. Set environment
export MEMORY_ID=<your-memory-id>
export AWS_REGION=us-west-2

# 4. Configure deployment
agentcore configure --entrypoint examples/agentcore_deployment_handler.py

# 5. Deploy
agentcore launch

# 6. Test deployed agent
agentcore invoke '{"prompt": "Who are the engineers?"}' --session-id test-1

# 7. View logs
agentcore logs --tail
```

## 🔧 Common Commands

```bash
# Activate venv
source venv/bin/activate

# Run examples
python3 examples/basic_usage.py

# Test Neo4j connection
python3 -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✓ Connected'); driver.close()"

# Verify AWS
aws sts get-caller-identity

# View AgentCore logs
agentcore logs --tail

# List memory resources
aws bedrock-agent-runtime list-memories --region us-west-2
```

## 🐛 Quick Troubleshooting

```bash
# Virtual env not activated?
which python  # Should show venv/bin/python
source venv/bin/activate

# Missing dependencies?
pip install -r requirements.txt

# AWS credentials issue?
aws configure
aws sts get-caller-identity

# Neo4j connection failed?
cat .env | grep NEO4J  # Verify credentials

# Bedrock model error "on-demand throughput isn't supported"?
# Update .env to use cross-region inference profile:
echo "BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0" >> .env

# Agent not responding?
export LOG_LEVEL=DEBUG
python3 quick_test.py
```

## 📚 Full Documentation

For comprehensive guide: [docs/guides/CLI_TESTING_GUIDE.md](docs/guides/CLI_TESTING_GUIDE.md)

## 🎯 What to Test

### Basic Functionality
- ✅ Agent creates successfully
- ✅ Responds to simple queries
- ✅ Routes to correct specialized agents
- ✅ Returns structured data from Neo4j

### Memory (AgentCore)
- ✅ Remembers within session
- ✅ Maintains context across turns
- ✅ Extracts preferences (LTM)

### Error Handling
- ✅ Handles invalid queries gracefully
- ✅ Reports permission errors
- ✅ Provides helpful error messages

### Performance
- ✅ Response time < 5 seconds
- ✅ Handles concurrent requests
- ✅ Logs structured output

---

**Need help?** Check the full [CLI Testing Guide](docs/guides/CLI_TESTING_GUIDE.md) or run `python3 examples/basic_usage.py` for examples.

