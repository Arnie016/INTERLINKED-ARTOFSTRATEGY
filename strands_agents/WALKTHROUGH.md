# Complete CLI Testing Walkthrough

**Follow these exact steps to test the orchestrator agent from the command line.**

## 📋 Prerequisites Checklist

Before starting, verify you have:

- [ ] Python 3.11+ installed
- [ ] AWS CLI v2 installed and configured
- [ ] AWS Bedrock access enabled in your account
- [ ] Neo4j instance running (Aura or local) with test data
- [ ] Your AWS credentials configured (`aws configure`)
- [ ] Terminal/shell access

---

## 🚀 Part 1: Local Development Testing (15 minutes)

### Step 1: Setup Environment

```bash
# Navigate to the strands_agents directory
cd /Users/stefn/Interlinked/AWS\ Hackathon/INTERLINKED-ARTOFSTRATEGY/strands_agents

# Run the automated setup script
./setup.sh

# Expected output:
# ✓ Python version OK
# ✓ AWS CLI installed
# ✓ AWS credentials configured
# ✓ Virtual environment created
# ✓ Dependencies installed
# ✓ .env file created from template
```

### Step 2: Configure Environment Variables

```bash
# Copy the environment template
cp env.template .env

# Edit .env with your credentials (use your preferred editor)
nano .env

# Required changes:
# 1. NEO4J_URI=neo4j+s://your-actual-instance.databases.neo4j.io
# 2. NEO4J_USERNAME=neo4j
# 3. NEO4J_PASSWORD=your-actual-password
# 4. AWS_REGION=us-west-2

# Save and exit (Ctrl+X, Y, Enter for nano)
```

### Step 3: Activate Virtual Environment

```bash
# Activate the virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
# Example: (venv) user@machine:~/strands_agents$
```

### Step 4: Verify Setup

```bash
# Test Python imports
python3 -c "import boto3; import neo4j; from strands import Agent; print('✓ All imports successful')"

# Expected output: ✓ All imports successful

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

# Expected output: ✓ Neo4j connection successful

# Verify AWS credentials
aws sts get-caller-identity

# Expected output: Your AWS account details (Account, UserId, Arn)
```

### Step 5: Run Automated Tests

```bash
# Run the automated test suite (local tests only)
./run_cli_tests.sh --local

# Expected output:
# ========================================
# Pre-flight Checks
# ========================================
# ✓ Python version: 3.11.x
# ✓ Virtual environment activated
# ✓ .env file exists
# ✓ Required environment variables set
# ✓ AWS credentials configured
# ✓ Python dependencies installed
# ✓ Neo4j connection successful
# ✓ All pre-flight checks passed!
#
# ========================================
# Local Orchestrator Testing
# ========================================
# Test 1: Creating orchestrator agent...
# ✓ Orchestrator created
# Test 2: Testing simple query...
# ✓ Simple query executed
# Test 3: Testing specialized agents...
# ✓ Specialized agents working
# Test 4: Running basic usage example...
# ✓ Basic usage example completed
# ✓ Local testing completed!
```

### Step 6: Interactive Testing

```bash
# Start interactive CLI mode
./run_cli_tests.sh --interactive

# You should see:
# ========================================
# Interactive Testing Mode
# ========================================
# Creating orchestrator...
# ✓ Ready!
# ----------------------------------------------------------------------
#
# You:
```

**Try these queries:**

```
Who are all the people in Engineering?
```

```
Find the most influential people in the organization
```

```
What processes does the Data team own?
```

```
Detect communities in our organization
```

```
exit
```

### Step 7: Run Example Scripts

```bash
# Run the basic usage examples
python3 examples/basic_usage.py

# Expected output: Multiple example scenarios demonstrating agent capabilities
```

---

## ☁️ Part 2: AgentCore Production Testing (30 minutes)

### Step 8: Install AgentCore CLI

```bash
# Install AWS Bedrock AgentCore CLI
pip install bedrock-agentcore

# Verify installation
agentcore --version

# Expected output: agentcore version x.x.x
```

### Step 9: Create Memory Resources

