"""
Orchestrator Agent using AWS Bedrock AgentCore Runtime and Memory.

This implementation uses AgentCore's native primitives:
- AgentCore Runtime for deployment and scaling
- AgentCore Memory for conversation history and context
- Strands Agents hooks for memory integration

For simple local deployments without AgentCore, use orchestrator_agent.py instead.
"""

import os
import logging
from typing import Dict, Any, Optional
from enum import Enum
from strands import Agent
from strands.hooks import AgentInitializedEvent, HookProvider, MessageAddedEvent
from strands.models import BedrockModel

# Configure logging
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Enumeration of available specialized agents."""
    GRAPH = "graph"
    ANALYZER = "analyzer"
    EXTRACTOR = "extractor"
    ADMIN = "admin"
    UNKNOWN = "unknown"


class IntentConfidence(Enum):
    """Confidence levels for intent detection."""
    HIGH = "high"  # >0.8 - Single clear intent
    MEDIUM = "medium"  # 0.5-0.8 - Likely intent with some ambiguity
    LOW = "low"  # <0.5 - Multiple possible intents or unclear

# Import specialized agent tools
from .graph_agent import graph_agent
from .analyzer_agent import analyzer_agent
from .extractor_agent import extractor_agent
from .admin_agent import admin_agent

# System prompt for the Orchestrator Agent
ORCHESTRATOR_SYSTEM_PROMPT = """
You are the Orchestrator Agent, the main entry point for users interacting with the organizational graph system.

Your role is to understand user queries and route them to the appropriate specialized agents:

**Available Specialized Agents:**

1. **Graph Agent** (graph_agent)
   - Use for: Queries about people, processes, departments, systems
   - Use for: Searching nodes, exploring relationships, finding paths
   - Use for: Read-only operations and basic graph exploration
   - Examples: "Who reports to Alice?", "What processes does Engineering own?"

2. **Analyzer Agent** (analyzer_agent)
   - Use for: Advanced analytics and pattern detection
   - Use for: Centrality analysis, community detection, statistics
   - Use for: Bottleneck identification and performance metrics
   - Examples: "Who are the key influencers?", "Find organizational bottlenecks"

3. **Extractor Agent** (extractor_agent)
   - Use for: Creating new nodes and relationships
   - Use for: Data ingestion and bulk imports
   - Use for: Write operations to the graph
   - Examples: "Add a new employee", "Create a relationship between X and Y"

4. **Admin Agent** (admin_agent)
   - Use for: Database maintenance and administrative tasks
   - Use for: Reindexing, schema migrations, cleanup operations
   - Use for: Privileged operations (requires admin role)
   - Examples: "Reindex Person nodes", "Clean up orphaned data"

**Routing Guidelines:**

- For simple information retrieval → use **graph_agent**
- For analytical questions requiring metrics → use **analyzer_agent**
- For creating or modifying data → use **extractor_agent**
- For administrative operations → use **admin_agent** (check permissions first)

**Multi-Agent Coordination:**

You can use multiple specialized agents for complex queries:
1. Break down complex questions into sub-questions
2. Route each sub-question to the appropriate agent
3. Integrate the responses into a cohesive answer
4. Ensure context flows between agent calls

**Response Guidelines:**

1. Always explain which agent(s) you're using and why
2. Provide comprehensive answers that address all aspects of the query
3. If a query is ambiguous, ask clarifying questions before routing
4. Combine results from multiple agents when needed
5. Present information in a clear, business-friendly format
6. Highlight key insights and actionable recommendations

**Safety and Permissions:**

