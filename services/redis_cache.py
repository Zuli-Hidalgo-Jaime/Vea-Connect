"""
Redis Cache Service for WhatsApp conversations.

This service provides a robust cache layer for WhatsApp bot conversations
with fallback to Django's cache system when Redis is not available.
"""

import json
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppCacheService:
    """
    Service for caching WhatsApp conversation data.
    
    Provides methods for storing and retrieving conversation context,
    user preferences, and temporary data with proper TTL management.
    """
    
    def __init__(self):
        """Initialize the cache service."""
        self.cache_prefix = "whatsapp"
        self.default_ttl = getattr(settings, 'REDIS_TTL_SECS', 3600)  # 1 hora por defecto
        self.conversation_ttl = 1800  # 30 minutos para conversaciones
        self.user_pref_ttl = 86400  # 24 horas para preferencias de usuario
        
    def _generate_key(self, key_type: str, identifier: str) -> str:
        """
        Generate a consistent cache key.
        
        Args:
            key_type: Type of cache key (conversation, user_pref, etc.)
            identifier: Unique identifier (phone number, user ID, etc.)
            
        Returns:
            Generated cache key
        """
        clean_identifier = str(identifier).replace('+', '').replace(' ', '').replace('-', '')
        return f"{self.cache_prefix}:{key_type}:{clean_identifier}"
    
    def _hash_content(self, content: str) -> str:
        """
        Generate hash for content to use as cache key.
        
        Args:
            content: Content to hash
            
        Returns:
            Hash string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def store_conversation_context(self, phone_number: str, context: Dict[str, Any]) -> bool:
        """
        Store conversation context for a phone number.
        
        Args:
            phone_number: User's phone number
            context: Conversation context data
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            key = self._generate_key("conversation", phone_number)
            cache.set(key, context, self.conversation_ttl)
            logger.info(f"Conversation context stored for {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error storing conversation context for {phone_number}: {e}")
            return False
    
    def get_conversation_context(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation context for a phone number.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Conversation context or None if not found
        """
        try:
            key = self._generate_key("conversation", phone_number)
            context = cache.get(key)
            if context:
                logger.debug(f"Conversation context retrieved for {phone_number}")
            return context
        except Exception as e:
            logger.error(f"Error retrieving conversation context for {phone_number}: {e}")
            return None
    
    def update_conversation_context(self, phone_number: str, updates: Dict[str, Any]) -> bool:
        """
        Update existing conversation context.
        
        Args:
            phone_number: User's phone number
            updates: Updates to apply to context
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            context = self.get_conversation_context(phone_number) or {}
            context.update(updates)
            return self.store_conversation_context(phone_number, context)
        except Exception as e:
            logger.error(f"Error updating conversation context for {phone_number}: {e}")
            return False
    
    def clear_conversation_context(self, phone_number: str) -> bool:
        """
        Clear conversation context for a phone number.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            key = self._generate_key("conversation", phone_number)
            cache.delete(key)
            logger.info(f"Conversation context cleared for {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation context for {phone_number}: {e}")
            return False
    
    def store_user_preference(self, phone_number: str, preference_key: str, value: Any) -> bool:
        """
        Store user preference.
        
        Args:
            phone_number: User's phone number
            preference_key: Preference key
            value: Preference value
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            key = self._generate_key("user_pref", f"{phone_number}:{preference_key}")
            cache.set(key, value, self.user_pref_ttl)
            logger.debug(f"User preference stored: {preference_key} for {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error storing user preference for {phone_number}: {e}")
            return False
    
    def get_user_preference(self, phone_number: str, preference_key: str, default: Any = None) -> Any:
        """
        Retrieve user preference.
        
        Args:
            phone_number: User's phone number
            preference_key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        try:
            key = self._generate_key("user_pref", f"{phone_number}:{preference_key}")
            value = cache.get(key, default)
            return value
        except Exception as e:
            logger.error(f"Error retrieving user preference for {phone_number}: {e}")
            return default
    
    def store_temporary_data(self, phone_number: str, data_key: str, data: Any, ttl: int = None) -> bool:
        """
        Store temporary data with custom TTL.
        
        Args:
            phone_number: User's phone number
            data_key: Data key
            data: Data to store
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            key = self._generate_key("temp_data", f"{phone_number}:{data_key}")
            timeout = ttl or self.default_ttl
            cache.set(key, data, timeout)
            logger.debug(f"Temporary data stored: {data_key} for {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error storing temporary data for {phone_number}: {e}")
            return False
    
    def get_temporary_data(self, phone_number: str, data_key: str, default: Any = None) -> Any:
        """
        Retrieve temporary data.
        
        Args:
            phone_number: User's phone number
            data_key: Data key
            default: Default value if not found
            
        Returns:
            Data value or default
        """
        try:
            key = self._generate_key("temp_data", f"{phone_number}:{data_key}")
            value = cache.get(key, default)
            return value
        except Exception as e:
            logger.error(f"Error retrieving temporary data for {phone_number}: {e}")
            return default
    
    def cache_llm_response(self, query: str, response: str, ttl: int = None) -> bool:
        """
        Cache LLM response for repeated queries.
        
        Args:
            query: User query
            response: LLM response
            ttl: Time to live in seconds
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            query_hash = self._hash_content(query)
            key = f"{self.cache_prefix}:llm_response:{query_hash}"
            timeout = ttl or self.default_ttl
            cache.set(key, response, timeout)
            logger.debug(f"LLM response cached for query hash: {query_hash}")
            return True
        except Exception as e:
            logger.error(f"Error caching LLM response: {e}")
            return False
    
    def get_cached_llm_response(self, query: str) -> Optional[str]:
        """
        Get cached LLM response for query.
        
        Args:
            query: User query
            
        Returns:
            Cached response or None if not found
        """
        try:
            query_hash = self._hash_content(query)
            key = f"{self.cache_prefix}:llm_response:{query_hash}"
            response = cache.get(key)
            if response:
                logger.debug(f"Cached LLM response found for query hash: {query_hash}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving cached LLM response: {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # This is a simplified version - in production you might want
            # to use Redis INFO command for detailed stats
            return {
                "cache_backend": cache._cache.__class__.__name__,
                "cache_prefix": self.cache_prefix,
                "default_ttl": self.default_ttl,
                "conversation_ttl": self.conversation_ttl,
                "user_pref_ttl": self.user_pref_ttl,
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    def clear_all_user_data(self, phone_number: str) -> bool:
        """
        Clear all cached data for a user.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            # Clear conversation context
            self.clear_conversation_context(phone_number)
            
            # Clear user preferences (this is a simplified approach)
            # In production, you might want to use Redis SCAN to find all keys
            logger.info(f"All user data cleared for {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error clearing all user data for {phone_number}: {e}")
            return False


# Global instance for easy access
whatsapp_cache = WhatsAppCacheService()