```bash
# Run the memory setup script
python3 examples/setup_agentcore_memory.py

# Expected output:
# ======================================================================
# AgentCore Memory Setup for Orchestrator Agent
# ======================================================================
#
# Creating Short-Term Memory (STM)...
#   Purpose: Stores raw conversation turns within a session
#   Retention: 30 days
#
# ✅ STM Created: mem_abc123xyz
#    Name: OrgGraph_STM_abc12345
#
# Creating Long-Term Memory (LTM)...
#   Purpose: Extracts preferences and facts across sessions
#   Retention: 180 days
#
# ✅ LTM Created: mem_def456uvw
#    Name: OrgGraph_LTM_def45678
#
# ======================================================================
# Setup Complete! Choose which memory to use:
# ======================================================================
#
# For SESSION-BASED MEMORY (remembers within session only):
#   export MEMORY_ID=mem_abc123xyz
#
# For CROSS-SESSION MEMORY (remembers preferences across sessions):
#   export MEMORY_ID=mem_def456uvw

# Copy the STM MEMORY_ID for testing
```

### Step 10: Configure Memory

```bash
# Set the MEMORY_ID environment variable (use STM for testing)
export MEMORY_ID=mem_abc123xyz  # Replace with your actual STM ID

# Add to .env file for persistence
echo "MEMORY_ID=$MEMORY_ID" >> .env

# Verify it's set
echo $MEMORY_ID

# Expected output: mem_abc123xyz (your actual ID)
```

### Step 11: Test Memory Integration Locally

```bash
# Create a test script
cat > test_memory_local.py << 'EOF'
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.agents.orchestrator_agent_agentcore import create_orchestrator_with_agentcore
from bedrock_agentcore.memory import MemoryClient
from dotenv import load_dotenv

load_dotenv()

memory_id = os.getenv('MEMORY_ID')
print(f"Testing with MEMORY_ID: {memory_id}\n")

memory_client = MemoryClient(region_name=os.getenv('AWS_REGION', 'us-west-2'))

orchestrator = create_orchestrator_with_agentcore(
    user_role="user",
    memory_client=memory_client,
    memory_id=memory_id,
    session_id="test-session-123"
)

# Test 1: Tell it something
print("Test 1: Setting context...")
print("You: My name is Alice and I prefer detailed technical explanations\n")
response = orchestrator("My name is Alice and I prefer detailed technical explanations")
print(f"Orchestrator: {response}\n")

# Test 2: Ask if it remembers
print("\nTest 2: Testing memory recall...")
print("You: What is my name?\n")
response = orchestrator("What is my name?")
print(f"Orchestrator: {response}\n")

# Test 3: Check preferences
print("\nTest 3: Testing preference memory...")
print("You: How should you communicate with me?\n")
response = orchestrator("How should you communicate with me?")
print(f"Orchestrator: {response}\n")

print("✓ Memory integration test complete!")
EOF

chmod +x test_memory_local.py

# Run the test
python3 test_memory_local.py

# Expected output:
# Testing with MEMORY_ID: mem_abc123xyz
#
# Test 1: Setting context...
# You: My name is Alice and I prefer detailed technical explanations
# Orchestrator: [acknowledges your name and preference]
#
# Test 2: Testing memory recall...
# You: What is my name?
# Orchestrator: Your name is Alice. [continues...]
#
# Test 3: Testing preference memory...
# You: How should you communicate with me?
# Orchestrator: You prefer detailed technical explanations. [continues...]
#
# ✓ Memory integration test complete!
```

### Step 12: Configure AgentCore Deployment

```bash
# Configure the deployment entrypoint
agentcore configure --entrypoint examples/agentcore_deployment_handler.py

# You'll be prompted for:
# Application name: interlinked-orchestrator
# Description: Organizational graph orchestrator agent
# AWS region: us-west-2
#
# Expected output:
# ✓ Configuration saved
```

### Step 13: Set Required Environment Variables

```bash
# Verify all required variables are set
export MEMORY_ID=mem_abc123xyz  # Your actual memory ID
export AWS_REGION=us-west-2
export NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_password
export USER_ROLE=user

# Verify they're all set
env | grep -E '(MEMORY_ID|AWS_REGION|NEO4J_URI|USER_ROLE)'

# Expected output: All variables displayed
```

### Step 14: Deploy to AgentCore

