"""
Session management for the FastAPI proxy.

Provides session ID generation and management for maintaining
conversation context across multiple requests.

Supports both file-based (development) and S3-based (production) session storage
through Strands Agents session managers.
"""

import os
import uuid
import logging
from typing import Optional
from fastapi import Request, Response
from strands.session.file_session_manager import FileSessionManager
from strands.session.s3_session_manager import S3SessionManager
import boto3

from .models import ProxyConfig

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session IDs and creates Strands session managers.
    
    Handles session ID extraction from requests, generation of new IDs,
    and creation of appropriate session managers based on configuration.
    """
    
    def __init__(self, config: ProxyConfig):
        """
        Initialize the session manager.
        
        Args:
            config: Proxy configuration settings
        """
        self.config = config
        self._session_managers = {}  # Cache of session managers by session ID
        
        logger.info(
            f"Initialized SessionManager with backend: {config.session_backend}"
        )
    
    def extract_session_id(self, request: Request) -> Optional[str]:
        """
        Extract session ID from request headers or cookies.
        
        Priority order:
        1. X-Session-ID header
        2. session_id cookie
        3. None (will generate new ID)
        
        Args:
            request: FastAPI request object
            
        Returns:
            Session ID if found, None otherwise
        """
        # Try header first
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            logger.debug(f"Found session ID in header: {session_id}")
            return session_id
        
        # Try cookie
        session_id = request.cookies.get("session_id")
        if session_id:
            logger.debug(f"Found session ID in cookie: {session_id}")
            return session_id
        
        logger.debug("No session ID found in request")
        return None
    
    def generate_session_id(self, prefix: str = "sess") -> str:
        """
        Generate a new unique session ID.
        
        Args:
            prefix: Prefix for the session ID
            
        Returns:
            New session ID in format: {prefix}-{uuid}
        """
        session_id = f"{prefix}-{uuid.uuid4().hex[:16]}"
        logger.info(f"Generated new session ID: {session_id}")
        return session_id
    
    def get_or_create_session_id(self, request: Request) -> str:
        """
        Get existing session ID from request or generate a new one.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Session ID (existing or newly generated)
        """
        session_id = self.extract_session_id(request)
        if not session_id:
            session_id = self.generate_session_id()
        
        return session_id
    
    def set_session_cookie(
        self,
        response: Response,
        session_id: str,
        max_age: int = 86400 * 7  # 7 days
    ):
        """
        Set session ID cookie in response.
        
        Args:
            response: FastAPI response object
            session_id: Session ID to set
            max_age: Cookie max age in seconds (default: 7 days)
        """
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=max_age,
            httponly=True,
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )
        logger.debug(f"Set session cookie: {session_id}")
    
    def create_strands_session_manager(self, session_id: str):
        """
        Create a Strands session manager for the given session ID.
        
        Creates either FileSessionManager (dev) or S3SessionManager (prod)
        based on configuration.
        
        Args:
            session_id: Session ID for the manager
            
        Returns:
            Strands session manager instance
            
        Raises:
            ValueError: If session backend is invalid
        """
        # Return cached manager if exists
        if session_id in self._session_managers:
            return self._session_managers[session_id]
        
        backend = self.config.session_backend.lower()
        
        if backend == "file":
            manager = self._create_file_session_manager(session_id)
        elif backend == "s3":
            manager = self._create_s3_session_manager(session_id)
        else:
            raise ValueError(
                f"Invalid session backend: {backend}. Must be 'file' or 's3'"
            )
        
        # Cache the manager
        self._session_managers[session_id] = manager
        
        logger.info(
            f"Created {backend} session manager for session: {session_id}"
        )
        
        return manager
    
    def _create_file_session_manager(self, session_id: str) -> FileSessionManager:
        """
        Create a file-based session manager for local development.
        
        Args:
            session_id: Session ID
            
        Returns:
            FileSessionManager instance
        """
        storage_dir = self.config.session_storage_dir
        if not storage_dir:
            # Use default temp directory
            storage_dir = os.path.join(os.getcwd(), ".sessions")
            os.makedirs(storage_dir, exist_ok=True)
        
        return FileSessionManager(
            session_id=session_id,
            storage_dir=storage_dir
        )
    
    def _create_s3_session_manager(self, session_id: str) -> S3SessionManager:
        """
        Create an S3-based session manager for production.
        
        Args:
            session_id: Session ID
            
        Returns:
            S3SessionManager instance
            
        Raises:
            ValueError: If S3 bucket is not configured
        """
        if not self.config.session_s3_bucket:
            raise ValueError(
                "S3 session backend requires session_s3_bucket configuration"
            )
        
        # Create boto3 session
        boto_session = boto3.Session(region_name=self.config.aws_region)
        
        return S3SessionManager(
            session_id=session_id,
            bucket=self.config.session_s3_bucket,
            prefix=self.config.session_s3_prefix,
            boto_session=boto_session
        )
    
    def clear_session_cache(self, session_id: Optional[str] = None):
        """
        Clear cached session managers.
        
        Args:
            session_id: Specific session to clear, or None to clear all
        """
        if session_id:
            if session_id in self._session_managers:
                del self._session_managers[session_id]
                logger.info(f"Cleared session manager cache for: {session_id}")
        else:
            count = len(self._session_managers)
            self._session_managers.clear()
            logger.info(f"Cleared all session manager caches ({count} sessions)")
    
    def get_active_sessions_count(self) -> int:
        """
        Get count of active (cached) session managers.
        
        Returns:
            Number of active sessions
        """
        return len(self._session_managers)


# Global session manager instance (initialized by the application)
_session_manager: Optional[SessionManager] = None


def initialize_session_manager(config: ProxyConfig):
    """
    Initialize the global session manager.
    
    Should be called during application startup.
    
    Args:
        config: Proxy configuration
    """
    global _session_manager
    _session_manager = SessionManager(config)
    logger.info("Global session manager initialized")


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Returns:
        SessionManager instance
        
    Raises:
        RuntimeError: If session manager not initialized
    """
    if _session_manager is None:
        raise RuntimeError(
            "Session manager not initialized. "
            "Call initialize_session_manager() during app startup."
        )
    return _session_manager

