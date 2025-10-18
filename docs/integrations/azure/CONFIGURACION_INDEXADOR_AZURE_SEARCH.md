# Configuración del Indexador de Azure AI Search

## Resumen Ejecutivo

Este documento define la configuración completa del indexador `indexer-veaconnect-documents` para Azure AI Search, que indexa archivos JSON del contenedor `converted/` en Azure Blob Storage, mapeando correctamente las propiedades del JSON con los campos del índice de búsqueda.

## Estructura del JSON de Texto Extraído

### Propiedades del JSON almacenado en `converted/`
```json
{
  "original_file": "document.pdf",
  "extracted_text": "Texto extraído por Azure Computer Vision...",
  "extraction_date": "2024-01-15T10:30:00.000Z",
  "source": "azure_computer_vision",
  "text_length": 1250,
  "metadata": {
    "file_type": ".pdf",
    "original_filename": "document.pdf",
    "extraction_method": "azure_computer_vision",
    "user_id": 123
  }
}
```

## Configuración del Indexador

### 1. Data Source Configuration

```json
{
  "name": "veaconnect-documents-datasource",
  "type": "azureblob",
  "credentials": {
    "connectionString": "DefaultEndpointsProtocol=https;AccountName=veaconnectstr;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=core.windows.net"
  },
  "container": {
    "name": "documents",
    "query": "converted/*.json"
  },
  "dataDeletionDetectionPolicy": {
    "@odata.type": "#Microsoft.Azure.Search.SoftDeleteColumnDeletionDetectionPolicy",
    "softDeleteColumnName": "isDeleted",
    "softDeleteMarkerValue": "true"
  }
}
```

### 2. Index Schema Configuration

```json
{
  "name": "documents",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "searchable": false,
      "filterable": false,
      "sortable": false,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "document_id",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": true,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "text",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "sortable": false,
      "facetable": false,
      "retrievable": true,
      "analyzer": "standard.lucene"
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": true,
      "facetable": false,
      "retrievable": true,
      "analyzer": "standard.lucene"
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "sortable": false,
      "facetable": false,
      "retrievable": true,
      "analyzer": "standard.lucene"
    },
    {
      "name": "embedding",
      "type": "Collection(Edm.Single)",
      "searchable": false,
      "filterable": false,
      "sortable": false,
      "facetable": false,
      "retrievable": true,
      "vectorSearchDimensions": 1536,
      "vectorSearchProfile": "my-vector-config"
    },
    {
      "name": "metadata",
      "type": "Edm.String",
      "searchable": false,
      "filterable": false,
      "sortable": false,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "created_at",
      "type": "Edm.DateTimeOffset",
      "searchable": false,
      "filterable": true,
      "sortable": true,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "updated_at",
      "type": "Edm.DateTimeOffset",
      "searchable": false,
      "filterable": true,
      "sortable": true,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "source_type",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": true,
      "facetable": true,
      "retrievable": true
    },
    {
      "name": "filename",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": true,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "original_file",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": true,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "extraction_date",
      "type": "Edm.DateTimeOffset",
      "searchable": false,
      "filterable": true,
      "sortable": true,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "text_length",
      "type": "Edm.Int32",
      "searchable": false,
      "filterable": true,
      "sortable": true,
      "facetable": false,
      "retrievable": true
    },
    {
      "name": "file_type",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": true,
      "facetable": true,
      "retrievable": true
    },
    {
      "name": "extraction_method",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": true,
      "facetable": true,
      "retrievable": true
    }
  ],
  "vectorSearch": {
    "profiles": [
      {
        "name": "my-vector-config",
        "algorithmConfigurationName": "my-algorithms-config"
      }
    ],
    "algorithms": [
      {
        "name": "my-algorithms-config",
        "kind": "hnsw",
        "parameters": {
          "m": 4,
          "efConstruction": 400,
          "efSearch": 500,
          "metric": "cosine"
        }
      }
    ]
  },
  "semantic": {
    "configurations": [
      {
        "name": "default",
        "prioritizedFields": {
          "titleField": {
            "fieldName": "title"
          },
          "contentFields": [
            {
              "fieldName": "content"
            },
            {
              "fieldName": "text"
            }
          ],
          "keywordsFields": [
            {
              "fieldName": "source_type"
            },
            {
              "fieldName": "extraction_method"
            }
          ]
        }
      }
    ]
  }
}
```

### 3. Indexer Configuration

