# Convención de Nombres de Almacenamiento

## Resumen

Este documento describe el sistema de resolución de nombres de Azure Blob Storage implementado para eliminar errores `BlobNotFound` causados por desajustes de nombres y prefijos.

## Problema Resuelto

Los errores `BlobNotFound` ocurrían cuando:
- Los nombres de archivos contenían espacios, acentos o caracteres especiales
- Los prefijos de categoría (`documents/`, `contacts/`, etc.) no coincidían
- Las URLs firmadas no manejaban correctamente caracteres especiales
- No había un mapeo entre nombres originales y nombres canónicos

## Solución Implementada

### 1. Canonicalización de Nombres

```python
# Ejemplo de canonicalización
original_name = "Donaciones Daya 2025_08_08.jpg"
canonical_name = azure_storage.canonicalize_blob_name(original_name, category="documents")
# Resultado: "documents/donaciones_daya_2025_08_08_202508111234_abc123.jpg"
```

**Proceso de canonicalización:**
1. Normalización Unicode (NFD)
2. Conversión a ASCII y minúsculas
3. Reemplazo de caracteres no seguros por `_`
4. Preservación de extensión de archivo
5. Adición de timestamp y hash para unicidad
6. Prefijo de categoría opcional

### 2. Sistema de Resolución Inteligente

El método `resolve_blob_name()` implementa múltiples estrategias:

1. **Búsqueda exacta**: Intenta el nombre tal como se proporciona
2. **Prefijos de categoría**: Prueba agregando/removiendo prefijos (`documents/`, `contacts/`, etc.)
3. **URL encoding**: Intenta con caracteres escapados
4. **Búsqueda por metadatos**: Busca en metadatos `original_name` (case-insensitive)
5. **Manifiesto**: Consulta archivo `__manifest/manifest.json` para mapeos

### 3. Metadatos Automáticos

Cada blob subido incluye metadatos:
```json
{
  "original_name": "Donaciones Daya 2025_08_08.jpg",
  "category": "documents",
  "uploaded_at_utc": "2025-08-11T15:30:00Z",
  "content_type": "image/jpeg"
}
```

### 4. Manifiesto de Mapeo

Archivo JSON en `__manifest/manifest.json`:
```json
{
  "donaciones daya 2025_08_08.jpg": {
    "blob": "documents/donaciones_daya_2025_08_08_202508111234_abc123.jpg",
    "category": "documents",
    "uploaded_at": "2025-08-11T15:30:00Z",
    "size": 1024
  }
}
```

## Uso en la Aplicación

### Subida de Archivos

```python
# Subir con nombre original - se canonicaliza automáticamente
result = azure_storage.upload_file(
    file_path="local_file.jpg",
    blob_name="Donaciones Daya 2025_08_08.jpg",
    category="documents",
    content_type="image/jpeg"
)

# El archivo se guarda como: documents/donaciones_daya_2025_08_08_202508111234_abc123.jpg
# Pero se puede acceder usando el nombre original
```

### Descarga de Archivos

```python
# Descargar usando nombre original (sin prefijo)
result = azure_storage.download_file(
    blob_name="Donaciones Daya 2025_08_08.jpg",  # Nombre original
    local_path="downloaded_file.jpg"
)

# También funciona con prefijo
result = azure_storage.download_file(
    blob_name="documents/Donaciones Daya 2025_08_08.jpg",  # Con prefijo
    local_path="downloaded_file.jpg"
)
```

### URLs Firmadas

```python
# Generar URL firmada con nombre original
result = azure_storage.get_blob_url(
    blob_name="Donaciones Daya 2025_08_08.jpg",
    expires_in=3600
)

# La URL se genera correctamente con caracteres escapados
```

### Eliminación

```python
# Eliminar usando nombre original
result = azure_storage.delete_blob("Donaciones Daya 2025_08_08.jpg")
```

## Compatibilidad Hacia Atrás

- **Todas las llamadas existentes siguen funcionando**
- Los nombres canónicos se generan automáticamente en subidas
- La resolución funciona tanto con nombres originales como canónicos
- No se requieren cambios en el código existente

## Categorías Soportadas

- `documents` - Documentos generales
- `contacts` - Archivos de contactos
- `events` - Archivos de eventos
- `converted` - Archivos convertidos
- `conversations` - Archivos de conversaciones
- `system` - Archivos del sistema (manifiestos, etc.)

## Verificación y Mantenimiento

### Script de Verificación

```bash
# Verificar consistencia
python scripts/storage_consistency_check.py

# Reconstruir manifiesto
python scripts/storage_consistency_check.py --rebuild-manifest

# Generar reporte CSV
python scripts/storage_consistency_check.py --output-format csv --output-file report.csv
```

### Diagnóstico E2E

```bash
# Incluye pruebas de resolución de nombres
python scripts/diagnostics/diagnostic_e2e.py
```

## Logging

### Al Subir
```
INFO: File uploaded successfully: Donaciones Daya 2025_08_08.jpg -> documents/donaciones_daya_2025_08_08_202508111234_abc123.jpg (category: documents, content_type: image/jpeg)
```

### Al Resolver
```
DEBUG: Blob found by metadata: documents/donaciones_daya_2025_08_08_202508111234_abc123.jpg
```

### Si No Se Encuentra
```
INFO: Blob not found: Donaciones Daya 2025_08_08.jpg. Pruebe con categoría 'documents' o verifique el nombre exacto
```

## Beneficios

1. **Eliminación de BlobNotFound**: Los errores desaparecen gracias a la resolución inteligente
2. **Compatibilidad total**: No se requieren cambios en código existente
3. **Nombres seguros**: Los nombres canónicos son compatibles con URLs y sistemas de archivos
4. **Trazabilidad**: Metadatos y manifiesto permiten rastrear archivos
5. **Flexibilidad**: Soporta múltiples formas de referenciar el mismo archivo

## Consideraciones

- El manifiesto se mantiene automáticamente (máximo 1000 entradas)
- Los metadatos se agregan automáticamente en nuevas subidas
- La resolución es case-insensitive para nombres originales
- Las URLs firmadas manejan correctamente caracteres especiales
- El sistema es backward-compatible con archivos existentes
