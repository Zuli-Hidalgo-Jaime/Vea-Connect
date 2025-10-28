import logging
import json
import os
import time
import azure.functions as func
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import requests
import hmac
import hashlib
import base64

# Try to import Azure Communication Messages SDK
try:
    from azure.communication.messages import NotificationMessagesClient
    from azure.communication.messages.models import TextNotificationContent, ImageNotificationContent
    ACS_SDK_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Azure Communication Advanced Messages SDK imported successfully")
except ImportError as e:
    ACS_SDK_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Azure Communication Advanced Messages SDK not available: {e}. Will use HTTP fallback.")
except Exception as e:
    ACS_SDK_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Error importing Azure Communication Advanced Messages SDK: {e}. Will use HTTP fallback.")

# Force SDK usage if available
if ACS_SDK_AVAILABLE:
    logger.info("SDK is available - will use SDK for messaging")
else:
    logger.error("SDK is NOT available - this is the problem!")
    # Try to debug why SDK is not available
    try:
        import sys
        logger.info(f"Python path: {sys.path}")
    except Exception as debug_e:
        logger.error(f"Error debugging SDK availability: {debug_e}")

# Configure logging
logger = logging.getLogger(__name__)

# Environment variables for configuration
E2E_DEBUG = os.getenv('E2E_DEBUG', 'false').lower() == 'true'
WHATSAPP_DEBUG = os.getenv('WHATSAPP_DEBUG', 'false').lower() == 'true'
RAG_ENABLED = os.getenv('RAG_ENABLED', 'true').lower() == 'true'  # Changed to true by default
BOT_SYSTEM_PROMPT = os.getenv('BOT_SYSTEM_PROMPT', """
Eres un asistente virtual de VEA Connect, una plataforma de gestión para organizaciones sin fines de lucro.

INSTRUCCIONES CRÍTICAS:
- SOLO responde con información que esté disponible en los documentos, eventos o datos de VEA Connect
- NUNCA inventes información que no esté explícitamente disponible
- Si no tienes información específica, di exactamente: "No tengo esa información específica disponible"
- Mantén las respuestas concisas y basadas únicamente en hechos
- Responde en español de manera amigable pero profesional

INFORMACIÓN DISPONIBLE:
- Documentos de la organización
- Eventos programados
- Información de donaciones
- Servicios disponibles

Si no puedes responder con información verificada, sugiere contactar al equipo de VEA Connect.
""")

# Diagnostic logging for ACS environment variables
if E2E_DEBUG:
    logger.info("=== ACS Environment Variables Diagnostic ===")
    acs_vars = {k: v for k, v in os.environ.items() if 'ACS' in k.upper()}
    for var_name, var_value in acs_vars.items():
        if 'KEY' in var_name.upper() or 'SECRET' in var_name.upper():
            logger.info(f"{var_name}: {'SET' if var_value else 'NOT SET'} - Value: {var_value[:10] if var_value else 'None'}...")
        else:
            logger.info(f"{var_name}: {'SET' if var_value else 'NOT SET'} - Value: {var_value if var_value else 'None'}")
    logger.info("=== End ACS Environment Variables Diagnostic ===")

