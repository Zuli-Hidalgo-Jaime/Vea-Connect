"""
Telemetry module for WhatsApp Event Grid webhook.

This module provides centralized telemetry tracking for the WhatsApp webhook
using the existing Application Insights service.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Application Insights service
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from services.application_insights import ApplicationInsightsService
    app_insights = ApplicationInsightsService()
except ImportError:
    logger.warning("Application Insights service not available, using local logging only")
    app_insights = None


class WhatsAppTelemetry:
    """
    Telemetry tracking for WhatsApp webhook events.
    
    Provides methods for tracking incoming messages, replies, RAG searches,
    LLM calls, and errors with proper timing and metadata.
    """
    
    def __init__(self):
        """Initialize telemetry service."""
        self.app_insights = app_insights
    
    def track_incoming_message(self, sender: str, has_text: bool, schema_used: Optional[str] = None) -> None:
        """
        Track incoming WhatsApp message.
        
        Args:
            sender: Sender phone number (normalized)
            has_text: Whether the message contains text
            schema_used: ACS payload schema used for parsing
        """
        properties = {
            'sender': sender,
            'has_text': has_text,
            'schema_used': schema_used or 'unknown',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.app_insights:
            self.app_insights.track_event('wa.incoming', properties)
        else:
            logger.info(f"wa.incoming: {properties}")
    
    def track_reply(self, sender: str, message_length: int, dry_run: bool, status: str, duration_ms: Optional[float] = None) -> None:
        """
        Track WhatsApp reply sent.
        
        Args:
            sender: Recipient phone number
            message_length: Length of the reply message
            dry_run: Whether this was a dry run (not actually sent)
            status: Success/failure status
            duration_ms: Time taken to send the message
        """
        properties = {
            'sender': sender,
            'len': message_length,
            'dry_run': dry_run,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        measurements = {}
        if duration_ms is not None:
            measurements['duration_ms'] = duration_ms
        
        if self.app_insights:
            self.app_insights.track_event('wa.reply', properties, measurements)
        else:
            logger.info(f"wa.reply: {properties}, measurements: {measurements}")
    
    def track_rag_search(self, query: str, hits: int, duration_ms: float, success: bool = True) -> None:
        """
        Track RAG search operation.
        
        Args:
            query: Search query
            hits: Number of results found
            duration_ms: Time taken for search
            success: Whether search was successful
        """
        properties = {
            'query': query[:100] + '...' if len(query) > 100 else query,  # Truncate long queries
            'hits': hits,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        measurements = {
            'duration_ms': duration_ms
        }
        
        if self.app_insights:
            self.app_insights.track_event('rag.search', properties, measurements)
        else:
            logger.info(f"rag.search: {properties}, measurements: {measurements}")
    
    def track_llm_call(self, user_message: str, response_length: int, duration_ms: float, approx_tokens: Optional[int] = None, success: bool = True) -> None:
        """
        Track LLM call to Azure OpenAI.
        
        Args:
            user_message: User's input message
            response_length: Length of AI response
            duration_ms: Time taken for LLM call
            approx_tokens: Approximate token count (if available)
            success: Whether LLM call was successful
        """
        properties = {
            'user_message': user_message[:100] + '...' if len(user_message) > 100 else user_message,
            'response_length': response_length,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        measurements = {
            'duration_ms': duration_ms
        }
        
        if approx_tokens is not None:
            measurements['approx_tokens'] = approx_tokens
        
        if self.app_insights:
            self.app_insights.track_event('llm.call', properties, measurements)
        else:
            logger.info(f"llm.call: {properties}, measurements: {measurements}")
    
    def track_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track error with context.
        
        Args:
            error: Exception that occurred
            context: Additional context information
        """
        properties = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if context:
            properties.update(context)
        
        if self.app_insights:
            self.app_insights.track_exception(error, properties)
        else:
            logger.error(f"error: {properties}")
    
    def track_rag_skipped(self, reason: str) -> None:
        """
        Track when RAG is skipped.
        
        Args:
            reason: Reason why RAG was skipped
        """
        properties = {
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.app_insights:
            self.app_insights.track_event('rag.skipped', properties)
        else:
            logger.info(f"rag.skipped: {properties}")
    
    def track_conversation_history(self, phone_number: str, history_length: int, operation: str) -> None:
        """
        Track conversation history operations.
        
        Args:
            phone_number: User's phone number
            history_length: Number of messages in history
            operation: Operation performed (get, update, clear)
        """
        properties = {
            'phone_number': phone_number,
            'history_length': history_length,
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.app_insights:
            self.app_insights.track_event('wa.conversation', properties)
        else:
            logger.info(f"wa.conversation: {properties}")
    
    def track_processing_time(self, event_type: str, duration_ms: float, success: bool = True) -> None:
        """
        Track overall processing time for events.
        
        Args:
            event_type: Type of event processed
            duration_ms: Total processing time
            success: Whether processing was successful
        """
        properties = {
            'event_type': event_type,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        measurements = {
            'duration_ms': duration_ms
        }
        
        if self.app_insights:
            self.app_insights.track_event('wa.processing', properties, measurements)
        else:
            logger.info(f"wa.processing: {properties}, measurements: {measurements}")


# Global telemetry instance
telemetry = WhatsAppTelemetry()


def track_function_execution(func_name: str):
    """
    Decorator to track function execution time and success.
    
    Args:
        func_name: Name of the function being tracked
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                telemetry.track_error(e, {'function': func_name})
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                telemetry.track_processing_time(func_name, duration_ms, success)
        return wrapper
    return decorator
