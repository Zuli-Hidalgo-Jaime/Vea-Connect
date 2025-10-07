"""
VEA Connect - Configuración del Sistema
Sistema de gestión de conocimiento para comunidad religiosa
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración principal del sistema VEA Connect"""
    
    # Azure AI Search
    SEARCH_SERVICE_NAME = os.getenv("SEARCH_SERVICE_NAME")
    SEARCH_SERVICE_KEY = os.getenv("SEARCH_SERVICE_KEY")
    SEARCH_SERVICE_ENDPOINT = os.getenv("SEARCH_SERVICE_ENDPOINT")
    SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME")
    
    # Azure Storage
    STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
    STORAGE_CONTAINER_NAME = os.getenv("STORAGE_CONTAINER_NAME")
    STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
    
    # Azure Cognitive Services
    COGNITIVE_SERVICES_KEY = os.getenv("COGNITIVE_SERVICES_KEY")
    COGNITIVE_SERVICES_ENDPOINT = os.getenv("COGNITIVE_SERVICES_ENDPOINT")
    
    # Azure OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
    OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
    
    # WhatsApp
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    
    # Aplicación
    APP_NAME = "VEA Connect"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("PORT", "8000"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Módulos del sistema
    MODULES = {
        "documentos": {
            "name": "Documentos",
            "description": "Gestión de documentos y conocimiento",
            "subcategories": [
                "manuales", "politicas", "procedimientos", "formularios",
                "plantillas", "reportes", "actas", "correspondencia"
            ]
        },
        "directorio": {
            "name": "Directorio",
            "description": "Directorio de líderes y contactos",
            "subcategories": [
                "pastores", "diaconos", "ministros", "coordinadores",
                "voluntarios", "miembros", "contactos_externos"
            ]
        },
        "eventos": {
            "name": "Eventos",
            "description": "Gestión de eventos y actividades",
            "subcategories": [
                "cultos", "conferencias", "retiros", "actividades",
                "celebraciones", "servicios_especiales", "reuniones", "capacitaciones"
            ]
        },
        "donaciones": {
            "name": "Donaciones",
            "description": "Control de donaciones y recursos",
            "subcategories": [
                "monetarias", "especie", "servicios", "equipos",
                "alimentos", "medicamentos", "ropa", "muebles"
            ]
        }
    }
    
    # Personalidad del chatbot
    CHATBOT_PERSONALITY = {
        "tone": "alegre_y_amigable",
        "language": "no_tecnico_religiosamente",
        "greeting": "Hermano(a)",
        "farewell": "Que Dios te bendiga, Hermano(a)",
        "escalation_phrase": "Te voy a conectar con Relaciones Públicas para que te ayuden mejor"
    }
    
    # Respuestas del chatbot
    CHATBOT_RESPONSES = {
        "greeting": "Hola! Soy VEA Connect, tu asistente virtual de la iglesia. En que puedo ayudarte hoy?",
        "no_answer": "No tengo informacion especifica sobre eso, pero te puedo conectar con Relaciones Publicas para que te ayuden mejor.",
        "escalation": "Te voy a conectar con nuestro equipo de Relaciones Publicas. Ellos podran ayudarte mejor con esa consulta.",
        "farewell": "Que tengas un dia bendecido! Si necesitas algo mas, no dudes en preguntar."
    }
    
    # Triggers de escalamiento
    ESCALATION_TRIGGERS = [
        "no se", "no tengo", "no encuentro", "no estoy seguro",
        "no puedo ayudar", "complejo", "especifico", "detallado"
    ]
    
    # Configuración de búsqueda
    SEARCH_CONFIG = {
        "max_results": 50,
        "default_language": "es",
        "supported_languages": ["es", "en"],
        "max_file_size": "100MB"
    }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validar que la configuración esté completa"""
        required_vars = [
            cls.SEARCH_SERVICE_NAME,
            cls.SEARCH_SERVICE_KEY,
            cls.SEARCH_SERVICE_ENDPOINT,
            cls.SEARCH_INDEX_NAME,
            cls.STORAGE_ACCOUNT_NAME,
            cls.STORAGE_CONTAINER_NAME,
            cls.STORAGE_CONNECTION_STRING,
            cls.COGNITIVE_SERVICES_KEY,
            cls.COGNITIVE_SERVICES_ENDPOINT
        ]
        return all(var for var in required_vars)
    
    @classmethod
    def get_storage_connection_string(cls) -> str:
        """Obtener la cadena de conexión de Azure Storage"""
        if cls.STORAGE_CONNECTION_STRING:
            return cls.STORAGE_CONNECTION_STRING
        
        return (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={cls.STORAGE_ACCOUNT_NAME};"
            f"AccountKey={cls.STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix=core.windows.net"
        )
