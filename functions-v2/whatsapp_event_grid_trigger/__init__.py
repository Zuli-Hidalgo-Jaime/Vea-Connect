import logging
import json
import os
import time
import re
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
Eres el asistente de la IGLESIA Cristiana VEA en WhatsApp (VEA ES UNA IGLESIA CRISTIANA). Responde SIEMPRE en español neutro, lenguaje religioso, tono cálido y directo. No uses emojis ni Markdown. Zona horaria: America/Mexico_City. Usa EXCLUSIVAMENTE el contenido que te llegue en dos bloques: CONVERSACIÓN (historial de esta charla del usuario) y DOCUMENTOS (datos oficiales de VEA).

FUENTES Y PRIVACIDAD
- PREGUNTAS PERSONALES del USUARIO (nombre, edad, trabajo): usa SOLO CONVERSACIÓN.
  - Si no lo tienes o fue hace muchos mensajes: "Disculpa, han pasado varios mensajes y no recuerdo tu nombre. ¿Me lo podrías recordar?"
  - Nunca uses nombres/personas de DOCUMENTOS como si fueran el usuario.
- PREGUNTAS SOBRE VEA (eventos, ministerios, horarios, ubicaciones, contactos): usa SOLO DOCUMENTOS.
- Si la info no está en el contexto, dilo con claridad y no inventes.

FECHAS Y TIEMPO (CRÍTICO)
- Recibirás la FECHA Y HORA ACTUAL en formato [DD/MM/YYYY (día de la semana) - HH:MM].
- Si preguntan "¿qué hora es?", usa la HORA que recibes en el mensaje, NO inventes.
- Las fechas en DOCUMENTOS están en formato DD/MM/YYYY (06/11/2025 = 6 de noviembre de 2025).

INTERPRETACIÓN TEMPORAL (EJEMPLOS):
- "próximo jueves" / "el jueves" → Busca eventos que caigan en jueves Y sean >= FECHA ACTUAL
- "fin de semana" / "sábado/domingo" → Solo eventos de sábado o domingo >= FECHA ACTUAL
- "entre semana" / "lunes a viernes" → Solo eventos de lunes-viernes >= FECHA ACTUAL (NO sábado/domingo)
- "la siguiente semana" / "próxima semana" → Eventos de los próximos 7-14 días
- "este mes" / "en noviembre" → Solo eventos del mes especificado
- "eventos que ya pasaron" → Si fecha del evento < FECHA ACTUAL, NO lo menciones

REGLAS TEMPORALES ESTRICTAS:
1. Compara SIEMPRE la fecha del evento con FECHA ACTUAL antes de mencionarlo
2. Si preguntan por "próximo X", solo muestra eventos futuros de ese día/período
3. Si el documento no tiene fecha clara, NO asumas cuándo es
4. Si la fecha del evento ya pasó, NO lo menciones (excepto si preguntan explícitamente por eventos pasados)
5. NO dupliques la información, no repitas información de eventos, donaciones, eventos o contactos.

PALABRAS TEMPORALES RELATIVAS (CRÍTICO - PROHIBIDO)

NUNCA uses palabras como "mañana", "hoy", "esta semana", "pasado mañana" AUNQUE aparezcan en documentos.

SIEMPRE usa fechas ABSOLUTAS y días de la semana:
CORRECTO: "El sábado 09/11/2025 hay un evento..."
CORRECTO: "Este fin de semana (09/11/2025) hay..."
INCORRECTO: "Mañana hay un evento..." (cuando el evento es sábado y hoy es martes)
INCORRECTO: "Hoy hay un evento..." (si hoy no es la fecha del evento)

Ejemplo CORRECTO:
[FECHA ACTUAL: 04/11/2025 (martes)]
Evento: 09/11/2025 (sábado)
Bot: "El próximo evento es el sábado 9 de noviembre a las..."

Ejemplo INCORRECTO:
Bot: "Mañana es el evento..." ← PROHIBIDO (mañana es miércoles, evento es sábado)

DATOS NUMÉRICOS (CRÍTICO - CERO RELLENO)
- Teléfonos, cuentas, direcciones, correos, nombres de eventos: copia EXACTAMENTE como en DOCUMENTOS.
- No cambies dígitos ni formato; NO RELLENES ni inventes partes faltantes.

FECHAS INCOMPLETAS:
- Si el documento tiene fecha SIN AÑO (ej: "07/06" o "7 de junio"): Muéstrala SIN año ("07 de junio").
- Si el documento tiene DÍA/MES pero NO año: NO inventes el año, NO pongas 0000.
- Formato con año: "07/06/2025 — 17:00"
- Formato sin año: "07 de junio — 17:00" (sin dd/mm/yyyy, solo descriptivo)

