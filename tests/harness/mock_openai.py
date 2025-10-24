"""
Mock puro de OpenAI para testing sin dependencias de Django.

Este módulo proporciona mocks de las funciones principales de OpenAI
para testing aislado sin necesidad de configuración de Django.
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class MockEmbedding:
    """Mock de un embedding de OpenAI."""
    object: str = "embedding"
    embedding: List[float] = None
    index: int = 0
    
    def __post_init__(self):
        if self.embedding is None:
            # Generar embedding mock de 1536 dimensiones
            import random
            random.seed(42)  # Para resultados consistentes
            self.embedding = [random.uniform(-1, 1) for _ in range(1536)]


@dataclass
class MockEmbeddingResponse:
    """Mock de respuesta de embeddings de OpenAI."""
    object: str = "list"
    data: List[MockEmbedding] = None
    model: str = "text-embedding-ada-002"
    usage: Dict[str, int] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = []
        if self.usage is None:
            self.usage = {
                "prompt_tokens": 0,
                "total_tokens": 0
            }


@dataclass
class MockChatMessage:
    """Mock de mensaje de chat."""
    role: str
    content: str


@dataclass
class MockChatChoice:
    """Mock de elección de chat."""
    index: int = 0
    message: MockChatMessage = None
    finish_reason: str = "stop"
    
    def __post_init__(self):
        if self.message is None:
            self.message = MockChatMessage(role="assistant", content="")


@dataclass
class MockChatResponse:
    """Mock de respuesta de chat de OpenAI."""
    id: str = None
    object: str = "chat.completion"
    created: int = None
    model: str = "gpt-4"
    choices: List[MockChatChoice] = None
    usage: Dict[str, int] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        if self.created is None:
            self.created = int(time.time())
        if self.choices is None:
            self.choices = []
        if self.usage is None:
            self.usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }


class MockOpenAI:
    """Mock principal de OpenAI para testing."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Inicializar mock de OpenAI.
        
        Args:
            api_key: API key (ignorada en mock)
            base_url: Base URL (ignorada en mock)
        """
        self.api_key = api_key or "mock-api-key"
        self.base_url = base_url or "https://api.openai.com/v1"
        self._mock_responses = {}
        self._call_count = 0
        
    def embeddings(self):
        """Retorna mock del cliente de embeddings."""
        return MockEmbeddingsClient()
    
    def chat(self):
        """Retorna mock del cliente de chat."""
        return MockChatClient()


class MockEmbeddingsClient:
    """Mock del cliente de embeddings."""
    
    def create(self, input: Union[str, List[str]], model: str = "text-embedding-ada-002", **kwargs) -> MockEmbeddingResponse:
        """
        Crear embeddings mock.
        
        Args:
            input: Texto o lista de textos
            model: Modelo a usar (ignorado en mock)
            **kwargs: Argumentos adicionales (ignorados)
            
        Returns:
            MockEmbeddingResponse con embeddings simulados
        """
        if isinstance(input, str):
            input = [input]
        
        embeddings = []
        for i, text in enumerate(input):
            # Generar embedding único basado en el texto
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            seed = int(hash_obj.hexdigest()[:8], 16)
            
            import random
            random.seed(seed)
            embedding_values = [random.uniform(-1, 1) for _ in range(1536)]
            
            embeddings.append(MockEmbedding(
                embedding=embedding_values,
                index=i
            ))
        
        return MockEmbeddingResponse(
            data=embeddings,
            model=model,
            usage={
                "prompt_tokens": sum(len(text.split()) for text in input),
                "total_tokens": sum(len(text.split()) for text in input)
            }
        )


class MockChatClient:
    """Mock del cliente de chat."""
    
    def completions(self):
        """Retorna mock del cliente de completions."""
        return MockCompletionsClient()


class MockCompletionsClient:
    """Mock del cliente de completions."""
    
    def create(self, messages: List[Dict[str, str]], model: str = "gpt-4", **kwargs) -> MockChatResponse:
        """
        Crear completion mock.
        
        Args:
            messages: Lista de mensajes
            model: Modelo a usar
            **kwargs: Argumentos adicionales
            
        Returns:
            MockChatResponse con respuesta simulada
        """
        # Generar respuesta basada en el último mensaje del usuario
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            last_user_message = user_messages[-1].get("content", "")
            
            # Respuesta mock inteligente basada en el contenido
            if "hola" in last_user_message.lower():
                response_content = "¡Hola! ¿En qué puedo ayudarte hoy?"
            elif "buscar" in last_user_message.lower() or "search" in last_user_message.lower():
                response_content = "He encontrado información relevante sobre tu consulta. Aquí tienes los resultados más importantes..."
            elif "descargar" in last_user_message.lower() or "download" in last_user_message.lower():
                response_content = "Te ayudo con la descarga. ¿Qué archivo necesitas?"
            else:
                response_content = f"Entiendo tu consulta sobre '{last_user_message[:50]}...'. Te proporciono la información solicitada."
        else:
            response_content = "No entiendo tu consulta. ¿Podrías reformularla?"
        
        # Calcular tokens aproximados
        total_tokens = sum(len(msg.get("content", "").split()) for msg in messages)
        completion_tokens = len(response_content.split())
        
        return MockChatResponse(
            model=model,
            choices=[
                MockChatChoice(
                    message=MockChatMessage(
                        role="assistant",
                        content=response_content
                    )
                )
            ],
            usage={
                "prompt_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens + completion_tokens
            }
        )


# Funciones de conveniencia para testing
def create_mock_embedding(text: str, dimensions: int = 1536) -> List[float]:
    """
    Crear un embedding mock para un texto específico.
    
    Args:
        text: Texto para generar embedding
        dimensions: Dimensiones del embedding
        
    Returns:
        Lista de valores float simulando embedding
    """
    import hashlib
    import random
    
    hash_obj = hashlib.md5(text.encode())
    seed = int(hash_obj.hexdigest()[:8], 16)
    random.seed(seed)
    
    return [random.uniform(-1, 1) for _ in range(dimensions)]


def create_mock_chat_response(content: str, model: str = "gpt-4") -> MockChatResponse:
    """
    Crear una respuesta de chat mock.
    
    Args:
        content: Contenido de la respuesta
        model: Modelo usado
        
    Returns:
        MockChatResponse
    """
    return MockChatResponse(
        model=model,
        choices=[
            MockChatChoice(
                message=MockChatMessage(
                    role="assistant",
                    content=content
                )
            )
        ],
        usage={
            "prompt_tokens": 10,
            "completion_tokens": len(content.split()),
            "total_tokens": 10 + len(content.split())
        }
    )


def get_mock_openai_client() -> MockOpenAI:
    """
    Obtener instancia mock de OpenAI.
    
    Returns:
        MockOpenAI configurado para testing
    """
    return MockOpenAI()


def create_mock_openai_client() -> MockOpenAI:
    """
    Alias para get_mock_openai_client para compatibilidad.
    
    Returns:
        MockOpenAI configurado para testing
    """
    return get_mock_openai_client()


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso del mock
    client = get_mock_openai_client()
    
    # Probar embeddings
    embedding_response = client.embeddings().create(
        input=["Hola mundo", "Test embedding"],
        model="text-embedding-ada-002"
    )
    print(f"Embeddings creados: {len(embedding_response.data)}")
    
    # Probar chat
    chat_response = client.chat().completions().create(
        messages=[
            {"role": "user", "content": "Hola, ¿cómo estás?"}
        ],
        model="gpt-4"
    )
    print(f"Respuesta del chat: {chat_response.choices[0].message.content}")
