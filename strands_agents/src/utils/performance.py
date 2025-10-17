"""
Performance utilities for graph analytics tools.

Provides caching and timeout management for expensive graph operations:
- Result caching with TTL and size limits
- Timeout decorators for long-running operations
- Cache invalidation strategies
- Performance metrics collection
"""

import time
import hashlib
import json
import threading
import signal
from functools import wraps
from typing import Any, Dict, Optional, Callable, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict

from .logging import get_logger
from .errors import ToolExecutionError, ValidationError

logger = get_logger(__name__)


class TimeoutError(ToolExecutionError):
    """Raised when an operation exceeds its timeout limit"""
    def __init__(self, operation: str, timeout_seconds: int, **kwargs):
        super().__init__(
            message=f"Operation '{operation}' exceeded timeout of {timeout_seconds} seconds",
            tool_name=operation,
            **kwargs
        )


class CacheEntry:
    """Represents a cached result with metadata"""
    
    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.expires_at
    
    def access(self) -> Any:
        """Record access and return value"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value
    
    def get_age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return (datetime.now() - self.created_at).total_seconds()


class ResultCache:
    """
    LRU cache with TTL for expensive graph operations.
    
    Features:
    - Time-to-live (TTL) for cache entries
    - Maximum cache size with LRU eviction
    - Thread-safe operations
    - Cache statistics and monitoring
    - Invalidation strategies
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize result cache.
        
        Args:
            max_size: Maximum number of entries to cache (default: 100)
            default_ttl: Default time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(
            f"Initialized ResultCache with max_size={max_size}, default_ttl={default_ttl}s",
            operation="cache_init"
        )
    
    def _generate_key(self, func_name: str, args: Tuple, kwargs: Dict) -> str:
        """
        Generate cache key from function name and arguments.
        
        Args:
            func_name: Name of the function
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Cache key string
        """
        # Create a stable representation of arguments
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items())  # Sort for consistency
        }
        
        # Serialize and hash
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                logger.debug(
                    f"Cache entry expired (age: {entry.get_age_seconds():.1f}s)",
                    operation="cache_miss",
                    reason="expired"
                )
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            
            value = entry.access()
            
            logger.debug(
                f"Cache hit (age: {entry.get_age_seconds():.1f}s, accesses: {entry.access_count})",
                operation="cache_hit"
            )
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        with self._lock:
            # Use default TTL if not specified
            ttl = ttl if ttl is not None else self.default_ttl
            
            # Evict if at capacity and adding new entry
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Remove least recently used (first item)
                evicted_key, evicted_entry = self._cache.popitem(last=False)
                self._evictions += 1
                logger.debug(
                    f"Evicted LRU entry (age: {evicted_entry.get_age_seconds():.1f}s)",
                    operation="cache_evict"
                )
            
            # Store entry
            self._cache[key] = CacheEntry(value, ttl)
            
            # Move to end (most recently used)
            if key in self._cache:
                self._cache.move_to_end(key)
            
            logger.debug(
                f"Cached result with TTL={ttl}s",
                operation="cache_set"
            )
    
    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries.
        
        Args:
            pattern: Optional pattern to match keys (substring match).
                    If None, clears entire cache.
        
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if pattern is None:
                # Clear entire cache
                count = len(self._cache)
                self._cache.clear()
                logger.info(
                    f"Cleared entire cache ({count} entries)",
                    operation="cache_clear"
                )
                return count
            
            # Invalidate matching entries
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            logger.info(
                f"Invalidated {len(keys_to_remove)} cache entries matching pattern '{pattern}'",
                operation="cache_invalidate"
            )
            
            return len(keys_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of expired entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(
                    f"Cleaned up {len(expired_keys)} expired cache entries",
                    operation="cache_cleanup"
                )
            
            return len(expired_keys)


# Global cache instance
_global_cache: Optional[ResultCache] = None
_cache_lock = threading.Lock()


def get_cache() -> ResultCache:
    """
    Get or create the global result cache instance.
    
    Returns:
        Global ResultCache instance
    """
    global _global_cache
    
    with _cache_lock:
        if _global_cache is None:
            _global_cache = ResultCache(max_size=100, default_ttl=300)
        return _global_cache


def clear_cache() -> None:
    """Clear the global cache (useful for testing)"""
    cache = get_cache()
    cache.invalidate()


def with_timeout(seconds: int, operation_name: Optional[str] = None):
    """
    Decorator to add timeout to a function.
    
    Args:
        seconds: Maximum execution time in seconds
        operation_name: Optional name for error messages (defaults to function name)
    
    Returns:
        Decorated function that raises TimeoutError if it exceeds the timeout
    
    Example:
        @with_timeout(30, "expensive_query")
        def my_function():
            # Long running operation
            pass
    
    Note:
        Uses threading.Timer for timeout management. The function will be allowed
        to complete but a TimeoutError will be raised if it takes too long.
        For true interruption, consider using signal.alarm (Unix only).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.time()
            timeout_occurred = threading.Event()
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)
            
            elapsed = time.time() - start_time
            
            if thread.is_alive():
                # Thread is still running - timeout occurred
                logger.error(
                    f"Operation '{op_name}' exceeded timeout of {seconds}s",
                    operation="timeout",
                    elapsed_time=elapsed
                )
                raise TimeoutError(
                    operation=op_name,
                    timeout_seconds=seconds
                )
            
            # Check if exception occurred
            if exception[0] is not None:
                raise exception[0]
            
            logger.debug(
                f"Operation '{op_name}' completed in {elapsed:.2f}s (timeout: {seconds}s)",
                operation="timeout_check",
                elapsed_time=elapsed
            )
            
            return result[0]
        
        return wrapper
    return decorator


def with_cache(ttl: Optional[int] = None, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds (uses cache default if not specified)
        key_prefix: Optional prefix for cache keys
    
    Returns:
        Decorated function that caches results
    
    Example:
        @with_cache(ttl=300, key_prefix="graph_stats")
        def graph_stats(node_type=None):
            # Expensive operation
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = cache._generate_key(prefix, args, kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def with_timeout_and_cache(
    timeout_seconds: int,
    cache_ttl: Optional[int] = None,
    operation_name: Optional[str] = None
):
    """
    Combined decorator for timeout and caching.
    
    Args:
        timeout_seconds: Maximum execution time in seconds
        cache_ttl: Cache time-to-live in seconds
        operation_name: Optional name for error messages
    
    Returns:
        Decorated function with both timeout and caching
    
    Example:
        @with_timeout_and_cache(timeout_seconds=30, cache_ttl=300)
        def expensive_graph_query():
            # Long running operation
            return results
    """
    def decorator(func: Callable) -> Callable:
        # Apply cache decorator first, then timeout
        cached_func = with_cache(ttl=cache_ttl)(func)
        timed_func = with_timeout(timeout_seconds, operation_name)(cached_func)
        return timed_func
    return decorator


def invalidate_cache_on_write(func: Callable) -> Callable:
    """
    Decorator to invalidate cache after write operations.
    
    This should be applied to write operations (create_node, create_relationship, etc.)
    to ensure cached read results are invalidated.
    
    Example:
        @invalidate_cache_on_write
        def create_node(label, properties):
            # Create node
            return result
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Execute write operation
        result = func(*args, **kwargs)
        
        # Invalidate relevant cache entries
        cache = get_cache()
        invalidated = cache.invalidate()  # Clear entire cache for simplicity
        
        if invalidated > 0:
            logger.info(
                f"Invalidated {invalidated} cache entries after write operation '{func.__name__}'",
                operation="cache_invalidate_on_write"
            )
        
        return result
    
    return wrapper


def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the global cache.
    
    Returns:
        Dictionary with cache statistics
    """
    cache = get_cache()
    return cache.get_stats()


def cleanup_expired_cache() -> int:
    """
    Clean up expired cache entries.
    
    Returns:
        Number of expired entries removed
    """
    cache = get_cache()
    return cache.cleanup_expired()

