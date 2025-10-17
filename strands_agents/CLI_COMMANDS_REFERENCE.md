# CLI Commands Quick Reference

Quick reference for all CLI testing commands.

## 🚀 Setup Commands

```bash
# Initial setup
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Configure environment
cp env.template .env
nano .env  # Edit with your credentials

# Verify setup
python3 -c "import boto3; import neo4j; from strands import Agent; print('✓ OK')"
```

## 🧪 Testing Commands

### Automated Testing

```bash
# Run all local tests
./run_cli_tests.sh --local

# Run AgentCore deployment tests
./run_cli_tests.sh --agentcore

# Run all tests
./run_cli_tests.sh --all

# Interactive testing mode
./run_cli_tests.sh --interactive

# Show help
./run_cli_tests.sh --help
```

### Manual Testing

```bash
# Run basic examples
python3 examples/basic_usage.py

# Test individual agents
python3 examples/test_specialized_agents.py

# Test with memory integration
python3 test_orchestrator_with_memory.py
```

## ☁️ AgentCore Commands

### Memory Management

```bash
# Create memory resources
python3 examples/setup_agentcore_memory.py

# List existing memory resources
aws bedrock-agent-runtime list-memories --region us-west-2

# View memory events
aws bedrock-agent-runtime list-memory-events \
  --memory-id $MEMORY_ID \
  --region us-west-2
```

### Deployment

```bash
# Configure deployment
agentcore configure --entrypoint examples/agentcore_deployment_handler.py

# Deploy to AgentCore Runtime
agentcore launch

# List deployments
agentcore list

# Get deployment info
agentcore describe

# Delete deployment
agentcore delete
```

### Invocation

```bash
# Single query
agentcore invoke '{"prompt": "Who are the engineers?"}' --session-id test-1

# Multiple queries with same session
agentcore invoke '{"prompt": "My name is Alice"}' --session-id alice-session
agentcore invoke '{"prompt": "What is my name?"}' --session-id alice-session

# Different sessions
agentcore invoke '{"prompt": "test"}' --session-id session-1
agentcore invoke '{"prompt": "test"}' --session-id session-2
```

### Monitoring

```bash
# View live logs
agentcore logs --tail

# View last N lines
agentcore logs --tail -n 50

# Filter by log level
agentcore logs --filter-level ERROR

# View specific time range
agentcore logs \
  --start-time "2024-01-01T00:00:00" \
  --end-time "2024-01-02T00:00:00"
```

## 📊 AWS Commands

### Identity & Credentials

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Configure credentials
aws configure

# Use specific profile
export AWS_PROFILE=your-profile
aws sts get-caller-identity
```

### Bedrock

```bash
# List available models
aws bedrock list-foundation-models --region us-west-2

# List Claude models
aws bedrock list-foundation-models \
  --region us-west-2 \
  --query "modelSummaries[?contains(modelId, 'claude')].modelId" \
  --output table

# Test model invocation
aws bedrock invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"Hello"}],"max_tokens":100}' \
  --region us-west-2 \
  /tmp/response.json
cat /tmp/response.json
```

### CloudWatch Metrics

```bash
# View invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/AgentCore \
  --metric-name Invocations \
  --dimensions Name=AgentName,Value=interlinked-orchestrator \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-2

# View response times
aws cloudwatch get-metric-statistics \
  --namespace AWS/AgentCore \
  --metric-name Duration \
  --dimensions Name=AgentName,Value=interlinked-orchestrator \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region us-west-2

# View errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/AgentCore \
  --metric-name Errors \
  --dimensions Name=AgentName,Value=interlinked-orchestrator \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-2
```

### CloudFormation

```bash
# List AgentCore stacks
aws cloudformation list-stacks \
  --region us-west-2 \
  --query "StackSummaries[?contains(StackName, 'agentcore')]"

# View stack events
aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region us-west-2

# Delete failed stack
aws cloudformation delete-stack \
  --stack-name <stack-name> \
  --region us-west-2
```

## 🗄️ Neo4j Commands

### Connection Testing

```bash
# Test connection
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
print('✓ Connected')
driver.close()
"

# Get database info
python3 -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)
with driver.session() as session:
    result = session.run('CALL dbms.components() YIELD name, versions')
    for record in result:
        print(f'{record[\"name\"]}: {record[\"versions\"]}')
