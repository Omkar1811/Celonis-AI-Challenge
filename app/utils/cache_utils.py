from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import Redis
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
import os
from functools import wraps
import logging
import time
import socket

logger = logging.getLogger(__name__)

# Get Redis configuration from environment variables or use defaults
REDIS_HOST = os.getenv("REDIS_HOST", "redis")  # Changed default from localhost to redis
REDIS_PORT = int(os.getenv("REDIS_PORT", 2000))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # Default 1 hour
REDIS_CONNECTION_RETRIES = int(os.getenv("REDIS_CONNECTION_RETRIES", 3))
REDIS_RETRY_DELAY = int(os.getenv("REDIS_RETRY_DELAY", 2))

redis_client = None

def try_resolve_redis_host():
    """Try to resolve Redis host, with fallback to localhost if needed"""
    global REDIS_HOST
    
    # Log the current Redis host
    logger.info(f"Attempting to resolve Redis host: {REDIS_HOST}")
    
    # Try to resolve the configured host
    try:
        socket.gethostbyname(REDIS_HOST)
        logger.info(f"Successfully resolved Redis host {REDIS_HOST}")
        return True
    except socket.gaierror:
        # If 'redis' hostname can't be resolved, try 'localhost' as fallback
        if REDIS_HOST != "localhost":
            prev_host = REDIS_HOST
            REDIS_HOST = "localhost"
            logger.warning(f"Cannot resolve '{prev_host}', falling back to {REDIS_HOST}")
            
            # Try to resolve localhost
            try:
                socket.gethostbyname(REDIS_HOST)
                logger.info(f"Successfully resolved fallback Redis host {REDIS_HOST}")
                return True
            except socket.gaierror:
                logger.error(f"Cannot resolve fallback Redis host {REDIS_HOST}")
                return False
        else:
            logger.error(f"Cannot resolve Redis host {REDIS_HOST}")
            return False

def init_cache(app):
    """Initialize FastAPI Cache with Redis backend"""
    global redis_client
    
    # Try to resolve the Redis hostname first
    try_resolve_redis_host()
    
    # Log the Redis connection parameters for debugging
    logger.info(f"Attempting to connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"Redis password set: {'Yes' if REDIS_PASSWORD else 'No'}")
    
    # Try to connect to Redis with retries
    for attempt in range(REDIS_CONNECTION_RETRIES):
        try:
            redis_client = Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                decode_responses=True,
                socket_timeout=5,  # Add timeout to prevent hanging
                socket_connect_timeout=5
            )
            
            # Test connection
            redis_client.ping()
            
            # Initialize FastAPI Cache
            FastAPICache.init(
                RedisBackend(redis_client),
                prefix="fastapi-cache",
                expire=CACHE_TTL
            )
            
            logger.info(f"Cache successfully initialized with Redis at {REDIS_HOST}:{REDIS_PORT}")
            return True
            
        except Exception as e:
            logger.warning(f"Redis connection attempt {attempt+1}/{REDIS_CONNECTION_RETRIES} failed: {str(e)}")
            
            if attempt < REDIS_CONNECTION_RETRIES - 1:
                logger.info(f"Retrying in {REDIS_RETRY_DELAY} seconds...")
                time.sleep(REDIS_RETRY_DELAY)
            else:
                logger.error(f"Failed to initialize cache after {REDIS_CONNECTION_RETRIES} attempts. The application will continue without caching.")
                redis_client = None
                return False

def generate_cache_key(func_name: str, args: List[Any], kwargs: Dict[str, Any]) -> str:
    """Generate a cache key based on function name and arguments"""
    # Create a string representation of the arguments
    args_str = json.dumps(args, sort_keys=True)
    kwargs_str = json.dumps(kwargs, sort_keys=True)
    
    # Generate a hash
    key = f"{func_name}:{args_str}:{kwargs_str}"
    return hashlib.md5(key.encode()).hexdigest()

def cache_result(ttl: Optional[int] = None):
    """
    Custom cache decorator that works with Redis
    
    Args:
        ttl: Time to live in seconds. If None, uses default CACHE_TTL
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if Redis is not available
            if redis_client is None:
                logger.debug(f"Redis not available, executing {func.__name__} without caching")
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    try:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return json.loads(cached_result)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode cached result for {func.__name__}")
            except Exception as e:
                logger.warning(f"Error retrieving from cache: {str(e)}")
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            # Store in cache
            try:
                redis_client.setex(
                    cache_key, 
                    ttl or CACHE_TTL,
                    json.dumps(result)
                )
                logger.debug(f"Cached result for {func.__name__}")
            except Exception as e:
                logger.warning(f"Failed to cache result: {str(e)}")
                
            return result
        return wrapper
    return decorator

def clear_cache(pattern: str = "*"):
    """Clear cache entries matching the given pattern"""
    if redis_client is None:
        logger.warning("Cannot clear cache: Redis client not initialized")
        return
        
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache entries")
        else:
            logger.info("No cache entries to clear")
    except Exception as e:
        logger.warning(f"Failed to clear cache: {str(e)}")