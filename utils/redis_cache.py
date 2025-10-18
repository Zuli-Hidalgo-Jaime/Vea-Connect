"""
Redis Cache utilities for embeddings and AI Search responses.
Simple KV operations without RediSearch dependency.
"""

import redis
import json
import hashlib
import os
import typing as t
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Redis client initialization
try:
    redis_url = getattr(settings, 'REDIS_URL', os.getenv('AZURE_REDIS_URL'))
    if redis_url:
        # Parse URL to handle SSL configuration properly
        from urllib.parse import urlparse
        parsed_url = urlparse(redis_url)
        
        # Configure SSL based on URL scheme
        ssl_config = {}
        if parsed_url.scheme == 'rediss':
            ssl_config = {
                'ssl': True,
                'ssl_cert_reqs': None,
                'ssl_ca_certs': None
            }
        
        _r = redis.from_url(redis_url, decode_responses=True, **ssl_config)
        # Test connection
        _r.ping()
        logger.info("Redis connection established successfully")
    else:
        _r = None
        logger.warning("Redis URL not configured, cache disabled")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    _r = None

def _h(txt: str) -> str:
    """Generate short reproducible hash for text."""
    return hashlib.sha256(txt.encode('utf-8')).hexdigest()[:16]

def get_emb(text: str) -> t.Optional[list]:
    """
    Get cached embedding for text.
    
    Args:
        text: Input text to get embedding for
        
    Returns:
        List of floats (embedding vector) or None if not cached
    """
    if not _r:
        return None
    
    try:
        key = f"emb:{_h(text)}"
        val = _r.get(key)
        if val:
            logger.debug(f"Cache hit for embedding: {key}")
            return json.loads(val)
        else:
            logger.debug(f"Cache miss for embedding: {key}")
            return None
    except Exception as e:
        logger.error(f"Error getting embedding from cache: {e}")
        return None

def set_emb(text: str, vec: list, ttl: int = None):
    """
    Cache embedding for text.
    
    Args:
        text: Input text
        vec: Embedding vector (list of floats)
        ttl: Time to live in seconds (default from settings)
    """
    if not _r:
        return
    
    try:
        if ttl is None:
            ttl = getattr(settings, 'REDIS_TTL_SECS', 86400)
        
        key = f"emb:{_h(text)}"
        _r.setex(key, ttl, json.dumps(vec))
        logger.debug(f"Cached embedding: {key} (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"Error setting embedding in cache: {e}")

def get_ans(q: str) -> t.Optional[dict]:
    """
    Get cached AI Search response for query.
    
    Args:
        q: Search query
        
    Returns:
        Cached response dict or None if not cached
    """
    if not _r:
        return None
    
    try:
        key = f"ans:{_h(q)}"
        val = _r.get(key)
        if val:
            logger.debug(f"Cache hit for AI Search response: {key}")
            return json.loads(val)
        else:
            logger.debug(f"Cache miss for AI Search response: {key}")
            return None
    except Exception as e:
        logger.error(f"Error getting AI Search response from cache: {e}")
        return None

def set_ans(q: str, ans: dict, ttl: int = None):
    """
    Cache AI Search response for query.
    
    Args:
        q: Search query
        ans: Response from AI Search
        ttl: Time to live in seconds (default from settings)
    """
    if not _r:
        return
    
    try:
        if ttl is None:
            ttl = getattr(settings, 'REDIS_TTL_SECS', 86400)
        
        key = f"ans:{_h(q)}"
        _r.setex(key, ttl, json.dumps(ans))
        logger.debug(f"Cached AI Search response: {key} (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"Error setting AI Search response in cache: {e}")

def clear_cache(pattern: str = None):
    """
    Clear cache entries.
    
    Args:
        pattern: Redis pattern to match (e.g., "emb:*", "ans:*")
    """
    if not _r:
        return
    
    try:
        if pattern:
            keys = _r.keys(pattern)
        else:
            keys = _r.keys("emb:*") + _r.keys("ans:*")
        
        if keys:
            _r.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache entries")
        else:
            logger.info("No cache entries to clear")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")

def get_cache_stats() -> dict:
    """
    Get cache statistics.
    
    Returns:
        Dict with cache statistics
    """
    if not _r:
        return {"error": "Redis not available"}
    
    try:
        emb_keys = len(_r.keys("emb:*"))
        ans_keys = len(_r.keys("ans:*"))
        
        return {
            "embedding_cache_entries": emb_keys,
            "ai_search_cache_entries": ans_keys,
            "total_cache_entries": emb_keys + ans_keys,
            "redis_connected": True
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}
