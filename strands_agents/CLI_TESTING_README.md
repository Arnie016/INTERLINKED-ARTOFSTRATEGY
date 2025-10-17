# CLI Testing Documentation

Complete documentation for testing the Strands Agents orchestrator via command line interface.

## 📚 Documentation Index

### Quick Start
- **[CLI_QUICKSTART.md](CLI_QUICKSTART.md)** - Get testing in 5 minutes
- **[WALKTHROUGH.md](WALKTHROUGH.md)** - Complete step-by-step guide with exact commands

### Comprehensive Guide
- **[docs/guides/CLI_TESTING_GUIDE.md](docs/guides/CLI_TESTING_GUIDE.md)** - Full testing guide with scenarios and troubleshooting

### Configuration
- **[env.template](env.template)** - Environment variables template

### Automation
- **[run_cli_tests.sh](run_cli_tests.sh)** - Automated testing script

---

## 🎯 Choose Your Path

### Path 1: Quick Test (5 minutes)
**For:** Rapid functionality check

```bash
# 1. Setup
./setup.sh
source venv/bin/activate

# 2. Configure
cp env.template .env
# Edit .env with your credentials

# 3. Test
./run_cli_tests.sh --local
```

**See:** [CLI_QUICKSTART.md](CLI_QUICKSTART.md)

---

### Path 2: Interactive Testing (15 minutes)
**For:** Manual exploration and testing

```bash
# 1. Setup (if not done)
./setup.sh
source venv/bin/activate

# 2. Start interactive CLI
./run_cli_tests.sh --interactive

# 3. Try queries
# "Who are the people in Engineering?"
# "Find the most influential people"
# "Detect communities"
```