```bash
# Launch the deployment
agentcore launch

# This will:
# - Build a container image
# - Push to AWS ECR
# - Create IAM roles
# - Deploy to AgentCore Runtime
# - Configure auto-scaling
#
# Expected output (this takes 5-10 minutes):
# Building container image...
# Pushing to AWS ECR...
# Creating IAM roles...
# Deploying to AgentCore Runtime...
# ✓ Deployment successful
#
# Agent URL: https://abc123.agentcore.us-west-2.amazonaws.com
# Session Management: Enabled
# Memory Integration: Active
```

### Step 15: Test Deployed Agent

```bash
# Test 1: Simple query
agentcore invoke '{"prompt": "Who are the people in Engineering?"}' --session-id test-session-1

# Expected output: JSON response with agent's answer

# Test 2: Test conversation memory
agentcore invoke '{"prompt": "My name is Bob"}' --session-id bob-session

agentcore invoke '{"prompt": "What is my name?"}' --session-id bob-session

# Expected output: Agent should remember "Bob"

# Test 3: Complex analytical query
agentcore invoke '{"prompt": "Find the most influential people and show their key relationships"}' --session-id analysis-session

# Expected output: Detailed analysis with people and relationships
```

### Step 16: View Logs

```bash
# Tail logs in real-time
agentcore logs --tail

# Expected output: Live log stream showing:
# - Request details
# - Agent routing decisions
# - Tool invocations
# - Response generation
# - Memory operations

# Filter by log level
agentcore logs --filter-level ERROR

# View recent logs (last 50 lines)
agentcore logs --tail -n 50
```

### Step 17: Monitor Metrics

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

# Expected output: Invocation count statistics

# View latency metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/AgentCore \
  --metric-name Duration \
  --dimensions Name=AgentName,Value=interlinked-orchestrator \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region us-west-2

# Expected output: Average and max response times
```

---

## 🧪 Part 3: Comprehensive Testing Scenarios

### Test Scenario 1: Basic Graph Queries

```bash
# Query 1: List people
agentcore invoke '{"prompt": "List all people in the Engineering department"}' --session-id scenario1

# Query 2: Reporting structure
agentcore invoke '{"prompt": "Who reports to Alice Johnson?"}' --session-id scenario1

# Query 3: Process ownership
agentcore invoke '{"prompt": "What processes does the Data team own?"}' --session-id scenario1

# Query 4: System relationships
agentcore invoke '{"prompt": "Which systems are used by the Engineering team?"}' --session-id scenario1
```

### Test Scenario 2: Analytical Queries

```bash
# Query 1: Influence analysis
agentcore invoke '{"prompt": "Who are the most influential people in the organization?"}' --session-id scenario2

# Query 2: Community detection
agentcore invoke '{"prompt": "Detect communities in our Engineering department"}' --session-id scenario2

# Query 3: Bottleneck identification
agentcore invoke '{"prompt": "Find organizational bottlenecks and suggest improvements"}' --session-id scenario2

# Query 4: Centrality metrics
agentcore invoke '{"prompt": "Calculate betweenness centrality for all managers"}' --session-id scenario2
```

### Test Scenario 3: Multi-Agent Coordination

```bash
# Complex query requiring multiple agents
agentcore invoke '{"prompt": "Find the most central person in Engineering, show their direct reports, analyze their influence on processes, and suggest who could back them up"}' --session-id scenario3

# Expected: Orchestrator should:
# 1. Use analyzer_agent for centrality
# 2. Use graph_agent for relationships
# 3. Use analyzer_agent for influence
# 4. Synthesize recommendations
```

### Test Scenario 4: Conversation Memory

```bash
# Conversation 1: Set context
agentcore invoke '{"prompt": "My name is Charlie. I work in Data Science and prefer visual representations of data"}' --session-id charlie

# Conversation 2: Query with context
agentcore invoke '{"prompt": "Show me the organizational structure"}' --session-id charlie
# Expected: Response should reference name and preference

# Conversation 3: Follow-up
agentcore invoke '{"prompt": "What did I tell you about my preferences?"}' --session-id charlie
# Expected: Agent recalls visual preference