def _normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone: Phone number in various formats
        
    Returns:
        Normalized phone number in E.164 format
    """
    # Remove common prefixes and clean up
    phone = str(phone).strip()
    
    # Remove whatsapp: prefix if present
    if phone.startswith('whatsapp:'):
        phone = phone[9:]
    
    # Remove common separators
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Add + if not present and looks like a valid number
    if not phone.startswith('+') and len(phone) >= 10:
        # Assume it's a US number if no country code
        if len(phone) == 10:
            phone = '+1' + phone
        elif len(phone) == 11 and phone.startswith('1'):
            phone = '+' + phone
    
    return phone

def _extract_message_data_tolerant(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract message data from ACS Advanced Messaging payload with tolerant schema parsing.
    Supports multiple schemas for robust parsing.
    
    Args:
        data: The message data dictionary
        
    Returns:
        Dictionary with normalized message info or None
    """
    try:
        # Log the data structure for debugging (truncated to 2000 chars)
        data_str = json.dumps(data, indent=2)
        if len(data_str) > 2000:
            data_str = data_str[:2000] + "..."
        logger.info(f"Attempting to extract message data from: {data_str}")
        
        # Schema 1: Evento plano con keys directas
        if all(key in data for key in ['content', 'channelType', 'messageType', 'from', 'to', 'messageId']):
            logger.info("Found flat event schema")
            
            if data.get('messageType') == 'text' and 'content' in data:
                content = data['content']
                if isinstance(content, dict) and 'text' in content:
                    text_content = content['text']
                    if isinstance(text_content, dict) and 'body' in text_content:
                        text = text_content['body']
                    elif isinstance(text_content, str):
                        text = text_content
                    else:
                        logger.warning(f"Unexpected text content structure: {text_content}")
                        return None
                elif isinstance(content, str):
                    text = content
                else:
                    logger.warning(f"Unexpected content structure: {content}")
                    return None
                
                # Normalize phone number (remove + prefix for internal use)
                from_number = data['from']
                if from_number.startswith('+'):
                    from_number = from_number[1:]
                
                return {
                    "text": text,
                    "from": from_number,
                    "to": data['to'],
                    "channel": "whatsapp",
                    "message_id": data['messageId'],
                    "ts": data.get('receivedTimestamp', datetime.now(timezone.utc).isoformat())
                }
        
        # Schema 2: Evento con data anidada
        if 'data' in data and isinstance(data['data'], dict):
            logger.info("Found nested data schema")
            nested_data = data['data']
            
            # Try message.text.body
            if 'message' in nested_data and isinstance(nested_data['message'], dict):
                message = nested_data['message']
                if 'text' in message and isinstance(message['text'], dict) and 'body' in message['text']:
                    text = message['text']['body']
                    from_number = nested_data.get('from', '')
                    if from_number.startswith('+'):
                        from_number = from_number[1:]
                    
                    return {
                        "text": text,
                        "from": from_number,
                        "to": nested_data.get('to', ''),
                        "channel": "whatsapp",
                        "message_id": nested_data.get('messageId', ''),
                        "ts": nested_data.get('receivedTimestamp', datetime.now(timezone.utc).isoformat())
                    }
            
            # Try message.content
            if 'message' in nested_data and isinstance(nested_data['message'], dict):
                message = nested_data['message']
                if 'content' in message and isinstance(message['content'], dict) and 'text' in message['content']:
                    text = message['content']['text']
                    from_number = nested_data.get('from', '')
                    if from_number.startswith('+'):
                        from_number = from_number[1:]
                    
                    return {
                        "text": text,
                        "from": from_number,
                        "to": nested_data.get('to', ''),
                        "channel": "whatsapp",
                        "message_id": nested_data.get('messageId', ''),
                        "ts": nested_data.get('receivedTimestamp', datetime.now(timezone.utc).isoformat())
                    }
            
            # Try message.payload.text
            if 'message' in nested_data and isinstance(nested_data['message'], dict):
                message = nested_data['message']
                if 'payload' in message and isinstance(message['payload'], dict) and 'text' in message['payload']:
                    text = message['payload']['text']
                    from_number = nested_data.get('from', '')
                    if from_number.startswith('+'):
                        from_number = from_number[1:]
                    
                    return {
                        "text": text,
                        "from": from_number,
                        "to": nested_data.get('to', ''),
                        "channel": "whatsapp",
                        "message_id": nested_data.get('messageId', ''),
                        "ts": nested_data.get('receivedTimestamp', datetime.now(timezone.utc).isoformat())
                    }
        
        # Schema 3: Legacy schema support
        if 'messageBody' in data and 'from' in data:
            logger.info("Found legacy schema")
            text = data['messageBody']
            from_number = data['from']
            if from_number.startswith('+'):
                from_number = from_number[1:]
            
            return {
                "text": text,
                "from": from_number,
                "to": data.get('to', ''),
                "channel": "whatsapp",
                "message_id": data.get('messageId', ''),
                "ts": data.get('receivedTimestamp', datetime.now(timezone.utc).isoformat())
            }
        
        # If no schema matches, log warning with found keys
        found_keys = list(data.keys())
        logger.warning(f"No matching schema found. Available keys: {found_keys}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting message data: {e}")
        return None

