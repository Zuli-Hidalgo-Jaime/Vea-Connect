"""
VEA Connect - Configuración Completa
Script principal para configurar VEA Connect usando Azure AI Studio
"""

import os
import sys
import json
import time
import requests
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SemanticSearch,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    HnswParameters,
    VectorSearchAlgorithmMetric,
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    VectorSearchProfile,
)
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_logger(name):
    """Logger simple para el script"""
    import logging
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)

logger = get_logger(__name__)

def check_environment():
    """Verificar variables de entorno"""
    print("🔧 Verificando configuración...")
    
    # Variables requeridas para Azure AI Studio
    ai_studio_vars = ["AIPROJECT_CONNECTION_STRING", "AISEARCH_INDEX_NAME"]
    
    # Variables requeridas para método tradicional
    traditional_vars = ["SEARCH_SERVICE_ENDPOINT", "SEARCH_SERVICE_KEY"]
    
    # Verificar si tenemos configuración de AI Studio
    has_ai_studio = all(os.getenv(var) for var in ai_studio_vars)
    has_traditional = all(os.getenv(var) for var in traditional_vars)
    
    if has_ai_studio:
        print("✅ Configuración de Azure AI Studio encontrada")
        return "ai_studio"
    elif has_traditional:
        print("✅ Configuración tradicional de Azure AI Search encontrada")
        return "traditional"
    else:
        print("❌ Configuración incompleta")
        print("💡 Configura al menos una de estas opciones:")
        print("   - Azure AI Studio: AIPROJECT_CONNECTION_STRING, AISEARCH_INDEX_NAME")
        print("   - Tradicional: SEARCH_SERVICE_ENDPOINT, SEARCH_SERVICE_KEY")
        return None

def create_index_ai_studio():
    """Crear índice usando Azure AI Studio"""
    print("🚀 Creando índice con Azure AI Studio...")
    
    try:
        # Crear cliente de proyecto
        project = AIProjectClient.from_connection_string(
            conn_str=os.environ["AIPROJECT_CONNECTION_STRING"], 
            credential=DefaultAzureCredential()
        )
        
        # Obtener conexión de búsqueda
        search_connection = project.connections.get_default(
            connection_type=ConnectionType.AZURE_AI_SEARCH, 
            include_credentials=True
        )
        
        # Crear cliente de índice
        index_client = SearchIndexClient(
            endpoint=search_connection.endpoint_url, 
            credential=AzureKeyCredential(key=search_connection.key)
        )
        
        # Crear definición del índice
        index_name = os.environ["AISEARCH_INDEX_NAME"]
        index_definition = create_index_definition_vea_connect(index_name)
        
        # Eliminar índice existente si existe
        try:
            existing_index = index_client.get_index(index_name)
            index_client.delete_index(index_name)
            logger.info(f"🗑️  Índice existente '{index_name}' eliminado")
        except Exception:
            logger.info(f"ℹ️  No se encontró índice existente '{index_name}'")
        
        # Crear el índice
        index_client.create_index(index_definition)
        logger.info(f"✅ Índice '{index_name}' creado exitosamente")
        
        return True, search_connection.endpoint_url, search_connection.key
        
    except Exception as e:
        logger.error(f"❌ Error al crear índice con AI Studio: {str(e)}")
        return False, None, None

def create_index_traditional():
    """Crear índice usando método tradicional"""
    print("🚀 Creando índice con método tradicional...")
    
    try:
        # Crear cliente de índice
        index_client = SearchIndexClient(
            endpoint=os.environ["SEARCH_SERVICE_ENDPOINT"], 
            credential=AzureKeyCredential(os.environ["SEARCH_SERVICE_KEY"])
        )
        
        # Crear definición del índice
        index_name = os.environ["SEARCH_INDEX_NAME"]
        index_definition = create_index_definition_vea_connect(index_name)
        
        # Eliminar índice existente si existe
        try:
            existing_index = index_client.get_index(index_name)
            index_client.delete_index(index_name)
            logger.info(f"🗑️  Índice existente '{index_name}' eliminado")
        except Exception:
            logger.info(f"ℹ️  No se encontró índice existente '{index_name}'")
        
        # Crear el índice
        index_client.create_index(index_definition)
        logger.info(f"✅ Índice '{index_name}' creado exitosamente")
        
        return True, os.environ["SEARCH_SERVICE_ENDPOINT"], os.environ["SEARCH_SERVICE_KEY"]
        
    except Exception as e:
        logger.error(f"❌ Error al crear índice tradicional: {str(e)}")
        return False, None, None

