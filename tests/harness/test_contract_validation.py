"""
Tests de validación de contratos para el harness de testing.

Este módulo contiene tests que validan que los mocks cumplen con los
contratos I/O definidos en docs/api/contracts.md.
"""

import pytest
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# Importar mocks
from .mock_openai import create_mock_openai_client, create_mock_embedding, create_mock_chat_response
from .mock_search import create_mock_search_client, create_mock_search_response
from .mock_storage import create_mock_blob_service_client, create_mock_blob
from .mock_redis import create_mock_redis_client


class TestSearchContractValidation:
    """Tests para validar contratos de búsqueda/RAG."""
    
    def test_search_input_contract(self):
        """Validar estructura de input de búsqueda."""
        # Input válido según contrato
        valid_input = {
            "query": {
                "text": "inteligencia artificial",
                "filters": {
                    "document_type": ["pdf", "image"],
                    "date_range": {
                        "start": "2024-01-01T00:00:00Z",
                        "end": "2024-12-31T23:59:59Z"
                    },
                    "tags": ["AI", "ML"],
                    "categories": ["technology"]
                },
                "search_type": "hybrid",
                "top_k": 10,
                "include_metadata": True,
                "rerank": True
            },
            "context": {
                "user_id": "user123",
                "session_id": "session456",
                "preferences": {
                    "language": "es",
                    "max_results": 10
                }
            }
        }
        
        # Validar campos requeridos
        assert "query" in valid_input
        assert "text" in valid_input["query"]
        assert isinstance(valid_input["query"]["text"], str)
        assert len(valid_input["query"]["text"]) > 0
        
        # Validar tipos de datos
        assert isinstance(valid_input["query"]["top_k"], int)
        assert isinstance(valid_input["query"]["include_metadata"], bool)
        assert isinstance(valid_input["query"]["rerank"], bool)
        
        # Validar rangos
        assert 1 <= valid_input["query"]["top_k"] <= 100
        
        # Validar enums
        assert valid_input["query"]["search_type"] in ["hybrid", "semantic", "vector", "bm25"]
        assert valid_input["context"]["preferences"]["language"] in ["es", "en"]
    
    def test_search_output_contract(self):
        """Validar estructura de output de búsqueda."""
        search_client = create_mock_search_client()
        response = search_client.search("inteligencia artificial", top=5)
        
        # Validar estructura principal
        assert hasattr(response, 'results')
        assert hasattr(response, 'total_count')
        assert hasattr(response, 'search_time_ms')
        assert hasattr(response, 'search_type')
        assert hasattr(response, 'query_processed')
        assert hasattr(response, 'filters_applied')
        
        # Validar tipos
        assert isinstance(response.results, list)
        assert isinstance(response.total_count, int)
        assert isinstance(response.search_time_ms, int)
        assert isinstance(response.search_type, str)
        assert isinstance(response.query_processed, str)
        assert isinstance(response.filters_applied, list)
        
        # Validar rangos
        assert response.total_count >= 0
        assert response.search_time_ms >= 0
        
        # Validar resultados individuales
        for result in response.results:
            assert hasattr(result, 'document')
            assert hasattr(result, 'score')
            assert hasattr(result, 'highlights')
            
            # Validar documento
            doc = result.document
            assert hasattr(doc, 'id')
            assert hasattr(doc, 'content')
            assert hasattr(doc, 'metadata')
            
            assert isinstance(doc.id, str)
            assert isinstance(doc.content, str)
            assert isinstance(doc.metadata, dict)
            
            # Validar metadata del documento
            required_metadata = ['filename', 'document_type', 'upload_date', 'file_size', 'sha256']
            for field in required_metadata:
                assert field in doc.metadata
            
            # Validar score
            assert isinstance(result.score, float)
            assert 0.0 <= result.score <= 1.0
            
            # Validar highlights
            assert isinstance(result.highlights, list)
            for highlight in result.highlights:
                assert 'text' in highlight
                assert 'start' in highlight
                assert 'end' in highlight
                assert isinstance(highlight['text'], str)
                assert isinstance(highlight['start'], int)
                assert isinstance(highlight['end'], int)
    
    def test_search_suggestions_contract(self):
        """Validar estructura de sugerencias de búsqueda."""
        search_client = create_mock_search_client()
        suggestions = search_client.suggest("django")
        
        # Validar estructura
        assert isinstance(suggestions, list)
        
        for suggestion in suggestions:
            assert 'text' in suggestion
            assert 'document_id' in suggestion
            assert 'score' in suggestion
            
            assert isinstance(suggestion['text'], str)
            assert isinstance(suggestion['document_id'], str)
            assert isinstance(suggestion['score'], float)
            
            assert len(suggestion['text']) > 0
            assert 0.0 <= suggestion['score'] <= 1.0


