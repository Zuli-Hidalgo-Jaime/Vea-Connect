"""
VEA Connect - Rutas API para el Chatbot
API REST para interactuar con el chatbot de VEA Connect
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import uuid
from datetime import datetime

from ..chatbot.vea_chatbot import vea_chatbot

# Crear router
router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

# Modelos Pydantic
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    conversation_id: str
    timestamp: str
    error: Optional[str] = None

class FunctionInfo(BaseModel):
    name: str
    description: str

class AvailableFunctionsResponse(BaseModel):
    functions: List[FunctionInfo]

# Almacenamiento temporal de conversaciones (en producción usar base de datos)
conversations = {}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """
    Endpoint para enviar mensajes al chatbot
    
    Args:
        chat_message: Mensaje del usuario
        
    Returns:
        Respuesta del chatbot
    """
    try:
        # Generar ID de conversación si no existe
        conversation_id = chat_message.conversation_id or str(uuid.uuid4())
        
        # Procesar mensaje con el chatbot
        response = await vea_chatbot.chat(
            user_message=chat_message.message,
            conversation_id=conversation_id
        )
        
        # Almacenar conversación
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        conversations[conversation_id].append({
            "user_message": chat_message.message,
            "bot_response": response["response"],
            "timestamp": response["timestamp"]
        })
        
        return ChatResponse(
            success=response["success"],
            response=response["response"],
            conversation_id=conversation_id,
            timestamp=response["timestamp"],
            error=response.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar mensaje: {str(e)}"
        )

@router.get("/functions", response_model=AvailableFunctionsResponse)
async def get_available_functions():
    """
    Obtener lista de funciones disponibles del chatbot
    
    Returns:
        Lista de funciones disponibles
    """
    try:
        functions = vea_chatbot.get_available_functions()
        
        function_info = [
            FunctionInfo(name=func["name"], description=func["description"])
            for func in functions
        ]
        
        return AvailableFunctionsResponse(functions=function_info)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener funciones: {str(e)}"
        )

@router.get("/conversations/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """
    Obtener historial de una conversación
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        Historial de la conversación
    """
    try:
        if conversation_id not in conversations:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada"
            )
        
        return {
            "conversation_id": conversation_id,
            "messages": conversations[conversation_id],
            "total_messages": len(conversations[conversation_id])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial: {str(e)}"
        )

@router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Limpiar historial de una conversación
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        Confirmación de limpieza
    """
    try:
        if conversation_id in conversations:
            del conversations[conversation_id]
            return {"message": "Conversación eliminada exitosamente"}
        else:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al limpiar conversación: {str(e)}"
        )

@router.post("/clear-history")
async def clear_all_history():
    """
    Limpiar todo el historial de conversaciones
    
    Returns:
        Confirmación de limpieza
    """
    try:
        global conversations
        conversations = {}
        vea_chatbot.clear_history()
        
        return {"message": "Historial limpiado exitosamente"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al limpiar historial: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Verificar estado del chatbot
    
    Returns:
        Estado del servicio
    """
    try:
        # Verificar que el chatbot esté funcionando
        test_response = await vea_chatbot.chat("Hola")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "chatbot_working": test_response["success"]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Endpoint para probar funciones específicas
@router.post("/test-search")
async def test_search_function(query: str, category: str = None):
    """
    Probar función de búsqueda directamente
    
    Args:
        query: Consulta de búsqueda
        category: Categoría específica (opcional)
        
    Returns:
        Resultados de búsqueda
    """
    try:
        from ..chatbot.search_agent import SearchAgent
        
        search_agent = SearchAgent()
        
        if category:
            # Usar función específica según categoría
            if category.lower() == "eventos":
                result = search_agent.search_events(query)
            elif category.lower() == "medicamentos":
                result = search_agent.search_medications(query)
            elif category.lower() == "lideres":
                result = search_agent.search_leaders(query)
            elif category.lower() == "servicios":
                result = search_agent.search_services(query)
            elif category.lower() == "donaciones":
                result = search_agent.search_donations(query)
            else:
                result = search_agent.search_documents(query, category)
        else:
            result = search_agent.search_documents(query)
        
        return {
            "success": True,
            "query": query,
            "category": category,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda: {str(e)}"
        )