def create_index_definition_vea_connect(index_name: str) -> SearchIndex:
    """Crear definición del índice para VEA Connect"""
    
    # Campos del índice adaptados para VEA Connect
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="merged_content", type=SearchFieldDataType.String),
        SimpleField(name="filepath", type=SearchFieldDataType.String),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SimpleField(name="url", type=SearchFieldDataType.String),
        SimpleField(name="metadata_storage_name", type=SearchFieldDataType.String),
        SimpleField(name="metadata_storage_path", type=SearchFieldDataType.String),
        SimpleField(name="metadata_storage_size", type=SearchFieldDataType.Int64),
        SimpleField(name="metadata_storage_last_modified", type=SearchFieldDataType.DateTimeOffset),
        SimpleField(name="language", type=SearchFieldDataType.String),
        SimpleField(name="document_type", type=SearchFieldDataType.String),
        SimpleField(name="category", type=SearchFieldDataType.String),
        SearchableField(name="keyphrases", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
        SearchableField(name="locations", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
        SearchableField(name="imageTags", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
        SearchableField(name="imageCaption", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
        SearchableField(name="text", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
        SearchableField(name="layoutText", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
    ]

    # Configuración semántica para VEA Connect
    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            keywords_fields=[SemanticField(field_name="keyphrases")],
            content_fields=[
                SemanticField(field_name="content"),
                SemanticField(field_name="merged_content")
            ],
        ),
    )

    # Configuración de búsqueda semántica
    semantic_search = SemanticSearch(configurations=[semantic_config])

    # Crear definición del índice
    return SearchIndex(
        name=index_name,
        fields=fields,
        semantic_search=semantic_search,
    )

def configure_search_resources(search_endpoint, search_key):
    """Configurar skillset e indexer usando archivos JSON"""
    print("🔧 Configurando skillset e indexer...")
    
    # Configurar skillset
    if not configure_skillset(search_endpoint, search_key):
        return False
    
    # Configurar indexer
    if not configure_indexer(search_endpoint, search_key):
        return False
    
    return True

def configure_skillset(search_endpoint, search_key):
    """Configurar skillset"""
    print("📋 Configurando skillset...")
    
    try:
        # Leer archivo JSON
        skillset_path = "../config/azure/vea-connect-skillset.json"
        if not os.path.exists(skillset_path):
            print(f"❌ Archivo no encontrado: {skillset_path}")
            return False
        
        with open(skillset_path, 'r', encoding='utf-8') as f:
            skillset_data = f.read()
        
        # URL y headers
        url = f"{search_endpoint}/skillsets/vea-connect-skillset?api-version=2023-11-01"
        headers = {
            "Content-Type": "application/json",
            "api-key": search_key
        }
        
        # Realizar petición
        response = requests.put(url, headers=headers, data=skillset_data)
        
        if response.status_code in [200, 201, 204]:
            print("✅ Skillset configurado exitosamente")
            return True
        else:
            print(f"❌ Error al configurar skillset: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error al configurar skillset: {str(e)}")
        return False

def configure_indexer(search_endpoint, search_key):
    """Configurar indexer"""
    print("📋 Configurando indexer...")
    
    try:
        # Leer archivo JSON
        indexer_path = "../config/azure/vea-connect-indexer.json"
        if not os.path.exists(indexer_path):
            print(f"❌ Archivo no encontrado: {indexer_path}")
            return False
        
        with open(indexer_path, 'r', encoding='utf-8') as f:
            indexer_data = f.read()
        
        # URL y headers
        url = f"{search_endpoint}/indexers/vea-connect-indexer?api-version=2023-11-01"
        headers = {
            "Content-Type": "application/json",
            "api-key": search_key
        }
        
        # Realizar petición
        response = requests.put(url, headers=headers, data=indexer_data)
        
        if response.status_code in [200, 201, 204]:
            print("✅ Indexer configurado exitosamente")
            return True
        else:
            print(f"❌ Error al configurar indexer: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error al configurar indexer: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚀 VEA Connect - Configuración Completa")
    print("=" * 50)
    
    # Verificar configuración
    config_type = check_environment()
    if not config_type:
        return
    
    # Crear índice
    if config_type == "ai_studio":
        success, search_endpoint, search_key = create_index_ai_studio()
    else:
        success, search_endpoint, search_key = create_index_traditional()
    
    if not success:
        print("❌ Error al crear índice")
        return
    
    # Configurar recursos de búsqueda
    if not configure_search_resources(search_endpoint, search_key):
        print("❌ Error al configurar recursos de búsqueda")
        return
    
    print("\n" + "=" * 50)
    print("🎉 ¡Configuración completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Crear data source manualmente desde el portal de Azure")
    print("2. Subir documentos al contenedor de Azure Storage")
    print("3. Ejecutar el indexer para procesar documentos")
    print("4. Probar la búsqueda")

if __name__ == "__main__":
    main()