```json
{
  "name": "indexer-veaconnect-documents",
  "dataSourceName": "veaconnect-documents-datasource",
  "targetIndexName": "documents",
  "fieldMappings": [
    {
      "sourceFieldName": "original_file",
      "targetFieldName": "id"
    },
    {
      "sourceFieldName": "original_file",
      "targetFieldName": "document_id"
    },
    {
      "sourceFieldName": "extracted_text",
      "targetFieldName": "text"
    },
    {
      "sourceFieldName": "extracted_text",
      "targetFieldName": "content"
    },
    {
      "sourceFieldName": "original_file",
      "targetFieldName": "title"
    },
    {
      "sourceFieldName": "original_file",
      "targetFieldName": "filename"
    },
    {
      "sourceFieldName": "original_file",
      "targetFieldName": "original_file"
    },
    {
      "sourceFieldName": "extraction_date",
      "targetFieldName": "created_at"
    },
    {
      "sourceFieldName": "extraction_date",
      "targetFieldName": "updated_at"
    },
    {
      "sourceFieldName": "extraction_date",
      "targetFieldName": "extraction_date"
    },
    {
      "sourceFieldName": "source",
      "targetFieldName": "source_type"
    },
    {
      "sourceFieldName": "text_length",
      "targetFieldName": "text_length"
    },
    {
      "sourceFieldName": "metadata",
      "targetFieldName": "metadata"
    },
    {
      "sourceFieldName": "metadata/file_type",
      "targetFieldName": "file_type"
    },
    {
      "sourceFieldName": "metadata/extraction_method",
      "targetFieldName": "extraction_method"
    }
  ],
  "outputFieldMappings": [
    {
      "sourceFieldName": "/document/text",
      "targetFieldName": "title",
      "mappingFunction": {
        "name": "base64Encode"
      }
    }
  ],
  "parameters": {
    "configuration": {
      "dataToExtract": "contentAndMetadata",
      "parsingMode": "json",
      "imageAction": "none",
      "excludedFileNameExtensions": ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx",
      "indexedFileNameExtensions": ".json"
    }
  },
  "schedule": {
    "interval": "PT1H"
  },
  "disabled": false
}
```

## Mapeo de Propiedades JSON a Campos del Índice

### ✅ **Mapeo Correcto Implementado**

| Propiedad JSON | Campo Índice | Tipo | Descripción |
|----------------|--------------|------|-------------|
| `original_file` | `id` | String | Clave primaria del documento |
| `original_file` | `document_id` | String | Identificador del documento |
| `original_file` | `title` | String | Título basado en nombre del archivo |
| `original_file` | `filename` | String | Nombre del archivo original |
| `original_file` | `original_file` | String | Nombre del archivo original (duplicado para compatibilidad) |
| `extracted_text` | `text` | String | Texto extraído por Azure Computer Vision |
| `extracted_text` | `content` | String | Contenido para búsqueda semántica |
| `extraction_date` | `created_at` | DateTimeOffset | Fecha de extracción como fecha de creación |
| `extraction_date` | `updated_at` | DateTimeOffset | Fecha de extracción como fecha de actualización |
| `extraction_date` | `extraction_date` | DateTimeOffset | Fecha de extracción original |
| `source` | `source_type` | String | Tipo de fuente (azure_computer_vision) |
| `text_length` | `text_length` | Int32 | Longitud del texto extraído |
| `metadata` | `metadata` | String | Metadatos completos en formato JSON |
| `metadata.file_type` | `file_type` | String | Tipo de archivo (.pdf, .jpg, etc.) |
| `metadata.extraction_method` | `extraction_method` | String | Método de extracción usado |

### ⚠️ **Propiedades Sin Mapear**

| Propiedad JSON | Estado | Comentario |
|----------------|--------|------------|
| `metadata.original_filename` | ❌ Sin mapear | Duplicado de `original_file` |
| `metadata.user_id` | ❌ Sin mapear | ID del usuario que subió el archivo |
| `embedding` | ❌ Sin mapear | Vector de embedding (se genera posteriormente) |

## Configuración de Filtros

### Solo Archivos JSON en `converted/`
```json
"container": {
  "name": "documents",
  "query": "converted/*.json"
}
```

### Exclusión de Archivos No Deseados
```json
"excludedFileNameExtensions": ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx"
```

### Inclusión Solo de Archivos JSON
```json
"indexedFileNameExtensions": ".json"
```

## Configuración de Programación

### Indexación Automática
```json
"schedule": {
  "interval": "PT1H"
}
```

