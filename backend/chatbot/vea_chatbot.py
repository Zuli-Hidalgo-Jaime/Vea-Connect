"""
VEA Connect - Chatbot Principal
Chatbot para la comunidad religiosa usando Semantic Kernel y Azure OpenAI
"""

import os
from typing import List, Dict, Any, Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from dotenv import load_dotenv

from chatbot.search_agent import create_search_agent_plugin

load_dotenv()

class VEAChatbot:
    """Chatbot principal para VEA Connect"""
    
    def __init__(self):
        """Inicializar el chatbot"""
        self.kernel = Kernel()
        self.chat_history = ChatHistory()
        self._setup_services()
        self._setup_plugins()
    
    def _setup_services(self):
        """Configurar servicios de AI"""
        # Configurar Azure OpenAI
        self.chat_service = AzureChatCompletion(
            service_id="vea_chat",
            deployment_name=os.getenv("OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo"),
            endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")
        )
        
        # Agregar servicio al kernel
        self.kernel.add_service(self.chat_service)
    
    def _setup_plugins(self):
        """Configurar plugins del chatbot"""
        try:
            # Agregar plugin de búsqueda
            create_search_agent_plugin(self.kernel)
            print("Plugins configurados correctamente")
        except Exception as e:
            print(f"Error al configurar plugins: {str(e)}")
            raise
    
    def _create_system_prompt(self) -> str:
        """Crear prompt del sistema para el chatbot"""
        return """
Eres el asistente virtual de la comunidad religiosa VEA Connect.

Estilo y conducta:
- Saluda y despídete amablemente (dirígete como "Hermano(a)").
- Responde con máxima concisión (2–3 líneas). Evita listas largas.
- No inventes información. Usa SOLO lo que proporcionen las funciones de búsqueda.
- Si no hay datos suficientes, dilo claramente y pide precisión.

Áreas de ayuda:
- Eventos y actividades, medicamentos de la farmacia, servicios y ministerios, directorio de líderes, donaciones.

Uso de funciones (obligatorio):
- search_documents, search_events, search_medications, search_leaders, search_services, search_donations.
- Siempre ejecuta la función adecuada ANTES de responder y redacta con lo encontrado.
"""
    
    async def chat(self, user_message: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Procesar mensaje del usuario y generar respuesta
        
        Args:
            user_message: Mensaje del usuario
            conversation_id: ID de la conversación (opcional)
            
        Returns:
            Respuesta del chatbot
        """
        try:
            # Primero, ejecutar búsqueda directamente basada en palabras clave
            search_result = None
            query_lower = user_message.lower()
            
            # Importar SearchAgent
            from chatbot.search_agent import SearchAgent
            search_agent = SearchAgent()
            
            # Detectar si es una pregunta relacionada con la iglesia
            church_keywords = [
                'evento', 'eventos', 'actividad', 'reunión', 'culto',
                'medicamento', 'medicina', 'farmacia', 'pastilla',
                'líder', 'líderes', 'pastor', 'pastores', 'directorio',
                'servicio', 'servicios', 'ministerio', 'ministerios',
                'donación', 'donaciones', 'donar', 'donativo', 'ofrenda',
                'iglesia', 'vea', 'comunidad', 'hermano', 'hermana',
                'culto', 'reunión', 'casa', 'amistad', 'daya', 'cda'
            ]
            
            is_church_related = any(word in query_lower for word in church_keywords)
            
            if not is_church_related:
                # No es una pregunta relacionada con la iglesia
                search_result = None
            elif any(word in query_lower for word in ['evento', 'eventos', 'actividad', 'reunión', 'culto']):
                search_result = search_agent.search_documents(user_message, category="eventos")
            elif any(word in query_lower for word in ['medicamento', 'medicina', 'farmacia', 'pastilla']):
                search_result = search_agent.search_documents(user_message, category="medicamentos")
            elif any(word in query_lower for word in ['líder', 'líderes', 'pastor', 'pastores', 'directorio']):
                search_result = search_agent.search_documents(user_message, category="lideres")
            elif any(word in query_lower for word in ['servicio', 'servicios', 'ministerio', 'ministerios']):
                search_result = search_agent.search_documents(user_message, category="servicios")
            elif any(word in query_lower for word in ['donación', 'donaciones', 'donar', 'donativo', 'ofrenda']):
                search_result = search_agent.search_documents(user_message, category="donaciones")
            else:
                # Búsqueda general solo si es relacionado con la iglesia
                search_result = search_agent.search_documents(user_message)
            
            # Agregar mensaje del usuario al historial
            self.chat_history.add_user_message(user_message)
            
            # Crear respuesta usando el LLM con la información encontrada
            if not is_church_related:
                # Pregunta no relacionada con la iglesia
                response_text = "¡Hola Hermano(a)! Soy el asistente virtual de VEA Connect y estoy aquí para ayudarte con información sobre nuestra comunidad religiosa: eventos, servicios, donaciones, medicamentos de la farmacia, etc. ¿En qué puedo ayudarte?"
            elif search_result and "No encontré información" not in search_result:
                # Usar el LLM para crear una respuesta amigable con la información encontrada
                from semantic_kernel.functions import KernelFunctionFromPrompt
                
                llm_prompt = f"""
Eres un asistente amigable de VEA Connect. El usuario preguntó: "{user_message}"

Información encontrada:
{search_result}

Responde de manera cálida y concisa (2-3 líneas máximo) usando SOLO la información proporcionada. 
Trata al usuario como "Hermano(a)" y sé positivo.
"""
                
                llm_function = KernelFunctionFromPrompt(
                    function_name="friendly_response",
                    plugin_name="VEAConnect",
                    prompt=llm_prompt
                )
                
                try:
                    llm_response = await self.kernel.invoke(llm_function, KernelArguments())
                    response_text = str(llm_response)
                except:
                    # Fallback si el LLM falla
                    response_text = f"¡Hola Hermano(a)! {search_result}"
            else:
                # No hay resultados, respuesta genérica
                response_text = "¡Hola Hermano(a)! No encontré información específica sobre eso en nuestra base de datos. Te recomiendo acercarte a la mesa de Relaciones Públicas para obtener más información. ¿Hay algo más en lo que pueda ayudarte?"
            
            # Agregar respuesta al historial
            self.chat_history.add_assistant_message(response_text)
            
            return {
                "success": True,
                "response": response_text,
                "conversation_id": conversation_id,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            error_message = f"Lo siento Hermano(a), hubo un problema técnico. ¿Podrías intentar de nuevo?"
            return {
                "success": False,
                "response": error_message,
                "error": str(e),
                "conversation_id": conversation_id,
                "timestamp": self._get_timestamp()
            }
    
    def get_available_functions(self) -> List[Dict[str, str]]:
        """Obtener lista de funciones disponibles"""
        return [
            {
                "name": "search_documents",
                "description": "Buscar en todos los documentos de la comunidad"
            },
            {
                "name": "search_events", 
                "description": "Buscar eventos y actividades"
            },
            {
                "name": "search_medications",
                "description": "Buscar medicamentos disponibles"
            },
            {
                "name": "search_leaders",
                "description": "Buscar información de líderes"
            },
            {
                "name": "search_services",
                "description": "Buscar servicios y ministerios"
            },
            {
                "name": "search_donations",
                "description": "Buscar información sobre donaciones"
            }
        ]
    
    def clear_history(self):
        """Limpiar historial de conversación"""
        self.chat_history = ChatHistory()
    
    def _get_timestamp(self) -> str:
        """Obtener timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()

# Instancia global del chatbot
vea_chatbot = VEAChatbot()

# Ejemplo de uso
if __name__ == "__main__":
    import asyncio
    
    async def test_chatbot():
        chatbot = VEAChatbot()
        
        # Prueba de consulta
        response = await chatbot.chat("¿Qué eventos hay esta semana?")
        print("Respuesta:", response["response"])
        
        # Prueba de búsqueda de medicamentos
        response = await chatbot.chat("¿Qué medicamentos tienen disponibles?")
        print("Respuesta:", response["response"])
    
    # Ejecutar prueba
    asyncio.run(test_chatbot())