# Conversation 4: New session (if using LTM)
agentcore invoke '{"prompt": "What do you know about me?"}' --session-id charlie-new-session
# Expected with LTM: Agent remembers across sessions
```

### Test Scenario 5: Error Handling

```bash
# Test 1: Permission error
agentcore invoke '{"prompt": "Delete all data in the database"}' --session-id error-test
# Expected: Permission error, no data deleted

# Test 2: Invalid query
agentcore invoke '{"prompt": "Show me the purple elephants in our org"}' --session-id error-test
# Expected: Graceful error, helpful message

# Test 3: Ambiguous request
agentcore invoke '{"prompt": "Find John"}' --session-id error-test
# Expected: Clarifying questions (e.g., "Which John?")
```

---

## 📊 Part 4: Verification & Validation

### Verify All Components

```bash
# 1. Check agent is responding
agentcore invoke '{"prompt": "Hello"}' --session-id health-check
# Expected: Friendly response

# 2. Verify memory is working
agentcore invoke '{"prompt": "Remember: test passed"}' --session-id memory-check
agentcore invoke '{"prompt": "What should you remember?"}' --session-id memory-check
# Expected: Agent recalls "test passed"

# 3. Check Neo4j connectivity
agentcore invoke '{"prompt": "Count all people in the database"}' --session-id db-check
# Expected: Actual count from Neo4j

# 4. Verify logging
agentcore logs --tail -n 10
# Expected: Recent request logs

# 5. Check metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/AgentCore \
  --metric-name Invocations \
  --dimensions Name=AgentName,Value=interlinked-orchestrator \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum \
  --region us-west-2
# Expected: Non-zero invocation count
```

### Performance Baseline

```bash
# Test response time
time agentcore invoke '{"prompt": "Who are the engineers?"}' --session-id perf-test
# Expected: < 5 seconds

# Concurrent requests test
for i in {1..5}; do
    agentcore invoke '{"prompt": "List people"}' --session-id "concurrent-$i" &
done
wait
# Expected: All complete successfully
```

---

## ✅ Success Criteria

Your testing is successful if:

- [x] Local orchestrator creates without errors
- [x] All specialized agents respond correctly
- [x] Neo4j queries return actual data
- [x] AgentCore deployment completes successfully
- [x] Deployed agent responds to queries
- [x] Memory persists across conversation turns
- [x] Logs show structured output
- [x] Metrics appear in CloudWatch
- [x] Response times are < 5 seconds
- [x] Error handling is graceful

---

## 🐛 Troubleshooting

If something goes wrong, check:

```bash
# 1. Environment variables
env | grep -E '(AWS|NEO4J|MEMORY)'

# 2. AWS credentials
aws sts get-caller-identity

# 3. Neo4j connection
python3 -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✓ OK'); driver.close()"

# 4. Virtual environment
which python3  # Should show venv/bin/python3

# 5. Dependencies
pip list | grep -E '(strands|boto3|neo4j)'

# 6. Logs (if deployed)
agentcore logs --tail -n 100

# 7. CloudFormation stacks (if deployment failed)
aws cloudformation list-stacks --region us-west-2 --query "StackSummaries[?contains(StackName, 'agentcore')]"
```

For detailed troubleshooting, see: [docs/guides/CLI_TESTING_GUIDE.md](docs/guides/CLI_TESTING_GUIDE.md)

---

## 📚 Next Steps

After completing this walkthrough:

1. **Review Documentation**
   - [CLI Testing Guide](docs/guides/CLI_TESTING_GUIDE.md)
   - [AgentCore Orchestration](docs/guides/agentcore-orchestration.md)
   - [Architecture Overview](docs/architecture/overview.md)

2. **Integrate with Frontend**
   - Test API endpoints
   - Configure authentication
   - Set up WebSocket for streaming

3. **Production Deployment**
   - Switch to LTM for memory
   - Configure monitoring dashboards
   - Set up billing alerts
   - Enable WAF and security groups

4. **Performance Optimization**
   - Review [Performance Guide](docs/guides/performance-optimization.md)
   - Tune connection pools
   - Configure caching
   - Optimize Neo4j indexes

---

**🎉 Congratulations!** You've successfully tested the orchestrator agent via CLI in both local and production environments using Strands Agents and AWS Bedrock AgentCore best practices.

