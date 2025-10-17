# Performance Optimization Guide

This guide explains how to use the caching and timeout management utilities to optimize graph analytics tools.

## Overview

The `src/utils/performance.py` module provides two main optimization techniques:

1. **Result Caching**: Store expensive computation results to avoid redundant queries
2. **Timeout Management**: Prevent long-running operations from blocking the system

## Table of Contents

- [Result Caching](#result-caching)
- [Timeout Management](#timeout-management)
- [Combined Optimization](#combined-optimization)
- [Cache Invalidation](#cache-invalidation)
- [Performance Monitoring](#performance-monitoring)
- [Best Practices](#best-practices)

## Result Caching

### Basic Caching

Use the `@with_cache` decorator to cache function results:

```python
from src.utils.performance import with_cache

@with_cache(ttl=300)  # Cache for 5 minutes
def expensive_graph_query(node_type: str, limit: int):
    """Query that should be cached"""
    # Expensive Neo4j query
    return results
```

### Cache Configuration

```python
from src.utils.performance import with_cache

@with_cache(
    ttl=600,  # Time-to-live in seconds (default: 300)
    key_prefix="my_operation"  # Optional prefix for cache keys
)
def my_function(param1, param2):
    return results
```

### Manual Cache Control

```python
from src.utils.performance import get_cache, clear_cache

# Get cache instance
cache = get_cache()

# Manually set a value
cache.set("my_key", "my_value", ttl=300)

# Get a value
value = cache.get("my_key")

# Invalidate specific entries
cache.invalidate(pattern="centrality_")

# Clear entire cache
clear_cache()
```

## Timeout Management

### Basic Timeout

Use the `@with_timeout` decorator to enforce execution limits:

```python
from src.utils.performance import with_timeout, TimeoutError

@with_timeout(seconds=30, operation_name="path_analysis")
def find_all_paths(start_node, end_node):
    """Operation with 30-second timeout"""
    try:
        # Potentially long-running operation
        return results
    except TimeoutError as e:
        logger.error(f"Operation timed out: {e}")
        return {"error": "timeout", "message": str(e)}
```

### Handling Timeouts

```python
from src.utils.performance import with_timeout, TimeoutError

@with_timeout(seconds=60)
def expensive_operation():
    # Long-running code
    pass

try:
    result = expensive_operation()
except TimeoutError as e:
    # Handle timeout gracefully
    logger.warning(f"Operation exceeded {e.timeout_seconds}s timeout")
    return partial_results
```

## Combined Optimization

### Timeout + Caching

Use `@with_timeout_and_cache` for both optimizations:

```python
from src.utils.performance import with_timeout_and_cache

@with_timeout_and_cache(
    timeout_seconds=30,  # Maximum execution time
    cache_ttl=300,       # Cache results for 5 minutes
    operation_name="community_detection"
)
def community_detection(algorithm: str, min_size: int):
    """
    Expensive operation with both timeout and caching.
    
    - First call: Executes with 30s timeout, caches result
    - Subsequent calls: Returns cached result immediately
    - After 5 minutes: Cache expires, re-executes if called again
    """
    # Expensive computation
    return results
```

### Example: Graph Statistics with Optimization

```python
from strands import tool
from src.utils.performance import with_timeout_and_cache
from src.utils.logging import get_logger
from src.config import get_driver

logger = get_logger(__name__)

@tool
@with_timeout_and_cache(
    timeout_seconds=60,
    cache_ttl=600,
    operation_name="graph_stats"
)
def graph_stats(node_type: Optional[str] = None):
    """
    Calculate comprehensive graph statistics.
    
    Performance optimizations:
    - 60-second timeout prevents runaway queries
    - 10-minute cache reduces redundant calculations
    """
    logger.info("Calculating graph statistics", node_type=node_type)
    
    driver = get_driver()
    with driver.session() as session:
        # Expensive queries
        result = session.run(...)
        return format_results(result)
```

## Cache Invalidation

### On Write Operations

Automatically invalidate cache after write operations:

```python
from src.utils.performance import invalidate_cache_on_write

@tool
@invalidate_cache_on_write
def create_node(label: str, properties: Dict):
    """
    Create a node and invalidate cache.
    
    After this operation, all cached read results are cleared
    to ensure consistency.
    """
    # Create node
    return result
```

### Selective Invalidation

Invalidate specific cache entries by pattern:

```python
from src.utils.performance import get_cache

def update_node_type(node_id: str, new_type: str):
    """Update node and invalidate relevant caches"""
    # Update node in database
    update_database(node_id, new_type)
    
    # Invalidate only caches related to this node type
    cache = get_cache()
    cache.invalidate(pattern=f"node_{node_id}")
    cache.invalidate(pattern=f"type_{new_type}")
```

### Cleanup Expired Entries

Periodically clean up expired cache entries:

```python
from src.utils.performance import cleanup_expired_cache

# In a background task or periodic job
def periodic_cache_maintenance():
    """Run periodically to clean up expired entries"""
    removed_count = cleanup_expired_cache()
    logger.info(f"Cleaned up {removed_count} expired cache entries")
```

## Performance Monitoring

### Cache Statistics

Monitor cache performance:

```python
from src.utils.performance import get_cache_stats

stats = get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.1f}%")
print(f"Total requests: {stats['total_requests']}")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
print(f"Current size: {stats['size']}/{stats['max_size']}")
print(f"Evictions: {stats['evictions']}")
```

### Example Output

```
Cache hit rate: 75.5%
Total requests: 1250
Hits: 943, Misses: 307
Current size: 87/100
Evictions: 12
```

### Integration with Logging

```python
from src.utils.performance import get_cache_stats
from src.utils.logging import get_logger

logger = get_logger(__name__)

def log_cache_performance():
    """Log cache statistics for monitoring"""
    stats = get_cache_stats()
    logger.info(
        "Cache performance metrics",
        hit_rate=stats['hit_rate'],
        size=stats['size'],
        hits=stats['hits'],
        misses=stats['misses']
    )
```

## Best Practices

### 1. Choose Appropriate TTL

```python
# Frequently changing data: short TTL
@with_cache(ttl=60)  # 1 minute
def get_active_sessions():
    pass

# Stable reference data: long TTL
@with_cache(ttl=3600)  # 1 hour
def get_node_labels():
    pass

# Expensive analytics: medium TTL
@with_cache(ttl=300)  # 5 minutes
def calculate_centrality():
    pass
```

### 2. Set Reasonable Timeouts

```python
# Simple queries: short timeout
@with_timeout(seconds=5)
def get_node_by_id(node_id):
    pass

# Complex analytics: longer timeout
@with_timeout(seconds=60)
def community_detection():
    pass

# Batch operations: extended timeout
@with_timeout(seconds=300)  # 5 minutes
def bulk_ingest(data):
    pass
```

### 3. Cache High-Value Operations

Cache operations that are:
- **Expensive**: Complex queries or computations
- **Repeated**: Called frequently with same parameters
- **Stable**: Results don't change often

Don't cache:
- **Write operations**: Should always execute
- **User-specific data**: Unless scoped properly
- **Real-time data**: Requires fresh results

### 4. Invalidate Strategically

```python
# Invalidate after writes
@invalidate_cache_on_write
def create_relationship(start, end, type):
    pass

# Selective invalidation for updates
def update_node_properties(node_id, properties):
    update_database(node_id, properties)
    cache = get_cache()
    # Only invalidate caches involving this node
    cache.invalidate(pattern=f"node_{node_id}")
```

### 5. Handle Timeouts Gracefully

```python
from src.utils.performance import with_timeout, TimeoutError

@with_timeout(seconds=30)
def expensive_query():
    try:
        return full_results()
    except TimeoutError:
        # Return partial results instead of error
        return {
            "status": "timeout",
            "partial_results": get_partial_results(),
            "message": "Query timeout, showing partial results"
        }
```

### 6. Monitor Performance

```python
# Regularly check cache effectiveness
def monitor_cache_health():
    stats = get_cache_stats()
    
    if stats['hit_rate'] < 50:
        logger.warning(
            "Low cache hit rate - consider adjusting TTL",
            hit_rate=stats['hit_rate']
        )
    
    if stats['evictions'] > stats['hits'] * 0.1:
        logger.warning(
            "High eviction rate - consider increasing cache size",
            evictions=stats['evictions']
        )
```

## Configuration

### Cache Configuration

Default cache settings can be customized:

```python
from src.utils.performance import ResultCache

# Create custom cache instance
custom_cache = ResultCache(
    max_size=200,      # Store up to 200 entries
    default_ttl=900    # Default 15-minute TTL
)
```

### Global Cache Settings

The default global cache uses:
- **Max Size**: 100 entries
- **Default TTL**: 300 seconds (5 minutes)
- **Eviction Strategy**: LRU (Least Recently Used)

## Examples

### Example 1: Optimized Centrality Analysis

```python
from strands import tool
from src.utils.performance import with_timeout_and_cache

@tool
@with_timeout_and_cache(
    timeout_seconds=45,
    cache_ttl=600,
    operation_name="centrality_analysis"
)
def centrality_analysis(
    algorithm: str = "pagerank",
    node_type: Optional[str] = None,
    limit: int = 50
):
    """
    Centrality analysis with optimization.
    
    - Timeout prevents queries from running >45 seconds
    - Results cached for 10 minutes
    - Repeated calls with same parameters use cache
    """
    # Implementation
    pass
```

### Example 2: Optimized Community Detection

```python
@tool
@with_timeout_and_cache(
    timeout_seconds=60,
    cache_ttl=900,
    operation_name="community_detection"
)
def community_detection(
    algorithm: str = "label_propagation",
    min_community_size: int = 2,
    max_communities: int = 20
):
    """
    Community detection with optimization.
    
    - 60-second timeout for complex algorithms
    - 15-minute cache for stable community structures
    """
    # Implementation
    pass
```

### Example 3: Write Operation with Cache Invalidation

```python
@tool
@invalidate_cache_on_write
def create_node(label: str, properties: Dict):
    """
    Create node and invalidate all caches.
    
    Ensures read operations see fresh data after writes.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            f"CREATE (n:{label} $props) RETURN n",
            props=properties
        )
        return format_node_response(result.single()["n"])
```

## Troubleshooting

### Cache Not Working

**Symptom**: Functions execute every time despite caching

**Solutions**:
1. Check if cache is being cleared unexpectedly
2. Verify TTL isn't too short
3. Ensure function parameters are hashable
4. Check cache statistics: `get_cache_stats()`

### High Memory Usage

**Symptom**: Application memory grows continuously

**Solutions**:
1. Reduce cache size: `ResultCache(max_size=50)`
2. Reduce TTL values
3. Run periodic cleanup: `cleanup_expired_cache()`
4. Monitor cache size: `get_cache_stats()['size']`

### Timeout Too Short

**Symptom**: Operations frequently timeout

**Solutions**:
1. Increase timeout value
2. Optimize query complexity
3. Add progress tracking
4. Return partial results on timeout

### Stale Data

**Symptom**: Cached results don't reflect recent changes

**Solutions**:
1. Reduce TTL for frequently changing data
2. Invalidate cache after write operations
3. Use selective invalidation patterns
4. Consider not caching real-time data

## Related Documentation

- [Query Safety Guide](./query-safety.md) - Rate limiting and validation
- [Logging Guide](../../src/utils/README.md#logging) - Performance logging
- [Error Handling](../../src/utils/README.md#errors) - Timeout error handling

## Summary

Performance optimization with caching and timeouts:

✅ Use `@with_cache` for expensive, repeated operations
✅ Use `@with_timeout` to prevent runaway queries  
✅ Use `@with_timeout_and_cache` for comprehensive optimization
✅ Invalidate cache after write operations
✅ Monitor cache performance regularly
✅ Choose appropriate TTL and timeout values
✅ Handle timeouts gracefully with partial results

These utilities help ensure graph analytics tools are both fast and reliable!