class TestBotResponseContractValidation:
    """Tests para validar contratos de respuesta del bot."""
    
    def test_bot_input_contract(self):
        """Validar estructura de input del bot."""
        valid_input = {
            "message": {
                "text": "¿Qué es la inteligencia artificial?",
                "user_id": "user123",
                "session_id": "session456",
                "context": {
                    "previous_messages": [
                        {
                            "role": "user",
                            "content": "Hola",
                            "timestamp": "2024-01-01T00:00:00Z"
                        }
                    ],
                    "user_preferences": {
                        "language": "es",
                        "response_style": "detailed",
                        "include_sources": True
                    }
                }
            },
            "search_context": {
                "enable_search": True,
                "search_filters": {
                    "document_types": ["pdf", "image"],
                    "date_range": {
                        "start": "2024-01-01T00:00:00Z",
                        "end": "2024-12-31T23:59:59Z"
                    }
                }
            }
        }
        
        # Validar campos requeridos
        assert "message" in valid_input
        assert "text" in valid_input["message"]
        assert isinstance(valid_input["message"]["text"], str)
        assert len(valid_input["message"]["text"]) > 0
        
        # Validar enums
        assert valid_input["message"]["context"]["user_preferences"]["language"] in ["es", "en"]
        assert valid_input["message"]["context"]["user_preferences"]["response_style"] in ["concise", "detailed"]
    
    def test_bot_output_contract(self):
        """Validar estructura de output del bot."""
        openai_client = create_mock_openai_client()
        response = openai_client.chat().completions().create(
            messages=[{"role": "user", "content": "Hola, ¿cómo estás?"}],
            model="gpt-4"
        )
        
        # Validar estructura principal
        assert hasattr(response, 'choices')
        assert hasattr(response, 'usage')
        assert hasattr(response, 'model')
        
        # Validar tipos
        assert isinstance(response.choices, list)
        assert isinstance(response.usage, dict)
        assert isinstance(response.model, str)
        
        # Validar choices
        assert len(response.choices) > 0
        choice = response.choices[0]
        assert hasattr(choice, 'message')
        assert hasattr(choice, 'finish_reason')
        
        # Validar message
        message = choice.message
        assert hasattr(message, 'role')
        assert hasattr(message, 'content')
        assert isinstance(message.role, str)
        assert isinstance(message.content, str)
        assert message.role == "assistant"
        assert len(message.content) > 0
        
        # Validar usage
        required_usage_fields = ['prompt_tokens', 'completion_tokens', 'total_tokens']
        for field in required_usage_fields:
            assert field in response.usage
            assert isinstance(response.usage[field], int)
            assert response.usage[field] >= 0
    
    def test_bot_response_with_performance_contract(self):
        """Validar estructura de respuesta del bot con métricas de performance."""
        # Simular respuesta completa del bot
        bot_response = {
            "response": {
                "answer": "La inteligencia artificial es una rama de la informática...",
                "confidence": 0.95,
                "language": "es",
                "response_type": "search_enhanced",
                "suggested_actions": [
                    {
                        "action": "search_more",
                        "label": "Buscar más información",
                        "parameters": {}
                    }
                ]
            },
            "citations": [
                {
                    "source_id": "doc-001",
                    "source_title": "Guía de IA",
                    "source_type": "document",
                    "relevance_score": 0.95,
                    "extract": "La IA incluye machine learning...",
                    "page_number": 1,
                    "url": "https://example.com/doc"
                }
            ],
            "performance": {
                "used_cache": True,
                "cache_hit_type": "embedding",
                "latency_ms": 250,
                "tokens_used": {
                    "input": 100,
                    "output": 200,
                    "total": 300
                },
                "model_used": "gpt-4"
            },
            "search_metadata": {
                "search_performed": True,
                "documents_retrieved": 5,
                "search_time_ms": 150,
                "query_used": "inteligencia artificial"
            }
        }
        
        # Validar respuesta
        response = bot_response["response"]
        assert "answer" in response
        assert "confidence" in response
        assert "language" in response
        assert "response_type" in response
        
        assert isinstance(response["answer"], str)
        assert isinstance(response["confidence"], float)
        assert 0.0 <= response["confidence"] <= 1.0
        assert response["language"] in ["es", "en"]
        assert response["response_type"] in ["direct", "search_enhanced", "clarification"]
        
        # Validar citations
        citations = bot_response["citations"]
        assert isinstance(citations, list)
        for citation in citations:
            required_fields = ["source_id", "source_title", "source_type", "relevance_score"]
            for field in required_fields:
                assert field in citation
            
            assert isinstance(citation["relevance_score"], float)
            assert 0.0 <= citation["relevance_score"] <= 1.0
        
        # Validar performance
        performance = bot_response["performance"]
        assert "used_cache" in performance
        assert "latency_ms" in performance
        assert "tokens_used" in performance
        
        assert isinstance(performance["used_cache"], bool)
        assert isinstance(performance["latency_ms"], int)
        assert performance["latency_ms"] >= 0


