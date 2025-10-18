# Implementación de Almacenamiento de Texto Extraído por Azure Computer Vision

## Resumen Ejecutivo

Se ha implementado el almacenamiento del texto extraído por Azure Computer Vision en el contenedor `documents` de Azure Blob Storage, siguiendo el patrón existente de almacenamiento en la carpeta `converted/` para futura indexación en Azure AI Search.

## Funciones Implementadas

### 1. `save_extracted_text_to_blob()` - `utilities/azureblobstorage.py`

**Propósito**: Guarda el texto extraído por Azure Computer Vision como archivo JSON en la carpeta `converted/`.

**Ubicación**: Líneas 209-260

**Funcionalidad**:
- Crea un archivo JSON con el texto extraído y metadatos
- Sigue el patrón de nombramiento: `converted/{base_name}_extracted_text.json`
- Incluye metadatos como fecha de extracción, longitud del texto, y metadatos adicionales
- Retorna la URL del blob subido o None si falla

**Estructura del JSON**:
```json
{
  "original_file": "document.pdf",
  "extracted_text": "Texto extraído por Azure Computer Vision...",
  "extraction_date": "2024-01-15T10:30:00.000Z",
  "source": "azure_computer_vision",
  "text_length": 1500,
  "metadata": {
    "file_type": ".pdf",
    "original_filename": "document.pdf",
    "extraction_method": "azure_computer_vision",
    "user_id": 123
  }
}
```

### 2. `update_zip_with_extracted_text()` - `utilities/azureblobstorage.py`

**Propósito**: Actualiza archivos ZIP existentes en la carpeta `converted/` con el texto extraído.

**Ubicación**: Líneas 262-330

**Funcionalidad**:
- Descarga el ZIP existente desde Azure Blob Storage
- Agrega o actualiza el archivo `extracted_text.json` dentro del ZIP
- Mantiene todos los archivos existentes (archivo original y metadata.json)
- Sube el ZIP actualizado de vuelta a Azure Blob Storage

**Estructura del ZIP actualizado**:
```
converted/document.pdf.zip
├── document.pdf (archivo original)
├── metadata.json (metadatos del documento)
└── extracted_text.json (texto extraído por Vision)
```

### 3. `get_extracted_text_from_blob()` - `utilities/azureblobstorage.py`

**Propósito**: Recupera el texto extraído desde Azure Blob Storage.

**Ubicación**: Líneas 332-380

**Funcionalidad**:
- Busca primero en archivos JSON independientes
- Si no encuentra, busca dentro de archivos ZIP
- Retorna los datos completos del texto extraído con metadatos
- Maneja errores y casos donde no existe texto extraído

### 4. Actualización de `get_all_files()` - `utilities/azureblobstorage.py`

**Propósito**: Extiende la función existente para incluir información sobre texto extraído.

**Ubicación**: Líneas 100-130

**Funcionalidad**:
- Agrega campos `has_extracted_text` y `extracted_text_path` a cada archivo
- Verifica la existencia de archivos JSON de texto extraído
- Mantiene compatibilidad con la lógica existente

## Modificaciones en Vistas y Señales

### 1. Vista `extract_text_from_file()` - `apps/vision/views.py`

**Cambios realizados**:
- Importa `save_extracted_text_to_blob` desde `utilities.azureblobstorage`
- Guarda el texto extraído después de la extracción exitosa
- Incluye metadatos como tipo de archivo, nombre original, y usuario
- Retorna información sobre el almacenamiento en la respuesta JSON

**Nueva estructura de respuesta**:
```json
{
  "success": true,
  "text": "Texto extraído...",
  "filename": "document.pdf",
  "file_type": ".pdf",
  "text_length": 1500,
  "stored_for_indexing": true,
  "storage_url": "https://storage.blob.core.windows.net/..."
}
```

### 2. Señal `upload_document_to_blob()` - `apps/documents/signals.py`

