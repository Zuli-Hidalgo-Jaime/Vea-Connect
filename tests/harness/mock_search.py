"""
Mock puro de Azure AI Search para testing sin dependencias de Django.

Este módulo proporciona mocks de las funciones principales de Azure AI Search
para testing aislado sin necesidad de configuración de Django.
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field


@dataclass
class MockSearchDocument:
    """Mock de un documento de búsqueda."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 1.0
    highlights: List[Dict[str, Any]] = field(default_factory=list)
    vector: List[float] = None
    
    def __post_init__(self):
        if self.vector is None:
            # Generar vector mock de 1536 dimensiones
            import random
            random.seed(hash(self.id) % 1000)
            self.vector = [random.uniform(-1, 1) for _ in range(1536)]


@dataclass
class MockSearchResult:
    """Mock de resultado de búsqueda."""
    document: MockSearchDocument
    score: float
    highlights: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MockSearchResponse:
    """Mock de respuesta de búsqueda."""
    results: List[MockSearchResult] = field(default_factory=list)
    total_count: int = 0
    search_time_ms: int = 0
    search_type: str = "hybrid"
    query_processed: str = ""
    filters_applied: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.total_count == 0:
            self.total_count = len(self.results)


@dataclass
class MockSearchFacet:
    """Mock de faceta de búsqueda."""
    value: str
    count: int


@dataclass
class MockSearchFacets:
    """Mock de facetas de búsqueda."""
    document_type: List[MockSearchFacet] = field(default_factory=list)
    tags: List[MockSearchFacet] = field(default_factory=list)
    categories: List[MockSearchFacet] = field(default_factory=list)


