"""
Helper functions for WhatsApp Event Grid webhook.

This module provides utility functions for extracting message data and
generating AI responses with RAG support.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import services
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from services.redis_cache import WhatsAppCacheService
    from services.search_index_service import SearchIndexService
    from telemetry import telemetry
except ImportError:
    logger.warning("Some services not available, using fallbacks")
    WhatsAppCacheService = None
    SearchIndexService = None
    telemetry = None


def extract_incoming_text(event_payload: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Extract incoming text and sender from ACS event payload.
    
    This function provides a tolerant parser for multiple ACS Advanced Messaging schemas:
    - Legacy: data.messageBody and data.from
    - Standard: data.message.content.text and data.message.from.phoneNumber
    - Alternative: data.content with text/body structure
    
    Args:
        event_payload: Raw event payload from Event Grid
        
    Returns:
        Tuple of (sender_e164, text, meta) where:
        - sender_e164: Normalized phone number in E.164 format
        - text: Extracted message text
        - meta: Additional metadata about the parsing
    """
    meta = {
        'schema_used': None,
        'parsing_success': False,
        'errors': []
    }
    
    try:
        data = event_payload.get('data', {})
        
        # Schema 1: Legacy format - data.messageBody and data.from
        if 'messageBody' in data and 'from' in data:
            text = data.get('messageBody', '').strip()
            sender = data.get('from', '').strip()
            if text and sender:
                meta['schema_used'] = 'legacy'
                meta['parsing_success'] = True
                return _normalize_phone_number(sender), text, meta
        
        # Schema 2: Standard format - data.message.content.text and data.message.from.phoneNumber
        if 'message' in data:
            message = data.get('message', {})
            if isinstance(message, dict):
                content = message.get('content', {})
                if isinstance(content, dict) and 'text' in content:
                    text = content.get('text', '').strip()
                    sender = message.get('from', {}).get('phoneNumber', '').strip()
                    if text and sender:
                        meta['schema_used'] = 'standard'
                        meta['parsing_success'] = True
                        return _normalize_phone_number(sender), text, meta
        
        # Schema 3: Alternative format - data.content with text/body
        if 'content' in data:
            content = data.get('content', {})
            if isinstance(content, dict):
                # Try text field first
                if 'text' in content:
                    text = content.get('text', '').strip()
                    sender = data.get('from', '').strip()
                    if text and sender:
                        meta['schema_used'] = 'content_text'
                        meta['parsing_success'] = True
                        return _normalize_phone_number(sender), text, meta
                
                # Try body field
                if 'body' in content:
                    text = content.get('body', '').strip()
                    sender = data.get('from', '').strip()
                    if text and sender:
                        meta['schema_used'] = 'content_body'
                        meta['parsing_success'] = True
                        return _normalize_phone_number(sender), text, meta
        
        # Schema 4: Direct text in data
        if 'text' in data:
            text = data.get('text', '').strip()
            sender = data.get('from', '').strip()
            if text and sender:
                meta['schema_used'] = 'direct_text'
                meta['parsing_success'] = True
                return _normalize_phone_number(sender), text, meta
        
        # If no schema matched, log the structure for debugging
        meta['errors'].append(f"No matching schema found. Available keys: {list(data.keys())}")
        logger.warning(f"Could not parse ACS event payload. Available data keys: {list(data.keys())}")
        
        return "", "", meta
        
    except Exception as e:
        meta['errors'].append(f"Exception during parsing: {str(e)}")
        logger.error(f"Error parsing ACS event payload: {e}")
        return "", "", meta


def _normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Phone number in E.164 format (e.g., +525512345678)
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # If it starts with +, assume it's already in international format
    if cleaned.startswith('+'):
        return cleaned
    
    # If it's 10 digits, assume it's a Mexican number
    if len(cleaned) == 10:
        return f"+52{cleaned}"
    
    # If it's 12 digits and starts with 52, add +
    if len(cleaned) == 12 and cleaned.startswith('52'):
        return f"+{cleaned}"
    
    # If it's 11 digits and starts with 1, assume US number
    if len(cleaned) == 11 and cleaned.startswith('1'):
        return f"+{cleaned}"
    
    # Default: return as is with + prefix if not present
    return cleaned if cleaned.startswith('+') else f"+{cleaned}"


def generate_ai_response(session_id: str, user_text: str, *, use_rag: bool = True) -> str:
    """
    Generate AI response for user message with optional RAG support.
    
    Args:
        session_id: Session identifier (usually phone number)
        user_text: User's input text
        use_rag: Whether to use RAG for context retrieval
        
    Returns:
        Generated AI response text
    """
    start_time = time.time()
    
    try:
        # Get conversation history
        conversation_history = _get_conversation_history(session_id)
        
        # Get RAG context if enabled
        rag_context = None
        if use_rag and RAG_ENABLED:
            rag_start_time = time.time()
            rag_context = _get_rag_context(user_text)
            rag_duration_ms = (time.time() - rag_start_time) * 1000
            
            if telemetry:
                if rag_context:
                    telemetry.track_rag_search(user_text, len(rag_context.split()), rag_duration_ms, True)
                else:
                    telemetry.track_rag_skipped("no_results")
        
        # Generate AI response
        llm_start_time = time.time()
        ai_response = _generate_ai_response_with_context(user_text, conversation_history, rag_context)
        llm_duration_ms = (time.time() - llm_start_time) * 1000
        
        # Track LLM call
        if telemetry:
            telemetry.track_llm_call(
                user_text, 
                len(ai_response), 
                llm_duration_ms, 
                approx_tokens=len(ai_response.split()) * 1.3,  # Rough estimate
                success=True
            )
        
        # Update conversation history
        _update_conversation_history(session_id, user_text, ai_response)
        
        total_duration_ms = (time.time() - start_time) * 1000
        logger.info(f"AI response generated in {total_duration_ms:.2f}ms for session {session_id}")
        
        return ai_response
        
    except Exception as e:
        if telemetry:
            telemetry.track_error(e, {
                'session_id': session_id,
                'user_text': user_text[:100],
                'use_rag': use_rag
            })
        logger.error(f"Error generating AI response: {e}")
        return "Lo siento, hubo un error procesando tu mensaje. Por favor intenta de nuevo."


