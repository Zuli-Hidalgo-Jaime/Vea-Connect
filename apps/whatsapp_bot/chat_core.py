"""
Núcleo de chat compartido entre CLI y webhook de WhatsApp.

Expone una función simple `generate_reply` que encapsula el flujo
de generación de respuesta con el mismo núcleo/prompt utilizado por el CLI.

No realiza envíos por ACS ni depende de SDKs externos; únicamente
construye la respuesta textual.
"""

from __future__ import annotations

from typing import Optional

from django.conf import settings  # type: ignore


def generate_reply(user_text: str, conversation_id: Optional[str] = None) -> str:
    """
    Genera una respuesta con el mismo núcleo que usa el CLI.

    - Respeta WHATSAPP_SYSTEM_PROMPT si está definido en settings.
    - Usa el flujo RAG del handler para garantizar paridad con el CLI.
    - No envía mensajes ni requiere ACS.
    """
    # Importar bajo demanda para evitar dependencias circulares al iniciar Django
    from apps.whatsapp_bot.handlers import WhatsAppBotHandler

    # El handler encapsula el núcleo RAG (_rag_answer) usado por el CLI
    handler = WhatsAppBotHandler()

    text = (user_text or "").strip()
    if not text:
        return ""

    try:
        # Usa el mismo núcleo RAG que el CLI
        reply = handler._rag_answer(text)
        # Si por alguna razón no hay respuesta, regresa cadena vacía
        return reply or ""
    except Exception as exc:  # pragma: no cover - tolerante a fallas en prod
        # Evita lanzar excepciones a la capa de transporte
        return f"Lo siento, no pude procesar tu mensaje. Detalle: {exc}"




