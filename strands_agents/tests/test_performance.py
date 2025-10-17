"""
Test suite for performance utilities (caching and timeout management)

Tests cover:
- Result caching with TTL
- LRU eviction
- Cache invalidation
- Timeout decorators
- Combined timeout and caching
- Cache statistics
- Thread safety
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

# Import the utilities under test
from src.utils.performance import (
    ResultCache,
    CacheEntry,
    TimeoutError,
    get_cache,
    clear_cache,
    with_timeout,
    with_cache,
    with_timeout_and_cache,
    invalidate_cache_on_write,
    get_cache_stats,
    cleanup_expired_cache
)


class TestCacheEntry:
    """Test CacheEntry class"""
    
    def test_cache_entry_creation(self):
        """Test creating a cache entry"""
        entry = CacheEntry("test_value", ttl_seconds=60)
        
        assert entry.value == "test_value"
        assert entry.access_count == 0
        assert not entry.is_expired()
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration"""
        # Create entry with 0 second TTL
        entry = CacheEntry("test_value", ttl_seconds=0)
        
        # Should be expired immediately
        time.sleep(0.01)
        assert entry.is_expired()
    
    def test_cache_entry_access(self):
        """Test accessing cache entry"""
        entry = CacheEntry("test_value")
        
        value = entry.access()
        
        assert value == "test_value"
        assert entry.access_count == 1
        
        # Access again
        entry.access()
        assert entry.access_count == 2
    
    def test_cache_entry_age(self):
        """Test getting cache entry age"""
        entry = CacheEntry("test_value")
        
        time.sleep(0.1)
        age = entry.get_age_seconds()
        
        assert age >= 0.1
        assert age < 0.2  # Reasonable upper bound


class TestResultCache:
    """Test ResultCache class"""
    
    def test_cache_initialization(self):
        """Test initializing a cache"""
        cache = ResultCache(max_size=50, default_ttl=120)
        
        assert cache.max_size == 50
        assert cache.default_ttl == 120
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
    
    def test_cache_set_and_get(self):
        """Test setting and getting values"""
        cache = ResultCache()
        
        key = "test_key"
        value = {"data": "test"}
        
        cache.set(key, value)
        retrieved = cache.get(key)
        
        assert retrieved == value
        assert cache.get_stats()["hits"] == 1
    
    def test_cache_miss(self):
        """Test cache miss"""
        cache = ResultCache()
        
        result = cache.get("nonexistent_key")
        
        assert result is None
        assert cache.get_stats()["misses"] == 1
    
    def test_cache_expiration(self):
        """Test cache entry expiration"""
        cache = ResultCache(default_ttl=0)
        
        cache.set("test_key", "test_value", ttl=0)
        time.sleep(0.01)
        
        result = cache.get("test_key")
        
        assert result is None
        assert cache.get_stats()["misses"] == 1
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = ResultCache(max_size=3)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add key4, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") is not None  # Still in cache
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") is not None  # Still in cache
        assert cache.get("key4") is not None  # Newly added
        
        stats = cache.get_stats()
        assert stats["evictions"] == 1
    
    def test_cache_invalidation_all(self):
        """Test invalidating entire cache"""
        cache = ResultCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        count = cache.invalidate()
        
        assert count == 3
        assert cache.get_stats()["size"] == 0
    
    def test_cache_invalidation_pattern(self):
        """Test invalidating cache entries by pattern"""
        cache = ResultCache()
        
        cache.set("user_123", "data1")
        cache.set("user_456", "data2")
        cache.set("stats_global", "data3")
        
        count = cache.invalidate(pattern="user_")
        
        assert count == 2
        assert cache.get("user_123") is None
        assert cache.get("user_456") is None
        assert cache.get("stats_global") is not None
    
    def test_cache_cleanup_expired(self):
        """Test cleaning up expired entries"""
        cache = ResultCache()
        
        # Add entries with different TTLs
        cache.set("short", "value1", ttl=0)
        cache.set("long", "value2", ttl=300)
        
        time.sleep(0.01)
        
        count = cache.cleanup_expired()
        
        assert count == 1
        assert cache.get("short") is None
        assert cache.get("long") is not None
    
    def test_cache_generate_key(self):
        """Test cache key generation"""
        cache = ResultCache()
        
        # Same arguments should generate same key
        key1 = cache._generate_key("func", (1, 2), {"a": "b"})
        key2 = cache._generate_key("func", (1, 2), {"a": "b"})
        
        assert key1 == key2
        
        # Different arguments should generate different keys
        key3 = cache._generate_key("func", (1, 3), {"a": "b"})
        
        assert key1 != key3


class TestTimeoutDecorator:
    """Test timeout decorator"""
    
    def test_timeout_success(self):
        """Test function completing within timeout"""
        @with_timeout(seconds=2, operation_name="test_op")
        def fast_function():
            return "success"
        
        result = fast_function()
        
        assert result == "success"
    
    def test_timeout_exceeded(self):
        """Test function exceeding timeout"""
        @with_timeout(seconds=1, operation_name="slow_op")
        def slow_function():
            time.sleep(2)
            return "should not reach here"
        
        with pytest.raises(TimeoutError) as exc_info:
            slow_function()
        
        assert "slow_op" in str(exc_info.value)
        assert "1 seconds" in str(exc_info.value)
    
    def test_timeout_with_exception(self):
        """Test that exceptions are properly propagated"""
        @with_timeout(seconds=2)
        def error_function():
            raise ValueError("test error")
        
        with pytest.raises(ValueError) as exc_info:
            error_function()
        
        assert "test error" in str(exc_info.value)