def _get_conversation_history(phone_number: str) -> List[Dict[str, str]]:
    """
    Get conversation history from Redis cache.
    
    Args:
        phone_number: User's phone number
        
    Returns:
        List of conversation messages
    """
    if not WhatsAppCacheService:
        logger.warning("WhatsAppCacheService not available, returning empty history")
        return []
    
    try:
        cache_service = WhatsAppCacheService()
        context = cache_service.get_conversation_context(phone_number)
        
        if context and 'messages' in context:
            messages = context['messages']
            if telemetry:
                telemetry.track_conversation_history(phone_number, len(messages), 'get')
            return messages
        else:
            if telemetry:
                telemetry.track_conversation_history(phone_number, 0, 'get_empty')
            return []
            
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []


def _update_conversation_history(phone_number: str, user_message: str, bot_response: str) -> bool:
    """
    Update conversation history in Redis cache.
    
    Args:
        phone_number: User's phone number
        user_message: User's message
        bot_response: Bot's response
        
    Returns:
        True if updated successfully, False otherwise
    """
    if not WhatsAppCacheService:
        logger.warning("WhatsAppCacheService not available, skipping history update")
        return False
    
    try:
        cache_service = WhatsAppCacheService()
        
        # Get existing context
        context = cache_service.get_conversation_context(phone_number) or {}
        messages = context.get('messages', [])
        
        # Add new messages
        messages.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        messages.append({
            'role': 'assistant',
            'content': bot_response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 messages to avoid context overflow
        if len(messages) > 10:
            messages = messages[-10:]
        
        # Update context
        context['messages'] = messages
        context['last_updated'] = datetime.utcnow().isoformat()
        
        success = cache_service.store_conversation_context(phone_number, context)
        
        if telemetry:
            telemetry.track_conversation_history(phone_number, len(messages), 'update')
        
        return success
        
    except Exception as e:
        logger.error(f"Error updating conversation history: {e}")
        return False


def _get_rag_context(query: str) -> Optional[str]:
    """
    Get RAG context from Azure AI Search.
    
    Args:
        query: Search query
        
    Returns:
        Context string or None if no results
    """
    if not SearchIndexService:
        logger.warning("SearchIndexService not available, skipping RAG")
        return None
    
    try:
        search_service = SearchIndexService()
        results = search_service.search(query, top=3)
        
        if not results:
            return None
        
        # Build context from search results
        context_parts = []
        for result in results:
            content = result.get('content', '')
            if content:
                context_parts.append(content)
        
        if context_parts:
            context = " ".join(context_parts)
            # Limit context size to ~1500 characters
            if len(context) > 1500:
                context = context[:1500] + "..."
            return context
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting RAG context: {e}")
        return None


def _generate_ai_response_with_context(user_message: str, conversation_history: List[Dict[str, str]], rag_context: Optional[str] = None) -> str:
    """
    Generate AI response using Azure OpenAI with context.
    
    Args:
        user_message: User's input message
        conversation_history: Previous conversation messages
        rag_context: RAG context if available
        
    Returns:
        Generated AI response
    """
    try:
        from openai import AzureOpenAI
        
        # Get OpenAI configuration
        endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
        api_key = os.environ.get('AZURE_OPENAI_API_KEY')
        deployment = os.environ.get('AZURE_OPENAI_CHAT_DEPLOYMENT', 'gpt-35-turbo')
        api_version = os.environ.get('AZURE_OPENAI_CHAT_API_VERSION', '2024-02-15-preview')
        
        if not all([endpoint, api_key, deployment]):
            logger.error("OpenAI configuration missing")
            return "Lo siento, el servicio de IA no está configurado correctamente."
        
        # Initialize OpenAI client
        client = AzureOpenAI(
            azure_endpoint=endpoint,  # type: ignore
            api_key=api_key,  # type: ignore
            api_version=api_version  # type: ignore
        )
        
        # Build system prompt
        system_prompt = os.environ.get('BOT_SYSTEM_PROMPT', """
Eres un asistente virtual de VEA Connect, una plataforma de gestión para organizaciones sin fines de lucro.
Tu función es ayudar a los usuarios con información sobre donaciones, eventos, documentos y servicios de la organización.
Responde de manera amigable y profesional en español. Mantén las respuestas concisas pero informativas.
Si no tienes información específica sobre algo, sugiere contactar al equipo de VEA Connect.
""")
        
        # Add RAG context if available
        if rag_context:
            system_prompt += f"\n\nContexto relevante:\n{rag_context}"
        
        # Build messages list
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-6:]:  # Keep last 6 messages for context
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if content:
                messages.append({"role": role, "content": content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        response = client.chat.completions.create(
            model=deployment,  # type: ignore
            messages=messages,  # type: ignore
            max_tokens=500,
            temperature=0.7
        )
        
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        else:
            logger.error("No response content from OpenAI")
            return "Lo siento, no pude generar una respuesta. Por favor intenta de nuevo."
            
    except Exception as e:
        logger.error(f"Error calling OpenAI: {e}")
        return "Lo siento, hubo un error al procesar tu mensaje. Por favor intenta de nuevo."


# Environment variables
RAG_ENABLED = os.getenv('RAG_ENABLED', 'false').lower() == 'true'
