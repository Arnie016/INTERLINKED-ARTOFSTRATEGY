# Command Line Interface Testing Guide

Complete guide for testing the Strands Agents orchestrator via CLI in development environment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development Testing](#local-development-testing)
4. [AgentCore Memory Setup](#agentcore-memory-setup)
5. [AgentCore Deployment](#agentcore-deployment)
6. [Testing Scenarios](#testing-scenarios)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- ✅ Python 3.11 or higher
- ✅ AWS CLI v2 installed and configured
- ✅ AWS account with Bedrock access
- ✅ Neo4j instance (local or Aura) with test data
- ✅ AWS Bedrock AgentCore CLI (`pip install bedrock-agentcore`)
- ✅ Active AWS credentials with proper IAM permissions

### Verify Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check AWS CLI
aws --version  # Should be 2.x

# Verify AWS credentials
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region us-west-2 --query "modelSummaries[?contains(modelId, 'claude')].modelId" --output table

# Check AgentCore CLI (install if needed)
pip install bedrock-agentcore
agentcore --version
```

---

## Environment Setup

### Step 1: Navigate to Project Directory

```bash
cd strands_agents
```

### Step 2: Run Setup Script

The setup script handles most initialization:

```bash
./setup.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Create `.env` template
- ✅ Verify AWS connectivity

### Step 3: Configure Environment Variables

Create or edit the `.env` file:

```bash
# Copy template if needed
cp .env.example .env

# Edit with your favorite editor
nano .env  # or code .env, vim .env, etc.
```

**Required Configuration for Local Testing:**

```bash
# ============================================
# AWS Configuration
# ============================================
AWS_REGION=us-west-2
AWS_PROFILE=default  # or your specific profile

# ============================================
# Neo4j Configuration
# ============================================
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=neo4j

# ============================================
# Bedrock Model Configuration
# ============================================
# Default model for agents
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_TEMPERATURE=0.5
BEDROCK_MAX_TOKENS=4096

# ============================================
# Optional: AgentCore Memory (for advanced testing)
# ============================================
# MEMORY_ID=<will-be-set-later>
# USER_ROLE=user  # Options: user, extractor, admin

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # Options: json, text
```

### Step 4: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 5: Verify Installation

```bash
# Test Python imports
python3 -c "import boto3; import neo4j; from strands import Agent; print('✓ All imports successful')"

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

# Verify Bedrock model access
aws bedrock invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"Hello"}],"max_tokens":100}' \
  --region us-west-2 \
  /tmp/bedrock_response.json && cat /tmp/bedrock_response.json
```

---

## Local Development Testing

### Test 1: Simple Orchestrator (No AgentCore)

Create a test script to interact with the orchestrator locally:

```bash
# Create test script
cat > test_orchestrator_cli.py << 'EOF'
#!/usr/bin/env python3
"""
Simple CLI for testing the orchestrator agent locally.
Run this for quick testing without AgentCore deployment.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents import create_orchestrator_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("=" * 70)
    print("Strands Agents - Local Orchestrator Test")
    print("=" * 70)
    print()
    
    # Create orchestrator for a regular user
    print("Creating orchestrator agent (user role)...")
    orchestrator = create_orchestrator_agent(user_role="user")
    print("✓ Orchestrator created")
    print()
    
    # Interactive CLI loop
    print("Enter your queries (type 'exit' to quit, 'help' for examples)")
    print("-" * 70)
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            # Process query
            print("\nOrchestrator: ", end="", flush=True)
            response = orchestrator(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

def print_help():
    """Print example queries."""
    print("\nExample queries:")
    print("  • Who are all the people in Engineering?")
    print("  • Find the most influential people in the organization")
    print("  • What processes does the Data team own?")
    print("  • Who reports to Alice Johnson?")
    print("  • Detect communities in our organization")
    print("  • Find organizational bottlenecks")

if __name__ == "__main__":
    main()
EOF

chmod +x test_orchestrator_cli.py
```

**Run the test:**

```bash
python3 test_orchestrator_cli.py
```

**Expected Output:**
```
======================================================================
Strands Agents - Local Orchestrator Test
======================================================================

Creating orchestrator agent (user role)...
✓ Orchestrator created

Enter your queries (type 'exit' to quit, 'help' for examples)
----------------------------------------------------------------------

You: Who are the people in Engineering?

Orchestrator: [Agent response with data from Neo4j...]
```

### Test 2: Test Individual Specialized Agents

```bash
# Create specialized agent test script
cat > test_specialized_agents.py << 'EOF'
#!/usr/bin/env python3
"""Test individual specialized agents."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents import (
    create_graph_agent,
    create_analyzer_agent,
    create_extractor_agent,
    create_admin_agent
)
from dotenv import load_dotenv

load_dotenv()

def test_graph_agent():
    """Test Graph Agent."""
    print("\n" + "=" * 70)
    print("Testing Graph Agent")
    print("=" * 70)
    
    agent = create_graph_agent()
    
    queries = [
        "Find all people in Engineering",
        "Who reports to the CTO?",
        "List all systems owned by the Data team"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 70)
        try:
            response = agent(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_analyzer_agent():
    """Test Analyzer Agent."""
    print("\n" + "=" * 70)
    print("Testing Analyzer Agent")
    print("=" * 70)
    
    agent = create_analyzer_agent()
    
    queries = [
        "Who are the most central people in the organization?",
        "Detect communities in Engineering",
        "Calculate betweenness centrality for all people"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 70)
        try:
            response = agent(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_extractor_agent():
    """Test Extractor Agent (requires extractor role)."""
    print("\n" + "=" * 70)
    print("Testing Extractor Agent")
    print("=" * 70)
    
    agent = create_extractor_agent()
    
    queries = [
        "Create a person: Test User, Engineer, Data team",
        "Add relationship: Test User REPORTS_TO Alice Johnson"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 70)
        try:
            response = agent(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def main():
    print("Strands Agents - Specialized Agent Testing")
    print("=" * 70)
    
    test_graph_agent()
    test_analyzer_agent()
    
    # Uncomment if you have extractor permissions
    # test_extractor_agent()

if __name__ == "__main__":
    main()
EOF

chmod +x test_specialized_agents.py
python3 test_specialized_agents.py
```

### Test 3: Run Example Scripts

```bash
# Run basic usage examples
python3 examples/basic_usage.py
```

---

## AgentCore Memory Setup

For production-ready testing with conversation memory and context management.

### Step 1: Install AgentCore SDK

```bash
pip install bedrock-agentcore
```

### Step 2: Create Memory Resources

```bash
# Run the memory setup script
python3 examples/setup_agentcore_memory.py
```

**Expected Output:**
```
======================================================================
AgentCore Memory Setup for Orchestrator Agent
======================================================================

Creating Short-Term Memory (STM)...
  Purpose: Stores raw conversation turns within a session
  Retention: 30 days

✅ STM Created: mem_abc123xyz
   Name: OrgGraph_STM_abc12345

Creating Long-Term Memory (LTM)...
  Purpose: Extracts preferences and facts across sessions
  Retention: 180 days

✅ LTM Created: mem_def456uvw
   Name: OrgGraph_LTM_def45678

======================================================================
Setup Complete! Choose which memory to use:
======================================================================

For SESSION-BASED MEMORY (remembers within session only):
  export MEMORY_ID=mem_abc123xyz

For CROSS-SESSION MEMORY (remembers preferences across sessions):
  export MEMORY_ID=mem_def456uvw
```

### Step 3: Set Memory ID

Choose STM for testing, LTM for production:

```bash
# For testing (Short-Term Memory)
export MEMORY_ID=mem_abc123xyz  # Replace with your actual STM ID

# Or add to .env file
echo "MEMORY_ID=mem_abc123xyz" >> .env
```

### Step 4: Test Local Memory Integration

```bash
# Create test script with memory
cat > test_orchestrator_with_memory.py << 'EOF'
#!/usr/bin/env python3
"""Test orchestrator with AgentCore Memory locally."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.orchestrator_agent_agentcore import create_orchestrator_with_agentcore
from bedrock_agentcore.memory import MemoryClient
from dotenv import load_dotenv

load_dotenv()

def main():
    memory_id = os.getenv('MEMORY_ID')
    if not memory_id:
        print("❌ Error: MEMORY_ID not set in environment")
        print("Run: export MEMORY_ID=<your-memory-id>")
        return
    
    print("=" * 70)
    print("Orchestrator with AgentCore Memory - Local Test")
    print("=" * 70)
    print(f"Memory ID: {memory_id}")
    print()
    
    # Create memory client
    memory_client = MemoryClient(region_name=os.getenv('AWS_REGION', 'us-west-2'))
    
    # Create orchestrator with memory
    print("Creating orchestrator with memory integration...")
    orchestrator = create_orchestrator_with_agentcore(
        user_role="user",
        memory_client=memory_client,
        memory_id=memory_id,
        session_id="cli-test-session"
    )
    print("✓ Orchestrator created with memory")
    print()
    
    # Test conversation with memory
    print("Testing conversation memory...")
    print("-" * 70)
    
    # First message
    print("\nYou: My name is Alice and I work in Engineering")
    response = orchestrator("My name is Alice and I work in Engineering")
    print(f"Orchestrator: {response}")
    
    # Second message - should remember name
    print("\nYou: What's my name?")
    response = orchestrator("What's my name?")
    print(f"Orchestrator: {response}")
    
    print("\n" + "=" * 70)
    print("✓ Memory test complete")

if __name__ == "__main__":
    main()
EOF

chmod +x test_orchestrator_with_memory.py
python3 test_orchestrator_with_memory.py
```

---

## AgentCore Deployment

Deploy the orchestrator to AWS Bedrock AgentCore Runtime for production testing.

### Step 1: Configure Deployment

```bash
cd strands_agents

# Configure the deployment
agentcore configure --entrypoint examples/agentcore_deployment_handler.py
```

**You'll be prompted for:**
- Application name: `interlinked-orchestrator`
- Description: `Organizational graph orchestrator agent`
- AWS region: `us-west-2`

### Step 2: Set Required Environment Variables

```bash
# Required for deployment
export MEMORY_ID=<your-memory-id-from-setup>
export AWS_REGION=us-west-2
export NEO4J_URI=<your-neo4j-uri>
export NEO4J_USERNAME=<username>
export NEO4J_PASSWORD=<password>
export USER_ROLE=user
```

### Step 3: Deploy to AgentCore

```bash
# Launch the deployment
agentcore launch
```

**Expected Output:**
```
Building container image...
Pushing to AWS ECR...
Creating IAM roles...
Deploying to AgentCore Runtime...
✓ Deployment successful

Agent URL: https://abc123.agentcore.us-west-2.amazonaws.com
Session Management: Enabled
Memory Integration: Active
```

### Step 4: Test Deployed Agent

```bash
# Single query test
agentcore invoke '{"prompt": "Who are the people in Engineering?"}' --session-id test-session-1

# Test conversation memory
agentcore invoke '{"prompt": "My name is Bob"}' --session-id bob-session

agentcore invoke '{"prompt": "What is my name?"}' --session-id bob-session

# Test cross-session memory (if using LTM)
agentcore invoke '{"prompt": "What are my preferences?"}' --session-id different-session
```

### Step 5: View Logs

```bash
# Tail logs in real-time
agentcore logs --tail

# Filter by log level
agentcore logs --filter-level ERROR

# View specific time range
agentcore logs --start-time "2024-01-01T00:00:00" --end-time "2024-01-02T00:00:00"
```

### Step 6: Monitor Performance

```bash
# View CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/AgentCore \
  --metric-name Invocations \
  --dimensions Name=AgentName,Value=interlinked-orchestrator \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-2
```

---

## Testing Scenarios

### Scenario 1: Basic Graph Queries

```bash
# Test reading data
agentcore invoke '{"prompt": "List all people in the Engineering department"}' --session-id test-1

agentcore invoke '{"prompt": "Who reports to Alice Johnson?"}' --session-id test-1

agentcore invoke '{"prompt": "What processes does the Data team own?"}' --session-id test-1
```

### Scenario 2: Analytical Queries

```bash
# Test analytics
agentcore invoke '{"prompt": "Who are the most influential people in the organization?"}' --session-id test-2

agentcore invoke '{"prompt": "Detect communities in our Engineering department"}' --session-id test-2

agentcore invoke '{"prompt": "Find organizational bottlenecks and suggest improvements"}' --session-id test-2
```

### Scenario 3: Multi-Agent Coordination

```bash
# Test complex query requiring multiple agents
agentcore invoke '{"prompt": "Find the most central person in Engineering, then show all processes they influence"}' --session-id test-3
```

### Scenario 4: Conversation Memory

```bash
# Test session-based memory
agentcore invoke '{"prompt": "My name is Charlie and I prefer detailed technical explanations"}' --session-id charlie-test

agentcore invoke '{"prompt": "Who are the engineers?"}' --session-id charlie-test

agentcore invoke '{"prompt": "Remember my communication style in future responses"}' --session-id charlie-test
```

### Scenario 5: Error Handling

```bash
# Test permission errors
agentcore invoke '{"prompt": "Delete all data in the database"}' --session-id test-4

# Test invalid queries
agentcore invoke '{"prompt": "Show me purple elephants"}' --session-id test-4

# Test timeout scenarios
agentcore invoke '{"prompt": "Run a very complex analysis on the entire graph"}' --session-id test-4
```

---

## Troubleshooting

### Issue 1: Import Errors

**Problem:** `ModuleNotFoundError: No module named 'strands'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep strands
```

### Issue 2: AWS Credentials

**Problem:** `UnauthorizedOperation` or `NoCredentialsError`

**Solution:**
```bash
# Verify credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure

# Check profile
echo $AWS_PROFILE
```

### Issue 3: Neo4j Connection

**Problem:** `ServiceUnavailable: Failed to establish connection`

**Solution:**
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

# Check .env file
cat .env | grep NEO4J
```

### Issue 4: AgentCore Memory Not Working

**Problem:** Agent doesn't remember previous conversations

**Solution:**
```bash
# Verify MEMORY_ID is set
echo $MEMORY_ID

# List memory resources
aws bedrock-agent-runtime list-memories --region us-west-2

# Check memory events
aws bedrock-agent-runtime list-memory-events \
  --memory-id $MEMORY_ID \
  --region us-west-2
```

### Issue 5: Bedrock Model Access

**Problem:** `AccessDeniedException` when calling Bedrock

**Solution:**
```bash
# Verify model access
aws bedrock list-foundation-models \
  --region us-west-2 \
  --query "modelSummaries[?modelId=='anthropic.claude-3-5-sonnet-20241022-v2:0']"

# Check IAM permissions
aws iam get-user
```

### Issue 6: Deployment Failures

**Problem:** `agentcore launch` fails

**Solution:**
```bash
# Check CloudFormation stacks
aws cloudformation list-stacks \
  --region us-west-2 \
  --query "StackSummaries[?contains(StackName, 'agentcore')]"

# View stack events
aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region us-west-2

# Delete failed stack and retry
aws cloudformation delete-stack \
  --stack-name <stack-name> \
  --region us-west-2
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set debug log level
export LOG_LEVEL=DEBUG

# Run with verbose output
python3 -u test_orchestrator_cli.py 2>&1 | tee debug.log

# For AgentCore
agentcore invoke '{"prompt": "test"}' --debug
```

---

## Best Practices

### 1. Session Management

```bash
# Use meaningful session IDs
agentcore invoke '{"prompt": "query"}' --session-id "user-alice-$(date +%Y%m%d)"

# Separate sessions for different users/contexts
agentcore invoke '{"prompt": "query"}' --session-id "engineering-analysis"
agentcore invoke '{"prompt": "query"}' --session-id "data-analysis"
```

### 2. Error Handling

Always wrap production calls in error handling:

```bash
if agentcore invoke '{"prompt": "query"}' --session-id test; then
    echo "✓ Success"
else
    echo "❌ Failed"
    agentcore logs --tail -n 50
fi
```

### 3. Performance Testing

```bash
# Measure response time
time agentcore invoke '{"prompt": "Who are the engineers?"}' --session-id perf-test

# Concurrent testing
for i in {1..10}; do
    agentcore invoke '{"prompt": "test query"}' --session-id "concurrent-$i" &
done
wait
```

### 4. Cost Optimization

- Use STM for development (faster, cheaper)
- Use LTM for production (better context)
- Monitor CloudWatch metrics for usage
- Set up billing alerts

---

## Next Steps

After successful CLI testing:

1. ✅ **Verify all test scenarios pass**
2. ✅ **Review logs for any warnings/errors**
3. ✅ **Test with real organizational data**
4. ✅ **Set up monitoring dashboards**
5. ✅ **Integrate with frontend application**
6. ✅ **Deploy to production environment**

---

## Additional Resources

- [Strands Agents Documentation](https://strandsagents.com/latest/documentation/)
- [AWS Bedrock AgentCore Docs](https://aws.github.io/bedrock-agentcore-starter-toolkit/)
- [AgentCore Memory Guide](agentcore-orchestration.md)
- [Performance Optimization](performance-optimization.md)
- [AWS Setup Guide](aws-setup.md)

---

**Need Help?**

- Check the [Troubleshooting](#troubleshooting) section
- Review agent logs: `agentcore logs --tail`
- Verify environment: `env | grep -E '(AWS|NEO4J|MEMORY)'`
- Test connectivity: Run all verification commands from Setup

