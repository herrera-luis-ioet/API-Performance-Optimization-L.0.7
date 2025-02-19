"""Redis cache connection and management module."""
from typing import Optional, Any
import json
from redis import asyncio as aioredis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError
from app.config import Settings

# Create Redis connection pool
redis_pool = ConnectionPool.from_url(
    Settings.REDIS_URL,
    max_connections=Settings.REDIS_POOL_SIZE,
    decode_responses=True
)

# Create Redis client
redis_client = aioredis.Redis(
    connection_pool=redis_pool,
    retry_on_timeout=True,
    socket_timeout=Settings.REDIS_SOCKET_TIMEOUT,
    socket_connect_timeout=Settings.REDIS_CONNECT_TIMEOUT
)

# PUBLIC_INTERFACE
async def get_cache() -> aioredis.Redis:
    """
    Get Redis cache client instance.
    
    Returns:
        aioredis.Redis: Redis client instance for cache operations.
        
    Raises:
        RedisError: If Redis connection cannot be established.
    """
    try:
        await redis_client.ping()
        return redis_client
    except RedisError as e:
        raise RedisError(f"Failed to connect to Redis: {str(e)}")

# PUBLIC_INTERFACE
async def set_cache(key: str, value: Any, expire: int = Settings.REDIS_DEFAULT_EXPIRE) -> bool:
    """
    Set a value in cache with optional expiration.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        expire: Expiration time in seconds
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        RedisError: If cache operation fails
    """
    try:
        return await redis_client.set(
            key,
            json.dumps(value),
            ex=expire
        )
    except RedisError as e:
        raise RedisError(f"Failed to set cache key {key}: {str(e)}")

# PUBLIC_INTERFACE
async def get_cache_value(key: str) -> Optional[Any]:
    """
    Get a value from cache.
    
    Args:
        key: Cache key to retrieve
        
    Returns:
        Optional[Any]: Cached value if exists, None otherwise
        
    Raises:
        RedisError: If cache operation fails
    """
    try:
        value = await redis_client.get(key)
        return json.loads(value) if value else None
    except RedisError as e:
        raise RedisError(f"Failed to get cache key {key}: {str(e)}")

# PUBLIC_INTERFACE
async def delete_cache(key: str) -> bool:
    """
    Delete a value from cache.
    
    Args:
        key: Cache key to delete
        
    Returns:
        bool: True if key was deleted, False if key didn't exist
        
    Raises:
        RedisError: If cache operation fails
    """
    try:
        return bool(await redis_client.delete(key))
    except RedisError as e:
        raise RedisError(f"Failed to delete cache key {key}: {str(e)}")

# PUBLIC_INTERFACE
async def init_cache() -> None:
    """
    Initialize cache connection and verify connectivity.
    
    Raises:
        RedisError: If Redis connection cannot be established.
    """
    try:
        await redis_client.ping()
    except RedisError as e:
        raise RedisError(f"Failed to initialize Redis connection: {str(e)}")