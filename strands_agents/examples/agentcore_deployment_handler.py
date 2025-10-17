"""
Example AgentCore Runtime deployment handler.

This file demonstrates how to deploy the orchestrator agent to AWS Bedrock AgentCore Runtime
with Memory integration for production use.

## Deployment Steps:

1. Set up Memory resource (run once):
   ```bash
   python examples/setup_agentcore_memory.py
   ```

2. Configure deployment:
   ```bash
   cd strands_agents
   agentcore configure --entrypoint examples/agentcore_deployment_handler.py
   ```

3. Set environment variables:
   ```bash
   export MEMORY_ID=<your-memory-id-from-step-1>
   export AWS_REGION=us-west-2
   export NEO4J_URI=<your-neo4j-uri>
   export NEO4J_USERNAME=<username>
   export NEO4J_PASSWORD=<password>
   ```

4. Deploy to AgentCore Runtime:
   ```bash
   agentcore launch
   ```

5. Test the deployed agent:
   ```bash
   agentcore invoke '{"prompt": "Who are the key people in Engineering?"}' --session-id user-session-123
   ```

## Features:
- Automatic conversation history management via AgentCore Memory
- Session isolation for multi-user scenarios
- Secure deployment on AWS infrastructure
- Automatic scaling based on demand
- Integration with AgentCore Identity for authentication
"""

import os
from strands_agents.src.agents.orchestrator_agent_agentcore import create_agentcore_app

# Get configuration from environment variables
MEMORY_ID = os.getenv('MEMORY_ID')
USER_ROLE = os.getenv('USER_ROLE', 'user')  # Can be: user, extractor, admin

# Create the AgentCore application
# This handles all the orchestration, memory management, and session handling
app = create_agentcore_app(
    user_role=USER_ROLE,
    memory_id=MEMORY_ID
)

# The app is now ready for deployment
# AgentCore CLI will handle containerization, deployment, and scaling

if __name__ == "__main__":
    # For local testing (before deployment)
    print("AgentCore application configured successfully!")
    print(f"Memory ID: {MEMORY_ID or 'Not configured'}")
    print(f"User Role: {USER_ROLE}")
    print("\nTo deploy:")
    print("1. agentcore configure --entrypoint examples/agentcore_deployment_handler.py")
    print("2. agentcore launch")
    print("\nTo test locally:")
    print("app.run()  # Starts local development server")