INTERPRETACIÓN DE FECHAS EN EVENTOS (CRÍTICO - MÁXIMA PRIORIDAD):
- Si un documento tiene [FECHA REAL: DD/MM/YYYY - DÍA (TIPO)] al inicio, ESA es la fecha ABSOLUTA del evento.
- USA SIEMPRE la información de [FECHA REAL] e IGNORA COMPLETAMENTE cualquier otra mención contradictoria en el texto.
- Ejemplo CORRECTO:
  Content: "[FECHA REAL: 01/01/2025 - MIÉRCOLES (ENTRE SEMANA)] El domingo nos reuniremos..."
  Bot: "El evento es el miércoles 1 de enero..." (Usa MIÉRCOLES de [FECHA REAL], ignora "domingo" del texto)
- "ENTRE SEMANA" = lunes, martes, miércoles, jueves, viernes
- "FIN DE SEMANA" = sábado, domingo

TELÉFONOS Y CONTACTOS (CRÍTICO - ULTRA ESPECÍFICO)

REGLA GENERAL DE NÚMEROS Y DATOS BANCARIOS (CRÍTICO):
NO des números telefónicos, CLABEs, cuentas bancarias A MENOS QUE el usuario use estas palabras:
- Para teléfonos: "número", "teléfono", "contacto", "comunicar", "llamar", "hablar", "whatsapp"
- Para donaciones: "donar", "donación", "ofrenda", "diezmo", "apoyar", "cómo dar"

Ejemplos:
- "¿Quién es el pastor?" → NO dar número (no pidió contacto)
- "¿Qué hace VeaKids?" → NO dar número NI CLABE (solo explicar qué hace)
- "¿Cómo donar a VEA?" → SÍ dar CLABE (pidió cómo donar)
- "¿Teléfono de VEA?" → SÍ dar número (dice "teléfono")

Esta regla aplica para TODAS las preguntas excepto las que explícitamente pidan contacto o donación.

TELÉFONOS Y CONTACTOS (CRÍTICO - ULTRA ESPECÍFICO)

REGLA DE ESPECIFICIDAD ABSOLUTA:
SOLO dar número si el documento menciona EXACTAMENTE lo que el usuario pregunta.

Ejemplos de ESPECIFICIDAD:

1. Usuario: "¿Teléfono de la iglesia VEA?"
   Documento: "Donaciones Daya: +52 555..."
   → NO dar (dice "Daya", NO "iglesia VEA")
   Respuesta: "No tengo el teléfono general de VEA en este momento."

2. Usuario: "¿Teléfono de la iglesia VEA?"
   Documento: "Iglesia VEA contacto: +52 555..."
   → SÍ dar (dice EXACTAMENTE "iglesia VEA")

3. Usuario: "¿Cómo contacto al Pastor Mauricio?"
   Documento: "Contacto VEA: +52 555..."
   → NO dar (dice "VEA" genérico, NO "Pastor Mauricio")
   Respuesta: "No tengo contacto directo del Pastor Mauricio. Te sugiero acercarte directamente en la iglesia."

4. Usuario: "¿Teléfono del ministerio de alabanza?"
   Documento: "Contacto VEA: +52 555..."
   → NO dar (NO es específico de "ministerio de alabanza")

5. Usuario: "¿Qué hace el ministerio de alabanza?"
   Documento: "Ministerio Alabanza: [info]"
   → NO dar número (NO pidió contacto, pidió información)

REGLAS ABSOLUTAS:
1. NO des números de un tema para responder sobre otro tema
2. NO des números genéricos para preguntas específicas
3. Si NO hay número ESPECÍFICO de lo que piden → Di: "No tengo ese contacto específico. Te sugiero acercarte en VEA."
4. NUNCA dar números para personas/ministerios específicos si solo tienes número genérico

NÚMEROS TELEFÓNICOS DE PERSONAS (PROHIBIDO TOTAL)

POLÍTICA DE PRIVACIDAD:
Los documentos NO contienen números telefónicos de personas por política de privacidad.

REGLA ABSOLUTA:
- NUNCA des números telefónicos de personas individuales (pastores, diáconos, servidores, líderes)
- Aunque encuentres nombre + puesto, NO hay número personal
- NO inventes números (NUNCA)

SI preguntan por número de una persona:
Di: "Por política de privacidad, no se proporcionan números personales. Te sugiero acercarte directamente a esa persona en la iglesia o contactar a VEA para que te comuniquen."

Ejemplos:
Pregunta: "¿Número del Pastor Mauricio?"
Bot: "Por privacidad, no proporciono números personales. Te sugiero acercarte en VEA."

Pregunta: "¿Número del diácono de matrimonios?"
Bot: "Por privacidad, no proporciono números personales. Te sugiero acercarte en VEA."

NUNCA inventes números como: +52 55 1234 5678

SEPARACIÓN VEA vs MINISTERIOS ESPECÍFICOS (CRÍTICO)

VEA (iglesia) es DIFERENTE de sus ministerios de donaciones:
- DAYA (Fundación Dar y Amar)
- Youvenis
- Cobija un Corazón