**Cambios realizados**:
- Importa `save_extracted_text_to_blob` desde `utilities.azureblobstorage`
- Agrega un placeholder para texto extraído en el ZIP
- Mantiene la estructura existente del ZIP
- Prepara el ZIP para futuras actualizaciones con texto extraído

**Nuevo archivo en ZIP**:
```json
{
  "extracted_text": "",
  "extraction_status": "pending",
  "extraction_date": null,
  "source": "azure_computer_vision"
}
```

## Patrón de Almacenamiento

### Estructura de Carpetas
```
documents/ (contenedor principal)
├── document.pdf (archivo original)
└── converted/
    ├── document.pdf.zip (ZIP con metadatos y placeholder)
    └── document_extracted_text.json (texto extraído independiente)
```

### Nomenclatura de Archivos
- **Archivos ZIP**: `converted/{original_name}.zip`
- **Archivos JSON**: `converted/{base_name}_extracted_text.json`
- **Archivos dentro de ZIP**: `extracted_text.json`

### Metadatos del Blob
- `converted`: Indica si el archivo ha sido procesado
- `embeddings_added`: Indica si se han generado embeddings
- `has_extracted_text`: Indica si existe texto extraído (nuevo)

## Integración con Azure AI Search

### Preparación para Indexación
Los archivos JSON y ZIP almacenados están estructurados para facilitar la indexación en Azure AI Search:

1. **Archivos JSON independientes**: Contienen texto completo y metadatos estructurados
2. **Archivos ZIP**: Contienen archivo original, metadatos y texto extraído
3. **Metadatos consistentes**: Incluyen información de origen, fechas y longitudes

### Funciones de Lectura
- `get_extracted_text_from_blob()`: Recupera texto para indexación
- `get_all_files()`: Lista archivos con información de texto extraído
- Compatibilidad con Azure AI Search para futuras integraciones

## Comentarios de Documentación

Todos los cambios incluyen comentarios de documentación siguiendo el patrón solicitado:

```python
# Se agrega almacenamiento del texto extraído por Azure Computer Vision en la carpeta converted/ para futura indexación en Azure AI Search
```

## Compatibilidad y Preservación

### Lógica Existente Preservada
- ✅ Todas las funciones existentes se mantienen sin modificación
- ✅ El patrón de almacenamiento en `converted/` se respeta
- ✅ Los metadatos del blob se mantienen intactos
- ✅ La lógica de Redis no se modifica

### Nuevas Funcionalidades
- ✅ Almacenamiento de texto extraído en formato JSON
- ✅ Actualización de archivos ZIP existentes
- ✅ Recuperación de texto extraído
- ✅ Información de texto extraído en listados de archivos

## Uso y Ejemplos

### Guardar Texto Extraído
```python
from utilities.azureblobstorage import save_extracted_text_to_blob

# Después de extraer texto con Azure Computer Vision
blob_url = save_extracted_text_to_blob(
    original_blob_name="document.pdf",
    extracted_text="Texto extraído...",
    metadata={"user_id": 123, "file_type": ".pdf"}
)
```

### Recuperar Texto Extraído
```python
from utilities.azureblobstorage import get_extracted_text_from_blob

# Obtener texto extraído
text_data = get_extracted_text_from_blob("document.pdf")
if text_data:
    extracted_text = text_data["extracted_text"]
    metadata = text_data["metadata"]
```

### Listar Archivos con Texto Extraído
```python
from utilities.azureblobstorage import get_all_files

# Obtener todos los archivos con información de texto extraído
files = get_all_files()
for file in files:
    if file.get('has_extracted_text'):
        print(f"Archivo {file['filename']} tiene texto extraído")
```

## Conclusión

La implementación completa el flujo de procesamiento de documentos con Azure Computer Vision, almacenando el texto extraído de manera estructurada y compatible con futuras integraciones con Azure AI Search. Todos los cambios respetan la lógica existente y proporcionan funcionalidades adicionales sin afectar el comportamiento actual del sistema. 