class MockSearchClient:
    """Mock del cliente de Azure AI Search."""
    
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """
        Inicializar mock del cliente de búsqueda.
        
        Args:
            endpoint: Endpoint de Azure Search (ignorado en mock)
            api_key: API key (ignorado en mock)
        """
        self.endpoint = endpoint or "https://mock-search.search.windows.net"
        self.api_key = api_key or "mock-api-key"
        self._mock_documents = self._create_mock_documents()
        self._search_count = 0
        
    def _create_mock_documents(self) -> List[MockSearchDocument]:
        """Crear documentos mock para testing."""
        documents = []
        
        # Documentos de ejemplo
        sample_docs = [
            {
                "id": "doc-001",
                "content": "Este es un documento sobre inteligencia artificial y machine learning. Contiene información sobre algoritmos de clasificación y redes neuronales.",
                "metadata": {
                    "filename": "ai_guide.pdf",
                    "document_type": "pdf",
                    "upload_date": "2024-01-15T10:30:00Z",
                    "file_size": 2048576,
                    "sha256": "abc123def456",
                    "tags": ["AI", "ML", "tutorial"],
                    "categories": ["technology", "education"]
                }
            },
            {
                "id": "doc-002", 
                "content": "Guía completa sobre desarrollo web con Django y Python. Incluye mejores prácticas, patrones de diseño y optimización de rendimiento.",
                "metadata": {
                    "filename": "django_guide.pdf",
                    "document_type": "pdf", 
                    "upload_date": "2024-01-20T14:15:00Z",
                    "file_size": 1536000,
                    "sha256": "def456ghi789",
                    "tags": ["Django", "Python", "web"],
                    "categories": ["programming", "framework"]
                }
            },
            {
                "id": "doc-003",
                "content": "Manual de seguridad informática. Cubre temas como criptografía, autenticación, autorización y mejores prácticas de seguridad.",
                "metadata": {
                    "filename": "security_manual.pdf",
                    "document_type": "pdf",
                    "upload_date": "2024-02-01T09:45:00Z", 
                    "file_size": 3072000,
                    "sha256": "ghi789jkl012",
                    "tags": ["security", "cryptography", "authentication"],
                    "categories": ["security", "best-practices"]
                }
            },
            {
                "id": "doc-004",
                "content": "Análisis de datos con pandas y numpy. Tutorial paso a paso sobre manipulación, limpieza y visualización de datos.",
                "metadata": {
                    "filename": "data_analysis.pdf",
                    "document_type": "pdf",
                    "upload_date": "2024-02-10T16:20:00Z",
                    "file_size": 2560000,
                    "sha256": "jkl012mno345",
                    "tags": ["pandas", "numpy", "data-analysis"],
                    "categories": ["data-science", "python"]
                }
            },
            {
                "id": "doc-005",
                "content": "Arquitectura de microservicios. Diseño, implementación y despliegue de aplicaciones distribuidas y escalables.",
                "metadata": {
                    "filename": "microservices.pdf",
                    "document_type": "pdf",
                    "upload_date": "2024-02-15T11:30:00Z",
                    "file_size": 4096000,
                    "sha256": "mno345pqr678",
                    "tags": ["microservices", "architecture", "distributed"],
                    "categories": ["architecture", "design-patterns"]
                }
            }
        ]
        
        for doc_data in sample_docs:
            documents.append(MockSearchDocument(**doc_data))
            
        return documents
    
    def search(self, search_text: str, **kwargs) -> MockSearchResponse:
        """
        Realizar búsqueda mock.
        
        Args:
            search_text: Texto a buscar
            **kwargs: Argumentos adicionales (filters, top, skip, etc.)
            
        Returns:
            MockSearchResponse con resultados simulados
        """
        self._search_count += 1
        start_time = time.time()
        
        # Simular tiempo de búsqueda
        time.sleep(0.1)
        
        # Filtrar documentos basado en el texto de búsqueda
        results = []
        search_text_lower = search_text.lower()
        
        for doc in self._mock_documents:
            # Calcular score basado en coincidencias
            score = 0.0
            
            # Búsqueda en contenido
            if search_text_lower in doc.content.lower():
                score += 0.8
                
            # Búsqueda en metadata
            for key, value in doc.metadata.items():
                if isinstance(value, str) and search_text_lower in value.lower():
                    score += 0.2
                elif isinstance(value, list):
                    for item in value:
                        if search_text_lower in str(item).lower():
                            score += 0.1
            
            # Aplicar filtros si se especifican
            filters = kwargs.get('filters', '')
            if filters:
                # Simular filtrado básico
                if 'document_type' in filters and doc.metadata.get('document_type') not in filters:
                    continue
                if 'tags' in filters and not any(tag in doc.metadata.get('tags', []) for tag in filters):
                    continue
            
            if score > 0:
                # Crear highlights simulados
                highlights = []
                if search_text_lower in doc.content.lower():
                    start_idx = doc.content.lower().find(search_text_lower)
                    end_idx = start_idx + len(search_text)
                    highlights.append({
                        "text": doc.content[start_idx:end_idx],
                        "start": start_idx,
                        "end": end_idx
                    })
                
                results.append(MockSearchResult(
                    document=doc,
                    score=score,
                    highlights=highlights
                ))
        
        # Ordenar por score
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Aplicar límites
        top = kwargs.get('top', 10)
        skip = kwargs.get('skip', 0)
        results = results[skip:skip + top]
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        return MockSearchResponse(
            results=results,
            total_count=len(results),
            search_time_ms=search_time_ms,
            search_type=kwargs.get('search_type', 'hybrid'),
            query_processed=search_text,
            filters_applied=list(kwargs.get('filters', {}).keys())
        )
    
    def suggest(self, search_text: str, suggester_name: str = "sg", **kwargs) -> List[Dict[str, Any]]:
        """
        Realizar sugerencias mock.
        
        Args:
            search_text: Texto para sugerencias
            suggester_name: Nombre del suggester (ignorado en mock)
            **kwargs: Argumentos adicionales
            
        Returns:
            Lista de sugerencias simuladas
        """
        suggestions = []
        search_text_lower = search_text.lower()
        
        # Generar sugerencias basadas en el texto
        for doc in self._mock_documents:
            if search_text_lower in doc.content.lower():
                # Extraer frase que contenga el texto de búsqueda
                words = doc.content.split()
                for i, word in enumerate(words):
                    if search_text_lower in word.lower():
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        suggestion_text = " ".join(words[start:end])
                        
                        suggestions.append({
                            "text": suggestion_text,
                            "document_id": doc.id,
                            "score": 0.8
                        })
                        break
        
        return suggestions[:5]  # Limitar a 5 sugerencias
    
    def get_document(self, key: str) -> Optional[MockSearchDocument]:
        """
        Obtener documento por ID.
        
        Args:
            key: ID del documento
            
        Returns:
            MockSearchDocument o None si no se encuentra
        """
        for doc in self._mock_documents:
            if doc.id == key:
                return doc
        return None
    
    def get_document_count(self) -> int:
        """
        Obtener número total de documentos.
        
        Returns:
            Número de documentos en el índice
        """
        return len(self._mock_documents)