Cada uno tiene gestión INDEPENDIENTE. NO mezclar:

1. Si preguntan por "VEA" o "iglesia" o "voluntariado" SIN mencionar ministerio específico:
   NO menciones DAYA, Youvenis ni Cobija un Corazón
   NO des números de estos ministerios
   Di: "Para voluntariado en VEA, te sugiero acercarte directamente en la iglesia"

2. Si preguntan ESPECÍFICAMENTE por "DAYA" o "Youvenis" o "Cobija un Corazón":
   Ahí SÍ da info/número de ese ministerio específico

3. Si preguntan "¿cómo ser voluntario?" sin especificar dónde:
   NO asumas que es DAYA
   Di: "¿Te refieres a voluntariado en VEA o en algún ministerio específico como DAYA, Youvenis o Cobija un Corazón?"

Ejemplos CORRECTOS:
- "¿Cómo ser voluntario?" → "Te sugiero acercarte a VEA para conocer las áreas donde puedes servir"
- "¿Cómo ayudar en DAYA?" → "Contacta a DAYA al +52..." (mencionó DAYA específicamente)

Ejemplos INCORRECTOS:
- "¿Cómo ser voluntario?" → "Contacta a DAYA al +52..." (asumió DAYA cuando no lo mencionaron)
- "¿Teléfono de VEA?" → "DAYA: +52..." (dio número de DAYA para pregunta de VEA)

DISCRIMINACIÓN DE CONTEXTO (CRÍTICO)
Recibirás múltiples documentos. Lee la PREGUNTA primero y usa SOLO los documentos relevantes:
- Si preguntan por UBICACIÓN/DIRECCIÓN de VEA: usa solo docs que hablen de "Iglesia VEA" o "ubicación/sede".
  NO uses direcciones de documentos de DONACIONES (esas son para transferencias, no ubicación física).
- Si preguntan por EVENTOS: usa solo docs tipo "evento", "reunión", "actividad" con fecha/hora.
  NO mezcles con info de donaciones o contactos.
- Si preguntan cómo DONAR/APOYAR/DAR DIEZMOS/DAR OFRENDAS: usa solo docs "cuenta", "CLABE", "donación", "ofrenda".
  NOTA: "Diezmos" y "Ofrendas" son SINÓNIMOS de "Donaciones".
  Aquí SÍ usa los datos bancarios.

RESPUESTAS AFIRMATIVAS/NEGATIVAS
Si el usuario responde SOLO "sí", "claro", "ok" después de que TÚ hiciste una pregunta:
- Mira TU mensaje anterior
- Si preguntaste "¿Te gustaría saber más eventos?" → Lista MÁS eventos de DOCUMENTOS
- Si preguntaste "¿Quieres info sobre X?" → Da información sobre X
- NO respondas genéricos como "gracias" sin cumplir tu oferta

ESTILO DE RESPUESTA
- MÁXIMO 4 LÍNEAS de texto (no más). Sé breve, claro y conciso.
- Lenguaje religioso amable, pero directo.
- Sin listas largas, salvo que el usuario pida eventos.
- Si no sabes algo con el contexto dado, dilo brevemente y ofrece canal de contacto si aparece en DOCUMENTOS.
- Evita textos largos o explicaciones excesivas.

MÓDULO DE EVENTOS
- Un DOCUMENTO es EVENTO si incluye: (fecha o día) + hora + actividad.
- NO repitas un mismo eventos dos veces
- PRIORIDAD: Eventos con ID "event_" son oficiales, muéstralos primero.
- Ordena por fecha/hora ascendente.
- Salida: "1. Título — dd/mm/yyyy — hh:mm — Lugar".
- Si hay más de 4, ofrece: "¿Te comparto más?"

MÓDULO DE MINISTERIOS (CRÍTICO)
Cuando pregunten "¿Qué ministerios hay?" o similar:
- Lista TODOS los ministerios que encuentres en documentos (NO solo 2).
- Formato: Solo NOMBRES de ministerios, sin personas ni contactos.
- Ejemplos: "VeaKids", "Conquistadores", "Daya", "Alabanza", "Matrimonios", "Ellas", etc.
- Si preguntan "¿Quién trabaja en X ministerio?" → Ahí SÍ da nombres de personas.
- Si preguntan "¿Qué hace X ministerio?" → Describe el ministerio, NO des contactos.
- NUNCA limites la lista a 2-3 ministerios cuando hay más en documentos.

REGLAS ANTI-ALUCINACIÓN (CRÍTICO - MÁXIMA PRIORIDAD)

NUNCA inventes información que NO esté EXPLÍCITAMENTE en documentos:

1. NO inventes nombres de:
   - Cursos, programas, discipulados
   - Eventos (si no está el nombre exacto)
   - Ministerios (solo menciona los que veas)
   - Personas (solo las que aparezcan)
   - Fechas u horarios (solo los exactos)
   - Ubicaciones o direcciones

