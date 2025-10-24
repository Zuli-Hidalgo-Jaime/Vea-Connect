"""
User Service for WhatsApp Bot.

This module provides user management functionality for WhatsApp users,
including registration, updates, and retrieval from PostgreSQL.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.db import connection, transaction as db_transaction
from contextlib import closing
from django.core.cache import cache

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for managing WhatsApp users in PostgreSQL.
    
    This service handles user registration, updates, and retrieval
    with proper error handling and caching.
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize User Service.
        
        Args:
            cache_ttl: Cache TTL in seconds for user data
        """
        self.cache_ttl = cache_ttl
    
    def register_or_update_user(self, phone_number: str, **kwargs) -> bool:
        """
        Register a new user or update existing user.
        
        Args:
            phone_number: User's phone number
            **kwargs: Additional user data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if user exists
            existing_user = self.get_user_by_phone(phone_number)
            
            if existing_user:
                # Update existing user
                return self._update_user(phone_number, **kwargs)
            else:
                # Register new user
                return self._register_user(phone_number, **kwargs)
                
        except Exception as e:
            logger.error(f"Error in register_or_update_user for {phone_number}: {e}")
            return False
    
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get user by phone number.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            # Try cache first
            cache_key = f"whatsapp_user:{phone_number}"
            cached_user = cache.get(cache_key)
            
            if cached_user:
                logger.info(f"Retrieved user from cache: {phone_number}")
                return cached_user
            
            # Query database
            with closing(connection.cursor()) as cursor:
                cursor.execute("""
                    SELECT 
                        id, phone_number, first_name, last_name, email,
                        is_active, created_at, updated_at, last_interaction,
                        interaction_count, preferred_language
                    FROM whatsapp_users 
                    WHERE phone_number = %s AND is_active = true
                """, [phone_number])
                
                row = cursor.fetchone()
                
                if row:
                    user_data = {
                        'id': row[0],
                        'phone_number': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'email': row[4],
                        'is_active': row[5],
                        'created_at': row[6],
                        'updated_at': row[7],
                        'last_interaction': row[8],
                        'interaction_count': row[9],
                        'preferred_language': row[10]
                    }
                    
                    # Cache user data
                    cache.set(cache_key, user_data, self.cache_ttl)
                    
                    logger.info(f"Retrieved user from database: {phone_number}")
                    return user_data
                else:
                    logger.info(f"User not found: {phone_number}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting user by phone {phone_number}: {e}")
            return None
    
    def get_user_interaction_history(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user interaction history.
        
        Args:
            phone_number: User's phone number
            limit: Maximum number of interactions to return
            
        Returns:
            List of interaction dictionaries
        """
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute("""
                    SELECT 
                        id, phone_number, message_text, intent_detected,
                        template_used, response_text, response_id,
                        fallback_used, processing_time_ms, success,
                        created_at
                    FROM whatsapp_interactions 
                    WHERE phone_number = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, [phone_number, limit])
                
                rows = cursor.fetchall()
                
                interactions = []
                for row in rows:
                    interactions.append({
                        'id': str(row[0]),
                        'phone_number': row[1],
                        'message_text': row[2],
                        'intent_detected': row[3],
                        'template_used': row[4],
                        'response_text': row[5],
                        'response_id': row[6],
                        'fallback_used': row[7],
                        'processing_time_ms': row[8],
                        'success': row[9],
                        'created_at': row[10].isoformat() if row[10] else None
                    })
                
                logger.info(f"Retrieved {len(interactions)} interactions for {phone_number}")
                return interactions
                
        except Exception as e:
            logger.error(f"Error getting interaction history for {phone_number}: {e}")
            return []
    
    def update_user_interaction_count(self, phone_number: str) -> bool:
        """
        Update user interaction count.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with db_transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
                with closing(connection.cursor()) as cursor:
                    cursor.execute("""
                        UPDATE whatsapp_users 
                        SET 
                            interaction_count = COALESCE(interaction_count, 0) + 1,
                            last_interaction = NOW(),
                            updated_at = NOW()
                        WHERE phone_number = %s
                    """, [phone_number])
                    
                    if cursor.rowcount > 0:
                        # Clear cache
                        cache_key = f"whatsapp_user:{phone_number}"
                        cache.delete(cache_key)
                        
                        logger.info(f"Updated interaction count for {phone_number}")
                        return True
                    else:
                        logger.warning(f"No user found to update interaction count: {phone_number}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error updating interaction count for {phone_number}: {e}")
            return False
    
    def get_user_statistics(self, phone_number: str) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            User statistics dictionary
        """
        try:
            user = self.get_user_by_phone(phone_number)
            if not user:
                return {
                    'phone_number': phone_number,
                    'exists': False,
                    'total_interactions': 0,
                    'successful_interactions': 0,
                    'template_usage': 0,
                    'fallback_usage': 0
                }
            
            # Get interaction statistics
            with closing(connection.cursor()) as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_interactions,
                        COUNT(CASE WHEN success = true THEN 1 END) as successful_interactions,
                        COUNT(CASE WHEN template_used IS NOT NULL THEN 1 END) as template_usage,
                        COUNT(CASE WHEN fallback_used = true THEN 1 END) as fallback_usage
                    FROM whatsapp_interactions 
                    WHERE phone_number = %s
                """, [phone_number])
                
                row = cursor.fetchone()
                
                stats = {
                    'phone_number': phone_number,
                    'exists': True,
                    'user_data': user,
                    'total_interactions': row[0] if row else 0,
                    'successful_interactions': row[1] if row else 0,
                    'template_usage': row[2] if row else 0,
                    'fallback_usage': row[3] if row else 0
                }
                
                # Calculate success rate
                if stats['total_interactions'] > 0:
                    stats['success_rate'] = (stats['successful_interactions'] / stats['total_interactions']) * 100
                else:
                    stats['success_rate'] = 0
                
                logger.info(f"Retrieved statistics for {phone_number}")
                return stats
                
        except Exception as e:
            logger.error(f"Error getting user statistics for {phone_number}: {e}")
            return {
                'phone_number': phone_number,
                'exists': False,
                'error': str(e)
            }
    
    def _register_user(self, phone_number: str, **kwargs) -> bool:
        """
        Register a new user.
        
        Args:
            phone_number: User's phone number
            **kwargs: Additional user data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with db_transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
                with closing(connection.cursor()) as cursor:
                    cursor.execute("""
                        INSERT INTO whatsapp_users (
                            phone_number, first_name, last_name, email,
                            is_active, created_at, updated_at, last_interaction,
                            interaction_count, preferred_language
                        ) VALUES (
                            %s, %s, %s, %s, %s, NOW(), NOW(), NOW(), 1, %s
                        )
                    """, [
                        phone_number,
                        kwargs.get('first_name'),
                        kwargs.get('last_name'),
                        kwargs.get('email'),
                        True,
                        kwargs.get('preferred_language', 'es')
                    ])
                    
                    logger.info(f"Registered new user: {phone_number}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error registering user {phone_number}: {e}")
            return False
    
    def _update_user(self, phone_number: str, **kwargs) -> bool:
        """
        Update existing user.
        
        Args:
            phone_number: User's phone number
            **kwargs: Additional user data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with db_transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
                # Build update query dynamically
                update_fields = []
                update_values = []
                
                if 'first_name' in kwargs:
                    update_fields.append("first_name = %s")
                    update_values.append(kwargs['first_name'])
                
                if 'last_name' in kwargs:
                    update_fields.append("last_name = %s")
                    update_values.append(kwargs['last_name'])
                
                if 'email' in kwargs:
                    update_fields.append("email = %s")
                    update_values.append(kwargs['email'])
                
                if 'preferred_language' in kwargs:
                    update_fields.append("preferred_language = %s")
                    update_values.append(kwargs['preferred_language'])
                
                # Always update these fields
                update_fields.append("updated_at = NOW()")
                update_fields.append("last_interaction = NOW()")
                
                if update_fields:
                    update_values.append(phone_number)
                    
                    with closing(connection.cursor()) as cursor:
                        query = f"""
                            UPDATE whatsapp_users 
                            SET {', '.join(update_fields)}
                            WHERE phone_number = %s
                        """
                        cursor.execute(query, update_values)
                        
                        if cursor.rowcount > 0:
                            # Clear cache
                            cache_key = f"whatsapp_user:{phone_number}"
                            cache.delete(cache_key)
                            
                            logger.info(f"Updated user: {phone_number}")
                            return True
                        else:
                            logger.warning(f"No user found to update: {phone_number}")
                            return False
                else:
                    logger.info(f"No fields to update for user: {phone_number}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error updating user {phone_number}: {e}")
            return False
    
    def deactivate_user(self, phone_number: str) -> bool:
        """
        Deactivate a user.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with db_transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
                with closing(connection.cursor()) as cursor:
                    cursor.execute("""
                        UPDATE whatsapp_users 
                        SET is_active = false, updated_at = NOW()
                        WHERE phone_number = %s
                    """, [phone_number])
                    
                    if cursor.rowcount > 0:
                        # Clear cache
                        cache_key = f"whatsapp_user:{phone_number}"
                        cache.delete(cache_key)
                        
                        logger.info(f"Deactivated user: {phone_number}")
                        return True
                    else:
                        logger.warning(f"No user found to deactivate: {phone_number}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error deactivating user {phone_number}: {e}")
            return False
    
    def get_active_users_count(self) -> int:
        """
        Get count of active users.
        
        Returns:
            Number of active users
        """
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM whatsapp_users 
                    WHERE is_active = true
                """)
                
                row = cursor.fetchone()
                count = row[0] if row else 0
                
                logger.info(f"Active users count: {count}")
                return count
                
        except Exception as e:
            logger.error(f"Error getting active users count: {e}")
            return 0
    
    def get_users_by_interaction_count(self, min_interactions: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get users by minimum interaction count.
        
        Args:
            min_interactions: Minimum number of interactions
            limit: Maximum number of users to return
            
        Returns:
            List of user dictionaries
        """
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute("""
                    SELECT 
                        phone_number, first_name, last_name, email,
                        interaction_count, last_interaction, created_at
                    FROM whatsapp_users 
                    WHERE is_active = true 
                    AND interaction_count >= %s
                    ORDER BY interaction_count DESC, last_interaction DESC
                    LIMIT %s
                """, [min_interactions, limit])
                
                rows = cursor.fetchall()
                
                users = []
                for row in rows:
                    users.append({
                        'phone_number': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'email': row[3],
                        'interaction_count': row[4],
                        'last_interaction': row[5].isoformat() if row[5] else None,
                        'created_at': row[6].isoformat() if row[6] else None
                    })
                
                logger.info(f"Retrieved {len(users)} users with {min_interactions}+ interactions")
                return users
                
        except Exception as e:
            logger.error(f"Error getting users by interaction count: {e}")
            return [] 