driver.close()
"
```

## 🔍 Verification Commands

### Environment

```bash
# View all environment variables
env | grep -E '(AWS|NEO4J|MEMORY|USER_ROLE)'

# Check specific variables
echo $AWS_REGION
echo $NEO4J_URI
echo $MEMORY_ID
echo $USER_ROLE

# Verify .env file
cat .env | grep -v '^#' | grep -v '^$'
```

### Python Environment

```bash
# Check Python version
python3 --version

# Verify virtual environment
which python3  # Should show venv/bin/python3

# List installed packages
pip list

# Check specific packages
pip list | grep -E '(strands|boto3|neo4j|bedrock)'

# Verify imports
python3 -c "
import boto3
import neo4j
from strands import Agent
from bedrock_agentcore.memory import MemoryClient
print('✓ All imports successful')
"
```

### Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# Install specific package
pip install bedrock-agentcore

# Upgrade package
pip install --upgrade strands-agents

# Show package info
pip show strands-agents
```

## 🐛 Debugging Commands

### Enable Debug Logging

```bash
# Set debug log level
export LOG_LEVEL=DEBUG

# Run with verbose output
python3 -u test_orchestrator_cli.py 2>&1 | tee debug.log

# AgentCore debug mode
agentcore invoke '{"prompt": "test"}' --debug --session-id debug-test
```

### View Logs

```bash
# Application logs
tail -f logs/*.log

# Test output logs
cat /tmp/test*.log

# AgentCore logs
agentcore logs --tail -n 100

# Filtered logs
agentcore logs --filter-level ERROR --tail -n 50
```

### Performance Testing

```bash
# Measure response time
time agentcore invoke '{"prompt": "test"}' --session-id perf-test

# Concurrent requests
for i in {1..10}; do
    agentcore invoke '{"prompt": "test"}' --session-id "concurrent-$i" &
done
wait

# Check system resources
top
htop  # if available
```

## 🧹 Cleanup Commands

### Local Cleanup

```bash
# Remove virtual environment
deactivate
rm -rf venv

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove logs
rm -rf logs/*.log
rm -f /tmp/test*.log

# Reset environment
rm .env
cp env.template .env
```

### AgentCore Cleanup

```bash
# Delete deployment
agentcore delete

# Delete memory resources
aws bedrock-agent-runtime delete-memory \
  --memory-id $MEMORY_ID \
  --region us-west-2

# Delete CloudFormation stacks
aws cloudformation delete-stack \
  --stack-name <stack-name> \
  --region us-west-2
```

## 📝 Common Workflows

### Fresh Start Workflow

```bash
# 1. Setup
cd strands_agents
./setup.sh
source venv/bin/activate

# 2. Configure
cp env.template .env
nano .env  # Add your credentials

# 3. Verify
python3 -c "import boto3; import neo4j; print('✓ OK')"
aws sts get-caller-identity

# 4. Test locally
./run_cli_tests.sh --local

# 5. Test interactively
./run_cli_tests.sh --interactive
```

### AgentCore Deployment Workflow

```bash
# 1. Create memory
python3 examples/setup_agentcore_memory.py
export MEMORY_ID=<your-memory-id>

# 2. Test locally with memory
python3 test_orchestrator_with_memory.py

# 3. Configure deployment
agentcore configure --entrypoint examples/agentcore_deployment_handler.py

# 4. Deploy
agentcore launch

# 5. Test deployment
agentcore invoke '{"prompt": "test"}' --session-id test-1

# 6. Monitor
agentcore logs --tail
```

### Debug Workflow

```bash
# 1. Enable debug mode
export LOG_LEVEL=DEBUG

# 2. Check environment
env | grep -E '(AWS|NEO4J|MEMORY)'

# 3. Verify connections
aws sts get-caller-identity
python3 -c "from neo4j import GraphDatabase; ..."  # Neo4j test

# 4. Run with logging
python3 -u test_orchestrator_cli.py 2>&1 | tee debug.log

# 5. Review logs
cat debug.log
agentcore logs --tail -n 100

# 6. Check metrics
aws cloudwatch get-metric-statistics ...
```

## 🔗 Quick Links

- [Full Testing Guide](docs/guides/CLI_TESTING_GUIDE.md)
- [Walkthrough](WALKTHROUGH.md)
- [Quick Start](CLI_QUICKSTART.md)
- [CLI Testing README](CLI_TESTING_README.md)

---

**💡 Tip:** Bookmark this page for quick command reference during testing!