def _get_conversation_history(phone_number: str) -> List[Dict[str, str]]:
    """
    Get conversation history from Redis cache.
    
    Args:
        phone_number: User's phone number
        
    Returns:
        List of conversation messages
    """
    try:
        # For now, return empty history
        # TODO: Implement Redis integration
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
        True if successful, False otherwise
    """
    try:
        # For now, just log the conversation
        logger.info(f"Conversation update for {phone_number}: User: {user_message[:50]}... Bot: {bot_response[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Error updating conversation history: {e}")
        return False

def _get_rag_context(query: str) -> Optional[str]:
    """
    Get RAG context for the query using Azure Search directly.
    
    Args:
        query: User's query
        
    Returns:
        RAG context or None
    """
    try:
        if not RAG_ENABLED:
            logger.info("RAG is disabled, skipping vector search")
            return None
        
        logger.info(f"Performing Azure Search for query: {query}")
        
        # Get Azure Search configuration
        search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        search_key = os.getenv('AZURE_SEARCH_KEY')
        search_index = os.getenv('AZURE_SEARCH_INDEX_NAME')
        
        if not all([search_endpoint, search_key, search_index]):
            logger.error("Azure Search configuration missing")
            return None
        
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
            
            # Initialize Azure Search client
            search_client = SearchClient(
                endpoint=search_endpoint,  # type: ignore
                index_name=search_index,  # type: ignore
                credential=AzureKeyCredential(search_key)  # type: ignore
            )
            
            # Perform search
            search_results = search_client.search(
                search_text=query,
                top=3,
                include_total_count=True
            )
            
            # Extract context from search results
            context_parts = []
            for result in search_results:
                # Extract relevant information
                content = result.get('content', '')
                text = result.get('text', '')
                title = result.get('title', '')
                score = result.get('@search.score', 0)
                
                # Use the most relevant content
                relevant_text = content or text or title
                if relevant_text and score > 0.5:  # Only include high-confidence results
                    context_parts.append(f"- {relevant_text[:200]}...")
            
            if context_parts:
                context = "\n".join(context_parts)
                logger.info(f"Generated RAG context with {len(context)} characters from Azure Search")
                return str(context)
            else:
                logger.info("No relevant context found in Azure Search results")
                return None
                
        except ImportError:
            logger.error("Azure Search SDK not available")
            return None
        except Exception as e:
            logger.error(f"Error searching Azure Search: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting RAG context: {e}")
        return None

def _generate_hmac_signature(access_key: str, url: str, method: str = 'POST', content: str = '') -> str:
    """
    Generate HMAC signature for Azure Communication Services.
    
    Args:
        access_key: ACS access key
        url: Full URL including query parameters
        method: HTTP method (default: POST)
        content: Request body content
        
    Returns:
        HMAC signature string
    """
    try:
        # Parse URL to get path and query
        from urllib.parse import urlparse, parse_qs
        
        parsed_url = urlparse(url)
        path_and_query = parsed_url.path
        if parsed_url.query:
            path_and_query += '?' + parsed_url.query
        
        # Create string to sign
        string_to_sign = f"{method}\n{path_and_query}\n{content}"
        
        # Decode access key from base64
        key_bytes = base64.b64decode(access_key)
        
        # Create HMAC signature
        signature = hmac.new(key_bytes, string_to_sign.encode('utf-8'), hashlib.sha256)
        signature_bytes = signature.digest()
        
        # Encode signature to base64
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        return signature_b64
        
    except Exception as e:
        logger.error(f"Error generating HMAC signature: {e}")
        return ""

def _generate_ai_response(user_message: str, conversation_history: List[Dict[str, str]], rag_context: Optional[str] = None) -> str:
    """
    Generate AI response using OpenAI.
    
    Args:
        user_message: User's message
        conversation_history: Conversation history
        rag_context: RAG context
        
    Returns:
        Generated response
    """
    try:
        logger.info(f"Generating AI response for: {user_message}")
        
        # Check if OpenAI is configured
        openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        openai_key = os.getenv('AZURE_OPENAI_API_KEY')
        openai_deployment = os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT')
        
        if not all([openai_endpoint, openai_key, openai_deployment]):
            logger.warning("OpenAI not configured, using fallback response")
            return f"Hola! Recibí tu mensaje: '{user_message}'. Soy el asistente virtual de VEA Connect. ¿En qué puedo ayudarte?"
        
        # Import OpenAI client
        try:
            from openai import AzureOpenAI
            import httpx
        except ImportError:
            logger.error("OpenAI library not available")
            return "Lo siento, el servicio de IA no está disponible en este momento."
        
        # Initialize OpenAI client with custom http_client to avoid proxies issue
        http_client = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        client = AzureOpenAI(
            azure_endpoint=openai_endpoint,  # type: ignore
            api_key=openai_key,  # type: ignore
            api_version=os.getenv('AZURE_OPENAI_CHAT_API_VERSION', '2024-02-15-preview'),
            http_client=http_client
        )
        
        # Build system prompt
        system_prompt = BOT_SYSTEM_PROMPT
        
        # Add RAG context if available
        if rag_context:
            system_prompt += f"\n\nInformación relevante encontrada:\n{rag_context}\n\nUsa esta información para responder de manera más precisa y útil."
            logger.info(f"Added RAG context to system prompt: {len(rag_context)} characters")
        
        # Build messages list
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 4 messages to keep context manageable)
        for msg in conversation_history[-4:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if content:
                messages.append({"role": role, "content": content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        logger.info(f"Sending request to OpenAI with {len(messages)} messages")
        
        # Generate response
        response = client.chat.completions.create(
            model=openai_deployment,  # type: ignore
            messages=messages,  # type: ignore
            max_tokens=500,
            temperature=0.0
        )
        
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"Generated AI response: {ai_response[:100]}...")
            return ai_response
        else:
            logger.error("No response content from OpenAI")
            return "Lo siento, no pude generar una respuesta. Por favor intenta de nuevo."
            
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return "Lo siento, estoy teniendo problemas para procesar tu mensaje. Por favor, intenta de nuevo más tarde."

def _send_whatsapp_text(to_number: str, text: str) -> bool:
    """
    Send WhatsApp text message using ACS.
    
    Args:
        to_number: Recipient phone number (without +)
        text: Message text
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get configuration from environment variables
        conn_string = os.getenv('ACS_CONNECTION_STRING')
        from_id = os.getenv('ACS_PHONE_NUMBER')  # Use ACS_PHONE_NUMBER instead of ACS_WHATSAPP_FROM
        
        # Check for missing environment variables
        missing_vars = []
        if not conn_string:
            missing_vars.append('ACS_CONNECTION_STRING')
        if not from_id:
            missing_vars.append('ACS_PHONE_NUMBER')
        
        if missing_vars:
            logger.error(f"Missing ACS configuration variables: {missing_vars}")
            return False
        
        # Ensure to_number has + prefix for ACS
        if to_number and not to_number.startswith('+'):
            to_number = '+' + to_number
        
        # Ensure from_id has + prefix for ACS
        if from_id and not from_id.startswith('+'):
            from_id = '+' + from_id
        
        logger.info(f"Using ACS SDK: {ACS_SDK_AVAILABLE}")
        
        # Force SDK usage if available
        if ACS_SDK_AVAILABLE:
            # Use Azure Communication Advanced Messages SDK
            try:
                # Get channel registration ID
                channel_registration_id = os.getenv('WHATSAPP_CHANNEL_ID_GUID')
                if not channel_registration_id:
                    logger.error("Missing WHATSAPP_CHANNEL_ID_GUID environment variable")
                    return False
                
                # Create the messaging client
                if not conn_string:
                    logger.error("Connection string is None")
                    return False
                messaging_client = NotificationMessagesClient.from_connection_string(conn_string)
                
                # Create text notification content with channel registration ID
                text_options = TextNotificationContent(
                    channel_registration_id=channel_registration_id,
                    to=[to_number],
                    content=text
                )
                
                # Send the message
                message_responses = messaging_client.send(text_options)
                response = message_responses.receipts[0]
                
                if response is not None:
                    logger.info(f"WhatsApp message sent successfully to {to_number} using Advanced Messages SDK")
                    logger.info(f"Message ID: {response.message_id}")
                    return True
                else:
                    logger.error("Message failed to send via SDK")
                    return False
                
            except Exception as sdk_error:
                logger.error(f"Advanced Messages SDK error: {sdk_error}")
                logger.info("Falling back to HTTP method")
                # Fall through to HTTP method
        else:
            logger.info("SDK not available, using HTTP method")
        
        # HTTP Fallback method with proper HMAC signature
        logger.info("Using HTTP method with HMAC signature")
        
        # Extract endpoint and access key from connection string
        # Format: "endpoint=https://...;accesskey=..."
        if conn_string:
            conn_parts = conn_string.split(';')
            endpoint = None
            access_key = None
            
            for part in conn_parts:
                if part.startswith('endpoint='):
                    endpoint = part.split('=', 1)[1]
                elif part.startswith('accesskey='):
                    access_key = part.split('=', 1)[1]
        else:
            endpoint = None
            access_key = None
        
        if not endpoint or not access_key:
            logger.error("Could not parse ACS_CONNECTION_STRING")
            return False
        
        # Clean up endpoint URL (remove trailing slash if present)
        if endpoint and endpoint.endswith('/'):
            endpoint = endpoint.rstrip('/')
        
        # Prepare the message payload
        payload = {
            "content": text,
            "from": from_id,
            "to": [to_number]
        }
        
        # Convert payload to JSON string
        payload_json = json.dumps(payload)
        
        # Build URL with API version
        url = f"{endpoint}/messages?api-version=2024-02-15-preview"
        
        logger.info(f"Using endpoint: {endpoint}")
        logger.info(f"Using API version: 2024-02-15-preview")
        
        # Generate HMAC signature
        signature = _generate_hmac_signature(access_key, url, 'POST', payload_json)
        
        if not signature:
            logger.error("Failed to generate HMAC signature")
            return False
        
        # Create headers with HMAC signature
        headers = {
            'Authorization': f'HMAC-SHA256 {signature}',
            'Content-Type': 'application/json',
            'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        logger.info(f"Sending WhatsApp message via HTTP to URL: {url}")
        logger.info(f"Payload: {payload_json}")
        logger.info(f"Headers: {headers}")
        
        # Add retry logic for connection issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} of {max_retries}")
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                break
            except requests.exceptions.ConnectionError as conn_error:
                logger.error(f"Connection error on attempt {attempt + 1}: {conn_error}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)  # Wait before retry
            except requests.exceptions.ReadTimeout as timeout_error:
                logger.error(f"Timeout error on attempt {attempt + 1}: {timeout_error}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)  # Wait before retry
        
        if response.status_code == 202:
            logger.info(f"WhatsApp message sent successfully to {to_number} via HTTP")
            return True
        elif response.status_code == 200:
            logger.info(f"WhatsApp message sent successfully to {to_number} via HTTP (200 OK)")
            return True
        else:
            logger.error(f"Failed to send WhatsApp message via HTTP. Status: {response.status_code}")
            logger.error(f"Response headers: {dict(response.headers)}")
            logger.error(f"Response body: {response.text[:1000]}...")
            
            # Log specific error details
            try:
                error_data = response.json()
                logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Could not parse error response as JSON")
            
            return False
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False

def _send_whatsapp_image(to_number: str, image_url: str, caption: str = "") -> bool:
    """
    Send WhatsApp image message using ACS Advanced Messages SDK.
    
    Args:
        to_number: Recipient phone number (without +)
        image_url: URL of the image to send
        caption: Optional caption for the image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get configuration from environment variables
        conn_string = os.getenv('ACS_CONNECTION_STRING')
        channel_registration_id = os.getenv('WHATSAPP_CHANNEL_ID_GUID')
        
        # Check for missing environment variables
        missing_vars = []
        if not conn_string:
            missing_vars.append('ACS_CONNECTION_STRING')
        if not channel_registration_id:
            missing_vars.append('WHATSAPP_CHANNEL_ID_GUID')
        
        if missing_vars:
            logger.error(f"Missing ACS configuration variables: {missing_vars}")
            return False
        
        # Ensure to_number has + prefix for ACS
        if to_number and not to_number.startswith('+'):
            to_number = '+' + to_number
        
        logger.info(f"Using ACS Advanced Messages SDK for image: {ACS_SDK_AVAILABLE}")
        
        if ACS_SDK_AVAILABLE:
            # Use Azure Communication Advanced Messages SDK
            try:
                # Create the messaging client
                if not conn_string:
                    logger.error("Connection string is None")
                    return False
                messaging_client = NotificationMessagesClient.from_connection_string(conn_string)
                
                # Create image notification content
                if not channel_registration_id:
                    logger.error("Channel registration ID is None")
                    return False
                image_options = ImageNotificationContent(
                    channel_registration_id=channel_registration_id,
                    to=[to_number],
                    media_uri=image_url
                )
                
                # Send the message
                message_responses = messaging_client.send(image_options)
                response = message_responses.receipts[0]
                
                if response is not None:
                    logger.info(f"WhatsApp image message sent successfully to {to_number} using Advanced Messages SDK")
                    logger.info(f"Message ID: {response.message_id}")
                    return True
                else:
                    logger.error("Image message failed to send via SDK")
                    return False
                
            except Exception as sdk_error:
                logger.error(f"Advanced Messages SDK error for image: {sdk_error}")
                return False
        else:
            logger.error("Advanced Messages SDK not available for image sending")
            return False
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp image message: {e}")
        return False

def main(event: func.EventGridEvent) -> None:
    """
    WhatsApp Event Grid trigger handler.
    Processes incoming WhatsApp messages via ACS Advanced Messaging.
    
    Args:
        event: Event Grid event containing WhatsApp message data
    """
    start_time = time.time()
    
    # Log event details
    logger.info(f"Event received - Type: {event.event_type}, Subject: {event.subject}, ID: {event.id}")
    
    # Log payload size for debugging
    payload_str = json.dumps(event.get_json())
    payload_size = len(payload_str)
    logger.info(f"Payload size: {payload_size} bytes")
    
    # Log truncated payload if debug enabled
    if E2E_DEBUG and payload_size > 0:
        truncated_payload = payload_str[:2000] + "..." if len(payload_str) > 2000 else payload_str
        logger.info(f"Payload (truncated): {truncated_payload}")
    
    try:
        # Handle SubscriptionValidation events
        if event.event_type == "Microsoft.EventGrid.SubscriptionValidationEvent":
            logger.info("Processing subscription validation event")
            
            # Extract validation code
            data = event.get_json()
            validation_code = data.get('validationCode')
            
            if validation_code:
                # Return validation response
                response_data = {
                    "validationResponse": validation_code
                }
                
                # Return the response (Event Grid will handle this)
                logger.info("Subscription validation successful")
                return None
            else:
                logger.error("No validation code found in subscription validation event")
                return None
        
        # Handle Advanced Message Received events
        if event.event_type == "Microsoft.Communication.AdvancedMessageReceived":
            logger.info("Processing Advanced Message Received event")
            
            # Parse event data
            data = event.get_json()
            
            # Extract message data with tolerant parser
            normalized = _extract_message_data_tolerant(data)
            if not normalized:
                logger.warning("Could not extract message data from event")
                return None
            
            text = normalized['text']
            from_number = normalized['from']
            message_id = normalized['message_id']
            
            logger.info(f"Processing message from {from_number} (ID: {message_id}): {text}")
            
            # Get conversation history
            conversation_history = _get_conversation_history(from_number)
            
            # Get RAG context if enabled
            rag_context = _get_rag_context(text)
            
            # Generate AI response
            ai_response = _generate_ai_response(text, conversation_history, rag_context)
            
            # Update conversation history
            _update_conversation_history(from_number, text, ai_response)
            
            # Send WhatsApp response
            success = _send_whatsapp_text(from_number, ai_response)
            
            # Log the response and status
            logger.info(f"Response sent: {ai_response[:100]}...")
            logger.info(f"Send status: {success}")
            
            if success:
                logger.info(f"Message processing completed successfully for {from_number}")
            else:
                logger.error(f"Failed to send response to {from_number}")
            
            # Log processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Total processing time: {processing_time_ms}ms")
            
        else:
            logger.info(f"Ignoring event type: {event.event_type}")
        
    except Exception as e:
        logger.exception(f"Error processing WhatsApp event: {e}")
        raise  # Re-raise for Event Grid retry