2. SI preguntan por algo que NO está específicamente en documentos:
   → Di: "No tengo información específica sobre [X] en este momento. Te sugiero contactar directamente a VEA."
   → NUNCA inventes listas o nombres que suenen "razonables"

3. Ejemplos CORRECTOS:
   Usuario: "¿Qué cursos hay para nuevos creyentes?"
   Documentos: "VEA tiene discipulados" (sin nombres específicos)
   Bot: "VEA ofrece programas de discipulado para nuevos creyentes. Te sugiero contactar a la iglesia para conocer los cursos disponibles y sus horarios."
   
4. Ejemplos INCORRECTOS:
   Usuario: "¿Qué cursos hay para nuevos creyentes?"
   Documentos: "VEA tiene discipulados" (sin nombres)
   Bot: "Hay: 1. Discipulado para Nuevos Creyentes, 2. Curso de Fundamentos..." ← INVENTADO

5. REGLA DE ORO:
   Si NO está escrito EXACTAMENTE en documentos → NO lo menciones.
   Es MEJOR decir "no tengo esa información" que inventar.

REGLA FINAL
- Lee la PREGUNTA, discrimina qué documentos son relevantes, ignora el resto.
- No alucines, no inventes, mantén coherencia
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
        # Log la estructura sin escapar acentos (solo logging)
        data_str = json.dumps(data, indent=2, ensure_ascii=False)
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
    Get conversation history from Blob Storage.
    
    Args:
        phone_number: User's phone number
        
    Returns:
        List of conversation messages (max 10 messages / 5 turns)
    """
    try:
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not configured - history disabled")
        return []
        
        from azure.storage.blob import BlobServiceClient
        
        # Limpiar número de teléfono (eliminar todos los caracteres no numéricos)
        clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').replace('[', '').replace(']', '')
        
        # Configurar cliente de Blob
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_name = os.getenv('AZURE_STORAGE_DOCUMENTS_CONTAINER', 'documents')
        blob_name = f"conversations/{clean_phone}.json"
        
        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        # Intentar descargar historial (con timeout de 10 segundos)
        if blob_client.exists(timeout=10):
            data = blob_client.download_blob(timeout=10).readall()
            history = json.loads(data.decode('utf-8'))
            messages = history.get("messages", [])
            # Devolver últimos 10 mensajes (5 turnos)
            logger.info(f"Conversation history loaded for {clean_phone}: {len(messages)} messages")
            return messages[-10:]
        
        logger.debug(f"No conversation history found for {clean_phone}")
        return []
        
    except Exception as e:
        logger.error(f"Error getting conversation history for {phone_number}: {e}")
        return []

def _update_conversation_history(phone_number: str, user_message: str, bot_response: str) -> bool:
    """
    Update conversation history in Blob Storage.
    
    Args:
        phone_number: User's phone number
        user_message: User's message
        bot_response: Bot's response
        
    Returns:
        True if successful, False otherwise
    """
    try:
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not configured - history disabled")
            return False
        
        from azure.storage.blob import BlobServiceClient
        
        # Limpiar número de teléfono (eliminar todos los caracteres no numéricos)
        clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').replace('[', '').replace(']', '')
        
        # Configurar cliente de Blob
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_name = os.getenv('AZURE_STORAGE_DOCUMENTS_CONTAINER', 'documents')
        blob_name = f"conversations/{clean_phone}.json"
        
        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        # 1. Leer historial existente (si existe, con timeout de 10 segundos)
        existing_messages = []
        if blob_client.exists(timeout=10):
            data = blob_client.download_blob(timeout=10).readall()
            existing_data = json.loads(data.decode('utf-8'))
            existing_messages = existing_data.get("messages", [])
        
        # 2. Agregar nuevos mensajes
        now = datetime.now(timezone.utc).isoformat()
        existing_messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": now
        })
        existing_messages.append({
            "role": "assistant",
            "content": bot_response,
            "timestamp": now
        })
        
        # 3. Mantener solo últimos 10 mensajes (5 turnos)
        existing_messages = existing_messages[-10:]
        
        # 4. Guardar en Blob Storage
        history_data = {
            "phone_number": clean_phone,
            "messages": existing_messages,
            "last_modified": now
        }
        
        blob_client.upload_blob(
            json.dumps(history_data, ensure_ascii=False, indent=2),
            overwrite=True,
            timeout=10
        )
        
        logger.info(f"Conversation history updated for {clean_phone}: {len(existing_messages)} messages stored")
        return True
        
    except Exception as e:
        logger.error(f"Error updating conversation history for {phone_number}: {e}")
        return False

def _calcular_dia_semana(fecha_str: str) -> Optional[str]:
    """
    Calcula el día de la semana para una fecha en formato DD/MM/YYYY.
    
    Args:
        fecha_str: Fecha en formato "DD/MM/YYYY" (ej: "09/11/2025")
        
    Returns:
        Día de la semana en español (ej: "sábado") o None si error
    """
    try:
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
        dias_es = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        return dias_es[fecha.weekday()]
    except Exception as e:
        logger.warning(f"Error calculando día de semana para '{fecha_str}': {e}")
        return None

def _extraer_fecha_del_content(content: str) -> Optional[str]:
    """
    Extrae fechas del texto en formatos comunes.
    
    Args:
        content: Texto del documento
        
    Returns:
        Fecha en formato DD/MM/YYYY o None
    """
    # Patrón para DD/MM/YYYY
    patron_completo = r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})'
    match = re.search(patron_completo, content)
    if match:
        dia, mes, año = match.groups()
        return f"{dia.zfill(2)}/{mes.zfill(2)}/{año}"
    
    # Patrón para "7 DE JUNIO" o "7 de junio"
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    for mes_nombre, mes_num in meses.items():
        patron = rf'(\d{{1,2}})\s+de\s+{mes_nombre}'
        match = re.search(patron, content.lower())
        if match:
            dia = match.group(1)
            from datetime import datetime
            año_actual = datetime.now().year
            return f"{dia.zfill(2)}/{mes_num}/{año_actual}"
    
    return None

def _extraer_dia_semana_del_content(content: str) -> Optional[str]:
    """
    Extrae el día de la semana del texto si está presente.
    
    Args:
        content: Texto del documento
        
    Returns:
        Día de la semana en español o None
    """
    content_lower = content.lower()
    
    dias = {
        'lunes': 'lunes', 'martes': 'martes', 'miércoles': 'miércoles',
        'miercoles': 'miércoles', 'jueves': 'jueves', 'viernes': 'viernes',
        'sábado': 'sábado', 'sabado': 'sábado', 'domingo': 'domingo'
    }
    
    for dia_buscar, dia_normalizado in dias.items():
        if dia_buscar in content_lower:
            return dia_normalizado
    
    return None

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
            
            # Perform VECTOR search EXACTAMENTE como CLI
            # Paso 1: Generar embedding del query (como EmbeddingManager.find_similar línea 108)
            openai_key = os.environ.get('AZURE_OPENAI_KEY')
            openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
            embedding_deployment = os.environ.get('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
            
            if not openai_key or not openai_endpoint:
                logger.error("OpenAI configuration missing for embeddings")
                return None
            
            from openai import AzureOpenAI
            openai_client = AzureOpenAI(
                api_key=openai_key,
                api_version="2024-02-15-preview",
                azure_endpoint=openai_endpoint
            )
            
            embedding_response = openai_client.embeddings.create(
                input=query,
                model=embedding_deployment
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Paso 2: Búsqueda vectorial (como AzureSearchClient.search_vector línea 198-213)
            search_options = {
                "vector_queries": [{
                    "vector": query_embedding,
                    "fields": "embedding",
                    "k": 15,  # Aumentado para filtrado posterior
                    "kind": "vector"
                }],
                "select": ["id", "content", "embedding", "created_at"],
                "top": 15  # Aumentado de 5 a 15
            }
            
            search_results = search_client.search(search_text="", **search_options)
            
            # Filtrado inteligente
            results_list = list(search_results)
            
            # Detectar si pregunta por CONTACTO o MINISTERIOS o PERSONAS o DONACIONES
            palabras_contacto = ['contacto', 'teléfono', 'telefono', 'número', 'numero', 'llamar', 'comunicar', 'hablar', 'whatsapp']
            palabras_ministerio = ['ministerio', 'ministerios', 'qué ministerios', 'cuáles ministerios', 'quién trabaja', 'quien trabaja', 'quién es', 'quien es']
            palabras_donacion = ['donación', 'donaciones', 'donar', 'diezmo', 'diezmos', 'ofrenda', 'ofrendas', 'dar', 'apoyo', 'apoyar']
            
            es_pregunta_contacto = any(palabra in query.lower() for palabra in palabras_contacto)
            es_pregunta_ministerio = any(palabra in query.lower() for palabra in palabras_ministerio)
            es_pregunta_donacion = any(palabra in query.lower() for palabra in palabras_donacion)
            
            # Filtrar contactos SOLO si NO es pregunta de contacto NI de ministerio/persona
            if not es_pregunta_contacto and not es_pregunta_ministerio:
                results_list = [r for r in results_list if not r.get('id', '').startswith('contact_')]
                logger.info(f"[FILTER] Contacts excluded. Remaining: {len(results_list)} documents")
            else:
                logger.info(f"[FILTER] Contacts included (question about contact/ministry/person). Total: {len(results_list)} documents")
            
            # Filtrar donations SIEMPRE si NO es pregunta sobre donaciones
            palabras_donacion_extra = ['cuenta', 'clabe', 'transferencia', 'bancario']
            es_pregunta_donacion_completa = es_pregunta_donacion or any(palabra in query.lower() for palabra in palabras_donacion_extra)
            
            if not es_pregunta_donacion_completa:
                # SIEMPRE excluir donations si no pregunta por donaciones
                results_list = [r for r in results_list if not r.get('id', '').startswith('donation_')]
                logger.info(f"[FILTER] Donations excluded (not donation question). Remaining: {len(results_list)} documents")
            else:
                logger.info(f"[FILTER] Donations included (question about donations/tithes/offerings)")
            
            # Priorizar events automáticamente
            events = [r for r in results_list if r.get('id', '').startswith('event_')]
            others = [r for r in results_list if not r.get('id', '').startswith('event_')]
            
            if events:
                results_list = events + others
                logger.info(f"[FILTER] Prioritized {len(events)} events")
            
            # Enriquecer eventos con día de semana (extrayendo del content)
            for result in results_list:
                doc_id = result.get('id', '')
                if doc_id.startswith('event_'):
                    content = result.get('content', '')
                    
                    # Intentar extraer fecha completa
                    fecha_extraida = _extraer_fecha_del_content(content)
                    
                    if fecha_extraida:
                        dia_semana = _calcular_dia_semana(fecha_extraida)
                        if dia_semana:
                            # Limpiar días contradictorios del texto
                            content_limpio = content
                            dias_a_limpiar = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado', 'domingo']
                            
                            for dia in dias_a_limpiar:
                                if dia != dia_semana:
                                    content_limpio = re.sub(rf'\b{dia}\b', '', content_limpio, flags=re.IGNORECASE)
                            
                            content_limpio = re.sub(r'\s+', ' ', content_limpio).strip()
                            
                            # Agregar info explícita al INICIO
                            es_fin_semana = dia_semana in ['sábado', 'domingo']
                            tipo_dia = "FIN DE SEMANA" if es_fin_semana else "ENTRE SEMANA"
                            info_fecha = f"[FECHA REAL: {fecha_extraida} - {dia_semana.upper()} ({tipo_dia})]"
                            result['content'] = f"{info_fecha}\n\n{content_limpio}"
                            result['_fecha_calculada'] = fecha_extraida
                            result['_dia_semana'] = dia_semana
                            logger.info(f"[ENRICH] {doc_id}: {fecha_extraida} -> {dia_semana} ({tipo_dia})")
                    else:
                        # Sin fecha completa, buscar día en texto
                        dia_semana = _extraer_dia_semana_del_content(content)
                        if dia_semana:
                            content_limpio = content
                            dias_a_limpiar = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado', 'domingo']
                            
                            for dia in dias_a_limpiar:
                                if dia != dia_semana:
                                    content_limpio = re.sub(rf'\b{dia}\b', '', content_limpio, flags=re.IGNORECASE)
                            
                            content_limpio = re.sub(r'\s+', ' ', content_limpio).strip()
                            
                            es_fin_semana = dia_semana in ['sábado', 'domingo']
                            tipo_dia = "FIN DE SEMANA" if es_fin_semana else "ENTRE SEMANA"
                            info_dia = f"[DÍA DE LA SEMANA: {dia_semana.upper()} ({tipo_dia})]"
                            result['content'] = f"{info_dia}\n\n{content_limpio}"
                            result['_dia_semana'] = dia_semana
                            logger.info(f"[ENRICH] {doc_id}: Day -> {dia_semana} ({tipo_dia})")
            
            # Filtrar por día de semana (si pregunta específica)
            palabras_fin_semana = ['fin de semana', 'sábado', 'sabado', 'domingo']
            palabras_entre_semana = ['entre semana', 'lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes']
            
            es_pregunta_fin_semana = any(p in query.lower() for p in palabras_fin_semana)
            es_pregunta_entre_semana = any(p in query.lower() for p in palabras_entre_semana)
            
            if es_pregunta_fin_semana:
                logger.info("[FILTER] Weekend events filter applied")
                events_filtered = []
                for r in results_list:
                    if r.get('id', '').startswith('event_'):
                        dia = r.get('_dia_semana')
                        if dia and dia in ['sábado', 'domingo']:
                            events_filtered.append(r)
                        elif not dia:
                            events_filtered.append(r)
                    else:
                        events_filtered.append(r)
                results_list = events_filtered
                logger.info(f"[FILTER] After weekend filter: {len(results_list)} documents")
            
            elif es_pregunta_entre_semana:
                logger.info("[FILTER] Weekday events filter applied")
                events_filtered = []
                for r in results_list:
                    if r.get('id', '').startswith('event_'):
                        dia = r.get('_dia_semana')
                        if dia and dia in ['lunes', 'martes', 'miércoles', 'jueves', 'viernes']:
                            events_filtered.append(r)
                        elif not dia:
                            events_filtered.append(r)
                    else:
                        events_filtered.append(r)
                results_list = events_filtered
                logger.info(f"[FILTER] After weekday filter: {len(results_list)} documents")
            
            # Ordenar por fecha (si pregunta "próximo")
            palabras_proximo = ['próximo', 'proximo', 'siguiente', 'próximos', 'proximos', 'siguientes']
            es_pregunta_proximo = any(p in query.lower() for p in palabras_proximo)
            
            if es_pregunta_proximo:
                logger.info("[SORT] Sorting events by date")
                events_to_sort = [r for r in results_list if r.get('id', '').startswith('event_') and r.get('_fecha_calculada')]
                others = [r for r in results_list if not (r.get('id', '').startswith('event_') and r.get('_fecha_calculada'))]
                
                def parse_fecha_sort(fecha_str):
                    try:
                        from datetime import datetime
                        return datetime.strptime(fecha_str, "%d/%m/%Y")
                    except:
                        from datetime import datetime
                        return datetime.min
                
                events_to_sort.sort(key=lambda r: parse_fecha_sort(r.get('_fecha_calculada', '')))
                results_list = events_to_sort[:3] + others
                logger.info(f"[SORT] Top 3 upcoming events selected")
            
            # Top 7 (aumentado de 5 para más contexto)
            results_list = results_list[:7]
            
            # Paso 3: Extraer contexto (como handlers._rag_answer línea 652-660)
            context_parts = []
            for result in results_list:
                try:
                    # CLI línea 655: h.get('text') or h.get('content')
                    txt = (result.get('text') or result.get('content') or '').strip()
                except Exception:
                    txt = ''
                if txt:
                    context_parts.append(f"- {txt}")  # Sin truncar, como CLI línea 659
            
            if context_parts:
                context = "\n".join(context_parts)[:4000]  # Límite 4000 como CLI línea 660
                logger.info(f"[V2] Generated RAG context with {len(context)} characters from {len(context_parts)} results")
                return str(context)
            else:
                logger.info("[V2] No relevant context found in Azure Search results")
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
        
        # EXACTAMENTE como CLI handlers._rag_answer líneas 647-673
        
        # Detectar preguntas personales y saludos (no requieren RAG)
        palabras_personales = ['me llamo', 'mi nombre', 'soy', 'mi edad', 'tengo', 'años']
        saludos = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'qué tal', 'hey', 'saludos']
        
        es_pregunta_personal = any(palabra in user_message.lower() for palabra in palabras_personales)
        es_saludo = any(saludo in user_message.lower() for saludo in saludos)
        
        # Si no hay contexto RAG Y NO es pregunta personal NI saludo, retornar mensaje
        if not rag_context and not es_pregunta_personal and not es_saludo:
            logger.info("[V2] No RAG context available - returning no info message")
            return "No encontré información relevante en el índice."
        
        if rag_context:
            logger.info(f"[V2] RAG context available: {len(rag_context)} characters")
        else:
            if es_saludo:
                logger.info("[V2] Greeting detected - proceeding without RAG context")
            else:
                logger.info("[V2] Personal question detected - proceeding without RAG context")
        
        # Agregar fecha y hora actual para contexto temporal
        from datetime import datetime
        import pytz
        tz = pytz.timezone('America/Mexico_City')
        fecha_hoy = datetime.now(tz).strftime("%d/%m/%Y")
        dia_semana_hoy = datetime.now(tz).strftime("%A")
        hora_actual = datetime.now(tz).strftime("%H:%M")
        
        # Traducir día de la semana a español
        dias_es = {
            'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
            'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
        }
        dia_semana_hoy = dias_es.get(dia_semana_hoy, dia_semana_hoy)
        
        # Construir mensajes con historial conversacional
        messages = [{"role": "system", "content": BOT_SYSTEM_PROMPT}]
        
        # Agregar historial de conversación (últimos 12 mensajes)
        for msg in conversation_history[-12:]:
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })
        
        # Construir mensaje actual con o sin RAG
        if rag_context:
            user_content = f"[FECHA Y HORA ACTUAL: {fecha_hoy} ({dia_semana_hoy}) - {hora_actual}]\n\n[Conversación anterior arriba]\n\n[DOCUMENTOS DE VEA]:\n{rag_context}\n\n[PREGUNTA]:\n{user_message}"
        else:
            # Pregunta personal sin RAG
            user_content = f"[FECHA Y HORA ACTUAL: {fecha_hoy} ({dia_semana_hoy}) - {hora_actual}]\n\n[Conversación anterior arriba]\n\n[PREGUNTA]:\n{user_message}"
        
        messages.append({"role": "user", "content": user_content})
        
        logger.info(f"[V2] Sending request to OpenAI with {len(messages)} messages (fecha: {fecha_hoy}, hora: {hora_actual})")
        
        # Manejo de errores de filtro de contenido
        try:
            # Generate response con temperatura reducida para evitar alucinaciones
            response = client.chat.completions.create(
                model=openai_deployment,  # type: ignore
                messages=messages,  # type: ignore
                max_tokens=350,
                temperature=0.0  # 0.0 para evitar inventar información
            )
            
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                ai_response = response.choices[0].message.content.strip()
                
                # Post-procesar respuesta para eliminar palabras temporales relativas
                ai_response_original = ai_response
                
                # Eliminar "mañana", "hoy", "pasado mañana", etc.
                palabras_prohibidas = [
                    (r'\bmañana,?\s*', ''),
                    (r'\bhoy,?\s*', ''),
                    (r'\bpasado mañana,?\s*', ''),
                    (r'\bayer,?\s*', ''),
                    (r'\beste\s+fin\s+de\s+semana,?\s*', 'este fin de semana '),
                    (r'\besta\s+semana,?\s*', ''),
                ]
                
                for patron, reemplazo in palabras_prohibidas:
                    ai_response = re.sub(patron, reemplazo, ai_response, flags=re.IGNORECASE)
                
                # Limpiar espacios dobles y comas dobles
                ai_response = re.sub(r'\s+', ' ', ai_response)
                ai_response = re.sub(r',\s*,', ',', ai_response)
                ai_response = ai_response.strip()
                
                # Capitalizar primera letra si se perdió
                if ai_response and ai_response[0].islower():
                    ai_response = ai_response[0].upper() + ai_response[1:]
                
                # Capitalizar después de ". "
                ai_response = re.sub(r'\.\s+([a-záéíóúñ])', lambda m: '. ' + m.group(1).upper(), ai_response)
                
                if ai_response != ai_response_original:
                    logger.info(f"[POST-PROCESS] Removed temporal words from response")
                
                logger.info(f"Generated AI response: {ai_response[:100]}...")
                return ai_response
            else:
                logger.error("No response content from OpenAI")
                return "Lo siento, no pude generar una respuesta. Por favor intenta de nuevo."
                
        except Exception as e:
            error_str = str(e)
            # Manejar filtro de contenido específicamente
            if 'content_filter' in error_str or 'BadRequest' in str(type(e)):
                logger.warning(f"[CONTENT_FILTER] Message blocked for user: {user_message[:50]}")
                return "Disculpa, no pude procesar tu mensaje debido a las políticas de seguridad. Intenta reformular tu pregunta de otra forma."
            else:
                logger.error(f"Error generating AI response: {e}")
                raise
            
    except Exception as e:
        logger.error(f"Error in _generate_ai_response outer: {e}")
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
                    content=str(text)  # fuerza tipo str para el SDK, sin recodificar ni alterar contenido
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
        
        # Serializa exactamente el JSON que se va a firmar y enviar (sin espacios)
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        
        # Build URL with API version
        url = f"{endpoint}/messages?api-version=2024-02-15-preview"
        
        logger.info(f"Using endpoint: {endpoint}")
        logger.info(f"Using API version: 2024-02-15-preview")
        
        # Firma sobre la MISMA cadena
        signature = _generate_hmac_signature(access_key, url, 'POST', payload_json)
        
        if not signature:
            logger.error("Failed to generate HMAC signature")
            return False
        
        # Create headers with HMAC signature
        headers = {
            'Authorization': f'HMAC-SHA256 {signature}',
            'Content-Type': 'application/json; charset=utf-8',
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
                # Enviar los MISMOS bytes firmados (UTF-8) y añadir Accept
                # response = requests.post(url, json=payload, headers=headers, timeout=30)  # ← comentado: causaba doble serialización
                response = requests.post(
                    url,
                    data=payload_json.encode('utf-8'),
                    headers={
                        **headers,
                        'Accept': 'application/json',
                    },
                    timeout=30,
                )
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
    
    # Log payload size (sin escapar acentos en logs)
    payload_str = json.dumps(event.get_json(), ensure_ascii=False)
    payload_size = len(payload_str)
    logger.info(f"Payload size: {payload_size} bytes")
    
    # Log truncated payload if debug enabled
    if E2E_DEBUG and payload_size > 0:
        truncated_payload = payload_str[:2000] + "..." if len(payload_str) > 2000 else payload_str
        logger.info(f"Payload (truncated): {truncated_payload}")
    
    try:
        # Handle SubscriptionValidation events
        if event.event_type == "Microsoft.EventGrid.SubscriptionValidationEvent":
            logger.info("[V2] Processing subscription validation event")
            
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
            logger.info("[V2] Processing Advanced Message Received event")
            
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
            
            logger.info(f"[V2] Processing message from {from_number} (ID: {message_id}): {text}")
            
            # Get conversation history
            conversation_history = _get_conversation_history(from_number)
            
            # Get RAG context if enabled
            rag_context = _get_rag_context(text)
            
            # Generate AI response
            ai_response = _generate_ai_response(text, conversation_history, rag_context)
            
            # Update conversation history
            _update_conversation_history(from_number, text, ai_response)
            
            # Normalizar UTF-8 antes de enviar (evitar mojibake)
            # ai_response_normalized = ai_response.encode('utf-8').decode('utf-8')  # ← comentado para evitar doble transcodificación
            
            # Send WhatsApp response (enviar la cadena Unicode tal cual)
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