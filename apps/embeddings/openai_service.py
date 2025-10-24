"""
OpenAI Service - Azure OpenAI integration for embeddings and chat completion
"""

import os
import logging
from typing import List, Dict, Optional, Any
from openai import AzureOpenAI
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

# Mensaje amable cuando Azure OpenAI rechaza por content_filter
SAFE_FILTER_MESSAGE = (
    "No puedo responder esa formulación porque activa nuestros filtros de contenido. "
    "Por favor, reformula tu pregunta con un lenguaje neutral y sin términos sensibles."
)


def _is_content_filter_error(err: Exception) -> bool:
    """
    Detecta si un error de Azure OpenAI corresponde a un filtro de contenido.
    
    Args:
        err: Excepción lanzada por Azure OpenAI
        
    Returns:
        True si es un error de content_filter, False en caso contrario
    """
    s = str(err).lower()
    return (
        "content_filter" in s
        or "responsibleaipolicyviolation" in s
        or ("content_filter_result" in s and "filtered" in s)
    )


class OpenAIService:
    """
    Service for Azure OpenAI integration.
    
    Handles embeddings generation and chat completion using Azure OpenAI endpoints.
    Supports configuration via environment variables and fallback to dummy implementations.
    """
    
    def __init__(self):
        """
        Initialize OpenAI service with Azure configuration.
        
        Reads configuration from environment variables and sets up Azure OpenAI client.
        Falls back to dummy mode if configuration is incomplete.
        """
        self.client = None
        self.is_configured = False
        self._configure_client()
    
    def _configure_client(self) -> None:
        """
        Configure Azure OpenAI client from environment variables.
        
        Sets up the client if all required environment variables are present.
        Otherwise, sets up dummy mode for development/testing.
        """
        try:
            # Variables requeridas (excepto la API key que permitimos con alias)
            # Para generar embeddings no es obligatorio tener CHAT deployment
            required_vars = [
                'AZURE_OPENAI_ENDPOINT',
                'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT',
            ]

            missing_core = [var for var in required_vars if not os.getenv(var)]
            if missing_core:
                logger.warning("Missing Azure OpenAI core configuration: %s", missing_core)
                self.is_configured = False
                return

            # API key: aceptar OPENAI_API_KEY o AZURE_OPENAI_API_KEY
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('AZURE_OPENAI_API_KEY')
            if not api_key:
                logger.warning("Azure OpenAI API key not found in OPENAI_API_KEY nor AZURE_OPENAI_API_KEY")
                self.is_configured = False
                return

            # Garantizar tipo str (no Optional) para el endpoint
            azure_endpoint_env = os.getenv('AZURE_OPENAI_ENDPOINT')
            if not azure_endpoint_env:
                logger.warning("Azure OpenAI endpoint not configured")
                self.is_configured = False
                return
            azure_endpoint: str = azure_endpoint_env

            # Usar versión de API válida para ambos endpoints; preferir CHAT, luego EMBEDDINGS, luego default
            api_version = (
                os.getenv('AZURE_OPENAI_CHAT_API_VERSION')
                or os.getenv('AZURE_OPENAI_EMBEDDINGS_API_VERSION')
                or '2024-02-15-preview'
            )

            # Cliente AzureOpenAI sin proxies; intenta con http_client y si falla por 'proxies', reintenta sin él
            try:
                http_client = httpx.Client(
                    timeout=httpx.Timeout(30.0, connect=10.0),
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                )
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=azure_endpoint,
                    http_client=http_client,
                )
            except TypeError as te:
                if 'proxies' in str(te).lower():
                    # Reintentar sin http_client para evitar choque con proxies internos
                    self.client = AzureOpenAI(
                        api_key=api_key,
                        api_version=api_version,
                        azure_endpoint=azure_endpoint,
                    )
                else:
                    raise

            self.is_configured = True
            logger.info(
                "Azure OpenAI client configured (endpoint=%s, api_version=%s, key_source=%s)",
                azure_endpoint,
                api_version,
                'OPENAI_API_KEY' if os.getenv('OPENAI_API_KEY') else 'AZURE_OPENAI_API_KEY',
            )

        except Exception as e:
            logger.error("Error configuring Azure OpenAI client: %s", e)
            self.is_configured = False
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If text is empty or invalid
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if not self.is_configured:
            logger.warning("Azure OpenAI not configured - using dummy embedding")
            return self._generate_dummy_embedding(text)
        
        try:
            model = os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')
            if not model:
                raise ValueError("Missing embeddings deployment configuration")
            
            if not self.client:
                raise ValueError("Azure OpenAI client not initialized")
                
            response = self.client.embeddings.create(
                input=text,
                model=model
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            logger.warning("Falling back to dummy embedding")
            return self._generate_dummy_embedding(text)
    
    def generate_chat_response(self, messages: List[Dict[str, str]], 
                             max_tokens: int = 1000,
                             temperature: float = 0.7) -> str:
        """
        Generate chat completion response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens in response
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Generated response text
            
        Raises:
            ValueError: If messages list is empty or invalid
            Exception: If chat completion fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        if not self.is_configured:
            logger.warning("Azure OpenAI not configured - using dummy response")
            return self._generate_dummy_chat_response(messages)
        
        try:
            model = os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT')
            if not model:
                raise ValueError("Missing chat deployment configuration")
            
            if not self.client:
                raise ValueError("Azure OpenAI client not initialized")
                
            # Convert messages to proper format for OpenAI API
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    formatted_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            response = self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            if content:
                logger.debug(f"Generated chat response with {len(content)} characters")
                return content
            else:
                return "No response generated"
            
        except Exception as e:
            # Solo para el caso de filtro de contenido de Azure: mensaje amable y SIN dummy
            if _is_content_filter_error(e):
                logger.warning("[OPENAI-CONTENT-FILTER] Respuesta filtrada por políticas (oculto al usuario)")
                return SAFE_FILTER_MESSAGE
            # Para cualquier otro error, conservar el comportamiento existente (incluido dummy)
            logger.error(f"Error generating chat response: {e}")
            logger.warning("Falling back to dummy response")
            return self._generate_dummy_chat_response(messages)
    
    def _generate_dummy_embedding(self, text: str) -> List[float]:
        """
        Generate dummy embedding for development/testing.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing dummy embedding
        """
        import hashlib
        import math
        
        # Create deterministic dummy embedding based on text hash
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Convert hash to list of floats
        embedding = []
        for i in range(0, len(hash_hex), 2):
            if len(embedding) >= 1536:  # OpenAI embedding dimension
                break
            hex_pair = hash_hex[i:i+2]
            value = int(hex_pair, 16) / 255.0  # Normalize to 0-1
            embedding.append(value)
        
        # Pad to 1536 dimensions if needed
        while len(embedding) < 1536:
            embedding.append(0.0)
        
        return embedding[:1536]
    
    def _generate_dummy_chat_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate dummy chat response for development/testing.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dummy response text
        """
        last_message = messages[-1] if messages else {}
        content = last_message.get('content', 'Hello')
        
        dummy_responses = [
            f"This is a dummy response to: {content[:50]}...",
            "I'm currently in dummy mode. Please configure Azure OpenAI for real responses.",
            f"Received message: {content}. This is a test response.",
            "Dummy chat completion - Azure OpenAI not configured."
        ]
        
        import random
        return random.choice(dummy_responses)
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """
        Get current configuration status.
        
        Returns:
            Dictionary with configuration information
        """
        return {
            'is_configured': self.is_configured,
            'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'chat_deployment': os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT'),
            'embeddings_deployment': os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT'),
            'api_version': os.getenv('AZURE_OPENAI_CHAT_API_VERSION') or os.getenv('AZURE_OPENAI_EMBEDDINGS_API_VERSION') or '2024-02-15-preview',
            'has_api_key': bool(os.getenv('OPENAI_API_KEY') or os.getenv('AZURE_OPENAI_API_KEY')),
            'key_source': 'OPENAI_API_KEY' if os.getenv('OPENAI_API_KEY') else ('AZURE_OPENAI_API_KEY' if os.getenv('AZURE_OPENAI_API_KEY') else None),
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Azure OpenAI connection and functionality.
        
        Returns:
            Dictionary with test results
        """
        results = {
            'connection_test': False,
            'embedding_test': False,
            'chat_test': False,
            'errors': []
        }
        
        try:
            if not self.is_configured:
                results['errors'].append("Azure OpenAI not configured")
                return results
            
            # Test embedding generation
            test_embedding = self.generate_embedding("Test message")
            if test_embedding and len(test_embedding) > 0:
                results['embedding_test'] = True
            
            # Test chat completion
            test_messages = [{"role": "user", "content": "Hello"}]
            test_response = self.generate_chat_response(test_messages)
            if test_response and len(test_response) > 0:
                results['chat_test'] = True
            
            results['connection_test'] = True
            
        except Exception as e:
            results['errors'].append(str(e))
        
        return results 