#!/usr/bin/env python
"""
Script para verificar el contenido del índice de Azure Search en producción.
"""
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Cargar .env
try:
    from dotenv import load_dotenv
    load_dotenv('./.env')
except:
    pass

import django
django.setup()

from utilities.embedding_manager import EmbeddingManager
from utilities.azure_search_client import get_azure_search_client

def check_index():
    try:
        # Obtener cliente de búsqueda
        client = get_azure_search_client()
        em = EmbeddingManager(search_client=client)
        
        print("=== Verificando contenido del índice ===\n")
        
        # Buscar documentos similares a algunas preguntas comunes
        test_queries = [
            "¿Cómo puedo donar?",
            "¿Dónde están ubicados?",
            "Información general",
            "Contacto",
            "Eventos"
        ]
        
        for query in test_queries:
            print(f"\n--- Query: '{query}' ---")
            try:
                results = em.find_similar(query, top_k=3, threshold=0.0)
                if results:
                    for i, r in enumerate(results, 1):
                        content = r.get('text', r.get('content', 'Sin contenido'))
                        print(f"\n[{i}] Score: {r.get('score', 'N/A')}")
                        print(f"Contenido: {content[:200]}...")
                else:
                    print("  → No se encontraron resultados")
            except Exception as e:
                print(f"  → Error: {e}")
        
        # Intentar listar todos los documentos del índice
        print("\n\n=== Intentando listar documentos del índice ===")
        try:
            # Usar search_semantic con query vacía para obtener todos
            all_docs = client.search_semantic("*", top_k=10)
            if all_docs:
                print(f"\nTotal de documentos encontrados: {len(all_docs)}")
                for i, doc in enumerate(all_docs[:5], 1):
                    content = doc.get('text', doc.get('content', 'Sin contenido'))
                    print(f"\n[{i}] Contenido: {content[:200]}...")
            else:
                print("  → No se encontraron documentos")
        except Exception as e:
            print(f"  → Error al listar documentos: {e}")
            
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_index()



