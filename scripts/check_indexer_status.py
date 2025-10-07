"""
Script para verificar el estado del indexador
"""
import os
import sys
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexerClient

# Agregar backend al path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

load_dotenv()

endpoint = os.getenv('SEARCH_SERVICE_ENDPOINT')
key = os.getenv('SEARCH_SERVICE_KEY')
indexer_name = 'vea-connect-indexer'

client = SearchIndexerClient(endpoint, AzureKeyCredential(key))

# Obtener estado del indexador
status = client.get_indexer_status(indexer_name)

print(f"Estado del Indexer: {status.status}")
print(f"Última ejecución: {status.last_result.status if status.last_result else 'N/A'}")

if status.last_result:
    print(f"Items procesados: {getattr(status.last_result, 'items_processed', 'N/A')}")
    print(f"Items fallidos: {getattr(status.last_result, 'items_failed', 'N/A')}")
    
    if hasattr(status.last_result, 'errors') and status.last_result.errors:
        print("\nErrores:")
        for error in status.last_result.errors:
            print(f"  - {error}")

# Verificar documentos en el índice
from azure.search.documents import SearchClient

search_client = SearchClient(
    endpoint=endpoint,
    index_name=os.getenv('SEARCH_INDEX_NAME'),
    credential=AzureKeyCredential(key)
)

results = search_client.search("*", select=["metadata_storage_name"], top=10)
count = 0
print("\nDocumentos en el índice:")
for result in results:
    print(f"  - {result.get('metadata_storage_name', 'Sin nombre')}")
    count += 1

if count == 0:
    print("  ¡El índice está vacío!")
else:
    print(f"\nTotal de documentos encontrados: {count}")