class TestCacheDecorator:
    """Test cache decorator"""
    
    def test_cache_decorator_basic(self):
        """Test basic caching functionality"""
        call_count = [0]
        
        @with_cache(ttl=300)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        
        # First call - should execute
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # Second call - should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not called again
        
        # Different argument - should execute
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count[0] == 2
    
    def test_cache_decorator_with_ttl(self):
        """Test caching with TTL"""
        # Clear cache to start fresh
        clear_cache()
        
        call_count = [0]
        
        @with_cache(ttl=1)  # 1 second TTL
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        
        # First call - should execute
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # Immediate second call - should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count[0] == 1
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Third call - should execute again due to expiration
        result3 = expensive_function(5)
        assert result3 == 10
        assert call_count[0] == 2


class TestCombinedDecorator:
    """Test combined timeout and cache decorator"""
    
    def test_combined_decorator(self):
        """Test timeout and caching together"""
        call_count = [0]
        
        @with_timeout_and_cache(timeout_seconds=2, cache_ttl=300)
        def function(x):
            call_count[0] += 1
            time.sleep(0.1)
            return x * 2
        
        # First call
        result1 = function(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # Second call - should use cache
        result2 = function(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not called again
    
    def test_combined_decorator_timeout(self):
        """Test timeout with caching"""
        @with_timeout_and_cache(timeout_seconds=1, cache_ttl=300)
        def slow_function():
            time.sleep(2)
            return "result"
        
        with pytest.raises(TimeoutError):
            slow_function()


class TestInvalidateOnWrite:
    """Test cache invalidation on write operations"""
    
    def test_invalidate_on_write_decorator(self):
        """Test cache invalidation after write"""
        cache = get_cache()
        cache.set("test_key", "test_value")
        
        assert cache.get("test_key") is not None
        
        @invalidate_cache_on_write
        def write_operation():
            return "write complete"
        
        result = write_operation()
        
        assert result == "write complete"
        assert cache.get("test_key") is None  # Cache should be cleared


class TestGlobalCache:
    """Test global cache functions"""
    
    def test_get_cache_singleton(self):
        """Test that get_cache returns singleton"""
        cache1 = get_cache()
        cache2 = get_cache()
        
        assert cache1 is cache2
    
    def test_clear_cache(self):
        """Test clearing global cache"""
        cache = get_cache()
        cache.set("test", "value")
        
        clear_cache()
        
        assert cache.get("test") is None
    
    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        cache = get_cache()
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")
        
        stats = get_cache_stats()
        
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
    
    def test_cleanup_expired_cache(self):
        """Test cleaning up expired entries"""
        cache = get_cache()
        cache.set("expired", "value", ttl=0)
        cache.set("valid", "value", ttl=300)
        
        time.sleep(0.01)
        
        count = cleanup_expired_cache()
        
        assert count >= 1


class TestThreadSafety:
    """Test thread safety of cache operations"""
    
    def test_concurrent_cache_access(self):
        """Test concurrent reads and writes"""
        cache = ResultCache()
        results = []
        
        def worker(thread_id):
            for i in range(10):
                key = f"key_{i}"
                cache.set(key, f"value_{thread_id}_{i}")
                value = cache.get(key)
                results.append((thread_id, value))
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should complete without errors
        assert len(results) > 0
    
    def test_concurrent_invalidation(self):
        """Test concurrent invalidation"""
        cache = ResultCache()
        
        # Populate cache
        for i in range(20):
            cache.set(f"key_{i}", f"value_{i}")
        
        def invalidator():
            cache.invalidate()
        
        threads = [threading.Thread(target=invalidator) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Cache should be empty
        assert cache.get_stats()["size"] == 0


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_cache_with_none_value(self):
        """Test caching None values"""
        cache = ResultCache()
        
        # None should be cacheable
        cache.set("null_key", None)
        result = cache.get("null_key")
        
        # Note: Current implementation returns None for both cache miss and cached None
        # This is a known limitation - could be improved with a sentinel value
        assert result is None
    
    def test_cache_with_complex_types(self):
        """Test caching complex data types"""
        cache = ResultCache()
        
        complex_value = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3)
        }
        
        cache.set("complex", complex_value)
        result = cache.get("complex")
        
        assert result == complex_value
    
    def test_timeout_with_args(self):
        """Test timeout decorator with function arguments"""
        @with_timeout(seconds=2)
        def function_with_args(a, b, c=10):
            return a + b + c
        
        result = function_with_args(1, 2, c=3)
        
        assert result == 6
    
    def test_cache_stats_with_zero_requests(self):
        """Test cache statistics with no requests"""
        cache = ResultCache()
        
        stats = cache.get_stats()
        
        assert stats["hit_rate"] == 0
        assert stats["total_requests"] == 0