### Configuración de Parsing JSON
```json
"parsingMode": "json",
"dataToExtract": "contentAndMetadata"
```

## Comandos de Implementación

### 1. Crear Data Source
```bash
az search datasource create \
  --name veaconnect-documents-datasource \
  --type azureblob \
  --connection-string "DefaultEndpointsProtocol=https;AccountName=veaconnectstr;AccountKey=YOUR_KEY;EndpointSuffix=core.windows.net" \
  --container-name documents \
  --query "converted/*.json" \
  --resource-group YOUR_RESOURCE_GROUP \
  --service-name YOUR_SEARCH_SERVICE
```

### 2. Crear/Actualizar Índice
```bash
az search index create \
  --name documents \
  --resource-group YOUR_RESOURCE_GROUP \
  --service-name YOUR_SEARCH_SERVICE \
  --schema @index-schema.json
```

### 3. Crear Indexador
```bash
az search indexer create \
  --name indexer-veaconnect-documents \
  --data-source-name veaconnect-documents-datasource \
  --target-index-name documents \
  --resource-group YOUR_RESOURCE_GROUP \
  --service-name YOUR_SEARCH_SERVICE \
  --field-mappings @field-mappings.json \
  --parameters @indexer-parameters.json
```

### 4. Ejecutar Indexador
```bash
az search indexer run \
  --name indexer-veaconnect-documents \
  --resource-group YOUR_RESOURCE_GROUP \
  --service-name YOUR_SEARCH_SERVICE
```

## Monitoreo y Troubleshooting

### Verificar Estado del Indexador
```bash
az search indexer show \
  --name indexer-veaconnect-documents \
  --resource-group YOUR_RESOURCE_GROUP \
  --service-name YOUR_SEARCH_SERVICE
```

### Ver Logs del Indexador
```bash
az search indexer show-status \
  --name indexer-veaconnect-documents \
  --resource-group YOUR_RESOURCE_GROUP \
  --service-name YOUR_SEARCH_SERVICE
```

### Errores Comunes y Soluciones

#### 1. Error de Parsing JSON
**Problema**: `Error parsing JSON content`
**Solución**: Verificar que los archivos JSON en `converted/` sean válidos

#### 2. Error de Mapeo de Campos
**Problema**: `Field mapping error for field 'metadata/file_type'`
**Solución**: Verificar que la propiedad `metadata.file_type` exista en el JSON

#### 3. Error de Permisos
**Problema**: `Access denied to blob storage`
**Solución**: Verificar que la connection string tenga permisos de lectura

## Validación de la Configuración

### Script de Validación
```python
# scripts/validation/validate_indexer_config.py
import json
import requests
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

def validate_indexer_configuration():
    """
    Validate that the indexer is correctly mapping JSON properties to index fields.
    """
    # Configuration
    search_endpoint = "https://your-search-service.search.windows.net"
    search_key = "your-search-key"
    index_name = "documents"
    
    # Create search client
    credential = AzureKeyCredential(search_key)
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=credential
    )
    
    # Test search to verify field mapping
    results = search_client.search(
        search_text="azure_computer_vision",
        select=["id", "document_id", "text", "title", "content", "extraction_date", "source_type"],
        top=5
    )
    
    for result in results:
        print(f"Document ID: {result['id']}")
        print(f"Source Type: {result['source_type']}")
        print(f"Text Length: {len(result.get('text', ''))}")
        print(f"Extraction Date: {result.get('extraction_date')}")
        print("---")

if __name__ == "__main__":
    validate_indexer_configuration()
```

## Conclusión

La configuración del indexador `indexer-veaconnect-documents` está diseñada para:

1. ✅ **Indexar solo archivos JSON** del contenedor `converted/`
2. ✅ **Mapear correctamente** las propiedades del JSON a los campos del índice
3. ✅ **Soportar búsqueda vectorial** con embeddings de 1536 dimensiones
4. ✅ **Soportar búsqueda semántica** con configuración optimizada
5. ✅ **Incluir metadatos completos** para filtrado y faceting
6. ✅ **Programar indexación automática** cada hora

### Propiedades Sin Mapear (Comentadas en Código)
- `metadata.original_filename`: Duplicado de `original_file`
- `metadata.user_id`: ID del usuario (opcional para privacidad)
- `embedding`: Vector de embedding (se genera posteriormente por Azure OpenAI)

La configuración está lista para implementación y proporciona una base sólida para la búsqueda semántica y vectorial de documentos procesados por Azure Computer Vision. 