# VEA Documents System Architecture

## Overview

El sistema de documentos de VEA Connect ha sido completamente refactorizado para proporcionar un flujo CRUD coherente, transaccional y trazable entre Azure Blob Storage, PostgreSQL y Azure AI Search.

## Architecture Components

### 1. Storage Layer (Azure Blob Storage)

**Service**: `services/storage_service.py`
- **DocumentStorageService**: Maneja todas las operaciones de almacenamiento
- **Métodos principales**:
  - `upload()`: Sube archivos con nombres únicos
  - `download_url()`: Genera URLs SAS temporales (72 horas)
  - `delete()`: Elimina archivos del contenedor
  - `exists()`: Verifica existencia de archivos
  - `download_to_tempfile()`: Descarga para procesamiento

**Configuración**:
```python
DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
AZURE_OVERWRITE_FILES = False
AZURE_URL_EXPIRATION_SECONDS = 259200  # 72 horas
```

### 2. Database Layer (PostgreSQL)

**Models**: `apps/documents/models.py`
- **Document**: Modelo principal con campos extendidos
  - `processing_state`: Enum (pending, converting, indexing, ready, error)
  - `vector_id`: UUID para identificación en índices vectoriales
  - `metadata`: JSON para metadatos adicionales

- **DocumentVectorCache**: Caché de vectores
  - `content`: Texto extraído del documento
  - `vector_id`: UUID del vector
  - `last_access`: Timestamp de último acceso

**Signals**:
- `post_delete`: Elimina archivo de Azure Storage
- `post_save`: Dispara procesamiento asíncrono

### 3. Processing Pipeline (Celery Tasks)

**Service**: `tasks/document_pipeline.py`
- **process_document_async**: Pipeline secuencial
  1. **Download**: Descarga archivo original
  2. **Convert**: Extrae texto del documento
  3. **Store**: Guarda versión convertida en `/converted/`
  4. **Embed**: Genera embeddings vectoriales
  5. **Cache**: Almacena en PostgreSQL
  6. **Index**: Inserta en Azure AI Search

**Logging**: JSON estructurado para Log Analytics
```json
{
  "stage": "indexing",
  "doc_id": "uuid",
  "filename": "document.pdf",
  "status": "success",
  "elapsed_ms": 1250
}
```

### 4. Search Layer (Azure AI Search)

**Service**: `services/search_index_service.py`
- **SearchIndexService**: Maneja operaciones de búsqueda
- **Métodos principales**:
  - `upsert_document()`: Inserta/actualiza documentos
  - `delete_document()`: Elimina del índice
  - `search()`: Búsqueda textual y vectorial
  - `get_document_count()`: Conteo de documentos

**Retry Strategy**: Retry exponencial para errores 5xx

## Data Flow

### Upload Flow
```
1. User uploads file → Django Form
2. DocumentStorageService.upload() → Azure Blob Storage
3. Document model saved → PostgreSQL
4. post_save signal → process_document_async.delay()
5. Async processing → Convert → Embed → Index
6. Document.processing_state = 'ready'
```

### Download Flow
```
1. User requests download → download_document view
2. DocumentStorageService.download_url() → SAS URL
3. Redirect to signed URL → Direct Azure download
```

### Delete Flow
```
1. User deletes document → delete_document view
2. post_delete signal → DocumentStorageService.delete()
3. SearchIndexService.delete_document() → Remove from index
4. DocumentVectorCache cascade delete → PostgreSQL
```

## Configuration

### Environment Variables Required

```bash
# Azure Storage
BLOB_ACCOUNT_NAME=veaconnectstr
BLOB_ACCOUNT_KEY=<storage-account-key>
BLOB_CONTAINER_NAME=documents

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://ai-search-veaconnect-prod.search.windows.net
AZURE_SEARCH_API_KEY=<search-api-key>
AZURE_SEARCH_INDEX_NAME=vea-connect-index

# Azure OpenAI (for embeddings)
AZURE_OPENAI_ENDPOINT=https://openai-veaconnect.openai.azure.com/
AZURE_OPENAI_API_KEY=<openai-api-key>
```

### Django Settings

```python
# File Storage
DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
AZURE_OVERWRITE_FILES = False
AZURE_URL_EXPIRATION_SECONDS = 259200

# Search
AZURE_SEARCH_ENDPOINT = os.environ.get('AZURE_SEARCH_ENDPOINT')
AZURE_SEARCH_API_KEY = os.environ.get('AZURE_SEARCH_API_KEY')
AZURE_SEARCH_INDEX_NAME = os.environ.get('AZURE_SEARCH_INDEX_NAME', 'vea-connect-index')
```

## Error Handling

### Storage Errors
- **Upload failures**: Retry automático con nombres únicos
- **Download failures**: URLs SAS con expiración
- **Delete failures**: Logging sin interrumpir flujo

### Processing Errors
- **Conversion failures**: Estado 'error', logging detallado
- **Indexing failures**: Retry exponencial (3 intentos)
- **Network timeouts**: Retry con backoff exponencial

### Search Errors
- **API failures**: Retry automático para errores 5xx
- **Authentication errors**: Logging inmediato
- **Throttling**: Backoff exponencial

## Monitoring & Observability

### Logging Strategy
- **Structured JSON**: Para Log Analytics
- **Stage tracking**: Cada etapa del pipeline
- **Performance metrics**: elapsed_ms por operación
- **Error correlation**: doc_id en todos los logs

### Metrics to Monitor
- **Upload success rate**: Documentos subidos vs procesados
- **Processing time**: Tiempo promedio por etapa
- **Search performance**: Latencia de consultas
- **Storage usage**: Uso del contenedor Azure

### Health Checks
- **Storage connectivity**: DocumentStorageService.exists()
- **Search connectivity**: SearchIndexService.get_document_count()
- **Database connectivity**: Document.objects.count()

## Security Considerations

### Access Control
- **SAS URLs**: Expiración de 72 horas
- **API Keys**: Rotación regular
- **Container permissions**: Blob Data Contributor

### Data Protection
- **No overwrite**: AZURE_OVERWRITE_FILES = False
- **Unique filenames**: Timestamp + UUID
- **Metadata sanitization**: Limpieza de metadatos sensibles

## Performance Optimizations

### Storage
- **Direct Azure URLs**: Evita proxy Django
- **SAS caching**: URLs reutilizables por 72 horas
- **Batch operations**: Para operaciones múltiples

### Processing
- **Async tasks**: Celery para procesamiento
- **Content caching**: PostgreSQL como caché ligera
- **Vector reuse**: Embeddings almacenados

### Search
- **Batch indexing**: Upsert en lotes
- **Vector search**: Búsqueda híbrida (texto + vectores)
- **Connection pooling**: Reutilización de conexiones

## Migration Guide

### From FileSystemStorage
1. **Backup existing files**: Exportar desde contenedor actual
2. **Update settings**: Cambiar DEFAULT_FILE_STORAGE
3. **Migrate data**: Script de migración de archivos
4. **Update views**: Usar DocumentStorageService
5. **Test thoroughly**: Verificar upload/download/delete

### Database Migrations
```bash
python manage.py makemigrations documents
python manage.py migrate
```

### Index Setup
1. **Create search index**: Azure AI Search
2. **Configure vector fields**: Para embeddings
3. **Set up data source**: Si usa indexer
4. **Test indexing**: Subir documento de prueba

## Troubleshooting

### Common Issues

**Upload fails**
- Verificar BLOB_ACCOUNT_KEY
- Check container permissions
- Validate file size limits

**Download fails**
- Verify SAS URL generation
- Check file existence in Azure
- Validate URL expiration

**Processing stuck**
- Check Celery worker status
- Verify task queue
- Review error logs

**Search not working**
- Validate AZURE_SEARCH_API_KEY
- Check index configuration
- Verify document count > 0

### Debug Commands

```bash
# Check storage connectivity
python manage.py shell -c "from services.storage_service import document_storage_service; print(document_storage_service.exists('test.txt'))"

# Check search connectivity
python manage.py shell -c "from services.search_index_service import search_index_service; print(search_index_service.get_document_count())"

# Check processing status
python manage.py shell -c "from apps.documents.models import Document; print(Document.objects.filter(processing_state='ready').count())"
```

## Future Enhancements

### Planned Features
- **OCR integration**: Para imágenes y PDFs
- **Advanced conversion**: Word, Excel, PowerPoint
- **Version control**: Historial de versiones
- **Collaborative editing**: Edición en tiempo real

### Performance Improvements
- **CDN integration**: Para archivos estáticos
- **Compression**: Para archivos grandes
- **Caching layers**: Redis para búsquedas frecuentes
- **Background indexing**: Indexación incremental

### Security Enhancements
- **Encryption at rest**: Para archivos sensibles
- **Access logging**: Auditoría de accesos
- **Virus scanning**: Escaneo de archivos
- **Compliance**: GDPR, HIPAA support