**See:** [CLI_QUICKSTART.md](CLI_QUICKSTART.md#-interactive-cli-test)

---

### Path 3: Complete Walkthrough (45 minutes)
**For:** Full testing including AgentCore deployment

**Covers:**
- ✅ Local development testing
- ✅ AgentCore Memory setup
- ✅ Production deployment
- ✅ Comprehensive test scenarios
- ✅ Monitoring and metrics

**See:** [WALKTHROUGH.md](WALKTHROUGH.md)

---

### Path 4: Production Deployment (30 minutes)
**For:** Deploying to AWS Bedrock AgentCore

```bash
# 1. Create memory resources
python3 examples/setup_agentcore_memory.py

# 2. Configure
export MEMORY_ID=<your-memory-id>
agentcore configure --entrypoint examples/agentcore_deployment_handler.py

# 3. Deploy
agentcore launch

# 4. Test
agentcore invoke '{"prompt": "test"}' --session-id test-1
```

**See:** [WALKTHROUGH.md](WALKTHROUGH.md#%EF%B8%8F-part-2-agentcore-production-testing-30-minutes)

---

## 🛠️ Automated Testing Script

The `run_cli_tests.sh` script provides automated testing:

### Usage

```bash
# Local testing only (default)
./run_cli_tests.sh --local

# AgentCore deployment testing
./run_cli_tests.sh --agentcore

# All tests
./run_cli_tests.sh --all

# Interactive mode
./run_cli_tests.sh --interactive

# Help
./run_cli_tests.sh --help
```

### What it does

**Pre-flight checks:**
- ✅ Verifies Python 3.11+
- ✅ Checks virtual environment
- ✅ Validates .env configuration
- ✅ Tests AWS credentials
- ✅ Verifies Neo4j connectivity
- ✅ Confirms dependencies installed

**Local testing:**
- ✅ Creates orchestrator agent
- ✅ Runs simple queries
- ✅ Tests specialized agents
- ✅ Executes example scripts

**AgentCore testing:**
- ✅ Installs AgentCore CLI
- ✅ Sets up memory resources
- ✅ Tests memory integration
- ✅ Deploys to AgentCore Runtime
- ✅ Validates deployment
- ✅ Shows logs and metrics

---

## 📋 Prerequisites

### Required
- Python 3.11+
- AWS CLI v2
- AWS account with Bedrock access
- Neo4j instance (Aura or local)
- AWS credentials configured

### Optional (for AgentCore)
- AWS Bedrock AgentCore access
- IAM permissions for Lambda, API Gateway, CloudWatch

### Verification

```bash
# Check all prerequisites
python3 --version           # 3.11+
aws --version               # 2.x
aws sts get-caller-identity # Verify credentials
```

---

## 🔧 Configuration

### Environment Variables

Copy `env.template` to `.env` and configure:

```bash
# Required
AWS_REGION=us-west-2
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# Optional (for AgentCore)
MEMORY_ID=mem_abc123xyz
USER_ROLE=user
```

**Full template:** [env.template](env.template)

---

## 🧪 Test Scenarios

### 1. Basic Graph Queries
- List people by department
- Query reporting structures
- Find process ownership
- Explore system relationships

### 2. Analytical Queries
- Influence analysis
- Community detection
- Bottleneck identification
- Centrality metrics

### 3. Multi-Agent Coordination
- Complex queries requiring multiple agents
- Context flow between agents
- Result synthesis

### 4. Conversation Memory
- Session-based memory
- Cross-session preferences (LTM)
- Context persistence

### 5. Error Handling
- Permission errors
- Invalid queries
- Timeout scenarios
- Graceful degradation

**Detailed scenarios:** [CLI_TESTING_GUIDE.md](docs/guides/CLI_TESTING_GUIDE.md#testing-scenarios)

---

## 📊 Monitoring & Validation

### Local Testing

```bash
# View logs
tail -f logs/*.log

# Check test outputs
cat /tmp/test*.log
```

### AgentCore Deployment

```bash
# Live logs
agentcore logs --tail

# Metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/AgentCore \
  --metric-name Invocations \
  --region us-west-2

# List deployments
agentcore list
```

---

## 🐛 Troubleshooting

### Common Issues

**Import errors:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**AWS credentials:**
```bash
aws configure
aws sts get-caller-identity
```

**Neo4j connection:**
```bash
cat .env | grep NEO4J
# Verify credentials are correct
```

**AgentCore deployment fails:**
```bash
agentcore logs --tail
aws cloudformation describe-stacks --region us-west-2
```

**Full troubleshooting:** [CLI_TESTING_GUIDE.md](docs/guides/CLI_TESTING_GUIDE.md#troubleshooting)

---

## 📚 Additional Resources

### Documentation
- [Architecture Overview](docs/architecture/overview.md)
- [AgentCore Orchestration](docs/guides/agentcore-orchestration.md)
- [AWS Setup Guide](docs/guides/aws-setup.md)
- [Neo4j Setup Guide](docs/guides/neo4j-setup.md)
- [Performance Optimization](docs/guides/performance-optimization.md)

### External Resources
- [Strands Agents Documentation](https://strandsagents.com/latest/documentation/)
- [AWS Bedrock AgentCore](https://aws.github.io/bedrock-agentcore-starter-toolkit/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)

### Examples
- [examples/basic_usage.py](examples/basic_usage.py) - Basic agent usage
- [examples/setup_agentcore_memory.py](examples/setup_agentcore_memory.py) - Memory setup
- [examples/agentcore_deployment_handler.py](examples/agentcore_deployment_handler.py) - Deployment handler

---

## ✅ Success Criteria

Your CLI testing is successful when:

- [ ] Local orchestrator creates and responds
- [ ] All specialized agents work correctly
- [ ] Neo4j queries return real data
- [ ] AgentCore deployment completes (if testing)
- [ ] Memory persists across turns
- [ ] Logs show structured output
- [ ] Response times are acceptable (< 5s)
- [ ] Error handling is graceful
- [ ] Metrics appear in CloudWatch (if deployed)

---

## 🚀 Next Steps

After successful CLI testing:

1. **Integration Testing**
   - Test with frontend application
   - Verify API endpoints
   - Configure authentication

2. **Performance Testing**
   - Measure response times
   - Test concurrent requests
   - Optimize as needed

3. **Production Deployment**
   - Switch to LTM for memory
   - Configure monitoring
   - Set up alerts
   - Enable security features

4. **Documentation**
   - Document custom queries
   - Create runbooks
   - Train team members

---

## 💡 Tips & Best Practices

### Development
- Use STM for faster development iterations
- Enable DEBUG logging for troubleshooting
- Test with small datasets first

### Testing
- Use meaningful session IDs
- Test error scenarios thoroughly
- Verify logs after each test

### Production
- Use LTM for better context
- Monitor CloudWatch metrics
- Set up billing alerts
- Implement proper error handling

### Performance
- Optimize Neo4j indexes
- Configure connection pooling
- Cache frequently accessed data
- Monitor response times

---

**Questions or Issues?**

- Check [Troubleshooting Section](#-troubleshooting)
- Review [Full Testing Guide](docs/guides/CLI_TESTING_GUIDE.md)
- Examine logs: `agentcore logs --tail`
- Verify configuration: `env | grep -E '(AWS|NEO4J|MEMORY)'`

---

**Happy Testing! 🎉**

For the quickest start, run:
```bash
./run_cli_tests.sh --interactive
```

