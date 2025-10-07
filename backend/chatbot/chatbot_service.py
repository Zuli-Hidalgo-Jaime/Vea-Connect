"""
VEA Connect - Servicio de Chatbot
Servicio básico de chatbot para VEA Connect
"""

import logging
from typing import Dict, List, Optional, Any
from ..search.search_service import SearchService
from config import Config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotService:
    """Servicio de chatbot para VEA Connect"""
    
    def __init__(self):
        """Inicializar servicio de chatbot"""
        self.search_service = SearchService()
        self.personality = Config.CHATBOT_PERSONALITY
        self.responses = Config.CHATBOT_RESPONSES
        self.escalation_triggers = Config.ESCALATION_TRIGGERS
        
        logger.info("Servicio de chatbot inicializado")
    
    def process_message(self, user_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Procesar mensaje del usuario
        
        Args:
            user_message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Respuesta del chatbot
        """
        try:
            logger.info(f"Procesando mensaje: '{user_message}'")
            
            # Verificar si es un saludo
            if self._is_greeting(user_message):
                return self._generate_greeting_response()
            
            # Verificar si es una despedida
            if self._is_farewell(user_message):
                return self._generate_farewell_response()
            
            # Verificar si necesita escalamiento
            if self._needs_escalation(user_message):
                return self._generate_escalation_response()
            
            # Buscar información relevante
            search_results = self._search_relevant_information(user_message)
            
            # Generar respuesta basada en los resultados
            response = self._generate_response(user_message, search_results)
            
            return {
                "message": response,
                "search_results": search_results,
                "escalation_needed": False,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {str(e)}")
            return self._generate_error_response()
    
    def _is_greeting(self, message: str) -> bool:
        """Verificar si el mensaje es un saludo"""
        greetings = [
            "hola", "buenos días", "buenas tardes", "buenas noches",
            "hi", "hello", "hey", "saludos"
        ]
        
        message_lower = message.lower().strip()
        return any(greeting in message_lower for greeting in greetings)
    
    def _is_farewell(self, message: str) -> bool:
        """Verificar si el mensaje es una despedida"""
        farewells = [
            "adiós", "hasta luego", "nos vemos", "chao", "bye",
            "hasta pronto", "que tengas buen día"
        ]
        
        message_lower = message.lower().strip()
        return any(farewell in message_lower for farewell in farewells)
    
    def _needs_escalation(self, message: str) -> bool:
        """Verificar si el mensaje necesita escalamiento"""
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in self.escalation_triggers)
    
    def _search_relevant_information(self, query: str) -> Dict[str, Any]:
        """Buscar información relevante para la consulta"""
        try:
            # Realizar búsqueda general
            search_results = self.search_service.search_all(query, top=5)
            
            # Si no hay resultados, intentar búsqueda más amplia
            if search_results["total_results"] == 0:
                # Buscar por palabras clave individuales
                words = query.split()
                for word in words:
                    if len(word) > 3:  # Solo palabras significativas
                        partial_results = self.search_service.search_all(word, top=3)
                        if partial_results["total_results"] > 0:
                            search_results = partial_results
                            break
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error en búsqueda de información: {str(e)}")
            return {"total_results": 0, "modules": {}}
    
    def _generate_greeting_response(self) -> Dict[str, Any]:
        """Generar respuesta de saludo"""
        return {
            "message": self.responses["greeting"],
            "search_results": None,
            "escalation_needed": False,
            "context": {"greeting": True}
        }
    
    def _generate_farewell_response(self) -> Dict[str, Any]:
        """Generar respuesta de despedida"""
        return {
            "message": self.responses["farewell"],
            "search_results": None,
            "escalation_needed": False,
            "context": {"farewell": True}
        }
    
    def _generate_escalation_response(self) -> Dict[str, Any]:
        """Generar respuesta de escalamiento"""
        return {
            "message": self.responses["escalation"],
            "search_results": None,
            "escalation_needed": True,
            "context": {"escalation": True}
        }
    
    def _generate_response(self, user_message: str, search_results: Dict[str, Any]) -> str:
        """Generar respuesta basada en los resultados de búsqueda"""
        try:
            if search_results["total_results"] == 0:
                return self.responses["no_answer"]
            
            # Construir respuesta basada en los resultados
            response_parts = []
            
            # Agregar información de cada módulo
            for module, results in search_results["modules"].items():
                if results:
                    module_name = self._get_module_display_name(module)
                    response_parts.append(f"En {module_name} encontré:")
                    
                    for result in results[:3]:  # Máximo 3 resultados por módulo
                        name = result.get("name", "Documento")
                        content = result.get("merged_content", result.get("content", ""))
                        
                        # Truncar contenido si es muy largo
                        if len(content) > 200:
                            content = content[:200] + "..."
                        
                        response_parts.append(f"• {name}: {content}")
            
            # Combinar todas las partes
            response = " ".join(response_parts)
            
            # Agregar despedida amigable
            response += f" {self.personality['farewell']}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error al generar respuesta: {str(e)}")
            return self.responses["no_answer"]
    
    def _get_module_display_name(self, module: str) -> str:
        """Obtener nombre de visualización del módulo"""
        module_names = {
            "documentos": "Documentos",
            "directorio": "Directorio",
            "eventos": "Eventos",
            "donaciones": "Donaciones"
        }
        return module_names.get(module, module.title())
    
    def _generate_error_response(self) -> Dict[str, Any]:
        """Generar respuesta de error"""
        return {
            "message": "Lo siento, hubo un error al procesar tu consulta. Por favor, intenta de nuevo.",
            "search_results": None,
            "escalation_needed": True,
            "context": {"error": True}
        }
    
    def get_available_commands(self) -> List[str]:
        """Obtener comandos disponibles del chatbot"""
        return [
            "Buscar información sobre eventos",
            "Consultar directorio de líderes",
            "Información sobre donaciones",
            "Buscar documentos",
            "Ayuda general"
        ]
    
    def get_module_help(self, module: str) -> str:
        """Obtener ayuda específica para un módulo"""
        if module in self.search_service.modules:
            module_info = self.search_service.modules[module]
            return f"Puedo ayudarte con {module_info['description']}. Puedes preguntar sobre: {', '.join(module_info['subcategories'])}"
        return "Módulo no encontrado"
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar salud del servicio de chatbot"""
        try:
            search_health = self.search_service.health_check()
            
            return {
                "status": "healthy" if search_health["status"] == "healthy" else "unhealthy",
                "search_service": search_health,
                "personality": self.personality,
                "available_commands": self.get_available_commands()
            }
            
        except Exception as e:
            logger.error(f"Error en health check del chatbot: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }




