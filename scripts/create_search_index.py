"""
VEA Connect - Crear Índice de Búsqueda con Azure AI Studio
Script para crear índice de búsqueda usando AIProjectClient (como el ejemplo)
"""

import os
import json
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

def create_project_client():
    """Crear cliente de proyecto usando AI Studio"""
    try:
        # Crear cliente de proyecto usando connection string
        project = AIProjectClient.from_connection_string(
            conn_str=os.environ["AIPROJECT_CONNECTION_STRING"], 
            credential=DefaultAzureCredential()
        )
        logger.info("✅ Cliente de proyecto creado exitosamente")
        return project
    except Exception as e:
        logger.error(f"❌ Error al crear cliente de proyecto: {str(e)}")
        raise e

def get_search_connection(project):
    """Obtener conexión de búsqueda por defecto"""
    try:
        search_connection = project.connections.get_default(
            connection_type=ConnectionType.AZURE_AI_SEARCH, 
            include_credentials=True
        )
        logger.info("✅ Conexión de búsqueda obtenida exitosamente")
        return search_connection
    except Exception as e:
        logger.error(f"❌ Error al obtener conexión de búsqueda: {str(e)}")
        raise e

def create_index_definition(index_name: str, model: str = "text-embedding-ada-002") -> SearchIndex:
    """Crear definición del índice de búsqueda para VEA Connect"""
    
    # Dimensiones del vector según el modelo
    dimensions = 1536  # text-embedding-ada-002
    if model == "text-embedding-3-large":
        dimensions = 3072
    
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
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=dimensions,
            vector_search_profile_name="myHnswProfile",
        ),
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

    # Configuración de búsqueda vectorial
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="myHnsw",
                kind=VectorSearchAlgorithmKind.HNSW,
                parameters=HnswParameters(
                    m=4,
                    ef_construction=1000,
                    ef_search=1000,
                    metric=VectorSearchAlgorithmMetric.COSINE,
                ),
            ),
            ExhaustiveKnnAlgorithmConfiguration(
                name="myExhaustiveKnn",
                kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                parameters=ExhaustiveKnnParameters(metric=VectorSearchAlgorithmMetric.COSINE),
            ),
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
            ),
            VectorSearchProfile(
                name="myExhaustiveKnnProfile",
                algorithm_configuration_name="myExhaustiveKnn",
            ),
        ],
    )

    # Configuración de búsqueda semántica
    semantic_search = SemanticSearch(configurations=[semantic_config])

    # Crear definición del índice
    return SearchIndex(
        name=index_name,
        fields=fields,
        semantic_search=semantic_search,
        vector_search=vector_search,
    )

def create_index_from_config(index_name: str, project, search_connection):
    """Crear índice desde configuración JSON"""
    
    # Obtener cliente de índice
    index_client = SearchIndexClient(
        endpoint=search_connection.endpoint_url, 
        credential=AzureKeyCredential(key=search_connection.key)
    )
    
    # Eliminar índice existente si existe
    try:
        existing_index = index_client.get_index(index_name)
        index_client.delete_index(index_name)
        logger.info(f"🗑️  Índice existente '{index_name}' eliminado")
    except Exception:
        logger.info(f"ℹ️  No se encontró índice existente '{index_name}'")
    
    # Crear definición del índice
    index_definition = create_index_definition(index_name)
    
    # Crear el índice
    index_client.create_index(index_definition)
    logger.info(f"✅ Índice '{index_name}' creado exitosamente")
    
    return index_client

def create_datasource_from_config(project, search_connection):
    """Crear data source desde configuración JSON"""
    
    # Leer configuración del data source
    datasource_path = "../config/azure/vea-connect-datasource.json"
    if not os.path.exists(datasource_path):
        logger.error(f"❌ Archivo de configuración no encontrado: {datasource_path}")
        return False
    
    with open(datasource_path, 'r', encoding='utf-8') as f:
        datasource_config = json.load(f)
    
    # Crear data source usando el cliente de proyecto
    try:
        # Nota: La creación de data source puede requerir usar el SearchIndexClient directamente
        # ya que AIProjectClient puede no tener este método específico
        logger.info("📋 Data source debe crearse manualmente desde el portal de Azure")
        logger.info(f"   Nombre: {datasource_config['name']}")
        logger.info(f"   Tipo: {datasource_config['type']}")
        logger.info(f"   Contenedor: {datasource_config['container']['name']}")
        return True
    except Exception as e:
        logger.error(f"❌ Error al crear data source: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚀 VEA Connect - Crear Índice de Búsqueda con Azure AI Studio")
    print("=" * 60)
    
    try:
        # Verificar variables de entorno
        required_vars = ["AIPROJECT_CONNECTION_STRING", "AISEARCH_INDEX_NAME"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
            print("\n💡 Configura estas variables en tu archivo .env:")
            print("   AIPROJECT_CONNECTION_STRING=tu_connection_string")
            print("   AISEARCH_INDEX_NAME=vea-connect-index")
            return
        
        # Crear cliente de proyecto
        project = create_project_client()
        
        # Obtener conexión de búsqueda
        search_connection = get_search_connection(project)
        
        # Crear índice
        index_name = os.getenv("AISEARCH_INDEX_NAME")
        index_client = create_index_from_config(index_name, project, search_connection)
        
        # Crear data source
        create_datasource_from_config(project, search_connection)
        
        print("\n" + "=" * 60)
        print("🎉 ¡Índice creado exitosamente!")
        print(f"📋 Nombre del índice: {index_name}")
        print(f"🔍 Endpoint: {search_connection.endpoint_url}")
        print("\n📋 Próximos pasos:")
        print("1. Crear data source manualmente desde el portal de Azure")
        print("2. Crear skillset usando setup-azure-search.py")
        print("3. Crear indexer para conectar data source con índice")
        print("4. Subir documentos y ejecutar indexer")
        
    except Exception as e:
        logger.error(f"❌ Error general: {str(e)}")
        print(f"\n💡 Verifica tu configuración y vuelve a intentar")

if __name__ == "__main__":
    main()




