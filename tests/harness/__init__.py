"""
Harness de testing para VEA Connect.

Este paquete proporciona mocks puros y tests de validación de contratos
para testing aislado sin dependencias de Django.
"""

from .mock_openai import (
    create_mock_openai_client,
    create_mock_embedding,
    create_mock_chat_response,
    MockOpenAI,
    MockEmbeddingResponse,
    MockChatResponse
)

from .mock_search import (
    create_mock_search_client,
    create_mock_search_index_client,
    create_mock_search_response,
    MockSearchClient,
    MockSearchResponse
)

from .mock_storage import (
    create_mock_blob_service_client,
    create_mock_container_client,
    create_mock_blob_client,
    create_mock_blob,
    MockBlobServiceClient,
    MockBlob
)

from .mock_redis import (
    create_mock_redis_client,
    create_mock_redis_with_data,
    create_mock_redis_unavailable,
    create_mock_redis_with_timeouts,
    MockRedis
)

__version__ = "1.0.0"
__author__ = "VEA Connect Team"

__all__ = [
    # OpenAI mocks
    "create_mock_openai_client",
    "create_mock_embedding", 
    "create_mock_chat_response",
    "MockOpenAI",
    "MockEmbeddingResponse",
    "MockChatResponse",
    
    # Search mocks
    "create_mock_search_client",
    "create_mock_search_index_client",
    "create_mock_search_response",
    "MockSearchClient",
    "MockSearchResponse",
    
    # Storage mocks
    "create_mock_blob_service_client",
    "create_mock_container_client",
    "create_mock_blob_client",
    "create_mock_blob",
    "MockBlobServiceClient",
    "MockBlob",
    
    # Redis mocks
    "create_mock_redis_client",
    "create_mock_redis_with_data",
    "create_mock_redis_unavailable",
    "create_mock_redis_with_timeouts",
    "MockRedis"
]
