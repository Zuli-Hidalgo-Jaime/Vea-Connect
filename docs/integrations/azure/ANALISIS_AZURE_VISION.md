# Análisis de Azure Computer Vision en VEA Connect

## Resumen Ejecutivo

Este documento analiza la integración de Azure Computer Vision en el proyecto VEA Connect, identificando dónde se procesa y almacena la información extraída de documentos.

## Funciones y Métodos que Utilizan Azure Computer Vision

### 1. Clase AzureVisionService (`apps/vision/azure_vision_service.py`)

#### Métodos principales:
- `extract_text_from_image()`: Extrae texto de imágenes usando OCR
- `extract_text_from_pdf()`: Extrae texto de PDFs usando Form Recognizer
- `is_service_available()`: Verifica disponibilidad del servicio

#### Ubicación de procesamiento:
```python
# Aquí se almacena el resultado del procesamiento de Vision, se mantiene documentado para posibles ajustes de integración con AI Search.
result = self.vision_client.recognize_printed_text_in_stream(image_data)
```

```python
# Aquí se almacena el resultado del procesamiento de Vision, se mantiene documentado para posibles ajustes de integración con AI Search.
poller = self.document_client.begin_analyze_document("prebuilt-document", pdf_data)
result = poller.result()
```

### 2. Vista extract_text_from_file (`apps/vision/views.py`)

#### Funcionalidad:
- Procesa archivos subidos (imágenes y PDFs)
- Utiliza AzureVisionService para extracción de texto
- Retorna JSON con texto extraído

#### Ubicación de procesamiento:
```python
# Aquí se almacena el resultado del procesamiento de Vision, se mantiene documentado para posibles ajustes de integración con AI Search.
if file_extension == '.pdf':
    extracted_text = vision_service.extract_text_from_pdf(temp_file_path)
else:
    extracted_text = vision_service.extract_text_from_image(temp_file_path)
```

## Almacenamiento de Resultados

### Contenedor de Blob Storage
- **Contenedor principal**: `documents` (configurado en `BLOB_CONTAINER_NAME`)
- **Cuenta de almacenamiento**: Configurada en `BLOB_ACCOUNT_NAME`

### Estructura de carpetas (prefijos)
Según el análisis del código en `utilities/azureblobstorage.py`:

1. **Archivos originales**: Se almacenan directamente en el contenedor `documents`
2. **Archivos procesados**: Se almacenan con prefijo `converted/`
3. **Metadatos**: Se almacenan como metadatos del blob con flags:
   - `converted`: Indica si el archivo ha sido procesado
   - `embeddings_added`: Indica si se han generado embeddings

### Variables de configuración
```env
BLOB_ACCOUNT_NAME=veaconnectstr
BLOB_ACCOUNT_KEY=your-storage-key
BLOB_CONTAINER_NAME=documents
```

## Flujo de Procesamiento

1. **Subida de archivo**: El usuario sube un archivo (imagen o PDF)
2. **Procesamiento temporal**: Se guarda temporalmente en el servidor
3. **Extracción de texto**: Azure Computer Vision extrae el texto
4. **Almacenamiento**: El texto extraído se puede almacenar como:
   - Respuesta JSON inmediata al usuario
   - Metadatos del blob en Azure Storage
   - Documento en Azure AI Search (para búsquedas semánticas)

## Integración con Azure AI Search

### Oportunidades de mejora:
1. **Almacenamiento automático**: Los textos extraídos podrían almacenarse automáticamente en Azure AI Search
2. **Generación de embeddings**: Los textos extraídos podrían generar embeddings para búsquedas vectoriales
3. **Metadatos enriquecidos**: Agregar metadatos sobre el proceso de extracción

### Implementación sugerida:
```python
# Después de extraer texto con Vision
extracted_text = vision_service.extract_text_from_pdf(file_path)

# Crear embedding y almacenar en Azure Search
embedding_manager = get_embedding_manager()
embedding_manager.create_embedding(
    document_id=file_id,
    text=extracted_text,
    metadata={
        'source': 'azure_vision',
        'file_type': 'pdf',
        'extraction_date': datetime.utcnow().isoformat()
    }
)
```

## Configuración de Azure Computer Vision

### Variables de entorno requeridas:
```env
VISION_ENDPOINT=https://cv-veaconnect.cognitiveservices.azure.com/
VISION_KEY=your-vision-key
```

### Servicios utilizados:
- **Computer Vision**: Para OCR en imágenes
- **Form Recognizer**: Para extracción de texto en PDFs

## Recomendaciones

1. **Documentación**: Mantener documentados todos los puntos donde se procesa información con Vision
2. **Integración**: Considerar la integración automática con Azure AI Search
3. **Monitoreo**: Implementar logging detallado del proceso de extracción
4. **Optimización**: Evaluar el uso de diferentes modelos de Form Recognizer según el tipo de documento

## Conclusión

Azure Computer Vision está integrado principalmente en el módulo `apps.vision` y procesa documentos que se almacenan en el contenedor `documents` de Azure Blob Storage. Los resultados se pueden integrar fácilmente con Azure AI Search para habilitar búsquedas semánticas en los documentos procesados. 