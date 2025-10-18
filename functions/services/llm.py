import os
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

# Import cache layer
try:
    from utils.cache_layer import get_ans, set_ans, is_cache_enabled
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logging.warning("Cache layer not available, falling back to direct LLM calls")

# Lazy loading of OpenAI client to avoid import errors
_client = None

def get_openai_client():
    """Get OpenAI client with lazy loading to avoid import errors."""
    global _client
    if _client is None:
        try:
            from openai import AzureOpenAI
            from utils.env_utils import get_env
            
            # Get environment variables
            azure_endpoint = get_env("AZURE_OPENAI_ENDPOINT")
            api_key = get_env("AZURE_OPENAI_API_KEY")
            api_version = get_env("AZURE_OPENAI_EMBEDDINGS_API_VERSION")
            
            _client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version
            )
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client: {str(e)}")
            return None
    return _client

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def generate_reply(message: str) -> str:
    """
    Generate a response using Azure OpenAI with RAG response caching
    
    Args:
        message: User message
        
    Returns:
        Generated response
    """
    # Check cache first if available
    if CACHE_AVAILABLE and is_cache_enabled():
        cached_response = get_ans(message)
        if cached_response:
            logging.info(f"Cache HIT for RAG response: {message[:50]}...")
            return cached_response.get('response', '')
        else:
            logging.info(f"Cache MISS for RAG response: {message[:50]}...")
    
    try:
        client = get_openai_client()
        if not client:
            return "Sorry, I'm having technical difficulties. Please try again later."
        
        system_prompt = """
        You are a VEA Connect virtual assistant. Respond in a friendly and helpful manner.
        Keep responses concise and in Spanish.
        """
        
        response = client.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Cache the response if cache is available
        if CACHE_AVAILABLE and is_cache_enabled():
            try:
                cache_data = {
                    'response': ai_response,
                    'model': 'gpt-35-turbo',
                    'max_tokens': 150,
                    'temperature': 0.7
                }
                set_ans(message, cache_data)
                logging.info(f"Cached RAG response for: {message[:50]}...")
            except Exception as e:
                logging.warning(f"Failed to cache RAG response: {e}")
        
        return ai_response
        
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        return "Sorry, I couldn't process your message right now. Please try again later."
