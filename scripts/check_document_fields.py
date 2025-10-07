"""
Script para verificar los campos de los documentos indexados
"""
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

endpoint = os.getenv('SEARCH_SERVICE_ENDPOINT')
key = os.getenv('SEARCH_SERVICE_KEY')
index_name = os.getenv('SEARCH_INDEX_NAME')

search_client = SearchClient(
    endpoint=endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(key)
)

# Buscar todos los documentos
results = search_client.search(
    "*",
    select=["metadata_storage_name", "category", "merged_content", "content", "keyphrases"],
    top=5
)

print("Documentos en el índice:")
print("=" * 60)

for i, doc in enumerate(results, 1):
    print(f"\n{i}. {doc.get('metadata_storage_name', 'Sin nombre')}")
    print(f"   Categoría: {doc.get('category', 'SIN CATEGORÍA')}")
    print(f"   Contenido: {doc.get('merged_content', doc.get('content', 'Sin contenido'))[:150]}...")
    print(f"   Frases clave: {doc.get('keyphrases', [])[:5]}")

