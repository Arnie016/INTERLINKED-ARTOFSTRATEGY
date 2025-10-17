"""
Strands Agent client wrapper for the FastAPI proxy.

Provides a clean interface for invoking Strands agents with proper
session management, error handling, and response formatting.
"""

import os
import sys
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

# Add strands_agents to path
strands_agents_path = Path(__file__).parent.parent.parent.parent / "strands_agents" / "src"
sys.path.insert(0, str(strands_agents_path))

from strands import Agent
from strands.session.file_session_manager import FileSessionManager
from strands.session.s3_session_manager import S3SessionManager

from .models import (
    StrandsAgentRequest,
    StrandsAgentResponse,
    ProxyConfig,
)

logger = logging.getLogger(__name__)


class AgentInvocationError(Exception):
    """Base exception for agent invocation errors."""
    pass


class AgentTimeoutError(AgentInvocationError):
    """Raised when agent invocation times out."""
    pass


class AgentConfigurationError(AgentInvocationError):
    """Raised when agent configuration is invalid."""
    pass


class StrandsAgentClient:
    """
    Client for invoking Strands agents with session management.
    
    This class wraps the Strands Agent orchestrator and provides:
    - Session-aware agent invocation
    - Error handling and retries
    - Performance metrics
    - AgentCore Memory integration
    """
    
    def __init__(self, config: ProxyConfig):
        """
        Initialize the Strands agent client.
        
        Args:
            config: Proxy configuration
        """
        self.config = config
        self._agent_cache: Dict[str, Agent] = {}
        
        # Load environment variables for AgentCore
        self._setup_environment()
        
        logger.info("Initialized StrandsAgentClient")
    
    def _setup_environment(self):
        """
        Set up environment variables for AgentCore and Strands.
        
        Ensures AWS region, memory ID, and other required variables are set.
        """
        # Set AWS region
        if not os.getenv("AWS_REGION"):
            os.environ["AWS_REGION"] = self.config.aws_region
        
        # Set AgentCore Memory ID if configured
        if self.config.memory_id:
            os.environ["MEMORY_ID"] = self.config.memory_id
        
        logger.debug(f"Environment configured: AWS_REGION={os.getenv('AWS_REGION')}")
    
    def create_agent(
        self,
        session_manager,
        use_agentcore: bool = True
    ) -> Agent:
        """
        Create a Strands orchestrator agent with session management.
        
        Args:
            session_manager: Strands session manager instance
            use_agentcore: Whether to use AgentCore Memory integration
            
        Returns:
            Configured Agent instance
            
        Raises:
            AgentConfigurationError: If agent creation fails
        """
        try:
            if use_agentcore and self.config.use_agentcore_memory:
                # Use AgentCore orchestrator with Memory
                from agents.orchestrator_agent_agentcore import (
                    create_orchestrator_with_agentcore
                )
                
                agent = create_orchestrator_with_agentcore(
                    session_manager=session_manager
                )
                logger.info("Created AgentCore-enabled orchestrator")
            else:
                # Use simple orchestrator without AgentCore
                from agents.orchestrator_agent import create_orchestrator
                
                agent = create_orchestrator(
                    session_manager=session_manager
                )
                logger.info("Created simple orchestrator")
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise AgentConfigurationError(f"Failed to create agent: {str(e)}") from e
    
    def invoke_agent(
        self,
        request: StrandsAgentRequest,
        session_manager
    ) -> StrandsAgentResponse:
        """
        Invoke the Strands agent with the given request.
        
        Args:
            request: Agent request with prompt and session ID
            session_manager: Session manager for this invocation
            
        Returns:
            Agent response
            
        Raises:
            AgentTimeoutError: If invocation times out
            AgentInvocationError: If invocation fails
        """
        start_time = time.time()
        session_id = request.session_id
        
        try:
            # Get or create agent for this session
            agent = self._get_or_create_agent(session_id, session_manager)
            
            # Invoke the agent
            logger.info(
                f"Invoking agent for session {session_id} with prompt: "
                f"{request.prompt[:100]}..."
            )
            
            # Call the agent (Strands agents are callable)
            result = agent(request.prompt)
            
            # Extract response
            if isinstance(result, str):
                response_text = result
            elif hasattr(result, 'content'):
                # Handle Message object
                response_text = result.content
            elif isinstance(result, dict):
                response_text = result.get('response', str(result))
            else:
                response_text = str(result)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Agent invocation completed for session {session_id} "
                f"in {execution_time_ms:.2f}ms"
            )
            
            # Create response
            response = StrandsAgentResponse(
                result=response_text,
                session_id=session_id,
                agent_used="orchestrator",
                metadata={
                    "execution_time_ms": round(execution_time_ms, 2),
                    "use_agentcore": self.config.use_agentcore_memory
                }
            )
            
            return response
            
        except TimeoutError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Agent invocation timed out for session {session_id} "
                f"after {execution_time_ms:.2f}ms"
            )
            raise AgentTimeoutError(
                f"Agent invocation timed out after {self.config.agent_timeout_seconds}s"
            ) from e
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Agent invocation failed for session {session_id} "
                f"after {execution_time_ms:.2f}ms: {e}",
                exc_info=True
            )
            raise AgentInvocationError(f"Agent invocation failed: {str(e)}") from e
    
    def _get_or_create_agent(
        self,
        session_id: str,
        session_manager
    ) -> Agent:
        """
        Get cached agent or create new one for the session.
        
        Args:
            session_id: Session ID
            session_manager: Session manager for this session
            
        Returns:
            Agent instance
        """
        # Check cache
        if session_id in self._agent_cache:
            logger.debug(f"Using cached agent for session {session_id}")
            return self._agent_cache[session_id]
        
        # Create new agent
        agent = self.create_agent(
            session_manager=session_manager,
            use_agentcore=self.config.use_agentcore_memory
        )
        
        # Cache it
        self._agent_cache[session_id] = agent
        logger.debug(f"Cached new agent for session {session_id}")
        
        return agent
    
    def clear_agent_cache(self, session_id: Optional[str] = None):
        """
        Clear cached agents.
        
        Args:
            session_id: Specific session to clear, or None to clear all
        """
        if session_id:
            if session_id in self._agent_cache:
                del self._agent_cache[session_id]
                logger.info(f"Cleared agent cache for session: {session_id}")
        else:
            count = len(self._agent_cache)
            self._agent_cache.clear()
            logger.info(f"Cleared all agent caches ({count} agents)")
    
    def get_cached_agents_count(self) -> int:
        """
        Get count of cached agents.
        
        Returns:
            Number of cached agents
        """
        return len(self._agent_cache)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the agent system.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to create a test agent without session
            from agents.orchestrator_agent import create_orchestrator
            
            test_agent = create_orchestrator(session_manager=None)
            
            return {
                "status": "ready",
                "cached_agents": self.get_cached_agents_count(),
                "use_agentcore": self.config.use_agentcore_memory
            }
            
        except Exception as e:
            logger.error(f"Agent health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "cached_agents": self.get_cached_agents_count()
            }


# Global client instance (initialized by the application)
_agent_client: Optional[StrandsAgentClient] = None


def initialize_agent_client(config: ProxyConfig):
    """
    Initialize the global agent client.
    
    Should be called during application startup.
    
    Args:
        config: Proxy configuration
    """
    global _agent_client
    _agent_client = StrandsAgentClient(config)
    logger.info("Global agent client initialized")


def get_agent_client() -> StrandsAgentClient:
    """
    Get the global agent client instance.
    
    Returns:
        StrandsAgentClient instance
        
    Raises:
        RuntimeError: If agent client not initialized
    """
    if _agent_client is None:
        raise RuntimeError(
            "Agent client not initialized. "
            "Call initialize_agent_client() during app startup."
        )
    return _agent_client