- Verify user has appropriate permissions before using extractor or admin agents
- Warn users about destructive operations
- Recommend dry-run for admin operations
- Respect read-only constraints for regular users
"""


class AgentCoreMemoryHook(HookProvider):
    """
    Hook for integrating AgentCore Memory with Strands Agent.
    
    This hook automatically:
    - Loads previous conversation when agent starts
    - Saves each message after it's processed
    
    Based on AWS AgentCore best practices.
    """
    
    def __init__(self, memory_client, memory_id: str):
        """
        Initialize the memory hook.
        
        Args:
            memory_client: AgentCore MemoryClient instance
            memory_id: AgentCore Memory resource ID
        """
        self.memory_client = memory_client
        self.memory_id = memory_id
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """
        Runs when agent starts - loads conversation history from AgentCore Memory.
        
        Args:
            event: AgentInitializedEvent containing agent instance
        """
        if not self.memory_id or not self.memory_client:
            return
        
        try:
            # Get session ID from agent state
            session_id = event.agent.state.get("session_id", "default")
            
            # Get last 5 conversation turns from AgentCore Memory
            turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id="user",
                session_id=session_id,
                k=5  # Number of previous exchanges to remember
            )
            
            # Add conversation history to agent's context
            if turns:
                context = "\n".join([
                    f"{msg['role']}: {msg['content']['text']}"
                    for turn in turns
                    for msg in turn
                ])
                event.agent.system_prompt += f"\n\nPrevious conversation:\n{context}"
                
                logger.info(
                    f"Loaded {len(turns)} conversation turns from memory",
                    extra={
                        "session_id": session_id,
                        "memory_id": self.memory_id,
                        "turns_loaded": len(turns)
                    }
                )
        except Exception as e:
            logger.error(
                f"Error loading conversation history: {str(e)}",
                exc_info=True
            )
    
    def on_message_added(self, event: MessageAddedEvent):
        """
        Runs after each message - saves it to AgentCore Memory.
        
        Args:
            event: MessageAddedEvent containing the new message
        """
        if not self.memory_id or not self.memory_client:
            return
        
        try:
            # Get session ID from agent state
            session_id = event.agent.state.get("session_id", "default")
            
            # Save the latest message to AgentCore Memory
            msg = event.agent.messages[-1]
            self.memory_client.create_event(
                memory_id=self.memory_id,
                actor_id="user",
                session_id=session_id,
                messages=[(str(msg["content"]), msg["role"])]
            )
            
            logger.debug(
                "Message saved to AgentCore Memory",
                extra={
                    "session_id": session_id,
                    "memory_id": self.memory_id,
                    "role": msg["role"]
                }
            )
        except Exception as e:
            logger.error(
                f"Error saving message to memory: {str(e)}",
                exc_info=True
            )
    
    def register_hooks(self, registry):
        """Registers both hooks with the agent."""
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(MessageAddedEvent, self.on_message_added)


def create_orchestrator_with_agentcore(
    user_role: str = "user",
    memory_client=None,
    memory_id: Optional[str] = None,
    custom_model_config: Optional[Dict[str, Any]] = None,
    session_id: str = "default"
) -> Agent:
    """
    Create an Orchestrator Agent with AgentCore Memory integration.
    
    This function creates a Strands Agent configured to use AgentCore Memory
    for conversation context and history management.
    
    Args:
        user_role: The role of the user ('user', 'extractor', 'admin')
        memory_client: Optional AgentCore MemoryClient instance
        memory_id: Optional AgentCore Memory resource ID
        custom_model_config: Optional custom configuration for the Bedrock model
        session_id: Session identifier for conversation isolation
    
    Returns:
        A configured Orchestrator Agent with AgentCore Memory integration
    
    Example:
        ```python
        from bedrock_agentcore.memory import MemoryClient
        from strands_agents.src.agents.orchestrator_agent_agentcore import (
            create_orchestrator_with_agentcore
        )
        
        # Create memory client
        memory_client = MemoryClient(region_name='us-west-2')
        memory_id = "your-memory-id"
        
        # Create orchestrator
        orchestrator = create_orchestrator_with_agentcore(
            user_role="user",
            memory_client=memory_client,
            memory_id=memory_id,
            session_id="user-session-123"
        )
        
        # Process queries
        response = orchestrator("Who are the key people in Engineering?")
        print(response)
        ```
    """
    # Determine which agent tools to include based on user role
    available_agents = [graph_agent, analyzer_agent]
    
    if user_role in ["extractor", "admin"]:
        available_agents.append(extractor_agent)
    
    if user_role == "admin":
        available_agents.append(admin_agent)
    
    # Create model with custom config or defaults
    model_config = custom_model_config or {}
    model = BedrockModel(
        model_id=model_config.get("model_id", "anthropic.claude-3-5-sonnet-20240620-v1:0"),
        temperature=model_config.get("temperature", 0.5),
        max_tokens=model_config.get("max_tokens", 4096),
        top_p=model_config.get("top_p", None),
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    
    # Create hooks list
    hooks = []
    if memory_client and memory_id:
        hooks.append(AgentCoreMemoryHook(memory_client, memory_id))
        logger.info(
            "AgentCore Memory integration enabled",
            extra={"memory_id": memory_id, "session_id": session_id}
        )
    
    # Create the orchestrator agent
    orchestrator = Agent(
        model=model,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=available_agents,
        hooks=hooks,
        state={"session_id": session_id}
    )
    
    logger.info(
        f"Orchestrator created for role: {user_role}",
        extra={
            "user_role": user_role,
            "memory_enabled": len(hooks) > 0,
            "available_agents": [a.__name__ for a in available_agents]
        }
    )
    
    return orchestrator


def create_agentcore_app(
    user_role: str = "user",
    memory_id: Optional[str] = None
):
    """
    Create a complete AgentCore application with orchestrator.
    
    This is designed for deployment to AgentCore Runtime.
    
    Args:
        user_role: The role of the user
        memory_id: Optional AgentCore Memory resource ID (can be set via env var)
    
    Returns:
        BedrockAgentCoreApp instance ready for deployment
    
    Example deployment:
        ```python
        # handler.py
        from strands_agents.src.agents.orchestrator_agent_agentcore import create_agentcore_app
        import os
        
        # Get memory ID from environment
        MEMORY_ID = os.getenv('MEMORY_ID')
        
        # Create app
        app = create_agentcore_app(
            user_role="user",
            memory_id=MEMORY_ID
        )
        
        # Deploy using agentcore CLI
        # $ agentcore configure --entrypoint handler.py
        # $ agentcore launch
        ```
    """
    try:
        from bedrock_agentcore.runtime import BedrockAgentCoreApp
        from bedrock_agentcore.memory import MemoryClient
    except ImportError:
        raise ImportError(
            "bedrock_agentcore package required for AgentCore deployment. "
            "Install with: pip install bedrock-agentcore"
        )
    
    # Initialize the AgentCore runtime app
    app = BedrockAgentCoreApp()
    
    # Connect to memory service if memory_id is provided
    memory_client = None
    if memory_id or os.getenv('MEMORY_ID'):
        memory_id = memory_id or os.getenv('MEMORY_ID')
        memory_client = MemoryClient(region_name=os.getenv('AWS_REGION', 'us-west-2'))
        logger.info(f"AgentCore Memory client initialized with memory_id: {memory_id}")
    
    # Create the orchestrator
    # Note: session_id will be set per request in the entrypoint
    orchestrator = None
    
    @app.entrypoint
    def invoke(payload, context):
        """
        Main entry point for AgentCore Runtime.
        
        Args:
            payload: Request payload containing 'prompt' and optional parameters
            context: AgentCore RequestContext with session_id
        
        Returns:
            Agent response string
        """
        nonlocal orchestrator
        
        # Get session ID from context (AgentCore provides this)
        session_id = getattr(context, 'session_id', 'default')
        
        # Create or update orchestrator with current session
        if orchestrator is None or orchestrator.state.get("session_id") != session_id:
            orchestrator = create_orchestrator_with_agentcore(
                user_role=user_role,
                memory_client=memory_client,
                memory_id=memory_id,
                session_id=session_id
            )
        
        # Process the user's message
        prompt = payload.get("prompt", "Hello")
        response = orchestrator(prompt)
        
        # Extract text from response
        if hasattr(response, 'message'):
            return response.message['content'][0]['text']
        return str(response)
    
    return app

