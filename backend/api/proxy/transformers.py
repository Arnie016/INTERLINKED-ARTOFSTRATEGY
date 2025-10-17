"""
Request/response transformation utilities for the FastAPI proxy.

Handles transformation between the existing frontend API format
and the internal Strands agent format.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from .models import (
    ChatMessage,
    ChatResponse,
    StrandsAgentRequest,
    StrandsAgentResponse,
)

logger = logging.getLogger(__name__)


class RequestTransformer:
    """
    Transforms incoming frontend requests to Strands agent format.
    
    Handles conversion from the existing ChatMessage format to the
    StrandsAgentRequest format expected by the agent client.
    """
    
    @staticmethod
    def transform(
        chat_message: ChatMessage,
        session_id: str,
        additional_context: Dict[str, Any] = None
    ) -> StrandsAgentRequest:
        """
        Transform frontend chat message to Strands agent request.
        
        Args:
            chat_message: Frontend chat message
            session_id: Session ID for conversation context
            additional_context: Optional additional context to include
            
        Returns:
            Strands agent request
        """
        logger.debug(
            f"Transforming request for session {session_id}: "
            f"agent_type={chat_message.agent_type}, "
            f"message_length={len(chat_message.message)}"
        )
        
        # Build context dictionary
        context = {
            "agent_type_hint": chat_message.agent_type,  # Hint for routing
        }
        
        if additional_context:
            context.update(additional_context)
        
        # Create Strands request
        request = StrandsAgentRequest(
            prompt=chat_message.message,
            session_id=session_id,
            context=context if context else None
        )
        
        logger.debug(f"Transformed to Strands request for session {session_id}")
        
        return request


class ResponseTransformer:
    """
    Transforms Strands agent responses to frontend API format.
    
    Handles conversion from StrandsAgentResponse to ChatResponse format
    expected by the existing frontend.
    """
    
    @staticmethod
    def transform(
        agent_response: StrandsAgentResponse,
        original_agent_type: str = "orchestrator"
    ) -> ChatResponse:
        """
        Transform Strands agent response to frontend chat response.
        
        Args:
            agent_response: Strands agent response
            original_agent_type: Original agent type from request (for backward compat)
            
        Returns:
            Frontend chat response
        """
        logger.debug(
            f"Transforming response for session {agent_response.session_id}: "
            f"result_length={len(agent_response.result)}"
        )
        
        # Determine agent type for response
        # Use the actual agent that was used, or fall back to original request type
        agent_type = agent_response.agent_used or original_agent_type
        
        # Create frontend response
        response = ChatResponse(
            success=True,
            response=agent_response.result,
            agent_type=agent_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            session_id=agent_response.session_id
        )
        
        logger.debug(
            f"Transformed to frontend response for session {agent_response.session_id}"
        )
        
        return response
    
    @staticmethod
    def transform_error(
        error_message: str,
        session_id: str = None,
        agent_type: str = "orchestrator"
    ) -> ChatResponse:
        """
        Transform an error into a ChatResponse format.
        
        Args:
            error_message: Error message to return
            session_id: Session ID (if available)
            agent_type: Agent type that encountered the error
            
        Returns:
            Frontend chat response with error message
        """
        logger.debug(f"Transforming error response: {error_message[:100]}")
        
        response = ChatResponse(
            success=False,
            response=f"I encountered an error: {error_message}",
            agent_type=agent_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            session_id=session_id
        )
        
        return response


def validate_chat_message(message: ChatMessage) -> tuple[bool, str]:
    """
    Validate an incoming chat message.
    
    Args:
        message: Chat message to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check message content
    if not message.message or not message.message.strip():
        return False, "Message content cannot be empty"
    
    # Check message length (reasonable limit)
    if len(message.message) > 10000:
        return False, "Message exceeds maximum length of 10,000 characters"
    
    # All checks passed
    return True, ""


def sanitize_message(message: str) -> str:
    """
    Sanitize message content for safe processing.
    
    Args:
        message: Message to sanitize
        
    Returns:
        Sanitized message
    """
    # Strip whitespace
    message = message.strip()
    
    # Remove null bytes (can cause issues)
    message = message.replace("\x00", "")
    
    # Normalize line endings
    message = message.replace("\r\n", "\n").replace("\r", "\n")
    
    return message