class MockSearchIndexClient:
    """Mock del cliente de índice de Azure AI Search."""
    
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """
        Inicializar mock del cliente de índice.
        
        Args:
            endpoint: Endpoint de Azure Search (ignorado en mock)
            api_key: API key (ignorado en mock)
        """
        self.endpoint = endpoint or "https://mock-search.search.windows.net"
        self.api_key = api_key or "mock-api-key"
        
    def get_index(self, index_name: str) -> Dict[str, Any]:
        """
        Obtener información del índice mock.
        
        Args:
            index_name: Nombre del índice
            
        Returns:
            Información del índice simulada
        """
        return {
            "name": index_name,
            "fields": [
                {
                    "name": "id",
                    "type": "Edm.String",
                    "key": True,
                    "searchable": False
                },
                {
                    "name": "content",
                    "type": "Edm.String",
                    "searchable": True,
                    "analyzer": "standard"
                },
                {
                    "name": "metadata",
                    "type": "Edm.String",
                    "searchable": True,
                    "filterable": True
                },
                {
                    "name": "vector",
                    "type": "Collection(Edm.Single)",
                    "searchable": False,
                    "dimensions": 1536
                }
            ],
            "suggesters": [
                {
                    "name": "sg",
                    "source_fields": ["content"]
                }
            ],
            "scoring_profiles": [
                {
                    "name": "default",
                    "text_weights": {
                        "weights": {
                            "content": 1.0,
                            "metadata": 0.5
                        }
                    }
                }
            ]
        }


# Funciones de conveniencia para testing
def create_mock_search_client() -> MockSearchClient:
    """
    Crear cliente mock de búsqueda.
    
    Returns:
        MockSearchClient configurado para testing
    """
    return MockSearchClient()


def create_mock_search_index_client() -> MockSearchIndexClient:
    """
    Crear cliente mock de índice de búsqueda.
    
    Returns:
        MockSearchIndexClient configurado para testing
    """
    return MockSearchIndexClient()


def create_mock_search_response(results: List[Dict[str, Any]]) -> MockSearchResponse:
    """
    Crear respuesta de búsqueda mock personalizada.
    
    Args:
        results: Lista de resultados en formato dict
        
    Returns:
        MockSearchResponse
    """
    mock_results = []
    for result in results:
        doc = MockSearchDocument(
            id=result.get('id', f"doc-{uuid.uuid4().hex[:8]}"),
            content=result.get('content', ''),
            metadata=result.get('metadata', {}),
            score=result.get('score', 1.0)
        )
        mock_results.append(MockSearchResult(
            document=doc,
            score=result.get('score', 1.0),
            highlights=result.get('highlights', [])
        ))
    
    return MockSearchResponse(
        results=mock_results,
        total_count=len(mock_results),
        search_time_ms=50,
        search_type='hybrid'
    )


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso del mock
    client = create_mock_search_client()
    
    # Probar búsqueda
    response = client.search(
        search_text="inteligencia artificial",
        top=5,
        search_type="hybrid"
    )
    print(f"Resultados encontrados: {len(response.results)}")
    
    for result in response.results:
        print(f"- {result.document.metadata.get('filename')}: {result.score}")
    
    # Probar sugerencias
    suggestions = client.suggest("django")
    print(f"Sugerencias: {len(suggestions)}")
    
    # Probar obtener documento
    doc = client.get_document("doc-001")
    if doc:
        print(f"Documento encontrado: {doc.metadata.get('filename')}")
