"""
Hybrid Search Canary Script - VEA Connect

This script demonstrates hybrid search (BM25 + vector) without calling actual services.
It shows how the hybrid search would be constructed and executed.
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridSearchCanary:
    """
    Canary implementation of hybrid search (BM25 + vector).
    
    This class demonstrates how hybrid search would be implemented
    without actually calling the search services.
    """
    
    def __init__(self):
        """Initialize the hybrid search canary."""
        self.search_service_available = self._check_search_service()
        self.embedding_service_available = self._check_embedding_service()
        self.vision_service_available = self._check_vision_service()
        
        # Configuration
        self.default_top_k = 10
        self.bm25_weight = 0.3
        self.vector_weight = 0.7
        self.rerank_enabled = True
        
        # Mock data for demonstration
        self.mock_documents = self._create_mock_documents()
    
    def _check_search_service(self) -> bool:
        """Check if Azure AI Search service is available."""
        required_vars = [
            'AZURE_SEARCH_ENDPOINT',
            'AZURE_SEARCH_API_KEY',
            'AZURE_SEARCH_INDEX_NAME'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Search service not available. Missing variables: {missing_vars}")
            return False
        
        logger.info("✅ Azure AI Search service configuration found")
        return True
    
    def _check_embedding_service(self) -> bool:
        """Check if embedding service is available."""
        required_vars = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Embedding service not available. Missing variables: {missing_vars}")
            return False
        
        logger.info("✅ Azure OpenAI embedding service configuration found")
        return True
    
    def _check_vision_service(self) -> bool:
        """Check if vision service is available."""
        required_vars = [
            'VISION_ENDPOINT',
            'VISION_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Vision service not available. Missing variables: {missing_vars}")
            return False
        
        logger.info("✅ Azure Vision service configuration found")
        return True
    
    def _create_mock_documents(self) -> List[Dict[str, Any]]:
        """Create mock documents for demonstration."""
        return [
            {
                'id': 'doc_001',
                'title': 'Documento de Donaciones Ministeriales',
                'content': 'Este documento describe los procesos de donaciones para ministerios gubernamentales. Incluye información sobre requisitos, procedimientos y contactos.',
                'metadata': {
                    'filename': 'donaciones_ministeriales.pdf',
                    'source_type': 'canary_test',
                    'created_at': '2024-01-15T10:30:00Z'
                },
                'bm25_score': 0.85,
                'vector_score': 0.92
            },
            {
                'id': 'doc_002',
                'title': 'Guía de Eventos Comunitarios',
                'content': 'Guía completa para la organización de eventos comunitarios. Contiene checklists, presupuestos y mejores prácticas.',
                'metadata': {
                    'filename': 'eventos_comunitarios.pdf',
                    'source_type': 'canary_test',
                    'created_at': '2024-01-16T14:20:00Z'
                },
                'bm25_score': 0.72,
                'vector_score': 0.78
            },
            {
                'id': 'doc_003',
                'title': 'Manual de Contactos de Emergencia',
                'content': 'Lista completa de contactos de emergencia para diferentes situaciones. Incluye números de teléfono y protocolos.',
                'metadata': {
                    'filename': 'contactos_emergencia.pdf',
                    'source_type': 'canary_test',
                    'created_at': '2024-01-17T09:15:00Z'
                },
                'bm25_score': 0.68,
                'vector_score': 0.65
            }
        ]
    
    def build_hybrid_query(self, query_text: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Build a hybrid search query (BM25 + vector).
        
        Args:
            query_text: The search query
            filters: Optional filters to apply
            
        Returns:
            Dictionary containing the hybrid query structure
        """
        # Generate query embedding (mock)
        query_embedding = self._generate_mock_embedding(query_text)
        
        # Build BM25 query
        bm25_query = self._build_bm25_query(query_text, filters)
        
        # Build vector query
        vector_query = self._build_vector_query(query_embedding, filters)
        
        # Combine into hybrid query
        hybrid_query = {
            'query_type': 'hybrid',
            'search_text': query_text,
            'query_embedding': query_embedding,
            'bm25_query': bm25_query,
            'vector_query': vector_query,
            'weights': {
                'bm25': self.bm25_weight,
                'vector': self.vector_weight
            },
            'filters': filters or {},
            'rerank': self.rerank_enabled,
            'top_k': self.default_top_k
        }
        
        return hybrid_query
    
    def _build_bm25_query(self, query_text: str, filters: Optional[Dict]) -> Dict[str, Any]:
        """Build BM25 text search query."""
        bm25_query = {
            'type': 'full',
            'search': query_text,
            'searchMode': 'all',
            'queryType': 'full',
            'searchFields': ['title', 'content'],
            'select': ['id', 'title', 'content', 'metadata'],
            'top': self.default_top_k,
            'orderBy': ['@search.score desc']
        }
        
        if filters:
            bm25_query['filter'] = self._build_filter_string(filters)
        
        return bm25_query
    
    def _build_vector_query(self, query_embedding: List[float], filters: Optional[Dict]) -> Dict[str, Any]:
        """Build vector similarity search query."""
        vector_query = {
            'type': 'vector',
            'vector': query_embedding,
            'fields': ['embedding'],
            'k': self.default_top_k,
            'select': ['id', 'title', 'content', 'metadata'],
            'orderBy': ['@search.score desc']
        }
        
        if filters:
            vector_query['filter'] = self._build_filter_string(filters)
        
        return vector_query
    
    def _build_filter_string(self, filters: Dict) -> str:
        """Build filter string for Azure Search."""
        filter_parts = []
        
        for key, value in filters.items():
            if isinstance(value, str):
                filter_parts.append(f"{key} eq '{value}'")
            elif isinstance(value, (int, float)):
                filter_parts.append(f"{key} eq {value}")
            elif isinstance(value, list):
                filter_parts.append(f"{key} in ({','.join([f\"'{v}'\" for v in value])})")
        
        return ' and '.join(filter_parts) if filter_parts else None
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding for demonstration."""
        # Use hash of text to generate consistent mock embedding
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Generate 1536-dimensional mock embedding
        import random
        random.seed(int(text_hash[:8], 16))
        embedding = [random.uniform(-1, 1) for _ in range(1536)]
        
        # Normalize to unit vector
        magnitude = sum(x*x for x in embedding) ** 0.5
        return [x/magnitude for x in embedding]
    
    def execute_hybrid_search(self, query_text: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute hybrid search (demonstration only).
        
        Args:
            query_text: The search query
            filters: Optional filters to apply
            
        Returns:
            Dictionary containing search results and metadata
        """
        print(f"\n🔍 Executing Hybrid Search for: '{query_text}'")
        print("=" * 60)
        
        # Build hybrid query
        hybrid_query = self.build_hybrid_query(query_text, filters)
        
        # Show query structure
        print("📋 Hybrid Query Structure:")
        print(json.dumps(hybrid_query, indent=2, default=str))
        
        # Check service availability
        if not self.search_service_available:
            print("\n⚠️ Search service not available - showing mock results")
            return self._get_mock_results(query_text, hybrid_query)
        
        if not self.embedding_service_available:
            print("\n⚠️ Embedding service not available - using BM25 only")
            return self._get_bm25_only_results(query_text, hybrid_query)
        
        # Show how the search would be executed
        print("\n🚀 How the search would be executed:")
        print("1. Generate query embedding using Azure OpenAI")
        print("2. Execute BM25 search in Azure AI Search")
        print("3. Execute vector similarity search in Azure AI Search")
        print("4. Combine and rerank results")
        print("5. Return hybrid results")
        
        return self._get_mock_results(query_text, hybrid_query)
    
    def _get_mock_results(self, query_text: str, hybrid_query: Dict) -> Dict[str, Any]:
        """Get mock search results."""
        # Simulate search execution
        results = []
        
        for doc in self.mock_documents:
            # Calculate hybrid score
            hybrid_score = (
                doc['bm25_score'] * hybrid_query['weights']['bm25'] +
                doc['vector_score'] * hybrid_query['weights']['vector']
            )
            
            # Add some relevance based on query
            if any(word.lower() in doc['content'].lower() for word in query_text.split()):
                hybrid_score *= 1.2
            
            results.append({
                'id': doc['id'],
                'title': doc['title'],
                'content': doc['content'][:200] + "...",
                'metadata': doc['metadata'],
                'scores': {
                    'bm25': doc['bm25_score'],
                    'vector': doc['vector_score'],
                    'hybrid': round(hybrid_score, 3)
                }
            })
        
        # Sort by hybrid score
        results.sort(key=lambda x: x['scores']['hybrid'], reverse=True)
        
        return {
            'query': query_text,
            'query_type': 'hybrid',
            'total_results': len(results),
            'results': results[:hybrid_query['top_k']],
            'execution_info': {
                'services_used': ['bm25', 'vector'],
                'weights_applied': hybrid_query['weights'],
                'rerank_enabled': hybrid_query['rerank']
            }
        }
    
    def _get_bm25_only_results(self, query_text: str, hybrid_query: Dict) -> Dict[str, Any]:
        """Get BM25-only search results."""
        results = []
        
        for doc in self.mock_documents:
            # Use only BM25 score
            results.append({
                'id': doc['id'],
                'title': doc['title'],
                'content': doc['content'][:200] + "...",
                'metadata': doc['metadata'],
                'scores': {
                    'bm25': doc['bm25_score'],
                    'vector': 0.0,
                    'hybrid': doc['bm25_score']
                }
            })
        
        # Sort by BM25 score
        results.sort(key=lambda x: x['scores']['bm25'], reverse=True)
        
        return {
            'query': query_text,
            'query_type': 'bm25_only',
            'total_results': len(results),
            'results': results[:hybrid_query['top_k']],
            'execution_info': {
                'services_used': ['bm25'],
                'weights_applied': {'bm25': 1.0, 'vector': 0.0},
                'rerank_enabled': False
            }
        }
    
    def show_service_status(self):
        """Show status of all required services."""
        print("\n🔧 Service Status:")
        print("=" * 40)
        print(f"Azure AI Search: {'✅ Available' if self.search_service_available else '❌ Not Available'}")
        print(f"Azure OpenAI: {'✅ Available' if self.embedding_service_available else '❌ Not Available'}")
        print(f"Azure Vision: {'✅ Available' if self.vision_service_available else '❌ Not Available'}")
        
        if not any([self.search_service_available, self.embedding_service_available, self.vision_service_available]):
            print("\n⚠️ No services available. Set required environment variables:")
            print("   AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_SEARCH_INDEX_NAME")
            print("   AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY")
            print("   VISION_ENDPOINT, VISION_KEY")
    
    def demonstrate_search_scenarios(self):
        """Demonstrate different search scenarios."""
        scenarios = [
            {
                'name': 'Donaciones Ministeriales',
                'query': 'donaciones ministerios gobierno',
                'filters': {'source_type': 'canary_test'}
            },
            {
                'name': 'Eventos Comunitarios',
                'query': 'eventos comunitarios organización',
                'filters': None
            },
            {
                'name': 'Contactos de Emergencia',
                'query': 'emergencia teléfono contacto',
                'filters': {'metadata/filename': 'contactos_emergencia.pdf'}
            }
        ]
        
        print("\n🧪 Search Scenarios Demonstration:")
        print("=" * 60)
        
        for scenario in scenarios:
            print(f"\n📝 Scenario: {scenario['name']}")
            print(f"Query: '{scenario['query']}'")
            if scenario['filters']:
                print(f"Filters: {scenario['filters']}")
            
            results = self.execute_hybrid_search(scenario['query'], scenario['filters'])
            
            print(f"\nResults ({len(results['results'])} found):")
            for i, result in enumerate(results['results'], 1):
                print(f"  {i}. {result['title']} (Score: {result['scores']['hybrid']})")
                print(f"     {result['content']}")
            
            print("-" * 40)


def main():
    """Main function to run the hybrid search canary."""
    print("🚀 Hybrid Search Canary - VEA Connect")
    print("=" * 60)
    
    # Initialize canary
    canary = HybridSearchCanary()
    
    # Show service status
    canary.show_service_status()
    
    # Demonstrate search scenarios
    canary.demonstrate_search_scenarios()
    
    print("\n🏁 Hybrid Search Canary demonstration completed")
    print("\n💡 To enable actual search:")
    print("   1. Set required environment variables")
    print("   2. Configure Azure AI Search index")
    print("   3. Set CANARY_INGEST_ENABLED=True")
    print("   4. Run with actual services")


if __name__ == "__main__":
    main()