class TestDownloadContractValidation:
    """Tests para validar contratos de descarga."""
    
    def test_download_input_contract(self):
        """Validar estructura de input de descarga."""
        valid_input = {
            "download_request": {
                "file_id": "file123",
                "user_id": "user456",
                "download_type": "direct",
                "format": "original",
                "include_metadata": True
            },
            "access_control": {
                "permissions": ["read", "download"],
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }
        
        # Validar campos requeridos
        assert "download_request" in valid_input
        assert "file_id" in valid_input["download_request"]
        assert isinstance(valid_input["download_request"]["file_id"], str)
        
        # Validar enums
        assert valid_input["download_request"]["download_type"] in ["direct", "stream", "sas_url"]
        assert valid_input["download_request"]["format"] in ["original", "pdf", "txt"]
    
    def test_download_stream_output_contract(self):
        """Validar estructura de output de descarga por stream."""
        storage_client = create_mock_blob_service_client()
        blob_client = storage_client.get_blob_client("vea-documents", "documents/ai_guide.pdf")
        
        # Simular respuesta de descarga por stream
        download_response = {
            "download": {
                "type": "stream",
                "content": "base64_encoded_content_here",
                "content_type": "application/pdf",
                "filename": "ai_guide.pdf",
                "file_size": 2048576,
                "checksum": {
                    "sha256": "abc123def456",
                    "md5": "md5hash123"
                }
            },
            "metadata": {
                "upload_date": "2024-01-15T10:30:00Z",
                "last_modified": "2024-01-15T10:30:00Z",
                "tags": ["AI", "ML"],
                "categories": ["technology"]
            }
        }
        
        # Validar estructura
        download = download_response["download"]
        assert "type" in download
        assert "content" in download
        assert "content_type" in download
        assert "filename" in download
        assert "file_size" in download
        
        assert download["type"] == "stream"
        assert isinstance(download["content"], str)
        assert isinstance(download["file_size"], int)
        assert download["file_size"] > 0
        
        # Validar checksum
        checksum = download["checksum"]
        assert "sha256" in checksum
        assert "md5" in checksum
        assert isinstance(checksum["sha256"], str)
        assert isinstance(checksum["md5"], str)
    
    def test_download_redirect_output_contract(self):
        """Validar estructura de output de descarga por redirect."""
        storage_client = create_mock_blob_service_client()
        blob_client = storage_client.get_blob_client("vea-documents", "documents/ai_guide.pdf")
        
        # Generar SAS token
        sas_token = blob_client.generate_sas(permission="r")
        
        # Simular respuesta de descarga por redirect
        download_response = {
            "download": {
                "type": "redirect_url",
                "url": f"https://storage.blob.core.windows.net/vea-documents/documents/ai_guide.pdf?{sas_token}",
                "expires_at": "2024-12-31T23:59:59Z",
                "content_type": "application/pdf",
                "filename": "ai_guide.pdf",
                "file_size": 2048576
            },
            "metadata": {
                "upload_date": "2024-01-15T10:30:00Z",
                "last_modified": "2024-01-15T10:30:00Z",
                "tags": ["AI", "ML"],
                "categories": ["technology"]
            }
        }
        
        # Validar estructura
        download = download_response["download"]
        assert "type" in download
        assert "url" in download
        assert "expires_at" in download
        assert "content_type" in download
        assert "filename" in download
        assert "file_size" in download
        
        assert download["type"] == "redirect_url"
        assert isinstance(download["url"], str)
        assert download["url"].startswith("https://")
        assert isinstance(download["file_size"], int)
        assert download["file_size"] > 0


class TestErrorContractValidation:
    """Tests para validar contratos de error."""
    
    def test_error_structure_contract(self):
        """Validar estructura de respuesta de error."""
        error_response = {
            "error": {
                "code": "NOT_FOUND",
                "message": "El recurso solicitado no fue encontrado",
                "details": "El archivo con ID 'file123' no existe en el sistema",
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "req-123456"
            }
        }
        
        # Validar estructura
        assert "error" in error_response
        error = error_response["error"]
        
        required_fields = ["code", "message", "details", "timestamp", "request_id"]
        for field in required_fields:
            assert field in error
            assert isinstance(error[field], str)
            assert len(error[field]) > 0
        
        # Validar códigos de error válidos
        valid_codes = [
            "INVALID_INPUT", "UNAUTHORIZED", "FORBIDDEN", "NOT_FOUND",
            "RATE_LIMITED", "INTERNAL_ERROR", "SERVICE_UNAVAILABLE",
            "SEARCH_ERROR", "EMBEDDING_ERROR", "STORAGE_ERROR"
        ]
        assert error["code"] in valid_codes


class TestMockIntegrationValidation:
    """Tests para validar integración entre mocks."""
    
    def test_openai_search_integration(self):
        """Validar integración entre OpenAI y Search mocks."""
        openai_client = create_mock_openai_client()
        search_client = create_mock_search_client()
        
        # Simular flujo completo: búsqueda + generación de respuesta
        query = "inteligencia artificial"
        
        # 1. Búsqueda
        search_response = search_client.search(query, top=3)
        assert len(search_response.results) > 0
        
        # 2. Generar respuesta con contexto de búsqueda
        context = " ".join([result.document.content[:100] for result in search_response.results])
        
        messages = [
            {"role": "user", "content": f"Basándote en esta información: {context}\n\nPregunta: {query}"}
        ]
        
        chat_response = openai_client.chat().completions().create(
            messages=messages,
            model="gpt-4"
        )
        
        # Validar que la respuesta es coherente
        assert len(chat_response.choices) > 0
        assert len(chat_response.choices[0].message.content) > 0
    
    def test_storage_redis_integration(self):
        """Validar integración entre Storage y Redis mocks."""
        storage_client = create_mock_blob_service_client()
        redis_client = create_mock_redis_client()
        
        # Simular flujo: obtener blob + cachear SAS token
        blob_path = "documents/ai_guide.pdf"
        
        # 1. Verificar si SAS token está cacheado
        cached_sas = redis_client.get_sas(blob_path)
        
        if cached_sas is None:
            # 2. Generar SAS token
            blob_client = storage_client.get_blob_client("vea-documents", blob_path)
            sas_token = blob_client.generate_sas(permission="r")
            
            # 3. Cachear SAS token
            success = redis_client.set_sas(blob_path, sas_token)
            assert success is True
            
            # 4. Verificar que se cacheó
            cached_sas = redis_client.get_sas(blob_path)
            assert cached_sas == sas_token
        
        # Validar que el SAS token es válido
        assert isinstance(cached_sas, str)
        assert "sv=" in cached_sas
        assert "sp=r" in cached_sas
    
    def test_search_redis_integration(self):
        """Validar integración entre Search y Redis mocks."""
        search_client = create_mock_search_client()
        redis_client = create_mock_redis_client()
        
        query = "machine learning"
        
        # 1. Verificar cache de búsqueda
        cached_response = redis_client.get_ans(query)
        
        if cached_response is None:
            # 2. Realizar búsqueda
            search_response = search_client.search(query, top=5)
            
            # 3. Convertir a formato cacheable
            cacheable_response = {
                "results": [
                    {
                        "id": result.document.id,
                        "content": result.document.content[:200],
                        "metadata": result.document.metadata,
                        "score": result.score
                    }
                    for result in search_response.results
                ],
                "total_count": search_response.total_count,
                "search_time_ms": search_response.search_time_ms
            }
            
            # 4. Cachear respuesta
            success = redis_client.set_ans(query, cacheable_response)
            assert success is True
            
            # 5. Verificar que se cacheó
            cached_response = redis_client.get_ans(query)
            assert cached_response is not None
            assert len(cached_response["results"]) == len(search_response.results)


class TestPerformanceValidation:
    """Tests para validar métricas de performance."""
    
    def test_search_performance_metrics(self):
        """Validar métricas de performance de búsqueda."""
        search_client = create_mock_search_client()
        
        start_time = time.time()
        response = search_client.search("test query", top=10)
        end_time = time.time()
        
        # Validar que search_time_ms es razonable
        actual_time_ms = int((end_time - start_time) * 1000)
        assert response.search_time_ms >= 0
        assert response.search_time_ms <= actual_time_ms + 100  # Margen de tolerancia
    
    def test_redis_performance_metrics(self):
        """Validar métricas de performance de Redis."""
        redis_client = create_mock_redis_client()
        
        # Llenar cache con datos
        for i in range(10):
            redis_client.set_emb(f"text_{i}", [0.1] * 1536)
            redis_client.set_ans(f"query_{i}", {"results": [], "total": 0})
        
        # Obtener estadísticas
        stats = redis_client.get_cache_stats()
        
        # Validar estadísticas
        assert "total_keys" in stats
        assert "namespaces" in stats
        assert "memory_usage" in stats
        
        assert stats["total_keys"] >= 20  # 10 embeddings + 10 queries
        assert "vea" in stats["namespaces"]
        assert stats["memory_usage"] > 0


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])
