"""
Azure Function: WhatsApp Event Grid Trigger V2
Basado en la lógica de scripts/whatsapp_chat_cli.py
Usa SOLO RAG con el prompt estricto y temperature=0.0
"""
import os
import sys
import json
import logging
import azure.functions as func

# Configurar logging
logger = logging.getLogger("whatsapp_event_grid_trigger_v2")
logger.setLevel(logging.INFO)


def ensure_django():
    """Configurar Django environment para importar handlers"""
    # Agregar la raíz del proyecto al path
    # En Azure Functions, el código está en /home/site/wwwroot/
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Configurar settings module
    settings_module = (
        "config.settings.azure_production"
        if 'WEBSITE_HOSTNAME' in os.environ
        else 'config.settings.development'
    )
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    
    # Setup Django
    import django
    django.setup()


# Inicializar Django ANTES de importar handlers
ensure_django()

from django.conf import settings
from apps.whatsapp_bot.handlers import WhatsAppBotHandler
from utilities.azure_search_client import get_azure_search_client
from utilities.embedding_manager import EmbeddingManager


# Habilitar RAG (como en el CLI, línea 45)
setattr(settings, 'BOT_USE_RAG', True)


# System prompt estricto (como scripts/prompts/whatsapp_cli_prompt.txt)
SYSTEM_PROMPT = """Eres un asistente de WhatsApp para la organización de VEA. Responde SOLO con base en el contexto del índice que se te proporciona. Sé claro, breve y respetuoso y usa lenguaje religioso amable. Si el contexto no contiene la respuesta, dilo explícitamente y sugiere contactar al equipo de Iglesia VEA."""


# Monkeypatch de OpenAIService.generate_chat_response (como CLI, líneas 79-103)
try:
    from apps.embeddings import openai_service as oai_mod
    if hasattr(oai_mod, 'OpenAIService'):
        _orig_generate = oai_mod.OpenAIService.generate_chat_response
        
        def _wrapped_generate(self, messages, max_tokens=1000, temperature=0.0):
            """
            Override para inyectar el SYSTEM_PROMPT estricto y usar temperature=0.0
            """
            if messages and isinstance(messages, list):
                # Reemplazar/inyectar el mensaje de sistema
                new_messages = []
                has_system = False
                for m in messages:
                    if m.get('role') == 'system' and not has_system:
                        new_messages.append({'role': 'system', 'content': SYSTEM_PROMPT})
                        has_system = True
                    else:
                        new_messages.append(m)
                if not has_system:
                    new_messages.insert(0, {'role': 'system', 'content': SYSTEM_PROMPT})
                messages = new_messages
            
            # SIEMPRE usar temperature=0.0 (más estricto que CLI)
            return _orig_generate(self, messages, max_tokens=max_tokens, temperature=0.0)
        
        # Aplicar monkeypatch
        oai_mod.OpenAIService.generate_chat_response = _wrapped_generate
        logger.info("[V2] Monkeypatch aplicado: SYSTEM_PROMPT estricto + temperature=0.0")
except Exception as e:
    logger.warning(f"[V2] No se pudo aplicar monkeypatch a OpenAIService: {e}")


# Inicializar servicios globales
_handler = None


def get_handler():
    """Lazy initialization del handler"""
    global _handler
    if _handler is None:
        try:
            # Importar ACS service
            from services.whatsapp_sender import WhatsAppSender
            
            # Inicializar Azure Search Client y Embedding Manager
            search_client = get_azure_search_client()
            embedding_manager = EmbeddingManager(search_client=search_client)
            
            # Inicializar ACS service
            connection_string = os.environ.get('ACS_CONNECTION_STRING')
            if not connection_string:
                raise ValueError("ACS_CONNECTION_STRING no está configurado")
            
            acs_service = WhatsAppSender(connection_string=connection_string)
            
            # Crear handler
            _handler = WhatsAppBotHandler(
                acs_service=acs_service,
                embedding_manager=embedding_manager
            )
            
            logger.info("[V2] Handler inicializado correctamente")
        except Exception as e:
            logger.error(f"[V2] Error inicializando handler: {e}")
            raise
    
    return _handler


def main(event: func.EventGridEvent):
    """
    Main function handler para Event Grid
    Lógica basada en whatsapp_chat_cli.py (modo RAG directo)
    """
    try:
        logger.info(f"[V2] Event Grid trigger ejecutado. Event ID: {event.id}")
        
        # Parsear el evento
        event_data = event.get_json()
        logger.info(f"[V2] Event data: {json.dumps(event_data, default=str)[:500]}")
        
        # Extraer información del mensaje
        event_type = event.event_type
        
        # Filtrar solo eventos de mensajes recibidos
        if "Microsoft.Communication.AdvancedMessageReceived" not in event_type:
            logger.info(f"[V2] Evento ignorado (no es mensaje recibido): {event_type}")
            return
        
        # Extraer datos del mensaje
        from_number = event_data.get('from')
        message_id = event_data.get('messageId') or event_data.get('id')
        
        # Obtener el contenido del mensaje
        content = event_data.get('content')
        if not content:
            logger.warning("[V2] No se encontró contenido en el mensaje")
            return
        
        text = content.get('text') or content.get('body')
        if not text:
            logger.warning("[V2] No se encontró texto en el contenido del mensaje")
            return
        
        logger.info(f"[V2] Procesando mensaje de {from_number} (ID: {message_id}): {text}")
        
        # Obtener handler
        handler = get_handler()
        
        # MODO RAG DIRECTO (como CLI línea 167)
        # Usar _rag_answer directamente sin pasar por intents
        try:
            logger.info(f"[V2] Llamando a handler._rag_answer('{text}')")
            ai_response = handler._rag_answer(text)
            logger.info(f"[V2] Respuesta RAG generada: {ai_response[:100]}...")
        except Exception as e:
            logger.error(f"[V2] Error en _rag_answer: {e}", exc_info=True)
            ai_response = "Lo siento, tuve un problema procesando tu consulta. Por favor contacta al equipo de Iglesia VEA."
        
        # Enviar respuesta por WhatsApp
        try:
            success = handler.acs_service.send_text_message(from_number, ai_response)
            if success:
                logger.info(f"[V2] Mensaje enviado correctamente a {from_number}")
            else:
                logger.error(f"[V2] Error enviando mensaje a {from_number}")
        except Exception as e:
            logger.error(f"[V2] Error enviando mensaje WhatsApp: {e}", exc_info=True)
        
        logger.info(f"[V2] Procesamiento completado para mensaje {message_id}")
        
    except Exception as e:
        logger.error(f"[V2] Error procesando evento: {e}", exc_info=True)
        raise

